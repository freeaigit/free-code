"""Interactive prompt with history."""

from __future__ import annotations

import readline
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

from free_code.config import HISTORY_FILE, ensure_config_dir

console = Console()

# Slash commands
SLASH_COMMANDS = {
    "/help": "Show available commands",
    "/clear": "Clear conversation history",
    "/model": "Show or switch model",
    "/config": "Show current configuration",
    "/files": "List files in project",
    "/repo": "Show repository map",
    "/diff": "Show git diff",
    "/status": "Show git status",
    "/test": "Run tests",
    "/quit": "Exit (also Ctrl+C or Ctrl+D)",
    "/compact": "Summarize conversation to save context",
}


def setup_history() -> None:
    """Initialize readline history."""
    ensure_config_dir()
    history_file = str(HISTORY_FILE)
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass
    readline.set_history_length(1000)

    import atexit
    atexit.register(readline.write_history_file, history_file)


def get_input(prompt_str: str = "> ") -> Optional[str]:
    """Get user input with readline support.

    Returns None on EOF/Ctrl+D.
    """
    try:
        text = console.input(f"[bold cyan]{prompt_str}[/bold cyan]")
        return text.strip()
    except EOFError:
        return None
    except KeyboardInterrupt:
        console.print()
        return None


def get_multiline_input() -> Optional[str]:
    """Get multi-line input (terminated by empty line or Ctrl+D)."""
    lines = []
    console.print("[dim]Enter your message (empty line to send, Ctrl+C to cancel):[/dim]")
    try:
        while True:
            line = input()
            if not line and lines:
                break
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        return None

    return "\n".join(lines).strip() or None


def show_help() -> None:
    """Display help for slash commands."""
    console.print("\n[bold]Commands:[/bold]\n")
    for cmd, desc in SLASH_COMMANDS.items():
        console.print(f"  [cyan]{cmd:12s}[/cyan]  {desc}")
    console.print()
    console.print("[dim]Or just type your coding request in plain English.[/dim]\n")
