"""Command-line interface for GitWise."""

import typer
import sys
import os
import subprocess
from typing import List
from gitwise.ui import components
from gitwise.cli.add import add_command
from gitwise.features.commit import commit_command
from gitwise.features.push import push_command
from gitwise.features.pr import pr_command
from gitwise.features.changelog import changelog_command

# Define command categories with emojis
# COMMIT_COMMANDS = {
#     "commit": "Create a commit with AI-generated message",
#     "push": "Push changes and optionally create a PR",
#     "pr": "Create a pull request with AI-generated description",
#     "changelog": "Generate a changelog from commits"
# }

# Create the main app
app = typer.Typer(
    name="gitwise",
    help="""
    🚀 GitWise - AI-powered Git workflow assistant
    
    Features:
    • Smart commit messages
    • Intelligent PR descriptions
    • Automatic changelog generation
    • Interactive staging and committing
    
    Use 'gitwise <command> --help' for more information about a command.
    """,
    add_completion=False
)

# Add commands
@app.command()
def add(
    files: List[str] = typer.Argument(None, help="Files to stage (default: all changes)")
) -> None:
    """Stage files with interactive selection."""
    add_command(files)

@app.command(name="commit", help="Create a commit with AI-generated message")
def commit(
    group: bool = typer.Option(
        False,
        "--group",
        "-g",
        help="Enable automatic grouping of related changes into separate commits (can be slower)."
    )
) -> None:
    """Create a commit with AI-generated message."""
    commit_command(group=group)

@app.command()
def push() -> None:
    """Push changes and optionally create a PR."""
    push_command()

@app.command()
def pr(
    use_labels: bool = typer.Option(False, "--labels", "-l", help="Add labels to the PR"),
    use_checklist: bool = typer.Option(False, "--checklist", "-c", help="Add checklist to the PR description"),
    skip_general_checklist: bool = typer.Option(False, "--skip-checklist", help="Skip general checklist items"),
    title: str = typer.Option(None, "--title", "-t", help="Custom title for the PR"),
    base: str = typer.Option(None, "--base", "-b", help="Base branch for the PR"),
    draft: bool = typer.Option(False, "--draft", "-d", help="Create a draft PR")
) -> None:
    """Create a pull request with AI-generated description."""
    pr_command(use_labels, use_checklist, skip_general_checklist, title, base, draft)

@app.command()
def changelog(
    version: str = typer.Option(None, "--version", help="Version string for the changelog"),
    output_file: str = typer.Option(None, "--output-file", help="Output file path"),
    format: str = typer.Option("markdown", "--format", help="Output format (markdown or json)"),
    auto_update: bool = typer.Option(False, "--auto-update", help="Automatically update the changelog without prompts")
) -> None:
    """Generate a changelog from commits since the last tag."""
    changelog_command(version, output_file, format, auto_update)

@app.command()
def git(
    args: List[str] = typer.Argument(None, help="Git command and arguments")
) -> None:
    """Pass through to git with enhanced output and pager handling for common commands."""
    if not args:
        components.show_error("No git command provided")
        raise typer.Exit(code=1)

    command_to_run = ["git"] + args
    
    # Simplified pager handling:
    # The responsibility of piping commands that use a pager (like log, diff)
    # is left to the user or handled by gh's pager if run via `gh alias`.
    # GitWise will stream the output directly.
    # pager_commands = {"log", "diff", "show", "branch"} 
    # is_pager_command = args[0] in pager_commands
    # is_piped_by_user = any("|" in arg for arg in args)
    # if is_pager_command and not is_piped_by_user:
    #     pass # No auto-piping

    try:
        # Use Popen for better control over the process
        process = subprocess.Popen(
            command_to_run,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                components.console.print(output.strip())
        
        # Get the return code
        return_code = process.poll()
        
        if return_code == 0:
            components.show_success("Git command executed successfully")
        else:
            components.show_error("Git command failed")
            # Print any remaining stderr
            stderr = process.stderr.read()
            if stderr:
                components.console.print(stderr)
            raise typer.Exit(code=return_code)
            
    except Exception as e:
        components.show_error(str(e))
        raise typer.Exit(code=1)

def main() -> None:
    """Main entry point for the application."""
    try:
        app()
    except Exception as e:
        components.show_error(str(e))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    main() 