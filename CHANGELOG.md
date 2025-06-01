# Changelog

## [0.1.0] - 2024-08-23
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
