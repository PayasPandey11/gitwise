"""Feature logic for the 'commit' command, including AI-assisted message generation and grouping."""

import os
import subprocess
import tempfile
import re
from typing import Callable, Dict, List, Optional, Any

import typer

from gitwise.config import ConfigError, get_llm_backend, load_config
from gitwise.core.git_manager import GitManager
from gitwise.features.context import ContextFeature
from gitwise.llm.router import get_llm_response
from gitwise.prompts import PROMPT_COMMIT_MESSAGE, PROMPT_PR_DESCRIPTION
from gitwise.ui import components
from gitwise.llm.offline import ensure_offline_model_ready
from gitwise.features.push import PushFeature

# Initialize GitManager
git_manager = GitManager()


# Import push_command only when needed to avoid circular imports
def get_push_command() -> Callable[[bool], bool]:
    """Dynamically imports and returns the push_command function to avoid circular imports."""
    from gitwise.features.push import PushFeature

    def push_wrapper(auto_confirm: bool = False) -> bool:
        return PushFeature().execute_push(auto_confirm=auto_confirm)

    return push_wrapper


COMMIT_TYPES = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "chore": "Changes to the build process or auxiliary tools",
    "ci": "Changes to CI configuration files and scripts",
    "build": "Changes that affect the build system or external dependencies",
    "revert": "Reverts a previous commit",
}


def safe_prompt(prompt_text: str, options: List[str], default: str = "Yes") -> int:
    """Prompt for user input using Typer with predefined options."""
    components.show_prompt(prompt_text, options=options, default=default)
    choice = typer.prompt("", type=int, default=1)
    return choice


def safe_confirm(prompt_text: str, default: bool = True) -> bool:
    """Prompt for confirmation using Typer."""
    return typer.confirm(prompt_text, default=default)


def safe_prompt_text(prompt_text: str, default: str = "") -> str:
    """Prompt for text input using Typer."""
    return typer.prompt(prompt_text, default=default)


def suggest_scope(changed_files: List[str]) -> str:
    """Suggest a scope based on the most common directory among changed files."""
    dirs = {}
    for file in changed_files:
        dir_name = os.path.dirname(file)
        if dir_name:
            dirs[dir_name] = dirs.get(dir_name, 0) + 1

    if dirs:
        return max(dirs, key=dirs.get)
    return ""


def build_commit_message_interactive() -> str:
    """Interactively build a conventional commit message."""
    changed_files = git_manager.get_changed_file_paths_staged()

    typer.echo("\nSelect commit type:")
    for type_key, desc in COMMIT_TYPES.items():
        typer.echo(f"  {type_key:<10} - {desc}")

    commit_type = safe_prompt_text("\nEnter commit type", default="feat").lower()

    suggested_scope = suggest_scope(changed_files)
    scope = safe_prompt_text("Enter scope (optional)", default=suggested_scope)

    description = safe_prompt_text("Enter commit description")

    body = safe_prompt_text(
        "Enter commit body (optional, press Enter to skip)", default=""
    )

    breaking_changes = ""
    if safe_confirm("Are there any breaking changes?", default=False):
        breaking_changes = safe_prompt_text("Describe the breaking changes")

    message = f"{commit_type}"
    if scope:
        message += f"({scope})"
    message += f": {description}"

    if body:
        message += f"\n\n{body}"

    if breaking_changes:
        message += f"\n\nBREAKING CHANGE: {breaking_changes}"

    return message


def analyze_changes(changed_files: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze changed files to find patterns for grouping.
    Returns a list of suggested commit groups.
    """
    # Group files by directory
    dir_groups = {}
    for file in changed_files:
        dir_name = file.split("/")[0] if "/" in file else "root"
        if dir_name not in dir_groups:
            dir_groups[dir_name] = []
        dir_groups[dir_name].append(file)

    # Create commit suggestions
    suggestions = []
    for dir_name, files in dir_groups.items():
        if len(files) >= 2:  # Only suggest groups with 2+ files
            suggestions.append({"type": "directory", "name": dir_name, "files": files})

    # Check for common patterns
    test_files = [f for f in changed_files if "test" in f.lower()]
    if len(test_files) >= 2:
        suggestions.append({"type": "tests", "name": "Test files", "files": test_files})

    doc_files = [
        f
        for f in changed_files
        if any(ext in f.lower() for ext in [".md", ".rst", ".txt", "readme"])
    ]
    if len(doc_files) >= 2:
        suggestions.append(
            {"type": "docs", "name": "Documentation", "files": doc_files}
        )

    return suggestions


def suggest_commit_groups() -> Optional[List[Dict[str, Any]]]:
    """
    Suggests ways to group staged changes into separate commits.
    Returns None if no good grouping is found.
    """
    try:
        staged = git_manager.get_staged_files()
        if len(staged) < 3:  # Not worth grouping if less than 3 files
            return None

        # Get just the file paths
        staged_paths = [file for _, file in staged]

        # Analyze for patterns
        groups = analyze_changes(staged_paths)

        # Only return if we found meaningful groups
        if groups and len(groups) >= 2:
            return groups
        return None
    except Exception:
        return None


def generate_commit_message(diff: str, guidance: str = "") -> str:
    """Generates a commit message using the LLM."""
    context = ContextFeature().get_context_for_ai_prompt() or ""
    if context:
        guidance = f"{context}\n{guidance}".strip()
    prompt = PROMPT_COMMIT_MESSAGE.replace("{{diff}}", diff).replace("{{guidance}}", guidance)
    return get_llm_response(prompt).strip()


def _get_pr_commits(base_branch: str) -> List[Dict]:
    """Return commits unique to the current branch."""
    try:
        merge_base = git_manager.get_merge_base(base_branch, "HEAD")
        if not merge_base:
            return []
        return git_manager.get_commits_between(merge_base, "HEAD")
    except Exception:
        return []


def _generate_pr_title(commits: List[Dict]) -> str:
    """Generate a PR title from the first commit."""
    if not commits:
        return "New Pull Request"
    return commits[0]["message"].split("\n")[0]


def _generate_pr_description_llm(commits: List[Dict]) -> str:
    """Generate a PR description from a list of commits."""
    guidance = ContextFeature().get_context_for_ai_prompt() or ""
    formatted_commits = "\n".join([f"- {c['message']}" for c in commits])
    prompt = PROMPT_PR_DESCRIPTION.replace("{{commits}}", formatted_commits).replace(
        "{{guidance}}", guidance
    )
    llm_output = get_llm_response(prompt)
    return llm_output.strip() if llm_output else ""


def _create_gh_pr(title: str, body: str, base: str, current_branch: str):
    """Creates a pull request using the gh CLI."""
    cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        components.show_success("Pull request created successfully by gh CLI.")
        components.console.print(f"[bold green]PR URL: {result.stdout.strip()}[/bold green]")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        components.show_error(f"Failed to create pull request: {e}")


def _create_pr_flow(auto_confirm: bool):
    """The full PR creation flow, called after a push."""
    components.show_section("Create a Pull Request")
    base = git_manager.get_default_remote_branch_name()
    branch = git_manager.get_current_branch()
    if not base or not branch:
        components.show_error("Could not determine branches for PR.")
        return

    commits = _get_pr_commits(f"origin/{base}")
    if not commits:
        components.show_warning("No new commits found to create a PR for.")
        return

    title = _generate_pr_title(commits)
    body = _generate_pr_description_llm(commits)
    if not body:
        return

    components.console.print(f"\n[bold]Title:[/bold] {title}")
    components.console.print(f"[bold]Body:[/bold]\n{body}\n")

    if auto_confirm or typer.confirm("Create this PR?", default=True):
        _create_gh_pr(title, body, base, branch)


class CommitFeature:
    """Handles the logic for creating commits, with AI assistance and grouping."""

    def __init__(self):
        """Initializes the CommitFeature, using the module-level GitManager."""
        self.git_manager = git_manager

    def execute_commit(self, group: bool = False, auto_confirm: bool = False, create_pr: bool = False) -> None:
        """Creates a commit, then offers to push and create a PR."""
        if not self.git_manager.get_changed_file_paths_staged():
            components.show_warning("No files staged for commit.")
            return

        # Grouping logic is complex and was causing issues.
        # For this fix, we will focus on the single-commit-then-pr flow.
        # A future task can be to restore the multi-group commit flow.
        
        diff = self.git_manager.get_staged_diff()
        if not diff:
            components.show_error("Could not get diff of staged files.")
            return

        commit_message = generate_commit_message(diff)
        components.show_section("Suggested Commit Message")
        components.console.print(f"[cyan]{commit_message}[/cyan]")
        
        if not auto_confirm and not typer.confirm("\nUse this commit message?", default=True):
            components.show_warning("Commit cancelled.")
            return

        if self.git_manager.create_commit(commit_message):
            components.show_success("✓ Git commit created successfully")
            if create_pr:
                self._push_and_pr_flow(auto_confirm)
        else:
            components.show_error("✗ Failed to create Git commit")

    def _push_and_pr_flow(self, auto_confirm: bool):
        """Handles the post-commit flow for pushing and creating a PR."""
        if PushFeature().execute_push(auto_confirm=auto_confirm):
            _create_pr_flow(auto_confirm)


# This is the old command function, to be replaced by calls to CommitFeature().execute_commit()
# def commit_command(group: bool = True) -> None:
#    feature = CommitFeature()
#    feature.execute_commit(group=group)

# The generate_commit_message function is now generate_commit_message_llm to avoid naming conflicts if we move it into the class
# and it should be called by an instance method if it uses self, or passed instance of git_manager etc.
# For now, it's a module-level helper using the module-level git_manager instance for its sub-calls (analyze_changes -> get_file_diff_staged).
