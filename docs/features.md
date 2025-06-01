---
layout: default
title: "Features - GitWise"
---

# Features & Advanced Usage

GitWise offers powerful features designed to enhance your Git workflow without getting in your way.

## 🤖 Three AI Backend Modes

GitWise gives you complete control over your AI backend, balancing privacy, quality, and convenience.

### 🦙 Ollama Mode (Recommended)
**Best for**: Privacy-conscious developers who want high-quality local AI

```bash
# Setup once
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
gitwise init  # Select Ollama
```

**Features**:
- 🔒 100% local, no data leaves your machine
- 🚀 High-quality models (Llama 3, CodeLlama, Mistral)
- 💰 Zero cost after initial setup
- 🔄 Easy model switching

### 🏠 Offline Mode
**Best for**: Air-gapped environments, maximum privacy

```bash
pip install "gitwise[offline]"
gitwise init  # Select Offline
```

**Features**:
- 🔐 No internet connection required
- 📦 Bundled model included
- ⚡ Fast, lightweight models
- 🛡️ Perfect for sensitive codebases

### 🌐 Online Mode
**Best for**: Access to cutting-edge models (GPT-4, Claude)

```bash
export OPENROUTER_API_KEY="your_key"
gitwise init  # Select Online
```

**Features**:
- 🧠 Latest AI models (GPT-4, Claude 3, etc.)
- 🎯 Highest quality outputs
- 💻 No local GPU required
- 🌍 Always up-to-date

## 🧠 Smart Commit Messages

### Basic Commit Generation
GitWise analyzes your staged changes and generates Conventional Commit messages:

```bash
# Stage your changes
gitwise add src/auth.py tests/test_auth.py

# AI generates contextual commit message
gitwise commit
# Suggests: "feat(auth): implement JWT-based user authentication
# 
# - Add User model with password hashing
# - Implement JWT token generation and validation
# - Add comprehensive test coverage"
```

### Advanced: Grouped Commits
For complex changes, GitWise can suggest splitting into multiple logical commits:

```bash
gitwise commit --group
# AI suggests 3 commits:
# 1. "refactor: extract user validation logic"
# 2. "feat: add email verification"  
# 3. "test: add user validation tests"
```

## ✍️ Intelligent PR Creation

### Auto-Generated PR Descriptions
```bash
gitwise pr
# Creates PR with:
# - Smart title based on commits
# - Detailed description with context
# - Summary of changes
```

### Enhanced PRs with Labels & Checklists
```bash
gitwise pr --labels --checklist
# Adds:
# - Relevant labels (enhancement, bug, docs, etc.)
# - File-type specific checklists
# - Context-aware reminders
```

**Example Generated Checklist**:
- ✅ Tests added for new functionality
- ✅ Documentation updated
- ✅ Breaking changes noted in commit message
- ✅ Security implications reviewed

## 📜 Changelog Management

### Automated Changelog Updates
```bash
# Generate version-specific changelog
gitwise changelog
# AI suggests semantic version (e.g., v1.2.0)
# Generates categorized entries:
# - Features
# - Bug Fixes  
# - Breaking Changes
```

### Continuous Changelog Updates
```bash
# Setup automatic changelog updates
gitwise setup-hooks
# Installs pre-commit hook that updates [Unreleased] section
```

## 🚀 Real-World Workflows

### Feature Development
```bash
# Create feature branch
gitwise checkout -b feature/user-auth

# Make changes to multiple files
vim src/auth.py src/models.py tests/test_auth.py

# Smart staging and commit
gitwise add .
gitwise commit --group
# Results in clean, logical commit history

# Push and create enhanced PR
gitwise push
gitwise pr --labels --checklist
```

### Bug Fix Workflow
```bash
# Fix the issue
vim src/cache.py src/utils.py

# Group related changes
gitwise commit --group
# AI suggests:
# 1. "fix: prevent race condition in cache invalidation"
# 2. "refactor: extract cache logic for better testability"
# 3. "test: add concurrent access tests"

# Update changelog and create PR
gitwise changelog --auto-update
gitwise pr --labels
```

### Release Preparation
```bash
# Generate comprehensive changelog
gitwise changelog
# Reviews all commits since last release
# Suggests appropriate version bump
# Creates organized release notes

# Create release PR
gitwise pr --base main --title "Release v2.1.0"
```

## ⚙️ Git Command Passthrough

Use GitWise as a drop-in replacement for Git:

```bash
# All standard Git commands work
gitwise status
gitwise log --oneline -5
gitwise branch -a
gitwise stash list
gitwise rebase -i HEAD~3

# Same speed as native Git
gitwise git <any_git_command>
```

## 🔧 Advanced Configuration

### Environment Variables
```bash
# Backend selection
export GITWISE_LLM_BACKEND=ollama  # ollama, offline, online

# Ollama configuration
export OLLAMA_MODEL=codellama
export OLLAMA_URL=http://localhost:11434

# Offline configuration  
export GITWISE_OFFLINE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Online configuration
export OPENROUTER_API_KEY="your_key"
export OPENROUTER_MODEL="anthropic/claude-3-haiku"
```

### Configuration File
Located at `~/.gitwise/config.json`:

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
    "api_key": "your_key",
    "model": "anthropic/claude-3-haiku"
  }
}
```

## 💡 Performance Tips

1. **For Speed**: Use Ollama with smaller models (`llama3`, `codellama`)
2. **For Quality**: Use online mode with Claude or GPT-4
3. **For Privacy**: Use offline mode with bundled models
4. **For Balance**: Ollama with `llama3` (recommended default)

## 🛠️ Troubleshooting

### Backend Issues
```bash
# Check current backend
gitwise config show

# Test configuration
gitwise init  # Re-run setup

# Quick backend switch
export GITWISE_LLM_BACKEND=offline
```

### Model Management (Ollama)
```bash
# List available models
ollama list

# Pull new model
ollama pull codellama

# Check Ollama status
curl http://localhost:11434/api/tags
```

---

## 🎯 Best Practices

1. **Commit Often**: GitWise works best with focused, related changes
2. **Use Conventional Commits**: Enables better changelog generation
3. **Stage Selectively**: Use `gitwise add -p` for partial staging
4. **Review AI Suggestions**: Always review and edit generated content
5. **Maintain Privacy**: Choose local backends for sensitive work

---

<div class="tip-box">
  <h3>💡 Pro Tip</h3>
  <p>Start with <code>gitwise init</code> to configure your preferences, then use <code>gitwise add .</code> and <code>gitwise commit</code> for your daily workflow. The AI learns from your codebase patterns!</p>
</div>

<style>
.tip-box {
  background-color: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 6px;
  padding: 1.5rem;
  margin: 2rem 0;
}

.tip-box h3 {
  color: #856404;
  margin-top: 0;
}

.tip-box p {
  color: #856404;
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

h2 {
  border-bottom: 1px solid #e1e4e8;
  padding-bottom: 0.5rem;
  margin-top: 2rem;
}

h3 {
  margin-top: 1.5rem;
}
</style> 