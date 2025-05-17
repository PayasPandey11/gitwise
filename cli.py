import typer
import sys
import os
import subprocess

# Support running from both the package and directly as a script
if __name__ == "__main__" and ("gitwise" not in sys.modules and not os.path.exists(os.path.join(os.path.dirname(__file__), "__init__.py"))):
    # Running as a script from gitwise/ directory
    from features.commit import commit_command
    from features.push import push_command
    from features.pr import pr_command
else:
    # Running as a module from parent directory
    from gitwise.features.commit import commit_command
    from gitwise.features.push import push_command
    from gitwise.features.pr import pr_command

app = typer.Typer(help="gitwise: AI-powered git assistant")

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def add(ctx: typer.Context):
    """Pass through to git add."""
    result = subprocess.run(["git", "add"] + ctx.args)
    raise typer.Exit(code=result.returncode)

@app.command()
def commit() -> None:
    """Generate a smart commit message for staged changes on the branch."""
    commit_command()

@app.command()
def push(target_branch: str = None) -> None:
    """Push changes to remote repository.
    
    Args:
        target_branch: Optional target branch to push to. If not provided, will prompt user.
    """
    push_command(target_branch)

@app.command()
def pr() -> None:
    """Create a pull request with an AI-generated title and description."""
    pr_command()

@app.command()
def changelog() -> None:
    """Generate a changelog from commit history."""
    typer.echo("Changelog generation coming soon!")

if __name__ == "__main__":
    app() 