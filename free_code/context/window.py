"""Context window optimization — fit the most relevant content into the token budget."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import tiktoken

from free_code.context.discovery import discover_files
from free_code.context.repo_map import generate_repo_map

# Approximate token overhead for system prompt, conversation, etc.
SYSTEM_OVERHEAD = 2000
RESPONSE_RESERVE = 4000

# Default encoding for token counting
_encoding: Optional[tiktoken.Encoding] = None


def get_encoding() -> tiktoken.Encoding:
    """Get or create the tiktoken encoding."""
    global _encoding
    if _encoding is None:
        try:
            _encoding = tiktoken.encoding_for_model("gpt-4o")
        except Exception:
            _encoding = tiktoken.get_encoding("cl100k_base")
    return _encoding


def count_tokens(text: str) -> int:
    """Count tokens in a string."""
    enc = get_encoding()
    return len(enc.encode(text, disallowed_special=()))


def build_context(
    root: Path,
    query: str,
    max_tokens: int = 32000,
    include_files: Optional[List[str]] = None,
) -> Tuple[str, List[str]]:
    """Build optimized context for the LLM.

    Returns (context_string, list_of_included_file_paths).

    Strategy:
    1. Always include repo map
    2. Include explicitly requested files
    3. Include files relevant to the query (by filename match)
    4. Fill remaining budget with small, important files
    """
    budget = max_tokens - SYSTEM_OVERHEAD - RESPONSE_RESERVE
    parts: List[str] = []
    included: List[str] = []
    used_tokens = 0

    # 1. Repo map (always include)
    repo_map = generate_repo_map(root, max_files=300)
    map_tokens = count_tokens(repo_map)
    if map_tokens < budget * 0.3:  # Don't let repo map consume > 30%
        parts.append(f"## Repository Structure\n\n{repo_map}")
        used_tokens += map_tokens

    # Discover all files
    all_files = discover_files(root, max_files=2000)
    query_lower = query.lower()

    # 2. Score files by relevance to query
    scored: List[Tuple[float, Path]] = []
    for f in all_files:
        score = _score_file(f, root, query_lower)
        scored.append((score, f))

    # Include explicitly requested files first
    if include_files:
        for inc in include_files:
            p = (root / inc).resolve()
            if p.exists() and p.is_file():
                content = _read_file(p)
                tokens = count_tokens(content)
                if used_tokens + tokens < budget:
                    rel = str(p.relative_to(root))
                    parts.append(f"## File: {rel}\n\n```\n{content}\n```")
                    used_tokens += tokens
                    included.append(rel)

    # 3. Add top-scored files
    scored.sort(key=lambda x: -x[0])
    for score, f in scored:
        if used_tokens >= budget:
            break
        rel = str(f.relative_to(root))
        if rel in included:
            continue

        content = _read_file(f)
        tokens = count_tokens(content)

        if used_tokens + tokens > budget:
            # Skip large files, try smaller ones
            if tokens > budget * 0.2:
                continue
            # Truncate to fit
            max_chars = (budget - used_tokens) * 3  # ~3 chars per token
            content = content[:max_chars] + "\n... (truncated)"
            tokens = count_tokens(content)

        if used_tokens + tokens <= budget:
            parts.append(f"## File: {rel}\n\n```\n{content}\n```")
            used_tokens += tokens
            included.append(rel)

    return "\n\n".join(parts), included


def _score_file(f: Path, root: Path, query: str) -> float:
    """Score a file's relevance to the query."""
    score = 0.0
    name = f.name.lower()
    rel = str(f.relative_to(root)).lower()

    # Filename contains query words
    words = query.split()
    for word in words:
        if len(word) < 3:
            continue
        if word in name:
            score += 10.0
        elif word in rel:
            score += 5.0

    # Config/important files get a boost
    important = {
        "pyproject.toml", "package.json", "cargo.toml", "go.mod",
        "makefile", "dockerfile", "readme.md", "claude.md",
    }
    if name in important:
        score += 8.0

    # Test files get a boost when query mentions tests
    if "test" in query:
        if "test" in name:
            score += 10.0

    # Smaller files are more likely to be useful whole
    try:
        size = f.stat().st_size
        if size < 2000:
            score += 3.0
        elif size < 5000:
            score += 1.0
    except OSError:
        pass

    # Depth penalty
    depth = len(f.relative_to(root).parts)
    score -= depth * 0.5

    return score


def _read_file(path: Path) -> str:
    """Read a file with error handling."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, OSError):
        return f"(cannot read file: {path})"
