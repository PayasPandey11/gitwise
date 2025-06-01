---
layout: default
title: "API Documentation - GitWise"
---

# GitWise API & Core Components

This document provides an overview of GitWise's internal structure, focusing on key classes and modules that developers might interact with or want to understand for contribution or advanced usage.

## 1. Core Git Operations: `gitwise.core.git_manager.GitManager`

All direct Git interactions are centralized in the `gitwise.core.git_manager.GitManager` class. This class uses `subprocess` to execute Git commands.

### Initialization

To use the `GitManager`, instantiate it. You can optionally provide a path to a Git repository; otherwise, it defaults to the current working directory.

```python
from gitwise.core.git_manager import GitManager

# Initialize for the current directory's repository
git_m = GitManager()

# Initialize for a specific repository path
# git_m_specific_path = GitManager(path="/path/to/your/repo")
```

### Key Public Methods of `GitManager`

Below are some of the core methods provided by `GitManager`. Refer to the source code for a complete list and detailed arguments.

-   `is_git_repo() -> bool`
    -   Checks if the current path is a Git repository.
-   `get_staged_files() -> List[Tuple[str, str]]`
    -   Returns a list of tuples, where each tuple contains the status (e.g., 'A', 'M') and file path of a staged file.
-   `get_unstaged_files() -> List[Tuple[str, str]]`
    -   Returns a list of tuples for unstaged (working directory) files with their status (e.g., 'Modified', 'Untracked').
-   `get_staged_diff() -> str`
    -   Returns the combined diff of all staged changes as a string.
-   `get_file_diff_staged(self, file_path: str) -> str`
    -   Returns the diff for a specific staged file.
-   `get_changed_file_paths_staged() -> List[str]`
    -   Returns a list of paths for all staged files.
-   `stage_files(self, file_paths: List[str]) -> bool`
    -   Stages the specified list of files. Returns `True` on success.
-   `stage_all(self) -> bool`
    -   Stages all changes (equivalent to `git add .`). Returns `True` on success.
-   `create_commit(self, message: str) -> bool`
    -   Creates a commit with the given message. Returns `True` on success.
-   `get_current_branch() -> Optional[str]`
    -   Returns the name of the current Git branch, or `None`.
-   `push_to_remote(self, local_branch: Optional[str] = None, remote_branch: Optional[str] = None, remote_name: str = "origin", force: bool = False) -> bool`
    -   Pushes changes to the specified remote. Returns `True` on success.
-   `get_default_remote_branch_name(self, remote_name: str = "origin") -> Optional[str]`
    -   Detects and returns the default branch name of the specified remote (e.g., 'main', 'master').
-   `get_commits_between(self, ref1: str, ref2: str, pretty_format: str = "%H|%s|%an") -> List[Dict[str, str]]`
    -   Retrieves commits between two references (e.g., 'tag1..tag2', 'origin/main..HEAD').
-   `get_merge_base(self, ref1: str, ref2: str) -> Optional[str]`
    -   Finds the best common ancestor between two commits.
-   `has_uncommitted_changes() -> bool`
    -   Checks if there are any staged or unstaged changes.
-   `has_staged_changes() -> bool`
    -   Checks if there are any staged changes.

*(For a full list of methods and their parameters, please refer to `gitwise/core/git_manager.py`)*

## 2. Feature Logic (`gitwise.features`)

Core functionalities of GitWise commands are encapsulated within feature classes in the `gitwise.features` package. These classes utilize `GitManager` for Git operations and the LLM router for AI assistance.

### `features.add.AddFeature`
   - **`execute_add(self, files: List[str] = None) -> None`**
     - Handles the logic for staging files, displaying changes, and presenting options for diffing or committing.

### `features.commit.CommitFeature`
   - **`execute_commit(self, group: bool = True) -> None`**
     - Manages the commit creation process, including AI-assisted message generation, optional change grouping, and user interaction for message approval.

### `features.push.PushFeature`
   - **`execute_push(self) -> bool`**
     - Handles pushing local changes to the remote repository, including setting upstream for new branches and prompting for PR creation.

### `features.pr.PrFeature`
   - **`execute_pr(self, use_labels: bool, ..., skip_prompts: bool) -> bool`**
     - Orchestrates Pull Request creation. This includes generating PR titles and descriptions using AI, suggesting labels and checklists (via `pr_enhancements.py`), and interacting with the GitHub CLI (`gh`).

### `features.changelog.ChangelogFeature`
   - **`execute_changelog(self, version: Optional[str], ..., auto_update: bool) -> None`**
     - Manages changelog generation and updates. It can suggest versions, generate entries from commits using AI, and update the `CHANGELOG.md` file. Also handles the pre-commit hook setup for automatic updates of an "[Unreleased]" section.

## 3. LLM Interaction (`gitwise.llm`)

- All AI model calls are routed through **`gitwise.llm.router.get_llm_response()`**.
- This router supports multiple backends:
    - **Ollama**: For local inference (default). Requires Ollama server to be running.
    - **Offline**: Uses a bundled Hugging Face model (e.g., TinyLlama) for local, offline inference.
    - **Online**: Uses OpenRouter to access various models (e.g., Claude, Mistral).
- Backend selection and model preferences (like Ollama model, OpenRouter API key, OpenRouter model) are configured via the `gitwise init` command or environment variables (see `README.md`).
- Specific backend implementations are in `gitwise/llm/ollama.py`, `gitwise/llm/offline.py`, and `gitwise/llm/online.py`.

## 4. Configuration (`gitwise.config`)

- The `gitwise.config` module handles loading, saving, and validating GitWise settings.
- Configuration is stored in `config.json`, either locally in `.gitwise/` within a repository or globally in `~/.gitwise/`.
- Key functions:
    - `load_config() -> Dict[str, Any]`: Loads the active configuration.
    - `write_config(config: Dict[str, Any], global_config: bool = False) -> str`: Writes configuration.
    - `get_llm_backend() -> str`: Determines the current LLM backend.
- The `gitwise init` command provides an interactive way to set up this configuration.

## 5. Prompts (`gitwise.prompts`)

- This module stores the string templates used for interacting with Large Language Models.
- Examples include `PROMPT_COMMIT_MESSAGE`, `PROMPT_PR_DESCRIPTION`, `CHANGELOG_SYSTEM_PROMPT_TEMPLATE`.
- These templates define the instructions and context provided to the AI for tasks like generating commit messages or PR descriptions.

## 6. Command Line Interface (`gitwise.cli`)

- The CLI is built using the [Typer](https://typer.tiangolo.com/) library.
- The main Typer application is defined in `gitwise.cli.__init__.py`.
- Most command handlers (e.g., `gitwise add`, `gitwise commit`) are defined in `gitwise.cli.__init__.py` and delegate their core logic to instances of the corresponding Feature classes from `gitwise.features`.
- The `gitwise init` command logic resides in `gitwise.cli.init.py`.

## Best Practices

*(This section can be retained or updated from the old API doc if relevant to internal development)*

1.  **Commit Messages**: Use conventional commit format.
2.  **Branch Names**: Use prefixes like `feature/`, `fix/`.
3.  **Pull Requests**: Create from feature branches, include clear descriptions.
4.  **Changelog**: Keep `[Unreleased]` up to date, use semantic versioning.

## Error Handling

*(This section can be retained or updated)*

- `GitManager` methods raise `RuntimeError` for failed Git commands, often including stderr.
- Feature classes and CLI commands handle exceptions and display user-friendly error messages via `gitwise.ui.components`.
- Configuration issues raise `ConfigError`.

## Contributing

Contributions to the API and core logic are welcome! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. 