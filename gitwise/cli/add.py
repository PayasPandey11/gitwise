"""Add command implementation for GitWise."""

import os
from typing import List
import typer
from ..core import git
from ..ui import components
from ..features.commit import commit_command
from ..features.push import push_command

def add_command(
    files: List[str] = None,
    # group: bool = False # Parameter not used
) -> None:
    """Stage files and prepare for commit with smart grouping."""
    try:
        # Check for unstaged changes
        with components.show_spinner("Checking for changes...") as progress:
            unstaged = git.get_unstaged_files()
            if not unstaged:
                components.show_section("Status")
                components.show_warning("No changes found to stage.")
                components.console.print("\n[dim]Use [cyan]git status[/cyan] to see repository state[/dim]")
                return

        # Stage files
        with components.show_spinner("Staging files...") as progress:
            if not files or (len(files) == 1 and files[0] == '.'):
                if not git.stage_all():
                    components.show_error("Failed to stage files")
                    return
            else:
                failed_files = []
                for file in files:
                    if os.path.exists(file):
                        if not git.stage_file(file):
                            components.show_error(f"Failed to stage file: {file}")
                            failed_files.append(file)
                    else:
                        components.show_error(f"File not found: {file}")
                        failed_files.append(file)
                
                if failed_files:
                    components.show_warning(f"Could not stage the following files: {', '.join(failed_files)}")
                    # Current logic proceeds even if some files fail to stage.

        # Show staged changes
        staged = git.get_staged_files()
        if staged:
            components.show_section("Staged Changes")
            components.show_files_table(staged)

            # Show current LLM backend to the user
            backend = os.environ.get("GITWISE_LLM_BACKEND", "ollama").lower()
            backend_display = {
                "ollama": "Ollama (local server)",
                "offline": "Offline (local model)",
                "online": "Online (OpenRouter)"
            }.get(backend, backend)
            components.show_section(f"[AI] LLM Backend: {backend_display}")

            while True:
                options = [
                    ("commit", "Create commit with these changes"),
                    ("diff", "View full diff of staged changes"),
                    ("quit", "Quit and leave files staged")
                ]
                components.show_menu(options)
                
                choice_map = {1: "commit", 2: "diff", 3: "quit"}
                user_choice_num = typer.prompt("Select an option", type=int, default=1)
                action = choice_map.get(user_choice_num)

                if action == "commit":
                    commit_command()
                    # After commit, offer to push
                    if git.get_current_branch():
                        if typer.confirm("Push these changes?", default=True):
                            push_command()
                    break
                elif action == "diff":
                    full_diff = git.get_staged_diff()
                    if full_diff:
                        components.show_section("Full Staged Changes")
                        components.show_diff(full_diff)
                    else:
                        components.show_warning("No staged changes to diff.")
                elif action == "quit":
                    components.show_warning("Operation cancelled. Files remain staged.")
                    break
                else:
                    components.show_error("Invalid choice. Please try again.")
        else:
            components.show_section("Status")
            components.show_warning("No files were staged.")
            components.console.print("\n[dim]Use [cyan]git status[/cyan] to see repository state[/dim]")
            
    except Exception as e:
        components.show_error(str(e))
        components.console.print("\n[dim]Please try again or use [cyan]git add[/cyan] directly.[/dim]") 