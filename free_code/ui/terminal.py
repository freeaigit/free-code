"""Rich terminal output — syntax highlighting, diffs, progress."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom theme
THEME = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red bold",
    "tool": "magenta",
    "file": "blue underline",
    "dim": "dim",
})

console = Console(theme=THEME)


def print_welcome() -> None:
    """Print the welcome banner."""
    console.print()
    console.print(
        Panel(
            "[bold]Free.ai Coder[/bold] — AI coding assistant\n"
            "[dim]Type your request, or /help for commands. Ctrl+C to exit.[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()


def print_model_info(provider: str, model: str) -> None:
    """Print current model info."""
    console.print(f"  [dim]Provider:[/dim] {provider}  [dim]Model:[/dim] {model}")
    console.print()


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[error]Error:[/error] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[warning]Warning:[/warning] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[success]{message}[/success]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[info]{message}[/info]")


def print_tool_call(tool_name: str, args: dict) -> None:
    """Print a tool call notification."""
    args_str = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items() if not k.startswith("_"))
    console.print(f"\n[tool]> {tool_name}[/tool]({args_str})")


def print_tool_result(result: str, collapsed: bool = False) -> None:
    """Print tool execution result."""
    if collapsed and len(result) > 500:
        lines = result.split("\n")
        preview = "\n".join(lines[:10])
        console.print(f"[dim]{preview}[/dim]")
        console.print(f"[dim]  ... ({len(lines)} lines total)[/dim]")
    else:
        console.print(f"[dim]{result}[/dim]")


def print_markdown(text: str) -> None:
    """Print markdown-formatted text."""
    md = Markdown(text)
    console.print(md)


def print_code(code: str, language: str = "python") -> None:
    """Print syntax-highlighted code."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def print_file_change(path: str, action: str = "modified") -> None:
    """Print a file change notification."""
    icons = {
        "created": "[success]+[/success]",
        "modified": "[warning]~[/warning]",
        "deleted": "[error]-[/error]",
    }
    icon = icons.get(action, "?")
    console.print(f"  {icon} [file]{path}[/file]")


def confirm(message: str, default: bool = True) -> bool:
    """Ask for user confirmation."""
    suffix = " [Y/n] " if default else " [y/N] "
    try:
        response = console.input(f"[warning]{message}[/warning]{suffix}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    if not response:
        return default
    return response in ("y", "yes")
