"""Feature logic for custom commit rules and templates."""

import re
from typing import Dict, List, Optional, Tuple, Any

import typer

from gitwise.config import load_config, save_config
from gitwise.ui import components


class CommitRulesFeature:
    """Handles custom commit message rules and format configuration."""

    def __init__(self):
        """Initialize CommitRulesFeature with current configuration."""
        self.config = load_config()
        self.rules = self.config.get('commit_rules', self._get_default_rules())

    def _get_default_rules(self) -> Dict[str, Any]:
        """Get default conventional commit rules."""
        return {
            "style": "conventional",
            "format": "{type}({scope}): {description}",
            "subject_max_length": 50,
            "body_wrap_length": 72,
            "allowed_types": [
                "feat", "fix", "docs", "style", "refactor", 
                "perf", "test", "chore", "ci", "build", "revert"
            ],
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

    def get_active_style(self) -> str:
        """Return current commit style: 'conventional' or 'custom'."""
        return self.rules.get("style", "conventional")

    def get_commit_rules(self) -> Dict[str, Any]:
        """Get current commit rules configuration."""
        return self.rules.copy()

    def validate_format(self, format_str: str) -> Tuple[bool, str]:
        """Validate format string has required placeholders and is well-formed."""
        if not format_str:
            return False, "Format string cannot be empty"
        
        # Must contain {description} placeholder
        if "{description}" not in format_str:
            return False, "Format must contain {description} placeholder"
        
        # Check for valid placeholders only
        valid_placeholders = {
            "type", "scope", "description", "ticket", "prefix", "emoji"
        }
        
        # Extract all placeholders
        placeholders = re.findall(r'\{([^}]+)\}', format_str)
        invalid_placeholders = [p for p in placeholders if p not in valid_placeholders]
        
        if invalid_placeholders:
            return False, f"Invalid placeholders: {', '.join(invalid_placeholders)}. Valid: {', '.join(valid_placeholders)}"
        
        return True, ""

    def validate_message(self, message: str) -> Tuple[bool, str]:
        """Validate commit message against active rules."""
        if not message:
            return False, "Commit message cannot be empty"
        
        lines = message.split('\n')
        subject = lines[0]
        
        # Check subject length
        max_length = self.rules.get("subject_max_length", 50)
        if len(subject) > max_length:
            return False, f"Subject line too long ({len(subject)} > {max_length} characters)"
        
        # Check capitalization if required
        if self.rules.get("rules", {}).get("capitalize", False):
            if subject and not subject[0].isupper():
                return False, "Subject line must be capitalized"
        
        # Check no period if required
        if self.rules.get("rules", {}).get("no_period", False):
            if subject.endswith('.'):
                return False, "Subject line should not end with a period"
        
        # Check required type if custom format
        if self.get_active_style() == "custom" and self.rules.get("rules", {}).get("require_type", False):
            allowed_types = self.rules.get("allowed_types", [])
            if allowed_types:
                # Extract type from beginning of message for common formats
                type_match = re.match(r'^(?:\[([^\]]+)\]|([^:\s(]+))', subject.lower())
                if not type_match:
                    return False, "Message must start with a valid type"
                
                extracted_type = (type_match.group(1) or type_match.group(2)).lower()
                if extracted_type not in [t.lower() for t in allowed_types]:
                    return False, f"Type '{extracted_type}' not in allowed types: {', '.join(allowed_types)}"
        
        return True, ""

    def generate_prompt(self, diff: str, context: str = "") -> str:
        """Generate AI prompt based on current rules."""
        if self.get_active_style() == "conventional":
            # Use existing conventional prompt
            from gitwise.prompts import PROMPT_COMMIT_MESSAGE
            return PROMPT_COMMIT_MESSAGE.format(diff=diff, guidance=context)
        
        # Generate custom prompt
        format_str = self.rules.get("format", "{description}")
        max_length = self.rules.get("subject_max_length", 80)
        allowed_types = self.rules.get("allowed_types", [])
        rules = self.rules.get("rules", {})
        custom_additions = self.rules.get("custom_prompt_additions", "")
        
        prompt = f"""Write a Git commit message for the following diff using this format:
{format_str}

Rules:
- Maximum subject length: {max_length} characters"""
        
        if allowed_types:
            prompt += f"\n- Use one of these types: {', '.join(allowed_types)}"
        
        if rules.get("capitalize", False):
            prompt += "\n- Capitalize the first letter"
        
        if rules.get("imperative_mood", False):
            prompt += "\n- Use imperative mood (e.g., 'Add' not 'Added')"
        
        if rules.get("no_period", False):
            prompt += "\n- No period at the end of subject line"
        
        if rules.get("require_type", False):
            prompt += "\n- Type is required in the format"
        
        if custom_additions:
            prompt += f"\n- {custom_additions}"
        
        prompt += "\n- Output only the commit message, no preamble or explanation"
        
        if context:
            prompt += f"\n\nContext: {context}"
        
        prompt += f"\n\nDiff:\n{diff}"
        
        return prompt

    def setup_interactive(self) -> Dict[str, Any]:
        """Interactive setup for custom commit rules."""
        components.console.print("\n🎨 [bold]Setting up custom commit rules...[/bold]\n")
        
        # Format selection
        components.console.print("1. Choose your commit message format:")
        components.console.print("   a) Simple: \"description\"")
        components.console.print("   b) Bracketed: \"[type] description\"")
        components.console.print("   c) Conventional-like: \"type: description\"")
        components.console.print("   d) Scoped: \"type(scope): description\"")
        components.console.print("   e) Custom format")
        
        format_choice = typer.prompt("\nSelect format (a/b/c/d/e)", default="b")
        
        format_templates = {
            "a": "{description}",
            "b": "[{type}] {description}",
            "c": "{type}: {description}",
            "d": "{type}({scope}): {description}",
        }
        
        if format_choice in format_templates:
            format_str = format_templates[format_choice]
        else:
            components.console.print("\nEnter your custom format using placeholders:")
            components.console.print("Available: {type}, {scope}, {description}, {ticket}, {prefix}, {emoji}")
            format_str = typer.prompt("Format", default="[{type}] {description}")
        
        # Validate format
        valid, error = self.validate_format(format_str)
        if not valid:
            components.show_error(f"Invalid format: {error}")
            return self._get_default_rules()
        
        # Types configuration
        require_types = False
        allowed_types = []
        
        if "{type}" in format_str:
            require_types = typer.confirm("\nDo you want to enforce specific types?", default=True)
            
            if require_types:
                components.console.print("\nEnter allowed commit types (comma-separated):")
                components.console.print("Examples: feature,bugfix,docs,refactor,test")
                types_input = typer.prompt("Types", default="feature,bugfix,docs,refactor,test")
                allowed_types = [t.strip() for t in types_input.split(",") if t.strip()]
        
        # Length configuration
        max_length = typer.prompt("\nMaximum subject line length", default=80, type=int)
        
        # Rule configuration
        components.console.print("\n📋 [bold]Additional rules:[/bold]")
        capitalize = typer.confirm("Capitalize first letter?", default=True)
        imperative_mood = typer.confirm("Use imperative mood?", default=False)
        no_period = typer.confirm("No period at end of subject?", default=True)
        
        # Custom guidance
        custom_additions = typer.prompt(
            "\nAny additional AI guidance? (optional)", 
            default="", 
            show_default=False
        )
        
        # Build configuration
        custom_rules = {
            "style": "custom",
            "format": format_str,
            "subject_max_length": max_length,
            "body_wrap_length": 72,
            "allowed_types": allowed_types,
            "allowed_scopes": [],
            "rules": {
                "capitalize": capitalize,
                "imperative_mood": imperative_mood,
                "no_period": no_period,
                "require_type": require_types,
                "require_scope": False,
                "allow_multiline": True,
                "require_body": False
            },
            "custom_prompt_additions": custom_additions
        }
        
        # Show preview
        components.console.print("\n✅ [bold green]Custom rules configured![/bold green]")
        self._show_rules_summary(custom_rules)
        
        return custom_rules

    def _show_rules_summary(self, rules: Dict[str, Any]) -> None:
        """Display a summary of the configured rules."""
        components.console.print(f"\n📋 [bold]Rules Summary:[/bold]")
        components.console.print(f"  • Format: [cyan]{rules['format']}[/cyan]")
        components.console.print(f"  • Max length: {rules['subject_max_length']} characters")
        
        if rules['allowed_types']:
            components.console.print(f"  • Types: {', '.join(rules['allowed_types'])}")
        
        rule_items = []
        if rules['rules']['capitalize']:
            rule_items.append("capitalize")
        if rules['rules']['imperative_mood']:
            rule_items.append("imperative mood")
        if rules['rules']['no_period']:
            rule_items.append("no period")
        
        if rule_items:
            components.console.print(f"  • Rules: {', '.join(rule_items)}")
        
        if rules['custom_prompt_additions']:
            components.console.print(f"  • Custom guidance: {rules['custom_prompt_additions']}")

    def save_rules(self, rules: Dict[str, Any]) -> bool:
        """Save commit rules to configuration."""
        try:
            # Update config
            self.config['commit_rules'] = rules
            save_config(self.config)
            self.rules = rules
            return True
        except Exception as e:
            components.show_error(f"Failed to save rules: {e}")
            return False

    def reset_to_conventional(self) -> bool:
        """Reset rules to conventional commits style."""
        default_rules = self._get_default_rules()
        default_rules['style'] = 'conventional'
        return self.save_rules(default_rules)

    def switch_style(self, style: str) -> bool:
        """Switch between conventional and custom styles."""
        if style not in ["conventional", "custom"]:
            return False
        
        current_rules = self.get_commit_rules()
        current_rules['style'] = style
        return self.save_rules(current_rules)

    def update_format(self, format_str: str) -> bool:
        """Update just the format string for custom rules."""
        valid, error = self.validate_format(format_str)
        if not valid:
            components.show_error(f"Invalid format: {error}")
            return False
        
        current_rules = self.get_commit_rules()
        current_rules['format'] = format_str
        current_rules['style'] = 'custom'  # Switch to custom when updating format
        return self.save_rules(current_rules)