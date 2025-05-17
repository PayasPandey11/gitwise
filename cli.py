import typer
from gitwise.features.commit import commit_command

app = typer.Typer(help="gitwise: AI-powered git assistant")

@app.command()
def commit():
    """Generate a smart commit message for staged changes."""
    commit_command()

@app.command()
def pr():
    """Generate a PR message for the current branch."""
    typer.echo("PR message generation coming soon!")

@app.command()
def changelog():
    """Generate a changelog from commit history."""
    typer.echo("Changelog generation coming soon!")

if __name__ == "__main__":
    app() 