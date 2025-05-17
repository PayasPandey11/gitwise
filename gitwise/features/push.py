import typer
from gitwise.gitutils import get_current_branch, run_git_push

def push_command(target_branch: str = None) -> None:
    """Handle the push command logic.
    
    Args:
        target_branch: Optional target branch to push to. If not provided, will prompt user.
    """
    try:
        current_branch = get_current_branch()
        
        if target_branch is None:
            push_same_branch = typer.confirm(
                f"Push to the same branch ({current_branch})?",
                default=True
            )
            
            if not push_same_branch:
                target_branch = typer.prompt(
                    "Enter the target branch name",
                    default=current_branch
                )
        
        output = run_git_push(target_branch)
        typer.echo("Changes pushed successfully.")
        if output:
            typer.echo(output)
            
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1) 