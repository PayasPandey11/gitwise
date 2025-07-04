"""Tests for integration between CommitRulesFeature and CommitFeature."""

import pytest
from unittest.mock import MagicMock, patch

from gitwise.features.commit import generate_commit_message
from gitwise.features.commit_rules import CommitRulesFeature


class TestCommitRulesIntegration:
    """Test integration of custom commit rules with commit message generation."""

    def test_generate_commit_message_conventional_style(self):
        """Test that conventional style uses standard prompt."""
        mock_config = {
            "commit_rules": {
                "style": "conventional",
                "format": "{type}({scope}): {description}"
            }
        }
        
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        
        with patch('gitwise.features.commit_rules.CommitRulesFeature') as mock_rules_class, \
             patch('gitwise.features.commit.ContextFeature') as mock_context_class, \
             patch('gitwise.features.commit.get_llm_response') as mock_llm, \
             patch('gitwise.features.commit.git_manager') as mock_git_manager, \
             patch('gitwise.features.commit.PROMPT_COMMIT_MESSAGE', 'Standard prompt {{diff}} {{guidance}}'):
            
            # Setup mocks
            mock_rules = MagicMock(spec=CommitRulesFeature)
            mock_rules.get_active_style.return_value = "conventional"
            mock_rules_class.return_value = mock_rules
            
            mock_context = MagicMock()
            mock_context.get_context_for_ai_prompt.return_value = ""
            mock_context.prompt_for_context_if_needed.return_value = None
            mock_context_class.return_value = mock_context
            
            mock_git_manager.get_staged_files.return_value = [("M", "test.py")]
            mock_llm.return_value = "feat: add hello world"
            
            # Call function
            result = generate_commit_message(diff)
            
            # Verify conventional style was used
            mock_rules.get_active_style.assert_called_once()
            mock_rules.generate_prompt.assert_not_called()
            mock_llm.assert_called_once()
            
            # Verify standard prompt was used (not custom)
            call_args = mock_llm.call_args[0][0]
            assert "Standard prompt" in call_args
            assert diff in call_args

    def test_generate_commit_message_custom_style(self):
        """Test that custom style uses custom prompt."""
        mock_config = {
            "commit_rules": {
                "style": "custom",
                "format": "[{type}] {description}",
                "subject_max_length": 80
            }
        }
        
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        custom_prompt = "Custom prompt format with rules"
        
        with patch('gitwise.features.commit_rules.CommitRulesFeature') as mock_rules_class, \
             patch('gitwise.features.commit.ContextFeature') as mock_context_class, \
             patch('gitwise.features.commit.get_llm_response') as mock_llm, \
             patch('gitwise.features.commit.git_manager') as mock_git_manager:
            
            # Setup mocks
            mock_rules = MagicMock(spec=CommitRulesFeature)
            mock_rules.get_active_style.return_value = "custom"
            mock_rules.generate_prompt.return_value = custom_prompt
            mock_rules_class.return_value = mock_rules
            
            mock_context = MagicMock()
            mock_context.get_context_for_ai_prompt.return_value = ""
            mock_context.prompt_for_context_if_needed.return_value = None
            mock_context_class.return_value = mock_context
            
            mock_git_manager.get_staged_files.return_value = [("M", "test.py")]
            mock_llm.return_value = "[feature] Add hello world"
            
            # Call function
            result = generate_commit_message(diff)
            
            # Verify custom style was used
            mock_rules.get_active_style.assert_called_once()
            mock_rules.generate_prompt.assert_called_once()
            mock_llm.assert_called_once()
            
            # Verify custom prompt was used
            call_args = mock_llm.call_args[0][0]
            assert call_args == custom_prompt

    def test_generate_commit_message_force_style_override(self):
        """Test that force_style parameter overrides config."""
        mock_config = {
            "commit_rules": {
                "style": "custom",  # Config says custom
                "format": "[{type}] {description}"
            }
        }
        
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        
        with patch('gitwise.features.commit_rules.CommitRulesFeature') as mock_rules_class, \
             patch('gitwise.features.commit.ContextFeature') as mock_context_class, \
             patch('gitwise.features.commit.get_llm_response') as mock_llm, \
             patch('gitwise.features.commit.git_manager') as mock_git_manager, \
             patch('gitwise.features.commit.PROMPT_COMMIT_MESSAGE', 'Standard prompt {{diff}} {{guidance}}'):
            
            # Setup mocks
            mock_rules = MagicMock(spec=CommitRulesFeature)
            mock_rules.get_active_style.return_value = "custom"  # Config returns custom
            mock_rules_class.return_value = mock_rules
            
            mock_context = MagicMock()
            mock_context.get_context_for_ai_prompt.return_value = ""
            mock_context.prompt_for_context_if_needed.return_value = None
            mock_context_class.return_value = mock_context
            
            mock_git_manager.get_staged_files.return_value = [("M", "test.py")]
            mock_llm.return_value = "feat: add hello world"
            
            # Call function with force_style="conventional"
            result = generate_commit_message(diff, force_style="conventional")
            
            # Verify that force_style overrode the config
            # When force_style is provided, get_active_style may not be called since force_style takes precedence
            mock_rules.generate_prompt.assert_not_called()  # Should not call custom prompt
            mock_llm.assert_called_once()
            
            # Verify standard prompt was used despite custom config
            call_args = mock_llm.call_args[0][0]
            assert "Standard prompt" in call_args

    def test_generate_commit_message_fallback_on_error(self):
        """Test that it falls back to conventional when custom rules fail."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        
        with patch('gitwise.features.commit_rules.CommitRulesFeature', side_effect=Exception("Rules failed")), \
             patch('gitwise.features.commit.ContextFeature') as mock_context_class, \
             patch('gitwise.features.commit.get_llm_response') as mock_llm, \
             patch('gitwise.features.commit.git_manager') as mock_git_manager, \
             patch('gitwise.features.commit.PROMPT_COMMIT_MESSAGE', 'Fallback prompt {{diff}} {{guidance}}'):
            
            # Setup mocks
            mock_context = MagicMock()
            mock_context.get_context_for_ai_prompt.return_value = ""
            mock_context.prompt_for_context_if_needed.return_value = None
            mock_context_class.return_value = mock_context
            
            mock_git_manager.get_staged_files.return_value = [("M", "test.py")]
            mock_llm.return_value = "feat: add hello world"
            
            # Call function
            result = generate_commit_message(diff)
            
            # Verify fallback was used
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0][0]
            assert "Fallback prompt" in call_args
            assert diff in call_args

    def test_generate_commit_message_with_context_and_guidance(self):
        """Test that context and guidance are properly integrated."""
        mock_config = {
            "commit_rules": {
                "style": "custom",
                "format": "[{type}] {description}"
            }
        }
        
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        guidance = "Initial guidance"
        context = "Branch context info"
        
        with patch('gitwise.features.commit_rules.CommitRulesFeature') as mock_rules_class, \
             patch('gitwise.features.commit.ContextFeature') as mock_context_class, \
             patch('gitwise.features.commit.get_llm_response') as mock_llm, \
             patch('gitwise.features.commit.git_manager') as mock_git_manager:
            
            # Setup mocks
            mock_rules = MagicMock(spec=CommitRulesFeature)
            mock_rules.get_active_style.return_value = "custom"
            mock_rules.generate_prompt.return_value = "Custom prompt"
            mock_rules_class.return_value = mock_rules
            
            mock_context = MagicMock()
            mock_context.get_context_for_ai_prompt.return_value = context
            mock_context.prompt_for_context_if_needed.return_value = None
            mock_context_class.return_value = mock_context
            
            mock_git_manager.get_staged_files.return_value = [("M", "test.py")]
            mock_llm.return_value = "[feature] Add hello world"
            
            # Call function with guidance
            result = generate_commit_message(diff, guidance)
            
            # Verify that custom prompt was called with combined guidance
            mock_rules.generate_prompt.assert_called_once()
            call_args = mock_rules.generate_prompt.call_args
            diff_arg, guidance_arg = call_args[0]
            
            assert diff_arg == diff
            assert context in guidance_arg
            assert guidance in guidance_arg
            assert "- M test.py (Test)" in guidance_arg  # File info should be included (test.py is detected as test file)

    def test_generate_commit_message_file_type_detection(self):
        """Test that file types are correctly detected and included in guidance."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        
        with patch('gitwise.features.commit_rules.CommitRulesFeature') as mock_rules_class, \
             patch('gitwise.features.commit.ContextFeature') as mock_context_class, \
             patch('gitwise.features.commit.get_llm_response') as mock_llm, \
             patch('gitwise.features.commit.git_manager') as mock_git_manager:
            
            # Setup mocks
            mock_rules = MagicMock(spec=CommitRulesFeature)
            mock_rules.get_active_style.return_value = "custom"
            mock_rules.generate_prompt.return_value = "Custom prompt"
            mock_rules_class.return_value = mock_rules
            
            mock_context = MagicMock()
            mock_context.get_context_for_ai_prompt.return_value = ""
            mock_context.prompt_for_context_if_needed.return_value = None
            mock_context_class.return_value = mock_context
            
            # Mix of file types
            mock_git_manager.get_staged_files.return_value = [
                ("M", "src/main.py"),
                ("A", "README.md"),
                ("M", "tests/test_main.py"),
                ("D", "docs/old.rst")
            ]
            mock_llm.return_value = "[feature] Add hello world"
            
            # Call function
            result = generate_commit_message(diff)
            
            # Verify file type detection in guidance
            guidance_arg = mock_rules.generate_prompt.call_args[0][1]
            assert "- M src/main.py (Code)" in guidance_arg
            assert "- A README.md (Documentation)" in guidance_arg
            assert "- M tests/test_main.py (Test)" in guidance_arg
            assert "- D docs/old.rst (Documentation)" in guidance_arg 