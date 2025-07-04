"""Feature logic for the 'commit' command, including AI-assisted message generation and grouping."""

import os
import shlex
import subprocess
import tempfile
import json
from typing import Callable, Dict, List, Optional, Any

import typer

from gitwise.config import ConfigError, get_llm_backend, load_config
from gitwise.core.git_manager import GitManager
from gitwise.exceptions import SecurityError
from gitwise.features.context import ContextFeature
from gitwise.llm.router import get_llm_response
from gitwise.prompts import PROMPT_COMMIT_MESSAGE, PROMPT_COMMIT_GROUPING
from gitwise.ui import components

# Initialize GitManager
git_manager = GitManager()

# Allowed editors for security
ALLOWED_EDITORS = {
    'vi', 'vim', 'nvim', 'nano', 'emacs', 'micro', 'code', 'subl', 
    'atom', 'gedit', 'kate', 'notepad', 'notepad++', 'TextEdit'
}


def _get_safe_editor() -> str:
    """Get a safe editor command, validating against known editors."""
    editor = os.environ.get("EDITOR", "vi")
    
    # Extract just the command name (remove path and arguments)
    editor_cmd = os.path.basename(editor.split()[0])
    
    if editor_cmd not in ALLOWED_EDITORS:
        raise SecurityError(
            f"Editor '{editor}' is not allowed for security reasons. "
            f"Allowed editors: {', '.join(sorted(ALLOWED_EDITORS))}"
        )
    
    return editor


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
    Analyze changed files using LLM to find semantic patterns for grouping.
    Falls back to simple pattern matching if LLM analysis fails.
    Returns a list of suggested commit groups.
    """
    # Try LLM-based analysis first
    try:
        # Get staged diff content for each file
        staged_changes = ""
        
        for file_path in changed_files:
            try:
                # Get diff for individual file
                file_diff = git_manager.get_file_diff_staged(file_path)
                if file_diff:
                    staged_changes += f"\n=== FILE: {file_path} ===\n"
                    staged_changes += file_diff
                    staged_changes += "\n" + "="*50 + "\n"
                else:
                    # Handle new files or files with no diff
                    staged_changes += f"\n=== FILE: {file_path} (new file or no changes) ===\n"
                    staged_changes += f"File path: {file_path}\n"
                    staged_changes += "="*50 + "\n"
            except Exception:
                # If we can't get diff for a file, just include the path
                staged_changes += f"\n=== FILE: {file_path} (diff unavailable) ===\n"
                staged_changes += f"File path: {file_path}\n"
                staged_changes += "="*50 + "\n"
        
        if not staged_changes.strip():
            raise Exception("No staged changes content available")
        
        # Call LLM with the grouping prompt
        prompt = PROMPT_COMMIT_GROUPING.replace("{{staged_changes}}", staged_changes)
        llm_response = get_llm_response(prompt)
        
        # Parse JSON response
        try:
            response_data = json.loads(llm_response.strip())
            
            # Validate response structure
            if "groups" not in response_data or "recommendation" not in response_data:
                raise ValueError("Invalid response structure")
            
            # Convert LLM response to our expected format
            suggestions = []
            for group in response_data["groups"]:
                if len(group.get("files", [])) >= 1:  # At least 1 file per group
                    suggestions.append({
                        "type": "llm_semantic",
                        "name": group.get("name", "LLM Suggested Group"),
                        "description": group.get("description", ""),
                        "files": group.get("files", []),
                        "suggested_commit_message": group.get("suggested_commit_message", ""),
                        "reasoning": group.get("reasoning", "")
                    })
            
            # Only return LLM suggestions if we have meaningful groups and recommendation is "multiple"
            if (suggestions and len(suggestions) >= 2 and 
                response_data.get("recommendation") == "multiple"):
                components.console.print("[dim cyan]✓ LLM analysis completed - semantic grouping suggested[/dim cyan]")
                return suggestions
            elif suggestions and len(suggestions) == 1:
                # Single group suggested by LLM - don't split
                components.console.print("[dim cyan]✓ LLM analysis completed - single commit recommended[/dim cyan]")
                return []
            else:
                # Fall back to pattern matching
                components.console.print("[dim yellow]⚠ LLM suggested no meaningful groups - using pattern matching[/dim yellow]")
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            components.console.print(f"[dim yellow]⚠ LLM response parsing failed: {e} - using pattern matching[/dim yellow]")
            
    except Exception as e:
        components.console.print(f"[dim yellow]⚠ LLM analysis failed: {e} - using pattern matching[/dim yellow]")
    
    # Fallback to original pattern-matching logic
    return _analyze_changes_pattern_matching(changed_files)


def _analyze_changes_pattern_matching(changed_files: List[str]) -> List[Dict[str, Any]]:
    """
    Original pattern-matching logic for grouping files.
    Used as fallback when LLM analysis fails.
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


def generate_commit_message(diff: str, guidance: str = "", force_style: str = None) -> str:
    """Generate a commit message using LLM prompt with context from ContextFeature."""
    # Get context for the current branch
    context_feature = ContextFeature()
    # First try to parse branch name for context if we don't have it already
    context_feature.parse_branch_context()
    # Then get context as a formatted string for the prompt
    context_string = context_feature.get_context_for_ai_prompt()
    
    # Prompt user for context if needed
    if not context_string:
        context_string = context_feature.prompt_for_context_if_needed() or ""
    
    # Show visual indication that context is being used
    if context_string:
        # Trim long contexts for display
        display_context = context_string
        if len(display_context) > 100:
            display_context = display_context[:97] + "..."
        components.show_section("Context Used for Commit Message")
        components.console.print(f"[dim cyan]{display_context}[/dim cyan]")
        
        # Add context to guidance
        if guidance:
            guidance = f"{context_string} {guidance}"
        else:
            guidance = context_string
    
    # Get list of staged files to include in the prompt
    staged_files = git_manager.get_staged_files()
    file_info = "\nFiles changed:\n"
    
    for status, file_path in staged_files:
        # Determine file type
        file_type = "Documentation" if file_path.endswith(('.md', '.rst', '.txt')) else "Code"
        if "test" in file_path.lower():
            file_type = "Test"
        elif "docs/" in file_path.lower():
            file_type = "Documentation"
        
        file_info += f"- {status} {file_path} ({file_type})\n"
    
    # Add file information to guidance
    if guidance:
        guidance = f"{guidance}\n\n{file_info}"
    else:
        guidance = file_info
    
    # Use custom commit rules if configured
    try:
        from gitwise.features.commit_rules import CommitRulesFeature
        rules_feature = CommitRulesFeature()
        
        # Determine which style to use (force_style overrides config)
        if force_style:
            use_style = force_style
        else:
            use_style = rules_feature.get_active_style()
        
        if use_style == "custom":
            # Generate custom prompt
            prompt = rules_feature.generate_prompt(diff, guidance)
        else:
            # Use conventional commit prompt
            prompt = PROMPT_COMMIT_MESSAGE.replace("{{diff}}", diff).replace(
                "{{guidance}}", guidance
            )
    except Exception:
        # Fallback to conventional if there's any issue with custom rules
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

    def execute_commit(self, group: bool = True, auto_confirm: bool = False, force_style: str = None) -> None:
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
            
            # Enhanced backend display with provider detection
            if backend == "online":
                try:
                    from gitwise.llm.providers import detect_provider_from_config
                    config = load_config()
                    provider = detect_provider_from_config(config)
                    
                    if provider == "google":
                        backend_display = "Online (Google Gemini)"
                    elif provider == "openai":
                        backend_display = "Online (OpenAI)"
                    elif provider == "anthropic":
                        backend_display = "Online (Anthropic Claude)"
                    elif provider == "openrouter":
                        backend_display = "Online (OpenRouter)"
                    else:
                        backend_display = "Online (Cloud provider)"
                except:
                    backend_display = "Online (Cloud provider)"
            else:
                backend_display = {
                    "ollama": "Ollama (local server)",
                }.get(backend, backend)
                
            components.show_section(f"[AI] LLM Backend: {backend_display}")


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
                        components.console.print(f"\n[bold]Group {i}: {group_item['name']}[/bold]")
                        components.console.print(
                            f"Files: {', '.join(group_item['files'])}"
                        )
                        
                        # Show different info based on group type
                        if group_item['type'] == 'llm_semantic':
                            if group_item.get('description'):
                                components.console.print(f"[dim]Description: {group_item['description']}[/dim]")
                            if group_item.get('suggested_commit_message'):
                                components.console.print(f"Suggested commit: [cyan]{group_item['suggested_commit_message']}[/cyan]")
                            if group_item.get('reasoning'):
                                components.console.print(f"[dim]Reasoning: {group_item['reasoning']}[/dim]")
                        else:
                            # Fallback display for pattern-matching groups
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
                                
                                # Use LLM-suggested commit message if available, otherwise generate one
                                if (group_item['type'] == 'llm_semantic' and 
                                    group_item.get('suggested_commit_message')):
                                    commit_message_for_group = group_item['suggested_commit_message']
                                    components.console.print(f"[dim cyan]Using LLM-suggested commit message[/dim cyan]")
                                else:
                                    # Generate LLM commit message for the group
                                    group_diff = self.git_manager.get_staged_diff()
                                    if group_diff:
                                        guidance = f"This commit affects {len(group_item['files'])} files in the {group_item['name']} {group_item['type']}."
                                        commit_message_for_group = generate_commit_message(group_diff, guidance, force_style)
                                    else:
                                        # Fallback to simple description if no diff
                                        commit_message_for_group = f"feat: add {len(group_item['files'])} files to {group_item['name']} {group_item['type']}"
                                
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
                message = generate_commit_message(diff_for_message_generation, "", force_style)

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
                try:
                    editor = _get_safe_editor()
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
                        force_style
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
