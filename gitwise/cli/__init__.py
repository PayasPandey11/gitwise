"""CLI package for GitWise."""

import typer
import sys
import os
import subprocess
from typing import Optional, List
from gitwise.cli.add import add_command
from gitwise.features.commit import commit_command
from gitwise.features.push import push_command
from gitwise.features.pr import pr_command
from gitwise.features.changelog import changelog_command
from gitwise.ui import components

# Define command categories with emojis and better descriptions
GITWISE_COMMANDS = {
    "commit": "📝 Generate a smart commit message for staged changes",
    "push": "⬆️  Push changes with option to create PR",
    "pr": "🔀 Create a pull request with AI-generated description",
    "changelog": "📋 Manage changelog with automatic updates"
}

GIT_PASSTHROUGH_COMMANDS = {
    "add": "➕ Stage changes with smart preview",
    "git": "🔄 Pass through any git command"
}

app = typer.Typer(
    help="""[bold blue]gitwise[/bold blue]: AI-powered git assistant 🤖

    [bold]Smart Features:[/bold]
    • [cyan]Smart Commits[/cyan] - Generate conventional commit messages using AI
    • [cyan]Smart PRs[/cyan] - Create PRs with AI-generated descriptions
    • [cyan]Smart Push[/cyan] - Push changes with automatic PR creation
    • [cyan]Smart Changelog[/cyan] - Automatic changelog management

    [bold]Usage:[/bold]
    • Use [cyan]gitwise --list[/cyan] to see all available commands
    • Use [cyan]gitwise <command> --help[/cyan] for detailed command help
    • All git commands are supported (e.g., [cyan]gitwise status[/cyan])

    [bold]Examples:[/bold]
    • [cyan]gitwise add .[/cyan] - Stage and prepare changes
    • [cyan]gitwise commit[/cyan] - Create a smart commit
    • [cyan]gitwise pr[/cyan] - Create a PR with AI description
    • [cyan]gitwise status[/cyan] - Regular git status
    • [cyan]gitwise checkout -b new[/cyan] - Regular git checkout
    """,
    add_completion=False,
    rich_markup_mode="rich"
)

@app.command()
def add(
    files: List[str] = typer.Argument(None, help="Files to stage. Use '.' for all files."),
    group: bool = typer.Option(False, "--group", "-g", help="Group related changes in commit message")
) -> None:
    """Stage files and prepare for commit with smart grouping."""
    add_command(files, group)

@app.command()
def commit(
    message: Optional[str] = typer.Argument(None, help="Commit message"),
    group: bool = typer.Option(True, "--group/--no-group", help="Group related changes into logical commits")
) -> None:
    """Create a commit with a smart message."""
    commit_command(message, group)

@app.command()
def push() -> None:
    """Push changes to the remote repository."""
    push_command()

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
        components.console.print("\n[bold blue]GitWise Commands[/bold blue]")
        components.console.print("\n[bold]Smart Commands:[/bold]")
        for cmd, desc in GITWISE_COMMANDS.items():
            components.console.print(f"  [cyan]{cmd:<10}[/cyan] {desc}")
        
        components.console.print("\n[bold]Git Commands:[/bold]")
        for cmd, desc in GIT_PASSTHROUGH_COMMANDS.items():
            components.console.print(f"  [cyan]{cmd:<10}[/cyan] {desc}")
        
        components.console.print("\n[bold]Examples:[/bold]")
        components.console.print("  [cyan]gitwise add .[/cyan]              # Stage and prepare changes")
        components.console.print("  [cyan]gitwise commit[/cyan]             # Create a smart commit")
        components.console.print("  [cyan]gitwise pr[/cyan]                 # Create a PR with AI description")
        components.console.print("  [cyan]gitwise status[/cyan]             # Regular git status")
        components.console.print("  [cyan]gitwise checkout -b new[/cyan]    # Regular git checkout")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        # If no command is provided, show help
        components.console.print(ctx.get_help())
        raise typer.Exit()

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def git(ctx: typer.Context):
    """Pass through to git command with enhanced output."""
    if not ctx.args:
        components.show_warning("Please provide a git command.")
        components.console.print("\n[bold]Examples:[/bold]")
        components.console.print("  [cyan]gitwise git status[/cyan]")
        components.console.print("  [cyan]gitwise git checkout -b feature/new[/cyan]")
        components.console.print("  [cyan]gitwise git log --oneline[/cyan]")
        raise typer.Exit(1)

    try:
        with components.show_spinner(f"Running git {' '.join(ctx.args)}...") as progress:
            result = subprocess.run(["git"] + ctx.args, capture_output=True, text=True)

            if result.returncode == 0:
                if result.stdout:
                    components.console.print(result.stdout)
                components.show_success("Command completed successfully!")
            else:
                components.show_error(result.stderr)
                raise typer.Exit(result.returncode)

    except Exception as e:
        components.show_error(str(e))
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 