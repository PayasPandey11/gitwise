"""Push command implementation for GitWise."""

from typing import Optional

import typer

from ..core.git_manager import GitManager
from ..ui import components


class PushFeature:
    """Handles the logic for pushing changes to a remote repository."""

    def __init__(self):
        """Initializes the PushFeature with a GitManager instance."""
        self.git_manager = GitManager()

    def execute_push(self, auto_confirm: bool = False) -> bool:
        """Pushes the current branch to the remote repository."""
        current_branch = self.git_manager.get_current_branch()
        if not current_branch:
            components.show_error("Not on any branch, cannot push.")
            return False

        # Check if the branch is tracking a remote
        is_tracking = self.git_manager.is_branch_tracking()

        if not is_tracking:
            prompt = f"Branch '{current_branch}' is not tracking a remote. Set upstream and push to origin?"
            if not auto_confirm and not typer.confirm(prompt, default=True):
                components.show_warning("Push cancelled.")
                return False
            
            with components.show_spinner(f"Pushing and setting upstream for '{current_branch}'..."):
                if self.git_manager.push_to_remote(local_branch=current_branch, set_upstream=True):
                    components.show_success(f"Branch '{current_branch}' pushed and tracking 'origin/{current_branch}'.")
                else:
                    components.show_error("Failed to push and set upstream.")
                    return False
        else:
            with components.show_spinner(f"Pushing changes for branch '{current_branch}'..."):
                if self.git_manager.push_to_remote(local_branch=current_branch):
                    components.show_success("Changes pushed successfully.")
                else:
                    components.show_error("Failed to push changes.")
                    return False
        
        return True
