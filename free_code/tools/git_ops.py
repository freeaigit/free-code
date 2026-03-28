"""Git operations — status, diff, commit, log."""

from __future__ import annotations

import subprocess
from typing import List, Optional


def _git(args: List[str], cwd: Optional[str] = None) -> str:
    """Run a git command and return output."""
    cmd = ["git"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        output = result.stdout
        if result.stderr and result.returncode != 0:
            output += f"\n{result.stderr}"
        return output.strip() or "(no output)"
    except FileNotFoundError:
        return "Error: git is not installed"
    except subprocess.TimeoutExpired:
        return "Error: git command timed out"


def git_status(_project_root: Optional[str] = None) -> str:
    """Show git status."""
    return _git(["status", "--short"], cwd=_project_root)


def git_diff(
    staged: bool = False,
    _project_root: Optional[str] = None,
) -> str:
    """Show git diff.

    Args:
        staged: If True, show only staged changes.
    """
    args = ["diff"]
    if staged:
        args.append("--cached")
    return _git(args, cwd=_project_root)


def git_commit(
    message: str,
    files: Optional[List[str]] = None,
    _project_root: Optional[str] = None,
) -> str:
    """Create a git commit.

    Args:
        message: Commit message.
        files: Specific files to stage (default: all modified).
    """
    # Stage files
    if files:
        for f in files:
            result = _git(["add", f], cwd=_project_root)
            if "Error" in result:
                return result
    else:
        result = _git(["add", "-A"], cwd=_project_root)
        if "Error" in result:
            return result

    # Commit
    return _git(["commit", "-m", message], cwd=_project_root)


def git_log(
    count: int = 10,
    _project_root: Optional[str] = None,
) -> str:
    """Show recent git log.

    Args:
        count: Number of entries.
    """
    return _git(
        ["log", f"-{count}", "--oneline", "--no-decorate"],
        cwd=_project_root,
    )


def is_git_repo(path: Optional[str] = None) -> bool:
    """Check if the current directory is a git repo."""
    result = _git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return result.strip() == "true"


def git_root(path: Optional[str] = None) -> Optional[str]:
    """Get the root of the git repository."""
    result = _git(["rev-parse", "--show-toplevel"], cwd=path)
    if "Error" in result or "fatal" in result:
        return None
    return result.strip()
