"""SSE streaming display for terminal output."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Callable, Dict, Optional

import httpx
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax

console = Console()


async def stream_sse(
    response: httpx.Response,
) -> AsyncIterator[Dict[str, Any]]:
    """Parse SSE events from an httpx response stream."""
    buffer = ""
    async for chunk in response.aiter_text():
        buffer += chunk
        while "\n\n" in buffer:
            event_str, buffer = buffer.split("\n\n", 1)
            event_data = {}
            for line in event_str.strip().split("\n"):
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        event_data = {"type": "done"}
                    else:
                        try:
                            event_data = json.loads(data_str)
                        except json.JSONDecodeError:
                            event_data = {"type": "text", "content": data_str}
                elif line.startswith("event: "):
                    event_data["event"] = line[7:]
            if event_data:
                yield event_data


def render_streaming_text(text: str, is_code: bool = False, language: str = "python") -> None:
    """Render text content with appropriate formatting."""
    if is_code:
        syntax = Syntax(text, language, theme="monokai", line_numbers=False)
        console.print(syntax)
    else:
        console.print(Markdown(text))


class StreamPrinter:
    """Accumulates streamed text and renders it progressively."""

    def __init__(self) -> None:
        self.buffer = ""
        self.in_code_block = False
        self.code_language = ""
        self.live: Optional[Live] = None

    def feed(self, text: str) -> None:
        """Feed new text from the stream."""
        self.buffer += text

    def flush_line(self) -> Optional[str]:
        """Flush a complete line from the buffer."""
        if "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            return line + "\n"
        return None

    def print_token(self, token: str) -> None:
        """Print a single token to the terminal."""
        console.print(token, end="", highlight=False)

    def finish(self) -> None:
        """Flush remaining buffer."""
        if self.buffer:
            console.print(self.buffer, end="", highlight=False)
            self.buffer = ""
        console.print()  # Final newline
