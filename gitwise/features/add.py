"""Feature logic for the 'add' command."""
import os
from typing import List

import typer  # For typer.confirm, typer.prompt

from gitwise.config import ConfigError, get_llm_backend, load_config

from ..core.git_manager import GitManager
from ..features.commit import CommitFeature  # commit_command is called by add
from ..features.push import PushFeature  # push_command is called by add
from ..ui import components


class AddFeature:
    """Handles the logic for staging files and an interactive workflow."""

    def __init__(self):
        """Initializes the AddFeature with a GitManager instance."""
        self.git_manager = GitManager()

    def execute_add(self, files: List[str] = None) -> None:
        """Stage files and prepare for commit with smart grouping."""
        try:
            # Config check - Note: direct call to init_command from features might be debatable design-wise
            # but keeping existing behavior for now.
            try:
                load_config()
            except ConfigError as e:
                from ..cli.init import init_command # Moved import here
                components.show_error(str(e))
                if typer.confirm(
                    "Would you like to run 'gitwise init' now?", default=True
                ):
                    init_command()  # Calling init_command from gitwise.cli.init
                return

            # Check for unstaged changes
            with components.show_spinner("Checking for changes..."):
                unstaged = self.git_manager.get_unstaged_files()
                if not unstaged:
                    components.show_section("Status")
                    components.show_warning("No changes found to stage.")
                    components.console.print(
                        "\n[dim]Use [cyan]git status[/cyan] to see repository state[/dim]"
                    )
                    return

            # Stage files
            with components.show_spinner("Staging files..."):
                if not files or (len(files) == 1 and files[0] == "."):
                    if not self.git_manager.stage_all():
                        components.show_error("Failed to stage files")
                        return
                else:
                    found_files = []
                    failed_to_find = []
                    failed_to_stage = []
                    for file in files:
                        if os.path.exists(file):
                            found_files.append(file)
                        else:
                            components.show_error(f"File not found: {file}")
                            failed_to_find.append(file)
                    
                    if found_files: # Only proceed if some files were found
                        for file_to_stage in found_files:
                            if not self.git_manager.stage_files([file_to_stage]):
                                components.show_error(f"Failed to stage file: {file_to_stage}")
                                failed_to_stage.append(file_to_stage)
                    
                    if failed_to_find or failed_to_stage:
                        error_messages = []
                        if failed_to_find:
                            error_messages.append(f"Could not find: {', '.join(failed_to_find)}")
                        if failed_to_stage:
                             error_messages.append(f"Could not stage: {', '.join(failed_to_stage)}")
                        components.show_warning("; ".join(error_messages))

            # Show staged changes
            staged = self.git_manager.get_staged_files()
            if staged:
                components.show_section("Staged Changes")
                components.show_files_table(staged)

                backend = get_llm_backend()
                backend_display = {
                    "ollama": "Ollama (local server)",
                    "offline": "Offline (local model)",
                    "online": "Online (OpenRouter)",
                }.get(backend, backend)
                components.show_section(f"[AI] LLM Backend: {backend_display}")

                while True:
                    options = [
                        ("commit", "Create commit with these changes"),
                        ("diff", "View full diff of staged changes"),
                        ("quit", "Quit and leave files staged"),
                    ]
                    components.show_menu(options)

                    choice_map = {1: "commit", 2: "diff", 3: "quit"}
                    user_choice_num = typer.prompt(
                        "Select an option", type=int, default=1
                    )
                    action = choice_map.get(user_choice_num)

                    if action == "commit":
                        commit_feature_instance = CommitFeature()
                        commit_feature_instance.execute_commit()
                        break
                    elif action == "diff":
                        full_diff = self.git_manager.get_staged_diff()
                        if full_diff:
                            components.show_section("Full Staged Changes")
                            components.show_diff(full_diff)
                        else:
                            components.show_warning("No staged changes to diff.")
                    elif action == "quit":
                        components.show_warning(
                            "Operation cancelled. Files remain staged."
                        )
                        break
                    else:
                        components.show_error("Invalid choice. Please try again.")
            else:
                components.show_section("Status")
                components.show_warning("No files were staged.")
                components.console.print(
                    "\n[dim]Use [cyan]git status[/cyan] to see repository state[/dim]"
                )

        except Exception as e:
            components.show_error(str(e))
            # Consider logging the full traceback here for debugging
            components.console.print(
                "\n[dim]An error occurred in the add command. Please try again or use [cyan]git add[/cyan] directly.[/dim]"
            )
