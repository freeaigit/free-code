# Free.ai Coder

Free AI coding assistant for your terminal. A free, open-source alternative to Claude Code, Cursor, and GitHub Copilot.

**[Website](https://free.ai/coder/)** | **[PyPI](https://pypi.org/project/freeai-code/)** | **[npm](https://www.npmjs.com/package/freeai-code)** | **[Web IDE](https://free.ai/coder/)**

## Install

```bash
# Universal (Linux / macOS)
curl -fsSL https://free.ai/install | sh

# pip
pip install freeai-code

# npm
npm install -g freeai-code
```

## Quick Start

```bash
# Interactive coding session in your project directory
cd your-project/
free-code

# Ask a one-shot question about your codebase
free-code ask "How does the auth system work?"

# Execute a task
free-code run "Add unit tests for the User model"

# Initialize and scan codebase
free-code init
```

## Commands

| Command | Description |
|---------|-------------|
| `free-code` | Interactive coding session (alias: `free-code chat`) |
| `free-code ask "question"` | One-shot question about the codebase |
| `free-code run "task"` | Execute a coding task |
| `free-code init` | Initialize config, scan codebase |
| `free-code config` | Show current configuration |
| `free-code config set key value` | Set a config value |
| `free-code login` | Authenticate with Free.ai |

## Features

- File read/write with diff preview and approval gates
- Shell command execution (with confirmation in safe mode)
- Git integration (status, diff, commit, branch)
- Test runner auto-detection (pytest, jest, go test, cargo test)
- Streaming output with syntax highlighting
- Context window optimization and repo map generation
- .gitignore-aware file discovery
- Session sync — continue conversations from [web](https://free.ai/coder/) to CLI and back

## Configuration

Config is stored at `~/.free-code/config.yaml`.

```bash
# Set your Free.ai token (get one at https://free.ai/account/)
free-code config set token sk-free-xxx

# Use your own API key (BYOK — no markup, use your own provider)
free-code config set provider openai
free-code config set api_key sk-xxx

# Choose a model
free-code config set model qwen2.5-coder-32b

# Enable safe mode (confirm before file writes)
free-code config set safe_mode true
```

### Supported Providers

| Provider | Default Model | Free Tier |
|----------|--------------|-----------|
| **free.ai** (default) | Qwen 2.5 Coder 32B | 50K tokens/day |
| **openai** | GPT-4o | BYOK — no markup |
| **anthropic** | Claude Sonnet 4 | BYOK — no markup |
| **google** | Gemini 2.5 Pro | BYOK — no markup |
| **openrouter** | 346+ models | BYOK — no markup |

## How It Works

1. Scans your project (respects .gitignore)
2. Builds a context map of your codebase
3. Sends your request + relevant code context to the AI
4. AI plans steps, reads/writes files, runs commands
5. You review and approve changes (safe mode)

All file operations happen locally on your machine. The AI sees only what it needs.

## Pricing

- **Anonymous**: 10K tokens/day (Qwen Coder only)
- **Free account**: 50K tokens/day (sign up at [free.ai](https://free.ai/signup/))
- **Paid plans**: From $5/month for 200K tokens ([pricing](https://free.ai/pricing/))
- **BYOK**: $0 — bring your own API key, no markup

## Links

- [Free.ai](https://free.ai) — 400+ free AI tools
- [Web IDE](https://free.ai/coder/) — Use in your browser
- [API Docs](https://free.ai/api/) — Build on top of Free.ai
- [Compare vs Claude Code](https://free.ai/compare/coder-vs-claude-code/)
- [Compare vs Cursor](https://free.ai/compare/coder-vs-cursor/)

## License

MIT
