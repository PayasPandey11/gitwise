import pytest
from unittest.mock import patch, MagicMock

from gitwise.features.push import PushFeature
from gitwise.core.git_manager import GitManager
from gitwise.features.pr import PrFeature # For mocking
from gitwise.config import ConfigError # For testing config error handling

@pytest.fixture
def mock_git_manager_push(): # Renamed for clarity
    with patch("gitwise.features.push.GitManager", spec=GitManager) as mock_gm_constructor:
        mock_gm_instance = mock_gm_constructor.return_value
        mock_gm_instance.get_current_branch.return_value = "feature/test-push"
        mock_gm_instance._run_git_command.return_value = MagicMock(stdout="", returncode=0) # For fetch and tracking check
        mock_gm_instance.push_to_remote.return_value = True
        mock_gm_instance.get_default_remote_branch_name.return_value = "main"
        mock_gm_instance.get_commits_between.return_value = [{"hash": "c1", "message": "feat: pushed this"}] # Has commits to push
        yield mock_gm_instance

@pytest.fixture
def mock_push_dependencies(mock_git_manager_push):
    with patch("gitwise.features.push.components") as mock_components, \
         patch("gitwise.features.push.typer.confirm") as mock_confirm, \
         patch("gitwise.features.push.typer.prompt") as mock_prompt, \
         patch("gitwise.features.push.PrFeature") as mock_pr_feature, \
         patch("gitwise.cli.init.init_command") as mock_init_command:
        # Set up the mocked PrFeature instance to return True when execute_pr is called
        mock_pr_instance = MagicMock()
        mock_pr_instance.execute_pr.return_value = True
        mock_pr_feature.return_value = mock_pr_instance
        
        yield {
            "components": mock_components,
            "confirm": mock_confirm,
            "prompt": mock_prompt,
            "pr_feature": mock_pr_feature,
            "pr_instance": mock_pr_instance,
            "init_command": mock_init_command
        }

def test_push_feature_execute_push_tracking_and_create_pr(mock_git_manager_push, mock_push_dependencies):
    # Simulate branch is already tracking a remote branch
    mock_git_manager_push._run_git_command.side_effect = [
        MagicMock(stdout="", returncode=0), # git fetch origin (first call in execute_push)
        MagicMock(stdout="origin/feature/test-push", returncode=0) # git rev-parse --abbrev-ref --symbolic-full-name @{u} (is tracking)
    ]
    mock_push_dependencies["confirm"].return_value = True # Confirm create PR, Confirm include extras

    feature = PushFeature()
    result = feature.execute_push()

    assert result is True
    mock_git_manager_push.push_to_remote.assert_called_once_with(local_branch="feature/test-push")
    mock_push_dependencies["pr_instance"].execute_pr.assert_called_once_with(
        use_labels=True, use_checklist=True, skip_general_checklist=False, skip_prompts=False, base="main"
    )

def test_push_feature_execute_push_not_tracking_set_upstream_and_pr(mock_git_manager_push, mock_push_dependencies):
    # Simulate branch is not tracking
    mock_git_manager_push._run_git_command.side_effect = [
        MagicMock(stdout="", returncode=0), # git fetch origin
        MagicMock(stderr="fatal: no upstream configured for branch", returncode=128), # Not tracking
        MagicMock(returncode=0) # Successful push --set-upstream
    ]
    mock_push_dependencies["prompt"].return_value = 1  # User chooses "Yes" to set upstream
    mock_push_dependencies["confirm"].return_value = True # Confirm create PR, Confirm include extras

    feature = PushFeature()
    result = feature.execute_push()

    assert result is True
    # push_to_remote is called after the --set-upstream command succeeds
    mock_git_manager_push.push_to_remote.assert_called_once_with(local_branch="feature/test-push")
    # The _run_git_command for "push --set-upstream" is key.
    assert mock_git_manager_push._run_git_command.call_count == 3 # fetch, rev-parse, push --set-upstream
    assert mock_git_manager_push._run_git_command.call_args_list[2][0][0] == \
        ["push", "--set-upstream", "origin", "feature/test-push"]
    # After set-upstream, the flow continues to PR creation
    mock_push_dependencies["pr_instance"].execute_pr.assert_called_once_with(
        use_labels=True, use_checklist=True, skip_general_checklist=False, skip_prompts=False, base="main"
    )

def test_push_feature_no_commits_to_push_but_create_pr_anyway(mock_git_manager_push, mock_push_dependencies):
    mock_git_manager_push.get_commits_between.return_value = [] # No new commits
    mock_push_dependencies["confirm"].side_effect = [True, True] # Yes create PR anyway, Yes include extras

    # Simulate branch is already tracking
    mock_git_manager_push._run_git_command.side_effect = [
        MagicMock(stdout="", returncode=0), # git fetch origin
        MagicMock(stdout="origin/feature/test-push", returncode=0) # is tracking
    ]

    feature = PushFeature()
    result = feature.execute_push()

    assert result is True
    mock_push_dependencies["pr_instance"].execute_pr.assert_called_once()

def test_push_feature_push_fails(mock_git_manager_push, mock_push_dependencies):
    mock_git_manager_push.push_to_remote.return_value = False # Push fails
    # Simulate branch is already tracking
    mock_git_manager_push._run_git_command.side_effect = [
        MagicMock(stdout="", returncode=0), # git fetch origin
        MagicMock(stdout="origin/feature/test-push", returncode=0) # is tracking
    ]

    feature = PushFeature()
    result = feature.execute_push()

    assert result is False
    mock_push_dependencies["pr_instance"].execute_pr.assert_not_called()

@patch("gitwise.features.push.load_config")
def test_push_feature_config_error_and_init(mock_load_config_push, mock_git_manager_push, mock_push_dependencies):
    mock_load_config_push.side_effect = ConfigError("Test config error")
    mock_push_dependencies["confirm"].return_value = True # User confirms to run init

    feature = PushFeature()
    result = feature.execute_push()

    assert result is False # Should not proceed to push if config fails and init is run
    mock_push_dependencies["init_command"].assert_called_once()
    mock_git_manager_push.get_current_branch.assert_not_called() # Execution stops early

def test_push_feature_not_on_branch(mock_git_manager_push, mock_push_dependencies):
    mock_git_manager_push.get_current_branch.return_value = None # Not on a branch
    feature = PushFeature()
    result = feature.execute_push()
    assert result is False
    mock_git_manager_push.push_to_remote.assert_not_called() 