"""Model routing — select models based on provider and config."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from free_code.config import PROVIDER_MODELS, load_config

# Models available on Free.ai (self-hosted, free tier)
FREE_AI_MODELS = [
    {"id": "qwen2.5-coder-32b", "name": "Qwen 2.5 Coder 32B", "context": 32768, "free": True},
    {"id": "qwen2.5-72b", "name": "Qwen 2.5 72B", "context": 32768, "free": True},
    {"id": "qwen2.5-7b", "name": "Qwen 2.5 7B", "context": 32768, "free": True},
    {"id": "deepseek-coder-v2-lite", "name": "DeepSeek Coder V2 Lite", "context": 16384, "free": True},
    {"id": "mistral-7b", "name": "Mistral 7B", "context": 32768, "free": True},
    {"id": "phi-3", "name": "Phi-3", "context": 4096, "free": True},
]


def get_model(config: Optional[Dict[str, Any]] = None) -> str:
    """Get the model ID to use based on config."""
    if config is None:
        config = load_config()
    model = config.get("model")
    if model:
        return model
    provider = config.get("provider", "free.ai")
    return PROVIDER_MODELS.get(provider, "qwen2.5-coder-32b")


def list_models(provider: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available models for a provider."""
    if provider is None or provider == "free.ai":
        return FREE_AI_MODELS
    # For BYOK providers, return a hint list
    hints = {
        "openai": [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "o3-mini", "name": "o3-mini"},
        ],
        "anthropic": [
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
            {"id": "claude-haiku-3-5-20241022", "name": "Claude 3.5 Haiku"},
        ],
        "google": [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
        ],
        "openrouter": [
            {"id": "anthropic/claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
            {"id": "google/gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
        ],
    }
    return hints.get(provider, [])
