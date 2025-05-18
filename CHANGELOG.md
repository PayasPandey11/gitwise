# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Changelog generation command (payas)
- Contributing guidelines (payas)
- Contributor Covenant Code of Conduct (payas)
- API documentation for GitWise (payas)
- `--create-tag` option to changelog command (payas)
- Version parsing and comparison for changelog generation (payas)

### Changed

- Enhanced add command workflow and UI (payas)
  - Improved UX with smart file preview and diff table
  - Simplified flow and prompts
  - Added file staging and commit preparation
- Enhanced pull request creation flow and error handling (payas)
  - Improved PR title generation and description
  - Enhanced remote branch handling for commit retrieval
- Enhanced changelog generation (payas)
- Updated CI workflow (payas)
- Enhanced feature descriptions in README and added changelog guide (payas)

### Fixed

- Simplified add and commit commands (payas)

### Miscellaneous

- Added MANIFEST.in for packaging (payas)
- Added CHANGELOG.md (payas)
- Enhanced Makefile targets (payas)

## [1.0.0] - YYYY-MM-DD

### Added

- Initial release of GitWise
- Add command with smart file preview and staging
- Commit command with conventional commit message generation
- Pull request creation functionality
- Changelog generation command
- Unit tests for commit, pr, and changelog features
- GitHub Actions workflow for testing and deployment