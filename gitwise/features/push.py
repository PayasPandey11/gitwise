"""Push command implementation for GitWise."""

import subprocess
from typing import Optional
from gitwise.core import git
from gitwise.ui import components
from gitwise.features.pr import pr_command

def push_command() -> None:
    """Push changes to remote repository and optionally create a PR."""
    try:
        # Get current branch
        current_branch = git.get_current_branch()
        if not current_branch:
            components.show_error("Not on any branch")
            return

        # Check if there are any commits to push
        with components.show_spinner("Checking for commits to push...") as progress:
            result = subprocess.run(
                ["git", "log", "@{u}.."],
                capture_output=True,
                text=True
            )
            if not result.stdout.strip():
                components.show_warning("No commits to push")
                return

        # Show what will be pushed
        components.show_section("Changes to Push")
        result = subprocess.run(
            ["git", "log", "--oneline", "@{u}.."],
            capture_output=True,
            text=True
        )
        components.console.print(result.stdout)

        # Ask about pushing
        components.show_prompt(
            f"Push to the same branch ({current_branch})?",
            options=["Yes", "No"],
            default="Yes"
        )
        if not subprocess.run(["git", "push"], capture_output=True).returncode == 0:
            components.show_error("Failed to push changes")
            return

        components.show_success("Changes pushed successfully")

        # Ask about creating PR
        components.show_prompt(
            "Would you like to create a pull request?",
            options=["Yes", "No"],
            default="No"
        )
        if subprocess.run(["git", "push", "--set-upstream", "origin", current_branch], capture_output=True).returncode == 0:
            pr_command()
        else:
            components.show_error("Failed to set upstream branch")

    except Exception as e:
        components.show_error(str(e)) 