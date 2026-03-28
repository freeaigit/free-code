"""File read, write, and patch operations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def file_read(
    path: str,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    _project_root: Optional[str] = None,
) -> str:
    """Read file contents. Returns numbered lines like `cat -n`.

    Args:
        path: File path (absolute or relative to project root).
        offset: Start line (1-based).
        limit: Max lines to return.
    """
    resolved = _resolve_path(path, _project_root)
    if not resolved.exists():
        return f"Error: File not found: {resolved}"
    if not resolved.is_file():
        return f"Error: Not a file: {resolved}"

    try:
        text = resolved.read_text(encoding="utf-8", errors="replace")
    except PermissionError:
        return f"Error: Permission denied: {resolved}"

    lines = text.splitlines(keepends=True)
    total = len(lines)

    start = (offset or 1) - 1
    start = max(0, min(start, total))
    end = start + limit if limit else total

    numbered = []
    for i, line in enumerate(lines[start:end], start=start + 1):
        numbered.append(f"{i:>6}\t{line.rstrip()}")

    header = f"[{resolved}] ({total} lines)"
    return header + "\n" + "\n".join(numbered)


def file_write(
    path: str,
    content: str,
    _project_root: Optional[str] = None,
) -> str:
    """Write content to a file, creating parent directories as needed.

    Args:
        path: File path.
        content: Full file content.
    """
    resolved = _resolve_path(path, _project_root)

    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        lines = content.count("\n") + (0 if content.endswith("\n") else 1)
        return f"Wrote {lines} lines to {resolved}"
    except PermissionError:
        return f"Error: Permission denied: {resolved}"
    except OSError as e:
        return f"Error writing file: {e}"


def apply_patch(
    path: str,
    old_string: str,
    new_string: str,
    _project_root: Optional[str] = None,
) -> str:
    """Apply a search/replace patch to a file.

    Args:
        path: File path.
        old_string: Exact string to find.
        new_string: Replacement string.
    """
    resolved = _resolve_path(path, _project_root)
    if not resolved.exists():
        return f"Error: File not found: {resolved}"

    try:
        text = resolved.read_text(encoding="utf-8")
    except PermissionError:
        return f"Error: Permission denied: {resolved}"

    count = text.count(old_string)
    if count == 0:
        return f"Error: old_string not found in {resolved}"
    if count > 1:
        return f"Error: old_string matches {count} locations in {resolved}. Provide more context to make it unique."

    new_text = text.replace(old_string, new_string, 1)
    resolved.write_text(new_text, encoding="utf-8")
    return f"Applied patch to {resolved}"


def _resolve_path(path: str, project_root: Optional[str] = None) -> Path:
    """Resolve a path, making it absolute relative to project root."""
    p = Path(path)
    if p.is_absolute():
        return p
    root = Path(project_root) if project_root else Path.cwd()
    return (root / p).resolve()
