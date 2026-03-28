"""Local agent loop — plan, execute, observe."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from free_code.client import CoderClient
from free_code.config import load_config
from free_code.context.repo_map import generate_repo_map
from free_code.context.window import build_context
from free_code.tools import TOOL_DEFINITIONS, TOOL_REGISTRY
from free_code.tools.shell import is_dangerous
from free_code.ui.terminal import (
    confirm,
    print_error,
    print_markdown,
    print_tool_call,
    print_tool_result,
)

console = Console()

SYSTEM_PROMPT = """\
You are Free.ai Coder, an expert AI coding assistant running in the user's terminal.
You have access to their local filesystem and can read, write, and edit files.

## Tools Available
You can use these tools to help the user:
- file_read: Read file contents
- file_write: Write/create files
- apply_patch: Search/replace edit in a file
- shell_command: Execute shell commands
- grep_search: Search for patterns in code
- git_status, git_diff, git_commit, git_log: Git operations
- run_tests: Run the project's test suite
- list_files: List project files

## Guidelines
- Read files before editing them to understand the full context
- Make minimal, focused changes
- Show diffs for significant edits
- Run tests after making changes when appropriate
- Use grep_search to find relevant code before making changes
- Prefer apply_patch over file_write for editing existing files
- Ask for confirmation before destructive operations
- Be concise in explanations, verbose in code

When you need to use a tool, respond with a JSON tool call in this format:
{"tool": "tool_name", "args": {"arg1": "value1"}}

After each tool result, analyze the output and decide the next step.
When you're done, provide a final summary of what was accomplished.
"""

MAX_AGENT_STEPS = 30


class Agent:
    """The coding agent — runs a plan/execute/observe loop."""

    def __init__(
        self,
        project_root: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.config = config or load_config()
        self.client = CoderClient(self.config)
        self.messages: List[Dict[str, str]] = []
        self.safe_mode = self.config.get("safe_mode", True)

    async def chat(self, user_message: str) -> None:
        """Process a user message through the agent loop."""
        # Build context on first message
        if not self.messages:
            context, included = build_context(
                self.project_root,
                user_message,
                max_tokens=self.config.get("max_context_tokens", 32000),
            )
            system = SYSTEM_PROMPT + f"\n\n## Project Context\n\n{context}"
        else:
            system = None

        self.messages.append({"role": "user", "content": user_message})

        for step in range(MAX_AGENT_STEPS):
            # Get LLM response
            response_text = await self._get_response(system)
            system = None  # Only send system on first turn

            if not response_text:
                break

            # Check for tool calls in the response
            tool_call = self._extract_tool_call(response_text)

            if tool_call:
                tool_name = tool_call["tool"]
                tool_args = tool_call.get("args", {})

                # Print any text before the tool call
                pre_text = response_text[:response_text.find('{"tool"')].strip()
                if pre_text:
                    print_markdown(pre_text)

                # Execute the tool
                result = await self._execute_tool(tool_name, tool_args)

                if result is None:
                    # Tool was cancelled by user
                    self.messages.append({
                        "role": "assistant",
                        "content": response_text,
                    })
                    self.messages.append({
                        "role": "user",
                        "content": "(Tool execution cancelled by user)",
                    })
                    continue

                # Add assistant message and tool result
                self.messages.append({
                    "role": "assistant",
                    "content": response_text,
                })
                self.messages.append({
                    "role": "user",
                    "content": f"[Tool result for {tool_name}]:\n{result}",
                })
            else:
                # No tool call — this is the final response
                print_markdown(response_text)
                self.messages.append({
                    "role": "assistant",
                    "content": response_text,
                })
                break

    async def _get_response(self, system: Optional[str] = None) -> str:
        """Get a streaming response from the LLM."""
        chunks: List[str] = []
        spinner = Spinner("dots", text="Thinking...")

        with Live(spinner, console=console, refresh_per_second=10, transient=True):
            first_chunk = True
            async for event in self.client.chat_stream(self.messages, system=system):
                event_type = event.get("type", "")

                if event_type == "text":
                    content = event.get("content", "")
                    if first_chunk:
                        first_chunk = False
                    chunks.append(content)

                elif event_type == "error":
                    print_error(event.get("content", "Unknown error"))
                    return ""

                elif event_type == "done":
                    break

        return "".join(chunks)

    def _extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a tool call JSON from the response text."""
        # Look for {"tool": "..."} pattern
        start = text.find('{"tool"')
        if start == -1:
            return None

        # Find the matching closing brace
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(text[start:i + 1])
                        if "tool" in data:
                            return data
                    except json.JSONDecodeError:
                        pass
                    break
        return None

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> Optional[str]:
        """Execute a tool and return the result. Returns None if cancelled."""
        if tool_name not in TOOL_REGISTRY:
            return f"Error: Unknown tool: {tool_name}"

        # Safety checks
        if self.safe_mode:
            if tool_name in ("file_write", "apply_patch", "git_commit"):
                print_tool_call(tool_name, tool_args)
                if not confirm("Apply this change?"):
                    return None

            if tool_name == "shell_command":
                cmd = tool_args.get("command", "")
                print_tool_call(tool_name, tool_args)
                if is_dangerous(cmd):
                    console.print("[warning]This command could be dangerous.[/warning]")
                if not confirm(f"Run: {cmd}"):
                    return None
        else:
            # Even in non-safe mode, confirm dangerous shell commands
            if tool_name == "shell_command" and is_dangerous(tool_args.get("command", "")):
                print_tool_call(tool_name, tool_args)
                if not confirm("This command could be dangerous. Run anyway?"):
                    return None

        if tool_name not in ("file_write", "apply_patch", "shell_command", "git_commit") or not self.safe_mode:
            print_tool_call(tool_name, tool_args)

        # Inject project root
        tool_args["_project_root"] = str(self.project_root)

        # Execute
        func = TOOL_REGISTRY[tool_name]
        try:
            result = func(**tool_args)
        except TypeError as e:
            # Handle unexpected keyword arguments
            tool_args_clean = {k: v for k, v in tool_args.items() if not k.startswith("_")}
            tool_args_clean["_project_root"] = str(self.project_root)
            try:
                result = func(**tool_args_clean)
            except Exception as e2:
                result = f"Error executing {tool_name}: {e2}"
        except Exception as e:
            result = f"Error executing {tool_name}: {e}"

        print_tool_result(result, collapsed=len(str(result)) > 1000)
        return str(result)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()

    def compact_history(self) -> None:
        """Summarize conversation to save context."""
        if len(self.messages) <= 2:
            return
        # Keep first and last 4 messages, summarize the middle
        kept = self.messages[:1] + self.messages[-4:]
        summary = f"(Previous conversation with {len(self.messages)} messages was compacted)"
        self.messages = [{"role": "user", "content": summary}] + kept
