"""Changelog generation feature for GitWise."""

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional, Tuple

import typer

from ..config import ConfigError, get_llm_backend, load_config
from ..core.git_manager import GitManager
from ..llm.offline import ensure_offline_model_ready
from ..llm.router import get_llm_response
from ..prompts import (CHANGELOG_SYSTEM_PROMPT_TEMPLATE,
                       CHANGELOG_USER_PROMPT_TEMPLATE)
from ..ui import components

git_manager = GitManager()


class VersionInfo(NamedTuple):
    """Version information with pre-release and build metadata."""

    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None
    build_metadata: Optional[str] = None

    def __lt__(self, other: "VersionInfo") -> bool:
        """Compare versions according to semver spec."""
        # Compare main version numbers
        if (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        ):
            return True
        if (self.major, self.minor, self.patch) > (
            other.major,
            other.minor,
            other.patch,
        ):
            return False

        # If main versions are equal, compare pre-release
        if self.pre_release is None and other.pre_release is None:
            return False
        if self.pre_release is None:
            return False  # No pre-release is greater than pre-release
        if other.pre_release is None:
            return True  # Pre-release is less than no pre-release

        # Compare pre-release identifiers
        self_parts = self.pre_release.split(".")
        other_parts = other.pre_release.split(".")

        for i in range(max(len(self_parts), len(other_parts))):
            if i >= len(self_parts):
                return True  # Shorter pre-release is less
            if i >= len(other_parts):
                return False  # Longer pre-release is greater

            # Try to compare as numbers first
            try:
                self_num = int(self_parts[i])
                other_num = int(other_parts[i])
                if self_num != other_num:
                    return self_num < other_num
            except ValueError:
                # Compare as strings if not numbers
                if self_parts[i] != other_parts[i]:
                    return self_parts[i] < other_parts[i]

        return False


def _get_latest_tag() -> Optional[str]:
    """
    Retrieves the latest git tag.

    Returns:
        The latest tag as a string, or None if no tags are found.
    """
    result = git_manager._run_git_command(["tag", "--sort=-v:refname"], check=False)
    tags = (
        [tag for tag in result.stdout.splitlines() if tag]
        if result.returncode == 0
        else []
    )
    return tags[0] if tags else None


def _get_commits_since_tag_as_dicts(tag: str) -> List[Dict[str, str]]:
    """
    Retrieves commits made since a specific tag.

    Args:
        tag: The tag to get commits since.

    Returns:
        A list of commit dictionaries.
    """
    return git_manager.get_commits_between(tag, "HEAD")


def _get_all_commits_current_branch_as_dicts() -> List[Dict[str, str]]:
    """
    Retrieves all commits from the current branch (not on default remote).

    Returns:
        A list of commit dictionaries.
    """
    default_remote_branch = git_manager.get_default_remote_branch_name()
    base = "HEAD~1000"  # Deep fallback if no remote or merge base
    if default_remote_branch:
        remote_base = f"origin/{default_remote_branch}"
        merge_base = git_manager.get_merge_base(remote_base, "HEAD")
        if merge_base:
            base = merge_base
    return git_manager.get_commits_between(base, "HEAD")


def _get_unreleased_commits_as_dicts() -> List[Dict[str, str]]:
    """
    Retrieves all commits that have not been released (since last tag or all).

    Returns:
        A list of commit dictionaries.
    """
    latest_tag = _get_latest_tag()
    if latest_tag:
        return _get_commits_since_tag_as_dicts(latest_tag)
    else:
        return _get_all_commits_current_branch_as_dicts()


def _summarize_commits_for_changelog(commits_msgs: List[str]) -> str:
    """
    Summarizes a list of commit messages for a changelog using an LLM.
    """
    commits_str = "\n".join(commits_msgs)
    prompt = f"Generate a concise changelog summary from the following commit messages:\n{commits_str}\n\nFocus on user-facing changes and group related items. Use markdown format."
    summary = get_llm_response(prompt=prompt, max_tokens=500)
    return summary


def _get_repository_info() -> Dict[str, str]:
    """Get repository information.

    Returns:
        Dictionary with repository information.
    """
    info = {}

    try:
        # Get repository URL using GitManager
        url_result = git_manager._run_git_command(
            ["config", "--get", "remote.origin.url"], check=False
        )
        info["url"] = url_result.stdout.strip() if url_result.returncode == 0 else ""
    except RuntimeError:
        info["url"] = ""  # Could not get URL

    # Get repository name
    if info["url"]:
        # Extract name from URL
        match = re.search(r"[:/]([^/]+/[^/]+?)(?:\\.git)?$", info["url"])
        if match:
            info["name"] = match.group(1)
        else:  # Default if parsing fails
            info["name"] = "repository"
    else:  # Default if no URL
        info["name"] = "repository"

    return info


def _get_version_tags_sorted() -> List[str]:
    """Get all version tags from the repository.

    Returns:
        List of version tags sorted by creation date.
    """
    result = git_manager._run_git_command(["tag", "--sort=-creatordate"], check=False)
    return (
        [tag for tag in result.stdout.splitlines() if tag]
        if result.returncode == 0
        else []
    )


def get_commits_between_tags(
    start_tag: Optional[str], end_tag: str
) -> List[Dict[str, str]]:
    """Get commits between two tags.

    Args:
        start_tag: Starting tag (exclusive). If None, gets all commits up to end_tag.
        end_tag: Ending tag (inclusive).

    Returns:
        List of commit dictionaries.
    """
    return git_manager.get_commits_between(start_tag or end_tag, end_tag)


def _categorize_changes(
    commits: List[Dict[str, str]]
) -> Dict[str, List[Dict[str, str]]]:
    """Categorize commits by type.

    Args:
        commits: List of commit dictionaries.

    Returns:
        Dictionary mapping commit types to lists of commits.
    """
    categories = {
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Style": [],
        "Refactor": [],
        "Performance": [],
        "Tests": [],
        "Chores": [],
        "Other": [],
    }

    type_mapping = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "docs": "Documentation",
        "style": "Style",
        "refactor": "Refactor",
        "perf": "Performance",
        "test": "Tests",
        "chore": "Chores",
    }

    for commit in commits:
        message = commit["message"]
        # Check for conventional commit format
        if ":" in message:
            type_ = message.split(":")[0].lower()
            if type_ in type_mapping:
                categories[type_mapping[type_]].append(commit)
                continue
        categories["Other"].append(commit)

    return categories


def _generate_changelog_llm_content(
    commits: List[Dict], version: Optional[str] = None
) -> str:
    """Generate a changelog from commits using an LLM."""
    commit_text = "\n".join(
        [f"- {commit['message']} ({commit['author']})" for commit in commits]
    )

    # Get repository info
    repo_info = _get_repository_info()
    repo_name = repo_info.get("name", "the repository")

    # Generate changelog using LLM
    prompt_version_guidance = (
        f"Generate the detailed changelog entries for version {version} of {repo_name}. "
        if version
        else f"Generate a summary of recent changes for {repo_name}. "
    )

    system_prompt = CHANGELOG_SYSTEM_PROMPT_TEMPLATE.format(repo_name=repo_name)
    user_prompt = CHANGELOG_USER_PROMPT_TEMPLATE.format(
        guidance_text=prompt_version_guidance, commit_text=commit_text
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        llm_content = get_llm_response(messages)

        return (
            llm_content.strip()
        )  # Just the content, header added by _write_version_to_changelog
    except Exception as e:
        components.show_error(f"Could not generate changelog content via LLM: {str(e)}")
        return ""


def _write_version_to_changelog(
    changelog_path: str, version_content: str, version_header_str: str
):
    """Writes a given version block (header + content) into the changelog file."""
    existing_content = ""
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    date = datetime.now().strftime("%Y-%m-%d")
    full_version_block = (
        f"## {version_header_str} ({date})\n{version_content.strip()}\n\n"
    )

    updated_content = ""
    changelog_title_text = "# Changelog"
    # Regex to find an existing [Unreleased] section or any version header to insert before
    # It tries to find [Unreleased], then any ## vX.Y.Z, then the main # Changelog title, then beginning of file.
    insertion_regex = re.compile(
        r"(^##\s+\[Unreleased\].*?)(?=^##\s+v?\d+\.\d+\.\d+|^\Z)|(^##\s+v?\d+\.\d+\.\d+)|(^{}\s*\n(?:\n)?)".format(
            re.escape(changelog_title_text)
        ),
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )

    match = insertion_regex.search(existing_content)
    inserted = False
    if match:
        if match.group(1):  # Found [Unreleased], insert after it
            insert_point = match.end(1)
            updated_content = (
                existing_content[:insert_point].rstrip()
                + "\n\n"
                + full_version_block
                + existing_content[insert_point:].lstrip()
            )
            inserted = True
        elif match.group(2):  # Found existing version, insert before it
            insert_point = match.start(2)
            updated_content = (
                existing_content[:insert_point]
                + full_version_block
                + existing_content[insert_point:]
            )
            inserted = True
        elif match.group(3):  # Found # Changelog title, insert after it
            insert_point = match.end(3)
            updated_content = (
                existing_content[:insert_point]
                + full_version_block
                + existing_content[insert_point:]
            )
            inserted = True

    if not inserted:  # Nothing found or empty file, prepend title if needed and add
        if not existing_content.strip().startswith(changelog_title_text):
            updated_content = (
                changelog_title_text + "\n\n" + full_version_block + existing_content
            )
        else:
            updated_content = (
                existing_content.rstrip() + "\n\n" + full_version_block
            )  # Ensure space if appending

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(updated_content.strip() + "\n")


def _create_version_tag(
    version: str, commits_for_message: List[Dict[str, str]]
) -> None:
    """Create a version tag.

    Args:
        version: Version string.
        commits_for_message: List of commit dictionaries for tag message.
    """
    message_parts = []
    if commits_for_message:
        categories = _categorize_changes(commits_for_message)
        for category, cat_commits in categories.items():
            if cat_commits:
                message_parts.append(f"{category}:")
                for commit in cat_commits[:3]:  # Top 3 per category for tag message
                    msg_body = (
                        commit["message"].split(":", 1)[1].strip()
                        if ":" in commit["message"]
                        else commit["message"]
                    )
                    message_parts.append(f"- {msg_body}")
                if len(cat_commits) > 3:
                    message_parts.append(f"- ... and {len(cat_commits) - 3} more")
                message_parts.append("")
    message = (
        "\n".join(message_parts).strip() or f"Release {version}"
    )  # Default message if no categorized changes
    try:
        git_manager._run_git_command(["tag", "-a", version, "-m", message], check=True)
        components.show_success(f"Created version tag: {version}")
    except RuntimeError as e:
        components.show_error(f"Failed to create version tag {version}: {e}")


def _update_unreleased_changelog_section(changelog_path: str = "CHANGELOG.md") -> None:
    """Update the unreleased section of the changelog."""
    commits = _get_unreleased_commits_as_dicts()
    if not commits:
        return

    existing_content = ""
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    # Generate unreleased section
    categories = _categorize_changes(commits)
    unreleased_lines = ["## [Unreleased]", ""]
    has_content = False
    for category, cat_commits in categories.items():
        if cat_commits:
            has_content = True
            unreleased_lines.append(f"### {category}")
            unreleased_lines.append("")
            for commit in cat_commits:
                msg_body = (
                    commit["message"].split(":", 1)[1].strip()
                    if ":" in commit["message"]
                    else commit["message"]
                )
                unreleased_lines.append(f"- {msg_body}")
            unreleased_lines.append("")

    if not has_content:
        unreleased_lines.append("- No changes yet.")
        unreleased_lines.append("")
    new_unreleased_section = "\n".join(unreleased_lines).strip() + "\n\n"

    pattern = re.compile(
        r"(##\s+\[Unreleased\].*?)(?=^##\s+v?\d+\.\d+\.\d+|^\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(existing_content)
    updated_content = ""
    changelog_title_text = "# Changelog"

    if match:
        updated_content = (
            existing_content[: match.start()]
            + new_unreleased_section
            + existing_content[match.end() :].lstrip()
        )
    else:
        title_match = re.match(
            rf"(^{re.escape(changelog_title_text)}\s*\n(?:\n)?)",
            existing_content,
            re.IGNORECASE,
        )
        if title_match:
            insert_point = title_match.end(0)
            updated_content = (
                existing_content[:insert_point]
                + new_unreleased_section
                + existing_content[insert_point:]
            )
        else:  # No title, or title not at start
            updated_content = (
                f"{changelog_title_text}\n\n{new_unreleased_section}{existing_content}"
            )

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(updated_content.strip() + "\n")


def _commit_hook() -> None:
    """Git commit hook to update changelog."""
    try:
        _update_unreleased_changelog_section()
    except Exception as e:
        print(f"Warning: Could not update changelog: {str(e)}")


def _setup_commit_hook() -> None:
    """Set up git commit hook for automatic changelog updates."""
    hook_path = os.path.join(
        git_manager.repo_path or ".", ".git", "hooks", "pre-commit"
    )
    hook_content = """#!/bin/sh
# GitWise pre-commit hook to update [Unreleased] changelog section.
# To disable, remove this file or make it non-executable.
echo "[GitWise] Running pre-commit hook for changelog..."
# Ensure gitwise is in PATH or use full path if installed in a venv not on system PATH
# This might require user to configure their environment or the hook correctly.
# A safer bet for hooks is often to call a script from the repo itself.
# For now, assuming 'gitwise' command is available.
if command -v gitwise >/dev/null 2>&1; then
    gitwise changelog --auto-update
    if [ $? -ne 0 ]; then
        echo "[GitWise] Warning: Changelog auto-update failed. Please check manually."
    fi
    # Add CHANGELOG.md if it was modified by the hook
    if [ -n "$(git status --porcelain CHANGELOG.md)" ]; then
        git add CHANGELOG.md
    fi
else
    echo "[GitWise] Warning: 'gitwise' command not found in PATH. Cannot auto-update changelog."
fi
"""

    # Create hook directory if it doesn't exist
    os.makedirs(os.path.dirname(hook_path), exist_ok=True)

    # Write hook file
    with open(hook_path, "w") as f:
        f.write(hook_content)

    # Make hook executable
    os.chmod(hook_path, 0o755)
    print("✅ Git commit hook installed for automatic changelog updates")


def _parse_version(version_str: str) -> Optional[VersionInfo]:
    """Parse version string into components.

    Args:
        version_str: Version string (e.g., "v1.2.3-alpha.1+build.123").

    Returns:
        VersionInfo tuple with version components or None if parsing fails.

    Raises:
        ValueError: If version format is invalid (though currently returns None).
    """
    if not version_str:
        return None
    version_str = version_str.lstrip("v")
    main_version, *extras = version_str.split("+", 1)
    build_metadata = extras[0] if extras else None
    main_version, *pre_release_parts = main_version.split("-", 1)
    pre_release = pre_release_parts[0] if pre_release_parts else None
    try:
        major, minor, patch = map(int, main_version.split("."))
        if pre_release and not re.match(r"^[0-9A-Za-z\.-]+$", pre_release):
            # Slightly more permissive regex for pre-release like 1.0.0-alpha.beta, 1.0.0-rc.1
            raise ValueError("Invalid pre-release format")
        return VersionInfo(major, minor, patch, pre_release, build_metadata)
    except ValueError:
        return None


def _format_version(version_info: VersionInfo) -> str:
    """Formats a VersionInfo object into a string (e.g., v1.2.3-alpha.1)."""
    version_str = f"v{version_info.major}.{version_info.minor}.{version_info.patch}"
    if version_info.pre_release:
        version_str += f"-{version_info.pre_release}"
    if version_info.build_metadata:
        version_str += f"+{version_info.build_metadata}"
    return version_str


def _analyze_commits_for_version_bump(commits: List[Dict[str, str]]) -> Dict[str, bool]:
    """Analyzes commits to determine the type of version bump needed."""
    analysis = {
        "has_breaking": False,
        "has_feature": False,
        "has_fix": False,
        "has_docs": False,
        "has_perf": False,
        "has_refactor": False,
        "has_test": False,
        "has_style": False,
        "has_chore": False,
    }

    for commit in commits:
        message = commit["message"].lower()

        # Check for breaking changes
        if "!" in message or "breaking" in message:
            analysis["has_breaking"] = True

        # Check commit types
        if message.startswith("feat:"):
            analysis["has_feature"] = True
        elif message.startswith("fix:"):
            analysis["has_fix"] = True
        elif message.startswith("docs:"):
            analysis["has_docs"] = True
        elif message.startswith("perf:"):
            analysis["has_perf"] = True
        elif message.startswith("refactor:"):
            analysis["has_refactor"] = True
        elif message.startswith("test:"):
            analysis["has_test"] = True
        elif message.startswith("style:"):
            analysis["has_style"] = True
        elif message.startswith("chore:"):
            analysis["has_chore"] = True

    return analysis


def _suggest_next_version(commits: List[Dict[str, str]]) -> Tuple[str, str]:
    """Suggests the next semantic version based on commit analysis."""
    # Get latest version
    latest_version_str = _get_latest_tag()
    if not latest_version_str:
        return "v0.1.0", "First release"

    try:
        current_version = _parse_version(latest_version_str)
    except ValueError:
        return (
            "v0.1.0",
            f"Invalid current version format ('{latest_version_str}'), suggesting v0.1.0",
        )

    # Analyze commits
    analysis = _analyze_commits_for_version_bump(commits)

    # Determine version bump and explanation
    if analysis["has_breaking"]:
        new_val = VersionInfo(current_version.major + 1, 0, 0)
        explanation = "Breaking changes detected"
    elif analysis["has_feature"]:
        new_val = VersionInfo(current_version.major, current_version.minor + 1, 0)
        explanation = "New features added"
    elif any([analysis["has_fix"], analysis["has_perf"], analysis["has_refactor"]]):
        new_val = VersionInfo(
            current_version.major, current_version.minor, current_version.patch + 1
        )
        explanation = "Bug fixes and improvements"
    else:
        new_val = VersionInfo(
            current_version.major, current_version.minor, current_version.patch + 1
        )
        explanation = "Minor changes and updates"

    return _format_version(new_val), explanation


def _validate_version_input(
    version_str: str, current_version_str_opt: Optional[str] = None
) -> Optional[str]:
    """Validates and normalize version input.

    Args:
        version: User input version string.
        current_version: Current version to compare against.

    Returns:
        Normalized version string or None if invalid.
    """
    parsed_new_version = _parse_version(version_str)
    if not parsed_new_version:
        components.show_error(
            f"Invalid version format: '{version_str}'. Must be e.g., vX.Y.Z, X.Y.Z, vX.Y.Z-alpha.1"
        )
        return None
    normalized_version_str = (
        version_str if version_str.startswith("v") else f"v{version_str}"
    )
    # Re-parse after ensuring 'v' prefix for consistent VersionInfo object for comparison
    parsed_new_version_for_comp = _parse_version(normalized_version_str)
    if not parsed_new_version_for_comp:  # Should not happen if first parse was okay
        components.show_error("Internal error during version validation.")
        return None

    if current_version_str_opt:
        parsed_current_version = _parse_version(current_version_str_opt)
        if (
            parsed_current_version
            and parsed_new_version_for_comp <= parsed_current_version
        ):
            components.show_error(
                f"New version {normalized_version_str} must be greater than current version: {current_version_str_opt}"
            )
            return None
    return normalized_version_str


class ChangelogFeature:
    """Handles the generation and management of changelogs."""

    def __init__(self):
        """Initializes the ChangelogFeature with a GitManager instance."""
        self.git_manager = git_manager

    def execute_changelog(
        self,
        version: Optional[str] = None,
        output_file: Optional[str] = None,
        format_output: str = "markdown",
        auto_update: bool = False,
    ) -> None:
        """Main logic for generating or updating a changelog."""
        if format_output != "markdown":
            components.show_error(
                "Only markdown format is currently supported for changelog."
            )
            return
        try:
            load_config()
        except ConfigError as e:
            components.show_error(str(e))
            if typer.confirm("Would you like to run 'gitwise init' now?", default=True):
                from ..cli.init import init_command

                init_command()
            return

        if get_llm_backend() != "online":
            try:
                ensure_offline_model_ready()
            except Exception as e:
                components.show_error(f"Failed to load/prepare offline model: {e}")
                return

        try:
            if auto_update and not version:
                components.show_section("Auto-updating [Unreleased] Changelog")
                with components.show_spinner("Updating [Unreleased] section..."):
                    try:
                        path_to_update = output_file or "CHANGELOG.md"
                        _update_unreleased_changelog_section(changelog_path=path_to_update)
                    except Exception as e:
                        components.show_error(
                            f"Failed to auto-update changelog: {str(e)}"
                        )
                return

            components.show_section("Analyzing Commits for Changelog")
            with components.show_spinner("Checking for recent commits..."):
                commits = _get_unreleased_commits_as_dicts()
                if not commits:
                    components.show_warning(
                        "No new commits found to generate changelog entries."
                    )
                    return

            target_version = version
            if not target_version:
                latest_tag_str = _get_latest_tag()
                suggested_v, reason = _suggest_next_version(commits)
                components.show_prompt(
                    f"No version specified. Current latest is {latest_tag_str or 'None'}. Suggested next: {suggested_v} (reason: {reason})",
                    options=[
                        "Use suggested version",
                        "Enter version manually",
                        "Cancel",
                    ],
                    default="Use suggested version",
                )
                choice = typer.prompt("Selection", type=int, default=1)
                if choice == 1:
                    target_version = suggested_v
                elif choice == 2:
                    version_input_str = typer.prompt(
                        "Enter version (e.g., v1.2.3 or 1.2.3)"
                    )
                    target_version = _validate_version_input(
                        version_input_str, current_version_str_opt=latest_tag_str
                    )
                    if not target_version:
                        return
                else:
                    components.show_warning("Changelog generation cancelled.")
                    return
            else:
                validated_target_version = _validate_version_input(
                    target_version, current_version_str_opt=_get_latest_tag()
                )
                if not validated_target_version:
                    return
                target_version = validated_target_version

            components.show_section(f"Commits for Version {target_version}")
            for commit in commits:
                components.console.print(
                    f"[bold cyan]{commit['hash'][:7]}[/bold cyan] {commit['message']}"
                )

            components.show_section(
                f"Generating Changelog Entries for {target_version}"
            )
            with components.show_spinner("Asking AI to draft changelog entries..."):
                new_version_llm_content = _generate_changelog_llm_content(
                    commits, target_version
                )

            if not new_version_llm_content.strip():
                components.show_error(
                    "LLM failed to generate changelog content. Please check LLM backend or try again."
                )
                return

            components.show_section(f"Drafted Content for {target_version}")
            # Display LLM content with a temporary header for context
            temp_display_content = (
                f"## {target_version} (Preview Date)\n{new_version_llm_content}"
            )
            components.console.print(temp_display_content)

            final_content_for_file = new_version_llm_content

            if not auto_update:
                components.show_prompt(
                    f"Review the content for {target_version}. Add to {output_file or 'CHANGELOG.md'}?",
                    options=[
                        "Yes, add as is",
                        "Edit content before adding",
                        "No, cancel",
                    ],
                    default="Yes, add as is",
                )
                user_choice = typer.prompt("Selection", type=int, default=1)
                if user_choice == 3:
                    components.show_warning("Changelog update cancelled.")
                    return
                if user_choice == 2:
                    with tempfile.NamedTemporaryFile(
                        suffix=".md", delete=False, mode="w+", encoding="utf-8"
                    ) as tf:
                        tf.write(final_content_for_file.strip())
                        tf.flush()
                    editor = os.environ.get("EDITOR", "vi")
                    try:
                        subprocess.run([editor, tf.name], check=True)
                        with open(tf.name, "r", encoding="utf-8") as f_read:
                            final_content_for_file = f_read.read().strip()
                    except Exception as e_edit:
                        components.show_error(f"Error during edit: {e_edit}")
                    finally:
                        if os.path.exists(tf.name):
                            os.unlink(tf.name)
                    components.show_section(
                        f"Edited Content for {target_version} (body only)"
                    )
                    components.console.print(final_content_for_file)
                    if not typer.confirm(
                        "Proceed with adding this edited content body?", default=True
                    ):
                        components.show_warning(
                            "Changelog update cancelled after edit."
                        )
                        return

            if not final_content_for_file.strip():
                components.show_error("Changelog content is empty. Aborting update.")
                return

            target_changelog_filename = output_file or "CHANGELOG.md"
            components.show_section(f"Updating {target_changelog_filename}")
            with components.show_spinner(f"Saving to {target_changelog_filename}..."):
                try:
                    _write_version_to_changelog(
                        target_changelog_filename,
                        final_content_for_file,
                        target_version,
                    )
                    components.show_success(
                        f"Changelog successfully updated in {target_changelog_filename}"
                    )
                    if not auto_update and typer.confirm(
                        f"Create git tag '{target_version}' for this release?",
                        default=True,
                    ):
                        _create_version_tag(target_version, commits_for_message=commits)
                except Exception as e_write:
                    components.show_error(
                        f"Failed to update {target_changelog_filename}: {str(e_write)}"
                    )
        except Exception as e_outer:
            components.show_error(f"Changelog command failed: {str(e_outer)}")
            import traceback

            components.console.print(f"[dim]{traceback.format_exc()}[/dim]")


# Remove the old changelog_command function entirely
# def changelog_command(...): was here
