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
    
    # Get the remote tracking branch
    remote_branch = f"origin/{current_branch}"
    
    # Check if remote branch exists
    try:
        # Try to get the remote branch
        repo.git.rev_parse(f"{remote_branch}")
        # If we get here, remote branch exists, get commits since last push
        return list(repo.iter_commits(f"{remote_branch}..{current_branch}"))
    except:
        # Remote branch doesn't exist, get all commits since base branch
        return list(repo.iter_commits(f"{base_branch}..{current_branch}"))

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
        
        # Validate branch name
        current_branch = get_current_branch()
        if not validate_branch_name(current_branch):
            raise ValueError(f"Invalid branch name: {current_branch}")
        
        # Get commits since last PR
        commits = get_commits_since_last_pr(repo, base_branch)
        if not commits:
            raise ValueError("No new commits to create PR for")
        
        # Generate PR title and description
        pr_title = title or generate_pr_title(commits)
        pr_description = generate_pr_description(commits)
        
        # Enhance PR description with labels and checklist if requested
        enhanced_description, labels = enhance_pr_description(
            commits, 
            pr_description,
            use_labels=use_labels,
            use_checklist=use_checklist,
            skip_general_checklist=skip_general_checklist
        )
        
        # Show preview
        print("\n=== PR Preview ===")
        print(f"Title: {pr_title}")
        print("\nDescription:")
        print(enhanced_description)
        if use_labels:
            print("\nLabels to be applied:", ", ".join(labels) if labels else "None")
        
        # Confirm PR creation
        if input("\nCreate pull request? (y/N) ").lower() != 'y':
            print("PR creation cancelled.")
            return

        # Create PR using GitHub CLI
        try:
            # Create PR with title and description
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
                
                # Add labels if enabled and available
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