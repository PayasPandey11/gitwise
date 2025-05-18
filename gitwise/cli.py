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
                
                # After successful commit, ask about pushing
                if typer.confirm("Would you like to push these changes?", default=False):
                    console.print("\nPushing changes...")
                    push_command()
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
    """Create a commit with a smart message.
    
    This command will:
    1. Analyze your staged changes
    2. Generate a conventional commit message
    3. Allow you to edit or regenerate the message
    4. Create the commit
    5. Optionally push the changes
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            # Show initial status
            task1 = progress.add_task("📊 Analyzing staged changes...", total=None)
            staged = get_staged_files()
            if not staged:
                console.print("[yellow]⚠️  No staged changes found. Please stage your changes first.[/yellow]")
                return
            
            # Show staged files
            table = Table(title="📝 Staged Changes", show_header=True, header_style="bold magenta")
            table.add_column("Status", style="cyan")
            table.add_column("File", style="green")
            
            for status, file in staged:
                table.add_row(status, file)
            
            console.print(Panel(table, title="[bold green]Files to Commit[/bold green]"))
            
            # Generate commit message
            progress.update(task1, description="🤖 Generating commit message...")
            commit_command(message=message, group=group)
            progress.update(task1, completed=True)
            
            # Show success message
            console.print("\n[bold green]✅ Commit created successfully![/bold green]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def push() -> None:
    """Push changes to the remote repository.
    
    This command will:
    1. Push your changes to the remote
    2. Optionally create a PR if not on main branch
    3. Show the PR URL if created
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            # Check branch
            task1 = progress.add_task("🔍 Checking branch status...", total=None)
            current_branch = get_current_branch()
            progress.update(task1, completed=True)
            
            # Show commits to push
            task2 = progress.add_task("📜 Analyzing commits to push...", total=None)
            commits = get_commit_history()
            if commits:
                table = Table(title="📝 Commits to Push", show_header=True, header_style="bold magenta")
                table.add_column("Hash", style="cyan")
                table.add_column("Message", style="green")
                
                for commit in commits:
                    table.add_row(
                        commit['hash'][:7],
                        commit['message']
                    )
                
                console.print(Panel(table, title="[bold blue]Push Preview[/bold blue]"))
            
            # Push changes
            progress.update(task2, description="⬆️  Pushing changes...")
            push_command()
            progress.update(task2, completed=True)
            
            # Show success message
            console.print("\n[bold green]✅ Changes pushed successfully![/bold green]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def pr(
    use_labels: bool = typer.Option(False, "--use-labels/--no-labels", help="Add labels based on commit types"),
    use_checklist: bool = typer.Option(False, "--use-checklist/--no-checklist", help="Add checklist based on changed files"),
    skip_general_checklist: bool = typer.Option(False, "--skip-general-checklist/--no-skip-general-checklist", help="Skip general checklist items")
) -> None:
    """Create a pull request with a smart description.
    
    This command will:
    1. Analyze your commits
    2. Generate a PR title and description
    3. Add labels and checklist if requested
    4. Create the PR and show the URL
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            # Get current branch
            task1 = progress.add_task("🔍 Checking branch status...", total=None)
            current_branch = get_current_branch()
            progress.update(task1, completed=True)
            
            # Get commits
            task2 = progress.add_task("📜 Analyzing commits...", total=None)
            commits = get_commit_history()
            if not commits:
                console.print("[yellow]⚠️  No commits found to create PR for.[/yellow]")
                return
            
            # Show commits
            table = Table(title="📝 Commits to Include", show_header=True, header_style="bold magenta")
            table.add_column("Hash", style="cyan")
            table.add_column("Message", style="green")
            table.add_column("Author", style="yellow")
            
            for commit in commits:
                table.add_row(
                    commit['hash'][:7],
                    commit['message'],
                    commit['author']
                )
            
            console.print(Panel(table, title="[bold blue]PR Preview[/bold blue]"))
            
            # Generate PR
            progress.update(task2, description="🤖 Generating PR description...")
            pr_command(use_labels, use_checklist, skip_general_checklist)
            progress.update(task2, completed=True)
            
            # Show success message
            console.print("\n[bold green]✅ PR created successfully![/bold green]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)

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
        console.print("\n[bold blue]GitWise Commands[/bold blue]")
        console.print("\n[bold]Smart Commands:[/bold]")
        for cmd, desc in GITWISE_COMMANDS.items():
            console.print(f"  [cyan]{cmd:<10}[/cyan] {desc}")
        
        console.print("\n[bold]Git Commands:[/bold]")
        for cmd, desc in GIT_PASSTHROUGH_COMMANDS.items():
            console.print(f"  [cyan]{cmd:<10}[/cyan] {desc}")
        
        console.print("\n[bold]Examples:[/bold]")
        console.print("  [cyan]gitwise add .[/cyan]              # Stage and prepare changes")
        console.print("  [cyan]gitwise commit[/cyan]             # Create a smart commit")
        console.print("  [cyan]gitwise pr[/cyan]                 # Create a PR with AI description")
        console.print("  [cyan]gitwise status[/cyan]             # Regular git status")
        console.print("  [cyan]gitwise checkout -b new[/cyan]    # Regular git checkout")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        # If no command is provided, show help
        console.print(ctx.get_help())
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