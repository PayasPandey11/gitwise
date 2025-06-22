Output demo/assets/commit-comparison.gif
Set FontSize 14
Set Width 1400
Set Height 700
Set Theme "Dracula"
Set TypingSpeed 0.1s

# Title screen
Type "# Git Commit Workflow Comparison"
Enter
Type "# Traditional Git (Left) vs GitWise (Right)"
Enter
Sleep 2s
Ctrl+L

# Split screen simulation - Traditional Git Side
Type "# === TRADITIONAL GIT ==="
Enter
Type "# Multiple files changed, need to commit..."
Enter
Sleep 1s

Type "git add ."
Enter
Sleep 0.5s

Type "git commit -m 'fix stuff'"
Enter
Sleep 1s

Type "# 😞 Result: Poor commit message"
Enter
Type "# Multiple logical changes in one commit"
Enter
Type "# Hard to review and understand"
Enter
Sleep 2s
Enter

Type "git log --oneline -3"
Enter
Sleep 1s
Type "a1b2c3d fix stuff"
Enter
Type "d4e5f6g another fix"  
Enter
Type "g7h8i9j more changes"
Enter
Sleep 2s

# Add separator
Type "# =================================="
Enter
Sleep 1s

# GitWise Side
Type "# === GITWISE ==="
Enter  
Type "# Same multiple files changed..."
Enter
Sleep 1s

Type "gitwise add . -y"
Enter
Sleep 1s

Type "✅ Analyzing changes..."
Sleep 1s
Enter
Type "✅ Creating 3 logical commits:"
Sleep 0.8s
Enter
Type "   • feat: add JWT authentication middleware"
Sleep 0.8s
Enter  
Type "   • fix: handle null user validation edge case"
Sleep 0.8s
Enter
Type "   • docs: update API authentication guide"
Sleep 0.8s
Enter
Type "✅ Pushed to origin/feature-auth"
Sleep 0.8s
Enter
Type "✅ Created PR #42 with labels and checklist"
Sleep 1s
Enter
Sleep 1s

Type "# 🎉 Result: Perfect commit history!"
Enter
Type "# Each commit has single responsibility"  
Enter
Type "# Easy to review and understand"
Enter
Sleep 2s
Enter

Type "git log --oneline -3"
Enter  
Sleep 1s
Type "x9y8z7w docs: update API authentication guide"
Enter
Type "w6v5u4t fix: handle null user validation edge case"
Enter  
Type "t3s2r1q feat: add JWT authentication middleware"
Enter
Sleep 3s

# Final message
Enter
Type "# 🚀 GitWise: Git, but Intelligent"
Enter
Type "# Stop fighting with Git commits!"
Sleep 3s 