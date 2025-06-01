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

## 🧠 Local LLM Mode (Ollama Default)

GitWise now uses [Ollama](https://ollama.com/) as the **default** backend for all local AI features. This provides fast, private, and fully offline LLM inference.

### How Ollama mode works:

- **Ollama must be running locally** (see [Ollama install docs](https://ollama.com/download)).
- By default, GitWise sends prompts to Ollama at `http://localhost:11434` using the model specified by `OLLAMA_MODEL` (default: `llama3`).
- If Ollama is not running or not available, GitWise will automatically fall back to its built-in offline backend (using `TinyLlama/TinyLlama-1.1B-Chat-v1.0` by default).
- You can override the backend selection with the environment variable:
  ```bash
  export GITWISE_LLM_BACKEND=ollama   # (default)
  export GITWISE_LLM_BACKEND=offline  # Use built-in offline model (e.g., TinyLlama)
  export GITWISE_LLM_BACKEND=online   # Use OpenRouter/online LLM
  ```
- To change the Ollama model:
  ```bash
  export OLLAMA_MODEL="llama3"  # or any model you have pulled in Ollama
  ```
- To change the built-in offline model (if `GITWISE_LLM_BACKEND=offline`):
  ```bash
  export GITWISE_OFFLINE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0" # Example
  ```

**Tip:**
- If you see connection errors, make sure the Ollama server is running locally and the model is available. See [Ollama troubleshooting](https://ollama.com/docs/troubleshooting) for help.
- You can still use the previous offline mode by setting `GITWISE_LLM_BACKEND=offline`.

## Ollama Troubleshooting & FAQ

**Q: What happens if Ollama is not installed or not running?**
- GitWise will automatically fall back to its offline backend (e.g., `TinyLlama/TinyLlama-1.1B-Chat-v1.0`) and show a warning. No AI features will work with Ollama until it is running.

**Q: What if the specified model (e.g., `llama2:latest`) is not available in Ollama?**
- Ollama will return an error. You should pull the model with:
  ```bash
  ollama pull llama2
  ```
  or the appropriate model name.

**Q: Do I need the `requests` library?**
- GitWise will use `requests` for Ollama HTTP calls if available (recommended for best compatibility). If not, it will fall back to Python's standard library HTTP support.
- To ensure requests is installed:
  ```bash
  pip install .[ollama]
  ```

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

# For development (editable install with dev dependencies)
make install-dev # or pip install -e ".[dev]"
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
- **For New Releases**: Run `gitwise changelog`. It will suggest a semantic version based on your recent commits. Confirm or provide a version (e.g., `v1.2.3`). The AI will generate entries for this version. The command will also offer to create a git tag for the version.
- **Automatic Unreleased Section**: To automatically update an `[Unreleased]` section in your `CHANGELOG.md` before each commit, run `gitwise setup-hooks`. This installs a Git pre-commit hook script that calls `gitwise changelog --auto-update` and stages `CHANGELOG.md` if it was modified. 
    - **Note for `pre-commit` framework users**: If you use the [pre-commit](https://pre-commit.com/) framework, you should integrate `gitwise changelog --auto-update` into your existing `.pre-commit-config.yaml` instead of using `gitwise setup-hooks`.
- **Best Practice**: Use [Conventional Commit](https://www.conventionalcommits.org/) messages (e.g., `feat: ...`, `fix: ...`) for the best changelog results.

### `gitwise setup-hooks`
- Installs a Git pre-commit script (`.git/hooks/pre-commit`) that attempts to run `gitwise changelog --auto-update` before each commit. 
- This helps maintain an up-to-date pending changelog. 
- If you use the `pre-commit` framework, manage GitWise through your `.pre-commit-config.yaml` instead.

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
    python3 -m venv .venv  # Recommend python3 explicitly
    source .venv/bin/activate
    pip3 install -e ".[dev]" # Recommend pip3 explicitly
    ```
3.  **Run tests:**
    ```bash
    make test # or pytest
    ```
4.  **Check linting & formatting:**
    ```bash
    make format  # Runs black and isort
    make lint    # Runs flake8, black --check, isort --check, mypy
    # Or run directly: 
    # python3 -m black gitwise tests
    # python3 -m isort gitwise tests
    # python3 -m flake8 gitwise tests
    # python3 -m mypy gitwise tests
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