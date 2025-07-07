"""CLI commands for PR rules configuration."""

import json
import typer
from typing import Optional, Dict

from gitwise.features.pr_rules import PrRulesFeature
from gitwise.ui import components
from gitwise.exceptions import GitWiseError


def config_pr_command(
    show: bool = typer.Option(False, "--show", help="Show current PR rules"),
    setup: bool = typer.Option(False, "--setup", help="Interactive setup for PR rules"),
    style: Optional[str] = typer.Option(None, "--style", help="Set PR style (github or custom)"),
    reset: bool = typer.Option(False, "--reset", help="Reset to default GitHub style"),
    export_file: Optional[str] = typer.Option(None, "--export", help="Export PR rules to file"),
    import_file: Optional[str] = typer.Option(None, "--import", help="Import PR rules from file"),
):
    """Configure PR description rules and templates."""
    pr_rules = PrRulesFeature()
    
    # Handle export
    if export_file:
        try:
            rules = pr_rules.get_pr_rules()
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, indent=2)
            components.show_success(f"PR rules exported to {export_file}")
            return
        except Exception as e:
            components.show_error(f"Failed to export PR rules: {str(e)}")
            raise typer.Exit(1)
    
    # Handle import
    if import_file:
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            # Validate imported rules
            if 'style' not in rules:
                components.show_error("Invalid PR rules file: missing 'style' field")
                raise typer.Exit(1)
            
            pr_rules.save_rules(rules)
            components.show_success(f"PR rules imported from {import_file}")
            return
        except FileNotFoundError:
            components.show_error(f"File not found: {import_file}")
            raise typer.Exit(1)
        except json.JSONDecodeError:
            components.show_error(f"Invalid JSON in file: {import_file}")
            raise typer.Exit(1)
        except Exception as e:
            components.show_error(f"Failed to import PR rules: {str(e)}")
            raise typer.Exit(1)
    
    # Handle reset
    if reset:
        if typer.confirm("Reset to default GitHub PR style?", default=True):
            pr_rules.reset_to_github()
        return
    
    # Handle style change
    if style:
        try:
            pr_rules.switch_style(style)
        except GitWiseError as e:
            components.show_error(str(e))
            raise typer.Exit(1)
        return
    
    # Handle setup
    if setup:
        rules = pr_rules.setup_interactive()
        pr_rules.save_rules(rules)
        components.show_success("PR rules configured successfully!")
        
        # Show example
        components.show_section("Example PR Format")
        _show_example_pr(rules)
        return
    
    # Default: show current rules
    if show or not any([setup, style, reset, export_file, import_file]):
        _show_current_rules(pr_rules)


def _show_current_rules(pr_rules: PrRulesFeature):
    """Display current PR rules configuration."""
    rules = pr_rules.get_pr_rules()
    style = rules.get('style', 'github')
    
    components.show_section("Current PR Rules Configuration")
    components.console.print(f"[bold]Style:[/bold] {style}")
    
    if style == 'github':
        components.console.print("\n[dim]Using default GitHub PR format[/dim]")
        
        # Show GitHub customizations if any
        ai_settings = rules.get('ai_settings', {})
        if ai_settings.get('tone') != 'professional':
            components.console.print(f"[bold]Tone:[/bold] {ai_settings.get('tone')}")
        if ai_settings.get('include_emoji'):
            components.console.print("[bold]Emoji:[/bold] Enabled")
        
        validation = rules.get('validation', {})
        if validation.get('require_issue_reference'):
            components.console.print(f"[bold]Issue Reference:[/bold] Required (pattern: {validation.get('issue_reference_pattern')})")
    
    else:  # custom
        template = rules.get('template', {})
        
        components.console.print(f"\n[bold]Template Format:[/bold] {template.get('format', 'sections')}")
        
        if template.get('format') == 'sections':
            components.console.print("\n[bold]Sections:[/bold]")
            for section in template.get('sections', []):
                required = "✓" if section.get('required') else "○"
                components.console.print(f"  {required} {section['title']}")
                if section.get('type'):
                    components.console.print(f"    [dim]Type: {section['type']}[/dim]")
                if section.get('ai_guidance'):
                    components.console.print(f"    [dim]Guidance: {section['ai_guidance']}[/dim]")
        
        elif template.get('format') == 'markdown':
            components.console.print("\n[bold]Custom Template:[/bold]")
            components.console.print(f"[dim]{template.get('custom_template', 'No template defined')}[/dim]")
        
        # Validation rules
        validation = rules.get('validation', {})
        components.console.print("\n[bold]Validation:[/bold]")
        components.console.print(f"  Min length: {validation.get('min_description_length', 'None')}")
        components.console.print(f"  Max length: {validation.get('max_description_length', 'None')}")
        if validation.get('require_issue_reference'):
            components.console.print(f"  Issue reference: Required ({validation.get('issue_reference_pattern')})")
        
        # AI settings
        ai_settings = rules.get('ai_settings', {})
        components.console.print("\n[bold]AI Settings:[/bold]")
        components.console.print(f"  Tone: {ai_settings.get('tone', 'professional')}")
        components.console.print(f"  Emoji: {'Enabled' if ai_settings.get('include_emoji') else 'Disabled'}")
        if ai_settings.get('custom_instructions'):
            components.console.print(f"  Custom instructions: {ai_settings['custom_instructions']}")
    
    # Auto-labeling
    auto_labels = rules.get('auto_labels', {})
    if auto_labels.get('enabled'):
        components.console.print("\n[bold]Auto-labeling:[/bold] Enabled")
        for rule in auto_labels.get('rules', []):
            components.console.print(f"  Pattern: {rule['pattern']} → Labels: {', '.join(rule['labels'])}")


def _show_example_pr(rules: Dict):
    """Show an example PR based on current rules."""
    style = rules.get('style', 'github')
    
    if style == 'github':
        example = """## Summary
Fixed authentication bug causing login failures for users with special characters

## Motivation
Users reported being unable to login when their passwords contained certain special characters

## Changes
- Updated password validation regex to properly escape special characters
- Added comprehensive test cases for various password formats
- Improved error messages for authentication failures

## Testing
- Added 15 new unit tests covering edge cases
- Manual testing with affected user accounts
- Verified fix on staging environment

## Related Issues
Fixes #789"""
        
        if rules.get('ai_settings', {}).get('include_emoji'):
            example = example.replace("## Summary", "## 📝 Summary")
            example = example.replace("## Motivation", "## 💡 Motivation")
            example = example.replace("## Changes", "## 🔄 Changes")
            example = example.replace("## Testing", "## 🧪 Testing")
            example = example.replace("## Related Issues", "## 🔗 Related Issues")
    
    else:  # custom
        template = rules.get('template', {})
        
        if template.get('format') == 'sections':
            sections = template.get('sections', [])
            example_parts = []
            
            for section in sections:
                title = section['title']
                if rules.get('ai_settings', {}).get('include_emoji'):
                    emoji_map = {
                        'Summary': '📝',
                        'What': '❓',
                        'Why': '🤔',
                        'Changes': '🔄',
                        'Testing': '🧪',
                        'Impact Analysis': '📊'
                    }
                    emoji = emoji_map.get(title, '')
                    if emoji:
                        title = f"{emoji} {title}"
                
                example_parts.append(f"## {title}")
                
                if section.get('type') == 'list':
                    example_parts.append("- First change item")
                    example_parts.append("- Second change item")
                elif section.get('type') == 'checklist':
                    for option in section.get('options', ['Option 1', 'Option 2'])[:2]:
                        example_parts.append(f"- [x] {option}")
                else:
                    example_parts.append(f"Example content for {section['title']} section")
                
                example_parts.append("")
            
            example = '\n'.join(example_parts).strip()
        
        else:  # markdown template
            custom_template = template.get('custom_template', '')
            example = custom_template.replace('{title}', 'Fix authentication bug')
            example = example.replace('{summary}', 'Fixed login issues for special characters')
            example = example.replace('{changes}', '- Updated validation\n- Added tests')
            example = example.replace('{what}', 'Fixed authentication validation')
            example = example.replace('{why}', 'Users couldn\'t login with special characters')
    
    components.console.print(example)