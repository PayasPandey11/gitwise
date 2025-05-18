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
    group: bool = False
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
                for file in files:
                    if os.path.exists(file):
                        if not git.stage_file(file):
                            components.show_error(f"Failed to stage file: {file}")
                    else:
                        components.show_error(f"File not found: {file}")

        # Show staged changes
        staged = git.get_staged_files()
        if staged:
            components.show_section("Staged Changes")
            components.show_files_table(staged)

            # Show diff for each file
            for status, file in staged:
                diff = git.get_file_diff(file)
                if diff:
                    components.show_diff(diff, f"Changes in {file}")

            # Show menu
            options = [
                ("", "Create commit"),
                ("", "Review changes"),
                ("", "Quit")
            ]
            components.show_menu(options)
            
            choice = typer.prompt("", type=int, default=1)
            
            if choice == 1:
                commit_command(group=group)
                # After commit, offer to push
                components.show_prompt(
                    "Push these changes?",
                    options=["Yes", "No"],
                    default="Yes"
                )
                if typer.confirm("", default=True):
                    push_command()
            elif choice == 2:
                # Show full diff
                diff = git.get_staged_diff()
                if diff:
                    components.show_section("Full Changes")
                    components.show_diff(diff)
            else:
                components.show_warning("Operation cancelled.")
        else:
            components.show_section("Status")
            components.show_warning("No files were staged.")
            components.console.print("\n[dim]Use [cyan]git status[/cyan] to see repository state[/dim]")
            
    except Exception as e:
        components.show_error(str(e))
        components.console.print("\n[dim]Please try again or use [cyan]git add[/cyan] directly.[/dim]") 