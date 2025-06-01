# GitWise: Your AI-Powered Git Co-pilot

[![PyPI version](https://badge.fury.io/py/gitwise.svg)](https://pypi.org/project/gitwise/)
[![Python versions](https://img.shields.io/pypi/pyversions/gitwise.svg)](https://pypi.org/project/gitwise/)
[![License](https://img.shields.io/pypi/l/gitwise.svg)](https://github.com/PayasPandey11/gitwise/blob/main/LICENSE)
[![CI Status](https://github.com/PayasPandey11/gitwise/workflows/CI/badge.svg)](https://github.com/PayasPandey11/gitwise/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**GitWise is a command-line tool designed for experienced developers to enhance their Git workflow with intelligent AI assistance. It focuses on speed, efficiency, and integrating seamlessly with your existing habits, while upholding industry best practices.**

Are you a seasoned developer who loves the power of Git but wishes some parts were faster or smarter? GitWise is built for you. We don't replace your Git knowledge; we augment it. GitWise helps you:

- **Craft Perfect Commits, Instantly**: Generate Conventional Commit messages from your staged diffs in seconds.
- **Streamline PR Creation**: Get AI-generated PR titles and descriptions, plus automated label and checklist suggestions.
- **Maintain Changelogs Effortlessly**: Keep your `CHANGELOG.md` up-to-date with minimal fuss.
- **Retain Full Git Control**: Use any standard Git command via `gitwise git ...` with the speed you expect. AI features are opt-in enhancements.

GitWise aims to make your `add -> commit -> push -> PR` cycle more efficient and enjoyable.

## Key Features

- **🚀 Blazing Fast Core**: Standard Git commands passed through `gitwise git ...` run at native Git speed.
- **🧠 Smart Commit Messages**: AI-generated Conventional Commits (opt-in grouping for complex changes via `gitwise commit --group`).
- **✍️ Intelligent PR Descriptions**: AI-generated PR titles and descriptions.
- **🏷️ Automated PR Enhancements**: Optional label suggestions based on commit types and file-specific checklists for PRs.
- **📜 Changelog Management**: Automated updates for unreleased changes and easy generation for new versions.
- **⚙️ Git Command Passthrough**: Use `gitwise` as a wrapper for any `git` command (e.g., `gitwise status`, `gitwise log`).
- **🔒 Privacy-First**: Choose between local (Ollama/Offline) or cloud-based AI backends.

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install gitwise

# For offline model support
pip install "gitwise[offline]"
```

📌 **[Quick Reference Guide](docs/QUICK_REFERENCE.md)** - Keep this handy for all commands and options!

### Initial Setup with `gitwise init`

GitWise offers three AI backend modes. Run `gitwise init` to configure your preferred mode:

```bash
gitwise init
```

This interactive setup will:
1. Let you choose your AI backend (Ollama, Offline, or Online)
2. Configure necessary API keys or model settings
3. Test your configuration
4. Save your preferences

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
pip install "gitwise[offline]"

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

### Mode Comparison

| Feature | Ollama | Offline | Online |
|---------|---------|---------|---------|
| Privacy | 🟢 Full | 🟢 Full | 🔴 API calls |
| Internet | 🟡 Initial only | 🟢 Never | 🔴 Always |
| Quality | 🟢 High | 🟡 Good | 🟢 Best |
| Speed | 🟢 Fast | 🟢 Fast | 🟡 Network dependent |
| Cost | 🟢 Free | 🟢 Free | 🔴 Per use |
| Setup | 🟡 Medium | 🟢 Easy | 🟢 Easy |

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

### `gitwise add [files...]`
- Interactively stage files. 
- Shows a summary of staged files and offers to commit or view the full diff.
- Example: `gitwise add .` or `gitwise add file1.py file2.md`

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

### Example 1: Feature Development Workflow

```bash
# Start a new feature
gitwise checkout -b feature/user-authentication

# Make changes to multiple files
vim src/auth.py src/models/user.py tests/test_auth.py

# Stage and commit with AI assistance
gitwise add .
gitwise commit
# AI suggests: "feat: implement JWT-based user authentication
# 
# - Add User model with password hashing
# - Implement JWT token generation and validation
# - Add login/logout endpoints
# - Include comprehensive test coverage"

# Push and create PR with context
gitwise push
gitwise pr --labels --checklist
# AI creates PR with:
# - Title: "Feature: Add JWT-based user authentication"
# - Labels: enhancement, backend, security
# - Checklist: ✓ Tests added, ✓ Documentation updated, ✓ Security review needed
```

### Example 2: Bug Fix with Grouped Commits

```bash
# Fix a complex bug affecting multiple components
gitwise add -p  # Stage specific hunks

# Use grouped commits for clarity
gitwise commit --group
# AI suggests 3 commits:
# 1. "fix: prevent race condition in cache invalidation"
# 2. "refactor: extract cache logic to separate module"  
# 3. "test: add integration tests for concurrent cache access"

# Update changelog automatically
gitwise changelog --auto-update
```

### Example 3: Release Preparation

```bash
# Generate changelog for new version
gitwise changelog
# AI analyzes commits and suggests version: 2.1.0
# Generates organized changelog with Features, Fixes, etc.

# Create and push release tag
gitwise tag v2.1.0
gitwise push --tags

# Create release PR
gitwise pr --base main --title "Release v2.1.0"
```

## 🔄 Migrating from Other Tools

### From Conventional Commits CLI

```bash
# Before: git add . && git cz
# After:  gitwise add . && gitwise commit

# GitWise provides the same conventional commit structure
# with better context understanding
```

### From GitHub CLI

```bash
# Before: gh pr create --title "..." --body "..."
# After:  gitwise pr

# GitWise generates title and body automatically
# while still using gh CLI under the hood
```

### From Manual Workflows

```bash
# Before: 
# - Think of commit message
# - Write PR description
# - Update changelog
# - Remember to add labels

# After:
# gitwise handles all of this intelligently
```

## 💡 Tips & Best Practices

1. **Commit Message Quality**: GitWise works best when you stage related changes together
2. **PR Descriptions**: The more descriptive your commits, the better the PR description
3. **Changelog Updates**: Use conventional commits for automatic changelog categorization
4. **Performance**: Use Ollama for the best balance of speed and quality
5. **Privacy**: Use offline mode for sensitive codebases

## Development Setup

If you want to contribute to GitWise:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/PayasPandey11/gitwise.git
    cd gitwise
    ```
2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv .venv  # Recommend python3 explicitly
    source .venv/bin/activate
    pip3 install -e ".[dev]" # Recommend pip3 explicitly
    ```
3.  **Run tests:**
    ```bash
    make test # or pytest
    ```
4.  **Check linting & formatting:**
    ```bash
    make format  # Runs black and isort
    make lint    # Runs flake8, black --check, isort --check, mypy
    # Or run directly: 
    # python3 -m black gitwise tests
    # python3 -m isort gitwise tests
    # python3 -m flake8 gitwise tests
    # python3 -m mypy gitwise tests
    ```

## Roadmap & Future Ideas

GitWise is actively developing! Here are some directions we're exploring:

- **Enhanced AI Capabilities**: 
    - AI-assisted interactive rebase (`git rebase -i`).
    - AI-driven diff summaries (`gitwise diff-ai`).
    - Smart stash messages and management.
- **More Local Models**: Support for additional local model backends (LlamaCPP, GPT4All).
- **Model Fine-tuning**: Custom models trained on your codebase patterns.
- **Pre-PR Sanity Checks**: Automated checks for common issues before PR creation.
- **Deeper IDE Integration**: Tighter coupling with IDEs like VS Code.
- **Configuration Flexibility**: Allow users to select LLM models and define custom prompts/behavior via a config file.
- **Team-Specific Workflows**: Features to support team conventions and automation.

Stay tuned, or contribute your own ideas!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Check out our `CONTRIBUTING.md` for guidelines.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.