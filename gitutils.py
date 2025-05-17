import subprocess

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