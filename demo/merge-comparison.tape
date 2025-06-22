Output demo/assets/merge-comparison.gif
Set FontSize 14
Set Width 1400
Set Height 700
Set Theme "Dracula"
Set TypingSpeed 0.1s

# Title screen
Type "# Git Merge Conflict Comparison"
Enter
Type "# Traditional Git (Left) vs GitWise (Right)"
Enter
Sleep 2s
Ctrl+L

# Traditional Git Side - Merge Conflict Nightmare
Type "# === TRADITIONAL GIT ==="
Enter
Type "# Trying to merge feature branch..."
Enter
Sleep 1s

Type "git merge feature-auth"
Enter
Sleep 1s
Type "Auto-merging auth.py"
Enter
Type "CONFLICT (content): Merge conflict in auth.py"
Enter
Type "Automatic merge failed; fix conflicts and then commit the result."
Enter
Sleep 1s

Type "# 😰 Oh no! Manual conflict resolution needed..."
Enter
Sleep 1s

Type "cat auth.py"
Enter
Sleep 0.5s
Type "def authenticate(user):"
Enter
Type "<<<<<<< HEAD"
Enter  
Type "    if user.is_valid():"
Enter
Type "        return create_token(user)"
Enter
Type "======="
Enter
Type "    if user and user.is_authenticated:"
Enter
Type "        return generate_jwt_token(user)"
Enter
Type ">>>>>>> feature-auth"
Enter
Type "    return None"
Enter
Sleep 2s

Type "# Now I need to:"
Enter
Type "# 1. Understand both changes"
Enter
Type "# 2. Decide which to keep"  
Enter
Type "# 3. Manually edit the file"
Enter
Type "# 4. Test that it works"
Enter
Type "# 5. git add and commit"
Enter
Sleep 1s

Type "vim auth.py  # 😵 Manual editing..."
Enter
Sleep 2s
Type "# ... 10 minutes later ..."
Enter
Sleep 1s

Type "git add auth.py"
Enter
Type "git commit -m 'merge feature-auth'"
Enter
Sleep 1s

Type "# 😓 Finally done... but was it right?"
Enter
Sleep 2s

# Add separator  
Type "# =================================="
Enter
Sleep 1s

# GitWise Side - Intelligent Resolution
Type "# === GITWISE ==="
Enter
Type "# Same merge scenario..."
Enter
Sleep 1s

Type "gitwise merge feature-auth"
Enter
Sleep 1s

Type "🔍 Analyzing merge conflict in auth.py..."
Sleep 1.5s
Enter
Type "🧠 Understanding changes:"
Sleep 0.8s
Enter
Type "   • HEAD: Basic user validation"
Sleep 0.8s
Enter
Type "   • feature-auth: JWT token generation"
Sleep 0.8s
Enter
Type "💡 Recommended resolution:"
Sleep 0.8s
Enter
Type "   • Keep: JWT token generation (more secure)"
Sleep 0.8s
Enter
Type "   • Combine: user validation from both"
Sleep 0.8s
Enter
Sleep 1s

Type "✅ Applied intelligent merge resolution"
Sleep 1s
Enter
Type "✅ Merge completed successfully"
Sleep 1s
Enter
Sleep 1s

Type "cat auth.py"
Enter
Sleep 0.5s
Type "def authenticate(user):"
Enter
Type "    if user and user.is_valid() and user.is_authenticated:"
Enter
Type "        return generate_jwt_token(user)"
Enter  
Type "    return None"
Enter
Sleep 1.5s

Type "# 🎉 Perfect! AI combined the best of both:"
Enter
Type "# ✓ Comprehensive validation"
Enter
Type "# ✓ Modern JWT tokens"
Enter
Type "# ✓ Safe and secure"
Enter
Sleep 2s

Type "# ⚡ Total time: 30 seconds vs 10+ minutes"
Enter
Sleep 3s

# Final message
Enter
Type "# 🚀 GitWise: Smart conflict resolution"
Enter  
Type "# No more merge anxiety!"
Sleep 3s 