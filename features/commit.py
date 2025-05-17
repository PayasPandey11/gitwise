import typer
import tempfile
import os
from gitwise.llm import generate_commit_message
from gitwise.gitutils import get_staged_diff, run_git_commit, run_git_push, get_current_branch

def commit_command() -> None:
    """Main logic for the commit command: gets staged diff, generates commit message, allows editing, and commits."""
    try:
        staged_diff = get_staged_diff()
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)

    if not staged_diff:
        typer.echo("No staged changes found. Please stage your changes first.")
        raise typer.Exit(code=0)

    typer.echo("Analyzing staged changes:\n")
    typer.echo(staged_diff[:1000] + ("\n... (truncated) ..." if len(staged_diff) > 1000 else ""))
    commit_message = generate_commit_message(staged_diff)
    typer.echo(f"\nSuggested commit message:\n{commit_message}\n")

    edit = typer.confirm("Would you like to edit the commit message?", default=False)
    final_message = commit_message
    if edit:
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
            tf.write(commit_message)
            tf.flush()
            editor = os.environ.get("EDITOR", "vi")
            os.system(f'{editor} {tf.name}')
            tf.seek(0)
            final_message = tf.read().strip()
        os.unlink(tf.name)
        typer.echo(f"\nEdited commit message:\n{final_message}\n")

    confirm = typer.confirm("Use this commit message?", default=True)
    if confirm:
        try:
            run_git_commit(final_message)
            typer.echo("Commit created successfully.")
            
            # Ask about pushing
            push = typer.confirm("Would you like to push these changes?", default=False)
            if push:
                try:
                    current_branch = get_current_branch()
                    push_same_branch = typer.confirm(
                        f"Push to the same branch ({current_branch})?",
                        default=True
                    )
                    
                    target_branch = None
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
        except RuntimeError as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
    else:
        typer.echo("Aborted. No commit made.") 