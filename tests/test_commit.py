from unittest.mock import MagicMock, patch, call
import pytest
import os

from gitwise.features.commit import (
    CommitFeature,
    suggest_commit_groups, # Helper for testing grouping logic
    generate_commit_message, # Helper for direct LLM message generation test
    analyze_changes, # Helper for testing grouping logic
    suggest_scope # Helper for scope suggestion
)
from gitwise.core.git_manager import GitManager # Import GitManager
from gitwise.prompts import PROMPT_COMMIT_MESSAGE # Import for verifying prompt


@pytest.fixture
def mock_git_manager():
    """Fixture to mock GitManager."""
    with patch("gitwise.features.commit.git_manager", spec=GitManager) as mock_gm:
        mock_gm.get_changed_file_paths_staged.return_value = ["file1.py", "module/file2.py"]
        mock_gm.get_list_of_unstaged_tracked_files.return_value = [] # Corrected attribute name
        mock_gm.get_list_of_untracked_files.return_value = []
        mock_gm.get_staged_files.return_value = [("M", "file1.py")]
        mock_gm.get_staged_diff.return_value = "@@ -1,1 +1,1 @@\\n- old line\\n+ new line"
        mock_gm.get_file_diff_staged.return_value = "...diff for a file..."
        mock_gm.create_commit.return_value = True
        mock_gm.stage_files.return_value = True
        mock_gm.stage_all.return_value = True
        mock_gm._run_git_command.return_value = MagicMock(stdout='', returncode=0) # For reset HEAD in grouping
        yield mock_gm


@pytest.fixture
def mock_diff_str():
    return "@@ -1,1 +1,1 @@\\n- old line\\n+ new line"


@pytest.fixture
def mock_dependencies_commit_feature():
    """Mocks dependencies for CommitFeature that are not GitManager or LLM."""
    with patch("gitwise.features.commit.load_config", MagicMock(return_value={})), \
         patch("gitwise.features.commit.get_llm_backend", MagicMock(return_value="offline")), \
         patch("gitwise.features.commit.ensure_offline_model_ready", MagicMock()), \
         patch("gitwise.features.commit.typer.confirm") as mock_confirm, \
         patch("gitwise.features.commit.typer.prompt") as mock_prompt, \
         patch("gitwise.features.commit.safe_prompt") as mock_safe_prompt, \
         patch("gitwise.features.commit.safe_confirm") as mock_safe_confirm, \
         patch("gitwise.features.commit.components.show_spinner", MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))), \
         patch("gitwise.features.commit.get_push_command") as mock_get_push_command:
        
        mock_push_callable = MagicMock(return_value=True)
        mock_get_push_command.return_value = mock_push_callable
        
        yield {
            "confirm": mock_confirm,
            "prompt": mock_prompt, # typer.prompt
            "safe_prompt": mock_safe_prompt, # gitwise.features.commit.safe_prompt
            "safe_confirm": mock_safe_confirm, # gitwise.features.commit.safe_confirm
            "push_command": mock_push_callable
        }


def test_suggest_scope():
    assert suggest_scope(["file1.py", "module/file2.py", "module/file3.py"]) == "module"
    assert suggest_scope(["file1.py", "file2.js"]) == "" # No common parent dir other than root
    assert suggest_scope(["toplevel.py"]) == ""


@patch("gitwise.features.commit.generate_commit_message", return_value="chore: Default analysis message")
def test_analyze_changes_basic(mock_gen_msg, mock_git_manager):
    mock_git_manager.get_file_diff_staged.return_value = "diff for file1.py"
    changes = analyze_changes(["file1.py"])
    assert len(changes) == 1
    assert changes[0]["files"] == ["file1.py"]
    assert changes[0]["type"] == "chore"
    mock_gen_msg.assert_called_once_with("diff for file1.py")


@patch("gitwise.features.commit.generate_commit_message")
def test_analyze_changes_grouping(mock_gen_msg, mock_git_manager):
    mock_git_manager.get_file_diff_staged.side_effect = [
        "diff for file1.py", 
        "diff for file2.py",
        "diff for file3.py"
    ]
    # Simulate LLM generating same message for file1 and file3, different for file2
    mock_gen_msg.side_effect = [
        "feat: common feature", # for file1.py
        "fix: separate bug",    # for file2.py
        "feat: common feature"  # for file3.py
    ]
    
    changed_files = ["file1.py", "file2.py", "file3.py"]
    groups = analyze_changes(changed_files)
    
    assert len(groups) == 2
    # Find the group for common feature
    common_group = next(g for g in groups if g["type"] == "feat" and "common feature" in g["description"])
    assert sorted(common_group["files"]) == sorted(["file1.py", "file3.py"])
    assert common_group["diff"] == "diff for file1.py\ndiff for file3.py"
    
    # Find the group for separate bug
    bug_group = next(g for g in groups if g["type"] == "fix")
    assert bug_group["files"] == ["file2.py"]
    assert bug_group["diff"] == "diff for file2.py"


@patch("gitwise.features.commit.analyze_changes")
def test_suggest_commit_groups_calls_analyze_changes(mock_analyze, mock_git_manager):
    mock_git_manager.get_changed_file_paths_staged.return_value = ["file1.py"]
    suggest_commit_groups()
    mock_analyze.assert_called_once_with(["file1.py"])


@patch("gitwise.features.commit.get_llm_response")
def test_execute_commit_single_no_grouping(mock_get_llm, mock_git_manager, mock_dependencies_commit_feature, mock_diff_str):
    mock_get_llm.return_value = "feat: test commit message"
    mock_dependencies_commit_feature["safe_confirm"].return_value = True # Confirm push
    mock_dependencies_commit_feature["safe_prompt"].return_value = 1  # Use suggested message
    mock_dependencies_commit_feature["confirm"].return_value = False # No, don't view full diff

    feature = CommitFeature()
    feature.execute_commit(group=False)

    mock_git_manager.get_changed_file_paths_staged.assert_called()
    mock_git_manager.get_staged_diff.assert_called() # Called for message generation
    
    expected_prompt = PROMPT_COMMIT_MESSAGE.replace("{{diff}}", mock_diff_str).replace("{{guidance}}", "")
    mock_get_llm.assert_called_once_with(expected_prompt)
    mock_git_manager.create_commit.assert_called_once_with("feat: test commit message")
    mock_dependencies_commit_feature["push_command"].assert_called_once()


@patch("gitwise.features.commit.get_llm_response")
@patch("gitwise.features.commit.suggest_commit_groups")
def test_execute_commit_with_grouping_commit_separately(mock_suggest_groups, mock_get_llm, mock_git_manager, mock_dependencies_commit_feature):
    mock_suggest_groups.return_value = [
        {"files": ["file1.py"], "type": "feat", "description": "feature one", "diff": "diff1"},
        {"files": ["file2.py"], "type": "fix", "description": "bug two", "diff": "diff2"}
    ]
    # User choices: Commit separately, proceed with group 1, proceed with group 2, push all
    mock_dependencies_commit_feature["safe_prompt"].side_effect = [1] # Commit separately
    mock_dependencies_commit_feature["safe_confirm"].side_effect = [True, True, True] # Proceed with group1, group2, push all
    
    feature = CommitFeature()
    feature.execute_commit(group=True)

    mock_suggest_groups.assert_called_once()
    # Check unstage all files in suggestions
    mock_git_manager._run_git_command.assert_called_once_with(["reset", "HEAD", "--", "file1.py", "file2.py"], check=True)
    
    # Check staging and committing for each group
    calls_stage = [call(["file1.py"]), call(["file2.py"])]
    mock_git_manager.stage_files.assert_has_calls(calls_stage)
    
    calls_commit = [call("feat: feature one"), call("fix: bug two")]
    mock_git_manager.create_commit.assert_has_calls(calls_commit)
    mock_dependencies_commit_feature["push_command"].assert_called_once()


@patch("gitwise.features.commit.get_llm_response")
@patch("gitwise.features.commit.suggest_commit_groups")
def test_execute_commit_with_grouping_consolidate(mock_suggest_groups, mock_get_llm, mock_git_manager, mock_dependencies_commit_feature, mock_diff_str):
    mock_suggest_groups.return_value = [
        {"files": ["file1.py"], "type": "feat", "description": "feature one", "diff": "diff1"},
        {"files": ["file2.py"], "type": "fix", "description": "bug two", "diff": "diff2"}
    ]
    mock_get_llm.return_value = "chore: consolidated commit"

    # User choices: Consolidate, Use suggested message, Push
    mock_dependencies_commit_feature["safe_prompt"].side_effect = [2, 1] # Consolidate, Use LLM message
    mock_dependencies_commit_feature["safe_confirm"].return_value = True # Push
    mock_dependencies_commit_feature["confirm"].return_value = False # No, don't view full diff

    feature = CommitFeature()
    feature.execute_commit(group=True)

    mock_suggest_groups.assert_called_once()
    # Ensure files are re-staged for consolidated commit if they were reset (though not explicitly reset in this path)
    # The original `current_staged_files_paths` is used. 
    # If the flow always unadds, then re-adds, this might need mock_git_manager.stage_files.assert_called_with(["file1.py", "module/file2.py"])
    
    expected_prompt = PROMPT_COMMIT_MESSAGE.replace("{{diff}}", mock_diff_str).replace("{{guidance}}", "")
    mock_get_llm.assert_called_once_with(expected_prompt)
    mock_git_manager.create_commit.assert_called_once_with("chore: consolidated commit")
    mock_dependencies_commit_feature["push_command"].assert_called_once()


@patch("gitwise.features.commit.get_llm_response")
def test_execute_commit_edit_message(mock_get_llm, mock_git_manager, mock_dependencies_commit_feature):
    mock_get_llm.return_value = "feat: initial LLM message"
    edited_message = "feat: user edited message"

    # User choices: Edit message, then use edited message, then push
    mock_dependencies_commit_feature["safe_prompt"].return_value = 2 # Edit message
    mock_dependencies_commit_feature["confirm"].return_value = False # No full diff view
    
    # Mock tempfile editing process
    with patch("gitwise.features.commit.tempfile.NamedTemporaryFile") as mock_tempfile, \
         patch("gitwise.features.commit.subprocess.run") as mock_subproc_run, \
         patch("builtins.open", MagicMock(read_data=edited_message)) as mock_builtin_open, \
         patch("gitwise.features.commit.os.unlink") as mock_os_unlink: # Patch os.unlink
        
        # Mock the tempfile object
        mock_tf = MagicMock()
        mock_tf.name = "/tmp/tempfile.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_tf
        
        # Simulate successful edit: editor saves and returns 0, then read the "edited_message"
        # The actual read happens via a new `open` call after subprocess.run
        # We need to ensure that when open(mock_tf.name, 'r') is called, it returns `edited_message`.
        # This is tricky because builtins.open is global. A better way is to mock the file read specifically.
        # For simplicity now, we assume subprocess.run works and then safe_confirm is used.

        # To handle the read: when open(mock_tf.name, 'r') is called, make it return the edited_message
        def open_side_effect(path, *args, **kwargs):
            if path == mock_tf.name and args[0] == 'r':
                # Simulate reading the edited file
                file_mock = MagicMock()
                file_mock.read.return_value = edited_message
                file_mock.__enter__.return_value = file_mock # For context manager
                file_mock.__exit__.return_value = None
                return file_mock
            return MagicMock() # Default mock for other open calls
        mock_builtin_open.side_effect = open_side_effect

        mock_dependencies_commit_feature["safe_confirm"].side_effect = [True, True] # Confirm edited message, Confirm push

        feature = CommitFeature()
        feature.execute_commit(group=False)

        mock_subproc_run.assert_called_once_with([os.environ.get("EDITOR", "vi"), mock_tf.name], check=True)
        mock_git_manager.create_commit.assert_called_once_with(edited_message)
        mock_dependencies_commit_feature["push_command"].assert_called_once()
        mock_os_unlink.assert_called_once_with(mock_tf.name) # Verify unlink was called


@patch("gitwise.features.commit.get_llm_response")
def test_execute_commit_handle_uncommitted_changes_stage_all(mock_get_llm, mock_git_manager, mock_dependencies_commit_feature):
    mock_git_manager.get_list_of_unstaged_tracked_files.return_value = ["unstaged.py"] # Has unstaged changes
    mock_git_manager.get_list_of_untracked_files.return_value = ["untracked.txt"] # Has untracked files
    mock_git_manager.get_changed_file_paths_staged.side_effect = [
        ["initial_staged.py"], # Before staging all
        ["initial_staged.py", "unstaged.py", "untracked.txt"] # After staging all
    ]
    mock_get_llm.return_value = "chore: committed all changes"

    # User choices: Stage all, Use LLM message, Push
    mock_dependencies_commit_feature["safe_prompt"].side_effect = [1, 1] # Stage all, Use LLM Message
    mock_dependencies_commit_feature["safe_confirm"].return_value = True # Push
    mock_dependencies_commit_feature["confirm"].return_value = False # No full diff

    feature = CommitFeature()
    feature.execute_commit(group=False)

    mock_git_manager.stage_all.assert_called_once()
    mock_git_manager.create_commit.assert_called_once_with("chore: committed all changes")
    mock_dependencies_commit_feature["push_command"].assert_called_once()
