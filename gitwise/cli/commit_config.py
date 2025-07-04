"""CLI commands for configuring commit rules and templates."""

from typing import Optional

import typer

from gitwise.features.commit_rules import CommitRulesFeature
from gitwise.ui import components


def config_commit_command(
    show: bool = typer.Option(False, "--show", help="Show current commit rules"),
    setup: bool = typer.Option(False, "--setup", help="Interactive setup of commit rules"),
    style: Optional[str] = typer.Option(None, "--style", help="Switch style: conventional or custom"),
    format_str: Optional[str] = typer.Option(None, "--format", help="Set custom format string"),
    reset: bool = typer.Option(False, "--reset", help="Reset to conventional commits")
) -> None:
    """Configure commit message rules and templates."""
    
    try:
        rules_feature = CommitRulesFeature()
        
        # Handle reset first
        if reset:
            if typer.confirm("Reset to conventional commits style?", default=True):
                if rules_feature.reset_to_conventional():
                    components.show_success("✅ Reset to conventional commits style")
                else:
                    components.show_error("Failed to reset commit rules")
            return
        
        # Handle setup
        if setup:
            custom_rules = rules_feature.setup_interactive()
            if rules_feature.save_rules(custom_rules):
                components.show_success("✅ Custom commit rules saved!")
                components.console.print("💡 Use [cyan]'gitwise commit'[/cyan] to generate messages with your custom format")
            else:
                components.show_error("Failed to save custom rules")
            return
        
        # Handle style switch
        if style:
            if style.lower() not in ["conventional", "custom"]:
                components.show_error("Style must be 'conventional' or 'custom'")
                return
            
            if rules_feature.switch_style(style.lower()):
                components.show_success(f"✅ Switched to {style.lower()} commit style")
            else:
                components.show_error(f"Failed to switch to {style.lower()} style")
            return
        
        # Handle format update
        if format_str:
            if rules_feature.update_format(format_str):
                components.show_success(f"✅ Updated format to: {format_str}")
                components.console.print("💡 This switches you to custom commit style")
            else:
                components.show_error("Failed to update format")
            return
        
        # Default behavior: show current rules
        current_rules = rules_feature.get_commit_rules()
        current_style = rules_feature.get_active_style()
        
        components.console.print(f"\n📋 [bold]Current Commit Rules[/bold] ([cyan]{current_style}[/cyan])\n")
        
        if current_style == "conventional":
            components.console.print("Using standard Conventional Commits format:")
            components.console.print("  • Format: [cyan]type(scope): description[/cyan]")
            components.console.print("  • Max length: 50 characters")
            components.console.print("  • Rules: imperative mood, capitalized, no period")
            components.console.print("  • Types: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert")
        else:
            rules_feature._show_rules_summary(current_rules)
        
        components.console.print(f"\n💡 [dim]Use [cyan]'gitwise config-commit --help'[/cyan] to see configuration options[/dim]")
        
    except Exception as e:
        components.show_error(f"Error managing commit rules: {e}")
        raise typer.Exit(code=1)