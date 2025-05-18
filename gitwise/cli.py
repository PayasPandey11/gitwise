"""Command-line interface for GitWise."""

import typer
import sys
import os
import subprocess
from typing import Optional, List

# Support running from both the package and directly as a script
if __name__ == "__main__" and ("gitwise" not in sys.modules and not os.path.exists(os.path.join(os.path.dirname(__file__), "__init__.py"))):
    # Running as a script from gitwise/ directory
    from features.commit import commit_command
    from features.push import push_command
    from features.pr import pr_command
    from features.changelog import changelog_command
else:
    # Running as a module from parent directory
    from gitwise.features.commit import commit_command
    from gitwise.features.push import push_command
    from gitwise.features.pr import pr_command
    from gitwise.features.changelog import changelog_command

# Define command categories
GITWISE_COMMANDS = {
    "commit": "Generate a smart commit message for staged changes",
    "push": "Push changes with option to create PR",
    "pr": "Create a pull request with AI-generated description"
}

GIT_PASSTHROUGH_COMMANDS = {
    "add": "Stage changes (git add passthrough)",
    "git": "Pass through any git command"
}

app = typer.Typer(
    help="""gitwise: AI-powered git assistant

    Smart Features:
    - Generate conventional commit messages using AI
    - Create PRs with AI-generated descriptions
    - Push changes with PR creation option

    Usage:
    - Use gitwise-specific commands for enhanced features
    - Use any git command directly (e.g., gitwise checkout, gitwise status)
    - All git commands are supported through passthrough
    """,
    add_completion=False
)

@app.command()
def add(
    files: str = typer.Argument(..., help="Files to stage"),
    group: bool = typer.Option(True, "--group/--no-group", help="Group related changes into logical commits")
) -> None:
    """Stage files and create a commit with a smart message."""
    # Stage files
    result = subprocess.run(["git", "add", files], capture_output=True, text=True)
    if result.returncode != 0:
        typer.echo(f"Error staging {files}: {result.stderr}")
        raise typer.Exit(code=1)
    
    # Create commit with smart message
    commit_command(group=group)

@app.command()
def commit(
    message: Optional[str] = typer.Argument(None, help="Commit message"),
    group: bool = typer.Option(True, "--group/--no-group", help="Group related changes into logical commits")
) -> None:
    """Create a commit with a smart message."""
    commit_command(message=message, group=group)

@app.command()
def push() -> None:
    """Push changes to the remote repository."""
    # TODO: Implement push command
    pass

@app.command()
def pr(
    use_labels: bool = typer.Option(False, "--use-labels/--no-labels", help="Add labels based on commit types"),
    use_checklist: bool = typer.Option(False, "--use-checklist/--no-checklist", help="Add checklist based on changed files"),
    skip_general_checklist: bool = typer.Option(False, "--skip-general-checklist/--no-skip-general-checklist", help="Skip general checklist items")
) -> None:
    """Create a pull request with a smart description."""
    pr_command(use_labels, use_checklist, skip_general_checklist)

@app.command()
def changelog(
    version: Optional[str] = typer.Argument(None, help="Version to generate changelog for"),
    create_tag: bool = typer.Option(False, "--create-tag", help="Create a new version tag if none exists"),
    auto_update: bool = typer.Option(False, "--auto-update", help="Update the unreleased section of the changelog"),
    setup_hook: bool = typer.Option(False, "--setup-hook", help="Set up git commit hook for automatic changelog updates")
) -> None:
    """Generate a changelog for the repository."""
    changelog_command(version, create_tag, auto_update, setup_hook)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, list_commands: bool = typer.Option(False, "--list", "-l", help="List all available commands")):
    """Main entry point for GitWise."""
    if list_commands:
        typer.echo("\nGitwise-specific commands:")
        for cmd, desc in GITWISE_COMMANDS.items():
            typer.echo(f"  {cmd:<10} {desc}")
        
        typer.echo("\nGit passthrough commands:")
        for cmd, desc in GIT_PASSTHROUGH_COMMANDS.items():
            typer.echo(f"  {cmd:<10} {desc}")
        
        typer.echo("\nExamples:")
        typer.echo("  gitwise commit              # Create a smart commit")
        typer.echo("  gitwise push                # Push changes with PR option")
        typer.echo("  gitwise status              # Regular git status")
        typer.echo("  gitwise checkout -b new     # Regular git checkout")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        # If no command is provided, show help
        typer.echo(ctx.get_help())
        raise typer.Exit()

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def git(ctx: typer.Context):
    """Pass through to git command.
    
    Examples:
        gitwise git status
        gitwise git checkout -b feature/new
        gitwise git log --oneline
    """
    if not ctx.args:
        typer.echo("Please provide a git command.")
        typer.echo("\nExamples:")
        typer.echo("  gitwise git status")
        typer.echo("  gitwise git checkout -b feature/new")
        typer.echo("  gitwise git log --oneline")
        raise typer.Exit(1)
    
    result = subprocess.run(["git"] + ctx.args)
    raise typer.Exit(code=result.returncode)

# Add a catch-all command for unknown commands
@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def catch_all(ctx: typer.Context):
    """Pass through to git command."""
    if not ctx.args:
        typer.echo("Please provide a git command.")
        raise typer.Exit(1)
    
    command = ctx.args[0]
    args = ctx.args[1:]
    
    # If it's a gitwise command, run it
    if command in GITWISE_COMMANDS:
        if command == "commit":
            commit_command()
        elif command == "push":
            push_command()
        elif command == "pr":
            pr_command()
    else:
        # Otherwise pass through to git
        result = subprocess.run(["git", command] + args)
        raise typer.Exit(code=result.returncode)

if __name__ == "__main__":
    app() 