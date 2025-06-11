"""Push command implementation for GitWise."""

from typing import Optional

import typer

from ..config import ConfigError, load_config
from ..core.git_manager import GitManager
from ..features.pr import PrFeature  # UPDATED from pr_command
from ..ui import components


class PushFeature:
    """Handles the logic for pushing changes to a remote repository and optionally creating a pull request."""

    def __init__(self):
        """Initializes the PushFeature with a GitManager instance."""
        self.git_manager = GitManager()

    def execute_push(self, auto_confirm: bool = False) -> bool:
        """Push changes to remote and optionally create a PR. Returns True if PR was created or already exists."""
        try:
            # Config check
            try:
                load_config()
            except ConfigError as e:
                from ..cli.init import init_command

                components.show_error(str(e))
                if typer.confirm(
                    "Would you like to run 'gitwise init' now?", default=True
                ):
                    init_command()
                return False

            # Get current branch
            current_branch = self.git_manager.get_current_branch()
            if not current_branch:
                components.show_error("Not on any branch")
                return False

            # Refresh remote state
            try:
                self.git_manager._run_git_command(["fetch", "origin"], check=False)
            except RuntimeError as e:
                components.show_warning(f"Could not fetch from origin: {e}")

            tracking_result = self.git_manager._run_git_command(
                ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
                check=False,
                capture_output=True,
                text=True,
            )
            is_tracking = tracking_result.returncode == 0

            if not is_tracking:
                components.show_warning(
                    f"Branch '{current_branch}' is not tracking a remote branch."
                )
                components.show_prompt(
                    f"Would you like to set upstream and push '{current_branch}' to origin?",
                    options=["Yes", "No"],
                    default="Yes",
                )
                set_upstream = (1 if auto_confirm else typer.prompt("", type=int, default=1))
                if set_upstream == 1:
                    spinner = components.show_spinner(
                        f"Pushing and setting upstream for '{current_branch}'..."
                    )
                    spinner.start()
                    push_success_upstream = False
                    try:
                        result = self.git_manager._run_git_command(
                            ["push", "--set-upstream", "origin", current_branch],
                            check=False,
                        )
                        push_success_upstream = result.returncode == 0
                    finally:
                        spinner.stop()
                        components.console.line()
                    if push_success_upstream:
                        components.show_success(
                            f"Branch '{current_branch}' is now tracking origin/{current_branch} and pushed."
                        )
                    else:
                        error_message = (
                            result.stderr
                            if hasattr(result, "stderr") and result.stderr
                            else "Unknown error during push --set-upstream"
                        )
                        components.show_error(
                            f"Failed to push and set upstream: {error_message}"
                        )
                        return False
                else:
                    components.show_warning("Push cancelled (no upstream set).")
                    return False

            default_remote_branch_name_only = (
                self.git_manager.get_default_remote_branch_name()
            )
            if not default_remote_branch_name_only:
                components.show_error(
                    "Could not determine the default remote branch. Please check your remote configuration."
                )
                return False

            default_remote_for_log = f"origin/{default_remote_branch_name_only}"

            # Push changes first
            with components.show_spinner("Pushing changes..."):
                push_success_main = self.git_manager.push_to_remote(
                    local_branch=current_branch
                )
            if push_success_main:
                components.show_success("Changes pushed successfully")
            else:
                components.show_error("Failed to push changes")
                return False

            # Check if there are new commits to create a PR for
            commits_to_push = self.git_manager.get_commits_between(
                default_remote_for_log, "HEAD"
            )

            if not commits_to_push:
                components.show_warning(
                    "No new commits to push relative to the default branch. "
                    "Use 'gitwise pr' to create a PR from staged files instead."
                )
                return True # Push was successful, no new commits to create a PR for.

            # Ask to create a PR
            should_create_pr = False
            if auto_confirm:
                # On main/master, don't auto-create a PR
                if current_branch == self.git_manager.get_local_base_branch_name():
                    components.show_section("Auto-confirm: Skipping PR creation (on default branch)")
                else:
                    components.show_section("Auto-confirm: Creating PR")
                    should_create_pr = True
            else:
                should_create_pr = typer.confirm(
                    "Would you like to create a pull request for the commits you just pushed?",
                    default=True,
                )

            if should_create_pr:
                try:
                    # The new `pr` command works from staged files, not previous commits.
                    # We should instruct the user to use the `pr` command directly.
                    components.show_section("Create a Pull Request")
                    components.console.print(
                        "The `push` command no longer creates PRs directly.\n"
                        "To create a PR with AI-generated commits, please run:"
                    )
                    components.console.print("\n[bold cyan]gitwise pr[/bold cyan]\n")
                    return True # Indicate that the push was successful
                except Exception as e:
                    components.show_error(f"An unexpected error occurred: {str(e)}")
                    return False

            return True  # Push was successful, user opted out of PR

        except Exception as e:
            components.show_error(str(e))
            return False
