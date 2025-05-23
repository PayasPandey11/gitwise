"""Core git operations for GitWise."""

import subprocess
from typing import List, Tuple, Optional

def get_staged_files() -> List[Tuple[str, str]]:
    """Get list of staged files with their status."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return []
    
    files = []
    for line in result.stdout.splitlines():
        if line.strip():
            status, file = line.split(maxsplit=1)
            files.append((status, file))
    return files

def get_unstaged_files() -> List[Tuple[str, str]]:
    """Get list of unstaged files with their status."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return []
    
    files = []
    for line in result.stdout.splitlines():
        if line.strip():
            # Parse the status code
            # First char: index status
            # Second char: working tree status
            status = line[:2]
            file = line[3:].strip()
            
            # Map status codes to more readable format
            status_map = {
                " M": "modified",
                "M ": "modified",
                "MM": "modified",
                " A": "new file",
                "A ": "new file",
                "AA": "new file",
                " D": "deleted",
                "D ": "deleted",
                "DD": "deleted",
                " R": "renamed",
                "R ": "renamed",
                "RR": "renamed",
                " C": "copied",
                "C ": "copied",
                "CC": "copied",
                "??": "untracked"
            }
            
            readable_status = status_map.get(status, status)
            files.append((readable_status, file))
    return files

def get_staged_diff() -> str:
    """Get diff of staged changes."""
    result = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True,
        text=True
    )
    return result.stdout if result.returncode == 0 else ""

def get_file_diff(file: str) -> str:
    """Get diff for a specific staged (cached) file."""
    result = subprocess.run(
        ["git", "diff", "--cached", file],
        capture_output=True,
        text=True
    )
    return result.stdout if result.returncode == 0 else ""

def stage_file(file: str) -> bool:
    """Stage a specific file."""
    result = subprocess.run(
        ["git", "add", file],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def stage_all() -> bool:
    """Stage all changes."""
    result = subprocess.run(
        ["git", "add", "."],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def create_commit(message: str) -> bool:
    """Create a commit with the given message."""
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def get_current_branch() -> str:
    """Get current branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""

def push_changes() -> bool:
    """Push changes to remote repository."""
    result = subprocess.run(
        ["git", "push"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def get_default_remote_branch() -> str:
    """Detect the default branch of the remote (origin) and return as 'origin/<branch>'."""
    # Try symbolic-ref first
    try:
        result = subprocess.run([
            "git", "symbolic-ref", "refs/remotes/origin/HEAD"
        ], capture_output=True, text=True, check=True)
        ref = result.stdout.strip()
        if ref.startswith("refs/remotes/origin/"):
            branch = ref[len("refs/remotes/origin/"):]
            return f"origin/{branch}"
    except subprocess.CalledProcessError:
        pass
    # Fallback: parse 'git remote show origin'
    try:
        result = subprocess.run([
            "git", "remote", "show", "origin"
        ], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if "HEAD branch:" in line:
                branch = line.split(":", 1)[1].strip()
                return f"origin/{branch}"
    except Exception:
        pass
    raise RuntimeError("Could not determine the default remote branch (origin). Please check your remote configuration.")

def has_uncommitted_changes() -> bool:
    """
    Returns True if there are any staged or unstaged changes in the working directory.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())

def has_uncommitted_changes_debug() -> Tuple[bool, str]:
    """
    Returns True if there are any staged or unstaged changes, plus debug info.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    output = result.stdout.strip()
    return bool(output), output

def has_staged_changes() -> bool:
    """
    Returns True if there are any staged changes ready to commit.
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True,
        text=True
    )
    return result.returncode != 0

def has_unstaged_changes() -> bool:
    """
    Returns True if there are any unstaged changes in tracked files.
    """
    result = subprocess.run(
        ["git", "diff", "--quiet"],
        capture_output=True,
        text=True
    )
    return result.returncode != 0 