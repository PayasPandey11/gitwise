"""Command-line interface for GitWise."""

import typer
import sys
import os
import subprocess
import tempfile
import re
from typing import Optional, List, Dict, Tuple
from gitwise.features.commit import commit_command
from gitwise.features.push import push_command
from gitwise.features.pr import pr_command
from gitwise.features.changelog import changelog_command
from gitwise.gitutils import get_staged_files, get_unstaged_files, get_staged_diff
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.spinner import Spinner
from rich.text import Text
from rich.box import ROUNDED

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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            # Check for unstaged changes
            task1 = progress.add_task("🔍 Checking for changes...", total=None)
            unstaged = get_unstaged_files()
            if not unstaged:
                console.print(Panel(
                    "[yellow]No changes to stage.[/yellow]",
                    title="[bold blue]Status[/bold blue]",
                    border_style="blue",
                    box=ROUNDED
                ))
                return

            # Stage files
            progress.update(task1, description="📦 Staging files...")
            if not files or (len(files) == 1 and files[0] == '.'):
                subprocess.run(["git", "add", "."], capture_output=True)
            else:
                for file in files:
                    if os.path.exists(file):
                        subprocess.run(["git", "add", file], capture_output=True)
                    else:
                        console.print(Panel(
                            f"[red]Warning: File not found - {file}[/red]",
                            title="[bold red]Error[/bold red]",
                            border_style="red",
                            box=ROUNDED
                        ))

            # Show staged changes
            progress.update(task1, description="📊 Analyzing staged changes...")
            staged = get_staged_files()
            if staged:
                # Create a beautiful table for staged changes
                table = Table(
                    title="📝 Staged Changes",
                    show_header=True,
                    header_style="bold magenta",
                    box=ROUNDED,
                    title_style="bold blue"
                )
                table.add_column("Status", style="cyan", justify="center")
                table.add_column("File", style="green")
                
                for status, file in staged:
                    table.add_row(status, file)
                
                console.print(Panel(
                    table,
                    title="[bold blue]Changes Overview[/bold blue]",
                    border_style="blue",
                    box=ROUNDED,
                    expand=False
                ))

                # Show diff in a more elegant way
                progress.update(task1, description="🔍 Analyzing changes...")
                for status, file in staged:
                    result = subprocess.run(
                        ["git", "diff", "--cached", "--", file],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.stdout:
                        # Create a diff table
                        diff_table = Table(
                            show_header=False,
                            box=ROUNDED,
                            padding=(0, 1),
                            title=f"[bold]{status} {file}[/bold]",
                            title_style="bold blue"
                        )
                        diff_table.add_column("Content", style="white")
                        
                        # Process diff lines
                        diff_lines = []
                        current_hunk = []
                        context_lines = []
                        
                        for line in result.stdout.splitlines():
                            if line.startswith('@@'):
                                if current_hunk:
                                    if context_lines:
                                        diff_lines.extend(context_lines)
                                        context_lines = []
                                    diff_lines.extend(current_hunk)
                                    diff_lines.append('')
                                current_hunk = [f"[blue]{line}[/blue]"]
                            elif line.startswith('+') and not line.startswith('+++'):
                                current_hunk.append(f"[green]{line}[/green]")
                            elif line.startswith('-') and not line.startswith('---'):
                                current_hunk.append(f"[red]{line}[/red]")
                            elif line.startswith(' '):
                                if len(context_lines) < 3:
                                    context_lines.append(line)
                                current_hunk.append(line)
                        
                        if current_hunk:
                            if context_lines:
                                diff_lines.extend(context_lines)
                            diff_lines.extend(current_hunk)
                        
                        # Add lines to table
                        for line in diff_lines[:30]:  # Show first 30 lines
                            diff_table.add_row(line)
                        
                        if len(diff_lines) > 30:
                            diff_table.add_row("...")
                        
                        console.print(Panel(
                            diff_table,
                            title=f"[bold blue]Changes in {file}[/bold blue]",
                            border_style="blue",
                            box=ROUNDED,
                            expand=False
                        ))

                # Simplified workflow with better styling
                console.print("\n[bold blue]What would you like to do?[/bold blue]")
                options = [
                    ("1", "Create commit", "cyan"),
                    ("2", "Review changes", "cyan"),
                    ("3", "Quit", "cyan")
                ]
                
                for key, text, color in options:
                    console.print(f"[{color}]{key}[/{color}] {text}")
                
                choice = typer.prompt(
                    "Select an option",
                    type=int,
                    default=1,
                    show_default=True
                )
                
                if choice == 1:
                    commit_command(group=group)
                    # After commit, offer to push with better styling
                    if typer.confirm("\n[bold blue]Would you like to push these changes?[/bold blue]", default=True):
                        push_command()
                elif choice == 2:
                    # Show full diff in a more elegant way
                    result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True)
                    if result.stdout:
                        diff_panel = Panel(
                            result.stdout,
                            title="[bold blue]Full Changes Diff[/bold blue]",
                            border_style="blue",
                            box=ROUNDED,
                            expand=False
                        )
                        console.print(diff_panel)
                else:
                    console.print(Panel(
                        "[yellow]Operation cancelled.[/yellow]",
                        title="[bold blue]Status[/bold blue]",
                        border_style="blue",
                        box=ROUNDED
                    ))
            else:
                console.print(Panel(
                    "[yellow]No files were staged.[/yellow]",
                    title="[bold blue]Status[/bold blue]",
                    border_style="blue",
                    box=ROUNDED
                ))
                
    except Exception as e:
        console.print(Panel(
            f"[red]Error: {str(e)}[/red]",
            title="[bold red]Error[/bold red]",
            border_style="red",
            box=ROUNDED
        ))
        console.print("Please try again or use [cyan]git add[/cyan] directly.")

@app.command()
def commit(
    message: Optional[str] = typer.Argument(None, help="Commit message"),
    group: bool = typer.Option(True, "--group/--no-group", help="Group related changes into logical commits")
) -> None:
    """Create a commit with a smart message."""
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
            table = Table(title="📝 Staged Changes", show_header=True, header_style="bold magenta", box=ROUNDED)
            table.add_column("Status", style="cyan")
            table.add_column("File", style="green")
            
            for status, file in staged:
                table.add_row(status, file)
            
            console.print(Panel(table, title="[bold green]Files to Commit[/bold green]", box=ROUNDED, expand=False))
            
            # Get staged diff
            task2 = progress.add_task("🔍 Analyzing changes...", total=None)
            staged_diff = get_staged_diff()
            progress.update(task2, completed=True)
            
            # Show changes in a more organized way
            changes_overview = []
            for status, file in staged:
                # Get file-specific diff
                result = subprocess.run(
                    ["git", "diff", "--cached", "--", file],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    # Parse and format the diff
                    diff_lines = []
                    current_hunk = []
                    context_lines = []
                    for line in result.stdout.splitlines():
                        if line.startswith('@@'):
                            if current_hunk:
                                # Add context lines before the hunk
                                if context_lines:
                                    diff_lines.extend(context_lines)
                                    context_lines = []
                                diff_lines.extend(current_hunk)
                                diff_lines.append('')
                            current_hunk = [f"[blue]{line}[/blue]"]
                        elif line.startswith('+') and not line.startswith('+++'):
                            current_hunk.append(f"[green]{line}[/green]")
                        elif line.startswith('-') and not line.startswith('---'):
                            current_hunk.append(f"[red]{line}[/red]")
                        elif line.startswith(' '):
                            # Keep track of context lines
                            if len(context_lines) < 3:  # Keep last 3 context lines
                                context_lines.append(line)
                            current_hunk.append(line)
                    
                    if current_hunk:
                        if context_lines:
                            diff_lines.extend(context_lines)
                        diff_lines.extend(current_hunk)
                    
                    # Show the diff in a panel
                    if diff_lines:
                        # Create a table for the diff
                        diff_table = Table(show_header=False, box=ROUNDED, padding=(0, 1))
                        diff_table.add_column("Content", style="white")
                        
                        for line in diff_lines[:30]:
                            diff_table.add_row(line)
                        
                        if len(diff_lines) > 30:
                            diff_table.add_row("...")
                        
                        changes_overview.append(Panel(
                            diff_table,
                            title=f"[bold]{status} {file}[/bold]",
                            border_style="blue",
                            box=ROUNDED,
                            expand=False
                        ))
            
            # Show all changes in a single panel
            if changes_overview:
                console.print(Panel(
                    "\n".join(str(panel) for panel in changes_overview),
                    title="[bold blue]Changes Overview[/bold blue]",
                    border_style="blue",
                    box=ROUNDED,
                    expand=False
                ))
            
            # Generate commit message
            progress.update(task1, description="🤖 Generating commit message...")
            commit_message = generate_commit_message(staged_diff)
            progress.update(task1, completed=True)
            
            # Show commit message in a nice panel
            console.print(Panel(
                Panel(
                    commit_message,
                    title="[bold green]Review Message[/bold green]",
                    border_style="green",
                    box=ROUNDED,
                    expand=False
                ),
                title="[bold blue]Suggested Commit Message[/bold blue]",
                border_style="blue",
                box=ROUNDED,
                expand=False
            ))
            
            # Handle commit message options
            while True:
                choice = typer.prompt(
                    "What would you like to do?",
                    type=str,
                    default="u",
                    show_choices=True,
                    show_default=True,
                    prompt_suffix="\n[u]se/[e]dit/[r]egenerate/[a]bort "
                ).lower()
                
                if choice == "a":
                    console.print("[yellow]Operation cancelled.[/yellow]")
                    return
                
                if choice == "r":
                    progress.add_task("🔄 Regenerating commit message...", total=None)
                    commit_message = generate_commit_message(staged_diff)
                    console.print(Panel(
                        Panel(
                            commit_message,
                            title="[bold green]New Commit Message[/bold green]",
                            border_style="green",
                            box=ROUNDED,
                            expand=False
                        ),
                        title="[bold blue]Suggested Commit Message[/bold blue]",
                        border_style="blue",
                        box=ROUNDED,
                        expand=False
                    ))
                    continue
                
                if choice == "e":
                    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
                        tf.write(commit_message)
                        tf.flush()
                        editor = os.environ.get("EDITOR", "vi")
                        os.system(f'{editor} {tf.name}')
                        tf.seek(0)
                        commit_message = tf.read().strip()
                    os.unlink(tf.name)
                    console.print(Panel(
                        Panel(
                            commit_message,
                            title="[bold green]Edited Commit Message[/bold green]",
                            border_style="green",
                            box=ROUNDED,
                            expand=False
                        ),
                        title="[bold blue]Suggested Commit Message[/bold blue]",
                        border_style="blue",
                        box=ROUNDED,
                        expand=False
                    ))
                    continue
                
                if choice == "u":
                    break
            
            # Create commit
            task3 = progress.add_task("💾 Creating commit...", total=None)
            run_git_commit(commit_message)
            progress.update(task3, completed=True)
            
            # Show success message
            console.print("\n[bold green]✅ Commit created successfully![/bold green]")
            
            # Ask about pushing
            if typer.confirm("\nWould you like to push these changes?", default=False):
                console.print("\n[bold blue]Pushing Changes[/bold blue]")
                push_command()
            
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
    """Generate a changelog for the repository.
    
    This command will:
    1. Analyze your repository's version history
    2. Generate or update the changelog
    3. Optionally create version tags
    4. Set up automatic updates
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            if setup_hook:
                task = progress.add_task("🔧 Setting up commit hook...", total=None)
                changelog_command(version, create_tag, auto_update, setup_hook)
                progress.update(task, completed=True)
                console.print("\n[bold green]✅ Commit hook set up successfully![/bold green]")
                return

            if auto_update:
                task = progress.add_task("📝 Updating unreleased section...", total=None)
                changelog_command(version, create_tag, auto_update, setup_hook)
                progress.update(task, completed=True)
                console.print("\n[bold green]✅ Changelog updated successfully![/bold green]")
                return

            # Get version tags
            task1 = progress.add_task("🔍 Checking version tags...", total=None)
            tags = get_version_tags()
            progress.update(task1, completed=True)

            if not tags:
                if create_tag:
                    # Get commits since last tag
                    task2 = progress.add_task("📜 Analyzing commits...", total=None)
                    commits = get_commits_between_tags(None, "HEAD")
                    progress.update(task2, completed=True)

                    if not commits:
                        console.print("[yellow]⚠️  No commits found to create a version tag.[/yellow]")
                        return

                    # Show commits
                    table = Table(title="📝 Commits to Include", show_header=True, header_style="bold magenta")
                    table.add_column("Hash", style="cyan")
                    table.add_column("Message", style="green")
                    table.add_column("Author", style="yellow")

                    for commit in commits:
                        table.add_row(
                            commit['hash'][:7],
                            commit['message'].split('\n')[0],  # Show only first line
                            commit['author']
                        )

                    console.print(Panel(table, title="[bold blue]Version Preview[/bold blue]"))

                    # Suggest next version
                    task3 = progress.add_task("🤖 Suggesting next version...", total=None)
                    suggested_version, explanation = suggest_next_version(commits)
                    progress.update(task3, completed=True)

                    console.print(f"\n[bold]Suggested version:[/bold] [cyan]{suggested_version}[/cyan]")
                    console.print(f"[bold]Reason:[/bold] {explanation}")

                    if typer.confirm("\nCreate this version?", default=True):
                        task4 = progress.add_task("📝 Creating version...", total=None)
                        changelog_command(suggested_version, create_tag, auto_update, setup_hook)
                        progress.update(task4, completed=True)
                        console.print("\n[bold green]✅ Version created successfully![/bold green]")
                else:
                    console.print("[yellow]⚠️  No version tags found in the repository.[/yellow]")
                    console.print("Run [cyan]gitwise changelog --create-tag[/cyan] to create a version tag.")
            else:
                task2 = progress.add_task("📝 Generating changelog...", total=None)
                changelog_command(version, create_tag, auto_update, setup_hook)
                progress.update(task2, completed=True)
                console.print("\n[bold green]✅ Changelog generated successfully![/bold green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)

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
    """Pass through to git command with enhanced output.
    
    Examples:
        gitwise git status
        gitwise git checkout -b feature/new
        gitwise git log --oneline
    """
    if not ctx.args:
        console.print("[yellow]⚠️  Please provide a git command.[/yellow]")
        console.print("\n[bold]Examples:[/bold]")
        console.print("  [cyan]gitwise git status[/cyan]")
        console.print("  [cyan]gitwise git checkout -b feature/new[/cyan]")
        console.print("  [cyan]gitwise git log --oneline[/cyan]")
        raise typer.Exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"🔄 Running git {' '.join(ctx.args)}...", total=None)
            result = subprocess.run(["git"] + ctx.args, capture_output=True, text=True)
            progress.update(task, completed=True)

            if result.returncode == 0:
                if result.stdout:
                    console.print(result.stdout)
                console.print("[bold green]✅ Command completed successfully![/bold green]")
            else:
                console.print(f"[red]❌ Error: {result.stderr}[/red]")
                raise typer.Exit(result.returncode)

    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)

# Add a catch-all command for unknown commands
@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def catch_all(ctx: typer.Context):
    """Pass through to git command with enhanced output."""
    if not ctx.args:
        console.print("[yellow]⚠️  Please provide a git command.[/yellow]")
        raise typer.Exit(1)

    command = ctx.args[0]
    args = ctx.args[1:]

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            # If it's a gitwise command, run it
            if command in GITWISE_COMMANDS:
                task = progress.add_task(f"🤖 Running {command} command...", total=None)
                if command == "commit":
                    commit_command()
                elif command == "push":
                    push_command()
                elif command == "pr":
                    pr_command()
                progress.update(task, completed=True)
                console.print(f"[bold green]✅ {command} command completed successfully![/bold green]")
            else:
                # Otherwise pass through to git
                task = progress.add_task(f"🔄 Running git {command}...", total=None)
                result = subprocess.run(["git", command] + args, capture_output=True, text=True)
                progress.update(task, completed=True)

                if result.returncode == 0:
                    if result.stdout:
                        console.print(result.stdout)
                    console.print("[bold green]✅ Command completed successfully![/bold green]")
                else:
                    console.print(f"[red]❌ Error: {result.stderr}[/red]")
                    raise typer.Exit(result.returncode)

    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)

def get_version_tags() -> List[str]:
    """Get all version tags from the repository."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-v:refname"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return [tag for tag in result.stdout.splitlines() if tag]
        return []
    except Exception:
        return []

def get_commits_between_tags(start_tag: Optional[str], end_tag: str) -> List[Dict]:
    """Get commits between two tags."""
    try:
        range_spec = f"{start_tag}..{end_tag}" if start_tag else end_tag
        result = subprocess.run(
            ["git", "log", "--pretty=format:%h|%s|%an", range_spec],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            commits = []
            for line in result.stdout.splitlines():
                if line:
                    hash_, message, author = line.split("|", 2)
                    commits.append({
                        "hash": hash_,
                        "message": message,
                        "author": author
                    })
            return commits
        return []
    except Exception:
        return []

def suggest_next_version(commits: List[Dict]) -> Tuple[str, str]:
    """Suggest the next version based on commit messages."""
    # Simple version suggestion logic
    major = minor = patch = 0
    for commit in commits:
        msg = commit["message"].lower()
        # Check for breaking changes
        if "breaking" in msg or "major" in msg or "!" in msg:
            major += 1
        # Check for features
        elif any(x in msg for x in ["feat", "feature", "add", "new"]):
            minor += 1
        # Everything else is a patch
        else:
            patch += 1
    
    # Get current version from latest tag
    current_version = "0.0.0"
    tags = get_version_tags()
    if tags:
        current_version = tags[0]  # Most recent tag
    
    # Parse current version
    try:
        major_curr, minor_curr, patch_curr = map(int, current_version.lstrip('v').split('.'))
        major += major_curr
        minor += minor_curr
        patch += patch_curr
    except (ValueError, IndexError):
        pass
    
    # Generate new version and reason
    if major > 0:
        return f"v{major}.0.0", "Major version bump due to breaking changes"
    elif minor > 0:
        return f"v0.{minor}.0", "Minor version bump due to new features"
    else:
        return f"v0.0.{patch}", "Patch version bump for fixes and improvements"

def format_commit_for_changelog(commit: Dict) -> str:
    """Format a commit message for the changelog."""
    msg = commit["message"].strip()
    # Remove conventional commit prefix if present
    msg = re.sub(r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([^)]+\))?:\s*', '', msg)
    # Take first line only
    msg = msg.split('\n')[0]
    return f"- {msg}"

if __name__ == "__main__":
    app() 