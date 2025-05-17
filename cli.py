import typer
import sys
import os
import subprocess

# Support running from both the package and directly as a script
if __name__ == "__main__" and ("gitwise" not in sys.modules and not os.path.exists(os.path.join(os.path.dirname(__file__), "__init__.py"))):
    # Running as a script from gitwise/ directory
    from features.commit import commit_command
else:
    # Running as a module from parent directory
    from gitwise.features.commit import commit_command

app = typer.Typer(help="gitwise: AI-powered git assistant")

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def add(ctx: typer.Context):
    """Pass through to git add."""
    result = subprocess.run(["git", "add"] + ctx.args)
    raise typer.Exit(code=result.returncode)

@app.command()
def commit() -> None:
    """Generate a smart commit message for staged changes."""
    commit_command()

@app.command()
def pr() -> None:
    """Generate a PR message for the current branch."""
    typer.echo("PR message generation coming soon!")

@app.command()
def changelog() -> None:
    """Generate a changelog from commit history."""
    typer.echo("Changelog generation coming soon!")

if __name__ == "__main__":
    app() 