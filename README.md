# free-code

Free AI coding assistant for your terminal. Powered by [Free.ai](https://free.ai).

## Install

```bash
pip install free-code
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

## Configuration

Config is stored at `~/.free-code/config.yaml`.

```bash
# Set your Free.ai token
free-code config set token sk-free-xxx

# Use your own API key (BYOK)
free-code config set provider openai
free-code config set api_key sk-xxx

# Choose a model
free-code config set model qwen2.5-coder-32b

# Enable safe mode (confirm before file writes)
free-code config set safe_mode true
```

### Supported Providers

- **free.ai** (default) — Free tier with daily limits, paid plans for more
- **openai** — Bring your own OpenAI API key
- **anthropic** — Bring your own Anthropic API key
- **google** — Bring your own Google AI API key
- **openrouter** — Access 300+ models with one key

## Features

- Reads and edits files in your project
- Shell command execution (with confirmation)
- Git integration (status, diff, commit, branch)
- Test runner auto-detection (pytest, jest, go test, cargo test)
- Streaming output with syntax highlighting
- Context window optimization
- .gitignore-aware file discovery

## License

MIT
