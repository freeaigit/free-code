"""Local tool implementations for the coding agent."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from free_code.tools.file_ops import file_read, file_write, apply_patch
from free_code.tools.shell import shell_command
from free_code.tools.search import grep_search
from free_code.tools.git_ops import git_status, git_diff, git_commit, git_log
from free_code.tools.test_runner import run_tests, detect_test_framework
from free_code.tools.list_files import list_files

# Tool registry — maps tool names to callables
TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "file_read": file_read,
    "file_write": file_write,
    "apply_patch": apply_patch,
    "shell_command": shell_command,
    "grep_search": grep_search,
    "git_status": git_status,
    "git_diff": git_diff,
    "git_commit": git_commit,
    "git_log": git_log,
    "run_tests": run_tests,
    "list_files": list_files,
}

# Tool definitions for the LLM (function calling schema)
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "file_read",
        "description": "Read the contents of a file. Returns the file content as a string.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path"},
                "offset": {"type": "integer", "description": "Line number to start reading from (1-based)"},
                "limit": {"type": "integer", "description": "Maximum number of lines to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "file_write",
        "description": "Write content to a file. Creates the file if it doesn't exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write to"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "apply_patch",
        "description": "Apply a search/replace edit to a file. The old_string must match exactly.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "old_string": {"type": "string", "description": "Exact string to find"},
                "new_string": {"type": "string", "description": "Replacement string"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "shell_command",
        "description": "Execute a shell command and return its output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "cwd": {"type": "string", "description": "Working directory (default: project root)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "grep_search",
        "description": "Search for a pattern in files using ripgrep or grep.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern (regex)"},
                "path": {"type": "string", "description": "Directory or file to search in"},
                "include": {"type": "string", "description": "Glob pattern to filter files (e.g. '*.py')"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "git_status",
        "description": "Show git status of the working directory.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "git_diff",
        "description": "Show git diff of staged and unstaged changes.",
        "parameters": {
            "type": "object",
            "properties": {
                "staged": {"type": "boolean", "description": "Show only staged changes"},
            },
        },
    },
    {
        "name": "git_commit",
        "description": "Create a git commit with the given message.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files to stage (default: all modified)",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "git_log",
        "description": "Show recent git log entries.",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of entries (default: 10)"},
            },
        },
    },
    {
        "name": "run_tests",
        "description": "Run the project's test suite.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Test file or directory"},
                "framework": {"type": "string", "description": "Test framework override (pytest, jest, go, cargo)"},
            },
        },
    },
    {
        "name": "list_files",
        "description": "List files in a directory, respecting .gitignore.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: project root)"},
                "pattern": {"type": "string", "description": "Glob pattern filter (e.g. '*.py')"},
                "max_depth": {"type": "integer", "description": "Maximum directory depth"},
            },
        },
    },
]
