import pytest
from unittest.mock import patch, MagicMock, call

from gitwise.features.add import AddFeature
from gitwise.core.git_manager import GitManager
from gitwise.features.commit import CommitFeature # For mocking
from gitwise.config import ConfigError # For testing config error handling

@pytest.fixture
def mock_git_manager_add(): # Renamed for clarity
    with patch("gitwise.features.add.GitManager") as mock_gm_constructor:
        mock_gm_instance = MagicMock(spec=GitManager)
        mock_gm_constructor.return_value = mock_gm_instance
        mock_gm_instance.get_unstaged_files.return_value = [("M", "file1.py"), ("??", "new_file.txt")]
        mock_gm_instance.stage_all.return_value = True
        mock_gm_instance.stage_files.return_value = True
        mock_gm_instance.get_staged_files.return_value = [("M", "file1.py"), ("A", "new_file.txt")]
        mock_gm_instance.get_staged_diff.return_value = "diff content"
        yield mock_gm_instance

@pytest.fixture
def mock_dependencies_add_feature():
    with patch("gitwise.features.add.get_llm_backend", MagicMock(return_value="offline")), \
         patch("gitwise.features.add.typer.confirm") as mock_confirm, \
         patch("gitwise.features.add.typer.prompt") as mock_prompt, \
         patch("gitwise.features.add.CommitFeature") as mock_commit_feature_constructor, \
         patch("gitwise.features.add.components") as mock_components, \
         patch("gitwise.cli.init.init_command") as mock_init_command: # Mock init_command
        
        # Set up components mocks
        mock_spinner = MagicMock()
        mock_spinner.__enter__ = MagicMock(return_value=mock_spinner)
        mock_spinner.__exit__ = MagicMock(return_value=None)
        mock_components.show_spinner.return_value = mock_spinner
        mock_components.show_section = MagicMock()
        mock_components.show_warning = MagicMock()
        mock_components.show_error = MagicMock()
        mock_components.show_files_table = MagicMock()
        mock_components.show_menu = MagicMock()
        mock_components.show_diff = MagicMock()
        mock_components.console = MagicMock()
        
        mock_commit_feature_instance = MagicMock()
        mock_commit_feature_constructor.return_value = mock_commit_feature_instance

        yield {
            "confirm": mock_confirm,
            "prompt": mock_prompt,
            "commit_feature_instance": mock_commit_feature_instance,
            "init_command": mock_init_command,
            "components": mock_components
        }


def test_add_feature_execute_add_all_and_commit(mock_git_manager_add, mock_dependencies_add_feature):
    mock_dependencies_add_feature["prompt"].return_value = 1 # Choose 'commit' from menu
    
    feature = AddFeature()
    feature.execute_add(files=["."]) # Simulate gitwise add .

    mock_git_manager_add.get_unstaged_files.assert_called_once()
    mock_git_manager_add.stage_all.assert_called_once()
    mock_git_manager_add.get_staged_files.assert_called_once()
    mock_dependencies_add_feature["commit_feature_instance"].execute_commit.assert_called_once()

def test_add_feature_execute_add_specific_files_and_diff_quit(mock_git_manager_add, mock_dependencies_add_feature):
    # User chooses 'diff', then 'quit'
    mock_dependencies_add_feature["prompt"].side_effect = [2, 3] # Diff, then Quit
    files_to_add = ["file1.py", "new_file.txt"]

    with patch("gitwise.features.add.os.path.exists", return_value=True): # Ensure files are seen as existing
        feature = AddFeature()
        feature.execute_add(files=files_to_add)

    mock_git_manager_add.stage_files.assert_has_calls([
        call(["file1.py"]),
        call(["new_file.txt"])
    ], any_order=True)
    mock_git_manager_add.get_staged_diff.assert_called_once()
    mock_dependencies_add_feature["commit_feature_instance"].execute_commit.assert_not_called()

def test_add_feature_no_changes_to_stage(mock_git_manager_add, mock_dependencies_add_feature):
    mock_git_manager_add.get_unstaged_files.return_value = [] # No unstaged files
    
    feature = AddFeature()
    feature.execute_add()
    
    mock_dependencies_add_feature["components"].show_warning.assert_any_call("No changes found to stage.")
    mock_git_manager_add.stage_all.assert_not_called()
    mock_git_manager_add.stage_files.assert_not_called()

def test_add_feature_failed_to_stage_all(mock_git_manager_add, mock_dependencies_add_feature):
    mock_git_manager_add.stage_all.return_value = False # Staging fails
    
    feature = AddFeature()
    feature.execute_add(files=["."])
    
    mock_dependencies_add_feature["components"].show_error.assert_any_call("Failed to stage files")
    mock_dependencies_add_feature["commit_feature_instance"].execute_commit.assert_not_called()

def test_add_feature_no_files_were_staged(mock_git_manager_add, mock_dependencies_add_feature):
    mock_git_manager_add.get_staged_files.return_value = [] # Simulate that staging resulted in no staged files
    # This can happen if `stage_all` was called but there was nothing stageable, or `stage_files` was called with non-existent files.
    
    # To make this scenario more direct for `stage_all`:
    mock_git_manager_add.stage_all.return_value = True # stage_all itself succeeds
    mock_git_manager_add.get_staged_files.return_value = [] # ...but nothing gets staged.

    feature = AddFeature()
    feature.execute_add(files=["."])
    
    mock_dependencies_add_feature["components"].show_warning.assert_any_call("No files were staged.")
    mock_dependencies_add_feature["commit_feature_instance"].execute_commit.assert_not_called()


@patch("gitwise.features.add.load_config") # Patch load_config directly in the add module
def test_add_feature_config_error_and_init(mock_load_config_add, mock_git_manager_add, mock_dependencies_add_feature):
    mock_load_config_add.side_effect = ConfigError("Test config error")
    mock_dependencies_add_feature["confirm"].return_value = True # User confirms to run init

    feature = AddFeature()
    feature.execute_add()

    mock_dependencies_add_feature["init_command"].assert_called_once()
    # Ensure that after init is called, the command doesn't proceed further in this mocked scenario
    mock_git_manager_add.get_unstaged_files.assert_not_called() 

@patch("gitwise.features.add.load_config")
def test_add_feature_config_error_and_no_init(mock_load_config_add_no_init, mock_git_manager_add, mock_dependencies_add_feature):
    mock_load_config_add_no_init.side_effect = ConfigError("Test config error")
    mock_dependencies_add_feature["confirm"].return_value = False # User declines to run init

    feature = AddFeature()
    feature.execute_add()

    mock_dependencies_add_feature["init_command"].assert_not_called()
    mock_git_manager_add.get_unstaged_files.assert_not_called()


# Test for handling a file that is not found
def test_add_feature_stage_specific_file_not_found(mock_git_manager_add, mock_dependencies_add_feature):
    files_to_add = ["non_existent_file.py"]

    # Patch os.path.exists for the add module
    with patch("gitwise.features.add.os.path.exists", return_value=False) as mock_os_exists, \
         patch("gitwise.features.add.load_config"):
        
        feature = AddFeature() # Uses mock_git_manager_add due to fixture
        feature.execute_add(files=files_to_add)

        mock_os_exists.assert_any_call("non_existent_file.py")
        mock_dependencies_add_feature["components"].show_error.assert_any_call("File not found: non_existent_file.py")
        # Optionally, verify that other calls like staging or committing didn't happen
        mock_git_manager_add.stage_files.assert_not_called()

# test_add_feature_execute_add_all_and_commit uses mock_dependencies_add_feature
# ... (other tests can continue to use the full fixture if appropriate) 