# GitWise Versioning Strategy

This project uses **Semantic Versioning (SemVer)** with intelligent automatic version bumping based on commit messages.

## Version Format: `MAJOR.MINOR.PATCH`

### 🔴 MAJOR Version (Breaking Changes)
**Triggers:** `1.0.0` → `2.0.0`
- Breaking changes to existing functionality
- Incompatible API changes
- Major feature overhauls

**Commit Message Patterns:**
```bash
feat!: remove deprecated --old-flag option
fix!: change function signature for process_commit()
BREAKING: restructure configuration format
chore!: drop support for Python 3.7
```

### 🟡 MINOR Version (New Features)
**Triggers:** `1.0.0` → `1.1.0`
- New features (backwards compatible)
- New functionality added
- New commands or options

**Commit Message Patterns:**
```bash
feat: add smart merge conflict resolution
feature: implement changelog generation
add: support for custom commit templates
new: AI-powered PR descriptions
```

### 🟢 PATCH Version (Bug Fixes)
**Triggers:** `1.0.0` → `1.0.1`
- Bug fixes (backwards compatible)
- Documentation updates
- Performance improvements
- Code refactoring

**Commit Message Patterns:**
```bash
fix: resolve merge conflict detection issue
bug: handle empty commit messages correctly
doc: update installation instructions
chore: update dependencies
refactor: improve code structure
perf: optimize git operations
test: add unit tests for new features
```

## How Automatic Versioning Works

### 1. **Commit Message Analysis**
The CI workflow analyzes recent commit messages to determine the appropriate version bump:

```bash
# Check recent commits since last version bump
git log --oneline --since="1 day ago" | head -10

# Analyze patterns:
# - BREAKING/!: → Major bump
# - feat/feature/add/new → Minor bump  
# - fix/bug/doc/chore/refactor/perf/test → Patch bump
```

### 2. **Version Bump Logic**
```bash
# Current: 0.1.4

# Major bump: 0.1.4 → 1.0.0
# Minor bump: 0.1.4 → 0.2.0  
# Patch bump: 0.1.4 → 0.1.5
```

### 3. **Automatic Release Process**
When code is merged to `main`:
1. ✅ Tests run and pass
2. 🔍 Analyze commit messages
3. 📈 Determine version bump type
4. 🏷️ Update version in `gitwise/__init__.py`
5. 💾 Commit version bump
6. 🚀 Deploy to PyPI + TestPyPI

## Best Practices

### ✅ Good Commit Messages
```bash
feat: add AI-powered commit message generation
fix: handle git repository initialization errors
docs: update CLI usage examples
chore: bump dependency versions
```

### ❌ Poor Commit Messages
```bash
update stuff
fix things
changes
wip
```

### 🔥 Breaking Changes
Always use `!` or `BREAKING` for incompatible changes:
```bash
feat!: remove deprecated --format option
BREAKING: change default behavior for merge command
```

## Manual Version Control

If you need to manually control versions:

```bash
# Edit version in gitwise/__init__.py
__version__ = "1.2.3"

# Commit with [skip ci] to avoid auto-bump
git commit -m "chore: manual version bump to 1.2.3 [skip ci]"
```

## Examples

### Scenario 1: Bug Fix Release
```bash
# Commits:
# fix: resolve authentication token issue
# doc: update troubleshooting guide

# Result: 0.1.4 → 0.1.5 (patch)
```

### Scenario 2: Feature Release
```bash
# Commits:
# feat: add support for custom PR templates
# fix: improve error handling

# Result: 0.1.4 → 0.2.0 (minor - feature takes precedence)
```

### Scenario 3: Breaking Change
```bash
# Commits:
# feat!: restructure CLI command interface
# fix: update documentation

# Result: 0.1.4 → 1.0.0 (major - breaking change takes precedence)
```

## Version Precedence

When multiple types of changes are present:
1. **Major** (breaking) > **Minor** (feature) > **Patch** (fix)
2. The highest precedence change determines the version bump
3. Default fallback is **patch** if no patterns match

---

*This versioning strategy ensures predictable, semantic releases while maintaining compatibility and clear communication about changes.* 