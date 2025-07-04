"""Tests for config-commit CLI command functionality."""

import pytest
from unittest.mock import MagicMock, patch
import typer
from typer.testing import CliRunner

from gitwise.cli.commit_config import config_commit_command
from gitwise.features.commit_rules import CommitRulesFeature


@pytest.fixture
def cli_runner():
    """CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_commit_rules_feature():
    """Mock CommitRulesFeature for testing."""
    with patch('gitwise.cli.commit_config.CommitRulesFeature') as mock_class:
        mock_feature = MagicMock(spec=CommitRulesFeature)
        mock_class.return_value = mock_feature
        yield mock_feature


@pytest.fixture
def mock_components():
    """Mock UI components."""
    with patch('gitwise.cli.commit_config.components') as mock_comp:
        mock_comp.show_success = MagicMock()
        mock_comp.show_error = MagicMock()
        mock_comp.console = MagicMock()
        yield mock_comp


class TestConfigCommitCommand:
    """Test config-commit CLI command."""

    def test_show_current_rules_conventional(self, mock_commit_rules_feature, mock_components):
        """Test showing current rules in conventional style."""
        # Setup mocks
        mock_commit_rules_feature.get_commit_rules.return_value = {
            "style": "conventional",
            "format": "{type}({scope}): {description}"
        }
        mock_commit_rules_feature.get_active_style.return_value = "conventional"
        
        # Run command with show option (using named parameters properly)
        config_commit_command(show=True, setup=False, style=None, format_str=None, reset=False)
        
        # Verify calls
        mock_commit_rules_feature.get_commit_rules.assert_called_once()
        mock_commit_rules_feature.get_active_style.assert_called_once()
        mock_components.console.print.assert_called()

    def test_show_current_rules_custom(self, mock_commit_rules_feature, mock_components):
        """Test showing current rules in custom style."""
        # Setup mocks
        mock_rules = {
            "style": "custom",
            "format": "[{type}] {description}",
            "subject_max_length": 80,
            "allowed_types": ["feature", "bugfix"]
        }
        mock_commit_rules_feature.get_commit_rules.return_value = mock_rules
        mock_commit_rules_feature.get_active_style.return_value = "custom"
        
        # Run command with show option
        config_commit_command(show=True, setup=False, style=None, format_str=None, reset=False)
        
        # Verify calls
        mock_commit_rules_feature.get_commit_rules.assert_called_once()
        mock_commit_rules_feature.get_active_style.assert_called_once()
        mock_commit_rules_feature._show_rules_summary.assert_called_once_with(mock_rules)

    def test_reset_to_conventional(self, mock_commit_rules_feature, mock_components):
        """Test reset to conventional commits."""
        mock_commit_rules_feature.reset_to_conventional.return_value = True
        
        with patch('gitwise.cli.commit_config.typer.confirm', return_value=True):
            config_commit_command(show=False, setup=False, style=None, format_str=None, reset=True)
        
        mock_commit_rules_feature.reset_to_conventional.assert_called_once()
        mock_components.show_success.assert_called_once()

    def test_reset_cancelled(self, mock_commit_rules_feature, mock_components):
        """Test reset cancelled by user."""
        with patch('gitwise.cli.commit_config.typer.confirm', return_value=False):
            config_commit_command(show=False, setup=False, style=None, format_str=None, reset=True)
        
        mock_commit_rules_feature.reset_to_conventional.assert_not_called()
        mock_components.show_success.assert_not_called()

    def test_reset_failure(self, mock_commit_rules_feature, mock_components):
        """Test reset failure."""
        mock_commit_rules_feature.reset_to_conventional.return_value = False
        
        with patch('gitwise.cli.commit_config.typer.confirm', return_value=True):
            config_commit_command(show=False, setup=False, style=None, format_str=None, reset=True)
        
        mock_commit_rules_feature.reset_to_conventional.assert_called_once()
        mock_components.show_error.assert_called_once()

    def test_interactive_setup_success(self, mock_commit_rules_feature, mock_components):
        """Test interactive setup success."""
        mock_rules = {"style": "custom", "format": "[{type}] {description}"}
        mock_commit_rules_feature.setup_interactive.return_value = mock_rules
        mock_commit_rules_feature.save_rules.return_value = True
        
        config_commit_command(show=False, setup=True, style=None, format_str=None, reset=False)
        
        mock_commit_rules_feature.setup_interactive.assert_called_once()
        mock_commit_rules_feature.save_rules.assert_called_once_with(mock_rules)
        mock_components.show_success.assert_called_once()

    def test_interactive_setup_failure(self, mock_commit_rules_feature, mock_components):
        """Test interactive setup failure."""
        mock_rules = {"style": "custom", "format": "[{type}] {description}"}
        mock_commit_rules_feature.setup_interactive.return_value = mock_rules
        mock_commit_rules_feature.save_rules.return_value = False
        
        config_commit_command(show=False, setup=True, style=None, format_str=None, reset=False)
        
        mock_commit_rules_feature.setup_interactive.assert_called_once()
        mock_commit_rules_feature.save_rules.assert_called_once_with(mock_rules)
        mock_components.show_error.assert_called_once()

    def test_switch_style_conventional(self, mock_commit_rules_feature, mock_components):
        """Test switching to conventional style."""
        mock_commit_rules_feature.switch_style.return_value = True
        
        config_commit_command(show=False, setup=False, style="conventional", format_str=None, reset=False)
        
        mock_commit_rules_feature.switch_style.assert_called_once_with("conventional")
        mock_components.show_success.assert_called_once()

    def test_switch_style_custom(self, mock_commit_rules_feature, mock_components):
        """Test switching to custom style."""
        mock_commit_rules_feature.switch_style.return_value = True
        
        config_commit_command(show=False, setup=False, style="custom", format_str=None, reset=False)
        
        mock_commit_rules_feature.switch_style.assert_called_once_with("custom")
        mock_components.show_success.assert_called_once()

    def test_switch_style_invalid(self, mock_commit_rules_feature, mock_components):
        """Test switching to invalid style."""
        config_commit_command(show=False, setup=False, style="invalid", format_str=None, reset=False)
        
        mock_commit_rules_feature.switch_style.assert_not_called()
        mock_components.show_error.assert_called_once()

    def test_switch_style_failure(self, mock_commit_rules_feature, mock_components):
        """Test style switch failure."""
        mock_commit_rules_feature.switch_style.return_value = False
        
        config_commit_command(show=False, setup=False, style="conventional", format_str=None, reset=False)
        
        mock_commit_rules_feature.switch_style.assert_called_once_with("conventional")
        mock_components.show_error.assert_called_once()

    def test_update_format_success(self, mock_commit_rules_feature, mock_components):
        """Test updating format string successfully."""
        mock_commit_rules_feature.update_format.return_value = True
        format_string = "[{type}] {description}"
        
        config_commit_command(show=False, setup=False, style=None, format_str=format_string, reset=False)
        
        mock_commit_rules_feature.update_format.assert_called_once_with(format_string)
        mock_components.show_success.assert_called_once()

    def test_update_format_failure(self, mock_commit_rules_feature, mock_components):
        """Test updating format string failure."""
        mock_commit_rules_feature.update_format.return_value = False
        format_string = "invalid format"
        
        config_commit_command(show=False, setup=False, style=None, format_str=format_string, reset=False)
        
        mock_commit_rules_feature.update_format.assert_called_once_with(format_string)
        mock_components.show_error.assert_called_once()

    def test_default_behavior_shows_rules(self, mock_commit_rules_feature, mock_components):
        """Test that default behavior shows current rules."""
        mock_commit_rules_feature.get_commit_rules.return_value = {
            "style": "conventional",
            "format": "{type}({scope}): {description}"
        }
        mock_commit_rules_feature.get_active_style.return_value = "conventional"
        
        # Call with no options (default behavior)
        config_commit_command(show=False, setup=False, style=None, format_str=None, reset=False)
        
        # Should show current rules
        mock_commit_rules_feature.get_commit_rules.assert_called_once()
        mock_commit_rules_feature.get_active_style.assert_called_once()
        mock_components.console.print.assert_called()

    def test_exception_handling(self, mock_commit_rules_feature, mock_components):
        """Test exception handling in CLI command."""
        mock_commit_rules_feature.get_commit_rules.side_effect = Exception("Test error")
        
        with pytest.raises(typer.Exit):
            config_commit_command(show=False, setup=False, style=None, format_str=None, reset=False)
        
        mock_components.show_error.assert_called_once()

    def test_multiple_options_precedence(self, mock_commit_rules_feature, mock_components):
        """Test that options are handled in correct precedence order."""
        mock_commit_rules_feature.reset_to_conventional.return_value = True
        
        with patch('gitwise.cli.commit_config.typer.confirm', return_value=True):
            # Reset should take precedence over other options
            config_commit_command(show=False, setup=True, style="custom", format_str=None, reset=True)
        
        # Only reset should be called
        mock_commit_rules_feature.reset_to_conventional.assert_called_once()
        mock_commit_rules_feature.setup_interactive.assert_not_called()
        mock_commit_rules_feature.switch_style.assert_not_called()

    def test_setup_then_style_precedence(self, mock_commit_rules_feature, mock_components):
        """Test that setup takes precedence over style when both provided."""
        mock_rules = {"style": "custom", "format": "[{type}] {description}"}
        mock_commit_rules_feature.setup_interactive.return_value = mock_rules
        mock_commit_rules_feature.save_rules.return_value = True
        
        config_commit_command(show=False, setup=True, style="conventional", format_str=None, reset=False)
        
        # Setup should be called, style should not
        mock_commit_rules_feature.setup_interactive.assert_called_once()
        mock_commit_rules_feature.switch_style.assert_not_called()

    def test_style_then_format_precedence(self, mock_commit_rules_feature, mock_components):
        """Test that style takes precedence over format when both provided."""
        mock_commit_rules_feature.switch_style.return_value = True
        
        config_commit_command(show=False, setup=False, style="custom", format_str="[{type}] {description}", reset=False)
        
        # Style should be called, format should not
        mock_commit_rules_feature.switch_style.assert_called_once_with("custom")
        mock_commit_rules_feature.update_format.assert_not_called()


class TestConfigCommitCommandIntegration:
    """Integration tests for config-commit CLI command."""
    
    def test_real_feature_integration(self, mock_components):
        """Test integration with real CommitRulesFeature (mocked config)."""
        mock_config = {
            "commit_rules": {
                "style": "conventional",
                "format": "{type}({scope}): {description}",
                "subject_max_length": 50
            }
        }
        
        with patch('gitwise.features.commit_rules.load_config', return_value=mock_config):
            # This should work without throwing exceptions
            config_commit_command(show=True, setup=False, style=None, format_str=None, reset=False)
            
            # Should have called console.print to show rules
            mock_components.console.print.assert_called()

    def test_real_feature_style_switch(self, mock_components):
        """Test real feature integration for style switching."""
        mock_config = {
            "commit_rules": {
                "style": "conventional",
                "format": "{type}({scope}): {description}",
                "subject_max_length": 50
            }
        }
        
        with patch('gitwise.features.commit_rules.load_config', return_value=mock_config), \
             patch('gitwise.features.commit_rules.save_config') as mock_save:
            
            config_commit_command(show=False, setup=False, style="custom", format_str=None, reset=False)
            
            # Should have attempted to save
            mock_save.assert_called_once()
            mock_components.show_success.assert_called_once()

    def test_real_feature_format_update(self, mock_components):
        """Test real feature integration for format updating."""
        mock_config = {
            "commit_rules": {
                "style": "conventional",
                "format": "{type}({scope}): {description}",
                "subject_max_length": 50
            }
        }
        
        with patch('gitwise.features.commit_rules.load_config', return_value=mock_config), \
             patch('gitwise.features.commit_rules.save_config') as mock_save:
            
            config_commit_command(show=False, setup=False, style=None, format_str="[{type}] {description}", reset=False)
            
            # Should have attempted to save
            mock_save.assert_called_once()
            mock_components.show_success.assert_called_once()

    def test_real_feature_invalid_format(self, mock_components):
        """Test real feature integration with invalid format."""
        mock_config = {
            "commit_rules": {
                "style": "conventional",
                "format": "{type}({scope}): {description}",
                "subject_max_length": 50
            }
        }
        
        with patch('gitwise.features.commit_rules.load_config', return_value=mock_config):
            config_commit_command(show=False, setup=False, style=None, format_str="invalid format without description", reset=False)
            
            # Should show error for invalid format
            mock_components.show_error.assert_called_once() 