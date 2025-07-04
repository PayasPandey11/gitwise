---
layout: default
title: "GitWise - AI-Powered Git Workflow Assistant"
---

<div class="hero">
  <h1>GitWise</h1>
  <p class="hero-subtitle">AI-Powered Git Workflow Assistant</p>
  
  <p class="hero-description">
    Stop writing commit messages and PR descriptions by hand. GitWise generates perfect Conventional Commits and detailed PR descriptions from your code changes, all while keeping your code private with local AI.
  </p>

  <div class="hero-buttons">
    <a href="quick-start.html" class="btn btn-primary">Get Started</a>
    <a href="https://github.com/PayasPandey11/gitwise" class="btn btn-secondary">View on GitHub</a>
  </div>
</div>

## ✨ See the Difference

**Before GitWise:**
```bash
git add .
git commit -m "fix stuff"  # 😬 Vague, unhelpful
# Manually write PR description... 10+ minutes
```

**After GitWise:**
```bash
gitwise add .
gitwise commit  # 🤖 "fix: resolve authentication timeout in user login"
gitwise pr      # 🤖 Detailed PR with labels and checklist
```

*Perfect commits and PRs in seconds, not minutes.*

## 🎯 Why Choose GitWise?

<div class="feature-grid">
  <div class="feature">
    <h3>⚡ Lightning Fast</h3>
    <p>2-second commits vs 2-minute manual writing. Transform your workflow speed.</p>
  </div>
  
  <div class="feature">
    <h3>🧠 Smart & Accurate</h3>
    <p>Conventional Commits with detailed descriptions generated from actual code changes.</p>
  </div>
  
  <div class="feature">
    <h3>🔒 Privacy First</h3>
    <p>Local AI models (Ollama) keep your code on your machine. No data leaves your computer.</p>
  </div>
  
  <div class="feature">
    <h3>🛠️ Familiar</h3>
    <p>Works exactly like Git commands you know. Drop-in replacement with AI superpowers.</p>
  </div>
</div>

## 🚀 Quick Start

```bash
# 1. Install
pip install pygitwise

# 2. Initialize (one-time setup)
gitwise init

# 3. Use it like Git, but smarter
gitwise add .       # Interactive file staging
gitwise commit      # AI-generated commit messages
gitwise pr          # Detailed PR descriptions
```

## 🤖 AI Backend Options

| Backend | Privacy | Quality | Speed | Best For |
|---------|---------|---------|-------|----------|
| **Ollama** (Local) | 🟢 Complete | 🟢 High | 🟢 Fast | Privacy-focused developers |
| **Online** (GPT-4/Claude) | 🟡 API calls | 🟢 Highest | 🟢 Instant | Latest AI capabilities |

Choose local for privacy, online for cutting-edge AI. Switch anytime.

## 🔥 Core Features

- **🤖 AI Commit Messages** - Generate perfect Conventional Commits from staged changes
- **📝 Smart PR Descriptions** - Detailed descriptions with automated labels and checklists  
- **⚡ Streamlined Workflow** - Complete Git workflow automation
- **🔒 Privacy-First Design** - Local AI keeps your code private
- **⚙️ Git Compatible** - Drop-in replacement for Git commands
- **📊 Changelog Generation** - Automated changelog maintenance

---

<div class="cta-section">
  <h2>Ready to transform your Git workflow?</h2>
  <p>Join thousands of developers using GitWise for better commits and PRs.</p>
  <a href="quick-start.html" class="btn btn-primary btn-large">Get Started in 2 Minutes</a>
</div>