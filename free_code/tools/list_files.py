"""Directory listing with .gitignore respect."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import List, Optional

import pathspec


def list_files(
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    max_depth: Optional[int] = None,
    max_files: int = 1000,
    _project_root: Optional[str] = None,
) -> str:
    """List files in a directory, respecting .gitignore.

    Args:
        path: Directory to list (default: project root).
        pattern: Glob pattern filter (e.g. '*.py').
        max_depth: Maximum directory depth to traverse.
        max_files: Maximum number of files to return.
    """
    root = Path(path or _project_root or ".").resolve()
    if not root.exists():
        return f"Error: Directory not found: {root}"
    if not root.is_dir():
        return f"Error: Not a directory: {root}"

    # Load .gitignore patterns
    ignore_spec = _load_gitignore(root)

    files: List[str] = []
    _walk(root, root, ignore_spec, pattern, max_depth, 0, files, max_files)

    if not files:
        return f"No files found in {root}"

    header = f"[{root}] ({len(files)} files)"
    if len(files) >= max_files:
        header += f" (truncated to {max_files})"

    return header + "\n" + "\n".join(files)


def _walk(
    base: Path,
    current: Path,
    ignore_spec: Optional[pathspec.PathSpec],
    pattern: Optional[str],
    max_depth: Optional[int],
    depth: int,
    results: List[str],
    max_files: int,
) -> None:
    """Recursively walk directory."""
    if len(results) >= max_files:
        return
    if max_depth is not None and depth > max_depth:
        return

    try:
        entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return

    for entry in entries:
        if len(results) >= max_files:
            return

        rel = str(entry.relative_to(base))
        if entry.is_dir():
            rel += "/"

        # Skip hidden directories (but not hidden files in root)
        if entry.name.startswith(".") and entry.is_dir():
            continue

        # Check gitignore
        if ignore_spec and ignore_spec.match_file(rel):
            continue

        if entry.is_file():
            if pattern and not fnmatch.fnmatch(entry.name, pattern):
                continue
            indent = "  " * depth
            results.append(f"{indent}{entry.name}")
        elif entry.is_dir():
            indent = "  " * depth
            results.append(f"{indent}{entry.name}/")
            _walk(base, entry, ignore_spec, pattern, max_depth, depth + 1, results, max_files)


def _load_gitignore(root: Path) -> Optional[pathspec.PathSpec]:
    """Load .gitignore patterns from the project root."""
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return None

    try:
        text = gitignore_path.read_text(errors="replace")
        return pathspec.PathSpec.from_lines("gitwildmatch", text.splitlines())
    except OSError:
        return None
