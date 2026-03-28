"""Generate a repository structure summary for LLM context."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from free_code.context.discovery import discover_files


def generate_repo_map(
    root: Path,
    max_files: int = 500,
) -> str:
    """Generate a concise repo map showing project structure.

    Returns a tree-like string with file paths and brief annotations.
    """
    root = root.resolve()
    files = discover_files(root, max_files=max_files)

    if not files:
        return f"(empty project at {root})"

    lines = [f"Repository: {root.name}", ""]

    # Build tree structure
    tree: dict = {}
    for f in files:
        rel = f.relative_to(root)
        parts = list(rel.parts)
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        # Leaf node: store file size info
        try:
            size = f.stat().st_size
        except OSError:
            size = 0
        node[parts[-1]] = size

    _render_tree(tree, lines, prefix="")

    # Add summary
    total = len(files)
    extensions = {}
    for f in files:
        ext = f.suffix or f.name
        extensions[ext] = extensions.get(ext, 0) + 1

    lines.append("")
    lines.append(f"Total: {total} files")

    # Top extensions
    top_ext = sorted(extensions.items(), key=lambda x: -x[1])[:8]
    ext_str = ", ".join(f"{ext}({n})" for ext, n in top_ext)
    lines.append(f"Types: {ext_str}")

    return "\n".join(lines)


def _render_tree(tree: dict, lines: List[str], prefix: str) -> None:
    """Render a tree dict into indented lines."""
    items = sorted(tree.items(), key=lambda x: (not isinstance(x[1], dict), x[0].lower()))

    for i, (name, value) in enumerate(items):
        is_last = i == len(items) - 1
        connector = "  " if is_last else "  "

        if isinstance(value, dict):
            lines.append(f"{prefix}{name}/")
            _render_tree(value, lines, prefix + "  ")
        else:
            # value is file size
            size_str = _format_size(value)
            lines.append(f"{prefix}{name}  ({size_str})")


def _format_size(size: int) -> str:
    """Format file size for display."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.0f}KB"
    else:
        return f"{size / (1024 * 1024):.1f}MB"
