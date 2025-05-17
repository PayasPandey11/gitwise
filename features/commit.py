import typer
import tempfile
import os
from gitwise.llm import generate_commit_message
from gitwise.gitutils import get_staged_diff, run_git_commit
from gitwise.features.push import push_command

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
    
    while True:
        commit_message = generate_commit_message(staged_diff)
        typer.echo(f"\nSuggested commit message:\n{commit_message}\n")

        action = typer.prompt(
            "What would you like to do?",
            type=str,
            default="use",
            show_choices=True,
            show_default=True,
            prompt_suffix="\n[use/edit/regenerate/abort] "
        )

        if action not in ["use", "edit", "regenerate", "abort"]:
            typer.echo("Invalid option. Please choose from: use, edit, regenerate, abort")
            continue

        if action == "abort":
            typer.echo("Aborted. No commit made.")
            return

        if action == "regenerate":
            typer.echo("Regenerating commit message...")
            continue

        if action == "edit":
            with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
                tf.write(commit_message)
                tf.flush()
                editor = os.environ.get("EDITOR", "vi")
                os.system(f'{editor} {tf.name}')
                tf.seek(0)
                commit_message = tf.read().strip()
            os.unlink(tf.name)
            typer.echo(f"\nEdited commit message:\n{commit_message}\n")
            action = typer.prompt(
                "What would you like to do?",
                type=str,
                default="use",
                show_choices=True,
                show_default=True,
                prompt_suffix="\n[use/edit/regenerate/abort] "
            )
            if action not in ["use", "edit", "regenerate", "abort"]:
                typer.echo("Invalid option. Please choose from: use, edit, regenerate, abort")
                continue
            if action == "abort":
                typer.echo("Aborted. No commit made.")
                return
            if action == "regenerate":
                typer.echo("Regenerating commit message...")
                continue

        # If we get here, action is "use"
        break

    try:
        run_git_commit(commit_message)
        typer.echo("Commit created successfully.")
        
        # Ask about pushing
        push = typer.confirm("Would you like to push these changes?", default=False)
        if push:
            push_command()
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1) 