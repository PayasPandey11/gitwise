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

<style>
.hero {
  text-align: center;
  padding: 3rem 0;
  border-bottom: 1px solid #e1e4e8;
  margin-bottom: 3rem;
}

.hero h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
  font-weight: 300;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: #586069;
  margin-bottom: 1.5rem;
}

.hero-description {
  font-size: 1.1rem;
  max-width: 600px;
  margin: 0 auto 2rem;
  line-height: 1.6;
}

.hero-buttons {
  margin-top: 2rem;
}

.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  margin: 0 0.5rem;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #0366d6;
  color: white;
}

.btn-primary:hover {
  background-color: #0256cc;
  color: white;
}

.btn-secondary {
  background-color: #f6f8fa;
  color: #24292e;
  border: 1px solid #d1d5da;
}

.btn-secondary:hover {
  background-color: #f3f4f6;
  color: #24292e;
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.feature {
  padding: 1.5rem;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  background-color: #f6f8fa;
}

.feature h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.cta-section {
  text-align: center;
  padding: 3rem 0;
  margin-top: 3rem;
  border-top: 1px solid #e1e4e8;
}

.cta-section h2 {
  margin-bottom: 1.5rem;
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
</style> 