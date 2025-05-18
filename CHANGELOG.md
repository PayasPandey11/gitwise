# Changelog


## v1.0.0-beta.1
*Released on 2025-05-18*

# GitWise v1.0.0-beta.1 Release Notes

## 🎉 New Features

### CLI Enhancements
- Enhanced `add` command and updated CLI for better usability
- Added smart commit grouping option to intelligently group related changes
- Implemented selective file staging with `stage_files` and `unstage_files` functions
- Improved error handling in the `add` command
- Enhanced gitwise CLI for direct git command usage
- Added command categories for better organization

### Pull Request Improvements
- Added pull request enhancement features with optional labels and checklists
- Improved pull request command options for greater flexibility
- Implemented pull request creation using GitHub CLI (later removed)
- Added validation checks before creating a pull request
- Prompt user to create a pull request if not on the main branch

### Commit Message Generation
- Added prompts for generating commit messages and pull request descriptions
- Improved commit message generation logic to include branch details
- Updated AI model to GPT for enhanced commit message generation

### Authentication
- Implemented user authentication system

## 🛠️ Refactors and Optimizations

- Extracted LLM API call to a separate function for better code organization
- Simplified `generate_pr_description` function for improved readability
- Streamlined `get_commit_history` function to compare against remote and use `main..HEAD`
- Refactored `analyze_changes` to group related file changes intelligently
- Switched to OpenRouter API and Claude model for LLM integration
- Updated comments in `llm.py` to focus on code changes rather than functionality
- Simplified catch-all command handling in CLI

## 📚 Documentation Updates

- Updated README with new changelog command and installation instructions
- Added Makefile commands and troubleshooting section to README
- Updated author and contact information in README, setup.py, and OpenAI API calls
- Added MIT license badge and file

## 🐛 Bug Fixes

- Improved error messages for no commits found in `pr.py`
- Ensured proper exit code when no git command is provided

## 🤝 Contributors

Special thanks to the following contributors for their significant contributions:

-


## [Unreleased]

### Documentation

- add changelog feature documentation and contributing guidelines
- add changelog feature documentation
- add API documentation for GitWise
- add contributing guidelines
- add contributor covenant code of conduct

### Tests

- add tests for changelog feature

### Chores

- add MANIFEST.in for packaging
- add CHANGELOG.md
- add CHANGELOG.md

### Other

- add changelog generation command
- enhance add command UI and workflow
- add changelog generation command
- enhance add command UI and workflow
- simplify add command flow and prompts
- enhance add command UI with diff table
- enhance remote branch handling for commit retrieval
- enhance add command workflow and UI
- enhance add command with smart file preview
- enhance add command workflow
- enhance add command with smart file preview
- enhance add command workflow
- enhance add command with file staging and commit prep
- enhance Makefile targets
- update CI workflow
- add unit tests for pr command and helpers
- add tests for commit feature
- simplify add and commit commands, add changelog generation
- add GitHub Actions workflow for testing and deployment
- enhance changelog generation
- simplify add and commit commands
- enhance feature descriptions and add changelog guide
- add version parsing and comparison
- add --create-tag option to changelog command

