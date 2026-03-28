"""Colorized diff display."""

from __future__ import annotations

import difflib
from typing import List, Optional

from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

console = Console()


def show_diff(old_content: str, new_content: str, filename: str = "") -> None:
    """Display a unified diff with colors."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filename}" if filename else "a/file",
        tofile=f"b/{filename}" if filename else "b/file",
        lineterm="",
    )

    diff_text = Text()
    for line in diff:
        line = line.rstrip("\n")
        if line.startswith("+++") or line.startswith("---"):
            diff_text.append(line + "\n", style="bold")
        elif line.startswith("@@"):
            diff_text.append(line + "\n", style="cyan")
        elif line.startswith("+"):
            diff_text.append(line + "\n", style="green")
        elif line.startswith("-"):
            diff_text.append(line + "\n", style="red")
        else:
            diff_text.append(line + "\n")

    if diff_text:
        console.print(diff_text)
    else:
        console.print("[dim](no changes)[/dim]")


def show_patch_preview(
    path: str,
    old_string: str,
    new_string: str,
) -> None:
    """Show a preview of what a patch will change."""
    console.print(f"\n[bold]Patch: {path}[/bold]")
    show_diff(old_string, new_string, filename=path)
