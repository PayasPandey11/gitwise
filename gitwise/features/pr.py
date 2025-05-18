"""Pull request creation feature for GitWise."""

import subprocess
import re
import json
from typing import List, Dict, Tuple, Optional
from git import Repo, Commit
from gitwise.gitutils import get_commit_history, get_current_branch, get_base_branch
from gitwise.llm import generate_pr_title, get_llm_response
from gitwise.features.pr_enhancements import enhance_pr_description, get_pr_labels
from gitwise.prompts import PR_DESCRIPTION_PROMPT
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich import print as rprint
from gitwise.core import git
from gitwise.ui import components
import os
import tempfile
import typer

console = Console()

def get_commits_since_last_pr(repo: Repo, base_branch: str = "main") -> List[Commit]:
    """Get commits since last PR was created.
    
    Args:
        repo: Git repository
        base_branch: Base branch to compare against
        
    Returns:
        List of commits since last PR
    """
    current_branch = repo.active_branch.name
    remote_branch = f"origin/{current_branch}"
    
    try:
        # First try to get commits between remote and local
        repo.git.fetch("origin", current_branch)
        commits = list(repo.iter_commits(f"{remote_branch}..HEAD"))
        
        # If no commits found, try getting commits since base branch
        if not commits:
            commits = list(repo.iter_commits(f"{base_branch}..HEAD"))
            
        return commits
    except Exception as e:
        # If any error occurs, fall back to base branch
        console.print(f"[yellow]Warning: {str(e)}[/yellow]")
        console.print("[yellow]Falling back to comparing with base branch...[/yellow]")
        return list(repo.iter_commits(f"{base_branch}..HEAD"))

def create_pr(repo: Repo, title: str, description: str, labels: List[str] = None) -> str:
    """Create a pull request.
    
    Args:
        repo: Git repository
        title: PR title
        description: PR description
        labels: Optional list of labels to add
        
    Returns:
        URL of the created PR
    """
    # This is a placeholder - in a real implementation, you would use the GitHub API
    # to create the PR. For now, we'll just return a mock URL.
    return f"https://github.com/owner/repo/pull/123"

def create_pull_request(repo: Repo, base_branch: str = "main", labels: List[str] = None) -> Optional[str]:
    """Create a pull request for the current branch.
    
    Args:
        repo: Git repository
        base_branch: Base branch to create PR against
        labels: Optional list of labels to add to the PR
        
    Returns:
        URL of the created PR if successful, None otherwise
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Get commits since last PR
            task = progress.add_task("Analyzing commits...", total=None)
            commits = get_commits_since_last_pr(repo, base_branch)
            progress.update(task, completed=True)
            
            if not commits:
                console.print("[red]No new commits to create PR for.[/red]")
                console.print("[yellow]This might happen if:")
                console.print("1. All commits have already been pushed and included in a PR")
                console.print("2. You haven't made any commits yet")
                console.print("3. You're on the base branch (main/master)[/yellow]")
                return None
                
            # Generate PR title
            task = progress.add_task("Generating PR title...", total=None)
            title = generate_pr_title(commits)
            progress.update(task, completed=True)
            
            # Prepare commit information for LLM
            commit_info = []
            for commit in commits:
                message = commit.message.split('\n')[0]
                commit_info.append(f"Commit: {commit.hexsha[:7]}\nMessage: {message}\nAuthor: {commit.author.name}\nDate: {commit.committed_datetime}\n")
            
            # Generate PR description
            components.show_section("Generating PR Description")
            try:
                with components.show_spinner("Analyzing changes...") as progress:
                    description = generate_pr_description(commits)
                    if not description:
                        raise ValueError("Failed to generate PR description")
            except Exception as e:
                components.show_error(f"Could not generate PR description: {str(e)}")
                components.show_prompt(
                    "Would you like to try again?",
                    options=["Yes", "No"],
                    default="No"
                )
                if not typer.confirm("", default=False):
                    return None
                # Try one more time
                try:
                    with components.show_spinner("Retrying...") as progress:
                        description = generate_pr_description(commits)
                        if not description:
                            components.show_error("Failed to generate PR description again")
                            return None
                except Exception as e:
                    components.show_error(f"Failed to generate PR description: {str(e)}")
                    return None

            # Show the generated description
            components.show_section("Suggested PR Description")
            components.console.print(description)

            if not skip_prompts:
                # Ask about creating PR
                components.show_prompt(
                    "Would you like to create this pull request?",
                    options=["Yes", "Edit description", "No"],
                    default="Yes"
                )
                choice = typer.prompt("", type=int, default=1)

                if choice == 3:  # No
                    components.show_warning("PR creation cancelled")
                    return None

                if choice == 2:  # Edit
                    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
                        tf.write(description)
                        tf.flush()
                        editor = os.environ.get("EDITOR", "vi")
                        # os.system(f'{editor} {tf.name}')
                        subprocess.run([editor, tf.name], check=True)
                        tf.seek(0)
                        description = tf.read().strip()
                    os.unlink(tf.name)
                    
                    if not description.strip():
                        components.show_error("PR description cannot be empty")
                        return None
                        
                    components.show_section("Edited PR Description")
                    components.console.print(description)

                    components.show_prompt(
                        "Proceed with PR creation?",
                        options=["Yes", "No"],
                        default="Yes"
                    )
                    if not typer.confirm("", default=True):
                        components.show_warning("PR creation cancelled")
                        return None

            # Create the PR
            components.show_section("Creating Pull Request")
            with components.show_spinner("Creating PR...") as progress:
                try:
                    # Use GitHub CLI if available
                    result = subprocess.run(
                        ["gh", "pr", "create",
                         "--title", title or f"feat: {commits[0]['message']}",
                         "--body", description,
                         "--base", base_branch,
                         *(["--draft"] if draft else [])],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        components.show_success("Pull request created successfully")
                        components.console.print(result.stdout)
                        return result.stdout.strip()
                    else:
                        components.show_error("Failed to create pull request")
                        components.console.print(result.stderr)
                        return None
                except FileNotFoundError:
                    components.show_error("GitHub CLI (gh) not found. Please install it to create PRs.")
                    components.console.print("\n[dim]You can install it from: https://cli.github.com/[/dim]")
                    return None

    except Exception as e:
        components.show_error(str(e))
        return None

def validate_branch_name(branch: str) -> bool:
    """Validate branch name against naming conventions."""
    # Protected branches
    protected = {"main", "master", "develop"}
    if branch in protected:
        return False
    
    # Branch name pattern
    pattern = r"^(feature|fix|docs|chore|refactor|test|style|perf|ci|build|revert)/[a-z0-9-]+$"
    return bool(re.match(pattern, branch))

def get_commits_since_last_pr(repo, base_branch: str) -> List[Dict]:
    """Get commits that haven't been included in a PR yet."""
    try:
        # Get commits between base branch and current branch
        result = subprocess.run(
            ["git", "log", f"{base_branch}..HEAD", "--pretty=format:%H|%s|%an"],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            return []
            
        commits = []
        for line in result.stdout.strip().split('\n'):
            hash_, message, author = line.split('|')
            commits.append({
                'hash': hash_,
                'message': message,
                'author': author
            })
            
        return commits
    except Exception as e:
        components.show_error(f"Failed to get commits: {str(e)}")
        return []

def pr_command(
    use_labels: bool = False,
    use_checklist: bool = False,
    skip_general_checklist: bool = False,
    title: Optional[str] = None,
    base: Optional[str] = None,
    draft: bool = False,
    skip_prompts: bool = False
) -> None:
    """Create a pull request with AI-generated description.
    
    Args:
        use_labels: Whether to add labels to the PR
        use_checklist: Whether to add a checklist to the PR description
        skip_general_checklist: Whether to skip general checklist items
        title: Custom title for the PR
        base: Base branch for the PR
        draft: Whether to create a draft PR
        skip_prompts: Whether to skip interactive prompts (used when called from push)
    """
    try:
        # Get current branch
        current_branch = git.get_current_branch()
        if not current_branch:
            components.show_error("Not on any branch")
            return

        # Get base branch
        base_branch = base or "main"
        
        # Get commits since last PR
        components.show_section("Analyzing Changes")
        with components.show_spinner("Checking for commits...") as progress:
            commits = get_commits_since_last_pr(None, base_branch)
            if not commits:
                components.show_warning("No commits to create PR for")
                return

        # Generate PR title using LLM
        pr_generated_title = title
        if not pr_generated_title:
            with components.show_spinner("Generating PR title..."):
                pr_generated_title = generate_pr_title(commits)

        # Show commits that will be included
        components.show_section("Commits to Include")
        for commit in commits:
            components.console.print(f"[bold cyan]{commit['hash'][:7]}[/bold cyan] {commit['message']}")

        # Generate PR description
        components.show_section("Generating PR Description")
        pr_body = ""
        try:
            with components.show_spinner("Analyzing changes...") as progress:
                # Use the local pr.py generate_pr_description, which calls get_repository_info
                pr_body = generate_pr_description(commits) 
                if not pr_body:
                    raise ValueError("Failed to generate PR description")
        except Exception as e:
            components.show_error(f"Could not generate PR description: {str(e)}")
            components.show_prompt(
                "Would you like to try again?",
                options=["Yes", "No"],
                default="No"
            )
            if not typer.confirm("", default=False):
                return
            # Try one more time
            try:
                with components.show_spinner("Retrying...") as progress:
                    pr_body = generate_pr_description(commits)
                    if not pr_body:
                        components.show_error("Failed to generate PR description again")
                        return
            except Exception as e:
                components.show_error(f"Failed to generate PR description: {str(e)}")
                return

        # Enhance PR description with checklist if requested
        # Labels will be handled separately with gh command
        final_labels = []
        if use_labels:
            with components.show_spinner("Generating labels..."):
                final_labels = get_pr_labels(commits) # Get labels based on commits
        
        if use_checklist:
            with components.show_spinner("Generating checklist..."):
                # Pass base_branch to enhance_pr_description for accurate checklist generation
                pr_body, _ = enhance_pr_description(commits, pr_body, use_labels=False, use_checklist=True, skip_general_checklist=skip_general_checklist, base_branch_for_checklist=base_branch)

        # Show the generated/enhanced description
        components.show_section("Suggested PR Description")
        components.console.print(f"[bold]Title:[/bold] {pr_generated_title}")
        if final_labels:
            components.console.print(f"[bold]Labels:[/bold] {', '.join(final_labels)}")
        components.console.print(f"[bold]Body:[/bold]\n{pr_body}")

        if not skip_prompts:
            # Ask about creating PR
            components.show_prompt(
                "Would you like to create this pull request?",
                options=["Yes", "Edit description", "No"],
                default="Yes"
            )
            choice = typer.prompt("", type=int, default=1)

            if choice == 3:  # No
                components.show_warning("PR creation cancelled")
                return

            if choice == 2:  # Edit
                with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
                    tf.write(pr_body) # Edit the potentially enhanced body
                    tf.flush()
                    editor = os.environ.get("EDITOR", "vi")
                    # os.system(f'{editor} {tf.name}')
                    subprocess.run([editor, tf.name], check=True)
                    tf.seek(0)
                    pr_body = tf.read().strip()
                os.unlink(tf.name)
                
                if not pr_body.strip():
                    components.show_error("PR description cannot be empty")
                    return
                    
                components.show_section("Edited PR Description")
                components.console.print(pr_body)

                components.show_prompt(
                    "Proceed with PR creation?",
                    options=["Yes", "No"],
                    default="Yes"
                )
                if not typer.confirm("", default=True):
                    components.show_warning("PR creation cancelled")
                    return

            # Create the PR
            components.show_section("Creating Pull Request")
            with components.show_spinner("Creating PR...") as progress:
                try:
                    # Use GitHub CLI if available
                    cmd = [
                        "gh", "pr", "create",
                        "--title", pr_generated_title or f"feat: {commits[0]['message']}", # Fallback if title is empty
                        "--body", pr_body,
                        "--base", base_branch
                    ]
                    if draft:
                        cmd.append("--draft")
                    for label in final_labels:
                        cmd.extend(["--label", label])
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        components.show_success("Pull request created successfully")
                        components.console.print(result.stdout)
                    else:
                        components.show_error("Failed to create pull request")
                        components.console.print(result.stderr)
                        return
                except FileNotFoundError:
                    components.show_error("GitHub CLI (gh) not found. Please install it to create PRs.")
                    components.console.print("\n[dim]You can install it from: https://cli.github.com/[/dim]")
                    return

    except Exception as e:
        components.show_error(str(e))

def create_pull_request(title: str, body: str, base: str, head: str, draft: bool = False) -> Dict:
    """Create a pull request using GitHub API."""
    # Implementation depends on your GitHub API integration
    pass

def generate_pr_description(commits: List[Dict]) -> str:
    """Generate a PR description from commits.
    
    Args:
        commits: List of commit dictionaries.
        
    Returns:
        Formatted PR description string.
    """
    if not commits:
        return ""
        
    # Prepare commit messages for LLM
    commit_text = "\n".join([
        f"- {commit['message']} ({commit['author']})"
        for commit in commits
    ])
    
    # Get repository info
    repo_info = get_repository_info()
    repo_name = repo_info.get("name", "the repository")
    repo_url = repo_info.get("url", "")
    
    # Generate PR description using LLM
    messages = [
        {
            "role": "system",
            "content": f"""You are a technical writer creating a pull request description for {repo_name}.
            Create clear, concise, and user-friendly PR descriptions that:
            1. Summarize the changes and their purpose
            2. Group related changes together
            3. Use clear, non-technical language where possible
            4. Include any breaking changes or migration steps
            5. Mention contributors if there are significant changes
            
            Format the description in markdown with appropriate sections."""
        },
        {
            "role": "user",
            "content": f"""Create a PR description for the following commits:

            {commit_text}"""
        }
    ]
    
    try:
        description = get_llm_response(messages)
        if not description:
            raise ValueError("Empty PR description generated")
        return description
    except Exception as e:
        components.show_error(f"Could not generate PR description: {str(e)}")
        return ""

def get_repository_info() -> Dict[str, str]:
    """Get repository information.
    
    Returns:
        Dictionary with repository information.
    """
    info = {}
    
    # Get repository URL
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True
    )
    info["url"] = result.stdout.strip()
    
    # Get repository name
    if info["url"]:
        # Extract name from URL
        match = re.search(r"[:/]([^/]+/[^/]+?)(?:\.git)?$", info["url"])
        if match:
            info["name"] = match.group(1)
    
    return info 