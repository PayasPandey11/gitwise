"""Command-line interface for GitWise."""

import subprocess
import sys
from typing import List

import typer

from gitwise.cli.add import add_command_cli
from gitwise.cli.init import init_command
from gitwise.features.changelog import ChangelogFeature
from gitwise.features.commit import CommitFeature
from gitwise.features.context import ContextFeature
from gitwise.features.pr import PrFeature
from gitwise.features.push import PushFeature
from gitwise.ui import components

# Create the main app
app = typer.Typer(
    name="gitwise",
    help="""
    🚀 GitWise - AI-powered Git workflow assistant
    
    Features:
    • Smart commit messages
    • Intelligent PR descriptions
    • Automatic changelog generation
    • Interactive staging and committing
    
    Use 'gitwise <command> --help' for more information about a command.
    """,
    add_completion=False,
)


def check_and_install_offline_deps() -> bool:
    missing = []
    packages_to_check = {"transformers": False, "torch": False}
    try:
        import transformers

        packages_to_check["transformers"] = True
    except ImportError:
        missing.append("transformers")
    try:
        import torch

        packages_to_check["torch"] = True
    except ImportError:
        missing.append("torch")

    if missing:
        print(
            f"[gitwise] Optional dependencies for offline mode ({', '.join(missing)}) are missing."
        )
        print("You can install them with: pip install gitwise[offline]")
        auto = (
            input(
                "Would you like to install them now (pip install gitwise[offline])? [Y/n]: "
            )
            .strip()
            .lower()
        )
        if auto in ("", "y", "yes"):
            cmd = [sys.executable, "-m", "pip", "install", "gitwise[offline]"]
            print(f"[gitwise] Running: {', '.join(cmd)}")
            subprocess.run(cmd)
            print("[gitwise] Dependencies installed! Please re-run your command.")
            return False
        else:
            print("[gitwise] Cannot proceed without required dependencies. Exiting.")
            return False
    return True


# Remove automatic dependency check at import time
# check_and_install_offline_deps()


# Add commands
@app.command(name="add")
def add_cli_entrypoint(
    files: List[str] = typer.Argument(
        None, help="Files to stage (default: all changes)"
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y", 
        help="Automatically answer 'yes' to all prompts (group, push, PR, labels)"
    )
) -> None:
    """Stage files with interactive selection."""
    add_command_cli(files, auto_confirm=yes)


@app.command(name="commit", help="Create a commit with AI-generated message")
def commit_cli_entrypoint(
    group: bool = typer.Option(
        False,
        "--group",
        "-g",
        help="Enable automatic grouping of related changes into separate commits (can be slower).",
    )
) -> None:
    """Create a commit with AI-generated message."""
    feature = CommitFeature()
    feature.execute_commit(group=group)


@app.command(name="push")
def push_cli_entrypoint() -> None:
    """Push changes and optionally create a PR."""
    feature = PushFeature()
    feature.execute_push()


@app.command(name="pr")
def pr_cli_entrypoint(
    from_staged: bool = typer.Option(
        False,
        "--from-staged",
        "-s",
        help="[New] Generate PR and commits together from staged files in a single AI call.",
    ),
    use_labels: bool = typer.Option(
        False, "--labels", "-l", help="Add labels to the PR"
    ),
    use_checklist: bool = typer.Option(
        False, "--checklist", "-c", help="Add checklist to the PR description"
    ),
    skip_general_checklist: bool = typer.Option(
        False, "--skip-checklist", help="Skip general checklist items"
    ),
    title: str = typer.Option(None, "--title", "-t", help="Custom title for the PR"),
    base: str = typer.Option(None, "--base", "-b", help="Base branch for the PR"),
    draft: bool = typer.Option(False, "--draft", "-d", help="Create a draft PR"),
    skip_prompts: bool = typer.Option(
        False, "--skip-prompts", help="Skip all interactive prompts and use defaults."
    ),
    auto_confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Automatically answer 'yes' to all prompts (group, push, PR, labels)",
    ),
) -> None:
    """Create a pull request with AI-generated description."""
    feature = PrFeature()

    if from_staged:
        feature.generate_and_create_pr_from_staged(auto_confirm=auto_confirm)
    else:
        feature.execute_pr(
            use_labels=use_labels,
            use_checklist=use_checklist,
            skip_general_checklist=skip_general_checklist,
            title=title,
            base=base,
            draft=draft,
            skip_prompts=skip_prompts,
            auto_confirm=auto_confirm,
        )


@app.command(name="changelog")
def changelog_cli_entrypoint(
    version: str = typer.Option(
        None, "--version", help="Version string for the changelog"
    ),
    output_file: str = typer.Option(None, "--output-file", help="Output file path"),
    format_output: str = typer.Option(
        "markdown", "--format", help="Output format (markdown or json)"
    ),
    auto_update: bool = typer.Option(
        False,
        "--auto-update",
        help="Automatically update the changelog without prompts",
    ),
) -> None:
    """Generate a changelog from commits since the last tag."""
    feature = ChangelogFeature()
    feature.execute_changelog(
        version=version,
        output_file=output_file,
        format_output=format_output,
        auto_update=auto_update,
    )


@app.command(
    name="git",
    context_settings={"allow_interspersed_args": False, "ignore_unknown_options": True},
)
def git_cli_entrypoint(
    ctx: typer.Context,
    args: List[str] = typer.Argument(None, help="Git command and arguments"),
) -> None:
    """Pass through to git with enhanced output and pager handling for common commands."""
    # args will now correctly capture everything after 'gitwise git'
    if not args:
        components.show_error("No git command provided")
        raise typer.Exit(code=1)

    command_to_run = ["git"] + args

    # Simplified pager handling:
    # The responsibility of piping commands that use a pager (like log, diff)
    # is left to the user or handled by gh's pager if run via `gh alias`.
    # GitWise will stream the output directly.
    # pager_commands = {"log", "diff", "show", "branch"}
    # is_pager_command = args[0] in pager_commands
    # is_piped_by_user = any("|" in arg for arg in args)
    # if is_pager_command and not is_piped_by_user:
    #     pass # No auto-piping

    try:
        # Use Popen for better control over the process
        process = subprocess.Popen(
            command_to_run,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                components.console.print(output.strip())

        # Get the return code
        return_code = process.poll()

        if return_code == 0:
            components.show_success("Git command executed successfully")
        else:
            components.show_error("Git command failed")
            # Print any remaining stderr
            stderr = process.stderr.read()
            if stderr:
                components.console.print(stderr)
            raise typer.Exit(code=return_code)

    except Exception as e:
        components.show_error(str(e))
        raise typer.Exit(code=1)


@app.command(
    "offline-model", help="Check and download the offline LLM model for offline mode."
)
def offline_model_cmd():
    """Check/download the offline LLM model (microsoft/phi-2 by default)."""
    # Only check dependencies when user explicitly requests offline model
    if not check_and_install_offline_deps():
        raise typer.Exit(code=1)

    from gitwise.llm.download import download_offline_model

    download_offline_model()


@app.command(name="init")
def setup_gitwise() -> None:
    """Interactively set up GitWise in this repo or globally."""
    init_command()


@app.command(name="set-context", help="Set context for the current branch to improve AI suggestions")
def set_context_cli_entrypoint(
    context: str = typer.Argument(..., help="Context string describing what you're working on")
) -> None:
    """Set context information for the current branch."""
    feature = ContextFeature()
    feature.execute_set_context(context)


@app.command(name="get-context", help="Display the current context for this branch")
def get_context_cli_entrypoint() -> None:
    """Show stored context for the current branch."""
    feature = ContextFeature()
    feature.execute_get_context()


def main() -> None:
    """Main entry point for the application."""
    try:
        app()
    except Exception as e:
        components.show_error(str(e))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
