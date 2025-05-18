"""Push command implementation for GitWise."""

import subprocess
from typing import Optional
from gitwise.core import git
from gitwise.ui import components
from gitwise.features.pr import pr_command
import typer

def push_command() -> None:
    """Push changes and optionally create a PR."""
    try:
        # Get current branch
        current_branch = git.get_current_branch()
        if not current_branch:
            components.show_error("Not on any branch")
            return

        # Check if there are commits to push
        with components.show_spinner("Checking for commits..."):
            result = subprocess.run(
                ["git", "log", f"origin/{current_branch}..HEAD"],
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                components.show_warning("No commits to push")
                return

            # Get commits to be pushed
            result = subprocess.run(
                ["git", "log", f"origin/{current_branch}..HEAD", "--oneline"],
                capture_output=True,
                text=True
            )
            commits = result.stdout.strip()

        # Show changes to be pushed
        components.show_section("Changes to Push")
        components.console.print(commits)

        # Ask about pushing
        components.show_prompt(
            "Would you like to push these changes?",
            options=["Yes", "No"],
            default="Yes"
        )
        choice = typer.prompt("", type=int, default=1)

        if choice == 2:  # No
            components.show_warning("Push cancelled")
            return

        # Push changes
        with components.show_spinner("Pushing to remote..."):
            result = subprocess.run(
                ["git", "push", "origin", current_branch],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                components.show_success("Changes pushed successfully")
                
                # Ask about creating PR
                components.show_prompt(
                    "Would you like to create a pull request?",
                    options=["Yes", "No"],
                    default="Yes"
                )
                choice = typer.prompt("", type=int, default=1)
                
                if choice == 1:  # Yes
                    try:
                        # Ask about PR options
                        components.show_prompt(
                            "Would you like to include labels and checklist in the PR?",
                            options=["Yes", "No"],
                            default="Yes"
                        )
                        include_extras = typer.prompt("", type=int, default=1) == 1
                        
                        # Call PR command with user preferences
                        pr_command(
                            use_labels=include_extras,
                            use_checklist=include_extras,
                            skip_general_checklist=not include_extras
                        )
                    except Exception as e:
                        components.show_error(f"Failed to create PR: {str(e)}")
                        # Continue execution since push was successful
            else:
                components.show_error("Failed to push changes")
                if result.stderr:
                    components.console.print(result.stderr)

    except Exception as e:
        components.show_error(str(e)) 