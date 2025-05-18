"""Command-line interface for GitWise."""

import typer
import sys
import os
import subprocess
from typing import Optional, List
from gitwise.features.commit import commit_command
from gitwise.features.push import push_command
from gitwise.features.pr import pr_command
from gitwise.features.changelog import changelog_command
from gitwise.gitutils import get_staged_files, get_unstaged_files
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

# Support running from both the package and directly as a script
if __name__ == "__main__" and ("gitwise" not in sys.modules and not os.path.exists(os.path.join(os.path.dirname(__file__), "__init__.py"))):
    # Running as a script from gitwise/ directory
    from features.commit import commit_command
    from features.push import push_command
    from features.pr import pr_command
    from features.changelog import changelog_command
    from gitutils import get_staged_files, get_unstaged_files
else:
    # Running as a module from parent directory
    from gitwise.features.commit import commit_command
    from gitwise.features.push import push_command
    from gitwise.features.pr import pr_command
    from gitwise.features.changelog import changelog_command
    from gitwise.gitutils import get_staged_files, get_unstaged_files

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

console = Console()

@app.command()
def add(
    files: List[str] = typer.Argument(None, help="Files to stage. Use '.' for all files."),
    group: bool = typer.Option(False, "--group", "-g", help="Group related changes in commit message")
) -> None:
    """Stage files and prepare for commit with smart grouping."""
    try:
        # Show initial status
        unstaged = get_unstaged_files()
        if not unstaged:
            console.print("[yellow]No changes to stage.[/yellow]")
            return

        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Staging files...", total=None)
            
            if not files or (len(files) == 1 and files[0] == '.'):
                # Stage all files
                subprocess.run(["git", "add", "."], capture_output=True)
            else:
                # Stage specific files
                for file in files:
                    if os.path.exists(file):
                        subprocess.run(["git", "add", file], capture_output=True)
                    else:
                        console.print(f"[red]Warning: File not found - {file}[/red]")
            
            progress.update(task, completed=True)

        # Show staged changes
        staged = get_staged_files()
        if staged:
            table = Table(title="Staged Changes", show_header=True, header_style="bold magenta")
            table.add_column("Status", style="cyan")
            table.add_column("File", style="green")
            
            for status, file in staged:
                table.add_row(status, file)
            
            console.print(Panel(table, title="[bold green]Successfully staged files[/bold green]"))
            
            # Show next steps and handle user input
            console.print("\n[bold]Next steps:[/bold]")
            console.print("1. Review staged changes above")
            console.print("2. Run [cyan]gitwise commit[/cyan] to commit changes")
            if group:
                console.print("   (Changes will be automatically grouped)")
            
            # Handle user input
            choice = typer.prompt(
                "What would you like to do?",
                type=str,
                default="2",
                show_choices=True,
                show_default=True,
                prompt_suffix="\n[1]review/[2]commit/[q]uit "
            ).lower()
            
            if choice == "1":
                # Show diff of staged changes
                result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True)
                console.print("\n[bold]Staged Changes Diff:[/bold]")
                console.print(result.stdout)
                # Ask again what to do
                choice = typer.prompt(
                    "What would you like to do?",
                    type=str,
                    default="2",
                    show_choices=True,
                    show_default=True,
                    prompt_suffix="\n[2]commit/[q]uit "
                ).lower()
            
            if choice == "2":
                # Call commit command
                commit_command(group=group)
            elif choice == "q":
                console.print("[yellow]Operation cancelled.[/yellow]")
            else:
                console.print("[red]Invalid choice.[/red]")
        else:
            console.print("[yellow]No files were staged.[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print("Please try again or use [cyan]git add[/cyan] directly.")

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