---
layout: default
title: "Quick Start - GitWise"
---

# Quick Start Guide

Get GitWise running in 2 minutes and transform your Git workflow immediately.

## 📦 Installation

### Option 1: Quick Install (Fastest)
```bash
pip install pygitwise
gitwise init
```

### Option 2: Local AI (Recommended for Privacy)
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

## 🚀 First Workflow

After installation, try GitWise on any Git repository:

```bash
# Navigate to your project
cd your-project

# Make some changes
echo "console.log('Hello GitWise!');" > test.js

# Use GitWise workflow
gitwise add .       # Interactive staging
gitwise commit      # AI generates: "feat: add hello world console output"
gitwise push        # Push to remote
gitwise pr          # Create PR with AI description
```

That's it! You now have perfect commits and PRs.

## 🤖 Choose Your AI Backend

During `gitwise init`, you'll choose an AI backend:

### 🦙 Ollama (Local) - Recommended
- **Privacy**: 🟢 Complete - Code never leaves your machine
- **Speed**: 🟢 Fast after initial setup
- **Quality**: 🟢 High
- **Cost**: 🟢 Free

**Setup:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
gitwise init  # Select Ollama
```

### 🌐 Online (GPT-4/Claude) - Latest AI
- **Privacy**: 🟡 API calls to providers
- **Speed**: 🟢 Instant
- **Quality**: 🟢 Highest
- **Cost**: 💰 Pay per use

**Setup:**
```bash
gitwise init  # Select Online, enter API key
```

## ⚡ Essential Commands

Once setup is complete, these are your main commands:

| Command | What It Does |
|---------|--------------|
| `gitwise add .` | Interactive file staging with AI insights |
| `gitwise commit` | Generate perfect Conventional Commits |
| `gitwise push` | Push with optional PR creation |
| `gitwise pr` | Create detailed PRs with labels & checklists |
| `gitwise init` | Change AI backend or reconfigure |

## 🎯 Pro Tips

### Speed Up Your Workflow
```bash
# Auto-confirm mode for faster workflow
gitwise add . --yes
gitwise commit --yes
gitwise push --yes
```

### Better PR Creation
```bash
# Create PR with labels and checklist automatically
gitwise pr --labels --checklist

# Create draft PR for review
gitwise pr --draft
```

### Context for Better AI
```bash
# Set context for better commit messages
gitwise set-context "Working on user authentication system"
```

## 🔧 Troubleshooting

### Command Not Found
If `gitwise` command is not found, add to your PATH:

**macOS/Linux:**
```bash
export PATH="$PATH:~/.local/bin"
# Add to ~/.bashrc or ~/.zshrc
```

**Or use virtual environment (recommended):**
```bash
python3 -m venv gitwise-env
source gitwise-env/bin/activate
pip install pygitwise
```

### Ollama Issues
```bash
# Check if Ollama is running
ollama list

# Start Ollama if needed
ollama serve

# Pull models if missing
ollama pull llama3
```

## 🎉 You're Ready!

Your Git workflow is now supercharged. Every commit will be meaningful, every PR will be detailed, and everything happens in seconds instead of minutes.

**Next Steps:**
- [📖 View all features](features.html)
- [⚡ Command reference](QUICK_REFERENCE.html)
- [🔧 Advanced configuration](features.html#advanced-configuration)