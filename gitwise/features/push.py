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

            with components.show_spinner("Pushing changes..."):
                push_success_main = self.git_manager.push_to_remote(
                    local_branch=current_branch
                )

                if push_success_main:
                    components.show_success("Changes pushed successfully")
                else:
                    components.show_error("Failed to push changes")
                    return False

            with components.show_spinner("Checking for commits..."):
                commits_to_push = self.git_manager.get_commits_between(
                    default_remote_for_log, "HEAD"
                )

                if not commits_to_push:
                    components.show_warning(
                        "No new commits to push relative to remote default branch."
                    )
                    components.console.line()
                    # Determine if we should create a PR even with no new commits
                    should_create_pr_anyway = False
                    if auto_confirm:
                        # Check if we're on main/master branch
                        current_branch = self.git_manager.get_current_branch()
                        default_branch = self.git_manager.get_local_base_branch_name()
                        if current_branch and default_branch and current_branch == default_branch:
                            components.show_section("Auto-confirm: Skipping PR creation (on main branch)")
                            should_create_pr_anyway = False
                        else:
                            components.show_section("Auto-confirm: Creating PR anyway (no new commits)")
                            should_create_pr_anyway = True
                    else:
                        should_create_pr_anyway = typer.confirm(
                            "Would you like to create a pull request anyway?", default=True
                        )
                    
                    if should_create_pr_anyway:
                        try:
                            include_extras = (True if auto_confirm else typer.confirm(
                                "Include labels and checklist in the PR?", default=True
                            ))
                            components.console.line()
                            pr_feature_instance = PrFeature()  # Create instance
                            pr_created = pr_feature_instance.execute_pr(  # Call method
                                use_labels=include_extras,
                                use_checklist=include_extras,
                                skip_general_checklist=not include_extras,
                                skip_prompts=auto_confirm,
                                auto_confirm=auto_confirm,
                                base=default_remote_branch_name_only,
                            )
                            return pr_created
                        except Exception as e:
                            components.show_error(f"Failed to create PR: {str(e)}")
                            return False
                    return False

            components.console.line()
            
            # Determine if we should create a PR
            should_create_pr = False
            if auto_confirm:
                # Check if we're on main/master branch
                current_branch = self.git_manager.get_current_branch()
                default_branch = self.git_manager.get_local_base_branch_name()
                if current_branch and default_branch and current_branch == default_branch:
                    components.show_section("Auto-confirm: Skipping PR creation (on main branch)")
                    should_create_pr = False
                else:
                    components.show_section("Auto-confirm: Creating PR with labels and checklist")
                    should_create_pr = True
            else:
                should_create_pr = typer.confirm("Would you like to create a pull request?", default=True)
            
            if should_create_pr:
                try:
                    include_extras = (True if auto_confirm else typer.confirm(
                        "Include labels and checklist in the PR?", default=True
                    ))
                    components.console.line()
                    pr_feature_instance = PrFeature()  # Create instance
                    pr_created = pr_feature_instance.execute_pr(  # Call method
                        use_labels=include_extras,
                        use_checklist=include_extras,
                        skip_general_checklist=not include_extras,
                        skip_prompts=auto_confirm,
                        auto_confirm=auto_confirm,
                        base=default_remote_branch_name_only,
                    )
                    return pr_created
                except Exception as e:
                    components.show_error(f"Failed to create PR: {str(e)}")
                    return False
            return True  # Push was successful, user opted out of PR. This is a successful completion.
        except Exception as e:
            components.show_error(str(e))
            return False
