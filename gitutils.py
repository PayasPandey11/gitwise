import subprocess

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