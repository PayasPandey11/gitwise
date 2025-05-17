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
            default="u",
            show_choices=True,
            show_default=True,
            prompt_suffix="\n[u]se/[e]dit/[r]egenerate/[a]bort "
        ).lower()

        if action not in ["u", "e", "r", "a"]:
            typer.echo("Invalid option. Please choose from: u, e, r, a")
            continue

        if action == "a":
            typer.echo("Aborted. No commit made.")
            return

        if action == "r":
            guidance = typer.prompt(
                "Enter guidance for the commit message (optional)",
                default="",
                show_default=False
            )
            if guidance:
                typer.echo("Regenerating commit message with guidance...")
                commit_message = generate_commit_message(staged_diff, guidance)
            else:
                typer.echo("Regenerating commit message...")
                commit_message = generate_commit_message(staged_diff)
            continue

        if action == "e":
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
                default="u",
                show_choices=True,
                show_default=True,
                prompt_suffix="\n[u]se/[e]dit/[r]egenerate/[a]bort "
            ).lower()
            if action not in ["u", "e", "r", "a"]:
                typer.echo("Invalid option. Please choose from: u, e, r, a")
                continue
            if action == "a":
                typer.echo("Aborted. No commit made.")
                return
            if action == "r":
                guidance = typer.prompt(
                    "Enter guidance for the commit message (optional)",
                    default="",
                    show_default=False
                )
                if guidance:
                    typer.echo("Regenerating commit message with guidance...")
                    commit_message = generate_commit_message(staged_diff, guidance)
                else:
                    typer.echo("Regenerating commit message...")
                    commit_message = generate_commit_message(staged_diff)
                continue

        # If we get here, action is "u"
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