# Changelog

## [Unreleased]

### 🚀 Features
- Add changelog generation command with version parsing and comparison (payas)
- Enhance pull request creation flow with improved title generation and error handling (payas) 
- Add smart file preview and diff table to `add` command for better staging visualization (payas)
- Introduce `--create-tag` option to `changelog` command for tagging releases (payas)

### 🐛 Bug Fixes
- None

### 📝 Documentation  
- Add changelog feature documentation and usage guide to README (payas)
- Create API documentation for GitWise (payas)
- Add contributing guidelines and contributor covenant code of conduct (payas)

### 🔧 Maintenance
- Enhance Makefile targets for improved development workflow (payas)
- Update CI workflow to include testing and deployment (payas)
- Add MANIFEST.in for proper packaging (payas)

### ♻️ Refactoring  
- Simplify `add` and `commit` command flows and prompts (payas)
- Improve remote branch handling for commit retrieval in `pr` command (payas)
- Streamline `add` command workflow and UI (payas)
- Enhance `push` command workflow (payas)

### ✅ Tests
- Add unit tests for `pr` command and helpers (payas)  
- Introduce tests for `commit` feature (payas)
- Create tests for `changelog` feature (payas)