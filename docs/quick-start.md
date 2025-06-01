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
1. Choosing your AI backend (Ollama, Offline, or Online)
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

<style>
.success-box {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 6px;
  padding: 1.5rem;
  margin: 2rem 0;
  text-align: center;
}

.success-box h3 {
  color: #155724;
  margin-top: 0;
}

.success-box p {
  color: #155724;
  margin-bottom: 0;
}

table {
  width: 100%;
  margin: 2rem 0;
  border-collapse: collapse;
}

table th,
table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e1e4e8;
}

table th {
  font-weight: 600;
  background-color: #f6f8fa;
}

code {
  background-color: #f6f8fa;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-size: 0.9em;
}

pre code {
  background-color: transparent;
  padding: 0;
}
</style> 