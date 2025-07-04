"""Tests for CommitRulesFeature class."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import json

from gitwise.features.commit_rules import CommitRulesFeature


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "commit_rules": {
            "style": "conventional",
            "format": "{type}({scope}): {description}",
            "subject_max_length": 50,
            "body_wrap_length": 72,
            "allowed_types": ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore"],
            "allowed_scopes": [],
            "rules": {
                "capitalize": True,
                "imperative_mood": True,
                "no_period": True,
                "require_type": True,
                "require_scope": False,
                "allow_multiline": True,
                "require_body": False
            },
            "custom_prompt_additions": ""
        }
    }


@pytest.fixture
def mock_custom_config():
    """Mock custom configuration for testing."""
    return {
        "commit_rules": {
            "style": "custom",
            "format": "[{type}] {description}",
            "subject_max_length": 80,
            "body_wrap_length": 72,
            "allowed_types": ["feature", "bugfix", "docs", "refactor"],
            "allowed_scopes": [],
            "rules": {
                "capitalize": True,
                "imperative_mood": False,
                "no_period": True,
                "require_type": True,
                "require_scope": False,
                "allow_multiline": True,
                "require_body": False
            },
            "custom_prompt_additions": "Use clear, descriptive language"
        }
    }


@pytest.fixture
def commit_rules_feature(mock_config):
    """CommitRulesFeature instance with mocked config."""
    with patch('gitwise.features.commit_rules.load_config', return_value=mock_config):
        return CommitRulesFeature()


@pytest.fixture
def custom_commit_rules_feature(mock_custom_config):
    """CommitRulesFeature instance with custom rules."""
    with patch('gitwise.features.commit_rules.load_config', return_value=mock_custom_config):
        return CommitRulesFeature()


class TestCommitRulesFeatureInitialization:
    """Test CommitRulesFeature initialization and basic methods."""

    def test_init_with_config(self, commit_rules_feature):
        """Test initialization with existing config."""
        assert commit_rules_feature.get_active_style() == "conventional"
        assert commit_rules_feature.rules["format"] == "{type}({scope}): {description}"

    def test_init_with_default_rules(self):
        """Test initialization with default rules when no config exists."""
        with patch('gitwise.features.commit_rules.load_config', return_value={}):
            feature = CommitRulesFeature()
            assert feature.get_active_style() == "conventional"
            assert feature.rules["style"] == "conventional"

    def test_get_default_rules(self, commit_rules_feature):
        """Test _get_default_rules returns correct structure."""
        default_rules = commit_rules_feature._get_default_rules()
        
        assert default_rules["style"] == "conventional"
        assert default_rules["format"] == "{type}({scope}): {description}"
        assert default_rules["subject_max_length"] == 50
        assert "feat" in default_rules["allowed_types"]
        assert "fix" in default_rules["allowed_types"]
        assert default_rules["rules"]["capitalize"] is True
        assert default_rules["rules"]["imperative_mood"] is True


class TestCommitRulesFeatureValidation:
    """Test validation methods."""

    def test_validate_format_valid(self, commit_rules_feature):
        """Test validate_format with valid format strings."""
        valid_formats = [
            "{description}",
            "[{type}] {description}",
            "{type}: {description}",
            "{type}({scope}): {description}",
            "{emoji} {type}: {description}",
            "{prefix} {type}: {description} - {ticket}"
        ]
        
        for format_str in valid_formats:
            valid, error = commit_rules_feature.validate_format(format_str)
            assert valid is True, f"Format '{format_str}' should be valid: {error}"
            assert error == ""

    def test_validate_format_invalid(self, commit_rules_feature):
        """Test validate_format with invalid format strings."""
        invalid_formats = [
            "",  # Empty string
            "No placeholders",  # No {description}
            "{type}: something",  # Missing {description}
            "{invalid_placeholder}: {description}",  # Invalid placeholder
            "{type}: {description} {unknown}"  # Unknown placeholder
        ]
        
        for format_str in invalid_formats:
            valid, error = commit_rules_feature.validate_format(format_str)
            assert valid is False, f"Format '{format_str}' should be invalid"
            assert error != ""

    def test_validate_message_basic(self, commit_rules_feature):
        """Test basic message validation."""
        valid_messages = [
            "Feat: add new feature",
            "Fix: resolve bug in authentication",
            "Docs: update README"
        ]
        
        for message in valid_messages:
            valid, error = commit_rules_feature.validate_message(message)
            assert valid is True, f"Message '{message}' should be valid: {error}"

    def test_validate_message_too_long(self, commit_rules_feature):
        """Test validation of messages that are too long."""
        long_message = "feat: " + "a" * 100  # Way over 50 char limit
        
        valid, error = commit_rules_feature.validate_message(long_message)
        assert valid is False
        assert "too long" in error.lower()

    def test_validate_message_empty(self, commit_rules_feature):
        """Test validation of empty messages."""
        valid, error = commit_rules_feature.validate_message("")
        assert valid is False
        assert "empty" in error.lower()

    def test_validate_message_capitalization(self, commit_rules_feature):
        """Test capitalization validation."""
        valid, error = commit_rules_feature.validate_message("lowercase message")
        assert valid is False
        assert "capitalized" in error.lower()

    def test_validate_message_period(self, commit_rules_feature):
        """Test period validation."""
        valid, error = commit_rules_feature.validate_message("Feat: add feature.")
        assert valid is False
        assert "period" in error.lower()


class TestCommitRulesFeaturePromptGeneration:
    """Test prompt generation for AI."""

    def test_generate_prompt_conventional(self, commit_rules_feature):
        """Test prompt generation for conventional style."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        
        with patch('gitwise.prompts.PROMPT_COMMIT_MESSAGE', 
                   "Test prompt {diff} {guidance}") as mock_prompt:
            prompt = commit_rules_feature.generate_prompt(diff, "context")
            assert "Test prompt" in prompt
            assert diff in prompt
            assert "context" in prompt

    def test_generate_prompt_custom(self, custom_commit_rules_feature):
        """Test prompt generation for custom style."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        context = "Adding hello world example"
        
        prompt = custom_commit_rules_feature.generate_prompt(diff, context)
        
        assert "[{type}] {description}" in prompt
        assert "Maximum subject length: 80" in prompt
        assert "feature, bugfix, docs, refactor" in prompt  # Space after comma
        assert "Capitalize the first letter" in prompt
        assert "No period at the end" in prompt
        assert "Use clear, descriptive language" in prompt
        assert diff in prompt
        assert context in prompt


class TestCommitRulesFeatureConfiguration:
    """Test configuration management methods."""

    def test_get_active_style(self, commit_rules_feature, custom_commit_rules_feature):
        """Test get_active_style returns correct style."""
        assert commit_rules_feature.get_active_style() == "conventional"
        assert custom_commit_rules_feature.get_active_style() == "custom"

    def test_get_commit_rules(self, commit_rules_feature):
        """Test get_commit_rules returns copy of rules."""
        rules = commit_rules_feature.get_commit_rules()
        assert rules["style"] == "conventional"
        
        # Modify returned rules shouldn't affect original
        rules["style"] = "custom"
        assert commit_rules_feature.get_active_style() == "conventional"

    @patch('gitwise.features.commit_rules.save_config')
    def test_save_rules(self, mock_save_config, commit_rules_feature):
        """Test save_rules saves configuration."""
        mock_save_config.return_value = None
        new_rules = {"style": "custom", "format": "[{type}] {description}"}
        
        result = commit_rules_feature.save_rules(new_rules)
        
        assert result is True
        mock_save_config.assert_called_once()
        assert commit_rules_feature.rules == new_rules

    def test_reset_to_conventional(self, commit_rules_feature):
        """Test reset_to_conventional resets to conventional style."""
        with patch.object(commit_rules_feature, 'save_rules', return_value=True) as mock_save:
            result = commit_rules_feature.reset_to_conventional()
            
            assert result is True
            mock_save.assert_called_once()
            saved_rules = mock_save.call_args[0][0]
            assert saved_rules["style"] == "conventional"

    def test_switch_style(self, commit_rules_feature):
        """Test switch_style changes style."""
        with patch.object(commit_rules_feature, 'save_rules', return_value=True) as mock_save:
            result = commit_rules_feature.switch_style("custom")
            
            assert result is True
            mock_save.assert_called_once()
            saved_rules = mock_save.call_args[0][0]
            assert saved_rules["style"] == "custom"

    def test_switch_style_invalid(self, commit_rules_feature):
        """Test switch_style rejects invalid styles."""
        result = commit_rules_feature.switch_style("invalid")
        assert result is False

    def test_update_format(self, commit_rules_feature):
        """Test update_format updates format string."""
        with patch.object(commit_rules_feature, 'save_rules', return_value=True) as mock_save:
            result = commit_rules_feature.update_format("[{type}] {description}")
            
            assert result is True
            mock_save.assert_called_once()
            saved_rules = mock_save.call_args[0][0]
            assert saved_rules["format"] == "[{type}] {description}"
            assert saved_rules["style"] == "custom"

    def test_update_format_invalid(self, commit_rules_feature):
        """Test update_format rejects invalid formats."""
        with patch('gitwise.features.commit_rules.components.show_error') as mock_show_error:
            result = commit_rules_feature.update_format("invalid format")
            
            assert result is False
            mock_show_error.assert_called_once() 