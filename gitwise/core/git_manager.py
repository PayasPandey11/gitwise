"""Core Git operations manager for GitWise, using subprocess."""

import os
import subprocess
import logging
from typing import Dict, List, Optional, Tuple

from gitwise.exceptions import SecurityError, GitOperationError


class GitManager:
    """
    Manages Git operations for the GitWise application.
    All methods interact with Git via subprocess calls.
    """

    def __init__(self, path: Optional[str] = None):
        """
        Initializes the GitManager.

        Args:
            path: The path to the Git repository. Defaults to the current working directory.
        """
        self.logger = logging.getLogger(__name__)
        self.repo_path = path or self._find_git_root()
        if not self.repo_path:
            self.logger.error(f"Git repository not found at path: {path}")
            raise GitOperationError(
                "Not inside a Git repository or .git directory not found."
            )
        
        self.logger.info(f"GitManager initialized for repo: {self.repo_path}")

    def _validate_file_path(self, file_path: str) -> str:
        """
        Validate that a file path is within the repository boundaries.
        
        Args:
            file_path: The file path to validate
            
        Returns:
            The absolute path if valid
            
        Raises:
            SecurityError: If the path is outside the repository
        """
        # Convert to absolute paths for comparison
        abs_file_path = os.path.abspath(file_path)
        abs_repo_path = os.path.abspath(self.repo_path)
        
        # Check if the file path is within the repository
        if not abs_file_path.startswith(abs_repo_path + os.sep) and abs_file_path != abs_repo_path:
            raise SecurityError(
                f"File path '{file_path}' is outside the repository boundaries. "
                f"Only files within the repository are allowed."
            )
        
        return abs_file_path

    def _run_git_command(
        self,
        command: List[str],
        check: bool = True,
        capture_output: bool = True,
        text: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Helper to run a Git command.

        Args:
            command: The Git command and its arguments as a list of strings.
            check: If True, raises CalledProcessError for a non-zero exit code.
            capture_output: If True, stdout and stderr are captured.
            text: If True, decodes stdout and stderr as text.

        Returns:
            A subprocess.CompletedProcess instance.
        """
        full_command = ["git"] + command
        try:
            return subprocess.run(
                full_command,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=text,
                check=check,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Git command not found. Please ensure Git is installed and in your PATH."
            )
        except subprocess.CalledProcessError as e:
            # Add more context to the error
            error_message = f"Git command '{' '.join(full_command)}' failed with exit code {e.returncode}."
            if e.stderr:
                error_message += f"\nStderr:\n{e.stderr.strip()}"
            if e.stdout:  # Sometimes errors also print to stdout
                error_message += f"\nStdout:\n{e.stdout.strip()}"
            raise RuntimeError(error_message) from e
        except Exception as e:  # Catch-all for other potential subprocess issues
            raise RuntimeError(
                f"An unexpected error occurred while running git command '{' '.join(full_command)}': {e}"
            )

    def _find_git_root(self) -> Optional[str]:
        """Finds the root directory of the current Git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def is_git_repo(self) -> bool:
        """Checks if the current path is a Git repository."""
        return self._find_git_root() is not None

    def get_staged_files(self) -> List[Tuple[str, str]]:
        """Get list of staged files with their status (e.g., 'A', 'M', 'D')."""
        result = self._run_git_command(
            ["diff", "--cached", "--name-status"], check=False
        )
        if result.returncode != 0:
            return []

        files = []
        for line in result.stdout.splitlines():
            if line.strip():
                status, file_path = line.split(maxsplit=1)
                files.append((status.strip(), file_path.strip()))
        return files

    def get_unstaged_files(self) -> List[Tuple[str, str]]:
        """Get list of unstaged (working directory) files with their status."""
        result = self._run_git_command(["status", "--porcelain"], check=False)
        if result.returncode != 0:
            return []

        files = []
        # Format of porcelain:
        # XY PATH
        # XY ORIG_PATH -> PATH (for renames/copies)
        for line in result.stdout.splitlines():
            if line.strip():
                status_xy = line[:2]
                path_info = line[3:]

                # Handle renames/copies (R/C) which have "ORIG_PATH -> PATH"
                if " -> " in path_info:
                    orig_path, file_path = path_info.split(" -> ", 1)
                else:
                    file_path = path_info

                # Map XY status to a more readable or usable single status
                # For simplicity, just returning XY for now. Can be expanded.
                # Example: ' M' = modified in working tree, 'MM' = modified in index and working tree
                # 'A ' = added to index, '??' = untracked
                status_map = {
                    " M": "Modified",
                    "M ": "Modified (staged)",
                    "MM": "Modified (staged & unstaged)",
                    " A": "Added",
                    "A ": "Added (staged)",
                    "AM": "Added (staged with unstaged mods)",
                    " D": "Deleted",
                    "D ": "Deleted (staged)",
                    " R": "Renamed",
                    "R ": "Renamed (staged)",
                    " C": "Copied",
                    "C ": "Copied (staged)",
                    "??": "Untracked",
                    "!!": "Ignored",
                }
                readable_status = status_map.get(
                    status_xy, status_xy
                )  # Default to XY if not in map
                files.append((readable_status, file_path.strip()))
        return files

    def get_staged_diff(self) -> str:
        """Get combined diff of all staged changes."""
        result = self._run_git_command(["diff", "--cached"], check=False)
        return result.stdout if result.returncode == 0 else ""

    def get_file_diff_staged(self, file_path: str) -> str:
        """Get diff for a specific staged (cached) file."""
        result = self._run_git_command(
            ["diff", "--cached", "--", file_path], check=False
        )
        return result.stdout if result.returncode == 0 else ""

    def get_changed_file_paths_staged(self) -> List[str]:
        """Get list of paths for staged files."""
        result = self._run_git_command(["diff", "--cached", "--name-only"], check=False)
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def stage_files(self, file_paths: List[str]) -> bool:
        """Stage specific files."""
        if not file_paths:
            return True  # Nothing to stage
        result = self._run_git_command(["add", "--"] + file_paths, check=False)
        return result.returncode == 0

    def stage_all(self) -> bool:
        """Stage all changes (git add .)."""
        result = self._run_git_command(["add", "."], check=False)
        return result.returncode == 0

    def create_commit(self, message: str) -> bool:
        """Create a commit with the given message."""
        # Consider using -F - to pass message via stdin if it's complex or multiline
        # For now, direct -m for simplicity, but be wary of shell injection if message is not controlled.
        # Typer/tempfile editing for messages mitigates this.
        result = self._run_git_command(["commit", "-m", message], check=False)
        if result.returncode not in [
            0,
            1,
        ]:  # 1 can mean "nothing to commit" if files were unstaged
            # Log or handle specific non-zero codes if needed
            pass
        return result.returncode == 0

    def get_current_branch(self) -> Optional[str]:
        """Get current branch name."""
        result = self._run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"], check=False
        )
        return (
            result.stdout.strip()
            if result.returncode == 0 and result.stdout.strip() != "HEAD"
            else None
        )

    def push_to_remote(
        self,
        local_branch: Optional[str] = None,
        remote_branch: Optional[str] = None,
        remote_name: str = "origin",
        force: bool = False,
    ) -> bool:
        """Push changes to remote repository."""
        cmd = ["push", remote_name]
        if local_branch and remote_branch:
            cmd.append(f"{local_branch}:{remote_branch}")
        elif (
            local_branch
        ):  # Push current local branch to a remote branch of the same name
            cmd.append(local_branch)
        # If neither local_branch nor remote_branch, git push uses default configured behavior.

        if force:
            cmd.append("--force")

        result = self._run_git_command(cmd, check=False)
        return result.returncode == 0

    def get_default_remote_branch_name(
        self, remote_name: str = "origin"
    ) -> Optional[str]:
        """
        Detect the default branch of the specified remote (e.g., 'main', 'master').
        Does not include the 'origin/' prefix.
        """
        try:
            # Try symbolic-ref first for origin/HEAD
            result_sym_ref = self._run_git_command(
                ["symbolic-ref", f"refs/remotes/{remote_name}/HEAD"], check=True
            )
            ref = result_sym_ref.stdout.strip()  # e.g., refs/remotes/origin/main
            prefix = f"refs/remotes/{remote_name}/"
            if ref.startswith(prefix):
                return ref[len(prefix) :]
        except RuntimeError:  # Raised by _run_git_command if check=True fails
            pass  # Symbolic ref might not exist or other issue, try next method.

        try:
            # Fallback: parse 'git remote show origin'
            result_remote_show = self._run_git_command(
                ["remote", "show", remote_name], check=True
            )
            for line in result_remote_show.stdout.splitlines():
                line_stripped = line.strip()
                if line_stripped.startswith("HEAD branch:"):
                    return line_stripped.split(":", 1)[1].strip()
        except RuntimeError:
            pass

        # If the above fail, common defaults, though less reliable
        for common_branch in ["main", "master"]:
            # Check if remote branch exists (e.g. origin/main)
            try:
                self._run_git_command(
                    [
                        "show-ref",
                        "--verify",
                        f"refs/remotes/{remote_name}/{common_branch}",
                    ],
                    check=True,
                )
                return common_branch
            except RuntimeError:
                continue
        return None

    def get_commits_between(
        self, ref1: str, ref2: str, pretty_format: str = "%H|%s|%an"
    ) -> List[Dict[str, str]]:
        """Get commits between two refs (e.g., 'tag1..tag2', 'origin/main..HEAD')."""
        range_spec = f"{ref1}..{ref2}"
        result = self._run_git_command(
            ["log", range_spec, f"--pretty=format:{pretty_format}"], check=False
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        commits = []
        keys = []
        if pretty_format == "%H|%s|%an":  # Default known format
            keys = ["hash", "message", "author"]
        # Add more recognized formats if needed, or make keys dynamic based on format codes

        for line in result.stdout.strip().split("\n"):
            parts = line.split("|", len(keys) - 1 if keys else 0)
            if keys and len(parts) == len(keys):
                commits.append(dict(zip(keys, parts)))
            elif not keys:  # If no keys (e.g. custom format not parsed here)
                commits.append({"raw": line})  # Store raw line
            # Else: malformed line for known format, skip or log
        return commits

    def get_merge_base(self, ref1: str, ref2: str) -> Optional[str]:
        """Get the best common ancestor between two commits."""
        try:
            result = self._run_git_command(["merge-base", ref1, ref2], check=True)
            return result.stdout.strip()
        except (
            RuntimeError
        ):  # Includes CalledProcessError if no common ancestor or other git errors
            return None

    def has_uncommitted_changes(self) -> bool:
        """Check if there are any staged or unstaged changes."""
        result = self._run_git_command(["status", "--porcelain"], check=False)
        return bool(result.stdout.strip()) if result.returncode == 0 else False

    def has_staged_changes(self) -> bool:
        """Check if there are any staged changes."""
        # `git diff --cached --quiet` exits with 1 if there are staged changes, 0 otherwise.
        result = self._run_git_command(["diff", "--cached", "--quiet"], check=False)
        return result.returncode == 1

    def has_unstaged_tracked_changes(self) -> bool:
        """Check if there are any unstaged changes in tracked files."""
        # `git diff --quiet` exits with 1 if there are unstaged changes, 0 otherwise.
        result = self._run_git_command(["diff", "--quiet"], check=False)
        return result.returncode == 1

    def get_list_of_unstaged_tracked_files(self) -> List[str]:
        """Get a list of unstaged (modified) tracked files."""
        result = self._run_git_command(["diff", "--name-only"], check=False)
        if result.returncode == 0 and result.stdout:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return []

    def get_list_of_untracked_files(self) -> List[str]:
        """Get a list of untracked files."""
        result = self._run_git_command(
            ["ls-files", "--others", "--exclude-standard"], check=False
        )
        if result.returncode == 0 and result.stdout:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return []

    # Example of a more complex function that might use GitPython if kept,
    # or would need more elaborate subprocess logic.
    # For now, using a simpler subprocess approach for get_base_branch
    def get_local_base_branch_name(self) -> Optional[str]:
        """
        Tries to determine a local base branch, commonly 'main' or 'master'.
        This is different from the default remote branch.
        """
        # Attempt to get init.defaultBranch from git config
        try:
            result = self._run_git_command(["config", "init.defaultBranch"], check=True)
            default_branch = result.stdout.strip()
            if default_branch:
                # Verify this branch exists locally
                verify_result = self._run_git_command(
                    ["rev-parse", "--verify", default_branch], check=False
                )
                if verify_result.returncode == 0:
                    return default_branch
        except RuntimeError:
            pass  # Config not set or branch doesn't exist

        # Check for common names 'main', then 'master'
        for branch_name in ["main", "master"]:
            verify_result = self._run_git_command(
                ["rev-parse", "--verify", branch_name], check=False
            )
            if verify_result.returncode == 0:
                return branch_name
        return None

    # Smart merge related methods
    def can_merge(self, source_branch: str, target_branch: Optional[str] = None) -> bool:
        """Check if a merge is possible between branches."""
        if not target_branch:
            target_branch = self.get_current_branch()
        if not target_branch:
            return False
        
        try:
            # Check if branches exist
            self._run_git_command(["rev-parse", "--verify", source_branch], check=True)
            self._run_git_command(["rev-parse", "--verify", target_branch], check=True)
            return True
        except RuntimeError:
            return False

    def get_merge_conflicts(self) -> List[str]:
        """Get list of files with merge conflicts."""
        result = self._run_git_command(["diff", "--name-only", "--diff-filter=U"], check=False)
        if result.returncode == 0 and result.stdout:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return []

    def get_conflict_content(self, file_path: str) -> Optional[Dict[str, str]]:
        """Get conflict markers content for a specific file with enhanced context."""
        try:
            # Validate the file path for security
            validated_path = self._validate_file_path(file_path)
            
            with open(validated_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '<<<<<<< HEAD' not in content:
                return None
            
            # Parse conflict markers with line numbers and context
            lines = content.splitlines()
            conflicts = []
            conflict_regions = []
            
            i = 0
            while i < len(lines):
                if lines[i].startswith('<<<<<<< '):
                    # Found start of conflict
                    start_line = i
                    our_lines = []
                    their_lines = []
                    separator_line = None
                    end_line = None
                    
                    i += 1
                    # Collect "our" content
                    while i < len(lines):
                        if lines[i].startswith('======='):
                            separator_line = i
                            break
                        our_lines.append(lines[i])
                        i += 1
                    
                    i += 1
                    # Collect "their" content
                    while i < len(lines):
                        if lines[i].startswith('>>>>>>> '):
                            end_line = i
                            break
                        their_lines.append(lines[i])
                        i += 1
                    
                    if end_line is not None:
                        conflicts.append({
                            "start_line": start_line,
                            "end_line": end_line,
                            "our_content": "\n".join(our_lines),
                            "their_content": "\n".join(their_lines),
                            "our_lines": our_lines,
                            "their_lines": their_lines
                        })
                        
                        conflict_regions.append((start_line, end_line))
                
                i += 1
            
            # Get context around conflicts (10 lines before and after each conflict)
            context_window = 10
            enhanced_conflicts = []
            
            for conflict in conflicts:
                start_line = conflict["start_line"]
                end_line = conflict["end_line"]
                
                # Get context before conflict
                context_start = max(0, start_line - context_window)
                before_context = lines[context_start:start_line]
                
                # Get context after conflict
                context_end = min(len(lines), end_line + 1 + context_window)
                after_context = lines[end_line + 1:context_end]
                
                enhanced_conflict = {
                    **conflict,
                    "before_context": "\n".join(before_context),
                    "after_context": "\n".join(after_context),
                    "context_start_line": context_start,
                    "context_end_line": context_end - 1,
                    "full_context": "\n".join(
                        before_context + 
                        [f"<<<< CONFLICT START (line {start_line + 1}) >>>>"] +
                        conflict["our_lines"] +
                        ["======= THEIR CHANGES ======="] +
                        conflict["their_lines"] +
                        [f"<<<< CONFLICT END (line {end_line + 1}) >>>>"] +
                        after_context
                    )
                }
                enhanced_conflicts.append(enhanced_conflict)
            
            return {
                "our_content": "\n".join(sum([c["our_lines"] for c in conflicts], [])),
                "their_content": "\n".join(sum([c["their_lines"] for c in conflicts], [])),
                "full_content": content,
                "conflicts": enhanced_conflicts,
                "total_lines": len(lines),
                "conflict_count": len(conflicts)
            }
        except Exception:
            return None

    def attempt_merge(self, source_branch: str, no_commit: bool = True) -> bool:
        """Attempt to merge a branch. Returns True if successful, False if conflicts."""
        cmd = ["merge"]
        if no_commit:
            cmd.append("--no-commit")
        cmd.append(source_branch)
        
        result = self._run_git_command(cmd, check=False)
        return result.returncode == 0

    def abort_merge(self) -> bool:
        """Abort an ongoing merge."""
        result = self._run_git_command(["merge", "--abort"], check=False)
        return result.returncode == 0

    def continue_merge(self) -> bool:
        """Continue merge after resolving conflicts."""
        result = self._run_git_command(["merge", "--continue"], check=False)
        return result.returncode == 0

    def is_merge_in_progress(self) -> bool:
        """Check if a merge is currently in progress."""
        try:
            result = self._run_git_command(["rev-parse", "--verify", "MERGE_HEAD"], check=False)
            return result.returncode == 0
        except RuntimeError:
            return False

    def get_branch_divergence(self, branch1: str, branch2: str) -> Optional[Dict[str, int]]:
        """Get number of commits each branch is ahead/behind the other."""
        try:
            # Get commits in branch1 not in branch2
            result1 = self._run_git_command(
                ["rev-list", "--count", f"{branch2}..{branch1}"], check=True
            )
            ahead = int(result1.stdout.strip())
            
            # Get commits in branch2 not in branch1
            result2 = self._run_git_command(
                ["rev-list", "--count", f"{branch1}..{branch2}"], check=True
            )
            behind = int(result2.stdout.strip())
            
            return {"ahead": ahead, "behind": behind}
        except (RuntimeError, ValueError):
            return None

    def can_fast_forward(self, source_branch: str, target_branch: Optional[str] = None) -> bool:
        """Check if merge can be fast-forwarded."""
        if not target_branch:
            target_branch = self.get_current_branch()
        if not target_branch:
            return False
        
        divergence = self.get_branch_divergence(source_branch, target_branch)
        return divergence is not None and divergence["behind"] == 0


# Example usage (for testing purposes, normally not here)
if __name__ == "__main__":
    try:
        manager = GitManager()
        if manager.is_git_repo():
            print(f"Current Git Repo Root: {manager.repo_path}")
            print(f"Current branch: {manager.get_current_branch()}")
            print(f"Staged files: {manager.get_staged_files()}")
            print(f"Unstaged files: {manager.get_unstaged_files()}")
            print(f"Has staged changes: {manager.has_staged_changes()}")
            print(f"Has uncommitted changes: {manager.has_uncommitted_changes()}")
            print(f"Default remote branch: {manager.get_default_remote_branch_name()}")
            print(f"Local base branch: {manager.get_local_base_branch_name()}")
        else:
            print("Not a git repository.")
    except RuntimeError as e:
        print(f"Error: {e}")
