"""Authentication flow for Free.ai and BYOK providers."""

from __future__ import annotations

import sys
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt

from free_code.config import load_config, save_config, set_config_value

console = Console()


def check_auth(config: Optional[dict] = None) -> bool:
    """Check if the user has valid authentication configured."""
    if config is None:
        config = load_config()
    provider = config.get("provider", "free.ai")
    if provider == "free.ai":
        # Free.ai allows anonymous usage with daily limits
        return True
    # BYOK providers need an API key
    return bool(config.get("api_key"))


def login_flow() -> None:
    """Interactive login flow."""
    config = load_config()
    console.print()
    console.print("[bold]Free.ai Coder — Login[/bold]")
    console.print()

    provider = Prompt.ask(
        "Provider",
        choices=["free.ai", "openai", "anthropic", "google", "openrouter"],
        default="free.ai",
    )

    if provider == "free.ai":
        console.print()
        console.print("Free.ai offers free daily limits with no account required.")
        console.print("For higher limits, get a token at [link=https://free.ai/pricing]https://free.ai/pricing[/link]")
        console.print()
        token = Prompt.ask("Free.ai token (press Enter to skip)", default="")
        if token:
            set_config_value("token", token)
            console.print("[green]Token saved.[/green]")
        else:
            console.print("[dim]Using free anonymous tier.[/dim]")
        set_config_value("provider", "free.ai")
    else:
        console.print()
        key_name = "API key"
        if provider == "openrouter":
            console.print("Get an API key at [link=https://openrouter.ai/keys]https://openrouter.ai/keys[/link]")
        elif provider == "openai":
            console.print("Get an API key at [link=https://platform.openai.com/api-keys]https://platform.openai.com/api-keys[/link]")
        elif provider == "anthropic":
            console.print("Get an API key at [link=https://console.anthropic.com/settings/keys]https://console.anthropic.com/settings/keys[/link]")
        elif provider == "google":
            console.print("Get an API key at [link=https://aistudio.google.com/apikey]https://aistudio.google.com/apikey[/link]")

        api_key = Prompt.ask(f"\n{key_name}")
        if not api_key:
            console.print("[red]API key is required for {provider}.[/red]")
            sys.exit(1)

        set_config_value("provider", provider)
        set_config_value("api_key", api_key)
        console.print(f"[green]Configured {provider} provider.[/green]")

    console.print("[green]Login complete. Run [bold]free-code[/bold] to start coding.[/green]")
