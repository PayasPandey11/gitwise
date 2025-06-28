---
layout: default
title: "Features - GitWise"
---

# Features & Advanced Usage

GitWise transforms your Git workflow with AI-powered automation while keeping you in control.

## 🤖 Core Features

### 🎯 AI-Powered Commit Messages
Transform your staged changes into perfect Conventional Commits:

```bash
# Before
git commit -m "fix stuff"

# After
gitwise commit
# Output: "fix: resolve authentication timeout in user login flow"
```

**Features:**
- Analyzes your actual code changes
- Generates Conventional Commit format
- Includes detailed descriptions
- Respects your coding context

### 📝 Intelligent PR Descriptions
Create comprehensive PRs with zero manual writing:

```bash
gitwise pr --labels --checklist
```

**Automatically generates:**
- Detailed description from commit history
- Relevant labels based on changes
- Context-specific checklists
- Proper PR title formatting

### ⚡ Interactive Complete Workflow
One command does everything with AI assistance:

```bash
# Traditional workflow (slow)
git add .
git commit -m "vague message"
git push
# Manually create PR... 10+ minutes

# GitWise interactive workflow (15 seconds)
gitwise add .
# 🔄 Shows changes → AI commit → Push → Create PR
# Complete workflow with AI assistance at each step
```

### 🧠 Smart Auto-Grouping
Automatically groups related changes into logical commits:

```bash
gitwise commit --group
# AI analyzes changes and creates separate commits for:
# - "feat: add user authentication"  
# - "docs: update API documentation"
# - "test: add auth unit tests"
```

### 🔀 Intelligent Merge Resolution
AI-powered conflict analysis and resolution:

```bash
gitwise merge feature-branch
# 🤖 Analyzes conflicts with context
# 🧠 Suggests resolutions
# 📝 Explains merge strategy
# ⚡ Guides you through resolution
```

### 🎯 Branch Context Management
Help AI understand your work:

```bash
# Set context for better suggestions
gitwise set-context "Implementing OAuth2 authentication system"

# View current context
gitwise get-context
```

## 🤖 AI Backend Options

### 🦙 Ollama (Local) - Recommended
**Perfect for privacy-focused developers**

```bash
# One-time setup
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
gitwise init  # Select Ollama
```

**Benefits:**
- 🔒 **Complete Privacy** - Code never leaves your machine
- 💰 **Zero Cost** - No API fees
- 🚀 **Fast** - Local processing
- 🔄 **Flexible** - Switch models easily

**Available Models:**
- `llama3` - Best overall quality
- `codellama` - Optimized for code
- `mistral` - Fast and efficient

### 🌐 Online (GPT-4/Claude) - Latest AI
**For cutting-edge AI capabilities**

```bash
gitwise init  # Select Online, enter API key
```

**Benefits:**
- 🎯 **Highest Quality** - Latest AI models
- ⚡ **Instant** - No local processing
- 🔄 **Always Updated** - Latest model versions

**Supported Providers:**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Google (Gemini Pro)
- OpenRouter (Access to multiple models)

## 🔥 Advanced Features

### 🔄 Auto-Confirm Mode
Speed up your workflow with automatic confirmations:

```bash
# Skip all prompts
gitwise add . --yes
gitwise commit --yes
gitwise push --yes
gitwise pr --yes --labels --checklist
```

### 🏷️ Smart PR Labels
Automatically add relevant labels based on your changes:

```bash
gitwise pr --labels
```

**Auto-detects:**
- `bug` - Bug fixes
- `feature` - New features  
- `docs` - Documentation changes
- `refactor` - Code refactoring
- `test` - Test additions

### ✅ Context-Aware Checklists
Generate checklists based on your file types:

```bash
gitwise pr --checklist
```

**Examples:**
- **Frontend changes**: Browser testing, accessibility
- **Backend changes**: API documentation, security review  
- **Database changes**: Migration testing, backup verification

### 📊 Changelog Management
Keep your changelog up-to-date automatically:

```bash
# Generate changelog for current version
gitwise changelog

# Update for specific version
gitwise changelog --version 1.2.0
```

### 🎮 Git Command Passthrough
Use GitWise as a drop-in Git replacement:

```bash
# All standard Git commands work
gitwise status
gitwise log --oneline
gitwise branch -a
gitwise diff HEAD~1
```

## ⚙️ Advanced Configuration

### Switching AI Backends
Change backends anytime:

```bash
gitwise init  # Reconfigure backend
```

### Custom Model Selection
For Ollama users:
```bash
# List available models
ollama list

# Pull new models
ollama pull codellama
ollama pull mistral

# GitWise will detect and offer them
```

### Configuration Files
GitWise stores config in:
- **Local**: `.gitwise/config.json` (per repository)
- **Global**: `~/.gitwise/config.json` (all repositories)

## 🎯 Best Practices

### For Teams
- Use consistent AI backend across team
- Set up branch context templates
- Standardize on Conventional Commits

### For Privacy
- Use Ollama for sensitive projects
- Keep API keys secure
- Review generated content before committing

### For Performance  
- Use auto-confirm mode for repetitive tasks
- Set branch context early
- Cache Ollama models locally

## 🔧 Troubleshooting

### Common Issues

**Ollama not responding:**
```bash
ollama serve  # Start Ollama server
ollama list   # Check available models
```

**API key issues:**
```bash
gitwise init  # Reconfigure API keys
```

**Performance slow:**
```bash
# For Ollama: ensure model is pulled locally
ollama pull llama3

# For Online: check internet connection
```

## 🚀 What's Next?

GitWise is actively developed with new features added regularly:

- **Smart merge conflict resolution** - AI-powered merge assistance
- **Code review suggestions** - Automated code quality checks  
- **Team collaboration** - Shared contexts and templates
- **IDE integrations** - VS Code, IntelliJ plugins

Stay updated at [github.com/PayasPandey11/gitwise](https://github.com/PayasPandey11/gitwise)