"""CLI entry point — Click commands for free-code."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from free_code import __version__
from free_code.config import (
    CONFIG_FILE,
    get_config_value,
    load_config,
    save_config,
    set_config_value,
)

console = Console()


def get_project_root() -> Path:
    """Determine the project root directory."""
    from free_code.tools.git_ops import git_root

    cwd = Path.cwd()
    root = git_root(str(cwd))
    if root:
        return Path(root)
    return cwd


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="free-code")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Free.ai Coder -- AI coding assistant for your terminal."""
    if ctx.invoked_subcommand is None:
        # Default: interactive chat
        ctx.invoke(chat)


@main.command()
def chat() -> None:
    """Start an interactive coding session."""
    from free_code.agent import Agent
    from free_code.context.repo_map import generate_repo_map
    from free_code.models import get_model
    from free_code.ui.prompt import get_input, setup_history, show_help
    from free_code.ui.terminal import (
        print_error,
        print_info,
        print_markdown,
        print_model_info,
        print_success,
        print_welcome,
    )

    config = load_config()
    project_root = get_project_root()
    agent = Agent(project_root, config)

    print_welcome()
    print_model_info(config.get("provider", "free.ai"), get_model(config))
    console.print(f"  [dim]Project:[/dim] {project_root}")
    console.print()

    setup_history()

    while True:
        try:
            user_input = get_input("you> ")
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break

        if user_input is None:
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            cmd = user_input.split()[0].lower()

            if cmd in ("/quit", "/exit", "/q"):
                console.print("[dim]Goodbye![/dim]")
                break
            elif cmd == "/help":
                show_help()
                continue
            elif cmd == "/clear":
                agent.clear_history()
                print_success("Conversation cleared.")
                continue
            elif cmd == "/compact":
                agent.compact_history()
                print_success("Conversation compacted.")
                continue
            elif cmd == "/model":
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    set_config_value("model", parts[1])
                    config = load_config()
                    agent.client = __import__(
                        "free_code.client", fromlist=["CoderClient"]
                    ).CoderClient(config)
                    print_success(f"Model set to: {parts[1]}")
                else:
                    print_info(f"Current model: {get_model(config)}")
                continue
            elif cmd == "/config":
                _show_config()
                continue
            elif cmd == "/files":
                from free_code.tools.list_files import list_files
                result = list_files(_project_root=str(project_root), max_depth=2)
                console.print(f"[dim]{result}[/dim]")
                continue
            elif cmd == "/repo":
                repo_map = generate_repo_map(project_root)
                console.print(f"[dim]{repo_map}[/dim]")
                continue
            elif cmd == "/diff":
                from free_code.tools.git_ops import git_diff
                result = git_diff(_project_root=str(project_root))
                console.print(f"[dim]{result}[/dim]")
                continue
            elif cmd == "/status":
                from free_code.tools.git_ops import git_status
                result = git_status(_project_root=str(project_root))
                console.print(f"[dim]{result}[/dim]")
                continue
            elif cmd == "/test":
                from free_code.tools.test_runner import run_tests
                parts = user_input.split(maxsplit=1)
                path = parts[1] if len(parts) > 1 else None
                with console.status("Running tests..."):
                    result = run_tests(path=path, _project_root=str(project_root))
                console.print(result)
                continue
            else:
                print_error(f"Unknown command: {cmd}. Type /help for available commands.")
                continue

        # Send to agent
        try:
            asyncio.run(agent.chat(user_input))
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted.[/dim]")
        except Exception as e:
            print_error(f"Agent error: {e}")


@main.command()
@click.argument("question", nargs=-1, required=True)
def ask(question: tuple) -> None:
    """Ask a one-shot question about your codebase."""
    from free_code.agent import Agent
    from free_code.ui.terminal import print_error

    question_str = " ".join(question)
    config = load_config()
    project_root = get_project_root()
    agent = Agent(project_root, config)

    # In ask mode, disable safe_mode for reads (it's one-shot)
    agent.safe_mode = config.get("safe_mode", True)

    try:
        asyncio.run(agent.chat(question_str))
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@main.command()
@click.argument("task", nargs=-1, required=True)
def run(task: tuple) -> None:
    """Execute a coding task (e.g., 'add unit tests for auth module')."""
    from free_code.agent import Agent
    from free_code.ui.terminal import print_error

    task_str = " ".join(task)
    config = load_config()
    project_root = get_project_root()
    agent = Agent(project_root, config)

    console.print(f"\n[bold]Task:[/bold] {task_str}")
    console.print(f"[dim]Project: {project_root}[/dim]\n")

    try:
        asyncio.run(agent.chat(
            f"Execute this task: {task_str}\n\n"
            "Work through it step by step. Read relevant files first, "
            "make the changes, then verify they work."
        ))
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@main.command()
def init() -> None:
    """Initialize free-code in the current project."""
    from free_code.context.discovery import discover_files
    from free_code.context.repo_map import generate_repo_map
    from free_code.tools.git_ops import is_git_repo
    from free_code.tools.test_runner import detect_test_framework
    from free_code.ui.terminal import print_info, print_success, print_warning

    project_root = get_project_root()
    console.print(f"\n[bold]Initializing free-code[/bold] in {project_root}\n")

    # Check git
    if is_git_repo(str(project_root)):
        print_success("Git repository detected")
    else:
        print_warning("Not a git repository")

    # Discover files
    with console.status("Scanning files..."):
        files = discover_files(project_root)
    print_info(f"Found {len(files)} code files")

    # Detect test framework
    framework = detect_test_framework(str(project_root))
    if framework:
        print_info(f"Test framework: {framework}")
    else:
        print_info("No test framework detected")

    # Generate repo map
    with console.status("Generating repository map..."):
        repo_map = generate_repo_map(project_root)

    console.print(f"\n[dim]{repo_map}[/dim]")
    console.print(f"\n[success]Initialization complete. Run [bold]free-code[/bold] to start coding.[/success]\n")


@main.group(invoke_without_command=True)
@click.pass_context
def config(ctx: click.Context) -> None:
    """View or edit configuration."""
    if ctx.invoked_subcommand is None:
        _show_config()


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    from free_code.ui.terminal import print_success

    set_config_value(key, value)
    print_success(f"Set {key} = {value}")


@config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value."""
    value = get_config_value(key)
    if value is not None:
        console.print(f"{key} = {value}")
    else:
        console.print(f"[dim]{key} is not set[/dim]")


@main.command()
def login() -> None:
    """Authenticate with Free.ai or configure a BYOK provider."""
    from free_code.auth import login_flow

    login_flow()


def _show_config() -> None:
    """Display current configuration as a table."""
    cfg = load_config()
    table = Table(title="Configuration", show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    for key, value in sorted(cfg.items()):
        display = str(value)
        # Mask sensitive values
        if key in ("token", "api_key") and value:
            display = display[:8] + "..." if len(display) > 8 else "***"
        table.add_row(key, display)

    table.add_row("[dim]config file[/dim]", f"[dim]{CONFIG_FILE}[/dim]")
    console.print(table)
