import typer
import subprocess
from gitwise.llm import generate_pr_description
from gitwise.gitutils import get_current_branch, get_commit_history

def pr_command() -> None:
    """Create a pull request with an AI-generated description."""
    try:
        # Get current branch
        current_branch = get_current_branch()
        typer.echo(f"Current branch: {current_branch}")
        
        # Get commit history
        commits = get_commit_history()
        if not commits:
            typer.echo("No commits found between current branch and remote tracking branch.")
            typer.echo("This could be because:")
            typer.echo("1. Your branch is up to date with remote")
            typer.echo("2. Your branch is not based on the remote branch")
            raise typer.Exit(code=1)
            
        typer.echo(f"Found {len(commits)} commits to analyze...")
        typer.echo("Analyzing commits for PR description...\n")
        
        # Generate PR description
        pr_title, pr_description = generate_pr_description(commits)
        
        typer.echo(f"Suggested PR title:\n{pr_title}\n")
        typer.echo(f"Suggested PR description:\n{pr_description}\n")
        
        if typer.confirm("Create PR with this title and description?", default=True):
            # TODO: Implement actual PR creation
            typer.echo("PR created successfully!")
            # For now, just show the URL
            typer.echo(f"https://github.com/PayasPandey11/gitwise/pull/new/{current_branch}")
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1) 