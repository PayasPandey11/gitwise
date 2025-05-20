import typer
import tempfile
import os
import subprocess
import sys
from typing import Optional, List, Dict, Tuple
from gitwise.llm import get_llm_response
from gitwise.prompts import COMMIT_MESSAGE_PROMPT
from gitwise.gitutils import get_staged_diff, get_changed_files, get_staged_files # get_unstaged_files is also in gitutils
from gitwise.ui import components
from gitwise.llm.offline import ensure_offline_model_ready

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


def safe_prompt(prompt_text: str, options: List[str], default: str = "Yes") -> int:
    """Prompt for user input using Typer with predefined options."""
    components.show_prompt(prompt_text, options=options, default=default)
    choice = typer.prompt("", type=int, default=1)
    return choice

def safe_confirm(prompt_text: str, default: bool = True) -> bool:
    """Prompt for confirmation using Typer."""
    return typer.confirm(prompt_text, default=default)

def safe_prompt_text(prompt_text: str, default: str = "") -> str:
    """Prompt for text input using Typer."""
    return typer.prompt(prompt_text, default=default)

def suggest_scope(changed_files: List[str]) -> str:
    """Suggest a scope based on the most common directory among changed files."""
    dirs = {}
    for file in changed_files:
        dir_name = os.path.dirname(file)
        if dir_name:
            dirs[dir_name] = dirs.get(dir_name, 0) + 1
    
    if dirs:
        return max(dirs, key=dirs.get) # Simplified to use key=dirs.get
    return ""

def build_commit_message_interactive() -> str:
    """Interactively build a conventional commit message."""
    changed_files = get_changed_files() # from gitutils
    
    typer.echo("\nSelect commit type:")
    for type_key, desc in COMMIT_TYPES.items(): # Renamed type_ to type_key for clarity
        typer.echo(f"  {type_key:<10} - {desc}")
    
    commit_type = safe_prompt_text(
        "\nEnter commit type",
        default="feat" # Simplified default, user can override
    ).lower()
    
    suggested_scope = suggest_scope(changed_files)
    scope = safe_prompt_text(
        "Enter scope (optional)",
        default=suggested_scope
    )
    
    description = safe_prompt_text(
        "Enter commit description"
    )
    
    body = safe_prompt_text(
        "Enter commit body (optional, press Enter to skip)",
        default=""
    )
    
    breaking_changes = ""
    if safe_confirm("Are there any breaking changes?", default=False):
        breaking_changes = safe_prompt_text(
            "Describe the breaking changes"
        )
    
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
    """Stage specified files using git add."""
    try:
        subprocess.run(["git", "add"] + files, check=True, capture_output=True, text=True) # Added capture_output and text for consistency
    except subprocess.CalledProcessError as e:
        # Provide more context from stderr if available
        error_message = f"Error staging files: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        raise RuntimeError(error_message) from e

def unstage_files(files: List[str]) -> None:
    """Unstage specified files using git reset."""
    try:
        subprocess.run(["git", "reset"] + files, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        error_message = f"Error unstaging files: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        raise RuntimeError(error_message) from e

def analyze_changes(changed_files: List[str]) -> List[Dict[str, any]]:
    """Analyze changes and suggest logical groupings based on file diffs and generated messages."""
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
            # If a single file diff fails, we can skip it or log a warning
            components.show_warning(f"Could not get diff for file: {file}. Skipping for analysis.")
            continue # Skip this file and proceed with others
    
    if not file_diffs:
        return []
    
    file_analyses = {}
    for file, diff_content in file_diffs.items(): # Renamed diff to diff_content for clarity
        commit_message = generate_commit_message(diff_content) # diff_content passed here
        file_analyses[file] = {
            "diff": diff_content,
            "message": commit_message,
            "type": commit_message.split(":")[0].strip() if ":" in commit_message else "chore",
            "description": commit_message.split(":", 1)[1].strip() if ":" in commit_message else commit_message
        }
    
    groups = []
    processed_files = set()
    
    for file, analysis in file_analyses.items():
        if file in processed_files:
            continue
            
        current_group = {
            "files": [file],
            "type": analysis["type"],
            "description": analysis["description"],
            "diff": analysis["diff"]
        }
        processed_files.add(file)
        
        for other_file, other_analysis in file_analyses.items():
            if other_file in processed_files:
                continue
                
            if (other_analysis["type"] == analysis["type"] and
                other_analysis["description"].lower() == analysis["description"].lower()): # Simple similarity check
                current_group["files"].append(other_file)
                current_group["diff"] += "\n" + other_analysis["diff"] # Concatenate diffs for the group
                processed_files.add(other_file)
        
        groups.append(current_group)
    
    suggestions = []
    for group in groups:
        if len(group["files"]) > 1:
            # For multiple files, the current logic uses the first file's analysis 
            # (type/description) for the group. A more advanced approach might involve
            # re-generating a message for the combined group["diff"].
            pass 

        suggestions.append({
            "files": group["files"],
            "type": group["type"],
            "description": group["description"],
            "diff": group["diff"] # This diff is the combined diff for the group
        })
    
    return suggestions

def suggest_commit_groups() -> Optional[List[Dict[str, any]]]:
    """Analyze staged changes and suggest commit groupings."""
    try:
        # get_changed_files gets --cached --name-only, which is what we need for analysis input
        staged_file_paths = get_changed_files() 
    except RuntimeError as e:
        components.show_error(str(e))
        return None

    if not staged_file_paths:
        components.show_warning("No staged changes found to analyze for grouping.")
        return None

    return analyze_changes(staged_file_paths)

def commit_command(group: bool = True) -> None:
    """Create a commit, with an option for AI-assisted message generation and change grouping."""
    try:
        # Pre-check for offline model if not in online mode
        if os.environ.get("GITWISE_ONLINE") != "1":
            try:
                ensure_offline_model_ready()
            except Exception as e:
                components.show_error(f"Failed to load offline model: {e}")
                return

        # Initial check for staged files to commit
        # Using get_changed_files (which is git diff --cached --name-only) for paths
        current_staged_files_paths = get_changed_files()
        if not current_staged_files_paths:
            components.show_warning("No files staged for commit. Please stage files first.")
            return

        try:
            from gitwise.core import git as core_git 
            unstaged_files_status = core_git.get_unstaged_files() # This should return List[Tuple[str, str]]
        except Exception as e: # Catch a broader exception if core_git or method is problematic
            components.show_warning(f"Could not check for unstaged files: {str(e)}")
            unstaged_files_status = [] 

        if unstaged_files_status:
            components.show_warning("You have unstaged changes:")
            for status, file_path in unstaged_files_status:
                components.console.print(f"  {status.strip()} {file_path}")
            
            choice = safe_prompt(
                "Would you like to stage them before committing, or commit only staged changes?",
                options=["Stage all and commit", "Commit only currently staged", "Abort commit"],
                default="Commit only currently staged"
            )
            
            if choice == 1:  # Stage all and commit
                with components.show_spinner("Staging all changes..."):
                    if core_git.stage_all():
                        components.show_success("All changes staged.")
                        current_staged_files_paths = get_changed_files() # Refresh staged files list
                        if not current_staged_files_paths: 
                            components.show_error("No files are staged after attempting to stage all. Aborting.")
                            return
                    else:
                        components.show_error("Failed to stage all changes. Aborting commit.")
                        return
            elif choice == 3:  # Abort
                components.show_warning("Commit cancelled.")
                return
            # If choice == 2, proceed with current_staged_files_paths

        if group:
            suggestions = None
            with components.show_spinner("Analyzing changes for potential commit groups..."):
                # suggest_commit_groups internally uses get_changed_files(), which is correct for staged files.
                suggestions = suggest_commit_groups()
                
            if suggestions and len(suggestions) > 1:
                components.show_section("Suggested Commit Groups")
                for i, group_item in enumerate(suggestions, 1):
                    components.console.print(f"\n[bold]Group {i}:[/bold]")
                    components.console.print(f"Files: {', '.join(group_item['files'])}")
                    components.console.print(f"Suggested commit: {group_item['type']}: {group_item['description']}")
                
                choice = safe_prompt(
                    "Commit these groups separately, or consolidate into a single commit?",
                    options=["Commit separately", "Consolidate into single commit", "Abort"],
                    default="Commit separately"
                )
                
                if choice == 1:  # Commit separately
                    all_files_in_suggestions = list(set(f for group_item in suggestions for f in group_item['files']))
                    if all_files_in_suggestions:
                        # Unstage all involved files first to handle them group by group cleanly
                        unstage_files(all_files_in_suggestions)
                    
                    commits_made_in_grouping = False
                    for group_item in suggestions:
                        components.show_section(f"Preparing Group: {', '.join(group_item['files'])}")
                        
                        # Ask per group if user wants to proceed with this specific group
                        if not safe_confirm(f"Proceed with committing this group ({group_item['type']}: {group_item['description']})?", default=True):
                            components.show_warning(f"Skipping group: {', '.join(group_item['files'])}")
                            continue # Skip to the next group

                        try:
                            stage_files(group_item['files'])
                            commit_message_for_group = f"{group_item['type']}: {group_item['description']}"
                            with components.show_spinner(f"Committing group - {len(group_item['files'])} files..."):
                                result = subprocess.run(
                                    ["git", "commit", "-m", commit_message_for_group],
                                    capture_output=True, text=True, check=False # check=False to handle errors manually
                                )
                                
                            if result.returncode == 0:
                                components.show_success(f"✓ Group commit successful: {commit_message_for_group}")
                                components.console.print(result.stdout.strip())
                                commits_made_in_grouping = True
                            else:
                                components.show_error(f"✗ Failed to create commit for group: {group_item['type']}: {group_item['description']}")
                                if result.stderr:
                                    components.console.print(f"[red]Error:[/red]\n{result.stderr.strip()}")
                                if not safe_confirm("Problem committing group. Continue with remaining groups?", default=True):
                                    return # Abort all further operations
                        except RuntimeError as e: # Catch errors from stage_files or unstage_files
                            components.show_error(str(e))
                            if not safe_confirm("Problem staging files for group. Continue with remaining groups?", default=True):
                                return # Abort all further operations
                    
                    if commits_made_in_grouping and safe_confirm("Push all committed groups now?", default=True):
                        get_push_command()()
                    return # Finished processing groups separately

                elif choice == 3: # Abort
                    components.show_warning("Commit operation cancelled by user.")
                    return
                else: # Consolidate
                    components.show_section("Consolidating changes into a single commit.")
                    # Ensure all files that were part of suggestions (and potentially unstaged) are re-staged
                    # This assumes current_staged_files_paths holds the original set of all files intended for commit.
                    # If files were unstaged above, they need to be staged again for the single commit.
                    # This logic needs to be robust: stage current_staged_files_paths which should be the full list.
                    with components.show_spinner("Re-staging all files for consolidated commit..."):
                        stage_files(current_staged_files_paths) 

        # Single commit logic (either by choice, or if no grouping was applicable/done)
        # current_staged_files_paths should reflect the files to be committed at this point.
        if not current_staged_files_paths:
             components.show_warning("No files are staged for the consolidated commit. Aborting.")
             return

        components.show_section("Files for Single Commit")
        try:
            # get_staged_files() provides status, current_staged_files_paths is just paths
            staged_files_for_table = get_staged_files() 
            if staged_files_for_table:
                 components.show_files_table(staged_files_for_table, title="Files to be committed")
            else: # Fallback if get_staged_files is empty but current_staged_files_paths is not
                 components.console.print("[bold yellow]Warning: Could not retrieve detailed status for staged files. Displaying paths:[/bold yellow]")
                 for f_path in current_staged_files_paths:
                    components.console.print(f"- {f_path}")
        except RuntimeError as e:
            components.console.print(f"[bold red]Error displaying staged files table: {e}. Displaying paths:[/bold red]")
            for f_path in current_staged_files_paths:
                components.console.print(f"- {f_path}")

        if typer.confirm("View full diff before generating commit message?", default=False):
            # Use get_staged_diff from gitutils for the full diff of currently staged changes
            full_staged_diff_content = get_staged_diff()
            if full_staged_diff_content:
                components.show_diff(full_staged_diff_content, "Full Staged Changes for Commit")
            else:
                components.show_warning("No staged changes to diff.")

        components.show_section("Generating Commit Message")
        # Pass the diff of currently staged files to generate_commit_message
        diff_for_message_generation = get_staged_diff()
        if not diff_for_message_generation and current_staged_files_paths: # If diff is empty but files are staged (e.g. new empty files)
             components.show_warning("Staged files have no diff content (e.g. new empty files). LLM might produce a generic message.")
             # Provide file list as context if diff is empty
             diff_for_message_generation = f"The following files are staged (no content changes detected):\n" + "\n".join(current_staged_files_paths)
        elif not diff_for_message_generation and not current_staged_files_paths:
            components.show_error("No staged changes or files to generate commit message from. Aborting.")
            return

        message = ""
        with components.show_spinner("Analyzing changes..."):
            message = generate_commit_message(diff_for_message_generation)

        components.show_section("Suggested Commit Message")
        components.console.print(message)

        user_choice_for_message = safe_prompt(
            "Use this commit message?",
            options=["Use message", "Edit message", "Regenerate message", "Abort"],
            default="Use message"
        )

        if user_choice_for_message == 4:  # Abort
            components.show_warning("Commit cancelled.")
            return

        if user_choice_for_message == 2:  # Edit
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w+", encoding="utf-8") as tf:
                tf.write(message)
                tf.flush()
            editor = os.environ.get("EDITOR", "vi") # Default to vi if EDITOR is not set
            try:
                subprocess.run([editor, tf.name], check=True)
                with open(tf.name, "r", encoding="utf-8") as f_read:
                    message = f_read.read().strip()
            except FileNotFoundError:
                 components.show_error(f"Editor '{editor}' not found. Please set your EDITOR environment variable or install {editor}.")
                 message = safe_prompt_text("Please manually enter the commit message:", default=message)
            except subprocess.CalledProcessError:
                 components.show_warning("Editor closed without successful save. Using previous message or enter new one.")
                 message = safe_prompt_text("Please manually enter/confirm the commit message:", default=message)
            finally:
                os.unlink(tf.name)
            
            if not message.strip():
                components.show_error("Commit message cannot be empty after editing. Aborting.")
                return

            components.show_section("Edited Commit Message")
            components.console.print(message)
            if not safe_confirm("Proceed with this edited commit message?", default=True):
                components.show_warning("Commit cancelled.")
                return

        if user_choice_for_message == 3:  # Regenerate
            with components.show_spinner("Regenerating message..."):
                message = generate_commit_message(diff_for_message_generation, "Please try a different style or focus for the commit message.")
            components.show_section("Newly Suggested Commit Message")
            components.console.print(message)
            if not safe_confirm("Use this new message?", default=True):
                 # Allow one more edit if regeneration is not satisfactory
                 with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w+", encoding="utf-8") as tf:
                    tf.write(message)
                    tf.flush()
                 editor = os.environ.get("EDITOR", "vi")
                 try:
                    subprocess.run([editor, tf.name], check=True)
                    with open(tf.name, "r", encoding="utf-8") as f_read:
                        message = f_read.read().strip()
                 except Exception:
                     components.show_warning("Failed to edit regenerated message. Using as is or aborting.")
                 finally:
                     os.unlink(tf.name)
                 if not message.strip() or not safe_confirm(f"Use this (potentially edited) message: \n{message}", default=True):
                    components.show_warning("Commit cancelled.")
                    return

        components.show_section("Creating Final Commit")
        commit_success = False
        with components.show_spinner("Running git commit..."):
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True, text=True, check=False # check=False to handle manually
            )
            
            if result.returncode == 0:
                components.show_success("✓ Git commit created successfully")
                components.console.print(result.stdout.strip())
                commit_success = True
            else:
                components.show_error("✗ Failed to create commit")
                if result.stderr:
                    components.console.print(f"[red]Error:[/red]\n{result.stderr.strip()}")
                return # Abort if commit fails

        if commit_success:
            if safe_confirm("Push this commit now?", default=True):
                get_push_command()()

    except RuntimeError as e: # Catch RuntimeErrors from git utils or staging/unstaging
        components.show_error(f"A critical Git operation failed: {str(e)}")
    except Exception as e:
        components.show_error(f"An unexpected error occurred: {str(e)}") 

def generate_commit_message(diff: str, guidance: str = "") -> str:
    prompt = COMMIT_MESSAGE_PROMPT.format(diff=diff, guidance=guidance)
    return get_llm_response(prompt) 