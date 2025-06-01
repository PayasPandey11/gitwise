"""PR enhancement features for GitWise."""

import json
import os
import re
from typing import Dict, List, Optional, Set, Tuple

from ..core.git_manager import GitManager

# Initialize GitManager at module level
git_manager = GitManager()

# Default mapping of commit types to GitHub labels
DEFAULT_COMMIT_TYPE_LABELS = {
    "feat": "enhancement",
    "fix": "bug",
    "docs": "documentation",
    "style": "style",
    "refactor": "refactor",
    "test": "test",
    "chore": "chore",
    "perf": "performance",
    "security": "security",
    "ci": "ci",
    "build": "build",
    "revert": "revert",
}

# Extended file patterns and their checklist items
FILE_PATTERN_CHECKLISTS = {
    r"\.py$": [
        "Added/updated docstrings",
        "Added/updated type hints",
        "Added/updated tests",
        "Updated README if needed",
        "Checked for unused imports",
        "Verified error handling",
        "Added logging if needed",
    ],
    r"\.md$": [
        "Checked for broken links",
        "Verified formatting",
        "Updated table of contents if needed",
        "Checked for proper heading hierarchy",
        "Verified code block syntax",
        "Added alt text for images",
    ],
    r"\.json$": [
        "Validated JSON format",
        "Updated schema if needed",
        "Checked for sensitive data",
        "Verified indentation",
    ],
    r"\.yaml$|\.yml$": [
        "Validated YAML format",
        "Updated schema if needed",
        "Checked for sensitive data",
        "Verified indentation",
        "Checked for duplicate keys",
    ],
    r"\.js$|\.ts$": [
        "Added/updated JSDoc comments",
        "Added/updated tests",
        "Updated README if needed",
        "Checked for unused variables",
        "Verified error handling",
        "Added type definitions if needed",
    ],
    r"\.css$|\.scss$": [
        "Checked browser compatibility",
        "Added/updated comments",
        "Updated style guide if needed",
        "Verified responsive design",
        "Checked for unused styles",
        "Added vendor prefixes if needed",
    ],
    r"\.html$": [
        "Verified accessibility",
        "Checked for proper meta tags",
        "Validated HTML structure",
        "Checked for broken links",
        "Verified responsive design",
    ],
    r"\.sql$": [
        "Added/updated documentation",
        "Checked for SQL injection risks",
        "Verified indexes",
        "Added migration script if needed",
        "Checked for sensitive data",
    ],
    r"\.sh$": [
        "Added/updated documentation",
        "Checked for proper error handling",
        "Verified file permissions",
        "Added shebang line",
        "Checked for shell compatibility",
    ],
    r"\.dockerfile$|Dockerfile": [
        "Added/updated documentation",
        "Checked for security best practices",
        "Verified base image version",
        "Added health check if needed",
        "Checked for unnecessary layers",
    ],
    r"\.env$|\.env\.": [
        "Checked for sensitive data",
        "Added to .gitignore if needed",
        "Provided example file",
        "Updated documentation",
    ],
    r"\.gitignore$": [
        "Checked for necessary patterns",
        "Verified no important files ignored",
        "Added comments for clarity",
    ],
    r"\.editorconfig$": [
        "Verified settings match project",
        "Added comments for clarity",
        "Checked for necessary rules",
    ],
    r"\.eslintrc$|\.prettierrc$": [
        "Verified settings match project",
        "Added comments for clarity",
        "Checked for necessary rules",
    ],
    r"\.github/workflows/.*\.yml$": [
        "Verified workflow triggers",
        "Checked for necessary permissions",
        "Added comments for clarity",
        "Verified environment variables",
    ],
}


def load_custom_labels() -> Dict[str, str]:
    """Load custom label mappings from config file.

    Returns:
        Dictionary mapping commit types to custom labels.
    """
    config_path = os.path.expanduser("~/.gitwise/labels.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Invalid labels.json file. Using default labels.")
    return {}


def extract_commit_types(commits: List[Dict[str, str]]) -> Set[str]:
    """Extract commit types from commit messages.

    Args:
        commits: List of commit dictionaries containing message.

    Returns:
        Set of commit types found in the messages.
    """
    types = set()
    for commit in commits:
        # Match conventional commit format: type(scope): description
        match = re.match(r"^(\w+)(?:\([^)]+\))?:", commit["message"])
        if match:
            commit_type = match.group(1)
            if commit_type in DEFAULT_COMMIT_TYPE_LABELS:
                types.add(commit_type)
    return types


def get_pr_labels(
    commits: List[Dict[str, str]], use_custom_labels: bool = True
) -> List[str]:
    """Get GitHub labels based on commit types.

    Args:
        commits: List of commit dictionaries containing message.
        use_custom_labels: Whether to use custom label mappings.

    Returns:
        List of GitHub labels to apply.
    """
    commit_types = extract_commit_types(commits)
    labels = DEFAULT_COMMIT_TYPE_LABELS.copy()

    if use_custom_labels:
        custom_labels = load_custom_labels()
        labels.update(custom_labels)

    return [labels[type_] for type_ in commit_types if type_ in labels]


def get_changed_files(base_branch: str = None) -> List[str]:
    """Get list of files changed in the PR.

    Args:
        base_branch: The base branch to compare against (e.g., "origin/main", "origin/develop").

    Returns:
        List of changed file paths.
    """
    # import subprocess # REMOVE: No longer needed here

    effective_base_branch = base_branch
    if effective_base_branch is None:
        try:
            # GitManager instance is now at module level
            effective_base_branch = git_manager.get_default_remote_branch_name()
            if not effective_base_branch:
                print(
                    "Error: Could not determine default remote branch for checklist. Falling back to 'main'."
                )
                effective_base_branch = "main"
            # For comparison with git diff, it's often origin/main
            if not effective_base_branch.startswith(
                "origin/"
            ) and effective_base_branch in ["main", "master", "develop"]:
                effective_base_branch = f"origin/{effective_base_branch}"
        except Exception as e:
            print(
                f"Error: Could not determine default remote branch for checklist: {e}. Falling back to 'origin/main'."
            )
            effective_base_branch = "origin/main"  # Fallback

    try:
        current_branch = git_manager.get_current_branch()
        if not current_branch:
            print(
                "Error: Could not determine current branch for diff. Returning empty list."
            )
            return []

        # Diff current branch against the determined base branch
        # Using format base_branch..current_branch for git diff
        diff_command = [
            "diff",
            "--name-only",
            f"{effective_base_branch}..{current_branch}",
        ]
        result = git_manager._run_git_command(diff_command, check=True)  # UPDATED
        return [f for f in result.stdout.splitlines() if f]
    except RuntimeError as e:
        print(
            f"Warning: Could not get changed files using base '{effective_base_branch}': {e}. Attempting fallback."
        )
        try:
            # Fallback: diff staged changes against HEAD (less accurate for PR context but a last resort)
            # This typically shows what *would* be committed if one ran `git commit` now.
            # For a PR checklist, it might be better to show files from commits on the branch.
            # However, get_changed_file_paths_staged() is for *staged* changes.
            # A better fallback for PR files might be a broader log.
            # For now, sticking to a simple diff against a common ancestor or recent history if all else fails.

            # Let's try diffing against the merge base with origin/main as a common fallback target
            # This is more aligned with typical PR diffs than just HEAD.
            fallback_base = git_manager.get_merge_base("origin/main", "HEAD")
            if fallback_base:
                diff_command_fallback = [
                    "diff",
                    "--name-only",
                    f"{fallback_base}..HEAD",
                ]
                result = git_manager._run_git_command(diff_command_fallback, check=True)
                print(
                    f"Warning: Fallback diff is against merge-base with origin/main ('{fallback_base}'). This may not represent all PR changes accurately."
                )
                return [f for f in result.stdout.splitlines() if f]
            else:  # Ultimate fallback: last N commit changes (not ideal for PR file list)
                print(
                    "Warning: Could not determine a reliable base for diff. Listing files from last 5 commits (approximate)."
                )
                commits_data = git_manager.get_commits_between("HEAD~5", "HEAD")
                files = set()
                for commit_dict in commits_data:
                    # This requires parsing diff of each commit, which is complex.
                    # Simplification: if GitManager could give files per commit, or using git log --name-only per commit.
                    # For now, this fallback is very approximate and might be removed if too unreliable.
                    # A simpler fallback is to return empty list if primary diff fails dramatically.
                    pass  # Placeholder - this part of fallback is hard to implement well here.
                print(
                    "Error: Fallback for changed files list is not fully implemented. Returning empty for safety."
                )
                return []  # Safer to return empty than inaccurate list here.

        except RuntimeError as e_fallback:
            print(
                f"Error: Could not get changed files for checklist generation even with fallback: {e_fallback}"
            )
            return []


def generate_checklist(files: List[str], skip_general: bool = False) -> str:
    """Generate a checklist based on changed files.

    Args:
        files: List of changed file paths.
        skip_general: Whether to skip general checklist items.

    Returns:
        Markdown formatted checklist.
    """
    checklist_items = set()

    # Add items based on file patterns
    for file in files:
        for pattern, items in FILE_PATTERN_CHECKLISTS.items():
            if re.search(pattern, file):
                checklist_items.update(items)

    # Add general items if not skipped
    if not skip_general:
        checklist_items.update(
            [
                "Code follows project style guide",
                "All tests pass",
                "Documentation is up to date",
                "No sensitive data in changes",
                "Changes are backward compatible",
                "Performance impact considered",
                "Security implications reviewed",
            ]
        )

    # Format as markdown checklist
    return "\n".join(f"- [ ] {item}" for item in sorted(checklist_items))


def enhance_pr_description(
    commits: List[Dict[str, str]],
    description: str,
    use_labels: bool = False,
    use_checklist: bool = False,
    skip_general_checklist: bool = False,
    base_branch_for_checklist: str = "origin/main",
) -> Tuple[str, List[str]]:
    """Enhance PR description with labels and checklist.

    Args:
        commits: List of commit dictionaries.
        description: Original PR description.
        use_labels: Whether to add labels (default: False).
        use_checklist: Whether to add checklist (default: False).
        skip_general_checklist: Whether to skip general checklist items (default: False).
        base_branch_for_checklist: The base branch to use for generating the checklist.

    Returns:
        Tuple of (enhanced description, labels)
    """
    enhanced_description = description
    labels = []

    # Get labels if enabled
    if use_labels:
        labels = get_pr_labels(commits)

    # Get changed files and generate checklist if enabled
    if use_checklist:
        files = get_changed_files(base_branch=base_branch_for_checklist)
        if files:
            checklist = generate_checklist(files, skip_general_checklist)
            enhanced_description = f"{description}\n\n## Checklist\n{checklist}"

    return enhanced_description, labels
