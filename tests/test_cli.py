import pytest
from unittest.mock import patch, MagicMock, call
import subprocess
import sys
import os

from typer.testing import CliRunner

from gitwise.cli import app # The Typer app
from gitwise.cli import init # Import the init module for direct testing of init_command
from gitwise.core.git_manager import GitManager # For mocking
from gitwise.config import ConfigError, get_local_config_path, get_global_config_path, write_config

runner = CliRunner()

@pytest.fixture
def mock_git_manager_cli(): # For init command that uses GitManager
    with patch("gitwise.cli.init.GitManager", spec=GitManager) as mock_gm_constructor:
        mock_gm_instance = mock_gm_constructor.return_value
        mock_gm_instance.is_git_repo.return_value = True # Default to being in a git repo
        yield mock_gm_instance

@pytest.fixture
def mock_cli_dependencies(mock_git_manager_cli): # Combined fixture for CLI tests
    with patch("gitwise.cli.init.typer.prompt") as mock_prompt, \
         patch("gitwise.cli.init.typer.echo"), \
         patch("gitwise.cli.init.typer.confirm") as mock_confirm, \
         patch("gitwise.cli.init.config_exists") as mock_config_exists, \
         patch("gitwise.cli.init.load_config") as mock_load_config, \
         patch("gitwise.cli.init.write_config") as mock_write_config, \
         patch("gitwise.cli.init.check_ollama_running", return_value=True), \
         patch("gitwise.cli.init.check_offline_model", return_value=True), \
         patch("gitwise.cli.add.AddFeature") as mock_add_feature_class, \
         patch("gitwise.cli.CommitFeature") as mock_commit_feature_class, \
         patch("gitwise.cli.PushFeature") as mock_push_feature_class, \
         patch("gitwise.cli.PrFeature") as mock_pr_feature_class, \
         patch("gitwise.cli.ChangelogFeature") as mock_changelog_feature_class, \
         patch("gitwise.cli.check_and_install_offline_deps") as mock_check_install_deps, \
         patch("gitwise.llm.download.download_offline_model") as mock_download_offline_model, \
         patch("gitwise.cli.subprocess.Popen") as mock_popen: # For 'gitwise git' command
        
        # Setup for 'gitwise git' command mock
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["output line 1\n", "output line 2\n", ""]
        mock_process.poll.return_value = 0 # Success
        mock_process.stderr.read.return_value = ""
        mock_popen.return_value = mock_process

        yield {
            "prompt": mock_prompt,
            "confirm": mock_confirm,
            "config_exists": mock_config_exists,
            "load_config": mock_load_config,
            "write_config": mock_write_config,
            "add_feature_instance": mock_add_feature_class.return_value,
            "commit_feature_instance": mock_commit_feature_class.return_value,
            "push_feature_instance": mock_push_feature_class.return_value,
            "pr_feature_instance": mock_pr_feature_class.return_value,
            "changelog_feature_instance": mock_changelog_feature_class.return_value,
            "check_install_deps": mock_check_install_deps,
            "download_offline_model": mock_download_offline_model,
            "popen": mock_popen,
            "git_manager": mock_git_manager_cli
        }

# --- Tests for 'gitwise init' command ---
def test_init_command_new_config_ollama_local(mock_cli_dependencies):
    mock_cli_dependencies["config_exists"].return_value = False # No existing config
    # Prompts: backend choice (1=ollama), ollama model, apply to repo only (yes)
    mock_cli_dependencies["prompt"].side_effect = ["1", "custom-ollama-model"]
    mock_cli_dependencies["confirm"].return_value = True # Apply to repo only
    mock_cli_dependencies["write_config"].return_value = "/test/repo/.gitwise/config.json"

    # Directly call the init_command function from the init module
    init.init_command()

    expected_config = {"llm_backend": "ollama", "ollama_model": "custom-ollama-model"}
    mock_cli_dependencies["write_config"].assert_called_once_with(expected_config, global_config=False)

def test_init_command_overwrite_config_online_global(mock_cli_dependencies):
    mock_cli_dependencies["config_exists"].return_value = True
    mock_cli_dependencies["load_config"].return_value = {"llm_backend": "old_backend"}
    # Prompts: overwrite (o), backend choice (3=online), API key, OpenRouter model (default), apply globally (yes, confirm not repo only)
    mock_cli_dependencies["prompt"].side_effect = ["o", "3", "test_api_key", "anthropic/claude-3-haiku"]
    # Confirmations: 
    # 1. Use env key for OPENROUTER_API_KEY? (No)
    # 2. Set a specific OpenRouter model? (No - use default)
    # 3. If not in git repo: Continue and apply config globally? (Yes)
    # 4. Apply settings to this repository only? (No - make it global)
    mock_cli_dependencies["confirm"].side_effect = [False, False, True, False] 
    mock_cli_dependencies["git_manager"].is_git_repo.return_value = False # Simulate not in a git repo
    mock_cli_dependencies["write_config"].return_value = "/home/user/.gitwise/config.json"

    with patch.dict(os.environ, {}, clear=True): # Ensure OPENROUTER_API_KEY is not in env
        init.init_command()

    expected_config = {
        "llm_backend": "online", 
        "openrouter_api_key": "test_api_key", 
        "openrouter_model": "anthropic/claude-3-haiku"
    }
    mock_cli_dependencies["write_config"].assert_called_once_with(expected_config, global_config=True)

def test_init_command_merge_config_offline_local(mock_cli_dependencies):
    mock_cli_dependencies["config_exists"].return_value = True
    existing_config = {"existing_key": "value1", "llm_backend": "online"}
    mock_cli_dependencies["load_config"].return_value = existing_config
    # Prompts: merge (m), backend choice (2=offline), apply to repo only (yes)
    mock_cli_dependencies["prompt"].side_effect = ["m", "2"]
    mock_cli_dependencies["confirm"].return_value = True # Apply to repo only
    mock_cli_dependencies["write_config"].return_value = "/test/repo/.gitwise/config.json"

    init.init_command()

    expected_config = {"existing_key": "value1", "llm_backend": "offline"} 
    mock_cli_dependencies["write_config"].assert_called_once_with(expected_config, global_config=False)

# --- Test CLI command invocations using CliRunner ---
# These tests check if the Typer app correctly routes commands to feature classes.

def test_cli_add_invokes_add_command_cli(mock_cli_dependencies):
    result = runner.invoke(app, ["add", "file1.py"])
    assert result.exit_code == 0
    mock_cli_dependencies["add_feature_instance"].execute_add.assert_called_once_with(["file1.py"])

def test_cli_commit_invokes_execute_commit(mock_cli_dependencies):
    result = runner.invoke(app, ["commit", "--group"])
    assert result.exit_code == 0
    mock_cli_dependencies["commit_feature_instance"].execute_commit.assert_called_once_with(group=True)

def test_cli_push_invokes_execute_push(mock_cli_dependencies):
    result = runner.invoke(app, ["push"])
    assert result.exit_code == 0
    mock_cli_dependencies["push_feature_instance"].execute_push.assert_called_once()

def test_cli_pr_invokes_execute_pr(mock_cli_dependencies):
    result = runner.invoke(app, ["pr", "--labels", "--base", "develop"])
    assert result.exit_code == 0
    mock_cli_dependencies["pr_feature_instance"].execute_pr.assert_called_once_with(
        use_labels=True, use_checklist=False, skip_general_checklist=False, 
        title=None, base="develop", draft=False, skip_prompts=False
    )

def test_cli_changelog_invokes_execute_changelog(mock_cli_dependencies):
    result = runner.invoke(app, ["changelog", "--version", "v1.2.3"])
    assert result.exit_code == 0
    mock_cli_dependencies["changelog_feature_instance"].execute_changelog.assert_called_once_with(
        version="v1.2.3", output_file=None, format_output="markdown", auto_update=False
    )

def test_cli_offline_model_cmd_invokes_download(mock_cli_dependencies):
    # This command now also calls check_and_install_offline_deps first
    result = runner.invoke(app, ["offline-model"])
    assert result.exit_code == 0 # Exits with 0 after running
    mock_cli_dependencies["check_install_deps"].assert_called_once() 
    mock_cli_dependencies["download_offline_model"].assert_called_once()

# Test 'gitwise git' command passthrough
def test_cli_git_passthrough_success(mock_cli_dependencies):
    result = runner.invoke(app, ["git", "status", "-sb"])
    assert result.exit_code == 0
    mock_cli_dependencies["popen"].assert_called_once_with(
        ["git", "status", "-sb"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    assert "output line 1" in result.stdout
    assert "output line 2" in result.stdout
    assert "Git command executed successfully" in result.stdout

def test_cli_git_passthrough_failure(mock_cli_dependencies):
    mock_process_fail = MagicMock()
    mock_process_fail.stdout.readline.side_effect = ["error output\n", ""]
    mock_process_fail.poll.return_value = 1 # Failure
    mock_process_fail.stderr.read.return_value = "git error details"
    mock_cli_dependencies["popen"].return_value = mock_process_fail

    result = runner.invoke(app, ["git", "bad-command"])
    assert result.exit_code == 1
    assert "error output" in result.stdout
    assert "Git command failed" in result.stdout
    assert "git error details" in result.stdout # Check stderr is printed

def test_cli_git_passthrough_no_command(mock_cli_dependencies):
    result = runner.invoke(app, ["git"])
    assert result.exit_code == 1
    assert "No git command provided" in result.stdout
    mock_cli_dependencies["popen"].assert_not_called()

# Test check_and_install_offline_deps (from cli/__init__.py, imported by app)
@patch("gitwise.cli.sys.exit") # To prevent test from exiting
@patch("gitwise.cli.subprocess.run")
@patch("builtins.input")
@patch("gitwise.llm.download.download_offline_model")
def test_check_and_install_offline_deps_installs(mock_download, mock_input, mock_subprocess_run, mock_sys_exit):
    # Simulate missing 'transformers' but 'torch' is present
    with patch.dict(sys.modules, {'transformers': None, 'torch': MagicMock()}):
        mock_input.return_value = 'y' # User confirms install
        # We call a command that triggers this check, e.g. offline-model
        # but it's easier to call the function directly for this unit test if it were standalone.
        # Since it's called at import time in the original and now by offline-model command,
        # we'll test via a command that calls it.
        runner.invoke(app, ["offline-model"])
    
    mock_input.assert_called_once()
    mock_subprocess_run.assert_called_once_with(
        [sys.executable, "-m", "pip", "install", "gitwise[offline]"]
    )
    mock_sys_exit.assert_called_with(1) # Should exit after attempting install

@patch("gitwise.cli.sys.exit")
@patch("gitwise.cli.subprocess.run")
@patch("builtins.input")
@patch("gitwise.llm.download.download_offline_model")
def test_check_and_install_offline_deps_no_install(mock_download, mock_input, mock_subprocess_run, mock_sys_exit):
    with patch.dict(sys.modules, {'transformers': None, 'torch': None}): # Both missing
        mock_input.return_value = 'n' # User declines install
        runner.invoke(app, ["offline-model"]) # offline-model calls the check
        
    mock_input.assert_called_once()
    mock_subprocess_run.assert_not_called()
    mock_sys_exit.assert_called_with(1) # Should still exit

@patch("gitwise.cli.sys.exit")
def test_check_and_install_offline_deps_all_present(mock_sys_exit):
    # Ensure both are mocked as present
    with patch.dict(sys.modules, {'transformers': MagicMock(), 'torch': MagicMock()}):
        # Call a command that would trigger it, e.g., offline-model
        # The check_and_install_offline_deps is part of the offline_model_cmd in cli
        with patch("gitwise.llm.download.download_offline_model") as mock_download: # prevent actual download
            runner.invoke(app, ["offline-model"])
            mock_download.assert_called_once() # Make sure the actual command part ran
    
    mock_sys_exit.assert_called_with(0) # Should exit with 0 if deps are present and command runs fully 