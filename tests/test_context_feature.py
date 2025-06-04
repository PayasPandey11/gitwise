"""Tests for the ContextFeature class."""

import json
import os
from unittest.mock import MagicMock, patch, mock_open

import pytest

from gitwise.features.context import ContextFeature

MOCK_REPO_PATH = "/test/repo"


@pytest.fixture
def mock_git_manager():
    """Create a mock GitManager for testing."""
    mock = MagicMock()
    mock.repo_path = MOCK_REPO_PATH
    mock.get_current_branch.return_value = "feature/TEST-123-example-branch"
    return mock


@pytest.fixture
def context_feature_instance(mock_git_manager):
    """Create a ContextFeature instance with a mock GitManager."""
    with patch("gitwise.features.context.git_manager", mock_git_manager):
        yield ContextFeature()


def test_get_context_dir_path(context_feature_instance):
    """Test that get_context_dir_path returns the correct path."""
    expected_path = os.path.join(MOCK_REPO_PATH, ".git", "gitwise", "context")
    assert context_feature_instance.get_context_dir_path() == expected_path


def test_get_branch_context_path(context_feature_instance):
    """Test that get_branch_context_path returns the correct path for a branch."""
    expected_path = os.path.join(
        MOCK_REPO_PATH,
        ".git",
        "gitwise",
        "context",
        "feature_TEST-123-example-branch.json"
    )
    assert context_feature_instance.get_branch_context_path() == expected_path


def test_get_branch_context_path_custom_branch(context_feature_instance):
    """Test that get_branch_context_path works with a specified branch name."""
    expected_path = os.path.join(
        MOCK_REPO_PATH,
        ".git",
        "gitwise",
        "context",
        "custom_branch.json"
    )
    assert context_feature_instance.get_branch_context_path("custom/branch") == expected_path


@patch("os.path.exists")
@patch("builtins.open", new_callable=mock_open, read_data='{"user_set_context": "Test context"}')
def test_get_context_existing(mock_file_open, mock_exists, context_feature_instance):
    """Test get_context when the context file exists."""
    mock_exists.return_value = True
    
    context = context_feature_instance.get_context()
    
    assert context["user_set_context"] == "Test context"
    mock_exists.assert_called_once()
    mock_file_open.assert_called_once()


@patch("os.path.exists")
def test_get_context_nonexistent(mock_exists, context_feature_instance):
    """Test get_context when the context file doesn't exist."""
    mock_exists.return_value = False
    
    context = context_feature_instance.get_context()
    
    # Should return default context
    assert "user_set_context" in context
    assert "parsed_ticket_id" in context
    assert "parsed_keywords" in context
    assert "last_updated" in context
    
    assert context["user_set_context"] == ""
    mock_exists.assert_called_once()


@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
@patch("json.dump")
def test_set_context(mock_json_dump, mock_file_open, mock_makedirs, context_feature_instance):
    """Test set_context."""
    # Mock get_context to return a default context
    with patch.object(
        context_feature_instance, 
        "get_context", 
        return_value=context_feature_instance._create_default_context()
    ):
        result = context_feature_instance.set_context("New test context")
        
        assert result is True
        mock_makedirs.assert_called_once()
        mock_file_open.assert_called_once()
        mock_json_dump.assert_called_once()
        
        # Check that the context was updated correctly
        context_arg = mock_json_dump.call_args[0][0]
        assert context_arg["user_set_context"] == "New test context"


def test_parse_branch_context(context_feature_instance):
    """Test parse_branch_context extracts ticket ID and keywords correctly."""
    # Mock the get_context and _write_context methods
    with patch.object(
        context_feature_instance, 
        "get_context", 
        return_value=context_feature_instance._create_default_context()
    ), patch.object(
        context_feature_instance,
        "_write_context",
        return_value=True
    ):
        # Call the method
        result = context_feature_instance.parse_branch_context()
        
        # Check the result
        assert result is True
        
        # Check that _write_context was called with correct arguments
        context_arg = context_feature_instance._write_context.call_args[0][0]
        assert context_arg["parsed_ticket_id"] == "TEST-123"
        assert "example" in context_arg["parsed_keywords"]
        assert "branch" in context_arg["parsed_keywords"]


def test_get_context_for_ai_prompt(context_feature_instance):
    """Test get_context_for_ai_prompt formats context correctly."""
    # Test with user-set context
    with patch.object(
        context_feature_instance,
        "get_context",
        return_value={
            "user_set_context": "Working on login feature",
            "parsed_ticket_id": "TEST-123",
            "parsed_keywords": ["login", "feature"],
            "last_updated": 12345
        }
    ):
        prompt_text = context_feature_instance.get_context_for_ai_prompt()
        assert "Working on login feature" in prompt_text
        assert "TEST-123" not in prompt_text  # Should not include ticket ID when user context exists
    
    # Test with ticket ID only
    with patch.object(
        context_feature_instance,
        "get_context",
        return_value={
            "user_set_context": "",
            "parsed_ticket_id": "TEST-123",
            "parsed_keywords": ["login", "feature"],
            "last_updated": 12345
        }
    ):
        prompt_text = context_feature_instance.get_context_for_ai_prompt()
        assert "TEST-123" in prompt_text
    
    # Test with keywords only
    with patch.object(
        context_feature_instance,
        "get_context",
        return_value={
            "user_set_context": "",
            "parsed_ticket_id": "",
            "parsed_keywords": ["login", "feature"],
            "last_updated": 12345
        }
    ):
        prompt_text = context_feature_instance.get_context_for_ai_prompt()
        assert "login" in prompt_text
        assert "feature" in prompt_text 