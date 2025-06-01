import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import subprocess

from gitwise.core.git_manager import GitManager, subprocess

# Test data
MOCK_REPO_PATH = "/test/repo"


@pytest.fixture
def mock_subprocess_run():
    with patch("gitwise.core.git_manager.subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def git_manager_instance(mock_subprocess_run):
    # Mock _find_git_root to avoid actual subprocess call during instantiation
    with patch.object(GitManager, "_find_git_root", return_value=MOCK_REPO_PATH):
        gm = GitManager(path=MOCK_REPO_PATH)
        # Reset mock_subprocess_run that might have been called by _find_git_root
        # if it wasn't patched *before* GitManager instantiation in a real scenario.
        # For this fixture setup, it's fine as _find_git_root is directly patched.
        mock_subprocess_run.reset_mock()
        yield gm


# Test _run_git_command (internal helper, but crucial)
def test_run_git_command_success(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(
        stdout="success", stderr="", returncode=0
    )
    result = git_manager_instance._run_git_command(["test-command"])
    mock_subprocess_run.assert_called_once_with(
        ["git", "test-command"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == "success"


def test_run_git_command_failure_called_process_error(
    git_manager_instance, mock_subprocess_run
):
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, "git test-command", stderr="git error"
    )
    with pytest.raises(RuntimeError) as excinfo:
        git_manager_instance._run_git_command(["test-command"])
    assert "Git command 'git test-command' failed with exit code 1." in str(
        excinfo.value
    )
    assert "Stderr:\ngit error" in str(excinfo.value)


def test_run_git_command_file_not_found(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.side_effect = FileNotFoundError
    with pytest.raises(RuntimeError) as excinfo:
        git_manager_instance._run_git_command(["test-command"])
    assert "Git command not found" in str(excinfo.value)


# Test _find_git_root
@patch("gitwise.core.git_manager.subprocess.run")
def test_find_git_root_success(mock_run_global):
    mock_run_global.return_value = MagicMock(stdout=f"{MOCK_REPO_PATH}\n", returncode=0)
    # Instantiate GitManager *after* patching subprocess.run globally for this test
    gm = GitManager()
    assert gm.repo_path == MOCK_REPO_PATH
    mock_run_global.assert_called_once_with(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )


@patch("gitwise.core.git_manager.subprocess.run")
def test_find_git_root_failure(mock_run_global):
    mock_run_global.side_effect = subprocess.CalledProcessError(1, "git rev-parse")
    with pytest.raises(RuntimeError, match="Not inside a Git repository"):
        GitManager()


# Test is_git_repo
def test_is_git_repo_true(mock_subprocess_run):
    # This test relies on GitManager being instantiated with a path,
    # and _find_git_root being mocked during its instantiation for other tests.
    # For a direct test of is_git_repo, we'd ideally mock _find_git_root for *this* instance.
    # However, since GitManager's constructor calls _find_git_root, we test its outcome.
    with patch.object(GitManager, "_find_git_root", return_value=MOCK_REPO_PATH):
        gm = GitManager()
        assert gm.is_git_repo() is True
    # Test when no git repo is found
    with patch.object(GitManager, "_find_git_root", return_value=None):
        # GitManager raises RuntimeError when no git repo is found
        with pytest.raises(RuntimeError, match="Not inside a Git repository"):
            gm = GitManager(path=None)


# Test get_staged_files
def test_get_staged_files_success(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(
        stdout="M\tfile1.py\nA\tfile2.txt", returncode=0
    )
    files = git_manager_instance.get_staged_files()
    assert files == [("M", "file1.py"), ("A", "file2.txt")]
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--cached", "--name-status"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


def test_get_staged_files_failure(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(returncode=1, stderr="error")
    files = git_manager_instance.get_staged_files()
    assert files == []


# Test get_unstaged_files
def test_get_unstaged_files_success(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(
        stdout=" M file1.py\n?? file2.txt", returncode=0
    )
    files = git_manager_instance.get_unstaged_files()
    assert files == [("Modified", "file1.py"), ("Untracked", "file2.txt")]
    mock_subprocess_run.assert_called_once_with(
        ["git", "status", "--porcelain"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test get_staged_diff
def test_get_staged_diff_success(git_manager_instance, mock_subprocess_run):
    diff_content = "diff --git a/file1.py b/file1.py\n--- a/file1.py\n+++ b/file1.py\n@@ -1 +1 @@\n-old\n+new"
    mock_subprocess_run.return_value = MagicMock(stdout=diff_content, returncode=0)
    diff = git_manager_instance.get_staged_diff()
    assert diff == diff_content
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--cached"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test get_file_diff_staged
def test_get_file_diff_staged_success(git_manager_instance, mock_subprocess_run):
    diff_content = "diff for file1.py"
    mock_subprocess_run.return_value = MagicMock(stdout=diff_content, returncode=0)
    diff = git_manager_instance.get_file_diff_staged("file1.py")
    assert diff == diff_content
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--cached", "--", "file1.py"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test get_changed_file_paths_staged
def test_get_changed_file_paths_staged_success(
    git_manager_instance, mock_subprocess_run
):
    mock_subprocess_run.return_value = MagicMock(
        stdout="file1.py\nmodule/file2.py", returncode=0
    )
    paths = git_manager_instance.get_changed_file_paths_staged()
    assert paths == ["file1.py", "module/file2.py"]
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--cached", "--name-only"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test stage_files
def test_stage_files_success(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    result = git_manager_instance.stage_files(["file1.py", "file2.txt"])
    assert result is True
    mock_subprocess_run.assert_called_once_with(
        ["git", "add", "--", "file1.py", "file2.txt"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


def test_stage_files_no_files(git_manager_instance, mock_subprocess_run):
    result = git_manager_instance.stage_files([])
    assert result is True
    mock_subprocess_run.assert_not_called()


# Test stage_all
def test_stage_all_success(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    result = git_manager_instance.stage_all()
    assert result is True
    mock_subprocess_run.assert_called_once_with(
        ["git", "add", "."],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test create_commit
def test_create_commit_success(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    result = git_manager_instance.create_commit("feat: test commit")
    assert result is True
    mock_subprocess_run.assert_called_once_with(
        ["git", "commit", "-m", "feat: test commit"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test get_current_branch
def test_get_current_branch_success(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(
        stdout="feature/branch-123\n", returncode=0
    )
    branch = git_manager_instance.get_current_branch()
    assert branch == "feature/branch-123"
    mock_subprocess_run.assert_called_once_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


def test_get_current_branch_detached_head(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(stdout="HEAD\n", returncode=0)
    branch = git_manager_instance.get_current_branch()
    assert branch is None


# Test push_to_remote
def test_push_to_remote_simple(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    result = git_manager_instance.push_to_remote(local_branch="main")
    assert result is True
    mock_subprocess_run.assert_called_once_with(
        ["git", "push", "origin", "main"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


def test_push_to_remote_with_remote_branch_and_force(
    git_manager_instance, mock_subprocess_run
):
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    result = git_manager_instance.push_to_remote(
        local_branch="feature/x",
        remote_branch="feature/x-upstream",
        remote_name="upstream",
        force=True,
    )
    assert result is True
    mock_subprocess_run.assert_called_once_with(
        ["git", "push", "upstream", "feature/x:feature/x-upstream", "--force"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test get_default_remote_branch_name
def test_get_default_remote_branch_name_sym_ref(
    git_manager_instance, mock_subprocess_run
):
    mock_subprocess_run.return_value = MagicMock(
        stdout="refs/remotes/origin/main\n", returncode=0
    )
    branch = git_manager_instance.get_default_remote_branch_name()
    assert branch == "main"
    mock_subprocess_run.assert_called_once_with(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=True,
    )


def test_get_default_remote_branch_name_remote_show(
    git_manager_instance, mock_subprocess_run
):
    # Simulate symbolic-ref failing, then remote show succeeding
    mock_subprocess_run.side_effect = [
        RuntimeError("symbolic-ref failed"),  # First call for symbolic-ref
        MagicMock(
            stdout="* remote origin\n  Fetch URL: ...\n  Push  URL: ...\n  HEAD branch: develop\n",
            returncode=0,
        ),  # Second call for remote show
    ]
    branch = git_manager_instance.get_default_remote_branch_name()
    assert branch == "develop"
    expected_calls = [
        call(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=True,
        ),
        call(
            ["git", "remote", "show", "origin"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=True,
        ),
    ]
    mock_subprocess_run.assert_has_calls(expected_calls)


def test_get_default_remote_branch_name_common_check(
    git_manager_instance, mock_subprocess_run
):
    # Simulate symbolic-ref and remote show failing, then common branch check succeeding for 'main'
    mock_subprocess_run.side_effect = [
        RuntimeError("symbolic-ref failed"),
        RuntimeError("remote show failed"),
        MagicMock(returncode=0),  # Successful check for 'refs/remotes/origin/main'
    ]
    branch = git_manager_instance.get_default_remote_branch_name()
    assert branch == "main"
    expected_calls = [
        call(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=True,
        ),
        call(
            ["git", "remote", "show", "origin"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=True,
        ),
        call(
            ["git", "show-ref", "--verify", "refs/remotes/origin/main"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=True,
        ),
    ]
    mock_subprocess_run.assert_has_calls(expected_calls)


def test_get_default_remote_branch_name_not_found(
    git_manager_instance, mock_subprocess_run
):
    # Simulate all methods failing
    mock_subprocess_run.side_effect = [
        RuntimeError("symbolic-ref failed"),
        RuntimeError("remote show failed"),
        RuntimeError("show-ref main failed"),
        RuntimeError("show-ref master failed"),
    ]
    branch = git_manager_instance.get_default_remote_branch_name()
    assert branch is None


# Test get_commits_between
def test_get_commits_between_success(git_manager_instance, mock_subprocess_run):
    log_output = "hash1|feat: one|Alice\nhash2|fix: two|Bob"
    mock_subprocess_run.return_value = MagicMock(stdout=log_output, returncode=0)
    commits = git_manager_instance.get_commits_between("tag1", "tag2")
    expected = [
        {"hash": "hash1", "message": "feat: one", "author": "Alice"},
        {"hash": "hash2", "message": "fix: two", "author": "Bob"},
    ]
    assert commits == expected
    mock_subprocess_run.assert_called_once_with(
        ["git", "log", "tag1..tag2", "--pretty=format:%H|%s|%an"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


def test_get_commits_between_no_commits(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(
        stdout="", returncode=0
    )  # Empty output
    commits = git_manager_instance.get_commits_between("tag1", "tag2")
    assert commits == []


# Test get_merge_base
def test_get_merge_base_success(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(
        stdout="commonancestorhash\n", returncode=0
    )
    base = git_manager_instance.get_merge_base("branch1", "branch2")
    assert base == "commonancestorhash"
    mock_subprocess_run.assert_called_once_with(
        ["git", "merge-base", "branch1", "branch2"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=True,
    )


def test_get_merge_base_failure(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.side_effect = RuntimeError("merge-base failed")
    base = git_manager_instance.get_merge_base("branch1", "branch2")
    assert base is None


# Test has_uncommitted_changes
def test_has_uncommitted_changes_true(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(stdout=" M file.txt\n", returncode=0)
    assert git_manager_instance.has_uncommitted_changes() is True


def test_has_uncommitted_changes_false(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(stdout="", returncode=0)
    assert git_manager_instance.has_uncommitted_changes() is False


# Test has_staged_changes
def test_has_staged_changes_true(git_manager_instance, mock_subprocess_run):
    # `git diff --cached --quiet` exits with 1 if there are staged changes
    mock_subprocess_run.return_value = MagicMock(returncode=1)
    assert git_manager_instance.has_staged_changes() is True
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--cached", "--quiet"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


def test_has_staged_changes_false(git_manager_instance, mock_subprocess_run):
    # `git diff --cached --quiet` exits with 0 if no staged changes
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    assert git_manager_instance.has_staged_changes() is False


# Test has_unstaged_tracked_changes
def test_has_unstaged_tracked_changes_true(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(returncode=1)
    assert git_manager_instance.has_unstaged_tracked_changes() is True
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--quiet"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test get_list_of_unstaged_tracked_files
def test_get_list_of_unstaged_tracked_files_present(
    git_manager_instance, mock_subprocess_run
):
    mock_subprocess_run.return_value = MagicMock(
        stdout="file1.py\ndir/file2.js\n", returncode=0
    )
    files = git_manager_instance.get_list_of_unstaged_tracked_files()
    assert files == ["file1.py", "dir/file2.js"]
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--name-only"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test get_list_of_untracked_files
def test_get_list_of_untracked_files_present(git_manager_instance, mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(
        stdout="untracked1.txt\nnew_dir/untracked2.log\n", returncode=0
    )
    files = git_manager_instance.get_list_of_untracked_files()
    assert files == ["untracked1.txt", "new_dir/untracked2.log"]
    mock_subprocess_run.assert_called_once_with(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=MOCK_REPO_PATH,
        capture_output=True,
        text=True,
        check=False,
    )


# Test get_local_base_branch_name
def test_get_local_base_branch_name_from_config(
    git_manager_instance, mock_subprocess_run
):
    # First call for 'git config init.defaultBranch', second for 'git rev-parse --verify <branch>'
    mock_subprocess_run.side_effect = [
        MagicMock(stdout="main\n", returncode=0),  # config output
        MagicMock(returncode=0),  # rev-parse main success
    ]
    branch = git_manager_instance.get_local_base_branch_name()
    assert branch == "main"
    expected_calls = [
        call(
            ["git", "config", "init.defaultBranch"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=True,
        ),
        call(
            ["git", "rev-parse", "--verify", "main"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=False,
        ),
    ]
    mock_subprocess_run.assert_has_calls(expected_calls)


def test_get_local_base_branch_name_common_main(
    git_manager_instance, mock_subprocess_run
):
    # config fails, rev-parse main succeeds
    mock_subprocess_run.side_effect = [
        RuntimeError("config failed"),
        MagicMock(returncode=0),  # rev-parse main success
    ]
    branch = git_manager_instance.get_local_base_branch_name()
    assert branch == "main"
    expected_calls = [
        call(
            ["git", "config", "init.defaultBranch"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=True,
        ),
        call(
            ["git", "rev-parse", "--verify", "main"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=False,
        ),
    ]
    mock_subprocess_run.assert_has_calls(expected_calls)


def test_get_local_base_branch_name_common_master(
    git_manager_instance, mock_subprocess_run
):
    # config fails, rev-parse main fails, rev-parse master succeeds
    mock_subprocess_run.side_effect = [
        RuntimeError("config failed"),
        MagicMock(returncode=1),  # rev-parse main fails
        MagicMock(returncode=0),  # rev-parse master success
    ]
    branch = git_manager_instance.get_local_base_branch_name()
    assert branch == "master"
    expected_calls = [
        call(
            ["git", "config", "init.defaultBranch"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=True,
        ),
        call(
            ["git", "rev-parse", "--verify", "main"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=False,
        ),
        call(
            ["git", "rev-parse", "--verify", "master"],
            cwd=MOCK_REPO_PATH,
            capture_output=True,
            text=True,
            check=False,
        ),
    ]
    mock_subprocess_run.assert_has_calls(expected_calls)


def test_get_local_base_branch_name_not_found(
    git_manager_instance, mock_subprocess_run
):
    # All checks fail
    mock_subprocess_run.side_effect = [
        RuntimeError("config failed"),
        MagicMock(returncode=1),  # rev-parse main fails
        MagicMock(returncode=1),  # rev-parse master fails
    ]
    branch = git_manager_instance.get_local_base_branch_name()
    assert branch is None
