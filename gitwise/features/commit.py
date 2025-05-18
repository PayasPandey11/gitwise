import typer
import tempfile
import os
import subprocess
from typing import Optional, List, Dict, Tuple
from gitwise.llm import generate_commit_message
from gitwise.gitutils import get_staged_diff, run_git_commit, get_changed_files
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
    
    commit_type = typer.prompt(
        "\nEnter commit type",
        type=str,
        default="feat" if "feat" in changed_files else "fix"
    ).lower()
    
    # Step 2: Enter scope
    suggested_scope = suggest_scope(changed_files)
    scope = typer.prompt(
        "Enter scope (optional)",
        type=str,
        default=suggested_scope
    )
    
    # Step 3: Enter description
    description = typer.prompt(
        "Enter commit description",
        type=str
    )
    
    # Step 4: Enter body (optional)
    body = typer.prompt(
        "Enter commit body (optional, press Enter to skip)",
        type=str,
        default=""
    )
    
    # Step 5: Enter breaking changes (optional)
    breaking = typer.confirm("Are there any breaking changes?", default=False)
    breaking_changes = ""
    if breaking:
        breaking_changes = typer.prompt(
            "Describe the breaking changes",
            type=str
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

def analyze_changes(changed_files: List[str], staged_diff: str) -> List[Dict[str, any]]:
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
            group_message = generate_commit_message(group["diff"])
            group["type"] = group_message.split(":")[0].strip() if ":" in group_message else group["type"]
            group["description"] = group_message.split(":", 1)[1].strip() if ":" in group_message else group["description"]
        
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

    return analyze_changes(changed_files, staged_diff)

def get_staged_diff(file: Optional[str] = None) -> str:
    """Get the diff of staged changes.
    
    Args:
        file: Optional specific file to get diff for
        
    Returns:
        The diff as a string
    """
    try:
        cmd = ["git", "diff", "--cached"]
        if file:
            cmd.append(file)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error getting staged diff: {e.stderr}")

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
        unstaged_files = []
        if unstaged_files:
            components.show_warning("You have unstaged changes")
            components.show_prompt(
                "Would you like to commit changes separately?",
                options=["Yes", "Stage all", "No"],
                default="Yes"
            )
            choice = typer.prompt("", type=int, default=1)
            
            if choice == 2:  # Stage all
                stage_files(staged_files)
                staged_files = get_changed_files()
            elif choice == 3:  # No
                components.show_warning("Commit cancelled")
                return

        # Check if changes should be grouped
        if group:
            suggestions = suggest_commit_groups()
            if suggestions and len(suggestions) > 1:
                components.show_section("Suggested Commit Groups")
                for i, group in enumerate(suggestions, 1):
                    components.console.print(f"\n[bold]Group {i}:[/bold]")
                    components.console.print(f"Files: {', '.join(group['files'])}")
                    components.console.print(f"Suggested commit: {group['type']}: {group['description']}")
                
                components.show_prompt(
                    "Would you like to commit these changes separately?",
                    options=["Yes", "No"],
                    default="Yes"
                )
                choice = typer.prompt("", type=int, default=1)
                
                if choice == 1:  # Yes
                    # First, unstage all files
                    all_files = [f for group in suggestions for f in group['files']]
                    unstage_files(all_files)
                    
                    # Then commit each group
                    for group in suggestions:
                        components.show_section(f"Committing Group: {', '.join(group['files'])}")
                        components.console.print(f"Suggested message: {group['type']}: {group['description']}")
                        
                        components.show_prompt(
                            "Proceed with this commit?",
                            options=["Yes", "No"],
                            default="Yes"
                        )
                        choice = typer.prompt("", type=int, default=1)
                        
                        if choice == 1:  # Yes
                            try:
                                # Stage only the files for this group
                                stage_files(group['files'])
                                with components.show_spinner(f"Committing {len(group['files'])} files..."):
                                    result = subprocess.run(
                                        ["git", "commit", "-m", f"{group['type']}: {group['description']}"],
                                        capture_output=True,
                                        text=True
                                    )
                                    if result.returncode == 0:
                                        components.show_success("Commit created successfully")
                                        components.console.print(result.stdout)
                                    else:
                                        components.show_error("Failed to create commit")
                                        if result.stderr:
                                            components.console.print(result.stderr)
                                        components.show_prompt(
                                            "Continue with remaining groups?",
                                            options=["Yes", "No"],
                                            default="Yes"
                                        )
                                        if not typer.confirm("", default=True):
                                            return
                            except Exception as e:
                                components.show_error(str(e))
                                components.show_prompt(
                                    "Continue with remaining groups?",
                                    options=["Yes", "No"],
                                    default="Yes"
                                )
                                if not typer.confirm("", default=True):
                                    return
                    
                    # Only ask about pushing after all commits are complete
                    components.show_prompt(
                        "Would you like to push these changes?",
                        options=["Yes", "No"],
                        default="Yes"
                    )
                    choice = typer.prompt("", type=int, default=1)
                    
                    if choice == 1:  # Yes
                        # Call push command directly without additional prompts
                        get_push_command()()
                    return

        # If no grouping or user chose not to group, proceed with single commit
        # Show staged changes
        components.show_section("Staged Changes")
        for file in staged_files:
            diff = get_staged_diff(file)
            components.console.print(f"\n[bold cyan]{file}[/bold cyan]")
            components.console.print(diff)

        # Generate commit message
        components.show_section("Generating Commit Message")
        with components.show_spinner("Analyzing changes..."):
            diff = get_staged_diff()
            message = generate_commit_message(diff)

        # Show the generated message
        components.show_section("Suggested Commit Message")
        components.console.print(message)

        # Ask about using the message
        components.show_prompt(
            "Would you like to use this commit message?",
            options=["Use message", "Edit message", "Regenerate message", "Abort"],
            default="Use message"
        )
        choice = typer.prompt("", type=int, default=1)

        if choice == 4:  # Abort
            components.show_warning("Commit cancelled")
            return

        if choice == 2:  # Edit
            with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
                tf.write(message)
                tf.flush()
                editor = os.environ.get("EDITOR", "vi")
                os.system(f'{editor} {tf.name}')
                tf.seek(0)
                message = tf.read().strip()
            os.unlink(tf.name)
            components.show_section("Edited Commit Message")
            components.console.print(message)

            components.show_prompt(
                "Proceed with commit?",
                options=["Yes", "No"],
                default="Yes"
            )
            if not typer.confirm("", default=True):
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
        
        with components.show_spinner("Creating git commit..."):
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                components.show_success("Git commit created successfully")
                components.console.print(result.stdout)
                commit_success = True
            else:
                components.show_error("Failed to create commit")
                if result.stderr:
                    components.console.print(result.stderr)
                return

        # Update changelog after successful commit
        if commit_success:
            with components.show_spinner("Updating changelog..."):
                try:
                    from gitwise.features.changelog import update_unreleased_changelog
                    update_unreleased_changelog()
                    components.show_success("Changelog updated successfully")
                except Exception as e:
                    components.show_warning(f"Could not update changelog: {str(e)}")

        # Only ask about pushing after all operations are complete
        if commit_success:
            components.show_prompt(
                "Would you like to push these changes?",
                options=["Yes", "No"],
                default="Yes"
            )
            choice = typer.prompt("", type=int, default=1)
            
            if choice == 1:  # Yes
                # Call push command directly without additional prompts
                get_push_command()()

    except Exception as e:
        components.show_error(str(e)) 