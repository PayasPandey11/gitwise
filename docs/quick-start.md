---
layout: default
title: "Quick Start - GitWise"
---

# Quick Start Guide

Get GitWise up and running in under 5 minutes.

## 📦 Installation

```bash
# Install from PyPI
pip install gitwise

# For offline model support (optional)
pip install "gitwise[offline]"
```

## 🚀 Initial Setup

Run the interactive setup to configure your preferred AI backend:

```bash
gitwise init
```

This will guide you through:
1. Choosing your AI backend (Ollama, Offline, Online through OpenRouter, or Direct Providers like OpenAI, Anthropic, Google Gemini)
2. Configuring API keys or model settings
3. Testing your configuration
4. Saving your preferences

## 🦙 Recommended: Ollama Setup

For the best balance of privacy, quality, and speed:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model
ollama pull llama3

# 3. Configure GitWise (select Ollama when prompted)
gitwise init
```

## ⚡ Your First GitWise Workflow

```bash
# 1. Make some changes
echo "print('Hello, GitWise!')" > hello.py

# 2. Stage changes with summary
gitwise add .
# Shows summary of changes and prompts for next action

# 3. Generate AI commit message
gitwise commit
# AI analyzes your diff and suggests: "feat: add hello world script"

# 4. Push to remote
gitwise push
# Offers to create a PR with AI-generated description

# 5. Create PR with enhancements
gitwise pr --labels --checklist
# Adds relevant labels and context-aware checklist
```

## 🔧 Alternative Backend Options

### 🏠 Offline Mode (No Internet Required)
```bash
pip install "gitwise[offline]"
gitwise init  # Select "Offline (built-in model)"
```

### 🌐 Online Mode (Latest AI Models)
```bash
# Get API key from https://openrouter.ai/
export OPENROUTER_API_KEY="your_api_key"
gitwise init  # Select "Online (OpenRouter API)"
```

### ✨ Direct LLM Providers (OpenAI, Anthropic, Gemini)
For direct integration with your preferred LLM provider:

**OpenAI:**
```bash
export GITWISE_LLM_BACKEND=openai
export OPENAI_API_KEY="your_openai_api_key"
gitwise init # Select "OpenAI"
```

**Anthropic:**
```bash
export GITWISE_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY="your_anthropic_api_key"
gitwise init # Select "Anthropic"
```

**Google Gemini:**
```bash
export GITWISE_LLM_BACKEND=google_gemini
export GOOGLE_API_KEY="your_google_api_key"
gitwise init # Select "Google Gemini"
```

During `gitwise init`, you can select your specific provider and enter the API key when prompted.

## 📋 Essential Commands

| Command | Description |
|---------|-------------|
| `gitwise init` | Initial setup and configuration |
| `gitwise add .` | Stage files with summary |
| `gitwise commit` | AI-generated commit messages |
| `gitwise commit --group` | Split complex changes into multiple commits |
| `gitwise push` | Push with PR creation prompt |
| `gitwise pr --labels --checklist` | Create enhanced PR |
| `gitwise git <cmd>` | Use any git command through gitwise |

## 🛠️ Quick Troubleshooting

**Ollama not working?**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

**Want to switch backends?**
```bash
# Quick switch
export GITWISE_LLM_BACKEND=offline

# Or reconfigure
gitwise init
```

**Need help?**
```bash
gitwise --help
gitwise commit --help
```

---

## 🎯 Next Steps

- **[Features Guide](features.html)** - Learn about advanced features and AI backends
- **[Quick Reference](QUICK_REFERENCE.html)** - Handy command reference
- **[API Documentation](api.html)** - For advanced usage and configuration

---

<div class="success-box">
  <h3>🎉 You're all set!</h3>
  <p>GitWise is now ready to enhance your Git workflow. Start with <code>gitwise add .</code> and let AI help with your commits!</p>
</div> 