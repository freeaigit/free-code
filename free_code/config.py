"""Configuration management — ~/.free-code/config.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

CONFIG_DIR = Path.home() / ".free-code"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
HISTORY_FILE = CONFIG_DIR / "history"

DEFAULTS: Dict[str, Any] = {
    "provider": "free.ai",
    "model": "qwen2.5-coder-32b",
    "api_url": "https://api.free.ai/coder/",
    "token": None,
    "api_key": None,
    "safe_mode": True,
    "max_context_tokens": 32000,
    "stream": True,
    "auto_commit": False,
    "theme": "monokai",
}

PROVIDER_ENDPOINTS = {
    "free.ai": "https://api.free.ai/coder/",
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "google": "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}

PROVIDER_MODELS = {
    "free.ai": "qwen2.5-coder-32b",
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-2.0-flash",
    "openrouter": "anthropic/claude-sonnet-4-20250514",
}


def ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load config from disk, merged with defaults."""
    config = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                user_config = yaml.safe_load(f) or {}
            config.update(user_config)
        except (yaml.YAMLError, OSError):
            pass
    # Environment variable overrides
    if env_token := os.environ.get("FREE_CODE_TOKEN"):
        config["token"] = env_token
    if env_key := os.environ.get("FREE_CODE_API_KEY"):
        config["api_key"] = env_key
    if env_provider := os.environ.get("FREE_CODE_PROVIDER"):
        config["provider"] = env_provider
    if env_model := os.environ.get("FREE_CODE_MODEL"):
        config["model"] = env_model
    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save config to disk (only non-default values)."""
    ensure_config_dir()
    to_save = {k: v for k, v in config.items() if v != DEFAULTS.get(k)}
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(to_save, f, default_flow_style=False, sort_keys=False)


def get_config_value(key: str) -> Any:
    """Get a single config value."""
    config = load_config()
    return config.get(key)


def set_config_value(key: str, value: str) -> None:
    """Set a single config value with type coercion."""
    config = load_config()
    # Type coercion
    if value.lower() in ("true", "yes", "1"):
        value = True  # type: ignore
    elif value.lower() in ("false", "no", "0"):
        value = False  # type: ignore
    elif value.isdigit():
        value = int(value)  # type: ignore
    config[key] = value
    save_config(config)


def get_api_url(config: Optional[Dict[str, Any]] = None) -> str:
    """Get the API endpoint URL for the configured provider."""
    if config is None:
        config = load_config()
    provider = config.get("provider", "free.ai")
    if provider == "free.ai":
        return config.get("api_url", DEFAULTS["api_url"])
    return PROVIDER_ENDPOINTS.get(provider, config.get("api_url", DEFAULTS["api_url"]))


def get_auth_header(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Get authorization headers for the configured provider."""
    if config is None:
        config = load_config()
    provider = config.get("provider", "free.ai")
    if provider == "free.ai":
        token = config.get("token")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    elif provider == "anthropic":
        key = config.get("api_key", "")
        return {"x-api-key": key, "anthropic-version": "2023-06-01"}
    else:
        key = config.get("api_key", "")
        return {"Authorization": f"Bearer {key}"}
