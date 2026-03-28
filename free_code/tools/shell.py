"""Shell command execution with safety checks."""

from __future__ import annotations

import subprocess
from typing import Optional

# Commands that are always blocked
BLOCKED_COMMANDS = {
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=/dev/zero",
    ":(){:|:&};:",
}

# Patterns that require confirmation even in non-safe mode
DANGEROUS_PATTERNS = [
    "rm -rf",
    "rm -r",
    "sudo rm",
    "git push --force",
    "git reset --hard",
    "DROP TABLE",
    "DROP DATABASE",
    "FORMAT",
    "shutdown",
    "reboot",
    "systemctl stop",
    "kill -9",
]


def is_dangerous(command: str) -> bool:
    """Check if a command contains dangerous patterns."""
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in cmd_lower:
            return True
    return False


def is_blocked(command: str) -> bool:
    """Check if a command is permanently blocked."""
    cmd_stripped = command.strip()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_stripped:
            return True
    return False


def shell_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 60,
    _project_root: Optional[str] = None,
) -> str:
    """Execute a shell command and return stdout + stderr.

    Args:
        command: Shell command string.
        cwd: Working directory.
        timeout: Timeout in seconds (default 60).
    """
    if is_blocked(command):
        return f"Error: Command blocked for safety: {command}"

    work_dir = cwd or _project_root or None

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=work_dir,
        )
        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[stderr]\n{result.stderr}")
        if result.returncode != 0:
            output_parts.append(f"[exit code: {result.returncode}]")

        output = "\n".join(output_parts)
        # Truncate very long output
        if len(output) > 50000:
            output = output[:25000] + "\n\n... (truncated) ...\n\n" + output[-25000:]
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s: {command}"
    except OSError as e:
        return f"Error executing command: {e}"
