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
# Write PR description manually... takes 10+ minutes
```

**After GitWise** (AI-powered):
```bash
gitwise add .
gitwise commit  # 🤖 "fix: resolve authentication timeout in user login"
gitwise pr      # 🤖 Generates detailed PR with labels, checklist, description
```

*Perfect commits and PRs in seconds, not minutes.*

## 🚀 Quick Start

```bash
# 1. Install
pip install pygitwise

# 2. Initialize (one-time setup)
gitwise init

# 3. Use it like Git, but smarter
gitwise add .       # Interactive file staging
gitwise commit      # AI-generated commit messages
gitwise push        # Push with PR creation
gitwise pr          # Detailed PR descriptions
```

**That's it!** Your commits now follow Conventional Commits, your PRs have detailed descriptions, and everything is generated from your actual code changes.

## 🎯 Why GitWise?

### ⚡ **Speed**: 2-second commits vs 2-minute manual writing
### 🧠 **Quality**: Conventional Commits with detailed descriptions
### 🔒 **Privacy**: Local AI models (Ollama) - your code never leaves your machine
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

## 🔥 Key Features

- **🤖 AI Commit Messages**: Generate Conventional Commits from your staged changes
- **📝 Smart PR Descriptions**: Detailed descriptions with automated labels and checklists  
- **⚡ Streamlined Workflow**: `gitwise add` → `gitwise commit` → `gitwise push` → `gitwise pr`
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