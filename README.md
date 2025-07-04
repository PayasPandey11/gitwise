# GitWise: AI-Powered Git Workflow Assistant

[![PyPI version](https://img.shields.io/pypi/v/pygitwise.svg)](https://pypi.org/project/pygitwise/)
[![Python versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/pygitwise/)
[![Documentation](https://img.shields.io/badge/docs-github%20pages-blue)](https://payaspandey11.github.io/gitwise/)

**Stop writing commit messages and PR descriptions by hand. Let AI do it for you.**

GitWise transforms your Git workflow with intelligent AI assistance - from perfect commit messages to comprehensive PR descriptions, all while keeping your code private with local AI models.

## ✨ See the Difference

**Before GitWise** (Manual workflow):
```bash
git add .
git commit -m "fix stuff"  # 😬 Vague, unhelpful
git push
# Write PR description manually... takes 10+ minutes
```

**After GitWise** (Interactive AI workflow):
```bash
gitwise add .
# 🤖 Interactive: Shows changes → Generates commit → Pushes → Creates PR
# Complete workflow in one command with AI assistance at each step
```

*Perfect commits and PRs in seconds, not minutes.*

## 🚀 Quick Start

```bash
# 1. Install
pip install pygitwise

# 2. Initialize (one-time setup)
gitwise init

# 3. Use it like Git, but smarter
gitwise add .       # 🔄 Interactive: stage → commit → push → PR (full workflow)
gitwise commit      # 🤖 AI-generated Conventional Commits  
gitwise merge       # 🧠 Smart merge with AI conflict resolution
gitwise pr          # 📝 Detailed PR with auto-labels & checklists
```

**That's it!** Your commits now follow Conventional Commits, your PRs have detailed descriptions, and everything is generated from your actual code changes.

## 🎯 Why GitWise?

### 🔄 **Complete Workflow**: One command does stage → commit → push → PR
### ⚡ **Lightning Fast**: 15-second full workflow vs 10+ minute manual process  
### 🧠 **Intelligent**: Auto-groups commits, resolves conflicts, generates perfect PRs
### 🔒 **Privacy-First**: Local AI models (Ollama) - your code never leaves your machine
### 🛠️ **Familiar**: Works exactly like Git, just smarter

## 🤖 AI Backend Options

| Backend | Privacy | Quality | Speed | Best For |
|---------|---------|---------|-------|----------|
| **Ollama** (Local) | 🟢 Complete | 🟢 High | 🟢 Fast | Privacy-focused developers |
| **Online** (GPT-4/Claude) | 🟡 API calls | 🟢 Highest | 🟢 Instant | Latest AI capabilities |

Choose local for privacy, online for cutting-edge AI. Switch anytime with `gitwise init`.

## 📦 Installation

### Option 1: Quick Install
```bash
pip install pygitwise
gitwise init
```

### Option 2: Local AI (Recommended)
```bash
# Install Ollama for local AI
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

# Install GitWise
pip install pygitwise
gitwise init  # Select Ollama when prompted
```

### Option 3: Virtual Environment (Best Practice)
```bash
python3 -m venv gitwise-env
source gitwise-env/bin/activate
pip install pygitwise
gitwise init
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
export GITWISE_GEMINI_MODEL="gemini-2.0-flash" # Optional
```

You can also configure these during `gitwise init` by selecting the specific provider. GitWise will automatically install the required dependencies for your chosen provider during initialization.

**Features**:
- Use your own API keys and billing with providers.
- Access to a wide range of models from each provider.
- Potentially more up-to-date model access than through aggregators.
- Internet connection required.
- Required dependencies are automatically installed when you select a provider.

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

#### Smart Merge with AI Conflict Analysis
```bash
# AI-powered merge with conflict resolution assistance
gitwise merge feature/payment-system

# For conflicts, AI explains what's happening:
# 🔍 Analyzing merge: feature/payment-system
# ⚠️ 2 conflicts detected in config.py and requirements.txt
# 🧠 AI explains: "Both branches modified database config..."
# 💡 AI suggests: "Combine both configurations..."
# 🛠️ Manual resolution required - resolve conflicts then:
gitwise merge --continue

# Or abort if needed
gitwise merge --abort
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
export GITWISE_GEMINI_MODEL="gemini-2.0-flash"
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
    "model": "gemini-2.0-flash"
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
export GITWISE_LLM_BACKEND=ollama
gitwise commit  # Now using Ollama mode

# Or reconfigure
gitwise init
```

## 🔥 Key Features

- **🔄 Interactive Workflow**: `gitwise add` does everything - stage → commit → push → PR in one flow
- **🤖 AI Commit Messages**: Generate perfect Conventional Commits from your changes
- **🧠 Smart Auto-Grouping**: Automatically groups related changes into separate commits
- **🔀 Intelligent Merges**: AI-powered conflict analysis and resolution assistance  
- **📝 Smart PR Descriptions**: Detailed descriptions with automated labels and checklists  
- **🔒 Privacy-First**: Local AI models (Ollama) keep your code on your machine
- **⚙️ Git Compatible**: Use as a drop-in replacement for Git commands
- **📊 Changelog Generation**: Automated changelog updates
- **🎯 Context Aware**: Remembers branch context for better suggestions

## 📚 Learn More

- **[📖 Complete Documentation](https://payaspandey11.github.io/gitwise/)** - Full guides and examples
- **[⚡ Quick Reference](https://payaspandey11.github.io/gitwise/QUICK_REFERENCE.html)** - All commands at a glance
- **[🚀 Advanced Features](https://payaspandey11.github.io/gitwise/features.html)** - Power user capabilities

## 🤝 Contributing

Found a bug? Have a feature request? Contributions welcome!

- **Issues**: [GitHub Issues](https://github.com/PayasPandey11/gitwise/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PayasPandey11/gitwise/discussions)

## 📄 License

Dual licensed: AGPL-3.0 for open source projects, Commercial license available for proprietary use.

---

**Ready to transform your Git workflow?** 
```bash
pip install pygitwise && gitwise init
```