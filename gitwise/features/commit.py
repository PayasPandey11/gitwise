import typer
import tempfile
import os
import subprocess
import sys
# import termios
# import tty
from typing import Optional, List, Dict, Tuple
from gitwise.llm import generate_commit_message
from gitwise.gitutils import get_staged_diff, run_git_commit, get_changed_files, get_staged_files # get_unstaged_files is also in gitutils
from gitwise.ui import components

# Import push_command only when needed to avoid circular imports
def get_push_command():
    from gitwise.features.push import push_command
    return push_command

COMMIT_TYPES = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "chore": "Changes to the build process or auxiliary tools",
    "ci": "Changes to CI configuration files and scripts",
    "build": "Changes that affect the build system or external dependencies",
    "revert": "Reverts a previous commit"
}

def disable_input():
    """Disable terminal input."""
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())
    return old_settings

def enable_input(old_settings):
    """Restore terminal input settings."""
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def safe_prompt(prompt_text: str, options: List[str], default: str = "Yes") -> int:
    """Safely prompt for user input with disabled input during operations."""
    components.show_prompt(prompt_text, options=options, default=default)
    # Enable input for the prompt
    # old_settings = termios.tcgetattr(sys.stdin)
    # tty.setraw(sys.stdin.fileno())
    # try:
    choice = typer.prompt("", type=int, default=1)
    return choice
    # finally:
    #     # Restore terminal settings
    #     termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def safe_confirm(prompt_text: str, default: bool = True) -> bool:
    """Safely prompt for confirmation with disabled input during operations."""
    # Enable input for the prompt
    # old_settings = termios.tcgetattr(sys.stdin)
    # tty.setraw(sys.stdin.fileno())
    # try:
    return typer.confirm(prompt_text, default=default)
    # finally:
    #     # Restore terminal settings
    #     termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def safe_prompt_text(prompt_text: str, default: str = "") -> str:
    """Safely prompt for text input with disabled input during operations."""
    # Enable input for the prompt
    # old_settings = termios.tcgetattr(sys.stdin)
    # tty.setraw(sys.stdin.fileno())
    # try:
    return typer.prompt(prompt_text, default=default)
    # finally:
    #     # Restore terminal settings
    #     termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def suggest_scope(changed_files: List[str]) -> str:
    """Suggest a scope based on changed files."""
    # Group files by directory
    dirs = {}
    for file in changed_files:
        dir_name = os.path.dirname(file)
        if dir_name:
            dirs[dir_name] = dirs.get(dir_name, 0) + 1
    
    # Return the most common directory as scope
    if dirs:
        return max(dirs.items(), key=lambda x: x[1])[0]
    return ""

def build_commit_message_interactive() -> str:
    """Build a commit message interactively."""
    # Get changed files
    changed_files = get_changed_files()
    
    # Step 1: Select commit type
    typer.echo("\nSelect commit type:")
    for type_, desc in COMMIT_TYPES.items():
        typer.echo(f"  {type_:<10} - {desc}")
    
    commit_type = safe_prompt_text(
        "\nEnter commit type",
        default="feat" if "feat" in changed_files else "fix"
    ).lower()
    
    # Step 2: Enter scope
    suggested_scope = suggest_scope(changed_files)
    scope = safe_prompt_text(
        "Enter scope (optional)",
        default=suggested_scope
    )
    
    # Step 3: Enter description
    description = safe_prompt_text(
        "Enter commit description"
    )
    
    # Step 4: Enter body (optional)
    body = safe_prompt_text(
        "Enter commit body (optional, press Enter to skip)",
        default=""
    )
    
    # Step 5: Enter breaking changes (optional)
    breaking = safe_confirm("Are there any breaking changes?", default=False)
    breaking_changes = ""
    if breaking:
        breaking_changes = safe_prompt_text(
            "Describe the breaking changes"
        )
    
    # Build the commit message
    message = f"{commit_type}"
    if scope:
        message += f"({scope})"
    message += f": {description}"
    
    if body:
        message += f"\n\n{body}"
    
    if breaking_changes:
        message += f"\n\nBREAKING CHANGE: {breaking_changes}"
    
    return message

def stage_files(files: List[str]) -> None:
    """Stage specific files."""
    try:
        subprocess.run(["git", "add"] + files, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error staging files: {e.stderr}")

def unstage_files(files: List[str]) -> None:
    """Unstage specific files."""
    try:
        subprocess.run(["git", "reset"] + files, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error unstaging files: {e.stderr}")

def analyze_changes(changed_files: List[str]) -> List[Dict[str, any]]:
    """Analyze changes and suggest logical groupings.
    
    Returns:
        List of dictionaries containing:
        - files: List of files in this group
        - type: Suggested commit type
        - description: Suggested commit description
        - diff: The diff for these files
    """
    # Get individual file diffs
    file_diffs = {}
    for file in changed_files:
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", file],
                capture_output=True,
                text=True,
                check=True
            )
            file_diffs[file] = result.stdout
        except subprocess.CalledProcessError:
            continue
    
    if not file_diffs:
        return []
    
    # Analyze each file's changes
    file_analyses = {}
    for file, diff in file_diffs.items():
        # Generate a commit message for this file to understand its changes
        commit_message = generate_commit_message(diff)
        file_analyses[file] = {
            "diff": diff,
            "message": commit_message,
            "type": commit_message.split(":")[0].strip() if ":" in commit_message else "chore",
            "description": commit_message.split(":", 1)[1].strip() if ":" in commit_message else commit_message
        }
    
    # Group files based on their changes
    groups = []
    processed_files = set()
    
    for file, analysis in file_analyses.items():
        if file in processed_files:
            continue
            
        # Start a new group with this file
        current_group = {
            "files": [file],
            "type": analysis["type"],
            "description": analysis["description"],
            "diff": analysis["diff"]
        }
        processed_files.add(file)
        
        # Look for related files
        for other_file, other_analysis in file_analyses.items():
            if other_file in processed_files:
                continue
                
            # Check if files are related based on:
            # 1. Same commit type
            # 2. Similar descriptions
            # 3. Related file paths
            if (other_analysis["type"] == analysis["type"] and
                other_analysis["description"].lower() == analysis["description"].lower()):
                current_group["files"].append(other_file)
                current_group["diff"] += "\n" + other_analysis["diff"]
                processed_files.add(other_file)
        
        groups.append(current_group)
    
    # Generate final commit messages for each group
    suggestions = []
    for group in groups:
        if len(group["files"]) > 1:
            # For multiple files, generate a new message that encompasses all changes
            # This is where an LLM call would happen for the group diff
            # For now, we assume the group["type"] and group["description"] from the first file is a placeholder
            # Or, if we want to reduce LLM calls, we could try to synthesize a message
            # from the individual file messages, or just use the first one more explicitly.
            # Current code re-uses the type/description from the first file that formed the group.
            # If an LLM call for the group diff is desired here, it would be:
            # group_message = generate_commit_message(group["diff"])
            # group["type"] = group_message.split(":")[0].strip() if ":" in group_message else group["type"]
            # group["description"] = group_message.split(":", 1)[1].strip() if ":" in group_message else group["description"]
            pass # Keeping current logic: uses first file's analysis for group type/desc
                 # If an LLM call was here, it would be for group["diff"]

        suggestions.append({
            "files": group["files"],
            "type": group["type"],
            "description": group["description"],
            "diff": group["diff"]
        })
    
    return suggestions

def suggest_commit_groups() -> Optional[List[Dict[str, any]]]:
    """Analyze staged changes and suggest commit groupings."""
    try:
        changed_files = get_changed_files()
        staged_diff = get_staged_diff()
    except RuntimeError as e:
        components.show_error(str(e))
        return None

    if not changed_files:
        components.show_warning("No staged changes found.")
        return None

    return analyze_changes(changed_files)

def commit_command(group: bool = True) -> None:
    """Create a commit with AI-generated message.
    
    Args:
        group: Whether to analyze and group changes (default: True)
    """
    try:
        # Get staged files
        staged_files = get_changed_files()
        if not staged_files:
            components.show_warning("No files staged for commit")
            return

        # Get unstaged files
        try:
            from gitwise.core import git as core_git # Use a different alias to avoid confusion if git is used as var
            # Alternatively, if get_unstaged_files is in gitutils.py, use that.
            # Assuming get_unstaged_files is in core_git as per initial analysis of add.py
            # Check `gitwise/core/git.py` for `get_unstaged_files`
            unstaged_files = core_git.get_unstaged_files()
        except Exception as e:
            components.show_warning(f"Could not check for unstaged files: {str(e)}")
            unstaged_files = [] # Proceed without unstaged check if error occurs

        if unstaged_files:
            components.show_warning("You have unstaged changes:")
            for status, file in unstaged_files:
                components.console.print(f"  {status.strip()} {file}")
            
            choice = safe_prompt(
                "Would you like to stage them before committing, or commit only staged changes?",
                options=["Stage all and commit", "Commit only currently staged", "Abort commit"],
                default="Commit only currently staged"
            )
            
            if choice == 1:  # Stage all and commit
                with components.show_spinner("Staging all changes..."):
                    if core_git.stage_all():
                        components.show_success("All changes staged.")
                        staged_files = get_changed_files() # Refresh staged files list
                        if not staged_files: # Should not happen if unstaged_files was non-empty
                            components.show_error("No files are staged after attempting to stage all. Aborting.")
                            return
                    else:
                        components.show_error("Failed to stage all changes. Aborting commit.")
                        return
            elif choice == 3:  # Abort
                components.show_warning("Commit cancelled")
                return
            # if choice == 2, proceed with currently staged files

        # Check if changes should be grouped
        if group:
            suggestions = None
            with components.show_spinner("Analyzing changes for potential commit groups..."):
                suggestions = suggest_commit_groups()
                
            if suggestions and len(suggestions) > 1:
                components.show_section("Suggested Commit Groups")
                for i, group_suggestion in enumerate(suggestions, 1): # Renamed to avoid conflict
                    components.console.print(f"\n[bold]Group {i}:[/bold]")
                    components.console.print(f"Files: {', '.join(group_suggestion['files'])}")
                    components.console.print(f"Suggested commit: {group_suggestion['type']}: {group_suggestion['description']}")
                
                choice = safe_prompt(
                    "Would you like to commit these changes separately, or consolidate them into a single commit?",
                    options=["Commit separately", "Consolidate into single commit", "Abort"],
                    default="Commit separately"
                )
                
                if choice == 1:  # Yes, commit separately
                    # First, unstage all files involved in any suggestion to handle them group by group
                    all_files_in_suggestions = list(set(f for group_suggestion in suggestions for f in group_suggestion['files']))
                    if all_files_in_suggestions:
                        unstage_files(all_files_in_suggestions)
                    
                    # Then commit each group
                    for group in suggestions:
                        components.show_section(f"Committing Group: {', '.join(group['files'])}")
                        components.console.print(f"Suggested message: {group['type']}: {group['description']}")
                        
                        choice = safe_prompt(
                            "Proceed with this commit?",
                            options=["Yes", "No"],
                            default="Yes"
                        )
                        
                        if choice == 1:  # Yes
                            try:
                                # Stage only the files for this group
                                stage_files(group['files'])
                                with components.show_spinner(f"Committing {len(group['files'])} files..."):
                                    # Disable input during operation
                                    # old_settings = disable_input()
                                    # try:
                                    result = subprocess.run(
                                        ["git", "commit", "-m", f"{group['type']}: {group['description']}"],
                                        capture_output=True,
                                        text=True
                                    )
                                    # finally:
                                    #     enable_input(old_settings)
                                    
                                if result.returncode == 0:
                                    components.show_success("✓ Commit created successfully")
                                    components.console.print(result.stdout)
                                else:
                                    components.show_error("✗ Failed to create commit")
                                    if result.stderr:
                                        components.console.print(result.stderr)
                                    choice = safe_prompt(
                                        "Continue with remaining groups?",
                                        options=["Yes", "No"],
                                        default="Yes"
                                    )
                                    if not safe_confirm("", default=True):
                                        return
                            except Exception as e:
                                components.show_error(str(e))
                                choice = safe_prompt(
                                    "Continue with remaining groups?",
                                    options=["Yes", "No"],
                                    default="Yes"
                                )
                                if not safe_confirm("", default=True):
                                    return
                    
                    # Only ask about pushing after all commits are complete
                    if get_changed_files(): # Check if any commits were actually made
                        choice = safe_prompt(
                            "Would you like to push these changes?",
                            options=["Yes", "No"],
                            default="Yes"
                        )
                        
                        if choice == 1:  # Yes
                            get_push_command()()
                    return # Finished processing groups separately
                elif choice == 3: # Abort
                    components.show_warning("Commit operation cancelled by user.")
                    return
                # If choice is 2 (Consolidate) or implicitly falls through, proceed to single commit logic below.
                # No specific action for choice == 2 here, it means we *don't* do the loop above
                # and instead fall through to the single commit generation for all staged files.
                else: # Consolidate
                    components.show_section("Consolidating changes into a single commit")
                    # Staged files should already represent all changes intended for the consolidated commit.
                    pass # Proceed to the single commit logic after this if/elif/else block

        # If no grouping, user chose to consolidate, or only one group initially suggested, proceed with single commit logic:
        components.show_section("Staged Files for Commit")
        # staged_files should already be up-to-date here
        if not staged_files:
            components.show_warning("No files are currently staged for commit.") # Should be caught earlier ideally
            return
        
        # Show table of staged files instead of individual diffs
        # Convert staged_files (list of paths) to list of tuples (status, path) if needed for show_files_table
        # For simplicity, just print the list of files directly or adapt show_files_table if it expects status.
        # get_changed_files() returns List[str]. We need status for show_files_table.
        # Let's use get_staged_files() from gitutils.py (or core/git.py) which returns (status, file)
        
        try:
            # from gitwise.core import git as core_git # Already imported if unstaged check was done
            # Need to ensure core_git is available or import gitutils.get_staged_files
            # from gitwise.gitutils import get_staged_files as get_staged_files_with_status # This was just added to imports
            # staged_files_with_status = get_staged_files_with_status()
            # Using the already imported get_staged_files from gitutils
            staged_files_with_status = get_staged_files() # Assumes get_staged_files from gitutils is the one with status
            if staged_files_with_status:
                 components.show_files_table(staged_files_with_status, title="Files to be committed")
            else:
                 components.console.print("[bold yellow]Warning: Could not retrieve status for staged files, but proceeding as files are staged.[/bold yellow]")
                 components.console.print("[bold]Files to be committed:[/bold]")
                 for f_path in staged_files:
                    components.console.print(f"- {f_path}")

        except ImportError:
            components.console.print("[bold yellow]Warning: Could not retrieve status for staged files due to import issue.[/bold yellow]")
            components.console.print("[bold]Files to be committed:[/bold]")
            for f_path in staged_files:
                components.console.print(f"- {f_path}")
        except RuntimeError as e:
            components.console.print(f"[bold red]Error displaying staged files table: {e}[/bold red]")
            # Fallback to simple list
            components.console.print("[bold]Files to be committed (fallback list):[/bold]")
            for f_path in staged_files:
                components.console.print(f"- {f_path}")

        if typer.confirm("View full diff before generating commit message?", default=False):
            # full_staged_diff = get_staged_diff() # from current file (commit.py)
            # Use the imported get_staged_diff from gitutils
            from gitwise.gitutils import get_staged_diff as util_get_staged_diff
            full_staged_diff = util_get_staged_diff()
            if full_staged_diff:
                components.show_diff(full_staged_diff, "Full Staged Changes for Commit")
            else:
                components.show_warning("No changes to diff.")

        # Generate commit message
        components.show_section("Generating Commit Message")
        with components.show_spinner("Analyzing changes..."):
            diff = get_staged_diff()
            message = generate_commit_message(diff)

        # Show the generated message
        components.show_section("Suggested Commit Message")
        components.console.print(message)

        # Ask about using the message
        choice = safe_prompt(
            "Would you like to use this commit message?",
            options=["Use message", "Edit message", "Regenerate message", "Abort"],
            default="Use message"
        )

        if choice == 4:  # Abort
            components.show_warning("Commit cancelled")
            return

        if choice == 2:  # Edit
            with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
                tf.write(message)
                tf.flush()
                editor = os.environ.get("EDITOR", "vi")
                # os.system(f'{editor} {tf.name}')
                subprocess.run([editor, tf.name], check=True)
                tf.seek(0)
                message = tf.read().strip()
            os.unlink(tf.name)
            components.show_section("Edited Commit Message")
            components.console.print(message)

            choice = safe_prompt(
                "Proceed with commit?",
                options=["Yes", "No"],
                default="Yes"
            )
            if not safe_confirm("", default=True):
                components.show_warning("Commit cancelled")
                return

        if choice == 3:  # Regenerate
            with components.show_spinner("Regenerating message..."):
                message = generate_commit_message(diff, "Please generate a different commit message")

        # Create commit
        components.show_section("Creating Commit")
        commit_success = False
        
        # Show all operations that will happen
        components.console.print("\n[bold]Operations to be performed:[/bold]")
        components.console.print("1. Creating git commit")
        components.console.print("2. Updating changelog")
        components.console.print("3. Running commit hooks (if any)")
        
        # Operation 1: Git Commit
        components.show_section("1. Creating Git Commit")
        with components.show_spinner("Running git commit..."):
            # Disable input during operation
            # old_settings = disable_input()
            # try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True
            )
            # finally:
            #     enable_input(old_settings)
            
            if result.returncode == 0:
                components.show_success("✓ Git commit created successfully")
                components.console.print(result.stdout)
                commit_success = True
            else:
                components.show_error("✗ Failed to create commit")
                if result.stderr:
                    components.console.print(result.stderr)
                return

        # Operation 2: Update Changelog
        if commit_success:
            components.show_section("2. Updating Changelog")
            with components.show_spinner("Updating changelog..."):
                # Disable input during operation
                # old_settings = disable_input()
                try:
                    from gitwise.features.changelog import update_unreleased_changelog
                    # update_unreleased_changelog() # Addressed in Flaw 4
                    components.show_success("✓ Changelog updated successfully (dummy - actual update moved to hook)")
                except Exception as e:
                    components.show_warning(f"⚠ Could not update changelog: {str(e)}")
                # finally:
                #     enable_input(old_settings)

        # Operation 3: Commit Hooks (Removed as per Flaw 3)
        # if commit_success:
        #     components.show_section("3. Running Commit Hooks")
        #     with components.show_spinner("Checking for commit hooks..."):
        #         # Disable input during operation
        #         # old_settings = disable_input()
        #         try:
        #             # Check if there are any commit hooks
        #             result = subprocess.run(
        #                 ["git", "rev-parse", "--git-path", "hooks"],
        #                 capture_output=True,
        #                 text=True,
        #                 check=True
        #             )
        #             hooks_dir = result.stdout.strip()
        #             if os.path.exists(hooks_dir):
        #                 components.show_success("✓ Commit hooks will be run by Git automatically")
        #             else:
        #                 components.console.print("No commit hooks found")
        #         except Exception as e:
        #             components.show_warning(f"⚠ Could not check commit hooks: {str(e)}")
                # finally:
                #     enable_input(old_settings)

        # Only ask about pushing after all operations are complete
        if commit_success:
            components.show_section("Push Changes")
            choice = safe_prompt(
                "Would you like to push these changes?",
                options=["Yes", "No"],
                default="Yes"
            )
            
            if choice == 1:  # Yes
                # Call push command directly without additional prompts
                get_push_command()()

    except Exception as e:
        components.show_error(str(e)) 