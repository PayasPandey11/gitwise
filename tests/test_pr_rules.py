"""Tests for PR rules feature."""

import json
import pytest
from unittest.mock import Mock, patch, mock_open
from gitwise.features.pr_rules import PrRulesFeature
from gitwise.exceptions import GitWiseError


class TestPrRulesFeature:
    def test_default_rules_loaded(self):
        """Test that default GitHub rules are loaded when no config exists."""
        with patch('gitwise.features.pr_rules.load_config', return_value={}):
            pr_rules = PrRulesFeature()
            
            assert pr_rules.get_active_style() == 'github'
            rules = pr_rules.get_pr_rules()
            assert rules['style'] == 'github'
            assert 'template' in rules
            assert 'validation' in rules
            assert 'ai_settings' in rules
    
    def test_custom_rules_loading(self):
        """Test loading custom PR rules from config."""
        custom_config = {
            'pr_rules': {
                'style': 'custom',
                'template': {
                    'format': 'sections',
                    'sections': [
                        {'title': 'What', 'required': True},
                        {'title': 'Why', 'required': True}
                    ]
                },
                'validation': {
                    'min_description_length': 50
                }
            }
        }
        
        with patch('gitwise.features.pr_rules.load_config', return_value=custom_config):
            pr_rules = PrRulesFeature()
            
            assert pr_rules.get_active_style() == 'custom'
            rules = pr_rules.get_pr_rules()
            assert rules['style'] == 'custom'
            assert len(rules['template']['sections']) == 2
    
    def test_style_switching(self):
        """Test switching between GitHub and custom styles."""
        with patch('gitwise.features.pr_rules.load_config', return_value={}):
            with patch('gitwise.features.pr_rules.save_config') as mock_save:
                pr_rules = PrRulesFeature()
                
                # Switch to custom
                pr_rules.switch_style('custom')
                assert pr_rules.get_active_style() == 'custom'
                mock_save.assert_called()
                
                # Switch back to github
                pr_rules.switch_style('github')
                assert pr_rules.get_active_style() == 'github'
    
    def test_invalid_style_switching(self):
        """Test that invalid styles raise errors."""
        with patch('gitwise.features.pr_rules.load_config', return_value={}):
            pr_rules = PrRulesFeature()
            
            with pytest.raises(GitWiseError):
                pr_rules.switch_style('invalid')
    
    def test_pr_description_validation_length(self):
        """Test PR description length validation."""
        config = {
            'pr_rules': {
                'validation': {
                    'min_description_length': 20,
                    'max_description_length': 100
                }
            }
        }
        
        with patch('gitwise.features.pr_rules.load_config', return_value=config):
            pr_rules = PrRulesFeature()
            
            # Too short
            is_valid, errors = pr_rules.validate_pr_description("short")
            assert not is_valid
            assert any("too short" in error.lower() for error in errors)
            
            # Valid length
            is_valid, errors = pr_rules.validate_pr_description("This is a valid length description that should pass")
            assert is_valid
            assert len(errors) == 0
            
            # Too long
            long_desc = "x" * 150
            is_valid, errors = pr_rules.validate_pr_description(long_desc)
            assert not is_valid
            assert any("too long" in error.lower() for error in errors)
    
    def test_issue_reference_validation(self):
        """Test issue reference validation."""
        config = {
            'pr_rules': {
                'validation': {
                    'require_issue_reference': True,
                    'issue_reference_pattern': r'#\d+'
                }
            }
        }
        
        with patch('gitwise.features.pr_rules.load_config', return_value=config):
            pr_rules = PrRulesFeature()
            
            # Missing issue reference
            is_valid, errors = pr_rules.validate_pr_description("No issue reference here")
            assert not is_valid
            assert any("issue reference" in error.lower() for error in errors)
            
            # Valid issue reference
            is_valid, errors = pr_rules.validate_pr_description("Fixed bug described in #123")
            assert is_valid
            assert len(errors) == 0
    
    def test_forbidden_content_validation(self):
        """Test forbidden content validation."""
        config = {
            'pr_rules': {
                'validation': {
                    'forbidden_content': ['TODO', 'FIXME']
                }
            }
        }
        
        with patch('gitwise.features.pr_rules.load_config', return_value=config):
            pr_rules = PrRulesFeature()
            
            # Contains forbidden content
            is_valid, errors = pr_rules.validate_pr_description("This is a TODO item")
            assert not is_valid
            assert any("forbidden content" in error.lower() for error in errors)
            
            # Clean content
            is_valid, errors = pr_rules.validate_pr_description("This is clean content")
            assert is_valid
            assert len(errors) == 0
    
    def test_github_prompt_generation(self):
        """Test GitHub-style prompt generation."""
        with patch('gitwise.features.pr_rules.load_config', return_value={}):
            pr_rules = PrRulesFeature()
            
            commits = [
                {'message': 'feat: add new feature'},
                {'message': 'fix: resolve bug'}
            ]
            context = {
                'repo_name': 'test-repo',
                'guidance': 'Test guidance'
            }
            
            prompt = pr_rules.generate_pr_prompt(commits, context)
            
            assert 'GitHub Pull Request description' in prompt
            assert 'test-repo' in prompt
            assert 'feat: add new feature' in prompt
            assert 'fix: resolve bug' in prompt
            assert 'Test guidance' in prompt
    
    def test_custom_prompt_generation(self):
        """Test custom prompt generation with sections."""
        config = {
            'pr_rules': {
                'style': 'custom',
                'template': {
                    'format': 'sections',
                    'sections': [
                        {
                            'title': 'What',
                            'required': True,
                            'ai_guidance': 'Describe what was changed'
                        },
                        {
                            'title': 'Why',
                            'required': True,
                            'ai_guidance': 'Explain why the change was needed'
                        }
                    ]
                }
            }
        }
        
        with patch('gitwise.features.pr_rules.load_config', return_value=config):
            pr_rules = PrRulesFeature()
            
            commits = [{'message': 'feat: add feature'}]
            context = {'repo_name': 'test-repo'}
            
            prompt = pr_rules.generate_pr_prompt(commits, context)
            
            assert 'What (REQUIRED)' in prompt
            assert 'Why (REQUIRED)' in prompt
            assert 'Describe what was changed' in prompt
            assert 'Explain why the change was needed' in prompt
    
    def test_auto_label_detection(self):
        """Test automatic label detection."""
        config = {
            'pr_rules': {
                'auto_labels': {
                    'enabled': True,
                    'rules': [
                        {
                            'pattern': r'breaking change',
                            'labels': ['breaking-change']
                        },
                        {
                            'pattern': r'bug|fix',
                            'labels': ['bug']
                        }
                    ]
                }
            }
        }
        
        with patch('gitwise.features.pr_rules.load_config', return_value=config):
            pr_rules = PrRulesFeature()
            
            # Test breaking change detection
            labels = pr_rules.apply_auto_labels("This is a breaking change")
            assert 'breaking-change' in labels
            
            # Test bug fix detection
            labels = pr_rules.apply_auto_labels("This fixes a bug")
            assert 'bug' in labels
            
            # Test multiple matches
            labels = pr_rules.apply_auto_labels("Bug fix with breaking change")
            assert 'bug' in labels
            assert 'breaking-change' in labels
            
            # Test no matches
            labels = pr_rules.apply_auto_labels("Simple feature addition")
            assert len(labels) == 0
    
    def test_auto_labels_disabled(self):
        """Test that auto-labeling is disabled when not configured."""
        config = {
            'pr_rules': {
                'auto_labels': {
                    'enabled': False
                }
            }
        }
        
        with patch('gitwise.features.pr_rules.load_config', return_value=config):
            pr_rules = PrRulesFeature()
            
            labels = pr_rules.apply_auto_labels("This is a breaking change")
            assert len(labels) == 0
    
    def test_ai_response_cleaning(self):
        """Test cleaning of AI response preambles."""
        with patch('gitwise.features.pr_rules.load_config', return_value={}):
            pr_rules = PrRulesFeature()
            
            # Test removal of preamble
            response_with_preamble = """Here's the PR description:

## Summary
This is the actual content

## Changes
- Fixed bug
- Added feature"""
            
            cleaned = pr_rules._clean_ai_response(response_with_preamble)
            assert not cleaned.startswith("Here's")
            assert cleaned.startswith("## Summary")
    
    def test_emoji_addition(self):
        """Test automatic emoji addition to section headers."""
        with patch('gitwise.features.pr_rules.load_config', return_value={}):
            pr_rules = PrRulesFeature()
            
            text = """## Summary
This is a summary

## Changes
- Change 1
- Change 2"""
            
            result = pr_rules._ensure_emoji(text)
            assert "📝 Summary" in result
            assert "🔄 Changes" in result
    
    def test_required_sections_validation(self):
        """Test that required sections are validated in custom templates."""
        config = {
            'pr_rules': {
                'style': 'custom',
                'template': {
                    'format': 'sections',
                    'sections': [
                        {'title': 'Summary', 'required': True},
                        {'title': 'Testing', 'required': False}
                    ]
                }
            }
        }
        
        with patch('gitwise.features.pr_rules.load_config', return_value=config):
            pr_rules = PrRulesFeature()
            
            # Missing required section
            is_valid, errors = pr_rules.validate_pr_description("## Testing\nSome testing info")
            assert not is_valid
            assert any("Summary" in error for error in errors)
            
            # Has required section
            is_valid, errors = pr_rules.validate_pr_description("## Summary\nGood summary\n## Testing\nSome testing")
            assert is_valid
            assert len(errors) == 0
    
    def test_save_and_reset_rules(self):
        """Test saving and resetting rules."""
        with patch('gitwise.features.pr_rules.load_config', return_value={}):
            with patch('gitwise.features.pr_rules.save_config') as mock_save:
                pr_rules = PrRulesFeature()
                
                # Test saving custom rules
                custom_rules = {'style': 'custom', 'template': {'format': 'sections'}}
                pr_rules.save_rules(custom_rules)
                mock_save.assert_called_with(custom_rules)
                
                # Test reset to GitHub
                pr_rules.reset_to_github()
                # Should have called save_config with GitHub defaults
                args, kwargs = mock_save.call_args
                assert args[0]['style'] == 'github'