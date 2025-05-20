# GitWise: Your AI-Powered Git Co-pilot

**GitWise is a command-line tool designed for experienced developers to enhance their Git workflow with intelligent AI assistance. It focuses on speed, efficiency, and integrating seamlessly with your existing habits, while upholding industry best practices.**

Are you a seasoned developer who loves the power of Git but wishes some parts were faster or smarter? GitWise is built for you. We don't replace your Git knowledge; we augment it. GitWise helps you:

- **Craft Perfect Commits, Instantly**: Generate Conventional Commit messages from your staged diffs in seconds.
- **Streamline PR Creation**: Get AI-generated PR titles and descriptions, plus automated label and checklist suggestions.
- **Maintain Changelogs Effortlessly**: Keep your `CHANGELOG.md` up-to-date with minimal fuss.
- **Retain Full Git Control**: Use any standard Git command via `gitwise git ...` with the speed you expect. AI features are opt-in enhancements.

GitWise aims to make your `add -> commit -> push -> PR` cycle more efficient and enjoyable.

## Key Features

- **🚀 Blazing Fast Core**: Standard Git commands passed through `gitwise git ...` run at native Git speed.
- **🧠 Smart Commit Messages**: AI-generated Conventional Commits (opt-in grouping for complex changes via `gitwise commit --group`).
- **✍️ Intelligent PR Descriptions**: AI-generated PR titles and descriptions.
- **🏷️ Automated PR Enhancements**: Optional label suggestions based on commit types and file-specific checklists for PRs.
- **📜 Changelog Management**: Automated updates for unreleased changes and easy generation for new versions.
- **⚙️ Git Command Passthrough**: Use `gitwise` as a wrapper for any `git` command (e.g., `gitwise status`, `gitwise log`).

## 🧠 Offline Mode (Local LLM)

GitWise runs all AI features fully offline by default using a local model (`microsoft/phi-2`). This is fast, private, and works great on MacBooks (Apple Silicon and Intel).

### How offline mode works:

- **No setup required:** The first time you use any AI feature (e.g., `gitwise commit`), GitWise will automatically prompt you to download the model (~1.7GB) if it is not already present.
- **Manual download (optional):** Advanced users can pre-download the model with:
  ```bash
  gitwise offline-model
  ```
- **After download:** All AI features will use the local model by default. To force online mode, set the environment variable:
  ```bash
  export GITWISE_ONLINE=1
  ```

**Tip:**
- You can override the model with `GITWISE_OFFLINE_MODEL` (e.g., TinyLlama).
- If you see warnings about OpenSSL/LibreSSL, they are safe to ignore for most users.

## Installation

Ensure you have Python 3.8+ installed.

### Using pip (Recommended)

```bash
pip install gitwise
```

### From Source

```bash
# Clone the repository
git clone https://github.com/PayasPandey11/gitwise.git
cd gitwise

# Install for use
make install # or python setup.py install

# For development (editable install)
make install-dev # or pip install -e .
```

## Quick Start

1.  **Configure your OpenRouter API Key:** GitWise uses OpenRouter to access LLMs.
    ```bash
    export OPENROUTER_API_KEY="your_openrouter_api_key"
    ```
    (Add this to your `.bashrc`, `.zshrc`, etc.)

2.  **Stage your changes:**
    ```bash
    git add . # Or use gitwise add .
    ```

3.  **Create a smart commit:**
    ```bash
    gitwise commit
    ```
    For more complex changes, consider `gitwise commit --group` to let AI suggest separate commits.

4.  **Push your changes:**
    ```bash
    gitwise push
    ```
    This will also offer to create a Pull Request.

5.  **Create a Pull Request directly:**
    ```bash
    gitwise pr
    ```
    Add labels and a checklist: `gitwise pr --labels --checklist`

## Detailed Usage

GitWise commands are designed to be intuitive. Here are the main ones:

### `gitwise add [files...]`
- Interactively stage files. 
- Shows a summary of staged files and offers to commit or view the full diff.
- Example: `gitwise add .` or `gitwise add file1.py file2.md`

### `gitwise commit [--group]`
- Generates an AI-powered Conventional Commit message for your staged changes.
- You can review, edit, or regenerate the message before committing.
- Use `--group` (or `-g`) for GitWise to analyze changes and suggest breaking them into multiple logical commits. This is powerful for refactoring or large feature work but can be slower due to more LLM calls.
- Example: `gitwise commit` (for a single smart commit)
- Example: `gitwise commit --group` (to try grouping)

### `gitwise push`
- Pushes your committed changes to the remote repository.
- Prompts to create a Pull Request after a successful push.

### `gitwise pr [--labels] [--checklist] [--base <branch>] [--title <title>] [--draft]`
- Creates a Pull Request on GitHub (requires `gh` CLI to be installed and authenticated).
- AI generates the PR title (if not provided) and a descriptive body based on your commits.
- `--labels`: Suggests relevant labels (e.g., bug, feature) based on commit types.
- `--checklist`: Adds a context-aware checklist to the PR body based on changed file types (e.g., reminders for tests, docs for Python files).
- Example: `gitwise pr --labels --checklist --base develop`

### `gitwise changelog [--version <version>] [--output-file <file>]`
- Generates or updates your `CHANGELOG.md`.
- **For New Releases**: Run `gitwise changelog`. It will suggest a semantic version based on your recent commits. Confirm or provide a version (e.g., `v1.2.3`). The AI will generate entries for this version.
- **Automatic Unreleased Section (Optional)**: For a fully automated workflow, set up the GitWise pre-commit hook:
  ```bash
  gitwise setup-hooks
  ```
  This hook will call `gitwise changelog --auto-update` before each commit to keep an `[Unreleased]` section in your `CHANGELOG.md` fresh. (Requires `pre-commit` to be installed: `pip install pre-commit`)
- **Best Practice**: Use [Conventional Commit](https://www.conventionalcommits.org/) messages (e.g., `feat: ...`, `fix: ...`) for the best changelog results.

### `gitwise setup-hooks`
- Installs a pre-commit hook to automatically update the `[Unreleased]` section of your changelog before each commit.
- This helps maintain an up-to-date pending changelog effortlessly.
- Requires `pre-commit` to be installed in your environment.

### `gitwise git <git_command_and_args...>`
- A direct passthrough to any standard `git` command.
- Useful if you want to stay within the `gitwise` CLI but need a specific Git command.
- Output is streamed directly from Git. If you are using a command that pages (e.g., `git log`, `git diff`) and need script-friendly output, you should pipe it manually (e.g., `gitwise git log | cat`). If running `gitwise` via a GitHub CLI alias (`gh alias set gw --shell 'gitwise $1'`), `gh` may handle paging for you.
- Example: `gitwise git status -sb`, `gitwise git log --oneline -n 5`

## Changelog Management Workflow

This workflow ensures your changelog is consistently updated with minimal manual effort.

## Development Setup

If you want to contribute to GitWise:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/PayasPandey11/gitwise.git
    cd gitwise
    ```
2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]" # Installs in editable mode with dev dependencies
    ```
3.  **Run tests:**
    ```bash
    pytest
    ```
4.  **Check linting:**
    ```bash
    # Add your linter command here, e.g., flake8 or ruff check .
    # flake8 gitwise tests
    ```

## Roadmap & Future Ideas

GitWise is actively developing! Here are some directions we're exploring:

- **Enhanced AI Capabilities**: 
    - AI-assisted interactive rebase (`git rebase -i`).
    - AI-driven diff summaries (`gitwise diff-ai`).
    - Smart stash messages and management.
- **Local LLM Support**: Run GitWise entirely offline using local models (e.g., Ollama, GPT4All).
- **Pre-PR Sanity Checks**: Automated checks for common issues before PR creation.
- **Deeper IDE Integration**: Tighter coupling with IDEs like VS Code.
- **Configuration Flexibility**: Allow users to select LLM models and define custom prompts/behavior via a config file.
- **Team-Specific Workflows**: Features to support team conventions and automation.

Stay tuned, or contribute your own ideas!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Check out our `CONTRIBUTING.md` for guidelines (if it exists, or create one!).

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.