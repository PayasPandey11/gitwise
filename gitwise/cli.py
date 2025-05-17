import typer
import sys
import os
import subprocess
from typing import Optional

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

# Define command categories
GITWISE_COMMANDS = {
    "commit": "Generate a smart commit message for staged changes",
    "push": "Push changes with option to create PR",
    "pr": "Create a pull request with AI-generated description",
    "changelog": "Generate a changelog from commit history (coming soon)"
}

GIT_PASSTHROUGH_COMMANDS = {
    "add": "Stage changes (git add passthrough)",
    "git": "Pass through any git command"
}

app = typer.Typer(
    help="""gitwise: AI-powered git assistant

    Smart Features:
    - Generate conventional commit messages using AI
    - Create PRs with AI-generated descriptions
    - Push changes with PR creation option
    - Coming soon: Changelog generation

    Usage:
    - Use gitwise-specific commands for enhanced features
    - Use any git command directly (e.g., gitwise checkout, gitwise status)
    - All git commands are supported through passthrough
    """,
    add_completion=False
)

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
    """Push changes to remote repository with option to create PR.
    
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
    """Generate a changelog from commit history (coming soon)."""
    typer.echo("Changelog generation coming soon!")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, list_commands: bool = typer.Option(False, "--list", "-l", help="List all available commands")):
    """gitwise: AI-powered git assistant with smart commit messages, PR descriptions, and more."""
    if list_commands:
        typer.echo("\nGitwise-specific commands:")
        for cmd, desc in GITWISE_COMMANDS.items():
            typer.echo(f"  {cmd:<10} {desc}")
        
        typer.echo("\nGit passthrough commands:")
        for cmd, desc in GIT_PASSTHROUGH_COMMANDS.items():
            typer.echo(f"  {cmd:<10} {desc}")
        
        typer.echo("\nExamples:")
        typer.echo("  gitwise commit              # Create a smart commit")
        typer.echo("  gitwise push                # Push changes with PR option")
        typer.echo("  gitwise status              # Regular git status")
        typer.echo("  gitwise checkout -b new     # Regular git checkout")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        # If no command is provided, show help
        typer.echo(ctx.get_help())
        raise typer.Exit()

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def git(ctx: typer.Context):
    """Pass through to git command.
    
    Examples:
        gitwise git status
        gitwise git checkout -b feature/new
        gitwise git log --oneline
    """
    if not ctx.args:
        typer.echo("Please provide a git command.")
        typer.echo("\nExamples:")
        typer.echo("  gitwise git status")
        typer.echo("  gitwise git checkout -b feature/new")
        typer.echo("  gitwise git log --oneline")
        raise typer.Exit(1)
    
    result = subprocess.run(["git"] + ctx.args)
    raise typer.Exit(code=result.returncode)

def run_git_command(command: str, args: list) -> None:
    """Run a git command with the given arguments."""
    result = subprocess.run(["git", command] + args)
    raise typer.Exit(code=result.returncode)

# Add a catch-all command for unknown commands
@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def catch_all(ctx: typer.Context):
    """Pass through to git command."""
    if not ctx.args:
        typer.echo("Please provide a git command.")
        raise typer.Exit(1)
    
    command = ctx.args[0]
    args = ctx.args[1:]
    
    # If it's a gitwise command, run it
    if command in GITWISE_COMMANDS:
        GITWISE_COMMANDS[command]()
    else:
        # Otherwise pass through to git
        run_git_command(command, args)

if __name__ == "__main__":
    # Get the command name from sys.argv
    if len(sys.argv) > 1:
        cmd_name = sys.argv[1]
        # If it's not a known command, pass it to git
        if cmd_name not in ["commit", "push", "pr", "changelog", "add", "git", "--help", "-h"]:
            # Remove the command name from sys.argv
            sys.argv.pop(1)
            # Run the git command
            result = subprocess.run(["git", cmd_name] + sys.argv[1:])
            sys.exit(result.returncode)
    
    app() 