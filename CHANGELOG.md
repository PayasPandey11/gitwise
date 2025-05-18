# Changelog


## [Unreleased]

### Chores

- add CHANGELOG.md

### Other

- enhance feature descriptions and add changelog guide
- add version parsing and comparison
- add --create-tag option to changelog command

## v1.0.0-beta.1

*Released on *

### Features

- add new feature (placeholder message)

### Documentation

- update README with new changelog command
- update author and contact information in README, setup.py, and OpenAI API calls

### Refactor

- update AI model to GPT for commit message generation

### Chores

- add MIT license file

### Other

- enhance add command and update CLI
- make labels and checklist opt-in
- improve PR command options
- add PR enhancement features
- enhance PR creation with labels and checklist
- add prompts for commit messages and PR descriptions
- add prompts and refactor commit message generation
- implement PR creation using GitHub CLI
- extract LLM API call to separate function
- simplify generate_pr_description function
- simplify get_commit_history function
- simplify PR command, remove GitHub CLI integration
- pass group flag to commit_command based on user input
- update get_commit_history to compare against remote
- add smart commit grouping option
- add license and project URLs
- update analyze_changes to group related file changes
- add MIT license badge
- Add stage_files and unstage_files functions for selective staging
- Update commit command description
- Merge pull request #13 from PayasPandey11/new_1
- simplify get_commit_history to use main..HEAD
- Merge pull request #12 from PayasPandey11/new_1
- update installation instructions, add Makefile commands, and troubleshooting section
- Merge pull request #11 from PayasPandey11/new_1
- Simplify catch-all command handling
- Merge pull request #10 from PayasPandey11/new_1
- add Makefile, update README, and update dependencies
- Merge pull request #9 from PayasPandey11/new_1
- switch to OpenRouter API and Claude model
- Merge pull request #8 from PayasPandey11/new_1
- Improve error handling in 'add' command
- Merge pull request #7 from PayasPandey11/new_1
- Updated comments in llm.py to focus on code changes, not functionality or features. Updated generation of PR description to emphasize functionality and features, not code changes.
- Merge pull request #6 from PayasPandey11/new_1
- Improve gitwise CLI command handling
- Merge pull request #5 from PayasPandey11/new_1
- Enhance gitwise CLI for direct git command usage
- Merge pull request #4 from PayasPandey11/new_1
- improve commit message guidelines
- Merge pull request #3 from PayasPandey11/new_1
- add command categories for gitwise
- Merge pull request #2 from PayasPandey11/new_1
- Ensure proper exit code when no git command is provided
- prompt user to create pull request if not on main branch
- Add setup.py for project configuration
- Merge pull request #1 from PayasPandey11/dev
- Improve error messages for no commits found
- improve commit message to include branch details
- Add validation checks before creating a pull request
- add command for creating pull requests
- improve commit message generation logic
- implement user authentication system
- Add push command to handle pushing changes to remote repository.
- Refactor git push logic to allow pushing to different branches
- Add option to push changes after committing.
- Refactor CLI to support running as a script from gitwise/ directory.
- Add AI-powered git assistant for generating smart commit messages, PR descriptions, and changelogs using open-source LLMs.
- Generate commit message using BitNet LLM
- Initial commit

