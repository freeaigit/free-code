"""Code search using ripgrep or grep."""

from __future__ import annotations

import shutil
import subprocess
from typing import Optional


def grep_search(
    pattern: str,
    path: Optional[str] = None,
    include: Optional[str] = None,
    max_results: int = 200,
    _project_root: Optional[str] = None,
) -> str:
    """Search for a regex pattern in files using ripgrep or grep.

    Args:
        pattern: Regex search pattern.
        path: Directory or file to search in.
        include: Glob filter (e.g. '*.py').
        max_results: Maximum number of matches.
    """
    search_path = path or _project_root or "."

    # Prefer ripgrep
    rg_path = shutil.which("rg")
    if rg_path:
        return _search_rg(rg_path, pattern, search_path, include, max_results)
    # Fall back to grep
    return _search_grep(pattern, search_path, include, max_results)


def _search_rg(
    rg_path: str,
    pattern: str,
    path: str,
    include: Optional[str],
    max_results: int,
) -> str:
    """Search using ripgrep."""
    cmd = [rg_path, "--no-heading", "-n", "--color=never", "-m", str(max_results)]
    if include:
        cmd.extend(["-g", include])
    cmd.extend([pattern, path])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if not output:
            return f"No matches found for: {pattern}"
        lines = output.split("\n")
        if len(lines) >= max_results:
            output += f"\n\n... (showing first {max_results} matches)"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Search timed out"
    except OSError as e:
        return f"Error: {e}"


def _search_grep(
    pattern: str,
    path: str,
    include: Optional[str],
    max_results: int,
) -> str:
    """Search using grep (fallback)."""
    cmd = ["grep", "-rn", "--color=never"]
    if include:
        cmd.extend(["--include", include])
    cmd.extend(["-m", str(max_results), pattern, path])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if not output:
            return f"No matches found for: {pattern}"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Search timed out"
    except OSError as e:
        return f"Error: {e}"
