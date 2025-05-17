import typer
import subprocess
from gitwise.llm import generate_pr_description
from gitwise.gitutils import get_current_branch, get_commit_history

def pr_command() -> None:
    """Handle the PR command logic."""
    try:
        # Get current branch
        current_branch = get_current_branch()
        
        # Get commit history since last common ancestor with main
        commits = get_commit_history()
        
        if not commits:
            typer.echo("No commits found to create PR from.")
            return
            
        typer.echo("Analyzing commits for PR description...")
        pr_title, pr_description = generate_pr_description(commits)
        
        typer.echo(f"\nSuggested PR title:\n{pr_title}\n")
        typer.echo(f"Suggested PR description:\n{pr_description}\n")
        
        # Ask for confirmation
        confirm = typer.confirm("Create PR with this title and description?", default=True)
        if not confirm:
            typer.echo("PR creation aborted.")
            return
            
        # Create PR using GitHub CLI if available
        try:
            result = subprocess.run(
                ["gh", "pr", "create", 
                 "--title", pr_title,
                 "--body", pr_description,
                 "--base", "main"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                typer.echo("PR created successfully!")
                typer.echo(result.stdout)
            else:
                typer.echo("Failed to create PR using GitHub CLI. Please create it manually:")
                typer.echo("\nTitle:")
                typer.echo(pr_title)
                typer.echo("\nDescription:")
                typer.echo(pr_description)
        except FileNotFoundError:
            typer.echo("GitHub CLI not found. Please create the PR manually:")
            typer.echo("\nTitle:")
            typer.echo(pr_title)
            typer.echo("\nDescription:")
            typer.echo(pr_description)
            
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1) 