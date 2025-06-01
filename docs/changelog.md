# Changelog Feature Documentation

The changelog feature in GitWise provides automated changelog generation and management. It helps maintain a clear record of changes in your project by automatically categorizing commits and generating well-formatted changelog entries via AI assistance.

## Core Functionality

The primary interaction with the changelog feature is through the `gitwise changelog` command-line interface. Internally, this is handled by the `gitwise.features.changelog.ChangelogFeature` class.

### Key Capabilities

-   **Automatic Version Suggestion**: Suggests the next semantic version based on commit history.
-   **AI-Powered Content Generation**: Uses LLMs to summarize commits and generate user-friendly changelog entries.
-   **Conventional Commit Support**: Works best with conventional commit messages for smart categorization (Features, Bug Fixes, etc.).
-   **Automated File Updates**: Modifies `CHANGELOG.md` to add new version sections or update an `[Unreleased]` section.
-   **Tagging**: Optionally creates a Git tag for the new version.
-   **Pre-commit Hook**: Provides a setup command (`gitwise setup-hooks`) to install a Git pre-commit hook that can automatically update the `[Unreleased]` section.

## Main Interface: `ChangelogFeature`

The core logic resides in `gitwise.features.changelog.ChangelogFeature`:

```python
from gitwise.features.changelog import ChangelogFeature

# How it's typically invoked by the CLI:
# feature = ChangelogFeature()
# feature.execute_changelog(
#     version="v1.2.3", 
#     output_file="CHANGELOG.md", 
#     format_output="markdown", 
#     auto_update=False
# )
```

-   **`execute_changelog(self, version: Optional[str], output_file: Optional[str], format_output: str, auto_update: bool) -> None`**
    -   This is the main method called by the CLI.
    -   It orchestrates fetching commits (via `GitManager`), generating content (via `llm.router`), interacting with the user for versioning and edits, and writing to the changelog file.
    -   Handles logic for `--auto-update` (for the `[Unreleased]` section) and for generating specific version releases.

*(Internal helper functions within `changelog.py` (like `_get_unreleased_commits_as_dicts`, `_generate_changelog_llm_content`, `_write_version_to_changelog`, `_create_version_tag`, etc.) handle the detailed steps, using `GitManager` for Git operations and `get_llm_response` for AI interaction.)*

## Command Line Interface

### `gitwise changelog [OPTIONS]`

Generates or updates a changelog for the repository.

**Options:**
-   `--version TEXT`: Specify the version string for the new changelog section (e.g., `v1.0.0`). If omitted, GitWise will suggest one.
-   `--output-file TEXT`: Path to the changelog file (default: `CHANGELOG.md`).
-   `--format TEXT`: Output format (currently only `markdown` is supported, which is the default).
-   `--auto-update`: Automatically update the `[Unreleased]` section in the changelog without prompts. Typically used with the pre-commit hook.
-   `--help`: Show help message.

**Examples:**
```bash
# Generate changelog for a new version (interactive)
gitwise changelog

# Generate changelog for a specific version
gitwise changelog --version v1.2.3

# Automatically update the [Unreleased] section (for hooks)
gitwise changelog --auto-update
```

### `gitwise setup-hooks`

Installs a Git pre-commit script (`.git/hooks/pre-commit`) that attempts to run `gitwise changelog --auto-update` before each commit. This helps maintain an up-to-date pending changelog. If you use the `pre-commit` framework, manage GitWise through your `.pre-commit-config.yaml` instead.

## Best Practices

1.  **Use Conventional Commits**: Start commit messages with types like `feat:`, `fix:`, `docs:`, etc., for better automatic categorization.
2.  **Version Tags**: Use semantic versioning for tags (e.g., `v1.0.0`). GitWise can create these for you when generating a versioned changelog entry.
3.  **Changelog Maintenance**: Regularly update the `[Unreleased]` section (e.g., via the hook) and review entries before tagging a release.

## Release Process Example

1.  Ensure your `[Unreleased]` section is up-to-date (commits will automatically update it if the hook is installed, or run `gitwise changelog --auto-update` manually).
2.  Run `gitwise changelog` and confirm the suggested version or provide one.
3.  Allow GitWise to create the version tag when prompted.
4.  Push your commits and the new tag (`git push --follow-tags`).

## Troubleshooting

-   **Missing Version Tags**: Ensure tags are created (GitWise can do this) and follow semantic versioning.
-   **Commit Hook Issues**: Verify hook installation with `gitwise setup-hooks`. Check `.git/hooks/pre-commit` for content and execute permissions. Ensure `gitwise` is in the `PATH` for the hook environment.
-   **Changelog Format**: Ensure `CHANGELOG.md` exists (GitWise will create/update it). For best results with automated updates, maintain a top-level `# Changelog` title and an `## [Unreleased]` section.

## Contributing

Contributions to the changelog feature are welcome! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. 