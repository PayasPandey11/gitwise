# GitWise Quick Reference

## 🚀 Setup
```bash
pip install gitwise               # Basic installation
pip install "gitwise[offline]"    # With offline model support
gitwise init                      # Configure AI backend
```

## 🤖 AI Backend Selection
```bash
# Environment variables
export GITWISE_LLM_BACKEND=ollama    # Default (recommended)
export GITWISE_LLM_BACKEND=offline   # Built-in model
export GITWISE_LLM_BACKEND=online    # OpenRouter API

# Quick switch
gitwise init  # Interactive reconfiguration
```

## 📝 Core Commands

### Stage & Commit
```bash
gitwise add .                     # Interactive staging
gitwise add file1.py file2.py     # Stage specific files
gitwise commit                    # AI-generated commit message
gitwise commit --group            # Split into multiple commits
```

### Push & PR
```bash
gitwise push                      # Push with PR prompt
gitwise pr                        # Create PR with AI description
gitwise pr --labels               # Add suggested labels
gitwise pr --checklist            # Add context-aware checklist
gitwise pr --draft                # Create draft PR
```

### Changelog
```bash
gitwise changelog                 # Generate changelog for release
gitwise changelog --auto-update   # Update unreleased section
gitwise setup-hooks               # Install pre-commit hook
```

### Git Passthrough
```bash
gitwise status                    # git status
gitwise log --oneline -5          # git log
gitwise diff                      # git diff
gitwise <any-git-command>         # Direct passthrough
```

## ⚙️ Configuration

### Ollama
```bash
export OLLAMA_MODEL=llama3        # Change model
export OLLAMA_URL=http://localhost:11434  # Custom server
ollama pull codellama             # Download new model
```

### Offline
```bash
export GITWISE_OFFLINE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
```

### Online
```bash
export OPENROUTER_API_KEY="your_key"
export OPENROUTER_MODEL="anthropic/claude-3-haiku"
```

## 🔥 Pro Tips

1. **Group commits for refactoring**: `gitwise commit --group`
2. **Quick PR with everything**: `gitwise pr --labels --checklist`
3. **Check Ollama status**: `curl http://localhost:11434/api/tags`
4. **Force offline mode**: `export GITWISE_LLM_BACKEND=offline`
5. **Custom config path**: `export GITWISE_CONFIG_PATH=~/.myconfig.json`

## 🆘 Troubleshooting

```bash
# Ollama not working?
ollama serve                      # Start Ollama service
ollama list                       # Check available models

# Permission issues?
chmod +x ~/.git/hooks/pre-commit  # Fix hook permissions

# Config issues?
rm ~/.gitwise/config.json         # Reset configuration
gitwise init                      # Reconfigure
``` 