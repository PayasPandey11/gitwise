"""Pull request creation feature for GitWise."""

import subprocess
import re
import json
from typing import List, Dict, Tuple, Optional
from git import Repo, Commit
from gitwise.gitutils import get_commit_history, get_current_branch, get_base_branch
from gitwise.llm import generate_pr_description as llm_generate_pr_description, generate_pr_title
from gitwise.features.pr_enhancements import enhance_pr_description
from gitwise.prompts import PR_DESCRIPTION_PROMPT
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich import print as rprint

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
        
        # Generate PR description using LLM
        task = progress.add_task("Generating PR description...", total=None)
        prompt = PR_DESCRIPTION_PROMPT.format(
            commits="\n".join(commit_info),
            base_branch=base_branch,
            current_branch=repo.active_branch.name
        )
        description = generate_pr_description(prompt)
        progress.update(task, completed=True)
        
        # Show preview
        console.print("\n[bold]PR Preview:[/bold]")
        console.print(Panel(f"[bold]{title}[/bold]\n\n{description}", title="Pull Request", border_style="blue"))
        
        if not Confirm.ask("Create this pull request?"):
            return None
            
        # Create PR
        task = progress.add_task("Creating pull request...", total=None)
        pr_url = create_pr(repo, title, description, labels)
        progress.update(task, completed=True)
        
        return pr_url

def validate_branch_name(branch: str) -> bool:
    """Validate branch name against naming conventions."""
    # Protected branches
    protected = {"main", "master", "develop"}
    if branch in protected:
        return False
    
    # Branch name pattern
    pattern = r"^(feature|fix|docs|chore|refactor|test|style|perf|ci|build|revert)/[a-z0-9-]+$"
    return bool(re.match(pattern, branch))

def pr_command(
    use_labels: bool = False,
    use_checklist: bool = False,
    skip_general_checklist: bool = False,
    title: Optional[str] = None,
    base: Optional[str] = None,
    draft: bool = False
) -> None:
    """Create a pull request with AI-generated title and description.
    
    Args:
        use_labels: Add labels to the PR (default: False).
        use_checklist: Add checklist to the PR description (default: False).
        skip_general_checklist: Skip general checklist items (default: False).
        title: Custom title for the PR (optional).
        base: Base branch for the PR (optional).
        draft: Create a draft PR (default: False).
    """
    try:
        repo = Repo(".")
        base_branch = base or get_base_branch()
        current_branch = get_current_branch()
        if not validate_branch_name(current_branch):
            raise ValueError(f"Invalid branch name: {current_branch}")

        # Get only new commits (not in remote or base)
        commits = get_commits_since_last_pr(repo, base_branch)
        if not commits:
            print("\n[bold yellow]No new commits to create PR for.[/bold yellow]")
            return

        # Generate PR title and description
        if title:
            pr_title = title
        else:
            # Generate a concise title from the most significant commit
            if commits:
                main_commit = commits[0]  # Most recent commit
                msg = main_commit.message.strip()
                # Remove conventional commit prefix if present
                msg = re.sub(r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([^)]+\))?:\s*', '', msg)
                # Take first line and limit length
                pr_title = msg.split('\n')[0][:100]
            else:
                pr_title = "Update"

        # Generate PR description using LLM
        pr_description = generate_pr_description(commits)
        
        # Enhance the description with labels and checklist if requested
        enhanced_description, labels = enhance_pr_description(
            commits,
            pr_description,
            use_labels=use_labels,
            use_checklist=use_checklist,
            skip_general_checklist=skip_general_checklist
        )

        # Simple, clean preview
        print("\n=== Pull Request Preview ===")
        print(f"[Title]\n{pr_title}\n")
        print(f"[Description]\n{enhanced_description.strip()}\n")
        if use_labels and labels:
            print(f"[Labels] {', '.join(labels)}\n")

        # Confirm PR creation
        if input("Create pull request? (y/N) ").lower() != 'y':
            print("PR creation cancelled.")
            return

        # Create PR using GitHub CLI
        try:
            result = subprocess.run(
                ["gh", "pr", "create",
                 "--title", pr_title,
                 "--body", enhanced_description],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                print(f"\n✅ Pull request created: {pr_url}")
                if use_labels and labels:
                    subprocess.run(
                        ["gh", "pr", "edit", pr_url, "--add-label", ",".join(labels)],
                        capture_output=True
                    )
                    print(f"Added labels: {', '.join(labels)}")
            else:
                print("\n❌ Failed to create pull request.")
                print("Error:", result.stderr)
                print("\nYou can create the PR manually with:")
                print(f"gh pr create --title '{pr_title}' --body '{enhanced_description}'")
        except FileNotFoundError:
            print("\n❌ GitHub CLI (gh) not found.")
            print("Please install GitHub CLI or create the PR manually with:")
            print(f"Title: {pr_title}")
            print(f"\nDescription:\n{enhanced_description}")
            if use_labels and labels:
                print(f"\nLabels: {', '.join(labels)}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please try again or create the PR manually.")

def create_pull_request(title: str, body: str, base: str, head: str, draft: bool = False) -> Dict:
    """Create a pull request using GitHub API."""
    # Implementation depends on your GitHub API integration
    pass 