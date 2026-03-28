"""File discovery with .gitignore respect."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Set

import pathspec

# Always ignored regardless of .gitignore
ALWAYS_IGNORE = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    ".next",
    ".nuxt",
    "target",  # Rust/Java
}

# File extensions to include (code/config files)
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".kt",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".m",
    ".vue", ".svelte", ".html", ".css", ".scss", ".less",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".md", ".txt", ".rst",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".graphql",
    ".dockerfile", ".Dockerfile",
    ".env.example", ".gitignore",
    "Makefile", "Dockerfile", "docker-compose.yml",
}

MAX_FILE_SIZE = 512 * 1024  # 512 KB — skip very large files


def discover_files(
    root: Path,
    max_files: int = 5000,
) -> List[Path]:
    """Discover all code files in a project, respecting .gitignore.

    Returns files sorted by relevance (config files first, then by path).
    """
    root = root.resolve()
    ignore_spec = _build_ignore_spec(root)

    files: List[Path] = []
    _walk_discover(root, root, ignore_spec, files, max_files)

    # Sort: config/root files first, then alphabetically
    def sort_key(p: Path) -> tuple:
        rel = p.relative_to(root)
        depth = len(rel.parts)
        is_config = p.name in (
            "pyproject.toml", "package.json", "Cargo.toml", "go.mod",
            "Makefile", "Dockerfile", "docker-compose.yml",
            "README.md", "CLAUDE.md",
        )
        return (not is_config, depth, str(rel).lower())

    files.sort(key=sort_key)
    return files


def _walk_discover(
    base: Path,
    current: Path,
    ignore_spec: Optional[pathspec.PathSpec],
    results: List[Path],
    max_files: int,
) -> None:
    """Recursively discover code files."""
    if len(results) >= max_files:
        return

    try:
        entries = sorted(current.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        return

    for entry in entries:
        if len(results) >= max_files:
            return

        # Skip always-ignored dirs
        if entry.name in ALWAYS_IGNORE or (entry.name.startswith(".") and entry.is_dir()):
            continue

        rel = str(entry.relative_to(base))

        # Check gitignore
        if ignore_spec:
            check_path = rel + "/" if entry.is_dir() else rel
            if ignore_spec.match_file(check_path):
                continue

        if entry.is_dir():
            _walk_discover(base, entry, ignore_spec, results, max_files)
        elif entry.is_file():
            # Check extension or known filename
            if entry.suffix in CODE_EXTENSIONS or entry.name in CODE_EXTENSIONS:
                # Skip very large files
                try:
                    if entry.stat().st_size <= MAX_FILE_SIZE:
                        results.append(entry)
                except OSError:
                    pass


def _build_ignore_spec(root: Path) -> Optional[pathspec.PathSpec]:
    """Build a PathSpec from .gitignore files in the project."""
    patterns: List[str] = []

    # Root .gitignore
    gitignore = root / ".gitignore"
    if gitignore.exists():
        try:
            patterns.extend(gitignore.read_text(errors="replace").splitlines())
        except OSError:
            pass

    # Add always-ignored patterns
    for p in ALWAYS_IGNORE:
        patterns.append(p)
        patterns.append(f"{p}/")

    if not patterns:
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
