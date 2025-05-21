# Changelog

## [Unreleased]

### Features

- Add config module for loading and saving GitWise settings
- add Gitwise configuration file
- add .internal/ to .gitignore
- add meta-level Cursor ruleset
- generate PR descriptions and changelogs using AI
- show all operations before commit to improve UX

### Documentation

- add changelog feature documentation and contributing guidelines
- add changelog feature documentation
- add API documentation for GitWise
- add contributing guidelines
- add contributor covenant code of conduct

### Tests

- add tests for changelog feature

### Chores

- - Ensure your commit message is clear. - Use a concise subject line. - Keep the message short and to the point. - Avoid using acronyms or abbreviations. - Use a clear subject line (less than 50 characters) and a meaningful body. - Add issue numbers or references to related issues if available. - Provide a clear and concise description of the changes. - Follow PEP 8 formatting guidelines. - Follow PEP 257 - Please include a clear description of the change you made. Ensure that your message is clear, conc
- [TITLE]
- add changelog generation command
- add MANIFEST.in for packaging
- add CHANGELOG.md
- add CHANGELOG.md

### Other

- clarify changelog generation prompt guidance
- Simplify LLM backend routing logic
- add config check before pushing changes
- Add config check and LLM backend detection for PR command
- add config check and LLM backend detection to commit command
- add config check and improve offline model handling
- add init command for gitwise setup
- check config and offer init on add command
- add init command for interactive setup
- add Ollama backend support and offline mode
- add documentation guidelines to meta-level rules
- `diff --git a/setup.py b/setup.py`
- **Type:** Changed file (rule update)
- Merge pull request #51 from PayasPandey11/ollama
- `type(scope): description`
- `type(scope): description`
- Fixes #3861637: Updates for offline mode and Ollama backend support
- Merge pull request #50 from PayasPandey11/ollama
- integrate ollama as lLM backend (#432) =============================================
- diff --git a/setup.py b/setup.py index cafeefd..5363a3b 100644 --- a/setup.py +++ b/setup.py @@ -39,7 +39,11 @@ setup(          "GitPython>=3.1.0",          "transformers>=4.36.0",          "torch>=2.0.0", +        # Add 'requests' as an optional dependency for Ollama backend support      ], +    extras_require={ +        "ollama": ["requests>=2.0.0"], +    },      entry_points={          "console_scripts": [              "gitwise=gitwise.cli:main", @@ -51,4 +55,7 @@ setup(          "Source": "https://github.com/PayasPandey11/gitwise",          "Documentation": "https://github.com/PayasPandey11/gitwise/blob/main/README.md",      }, -) \ No newline at end of file +) + +# Post-install message for user, added to inform them about Ollama backend support +print("
[gitwise] By default, GitWise uses Ollama as the LLM backend. If you want to override this, set GITWISE_LLM_BACKEND=offline or online.
") \ No newline at end of file
- Type: Bug Fix Scope: llm/router.py
- `type(scope): description`
- Type: Feature (new functionality) Scope: features/commit.py
- `type: update`
- `type: updates for offline mode and Ollama backend`
- Type: Feature Scope: CHANGELOG.md
- Merge pull request #49 from PayasPandey11/offline-support
- 
- Merge pull request #48 from PayasPandey11/offline-support
- The commit message should include a brief summary of the changes being made, followed by a clear and descriptive commit message. The commit message should also include the commit message template provided in the repository's `.github/commit_template.md` file.
- Git commit messages are written as a concise description of the changes made. They should be between 50 and 72 characters.
- - Use a concise and descriptive message that accurately reflects the change. - Avoid excessive adjectives or adverbs, as they can be difficult to understand. - Use a clear and descriptive commit title.
- Merge pull request #47 from PayasPandey11/offline-support
- [gitwise] Add offline LLM inference support
- - Adds new feature X - Fixes bug in function Y - Updates README.md Z - Adds new test suite with T - Adds new dependency with A
- Merge pull request #46 from PayasPandey11/offline-support
- Commit messages should be descriptive and provide a summary of the changes being made. Use present tense and avoid jargon or technical terms. Include a short summary of the goal or motivation behind the changes. Avoid including details that can be inferred from the diff.
- Merge pull request #45 from PayasPandey11/offline-support
- fix(bug): Fixes bug in function that caused unexpected behavior
- "Merge pull request #44 from PayasPandey11/fix/ux"
- `Add feature X` instead of `Added feature X`. - Avoid using acronyms or abbreviations. - Use a clear subject line (less than 50 characters) and a meaningful body. - Add issue numbers or references to related issues if available. - Provide a clear and concise description of the changes. - Follow PEP 8 formatting guidelines. - Follow PEP 257
- Please include a clear description of the change you made. Ensure that your message is clear, concise, and follows the conventions followed by other open source projects. Additionally, please include relevant issues or pull requests that are included in the commit.
- 
- Merge pull request #44 from PayasPandey11/fix/ux
- integrate OpenAI API for generating commit messages and PR content
- Merge pull request #43 from PayasPandey11/fix/ux
- truncate diff display to first 20 lines
- integrate OpenAI API for generating commit messages and PR descriptions
- remove unused run_git_commit function
- Generate PR description using centralized function
- generate conventional commit message interactively with AI assistance
- intelligently insert new version content into changelog
- add support for getting diff of specific staged file
- Simplify add command and improve error handling
- Simplify pager handling for git subcommand
- Generate AI-enhanced PR descriptions with edit option
- Allow interactive PR creation flow
- Generate AI-enhanced PR descriptions with edit option
- Merge pull request #42 from PayasPandey11/fix/ux
- Split PR creation into separate function, add skip prompt option
- generate AI-enhanced PR descriptions and changelogs
- Merge pull request #41 from PayasPandey11/fix/ux
- add option to edit PR description before creation
- generate PR descriptions and changelogs using AI
- enhance PR description generation
- Enhance PR description generation and improve robustness
- generate AI-enhanced PR descriptions and changelogs
- Bypass PR creation prompts and always create PR
- enhance PR description using AI-generated content
- Merge pull request #40 from PayasPandey11/fix/ux
- generate changelog and pull request details from templates
- improve PR description prompt
- enhance commit list for PR by fetching latest base branch state
- generate changelog and PR details using LLM templates
- add CHANGELOG prompts and guidance
- Improve error logging when PR creation fails
- generate changelog using templates for prompts
- generate PR details using LLM
- improve push command UI/UX
- enhance PR creation with LLM-generated details
- Enhance UX and handle errors gracefully
- enhance PR creation with LLM-generated details
- enhance setup.py for flexibility and maintainability
- improve prompt for better commit messages
- improve error handling for authentication failures
- Remove automatic changelog update before pushing
- improve changed files detection and checklist generation
- Enhance PR creation with LLM-generated details and GitHub CLI
- enhance commit command with grouping, unstaged checks, diffs, and confirmations
- generate changelog content for a specific version
- enhance add command UI and error handling
- enhance `git` passthrough with improved pager handling
- enhance changelog management workflow and add pre-commit hook
- show all operations before committing to improve UX
- improve UX by showing all operations before committing
- 
- update changelog and simplify PR creation flow after push
- Merge pull request #39 from PayasPandey11/fix/ux
- handle empty commit list and improve error handling
- improve error handling and user experience when creating PRs
- Merge pull request #38 from PayasPandey11/fix/ux
- improve push prompt flow for better user experience
- Merge pull request #37 from PayasPandey11/fix/ux
- Avoid circular imports when calling push command
- adjust push flow for better user experience
- simplify PR creation flow after pushing changes
- simplify command flows and improve user experience
- add `--no-group` flag to `commit` command
- add changelog generation and enhance PR creation
- add changelog generation command
- enhance add and changelog commands
- enhance push command workflow
- enhance add command UX
- improve add command ux
- enhance add command UX
- improve add command UX
- add PR title generation and enhance PR description
- improve add command UX
- Merge pull request #36 from PayasPandey11/fix/pr
- add PR title generation and enhance PR description generation
- improve PR creation flow and error handling
- add pull request creation functionality
- Merge pull request #35 from PayasPandey11/fix/pr
- add changelog generation command
- Merge pull request #34 from PayasPandey11/fix/pr
- Merge pull request #33 from PayasPandey11/fix/pr
- 
- add changelog generation command
- Merge pull request #32 from PayasPandey11/fix/pr
- enhance add command UI and workflow
- Merge pull request #31 from PayasPandey11/fix/pr
- add changelog generation command
- Merge pull request #30 from PayasPandey11/fix/pr
- enhance add command UI and workflow
- simplify add command flow and prompts
- enhance add command UI with diff table
- enhance remote branch handling for commit retrieval
- enhance add command workflow and UI
- Merge pull request #29 from PayasPandey11/fix/pr
- enhance add command with smart file preview
- Merge pull request #28 from PayasPandey11/fix/pr
- enhance add command workflow
- enhance add command with smart file preview
- Merge pull request #27 from PayasPandey11/fix/pr
- enhance add command workflow
- enhance add command with file staging and commit prep
- Merge pull request #26 from PayasPandey11/feat/docs-and-tests
- enhance Makefile targets
- update CI workflow
- Merge pull request #25 from PayasPandey11/feat/docs-and-tests
- add unit tests for pr command and helpers
- add tests for commit feature
- simplify add and commit commands, add changelog generation
- add GitHub Actions workflow for testing and deployment
- Merge pull request #24 from PayasPandey11/tests
- enhance changelog generation
- simplify add and commit commands
- Merge pull request #23 from PayasPandey11/tests
- enhance feature descriptions and add changelog guide
- Merge pull request #22 from PayasPandey11/tests
- add version parsing and comparison
- add --create-tag option to changelog command
- Merge pull request #21 from PayasPandey11/tests
- Merge pull request #20 from PayasPandey11/tests
- Merge pull request #19 from PayasPandey11/tests
- Merge pull request #18 from PayasPandey11/tests
- Merge pull request #17 from PayasPandey11/tests
- Merge pull request #16 from PayasPandey11/tests
- Merge pull request #15 from PayasPandey11/tests
- Merge pull request #14 from PayasPandey11/tests

