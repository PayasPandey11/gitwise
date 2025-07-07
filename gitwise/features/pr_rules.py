"""Pull request rules feature for custom PR description formats."""

import re
from typing import Dict, List, Tuple, Optional, Any
import json

from gitwise.config import load_config, save_config
from gitwise.ui import components
from gitwise.exceptions import GitWiseError
import typer


class PrRulesFeature:
    def __init__(self, auto_confirm: bool = False):
        self.auto_confirm = auto_confirm
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load PR rules from config or return defaults."""
        config = load_config()
        return config.get('pr_rules', self._get_default_rules())
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """Return default GitHub-style PR rules."""
        return {
            'style': 'github',
            'template': {
                'format': 'sections',
                'sections': [
                    {
                        'title': 'Summary',
                        'required': True,
                        'ai_guidance': 'One-line summary of the changes',
                        'placeholder': '{summary}'
                    },
                    {
                        'title': 'Motivation',
                        'required': False,
                        'ai_guidance': 'Why these changes are needed',
                        'placeholder': '{motivation}'
                    },
                    {
                        'title': 'Changes',
                        'required': True,
                        'type': 'list',
                        'ai_guidance': 'Bulleted list of specific changes made',
                        'placeholder': '{changes}'
                    },
                    {
                        'title': 'Breaking Changes',
                        'required': False,
                        'condition': 'if_present',
                        'ai_guidance': 'Any breaking changes that affect users',
                        'placeholder': '{breaking_changes}'
                    },
                    {
                        'title': 'Testing',
                        'required': False,
                        'ai_guidance': 'How the changes were tested',
                        'placeholder': '{testing}'
                    },
                    {
                        'title': 'Related Issues',
                        'required': False,
                        'ai_guidance': 'Issue references like #123 or JIRA-456',
                        'placeholder': '{issues}'
                    }
                ]
            },
            'validation': {
                'min_description_length': 20,
                'max_description_length': 5000,
                'require_issue_reference': False,
                'issue_reference_pattern': r'#\d+|[A-Z]+-\d+',
                'forbidden_content': [],
                'require_checklist': False
            },
            'ai_settings': {
                'tone': 'professional',
                'include_emoji': False,
                'include_metrics': True,
                'custom_instructions': ''
            },
            'auto_labels': {
                'enabled': False,
                'rules': []
            }
        }
    
    def get_active_style(self) -> str:
        """Return current PR style ('github' or 'custom')."""
        return self.rules.get('style', 'github')
    
    def get_pr_rules(self) -> Dict[str, Any]:
        """Get current PR rules configuration."""
        return self.rules.copy()
    
    def save_rules(self, rules: Dict[str, Any]) -> None:
        """Save PR rules to configuration."""
        config = load_config()
        config['pr_rules'] = rules
        save_config(config)
        self.rules = rules
    
    def reset_to_github(self) -> None:
        """Reset to default GitHub style."""
        self.save_rules(self._get_default_rules())
        components.show_success("Reset to default GitHub PR style")
    
    def switch_style(self, style: str) -> None:
        """Switch between github and custom styles."""
        if style not in ['github', 'custom']:
            raise GitWiseError(f"Invalid style: {style}. Must be 'github' or 'custom'")
        
        self.rules['style'] = style
        self.save_rules(self.rules)
        components.show_success(f"Switched to {style} PR style")
    
    def validate_pr_description(self, description: str) -> Tuple[bool, List[str]]:
        """Validate PR description against active rules."""
        errors = []
        validation = self.rules.get('validation', {})
        
        # Length validation
        min_length = validation.get('min_description_length', 0)
        max_length = validation.get('max_description_length', float('inf'))
        
        if len(description) < min_length:
            errors.append(f"Description too short (minimum {min_length} characters)")
        if len(description) > max_length:
            errors.append(f"Description too long (maximum {max_length} characters)")
        
        # Issue reference validation
        if validation.get('require_issue_reference', False):
            pattern = validation.get('issue_reference_pattern', r'#\d+')
            if not re.search(pattern, description):
                errors.append(f"Missing required issue reference (pattern: {pattern})")
        
        # Forbidden content
        forbidden = validation.get('forbidden_content', [])
        for term in forbidden:
            if term.lower() in description.lower():
                errors.append(f"Contains forbidden content: '{term}'")
        
        # Required sections for custom templates
        if self.get_active_style() == 'custom':
            template = self.rules.get('template', {})
            if template.get('format') == 'sections':
                for section in template.get('sections', []):
                    if section.get('required', False):
                        title = section['title']
                        if f"## {title}" not in description and f"### {title}" not in description:
                            errors.append(f"Missing required section: {title}")
        
        return len(errors) == 0, errors
    
    def generate_pr_prompt(self, commits: List[Dict], context: Dict) -> str:
        """Generate AI prompt based on current rules."""
        style = self.get_active_style()
        ai_settings = self.rules.get('ai_settings', {})
        
        # Base prompt components
        tone_map = {
            'professional': 'professional and formal',
            'casual': 'friendly and conversational',
            'technical': 'technical and detailed'
        }
        tone = tone_map.get(ai_settings.get('tone', 'professional'), 'professional')
        
        # Build prompt based on style
        if style == 'github':
            prompt = self._build_github_prompt(commits, context, tone, ai_settings)
        else:
            prompt = self._build_custom_prompt(commits, context, tone, ai_settings)
        
        # Add custom instructions if any
        custom_instructions = ai_settings.get('custom_instructions', '').strip()
        if custom_instructions:
            prompt += f"\n\nAdditional instructions: {custom_instructions}"
        
        return prompt
    
    def _build_github_prompt(self, commits: List[Dict], context: Dict, tone: str, ai_settings: Dict) -> str:
        """Build prompt for GitHub-style PR description."""
        prompt = f"""Write a GitHub Pull Request description for the following commits.

Tone: Be {tone}.

Rules:
- Use Markdown formatting
- Start with a brief summary (1-2 sentences)
- Include these sections: Motivation, Changes (bulleted list), Breaking Changes (if any), Testing, Related Issues
- Be concise but comprehensive
- Focus on the "why" and "what" of the changes"""

        if ai_settings.get('include_emoji', False):
            prompt += "\n- Use appropriate emoji in section headers"
        
        if ai_settings.get('include_metrics', True):
            prompt += "\n- Include relevant metrics if applicable (e.g., performance improvements, lines changed)"
        
        prompt += f"\n\nRepository: {context.get('repo_name', 'repository')}"
        
        if context.get('guidance'):
            prompt += f"\n\nContext: {context['guidance']}"
        
        if context.get('changed_files'):
            prompt += f"\n\nFiles changed:\n{context['changed_files']}"
        
        prompt += "\n\nCommits:\n"
        for commit in commits:
            prompt += f"- {commit['message']}\n"
        
        prompt += "\n\nGenerate the PR description:"
        
        return prompt
    
    def _build_custom_prompt(self, commits: List[Dict], context: Dict, tone: str, ai_settings: Dict) -> str:
        """Build prompt for custom PR description format."""
        template = self.rules.get('template', {})
        
        prompt = f"""Generate a Pull Request description with the following specifications.

Tone: Be {tone}.

Template Requirements:"""
        
        if template.get('format') == 'sections':
            prompt += "\n\nInclude these sections in order:\n"
            for section in template.get('sections', []):
                required = "REQUIRED" if section.get('required', False) else "OPTIONAL"
                prompt += f"\n- {section['title']} ({required})"
                if section.get('ai_guidance'):
                    prompt += f"\n  Guidance: {section['ai_guidance']}"
                if section.get('type') == 'list':
                    prompt += "\n  Format: Bulleted list"
                elif section.get('type') == 'checklist':
                    prompt += f"\n  Format: Checklist with options: {', '.join(section.get('options', []))}"
        
        elif template.get('format') == 'markdown':
            custom_template = template.get('custom_template', '')
            prompt += f"\n\nUse this template structure:\n{custom_template}"
            prompt += "\n\nFill in the placeholders with appropriate content."
        
        # Add validation requirements
        validation = self.rules.get('validation', {})
        if validation.get('require_issue_reference'):
            pattern = validation.get('issue_reference_pattern', '#\\d+')
            prompt += f"\n\nMUST include issue reference matching pattern: {pattern}"
        
        # Add context
        prompt += f"\n\nRepository: {context.get('repo_name', 'repository')}"
        
        if context.get('guidance'):
            prompt += f"\n\nContext: {context['guidance']}"
        
        if context.get('changed_files'):
            prompt += f"\n\nFiles changed:\n{context['changed_files']}"
        
        prompt += "\n\nCommits:\n"
        for commit in commits:
            prompt += f"- {commit['message']}\n"
        
        if ai_settings.get('include_emoji', False):
            prompt += "\n\nUse appropriate emoji where suitable."
        
        prompt += "\n\nGenerate the PR description following the template requirements:"
        
        return prompt
    
    def format_pr_description(self, ai_response: str, metadata: Dict) -> str:
        """Format AI response according to template rules."""
        # Clean up any preamble from AI response
        cleaned = self._clean_ai_response(ai_response)
        
        # Apply any post-processing based on rules
        if self.rules.get('ai_settings', {}).get('include_emoji', False):
            cleaned = self._ensure_emoji(cleaned)
        
        # Validate required sections are present
        if self.get_active_style() == 'custom':
            template = self.rules.get('template', {})
            if template.get('format') == 'sections':
                cleaned = self._ensure_required_sections(cleaned, template.get('sections', []))
        
        return cleaned
    
    def _clean_ai_response(self, response: str) -> str:
        """Remove common AI preambles and clean response."""
        # Remove lines like "Here's the PR description:" etc
        lines = response.strip().split('\n')
        start_idx = 0
        
        for i, line in enumerate(lines):
            if line.strip() and (
                line.startswith(('#', '##', '**')) or
                line.strip() == lines[i].strip() and i > 0  # Content started
            ):
                start_idx = i
                break
        
        return '\n'.join(lines[start_idx:]).strip()
    
    def _ensure_emoji(self, text: str) -> str:
        """Add emoji to section headers if missing."""
        emoji_map = {
            'Summary': '📝',
            'Motivation': '💡',
            'Changes': '🔄',
            'Breaking Changes': '⚠️',
            'Testing': '🧪',
            'Related Issues': '🔗',
            'What': '❓',
            'Why': '🤔',
            'Impact Analysis': '📊',
            'Rollback Plan': '⏮️'
        }
        
        for section, emoji in emoji_map.items():
            # Add emoji if section exists but doesn't have one
            text = re.sub(
                rf'^(#{1,3}\s*)({section})(\s*$)',
                rf'\1{emoji} \2\3',
                text,
                flags=re.MULTILINE
            )
        
        return text
    
    def _ensure_required_sections(self, text: str, sections: List[Dict]) -> str:
        """Ensure required sections are present in the description."""
        for section in sections:
            if section.get('required', False):
                title = section['title']
                # Check if section exists
                if not re.search(rf'^#{1,3}\s*(?:\S+\s+)?{re.escape(title)}\s*$', text, re.MULTILINE):
                    # Add placeholder section
                    text += f"\n\n## {title}\n*[This section is required but was not generated]*"
        
        return text
    
    def apply_auto_labels(self, description: str) -> List[str]:
        """Extract labels based on content rules."""
        labels = []
        
        if not self.rules.get('auto_labels', {}).get('enabled', False):
            return labels
        
        rules = self.rules.get('auto_labels', {}).get('rules', [])
        
        for rule in rules:
            pattern = rule.get('pattern', '')
            rule_labels = rule.get('labels', [])
            
            if pattern and re.search(pattern, description, re.IGNORECASE):
                labels.extend(rule_labels)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_labels = []
        for label in labels:
            if label not in seen:
                seen.add(label)
                unique_labels.append(label)
        
        return unique_labels
    
    def setup_interactive(self) -> Dict[str, Any]:
        """Interactive setup for custom PR rules."""
        components.show_section("PR Rules Configuration")
        
        # Choose style
        style_choice = typer.prompt(
            "Choose PR description style",
            type=typer.Choice(["github", "custom"]),
            default="github"
        )
        
        if style_choice == "github":
            rules = self._get_default_rules()
            
            # Optional GitHub customizations
            if typer.confirm("Would you like to customize GitHub style settings?", default=False):
                # Tone
                tone = typer.prompt(
                    "Select tone",
                    type=typer.Choice(["professional", "casual", "technical"]),
                    default="professional"
                )
                rules['ai_settings']['tone'] = tone
                
                # Emoji
                rules['ai_settings']['include_emoji'] = typer.confirm(
                    "Include emoji in section headers?",
                    default=False
                )
                
                # Issue references
                rules['validation']['require_issue_reference'] = typer.confirm(
                    "Require issue references in PRs?",
                    default=False
                )
                
                if rules['validation']['require_issue_reference']:
                    pattern = typer.prompt(
                        "Issue reference pattern (regex)",
                        default="#\\d+|[A-Z]+-\\d+"
                    )
                    rules['validation']['issue_reference_pattern'] = pattern
        
        else:  # custom
            rules = self._setup_custom_rules()
        
        # Auto-labeling
        if typer.confirm("Enable automatic label detection?", default=False):
            rules['auto_labels']['enabled'] = True
            rules['auto_labels']['rules'] = self._setup_auto_labels()
        
        return rules
    
    def _setup_custom_rules(self) -> Dict[str, Any]:
        """Setup custom PR rules interactively."""
        rules = self._get_default_rules()
        rules['style'] = 'custom'
        
        # Template format
        components.show_info("Choose template format:")
        components.console.print("1. Sections-based (recommended)")
        components.console.print("2. Custom markdown template")
        
        format_choice = typer.prompt("Select format", type=int, default=1)
        
        if format_choice == 1:
            rules['template'] = self._setup_sections_template()
        else:
            rules['template'] = self._setup_markdown_template()
        
        # Validation rules
        components.show_section("Validation Rules")
        
        rules['validation']['min_description_length'] = typer.prompt(
            "Minimum description length",
            type=int,
            default=50
        )
        
        rules['validation']['max_description_length'] = typer.prompt(
            "Maximum description length",
            type=int,
            default=5000
        )
        
        rules['validation']['require_issue_reference'] = typer.confirm(
            "Require issue references?",
            default=False
        )
        
        if rules['validation']['require_issue_reference']:
            rules['validation']['issue_reference_pattern'] = typer.prompt(
                "Issue reference pattern (regex)",
                default="#\\d+|[A-Z]+-\\d+"
            )
        
        # AI settings
        components.show_section("AI Settings")
        
        tone = typer.prompt(
            "Select tone",
            type=typer.Choice(["professional", "casual", "technical"]),
            default="professional"
        )
        rules['ai_settings']['tone'] = tone
        
        rules['ai_settings']['include_emoji'] = typer.confirm(
            "Include emoji?",
            default=False
        )
        
        custom_instructions = typer.prompt(
            "Additional AI instructions (optional)",
            default=""
        )
        if custom_instructions:
            rules['ai_settings']['custom_instructions'] = custom_instructions
        
        return rules
    
    def _setup_sections_template(self) -> Dict[str, Any]:
        """Setup sections-based template."""
        template = {
            'format': 'sections',
            'sections': []
        }
        
        # Predefined section templates
        predefined_sections = {
            '1': [  # Minimal
                {'title': 'What', 'required': True, 'ai_guidance': 'What changes were made'},
                {'title': 'Why', 'required': True, 'ai_guidance': 'Why these changes are needed'}
            ],
            '2': [  # Standard
                {'title': 'Summary', 'required': True, 'ai_guidance': 'Brief overview'},
                {'title': 'Changes', 'required': True, 'type': 'list', 'ai_guidance': 'List of changes'},
                {'title': 'Testing', 'required': False, 'ai_guidance': 'How it was tested'}
            ],
            '3': [  # Comprehensive
                {'title': 'Summary', 'required': True},
                {'title': 'Motivation', 'required': True},
                {'title': 'Changes', 'required': True, 'type': 'list'},
                {'title': 'Testing', 'required': True},
                {'title': 'Breaking Changes', 'required': False, 'condition': 'if_present'},
                {'title': 'Documentation', 'required': False}
            ]
        }
        
        components.show_info("Choose a template preset or create custom:")
        components.console.print("1. Minimal (What/Why)")
        components.console.print("2. Standard")
        components.console.print("3. Comprehensive")
        components.console.print("4. Custom")
        
        choice = typer.prompt("Select option", type=int, default=2)
        
        if choice in [1, 2, 3]:
            template['sections'] = predefined_sections[str(choice)]
        else:
            # Custom sections
            while True:
                section = {}
                section['title'] = typer.prompt("Section title")
                section['required'] = typer.confirm("Required?", default=True)
                section['ai_guidance'] = typer.prompt(
                    "AI guidance for this section",
                    default=""
                )
                
                if typer.confirm("Is this a list/checklist?", default=False):
                    section['type'] = typer.prompt(
                        "Type",
                        type=typer.Choice(["list", "checklist"]),
                        default="list"
                    )
                    
                    if section['type'] == 'checklist':
                        options = []
                        components.show_info("Enter checklist options (empty to finish):")
                        while True:
                            option = typer.prompt("Option", default="")
                            if not option:
                                break
                            options.append(option)
                        section['options'] = options
                
                template['sections'].append(section)
                
                if not typer.confirm("Add another section?", default=True):
                    break
        
        return template
    
    def _setup_markdown_template(self) -> Dict[str, Any]:
        """Setup custom markdown template."""
        template = {
            'format': 'markdown',
            'custom_template': ''
        }
        
        components.show_info("Enter your markdown template.")
        components.show_info("Use placeholders like {title}, {summary}, {changes}, etc.")
        components.console.print("\nExample:")
        components.console.print("# {title}\n\n## Summary\n{summary}\n\n## Changes\n{changes}")
        
        lines = []
        components.console.print("\nEnter template (type 'DONE' on new line when finished):")
        
        while True:
            line = input()
            if line.strip().upper() == 'DONE':
                break
            lines.append(line)
        
        template['custom_template'] = '\n'.join(lines)
        
        return template
    
    def _setup_auto_labels(self) -> List[Dict[str, Any]]:
        """Setup automatic labeling rules."""
        rules = []
        
        # Common patterns
        common_rules = [
            {'pattern': r'breaking change|backwards? incompatible', 'labels': ['breaking-change']},
            {'pattern': r'bug ?fix|fix(?:es|ed)? #\d+', 'labels': ['bug']},
            {'pattern': r'new feature|added?\s+\w+', 'labels': ['enhancement']},
            {'pattern': r'document|docs|readme', 'labels': ['documentation']},
            {'pattern': r'test|spec', 'labels': ['testing']},
            {'pattern': r'security|vulnerability|cve', 'labels': ['security']}
        ]
        
        if typer.confirm("Use common labeling patterns?", default=True):
            rules.extend(common_rules)
        
        if typer.confirm("Add custom labeling rules?", default=False):
            while True:
                pattern = typer.prompt("Pattern (regex)")
                labels_str = typer.prompt("Labels (comma-separated)")
                labels = [l.strip() for l in labels_str.split(',')]
                
                rules.append({
                    'pattern': pattern,
                    'labels': labels
                })
                
                if not typer.confirm("Add another rule?", default=False):
                    break
        
        return rules