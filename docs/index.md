---
layout: default
title: "GitWise - Your AI-Powered Git Co-pilot"
---

<div class="hero">
  <h1>GitWise</h1>
  <p class="hero-subtitle">Your AI-Powered Git Co-pilot</p>
  
  <p class="hero-description">
    GitWise is a command-line tool designed for experienced developers to enhance their Git workflow with intelligent AI assistance. It focuses on speed, efficiency, and integrating seamlessly with your existing habits.
  </p>

  <div class="hero-buttons">
    <a href="quick-start.html" class="btn btn-primary">Get Started</a>
    <a href="https://github.com/PayasPandey11/gitwise" class="btn btn-secondary">View on GitHub</a>
  </div>
</div>

## ✨ Key Features

<div class="feature-grid">
  <div class="feature">
    <h3>🚀 Blazing Fast</h3>
    <p>Standard Git commands run at native speed. AI features are opt-in enhancements.</p>
  </div>
  
  <div class="feature">
    <h3>🧠 Smart Commits</h3>
    <p>AI-generated Conventional Commit messages from your staged diffs in seconds.</p>
  </div>
  
  <div class="feature">
    <h3>✍️ Intelligent PRs</h3>
    <p>Automated PR titles, descriptions, labels, and context-aware checklists.</p>
  </div>
  
  <div class="feature">
    <h3>🔒 Privacy-First</h3>
    <p>Choose between local (Ollama/Offline) or cloud-based AI backends.</p>
  </div>
</div>

## 🎯 Perfect for Experienced Developers

GitWise doesn't replace your Git knowledge—it augments it. Built for developers who:

- ✅ Love Git's power but want some parts to be faster
- ✅ Write meaningful commit messages and want AI assistance
- ✅ Create detailed PR descriptions and want them generated intelligently
- ✅ Maintain changelogs and want automation without losing control
- ✅ Value privacy and want local AI options

## 🚀 Quick Example

```bash
# Install GitWise
pip install gitwise

# Make your changes
echo "print('Hello, GitWise!')" > hello.py

# AI-powered workflow
gitwise add .
gitwise commit  # AI suggests: "feat: add hello world script"
gitwise push
gitwise pr --labels --checklist  # AI generates PR with context
```

## 🤖 Three AI Modes, One Tool

| Mode | Best For | Privacy | Internet |
|------|----------|---------|----------|
| **🦙 Ollama** | High-quality local AI | 🟢 Full | 🟡 Setup only |
| **🏠 Offline** | Air-gapped environments | 🟢 Full | 🟢 Never |
| **🌐 Online** | Latest AI models (GPT-4, Claude) | 🔴 API calls | 🔴 Always |

---

<div class="cta-section">
  <h2>Ready to enhance your Git workflow?</h2>
  <a href="quick-start.html" class="btn btn-primary btn-large">Get Started in 5 Minutes</a>
</div> 