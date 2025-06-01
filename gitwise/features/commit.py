"""Feature logic for the 'commit' command, including AI-assisted message generation and grouping."""

import os
import subprocess
import tempfile
from typing import Callable, Dict, List, Optional, Any

import typer

from gitwise.config import ConfigError, get_llm_backend, load_config
from gitwise.core.git_manager import GitManager
from gitwise.llm.router import get_llm_response
from gitwise.prompts import PROMPT_COMMIT_MESSAGE
from gitwise.ui import components
from gitwise.llm.offline import ensure_offline_model_ready

# Initialize GitManager
git_manager = GitManager()


# Import push_command only when needed to avoid circular imports
def get_push_command() -> Callable[[bool], bool]:
    """Dynamically imports and returns the push_command function to avoid circular imports."""
    from gitwise.features.push import PushFeature

    def push_wrapper(auto_confirm: bool = False) -> bool:
        return PushFeature().execute_push(auto_confirm=auto_confirm)

    return push_wrapper


COMMIT_TYPES = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "chore": "Changes to the build process or auxiliary tools",
    "ci": "Changes to CI configuration files and scripts",
    "build": "Changes that affect the build system or external dependencies",
    "revert": "Reverts a previous commit",
}


def safe_prompt(prompt_text: str, options: List[str], default: str = "Yes") -> int:
    """Prompt for user input using Typer with predefined options."""
    components.show_prompt(prompt_text, options=options, default=default)
    choice = typer.prompt("", type=int, default=1)
    return choice


def safe_confirm(prompt_text: str, default: bool = True) -> bool:
    """Prompt for confirmation using Typer."""
    return typer.confirm(prompt_text, default=default)


def safe_prompt_text(prompt_text: str, default: str = "") -> str:
    """Prompt for text input using Typer."""
    return typer.prompt(prompt_text, default=default)


def suggest_scope(changed_files: List[str]) -> str:
    """Suggest a scope based on the most common directory among changed files."""
    dirs = {}
    for file in changed_files:
        dir_name = os.path.dirname(file)
        if dir_name:
            dirs[dir_name] = dirs.get(dir_name, 0) + 1

    if dirs:
        return max(dirs, key=dirs.get)
    return ""


def build_commit_message_interactive() -> str:
    """Interactively build a conventional commit message."""
    changed_files = git_manager.get_changed_file_paths_staged()

    typer.echo("\nSelect commit type:")
    for type_key, desc in COMMIT_TYPES.items():
        typer.echo(f"  {type_key:<10} - {desc}")

    commit_type = safe_prompt_text("\nEnter commit type", default="feat").lower()

    suggested_scope = suggest_scope(changed_files)
    scope = safe_prompt_text("Enter scope (optional)", default=suggested_scope)

    description = safe_prompt_text("Enter commit description")

    body = safe_prompt_text(
        "Enter commit body (optional, press Enter to skip)", default=""
    )

    breaking_changes = ""
    if safe_confirm("Are there any breaking changes?", default=False):
        breaking_changes = safe_prompt_text("Describe the breaking changes")

    message = f"{commit_type}"
    if scope:
        message += f"({scope})"
    message += f": {description}"

    if body:
        message += f"\n\n{body}"

    if breaking_changes:
        message += f"\n\nBREAKING CHANGE: {breaking_changes}"

    return message


def analyze_changes(changed_files: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze changed files to find patterns for grouping.
    Returns a list of suggested commit groups.
    """
    # Group files by directory
    dir_groups = {}
    for file in changed_files:
        dir_name = file.split("/")[0] if "/" in file else "root"
        if dir_name not in dir_groups:
            dir_groups[dir_name] = []
        dir_groups[dir_name].append(file)

    # Create commit suggestions
    suggestions = []
    for dir_name, files in dir_groups.items():
        if len(files) >= 2:  # Only suggest groups with 2+ files
            suggestions.append({"type": "directory", "name": dir_name, "files": files})

    # Check for common patterns
    test_files = [f for f in changed_files if "test" in f.lower()]
    if len(test_files) >= 2:
        suggestions.append({"type": "tests", "name": "Test files", "files": test_files})

    doc_files = [
        f
        for f in changed_files
        if any(ext in f.lower() for ext in [".md", ".rst", ".txt", "readme"])
    ]
    if len(doc_files) >= 2:
        suggestions.append(
            {"type": "docs", "name": "Documentation", "files": doc_files}
        )

    return suggestions


def suggest_commit_groups() -> Optional[List[Dict[str, Any]]]:
    """
    Suggests ways to group staged changes into separate commits.
    Returns None if no good grouping is found.
    """
    try:
        staged = git_manager.get_staged_files()
        if len(staged) < 3:  # Not worth grouping if less than 3 files
            return None

        # Get just the file paths
        staged_paths = [file for _, file in staged]

        # Analyze for patterns
        groups = analyze_changes(staged_paths)

        # Only return if we found meaningful groups
        if groups and len(groups) >= 2:
            return groups
        return None
    except Exception:
        return None


def generate_commit_message(diff: str, guidance: str = "") -> str:
    """Generate a commit message using LLM prompt only. The LLM outputs the full message."""
    prompt = PROMPT_COMMIT_MESSAGE.replace("{{diff}}", diff).replace(
        "{{guidance}}", guidance
    )
    llm_output = get_llm_response(prompt)
    return llm_output.strip()


class CommitFeature:
    """Handles the logic for creating commits, with AI assistance and grouping."""

    def __init__(self):
        """Initializes the CommitFeature, using the module-level GitManager."""
        self.git_manager = git_manager

    def execute_commit(self, group: bool = True, auto_confirm: bool = False) -> None:
        """Create a commit, with an option for AI-assisted message generation and change grouping."""
        try:
            # Config check
            try:
                load_config()
            except ConfigError as e:
                components.show_error(str(e))
                if auto_confirm or typer.confirm(
                    "Would you like to run 'gitwise init' now?", default=True
                ):
                    from gitwise.cli.init import (
                        init_command,
                    )  # Keep local import for CLI specific call

                    init_command()
                return

            backend = get_llm_backend()
            backend_display = {
                "ollama": "Ollama (local server)",
                "offline": "Offline (local model)",
                "online": "Online (OpenRouter)",
            }.get(backend, backend)
            components.show_section(f"[AI] LLM Backend: {backend_display}")

            if backend == "offline":
                try:
                    ensure_offline_model_ready()
                except Exception as e:
                    components.show_error(f"Failed to load offline model: {e}")
                    return

            current_staged_files_paths = (
                self.git_manager.get_changed_file_paths_staged()
            )
            if not current_staged_files_paths:
                components.show_warning(
                    "No files staged for commit. Please stage files first."
                )
                return

            # Updated handling of unstaged and untracked files
            modified_not_staged = self.git_manager.get_list_of_unstaged_tracked_files()
            untracked_files = self.git_manager.get_list_of_untracked_files()

            if modified_not_staged or untracked_files:
                components.show_warning("You have uncommitted changes:")
                if modified_not_staged:
                    components.console.print(
                        "[bold yellow]Modified but not staged:[/bold yellow]"
                    )
                    for file_path in modified_not_staged:
                        components.console.print(f"  M {file_path}")
                if untracked_files:
                    components.console.print(
                        "[bold yellow]Untracked files:[/bold yellow]"
                    )
                    for file_path in untracked_files:
                        components.console.print(f"  ?? {file_path}")

                choice = safe_prompt(
                    "Would you like to stage them before committing, or commit only staged changes?",
                    options=[
                        "Stage all modified and untracked files and commit",
                        "Commit only currently staged",
                        "Abort commit",
                    ],
                    default="Commit only currently staged",
                ) if not auto_confirm else 2  # Auto-select "Commit only currently staged"

                if choice == 1:  # Stage all and commit
                    with components.show_spinner("Staging all changes..."):
                        if (
                            self.git_manager.stage_all()
                        ):  # stage_all will add both modified and untracked
                            components.show_success("All changes staged.")
                            current_staged_files_paths = (
                                self.git_manager.get_changed_file_paths_staged()
                            )
                            if not current_staged_files_paths:
                                components.show_error(
                                    "No files are staged after attempting to stage all. Aborting."
                                )
                                return
                        else:
                            components.show_error(
                                "Failed to stage all changes. Aborting commit."
                            )
                            return
                elif choice == 3:  # Abort
                    components.show_warning("Commit cancelled.")
                    return
                # If choice is 2, we do nothing and proceed with currently staged files

            if group:
                suggestions = None
                with components.show_spinner(
                    "Analyzing changes for potential commit groups..."
                ):
                    suggestions = suggest_commit_groups()  # Uses module-level helper

                if suggestions and len(suggestions) > 1:
                    components.show_section("Suggested Commit Groups")
                    for i, group_item in enumerate(suggestions, 1):
                        components.console.print(f"\n[bold]Group {i}:[/bold]")
                        components.console.print(
                            f"Files: {', '.join(group_item['files'])}"
                        )
                        components.console.print(
                            f"Suggested commit: {group_item['type']}: {group_item['name']}"
                        )

                    choice = safe_prompt(
                        "Commit these groups separately, or consolidate into a single commit?",
                        options=[
                            "Commit separately",
                            "Consolidate into single commit",
                            "Abort",
                        ],
                        default="Commit separately",
                    ) if not auto_confirm else 1  # Auto-select "Commit separately"

                    if choice == 1:  # Commit separately
                        all_files_in_suggestions = sorted(
                            list(
                                set(
                                    f
                                    for group_item in suggestions
                                    for f in group_item["files"]
                                )
                            )
                        )
                        if all_files_in_suggestions:
                            # Unstage files using GitManager via _run_git_command
                            self.git_manager._run_git_command(
                                ["reset", "HEAD", "--"] + all_files_in_suggestions,
                                check=True,
                            )

                        commits_made_in_grouping = False
                        for group_item in suggestions:
                            components.show_section(
                                f"Preparing Group: {', '.join(group_item['files'])}"
                            )

                            if not (auto_confirm or safe_confirm(
                                f"Proceed with committing this group ({group_item['type']}: {group_item['name']})?",
                                default=True,
                            )):
                                components.show_warning(
                                    f"Skipping group: {', '.join(group_item['files'])}"
                                )
                                continue

                            try:
                                self.git_manager.stage_files(group_item["files"])
                                commit_message_for_group = (
                                    f"{group_item['type']}: {group_item['name']}"
                                )
                                with components.show_spinner(
                                    f"Committing group - {len(group_item['files'])} files..."
                                ):
                                    if self.git_manager.create_commit(
                                        commit_message_for_group
                                    ):
                                        components.show_success(
                                            f"✓ Group commit successful: {commit_message_for_group}"
                                        )
                                        commits_made_in_grouping = True
                                    else:
                                        components.show_error(
                                            f"✗ Failed to create commit for group: {group_item['type']}: {group_item['name']}"
                                        )
                                        if not (auto_confirm or safe_confirm(
                                            "Problem committing group. Continue with remaining groups?",
                                            default=True,
                                        )):
                                            return
                            except RuntimeError as e:
                                components.show_error(str(e))
                                if not (auto_confirm or safe_confirm(
                                    "Problem staging files for group. Continue with remaining groups?",
                                    default=True,
                                )):
                                    return

                        if commits_made_in_grouping:
                            if auto_confirm:
                                # Check if we're on main/master branch
                                current_branch = self.git_manager.get_current_branch()
                                default_branch = self.git_manager.get_local_base_branch_name()
                                if current_branch and default_branch and current_branch == default_branch:
                                    components.show_section("Auto-confirm: Skipping push (on main branch)")
                                else:
                                    components.show_section("Auto-confirm: Pushing committed groups")
                                    get_push_command()(auto_confirm)
                            elif safe_confirm("Push all committed groups now?", default=True):
                                get_push_command()(auto_confirm)
                            return

                    elif choice == 3:
                        components.show_warning("Commit operation cancelled by user.")
                        return
                    else:
                        components.show_section(
                            "Consolidating changes into a single commit."
                        )
                        with components.show_spinner(
                            "Re-staging all files for consolidated commit..."
                        ):
                            self.git_manager.stage_files(current_staged_files_paths)

            if not current_staged_files_paths:
                components.show_warning(
                    "No files are staged for the consolidated commit. Aborting."
                )
                return

            components.show_section("Files for Single Commit")
            try:
                staged_files_for_table = self.git_manager.get_staged_files()
                if staged_files_for_table:
                    components.show_files_table(
                        staged_files_for_table, title="Files to be committed"
                    )
                else:
                    components.console.print(
                        "[bold yellow]Warning: Could not retrieve detailed status for staged files. Displaying paths:[/bold yellow]"
                    )
                    for f_path in current_staged_files_paths:
                        components.console.print(f"- {f_path}")
            except RuntimeError as e:
                components.console.print(
                    f"[bold red]Error displaying staged files table: {e}. Displaying paths:[/bold red]"
                )
                for f_path in current_staged_files_paths:
                    components.console.print(f"- {f_path}")

            if not auto_confirm and typer.confirm(
                "View full diff before generating commit message?", default=False
            ):
                full_staged_diff_content = self.git_manager.get_staged_diff()
                if full_staged_diff_content:
                    components.show_diff(
                        full_staged_diff_content, "Full Staged Changes for Commit"
                    )
                else:
                    components.show_warning("No staged changes to diff.")

            components.show_section("Generating Commit Message")
            diff_for_message_generation = self.git_manager.get_staged_diff()
            if not diff_for_message_generation and current_staged_files_paths:
                components.show_warning(
                    "Staged files have no diff content (e.g. new empty files). LLM might produce a generic message."
                )
                diff_for_message_generation = (
                    f"The following files are staged (no content changes detected):\n"
                    + "\n".join(current_staged_files_paths)
                )
            elif not diff_for_message_generation and not current_staged_files_paths:
                components.show_error(
                    "No staged changes or files to generate commit message from. Aborting."
                )
                return

            message = ""
            with components.show_spinner("Analyzing changes..."):
                message = generate_commit_message(diff_for_message_generation)

            components.show_section("Suggested Commit Message")
            components.console.print(message)

            user_choice_for_message = safe_prompt(
                "Use this commit message?",
                options=["Use message", "Edit message", "Regenerate message", "Abort"],
                default="Use message",
            ) if not auto_confirm else 1  # Auto-select "Use message"

            if user_choice_for_message == 4:  # Abort
                components.show_warning("Commit cancelled.")
                return

            if user_choice_for_message == 2:  # Edit
                with tempfile.NamedTemporaryFile(
                    suffix=".txt", delete=False, mode="w+", encoding="utf-8"
                ) as tf:
                    tf.write(message)
                    tf.flush()
                editor = os.environ.get("EDITOR", "vi")
                try:
                    subprocess.run([editor, tf.name], check=True)
                    with open(tf.name, "r", encoding="utf-8") as f_read:
                        message = f_read.read().strip()
                except FileNotFoundError:
                    components.show_error(
                        f"Editor '{editor}' not found. Please set your EDITOR environment variable or install {editor}."
                    )
                    message = safe_prompt_text(
                        "Please manually enter the commit message:", default=message
                    )
                except subprocess.CalledProcessError:
                    components.show_warning(
                        "Editor closed without successful save. Using previous message or enter new one."
                    )
                    message = safe_prompt_text(
                        "Please manually enter/confirm the commit message:",
                        default=message,
                    )
                finally:
                    os.unlink(tf.name)

                if not message.strip():
                    components.show_error(
                        "Commit message cannot be empty after editing. Aborting."
                    )
                    return

                components.show_section("Edited Commit Message")
                components.console.print(message)
                if not safe_confirm(
                    "Proceed with this edited commit message?", default=True
                ):
                    components.show_warning("Commit cancelled.")
                    return

            if user_choice_for_message == 3:  # Regenerate
                with components.show_spinner("Regenerating message..."):
                    message = generate_commit_message(
                        diff_for_message_generation,
                        "Please try a different style or focus for the commit message.",
                    )
                components.show_section("Newly Suggested Commit Message")
                components.console.print(message)
                if not safe_confirm("Use this new message?", default=True):
                    with tempfile.NamedTemporaryFile(
                        suffix=".txt", delete=False, mode="w+", encoding="utf-8"
                    ) as tf:
                        tf.write(message)
                        tf.flush()
                    editor = os.environ.get("EDITOR", "vi")
                    try:
                        subprocess.run([editor, tf.name], check=True)
                        with open(tf.name, "r", encoding="utf-8") as f_read:
                            message = f_read.read().strip()
                    except Exception:
                        components.show_warning(
                            "Failed to edit regenerated message. Using as is or aborting."
                        )
                    finally:
                        os.unlink(tf.name)
                    if not message.strip() or not safe_confirm(
                        f"Use this (potentially edited) message: \n{message}",
                        default=True,
                    ):
                        components.show_warning("Commit cancelled.")
                        return

            components.show_section("Creating Final Commit")
            commit_success = False
            with components.show_spinner("Running git commit..."):
                if self.git_manager.create_commit(message):
                    components.show_success("✓ Git commit created successfully")
                    commit_success = True
                else:
                    components.show_error("✗ Failed to create commit")
                    return

            if commit_success:
                if auto_confirm:
                    # Check if we're on main/master branch
                    current_branch = self.git_manager.get_current_branch()
                    default_branch = self.git_manager.get_local_base_branch_name()
                    if current_branch and default_branch and current_branch == default_branch:
                        components.show_section("Auto-confirm: Skipping push (on main branch)")
                    else:
                        components.show_section("Auto-confirm: Pushing commit")
                        get_push_command()(auto_confirm)
                elif safe_confirm("Push this commit now?", default=True):
                    get_push_command()(auto_confirm)

        except RuntimeError as e:
            components.show_error(f"A critical Git operation failed: {str(e)}")
        except Exception as e:
            components.show_error(f"An unexpected error occurred: {str(e)}")


# This is the old command function, to be replaced by calls to CommitFeature().execute_commit()
# def commit_command(group: bool = True) -> None:
#    feature = CommitFeature()
#    feature.execute_commit(group=group)

# The generate_commit_message function is now generate_commit_message_llm to avoid naming conflicts if we move it into the class
# and it should be called by an instance method if it uses self, or passed instance of git_manager etc.
# For now, it's a module-level helper using the module-level git_manager instance for its sub-calls (analyze_changes -> get_file_diff_staged).
