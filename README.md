# GitWise: Your AI-Powered Git Co-pilot

[![PyPI version](https://img.shields.io/pypi/v/pygitwise.svg)](https://pypi.org/project/pygitwise/)
[![TestPyPI version](https://img.shields.io/badge/TestPyPI-v0.1.0-blue)](https://test.pypi.org/project/pygitwise/)
[![Python versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/pygitwise/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/PayasPandey11/gitwise/blob/main/LICENSE)
[![codecov](https://codecov.io/gh/PayasPandey11/gitwise/branch/main/graph/badge.svg)](https://codecov.io/gh/PayasPandey11/gitwise)
[![CI Status](https://github.com/PayasPandey11/gitwise/workflows/CI/badge.svg)](https://github.com/PayasPandey11/gitwise/actions)
[![Documentation](https://img.shields.io/badge/docs-github%20pages-blue)](https://payaspandey11.github.io/gitwise/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**GitWise is a command-line tool designed for experienced developers to enhance their Git workflow with intelligent AI assistance. It focuses on speed, efficiency, and integrating seamlessly with your existing habits, while upholding industry best practices.**

> 📖 **[Complete Documentation & Getting Started Guide →](https://payaspandey11.github.io/gitwise/)**

Are you a seasoned developer who loves the power of Git but wishes some parts were faster or smarter? GitWise is built for you. We don't replace your Git knowledge; we augment it. GitWise helps you:

- **Craft Perfect Commits, Instantly**: Generate Conventional Commit messages from your staged diffs in seconds.
- **Streamline PR Creation**: Get AI-generated PR titles and descriptions, plus automated label and checklist suggestions.
- **Maintain Changelogs Effortlessly**: Keep your `CHANGELOG.md` up-to-date with minimal fuss.
- **Retain Full Git Control**: Use any standard Git command via `gitwise git ...` with the speed you expect. AI features are opt-in enhancements.

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install pygitwise

# For offline model support
pip install "pygitwise[offline]"
```

📌 **[Quick Reference Guide →](https://payaspandey11.github.io/gitwise/QUICK_REFERENCE.html)** - Keep this handy for all commands and options!

### Your First GitWise Workflow

```bash
# 1. Initialize GitWise (first time only)
gitwise init

# 2. Make your code changes
echo "print('Hello, GitWise!')" > hello.py

# 3. Stage changes interactively
gitwise add .
# Shows summary of changes and prompts for next action

# 4. Generate AI-powered commit message
gitwise commit
# AI analyzes your diff and suggests: "feat: add hello world script"

# 5. Push and create PR
gitwise push
gitwise pr --labels --checklist
```

## 🤖 Three AI Backend Modes

| Mode | Best For | Privacy | Internet |
|------|----------|---------|----------|
| **🦙 Ollama** | High-quality local AI | 🟢 Full | 🟡 Setup only |
| **🏠 Offline** | Air-gapped environments | 🟢 Full | 🟢 Never |
| **🌐 Online** | Latest AI models (GPT-4, Claude) | 🔴 API calls | 🔴 Always |

**[→ Learn more about AI backends](https://payaspandey11.github.io/gitwise/features.html#three-ai-backend-modes)**

## Key Features

- **🚀 Blazing Fast Core**: Standard Git commands passed through `gitwise git ...` run at native Git speed.
- **🧠 Smart Commit Messages**: AI-generated Conventional Commits (opt-in grouping for complex changes via `gitwise commit --group`).
- **⚡ Streamlined Workflow**: Auto-confirm mode (`gitwise add -y`) for fully automated stage → commit → push → PR workflow.
- **✍️ Intelligent PR Descriptions**: AI-generated PR titles and descriptions.
- **🏷️ Automated PR Enhancements**: Optional label suggestions based on commit types and file-specific checklists for PRs.
- **📜 Changelog Management**: Automated updates for unreleased changes and easy generation for new versions.
- **⚙️ Git Command Passthrough**: Use `gitwise` as a wrapper for any `git` command (e.g., `gitwise status`, `gitwise log`).
- **🔒 Privacy-First**: Choose between local (Ollama/Offline) or cloud-based AI backends.

## 📖 Documentation

For comprehensive documentation, advanced features, troubleshooting, and real-world examples:

- **[🌐 GitWise Documentation](https://payaspandey11.github.io/gitwise/)** - Complete documentation site
- **[🚀 Quick Start Guide](https://payaspandey11.github.io/gitwise/quick-start.html)** - Get up and running in 5 minutes
- **[⚡ Features & Advanced Usage](https://payaspandey11.github.io/gitwise/features.html)** - Deep dive into all capabilities
- **[📋 Quick Reference](https://payaspandey11.github.io/gitwise/QUICK_REFERENCE.html)** - Handy command reference
- **[🔧 API Documentation](https://payaspandey11.github.io/gitwise/api.html)** - For developers and contributors


#### ⚠️ Command Not Found? (PATH issues)
If you see a warning like:

```
WARNING: The script gitwise is installed in '/Users/yourname/Library/Python/3.x/bin' which is not on PATH.
```

This means the `gitwise` command is not available in your terminal by default. To fix this, add the following to your shell config (replace `3.x` with your Python version):

```sh
export PATH="$PATH:/Users/$(whoami)/Library/Python/3.x/bin"
```

Add this line to your `~/.zshrc` or `~/.bash_profile` and restart your terminal, or run it directly in your current session.

- On Linux, the user base bin is usually `~/.local/bin`.
- On Windows, add the Scripts directory to your PATH (see Python docs).

---

#### ✅ Recommended: Use a Virtual Environment
For the best experience, use a [virtual environment](https://docs.python.org/3/tutorial/venv.html):

```sh
python3 -m venv venv
source venv/bin/activate
pip install pygitwise
```

This ensures the `gitwise` command is always available when the venv is activated.

📌 **[Quick Reference Guide](docs/QUICK_REFERENCE.md)** - Keep this handy for all commands and options!

```bash
# Install Ollama first
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Configure GitWise to use Ollama
gitwise init
# Select: Ollama (local server)
```

**[→ Complete setup guide for all backends](https://payaspandey11.github.io/gitwise/quick-start.html)**

## 🤖 AI Backend Modes

GitWise supports three distinct AI backends, each with unique advantages:

### 1. 🦙 Ollama Mode (Default - Recommended)

**Best for**: Privacy-conscious developers who want high-quality local AI with easy model management.

```bash
# Install Ollama first
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Configure GitWise to use Ollama
gitwise init
# Select: Ollama (local server)
```

**Features**:
- Runs 100% locally on your machine
- No internet required after model download
- Easy model switching (`ollama pull codellama`, `ollama pull mistral`)
- High-quality models (Llama 3, Mistral, CodeLlama, etc.)
- Zero cost after initial setup

**Configuration**:
```bash
export GITWISE_LLM_BACKEND=ollama
export OLLAMA_MODEL=llama3  # or codellama, mistral, etc.
```

### 2. 🏠 Offline Mode

**Best for**: Maximum privacy, air-gapped environments, or when Ollama isn't available.

```bash
# Install with offline support
pip install "pygitwise[offline]"

# Configure GitWise
gitwise init
# Select: Offline (built-in model)
```

**Features**:
- Runs 100% locally with bundled model
- No external dependencies
- Works in air-gapped environments
- Smaller, faster models (TinyLlama by default)
- Automatic fallback when Ollama unavailable

**Configuration**:
```bash
export GITWISE_LLM_BACKEND=offline
export GITWISE_OFFLINE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # optional
```

### 3. 🌐 Online Mode (OpenRouter)

**Best for**: Access to cutting-edge models (GPT-4, Claude) and highest quality outputs.

```bash
# Get your API key from https://openrouter.ai/
export OPENROUTER_API_KEY="your_api_key"

# Configure GitWise
gitwise init
# Select: Online (OpenRouter API)
# Enter your API key when prompted
```

**Features**:
- Access to latest AI models (GPT-4, Claude 3, etc.)
- Highest quality outputs
- No local GPU required
- Pay-per-use pricing
- Internet connection required

**Configuration**:
```bash
export GITWISE_LLM_BACKEND=online
export OPENROUTER_API_KEY="your_api_key"
export OPENROUTER_MODEL="anthropic/claude-3-haiku"  # optional
```

### 4. ⚡ Direct LLM Provider Mode

**Best for**: Using your preferred LLM provider (OpenAI, Anthropic, Google Gemini) directly with your own API keys.

GitWise now offers direct integration with major LLM providers, allowing you to use your existing accounts and preferred models.

**Supported Providers:**
- **OpenAI**: Access models like GPT-4, GPT-3.5-turbo, etc.
- **Anthropic**: Access Claude models like Claude 3 Opus, Sonnet, Haiku.
- **Google Gemini**: Access Gemini models like Gemini Pro.

**Configuration:**

To use a direct provider, set the `GITWISE_LLM_BACKEND` environment variable to `openai`, `anthropic`, or `google_gemini`, and provide the respective API key.

**OpenAI:**
```bash
export GITWISE_LLM_BACKEND=openai
export OPENAI_API_KEY="your_openai_api_key"
export GITWISE_OPENAI_MODEL="gpt-4" # Optional, defaults to a recommended model
```

**Anthropic:**
```bash
export GITWISE_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export GITWISE_ANTHROPIC_MODEL="claude-3-opus-20240229" # Optional
```

**Google Gemini:**
```bash
export GITWISE_LLM_BACKEND=google_gemini
export GOOGLE_API_KEY="your_google_api_key"
export GITWISE_GEMINI_MODEL="gemini-pro" # Optional
```

You can also configure these during `gitwise init` by selecting the specific provider.

**Features**:
- Use your own API keys and billing with providers.
- Access to a wide range of models from each provider.
- Potentially more up-to-date model access than through aggregators.
- Internet connection required.

### Mode Comparison

| Feature | Ollama | Offline | Online (OpenRouter) | Direct LLM (OpenAI, Anthropic, Gemini) |
|---------|---------|---------|---------|---------------------------------------|
| Privacy | 🟢 Full | 🟢 Full | 🔴 API calls | 🔴 API calls to provider             |
| Internet | 🟡 Initial only | 🟢 Never | 🔴 Always | 🔴 Always                             |
| Quality | 🟢 High | 🟡 Good | 🟢 Best | 🟢 Provider-dependent (Best available) |
| Speed | 🟢 Fast | 🟢 Fast | 🟡 Network dependent | 🟡 Network dependent                  |
| Cost | 🟢 Free | 🟢 Free | 🔴 Per use | 🔴 Per use (Provider billing)        |
| Setup | 🟡 Medium | 🟢 Easy | 🟢 Easy | 🟢 Easy (API key)                    |

## 📖 Usage Examples

### Basic Workflow

```bash
# 1. Initialize GitWise (first time only)
gitwise init

# 2. Make your code changes
echo "print('Hello, GitWise!')" > hello.py

# 3. Stage changes interactively
gitwise add .
# Shows summary of changes and prompts for next action

# 4. Generate AI-powered commit message
gitwise commit
# AI analyzes your diff and suggests: "feat: add hello world script"

# 5. Push and create PR
gitwise push
# Offers to create a PR with AI-generated description

# 6. Create PR with labels and checklist
gitwise pr --labels --checklist
```

### Streamlined Workflow (Auto-Confirm Mode)

```bash
# Perfect for rapid development or CI/CD environments
# Make your code changes
echo "print('Hello, GitWise!')" > hello.py

# One command does it all: stage → commit → push → PR
gitwise add . --yes
# ✅ Stages files
# ✅ Auto-commits with AI-generated message and grouping
# ✅ Auto-pushes changes  
# ✅ Auto-creates PR with labels and checklist
# 🛡️ Skips PR creation if on main/master branch

# Alternative short form
gitwise add . -y
```

### Advanced Features

#### Group Complex Changes
```bash
# When you have multiple logical changes
gitwise commit --group
# AI suggests splitting into multiple commits:
# 1. "refactor: extract user validation logic"
# 2. "feat: add email verification"
# 3. "test: add user validation tests"
```

#### Changelog Management
```bash
# Update changelog before release
gitwise changelog
# Suggests version based on commits (e.g., 1.2.0)
# Generates categorized changelog entries

# Auto-update changelog on every commit
gitwise setup-hooks
```

#### Git Command Passthrough
```bash
# Use any git command through gitwise
gitwise status
gitwise log --oneline -5
gitwise branch -a
gitwise stash list
```

## 🔧 Configuration

### Environment Variables

```bash
# Core settings
export GITWISE_LLM_BACKEND=ollama  # ollama, offline, or online
export GITWISE_CONFIG_PATH=~/.gitwise/config.json  # custom config location

# Ollama settings
export OLLAMA_MODEL=llama3
export OLLAMA_URL=http://localhost:11434  # custom Ollama server

# Offline settings
export GITWISE_OFFLINE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Online settings
export OPENROUTER_API_KEY="your_api_key"
export OPENROUTER_MODEL="anthropic/claude-3-haiku"

# Direct Provider Settings
# OpenAI
export GITWISE_LLM_BACKEND=openai
export OPENAI_API_KEY="your_openai_api_key"
export GITWISE_OPENAI_MODEL="gpt-4"
# Anthropic
export GITWISE_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export GITWISE_ANTHROPIC_MODEL="claude-3-opus-20240229"
# Google Gemini
export GITWISE_LLM_BACKEND=google_gemini
export GOOGLE_API_KEY="your_google_api_key"
export GITWISE_GEMINI_MODEL="gemini-pro"
```

### Configuration File

After running `gitwise init`, your settings are saved in `~/.gitwise/config.json`:

```json
{
  "llm_backend": "ollama",
  "ollama": {
    "model": "llama3",
    "url": "http://localhost:11434"
  },
  "offline": {
    "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
  },
  "online": {
    "api_key": "your_api_key",
    "model": "anthropic/claude-3-haiku"
  },
  "openai": {
    "api_key": "your_openai_api_key",
    "model": "gpt-4"
  },
  "anthropic": {
    "api_key": "your_anthropic_api_key",
    "model": "claude-3-opus-20240229"
  },
  "google_gemini": {
    "api_key": "your_google_api_key",
    "model": "gemini-pro"
  }
}
```

## 🛠️ Troubleshooting

### Ollama Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve

# List available models
ollama list

# Pull a new model
ollama pull codellama
```

### Switching Backends

```bash
# Quick switch via environment variable
export GITWISE_LLM_BACKEND=offline
gitwise commit  # Now using offline mode

# Or reconfigure
gitwise init
```

### Performance Tips

1. **For faster responses**: Use Ollama with smaller models like `llama3` or `codellama`
2. **For best quality**: Use online mode with Claude or GPT-4
3. **For air-gapped environments**: Use offline mode with the bundled model

## 📊 Detailed Command Reference

GitWise commands are designed to be intuitive. Here are the main ones:

### `gitwise add [files...] [--yes]`
- Interactively stage files. 
- Shows a summary of staged files and offers to commit or view the full diff.
- `--yes` (or `-y`): **Auto-confirm mode** - Automatically answers "yes" to all prompts for a streamlined, non-interactive workflow:
  - ✅ Enables automatic commit grouping 
  - ✅ Auto-pushes changes after commit
  - ✅ Auto-creates PR with labels and checklist (skipped if on main/master branch)
  - 🛡️ **Special behavior**: When on main/master branch, skips PR creation entirely
- Example: `gitwise add .` (interactive mode)
- Example: `gitwise add . --yes` (auto-confirm mode - perfect for CI/CD or rapid development)
- Example: `gitwise add file1.py file2.md -y` (auto-confirm with specific files)

### `gitwise commit [--group]`
- Generates an AI-powered Conventional Commit message for your staged changes.
- You can review, edit, or regenerate the message before committing.
- Use `--group` (or `-g`) for GitWise to analyze changes and suggest breaking them into multiple logical commits. This is powerful for refactoring or large feature work but can be slower due to more LLM calls.
- Example: `gitwise commit` (for a single smart commit)
- Example: `gitwise commit --group` (to try grouping)

### `gitwise push`
- Pushes your committed changes to the remote repository.
- Prompts to create a Pull Request after a successful push.

### `gitwise pr [--labels] [--checklist] [--base <branch>] [--title <title>] [--draft]`
- Creates a Pull Request on GitHub (requires `gh` CLI to be installed and authenticated).
- AI generates the PR title (if not provided) and a descriptive body based on your commits.
- `--labels`: Suggests relevant labels (e.g., bug, feature) based on commit types.
- `--checklist`: Adds a context-aware checklist to the PR body based on changed file types (e.g., reminders for tests, docs for Python files).
- Example: `gitwise pr --labels --checklist --base develop`

### `gitwise changelog [--version <version>] [--output-file <file>]`
- Generates or updates your `CHANGELOG.md`.
- **For New Releases**: Run `gitwise changelog`. It will suggest a semantic version based on your recent commits. Confirm or provide a version (e.g., `v1.2.3`). The AI will generate entries for this version. The command will also offer to create a git tag for the version.
- **Automatic Unreleased Section**: To automatically update an `[Unreleased]` section in your `CHANGELOG.md` before each commit, run `gitwise setup-hooks`. This installs a Git pre-commit hook script that calls `gitwise changelog --auto-update` and stages `CHANGELOG.md` if it was modified. 
    - **Note for `pre-commit` framework users**: If you use the [pre-commit](https://pre-commit.com/) framework, you should integrate `gitwise changelog --auto-update` into your existing `.pre-commit-config.yaml` instead of using `gitwise setup-hooks`.
- **Best Practice**: Use [Conventional Commit](https://www.conventionalcommits.org/) messages (e.g., `feat: ...`, `fix: ...`) for the best changelog results.

### `gitwise setup-hooks`
- Installs a Git pre-commit script (`.git/hooks/pre-commit`) that attempts to run `gitwise changelog --auto-update` before each commit. 
- This helps maintain an up-to-date pending changelog. 
- If you use the `pre-commit` framework, manage GitWise through your `.pre-commit-config.yaml` instead.

### `gitwise git <git_command_and_args...>`
- A direct passthrough to any standard `git` command.
- Useful if you want to stay within the `gitwise` CLI but need a specific Git command.
- Output is streamed directly from Git. If you are using a command that pages (e.g., `git log`, `git diff`) and need script-friendly output, you should pipe it manually (e.g., `gitwise git log | cat`). If running `gitwise` via a GitHub CLI alias (`gh alias set gw --shell 'gitwise $1'`), `gh` may handle paging for you.
- Example: `gitwise git status -sb`, `gitwise git log --oneline -n 5`

## 🌟 Real-World Examples

### Feature Development Workflow

```bash
# Start a new feature
gitwise checkout -b feature/user-authentication

# Make changes to multiple files
vim src/auth.py src/models/user.py tests/test_auth.py

# Stage and commit with AI assistance
gitwise add .
gitwise commit
# AI suggests: "feat: implement JWT-based user authentication"

# Push and create PR with context
gitwise push
gitwise pr --labels --checklist
```

### Bug Fix with Grouped Commits

```bash
# Use grouped commits for clarity
gitwise commit --group
# AI suggests 3 commits:
# 1. "fix: prevent race condition in cache invalidation"
# 2. "refactor: extract cache logic to separate module"  
# 3. "test: add integration tests for concurrent cache access"
```

**[→ More examples and advanced workflows](https://payaspandey11.github.io/gitwise/features.html#real-world-workflows)**

## 💡 Quick Tips

1. **Commit Message Quality**: GitWise works best when you stage related changes together
2. **Performance**: Use Ollama for the best balance of speed and quality
3. **Privacy**: Use offline mode for sensitive codebases
4. **Streamlined Workflow**: Use `gitwise add . -y` for a fully automated workflow (stage → commit → push → PR)
5. **Advanced Features**: Use `gitwise commit --group` for complex changes
6. **PR Enhancement**: Always use `--labels --checklist` for better PRs

## 🛠️ Development & Contributing

If you want to contribute to GitWise:

```bash
git clone https://github.com/PayasPandey11/gitwise.git
cd gitwise
python3 -m venv .venv
source .venv/bin/activate
pip3 install -e ".[dev]"
make test
```

**[→ Full development setup guide](https://payaspandey11.github.io/gitwise/api.html)**

## 🚀 Roadmap

GitWise is actively developing! Here are some directions we're exploring:

- **Enhanced AI Capabilities**: AI-assisted interactive rebase, smart stash messages
- **More Local Models**: Support for LlamaCPP, GPT4All backends  
- **Model Fine-tuning**: Custom models trained on your codebase patterns
- **IDE Integration**: Tighter coupling with VS Code and other editors
- **Team Workflows**: Features to support team conventions and automation

**[→ Complete roadmap and feature requests](https://github.com/PayasPandey11/gitwise/issues)**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**[📖 Documentation](https://payaspandey11.github.io/gitwise/) • [🚀 Quick Start](https://payaspandey11.github.io/gitwise/quick-start.html) • [💬 Issues](https://github.com/PayasPandey11/gitwise/issues) • [🤝 Contributing](CONTRIBUTING.md)**
</div>
This project is licensed under the MIT License - see the `LICENSE` file for details.
