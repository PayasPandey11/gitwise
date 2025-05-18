import typer
import tempfile
import os
import subprocess
from typing import Optional, List, Dict, Tuple
from gitwise.llm import generate_commit_message
from gitwise.gitutils import get_staged_diff, run_git_commit, get_changed_files

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
        typer.echo(str(e))
        return None

    if not changed_files:
        typer.echo("No staged changes found.")
        return None

    return analyze_changes(changed_files, staged_diff)

def commit_command(group: bool = False) -> None:
    """Main logic for the commit command: gets staged diff, generates commit message, allows editing, and commits."""
    try:
        staged_diff = get_staged_diff()
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)

    if not staged_diff:
        typer.echo("No staged changes found. Please stage your changes first.")
        raise typer.Exit(code=0)

    # Check if changes should be grouped
    if group:
        suggestions = suggest_commit_groups()
        if suggestions and len(suggestions) > 1:
            typer.echo("\nI notice your changes might be better organized into multiple commits:")
            for i, group in enumerate(suggestions, 1):
                typer.echo(f"\nGroup {i}:")
                typer.echo(f"Files: {', '.join(group['files'])}")
                typer.echo(f"Suggested commit: {group['type']}: {group['description']}")
            
            if typer.confirm("\nWould you like to commit these changes separately?", default=True):
                # First, unstage all files
                all_files = [f for group in suggestions for f in group['files']]
                unstage_files(all_files)
                
                # Then commit each group
                for group in suggestions:
                    typer.echo(f"\nCommitting group: {', '.join(group['files'])}")
                    typer.echo(f"Suggested message: {group['type']}: {group['description']}")
                    
                    if typer.confirm("Proceed with this commit?", default=True):
                        try:
                            # Stage only the files for this group
                            stage_files(group['files'])
                            run_git_commit(f"{group['type']}: {group['description']}")
                            typer.echo("Commit created successfully.")
                        except RuntimeError as e:
                            typer.echo(str(e))
                            if not typer.confirm("Continue with remaining groups?", default=True):
                                raise typer.Exit(code=1)
                
                # Ask about pushing after all commits
                if typer.confirm("\nWould you like to push these changes?", default=False):
                    # push_command()
                    return

    # If no grouping or user chose not to group, proceed with single commit
    typer.echo("Analyzing staged changes:\n")
    typer.echo(staged_diff[:1000] + ("\n... (truncated) ..." if len(staged_diff) > 1000 else ""))
    
    while True:
        commit_message = generate_commit_message(staged_diff)
        typer.echo(f"\nSuggested commit message:\n{commit_message}\n")

        action = typer.prompt(
            "What would you like to do?",
            type=str,
            default="u",
            show_choices=True,
            show_default=True,
            prompt_suffix="\n[u]se/[e]dit/[r]egenerate/[a]bort "
        ).lower()

        if action not in ["u", "e", "r", "a"]:
            typer.echo("Invalid option. Please choose from: u, e, r, a")
            continue

        if action == "a":
            typer.echo("Aborted. No commit made.")
            return

        if action == "r":
            guidance = typer.prompt(
                "Enter guidance for the commit message (optional)",
                default="",
                show_default=False
            )
            if guidance:
                typer.echo("Regenerating commit message with guidance...")
                commit_message = generate_commit_message(staged_diff, guidance)
            else:
                typer.echo("Regenerating commit message...")
                commit_message = generate_commit_message(staged_diff)
            continue

        if action == "e":
            with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
                tf.write(commit_message)
                tf.flush()
                editor = os.environ.get("EDITOR", "vi")
                os.system(f'{editor} {tf.name}')
                tf.seek(0)
                commit_message = tf.read().strip()
            os.unlink(tf.name)
            typer.echo(f"\nEdited commit message:\n{commit_message}\n")
            action = typer.prompt(
                "What would you like to do?",
                type=str,
                default="u",
                show_choices=True,
                show_default=True,
                prompt_suffix="\n[u]se/[r]egenerate/[a]bort "
            ).lower()
            if action not in ["u", "r", "a"]:
                typer.echo("Invalid option. Please choose from: u, r, a")
                continue
            if action == "a":
                typer.echo("Aborted. No commit made.")
                return
            if action == "r":
                guidance = typer.prompt(
                    "Enter guidance for the commit message (optional)",
                    default="",
                    show_default=False
                )
                if guidance:
                    typer.echo("Regenerating commit message with guidance...")
                    commit_message = generate_commit_message(staged_diff, guidance)
                else:
                    typer.echo("Regenerating commit message...")
                    commit_message = generate_commit_message(staged_diff)
                continue

        # If we get here, action is "u"
        break

    try:
        run_git_commit(commit_message)
        typer.echo("Commit created successfully.")
        
        # Ask about pushing
        # push = typer.confirm("Would you like to push these changes?", default=False)
        # if push:
        #     push_command()
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1) 