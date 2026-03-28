"""API client — connects to Free.ai or BYOK providers."""

from __future__ import annotations

import json
import sys
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from free_code.config import (
    get_api_url,
    get_auth_header,
    load_config,
    PROVIDER_ENDPOINTS,
)
from free_code.models import get_model

DEFAULT_TIMEOUT = 120.0


class CoderClient:
    """API client for the Free.ai Coder agent or direct LLM calls."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or load_config()
        self.provider = self.config.get("provider", "free.ai")
        self.model = get_model(self.config)
        self.api_url = get_api_url(self.config)
        self.headers = get_auth_header(self.config)
        self.headers["Content-Type"] = "application/json"
        self.headers["User-Agent"] = "free-code/0.1.0"

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat completion, yielding parsed events."""
        if self.provider == "free.ai":
            async for event in self._stream_free_ai(messages, system, tools):
                yield event
        elif self.provider == "anthropic":
            async for event in self._stream_anthropic(messages, system, tools):
                yield event
        else:
            # OpenAI-compatible (OpenAI, OpenRouter, Google via compat)
            async for event in self._stream_openai_compat(messages, system, tools):
                yield event

    async def _stream_free_ai(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream from the Free.ai coder agent endpoint."""
        payload: Dict[str, Any] = {
            "messages": messages,
            "model": self.model,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        yield {
                            "type": "error",
                            "content": f"API error {response.status_code}: {body.decode(errors='replace')}",
                        }
                        return

                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        while "\n\n" in buffer:
                            event_str, buffer = buffer.split("\n\n", 1)
                            for line in event_str.strip().split("\n"):
                                if line.startswith("data: "):
                                    data_str = line[6:]
                                    if data_str == "[DONE]":
                                        yield {"type": "done"}
                                        return
                                    try:
                                        yield json.loads(data_str)
                                    except json.JSONDecodeError:
                                        yield {"type": "text", "content": data_str}
        except httpx.ConnectError:
            yield {
                "type": "error",
                "content": "Cannot connect to Free.ai API. Check your internet connection.",
            }
        except httpx.TimeoutException:
            yield {"type": "error", "content": "Request timed out."}

    async def _stream_openai_compat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream from OpenAI-compatible API (OpenAI, OpenRouter)."""
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": all_messages,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        yield {
                            "type": "error",
                            "content": f"API error {response.status_code}: {body.decode(errors='replace')}",
                        }
                        return

                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                yield {"type": "done"}
                                return
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if content := delta.get("content"):
                                    yield {"type": "text", "content": content}
                                if tool_calls := delta.get("tool_calls"):
                                    yield {"type": "tool_calls", "tool_calls": tool_calls}
                            except (json.JSONDecodeError, IndexError, KeyError):
                                pass
        except httpx.ConnectError:
            yield {"type": "error", "content": f"Cannot connect to {self.provider} API."}
        except httpx.TimeoutException:
            yield {"type": "error", "content": "Request timed out."}

    async def _stream_anthropic(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream from Anthropic Messages API."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 8192,
            "stream": True,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        yield {
                            "type": "error",
                            "content": f"API error {response.status_code}: {body.decode(errors='replace')}",
                        }
                        return

                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                event_type = data.get("type", "")
                                if event_type == "content_block_delta":
                                    delta = data.get("delta", {})
                                    if text := delta.get("text"):
                                        yield {"type": "text", "content": text}
                                elif event_type == "message_stop":
                                    yield {"type": "done"}
                                    return
                                elif event_type == "error":
                                    yield {"type": "error", "content": str(data)}
                            except json.JSONDecodeError:
                                pass
        except httpx.ConnectError:
            yield {"type": "error", "content": "Cannot connect to Anthropic API."}
        except httpx.TimeoutException:
            yield {"type": "error", "content": "Request timed out."}

    async def chat_sync(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
    ) -> str:
        """Non-streaming chat completion. Returns full text."""
        chunks = []
        async for event in self.chat_stream(messages, system):
            if event.get("type") == "text":
                chunks.append(event.get("content", ""))
            elif event.get("type") == "error":
                return f"Error: {event.get('content', 'Unknown error')}"
        return "".join(chunks)
