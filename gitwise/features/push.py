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

        # Refresh remote state
        subprocess.run(["git", "fetch", "origin"], capture_output=True, text=True)

        # Check if branch is tracking a remote
        tracking_result = subprocess.run([
            "git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"
        ], capture_output=True, text=True)
        is_tracking = tracking_result.returncode == 0

        if not is_tracking:
            components.show_warning(f"Branch '{current_branch}' is not tracking a remote branch.")
            components.show_prompt(
                f"Would you like to set upstream and push '{current_branch}' to origin?",
                options=["Yes", "No"],
                default="Yes"
            )
            set_upstream = typer.prompt("", type=int, default=1)
            if set_upstream == 1:
                spinner = components.show_spinner(f"Pushing and setting upstream for '{current_branch}'...")
                spinner.start()
                try:
                    result = subprocess.run(
                        ["git", "push", "--set-upstream", "origin", current_branch],
                        capture_output=True,
                        text=True
                    )
                finally:
                    spinner.stop()
                    components.console.line()
                if result.returncode == 0:
                    components.show_success(f"Branch '{current_branch}' is now tracking origin/{current_branch} and pushed.")
                else:
                    components.show_error(f"Failed to push and set upstream: {result.stderr}")
                    return
            else:
                components.show_warning("Push cancelled (no upstream set).")
                return

        # Check if there are commits to push (now that remote is refreshed and tracking is ensured)
        with components.show_spinner("Checking for commits..."):
            result = subprocess.run(
                ["git", "log", f"origin/{current_branch}..HEAD"],
                capture_output=True,
                text=True
            )
            if not result.stdout.strip():
                components.show_warning("No commits to push")
                # After confirming there are no commits to push, still prompt for PR
                components.console.line()
                components.show_prompt(
                    "Would you like to create a pull request?",
                    options=["Yes", "No"],
                    default="Yes"
                )
                pr_choice = typer.prompt("", type=int, default=1)
                components.console.line()
                if pr_choice == 1:
                    try:
                        components.show_prompt(
                            "Would you like to include labels and checklist in the PR?",
                            options=["Yes", "No"],
                            default="Yes"
                        )
                        extras_choice = typer.prompt("", type=int, default=1)
                        include_extras = extras_choice == 1
                        components.console.line()
                        pr_command(
                            use_labels=include_extras,
                            use_checklist=include_extras,
                            skip_general_checklist=not include_extras,
                            skip_prompts=False
                        )
                    except Exception as e:
                        components.show_error(f"Failed to create PR: {str(e)}")
                    return
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
        components.console.line() # Line before prompt
        components.show_prompt(
            "Would you like to push these changes?",
            options=["Yes", "No"],
            default="Yes"
        )
        choice = typer.prompt("", type=int, default=1)
        components.console.line() # Line after prompt

        if choice == 2:  # No
            components.show_warning("Push cancelled")
            return

        # Push changes
        spinner = components.show_spinner("Pushing to remote...")
        spinner.start() # Start the spinner explicitly
        try:
            result = subprocess.run(
                ["git", "push", "origin", current_branch],
                capture_output=True,
                text=True
            )
        finally:
            spinner.stop() # Stop the spinner explicitly in a finally block
            components.console.line() # Ensure a newline after spinner stops to clear its line

        if result.returncode == 0:
            components.show_success("Changes pushed successfully")
            components.console.line() # Ensure clean line before next prompt
            components.show_prompt(
                "Would you like to create a pull request?",
                options=["Yes", "No"],
                default="Yes"
            )
            pr_choice = typer.prompt("", type=int, default=1) # Renamed variable
            components.console.line() # Line after prompt
            if pr_choice == 1:  # Yes
                try:
                    components.show_prompt(
                        "Would you like to include labels and checklist in the PR?",
                        options=["Yes", "No"],
                        default="Yes"
                    )
                    extras_choice = typer.prompt("", type=int, default=1) # Renamed variable
                    include_extras = extras_choice == 1
                    components.console.line() # Line after prompt and before pr_command
                    pr_command(
                        use_labels=include_extras,
                        use_checklist=include_extras,
                        skip_general_checklist=not include_extras, # Corrected logic here
                        skip_prompts=False  # CHANGED: Now allows pr_command to run its full interactive flow
                    )
                except Exception as e:
                    components.show_error(f"Failed to create PR: {str(e)}")
                return
            return
        else:
            components.show_error("Failed to push changes")
            if result.stderr:
                components.console.print(result.stderr)
            return

    except Exception as e:
        components.show_error(str(e)) 