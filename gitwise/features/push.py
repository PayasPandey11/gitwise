"""Push command implementation for GitWise."""

import subprocess
from typing import Optional
from gitwise.core import git
from gitwise.core.git import get_default_remote_branch
from gitwise.ui import components
from gitwise.features.pr import pr_command
import typer
from gitwise.config import get_llm_backend, load_config, ConfigError

def push_command() -> bool:
    """Push changes to remote and optionally create a PR. Returns True if PR was created or already exists."""
    try:
        # Config check
        try:
            load_config()
        except ConfigError as e:
            components.show_error(str(e))
            if typer.confirm("Would you like to run 'gitwise init' now?", default=True):
                from gitwise.cli.init import init_command
                init_command()
            return False

        # Get current branch
        current_branch = git.get_current_branch()
        if not current_branch:
            components.show_error("Not on any branch")
            return False

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
                    return False
            else:
                components.show_warning("Push cancelled (no upstream set).")
                return False

        # Get default remote branch (always remote-tracking)
        default_remote_branch = get_default_remote_branch()

        # Push changes
        with components.show_spinner("Pushing changes..."):
            result = subprocess.run(["git", "push"], capture_output=True, text=True)
            if result.returncode == 0:
                components.show_success("Changes pushed successfully")
            else:
                components.show_error("Failed to push changes")
                if result.stderr:
                    components.console.print(result.stderr)
                return False

        # Check if there are commits to push (now that remote is refreshed and tracking is ensured)
        with components.show_spinner("Checking for commits..."):
            result = subprocess.run(
                ["git", "log", f"{default_remote_branch}..HEAD"],
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
                        pr_created = pr_command(
                            use_labels=include_extras,
                            use_checklist=include_extras,
                            skip_general_checklist=not include_extras,
                            skip_prompts=False,
                            base=default_remote_branch # always remote-tracking branch
                        )
                        return pr_created
                    except Exception as e:
                        components.show_error(f"Failed to create PR: {str(e)}")
                        return False
                return False

        # After push, prompt for PR
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
                pr_created = pr_command(
                    use_labels=include_extras,
                    use_checklist=include_extras,
                    skip_general_checklist=not include_extras,
                    skip_prompts=False,
                    base=default_remote_branch # always remote-tracking branch
                )
                return pr_created
            except Exception as e:
                components.show_error(f"Failed to create PR: {str(e)}")
                return False
        return False
    except Exception as e:
        components.show_error(str(e))
        return False 