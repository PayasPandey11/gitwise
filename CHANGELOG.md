# Changelog

## v2.0.0 (2025-06-29)
### 🚀 Features

- Added direct integration with multiple LLM providers (OpenAI, Anthropic, Google Gemini)
- Enhanced Google Gemini model to use gemini-2.0-flash
- Upgraded to new online LLM options for OpenRouter provider
- Added context management feature to improve AI suggestions
- Implemented branch context for better AI assistance
- Added auto-confirm option to add and commit commands
- Improved PR description generation with more context
- Added test files and utilities for GitWise functionality demonstration

### 🔄 Refactoring

- Renamed LLM response functions for better clarity
- Improved commit & PR message generation flow
- Enhanced LLM provider setup for better flexibility
- Consolidated commit feature groups for better organization
- Reorganized code structure for better maintainability
- Improved test coverage and robustness

### 📝 Documentation

- Added documentation and Quick Start guide
- Updated badges to use TestPyPI and standard shields
- Added code coverage badge
- Added recommended setup instructions to README

### 🔧 Maintenance

- Enabled coverage upload to Codecov
- Updated codecov-action to v5
- Updated PyPI links to point to the correct package version
- Updated project name to "pygitwise" for consistency
- Added GitHub Pages support
- Added .gitignore entries for cursor folder
- Added Python 3.11 to test matrix
- Removed test files used for prompt validation

### 🐛 Bug Fixes

- Fixed dependency issues with OpenAI requirement (>=1.0.0)
- Improved error handling for config loading
- Enhanced spinner and error handling for config loading
- Improved handling for non-existent files in add feature

### 💥 Breaking Changes

- Dropped Python 3.8 support
- Renamed package to 'pygitwise' for consistency with PyPI

## [0.1.0] - 2025-01-10
*(Please update YYYY-MM-DD with the actual release date)*

### Added
- Initial public release of GitWise.
- Core features:
    - AI-powered conventional commit message generation.
    - AI-assisted Pull Request title and description generation.
    - Automated `CHANGELOG.md` updates based on Conventional Commits (via `gitwise changelog --auto-update` and pre-commit hook setup).
    - Interactive staging, commit, and push workflows (`gitwise add`, `gitwise commit`, `gitwise push`).
    - Pull request creation with optional AI-suggested labels and checklists (`gitwise pr`).
    - Support for multiple LLM backends:
        - Ollama (default, local server).
        - Offline (bundled model, e.g., TinyLlama, requires `gitwise[offline]`).
        - Online (OpenRouter API for models like Claude, GPT).
    - Git command passthrough via `gitwise git ...`.
    - Configuration system (`gitwise init`) for LLM backends and API keys.
    - Changelog generation for new releases (`gitwise changelog --version <version>`).

## [Unreleased]

### Features

- add new feature

### Bug Fixes

- resolve critical bug

### Documentation

- update installation guide

### Added
- Automatic installation of provider-specific dependencies when selecting Google Gemini, OpenAI, or Anthropic during initialization
- Configuration system (`gitwise init`) for LLM backends and API keys.
