"""Pull request creation feature for GitWise."""

import subprocess
import re
from typing import List, Dict, Tuple, Optional
from git import Repo, Commit
from gitwise.gitutils import get_commit_history, get_current_branch, get_base_branch
from gitwise.llm import generate_pr_description, generate_pr_title
from gitwise.features.pr_enhancements import enhance_pr_description

def get_commits_since_last_pr(repo: Repo, base_branch: str) -> List[Commit]:
    """Get commits since the last push to the remote branch."""
    current_branch = get_current_branch()
    
    try:
        # Get the remote tracking branch
        remote_branch = f"origin/{current_branch}"
        
        # Check if remote branch exists
        try:
            repo.git.rev_parse(f"{remote_branch}")
            # If we get here, remote branch exists, get commits since last push
            commits = list(repo.iter_commits(f"{remote_branch}..{current_branch}"))
        except:
            # Remote branch doesn't exist, get all commits since base branch
            commits = list(repo.iter_commits(f"{base_branch}..{current_branch}"))
        
        if not commits:
            # If no commits found, try getting commits since base branch
            commits = list(repo.iter_commits(f"{base_branch}..{current_branch}"))
        
        return commits
    except Exception as e:
        # If any error occurs, fall back to base branch
        return list(repo.iter_commits(f"{base_branch}..{current_branch}"))

def generate_pr_description(commits: List[Commit]) -> str:
    """Generate a structured PR description from commits."""
    if not commits:
        return "No changes to describe."

    # Group commits by type
    changes = {
        "Features": [],
        "Fixes": [],
        "Improvements": [],
        "Other": []
    }

    for commit in commits:
        msg = commit.message.strip()
        # Remove conventional commit prefix if present
        msg = re.sub(r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([^)]+\))?:\s*', '', msg)
        # Take first line only
        msg = msg.split('\n')[0]

        # Categorize the commit
        if any(x in commit.message.lower() for x in ["feat", "feature", "add", "new"]):
            changes["Features"].append(msg)
        elif any(x in commit.message.lower() for x in ["fix", "bug", "issue"]):
            changes["Fixes"].append(msg)
        elif any(x in commit.message.lower() for x in ["improve", "enhance", "update", "refactor"]):
            changes["Improvements"].append(msg)
        else:
            changes["Other"].append(msg)

    # Build the description
    description = []
    
    # Summary section
    total_changes = sum(len(msgs) for msgs in changes.values())
    description.append(f"## Summary\nThis PR includes {total_changes} changes:\n")
    
    # Add counts for each category
    for category, msgs in changes.items():
        if msgs:
            description.append(f"- {len(msgs)} {category.lower()}")
    description.append("")

    # Changes section
    for category, msgs in changes.items():
        if msgs:
            description.append(f"## {category}")
            for msg in msgs:
                description.append(f"- {msg}")
            description.append("")

    # Add a note about testing
    description.append("## Testing\nPlease verify the changes work as expected.")

    return "\n".join(description)

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

        pr_description = generate_pr_description(commits)
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

def validate_branch_name(branch: str) -> bool:
    """Validate branch name against naming conventions."""
    # Protected branches
    protected = {"main", "master", "develop"}
    if branch in protected:
        return False
    
    # Branch name pattern
    pattern = r"^(feature|fix|docs|chore|refactor|test|style|perf|ci|build|revert)/[a-z0-9-]+$"
    return bool(re.match(pattern, branch))

def create_pull_request(title: str, body: str, base: str, head: str, draft: bool = False) -> Dict:
    """Create a pull request using GitHub API."""
    # Implementation depends on your GitHub API integration
    pass 