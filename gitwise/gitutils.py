import subprocess
from typing import List, Dict

def get_current_branch() -> str:
    """Get the name of the current branch."""
    try:
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("Error getting current branch name.")

def get_staged_diff() -> str:
    """Return the staged git diff as a string. Raises RuntimeError on failure."""
    try:
        result = subprocess.run([
            "git", "diff", "--cached"
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("Error running git diff --cached.")

def run_git_commit(message: str) -> None:
    """Run git commit with the given message. Raises RuntimeError on failure."""
    try:
        subprocess.run(["git", "commit", "-m", message], check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("Error running git commit.")

def run_git_push(target_branch: str = None) -> None:
    """Run git push command.
    
    Args:
        target_branch: If provided, push to this branch. Otherwise, push to the current branch.
    """
    try:
        current_branch = get_current_branch()
        if target_branch:
            push_spec = f"{current_branch}:{target_branch}"
        else:
            push_spec = current_branch
            
        result = subprocess.run(
            ["git", "push", "origin", push_spec],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to push changes: {e.stderr}")

def get_commit_history() -> List[Dict[str, str]]:
    """Get commit history of commits that haven't been pushed to remote yet.
    
    Returns:
        List of dictionaries containing commit hash, author, date, and message.
    """
    try:
        # Get the current branch
        current_branch = get_current_branch()
        
        # Get commits that are in the current branch but not in the remote tracking branch
        result = subprocess.run(
            ["git", "log", f"origin/{current_branch}..HEAD", "--pretty=format:%H|%an|%ad|%s"],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            hash_, author, date, message = line.split('|', 3)
            commits.append({
                'hash': hash_,
                'author': author,
                'date': date,
                'message': message
            })
        
        return commits
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error getting commit history: {e.stderr}")

def get_changed_files() -> List[str]:
    """Get list of changed files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True
    )
    return [f for f in result.stdout.splitlines() if f] 