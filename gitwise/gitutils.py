import subprocess
from typing import List, Dict, Tuple, Optional
from git import Repo

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
    """Get commit history for unpushed commits.
    
    Returns:
        List of dictionaries containing commit hash, message, and author.
    """
    try:
        # Get the current branch
        current_branch = get_current_branch()
        
        # Get the remote tracking branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # No remote tracking branch found, compare with origin/main
            remote_branch = "origin/main"
        else:
            remote_branch = result.stdout.strip()
        
        # Get commits between remote branch and HEAD
        result = subprocess.run(
            ["git", "log", f"{remote_branch}..HEAD", "--pretty=format:%H|%s|%an"],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            return []
            
        commits = []
        for line in result.stdout.strip().split('\n'):
            hash, message, author = line.split('|')
            commits.append({
                'hash': hash,
                'message': message,
                'author': author
            })
            
        return commits
    except Exception as e:
        raise RuntimeError(f"Failed to get commit history: {str(e)}")

def get_changed_files() -> List[str]:
    """Get list of changed files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True
    )
    return [f for f in result.stdout.splitlines() if f]

def get_base_branch() -> str:
    """Get the base branch for the current repository.
    
    Returns:
        str: The name of the base branch (main or master)
    """
    try:
        # Try to get the default branch from git config
        result = subprocess.run(
            ["git", "config", "--get", "init.defaultBranch"],
            capture_output=True,
            text=True,
            check=True
        )
        default_branch = result.stdout.strip()
        if default_branch:
            return default_branch
    except subprocess.CalledProcessError:
        pass

    # If no default branch is set, check for main or master
    repo = Repo(".")
    for branch in ["main", "master"]:
        try:
            repo.heads[branch]
            return branch
        except (IndexError, KeyError):
            continue

    # If neither exists, return main as default
    return "main"

def get_staged_files() -> List[Tuple[str, str]]:
    """Get list of staged files with their status.
    
    Returns:
        List of tuples containing (status, file_path)
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-status"],
            capture_output=True,
            text=True,
            check=True
        )
        files = []
        for line in result.stdout.splitlines():
            if line:
                status, file_path = line.split('\t')
                files.append((status, file_path))
        return files
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error getting staged files: {e.stderr}")

def get_unstaged_files() -> List[Tuple[str, str]]:
    """Get list of unstaged files with their status.
    
    Returns:
        List of tuples containing (status, file_path)
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status"],
            capture_output=True,
            text=True,
            check=True
        )
        files = []
        for line in result.stdout.splitlines():
            if line:
                status, file_path = line.split('\t')
                files.append((status, file_path))
        return files
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error getting unstaged files: {e.stderr}") 