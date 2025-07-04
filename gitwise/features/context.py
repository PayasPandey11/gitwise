"""Feature logic for context management across branches for improving AI responses."""

import json
import os
import re
import time
from typing import Dict, Optional, Any

from gitwise.config import ConfigError, load_config
from gitwise.core.git_manager import GitManager
from gitwise.ui import components

# Initialize GitManager
git_manager = GitManager()

class ContextFeature:
    """Handles storing and retrieving context information per branch.
    
    This feature stores context about the "why" behind code changes to help
    improve the quality of AI-generated outputs (commit messages, PR descriptions, etc.).
    """

    def __init__(self):
        """Initialize the ContextFeature with a GitManager instance."""
        self.git_manager = git_manager
        
    def get_context_dir_path(self) -> str:
        """Return the path to the context directory within the git repo."""
        git_dir = os.path.join(self.git_manager.repo_path, ".git")
        context_dir = os.path.join(git_dir, "gitwise", "context")
        return context_dir
    
    def get_branch_context_path(self, branch_name: Optional[str] = None) -> str:
        """Get the path to the context file for the specified branch (or current branch)."""
        if branch_name is None:
            branch_name = self.git_manager.get_current_branch()
            if branch_name is None:
                raise ValueError("Cannot determine current branch")
                
        # Create a filename-safe version of the branch name
        safe_branch_name = re.sub(r'[^\w-]', '_', branch_name) + ".json"
        
        # Get the full path
        context_dir = self.get_context_dir_path()
        return os.path.join(context_dir, safe_branch_name)
    
    def get_context(self, branch_name: Optional[str] = None) -> Dict[str, Any]:
        """Get the stored context for the specified branch (or current branch)."""
        context_path = self.get_branch_context_path(branch_name)
        
        if os.path.exists(context_path):
            try:
                with open(context_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # If the file exists but is corrupt, return an empty context
                return self._create_default_context()
        else:
            # If the file doesn't exist, return default context structure
            return self._create_default_context()
    
    def set_context(self, context_string: str, branch_name: Optional[str] = None) -> bool:
        """Set user-provided context for the specified branch (or current branch)."""
        try:
            # Get existing context or create default
            context = self.get_context(branch_name)
            
            # Update with new user context
            context["user_set_context"] = context_string
            context["last_updated"] = int(time.time())
            
            # Write updated context
            return self._write_context(context, branch_name)
        except Exception as e:
            components.show_error(f"Failed to set context: {str(e)}")
            return False
    
    def parse_branch_context(self, branch_name: Optional[str] = None) -> bool:
        """Parse context information from branch name and update context storage."""
        if branch_name is None:
            branch_name = self.git_manager.get_current_branch()
            if branch_name is None:
                components.show_error("Cannot determine current branch")
                return False
        
        # Get existing context
        context = self.get_context(branch_name)
        
        # Parse ticket ID from branch name (e.g., "feature/TICKET-123-description")
        ticket_match = re.search(r'([A-Z]+-\d+)', branch_name)
        if ticket_match:
            context["parsed_ticket_id"] = ticket_match.group(1)
        
        # Extract keywords from branch name (e.g., "feature/fix-login-bug")
        # First, strip common prefixes like feature/, bugfix/, etc.
        branch_parts = branch_name.split('/', 1)
        keyword_source = branch_parts[1] if len(branch_parts) > 1 else branch_name
        
        # Extract keywords
        keywords = re.findall(r'[a-zA-Z]+', keyword_source)
        # Filter out common words and ticket IDs
        filtered_keywords = [
            kw.lower() for kw in keywords 
            if len(kw) > 2 and kw.lower() not in ['the', 'and', 'for', 'bug']
        ]
        
        if filtered_keywords:
            context["parsed_keywords"] = filtered_keywords
        
        # Update timestamp
        context["last_updated"] = int(time.time())
        
        # Write updated context
        return self._write_context(context, branch_name)
    
    def extract_keywords(self, text: str) -> list:
        """Extract meaningful keywords from text (branch name, context, etc)."""
        # Extract words from text
        keywords = re.findall(r'[a-zA-Z]+', text)
        
        # Common words to filter out
        common_words = {'the', 'and', 'for', 'bug', 'fix', 'feat', 'feature', 
                       'chore', 'docs', 'test', 'refactor', 'to', 'of', 'in', 
                       'on', 'at', 'from', 'with', 'by', 'is', 'are', 'was', 'were'}
        
        # Filter out common words, short words, and ticket IDs
        filtered_keywords = [
            kw.lower() for kw in keywords 
            if len(kw) > 2 
            and kw.lower() not in common_words
            and not re.match(r'^[A-Z]+-\d+$', kw.upper())  # Skip ticket IDs
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in filtered_keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords
    
    def prompt_for_context_if_needed(self, branch_name: Optional[str] = None) -> Optional[str]:
        """Check if context is missing and prompt user for context if needed.
        
        Returns the context string (either existing or newly provided), or None if unavailable.
        """
        context = self.get_context(branch_name)
        
        # If we already have user-set context, use it
        if context.get("user_set_context"):
            return context["user_set_context"]
        
        # If we have a ticket ID but no user context, that's still useful
        if context.get("parsed_ticket_id"):
            ticket_id = context["parsed_ticket_id"]
            components.show_section("Context Information")
            components.console.print(
                f"Using ticket ID [bold cyan]{ticket_id}[/bold cyan] as context (from branch name)."
            )
            components.console.print(
                "[dim]You can set more detailed context with [cyan]gitwise set-context \"your context\"[/cyan][/dim]"
            )
            return f"Ticket: {ticket_id}"
        
        # No context available, prompt the user
        components.show_section("Context Needed")
        components.console.print(
            "To improve AI suggestions, briefly describe what you're working on or provide a ticket ID:"
        )
        components.console.print(
            "[dim](Press Enter to skip, or use [cyan]gitwise set-context \"your context\"[/cyan] later)[/dim]"
        )
        
        user_input = input("> ").strip()
        if user_input:
            # Save the provided context
            self.set_context(user_input, branch_name)
            return user_input
        
        return None
    
    def get_context_for_ai_prompt(self, branch_name: Optional[str] = None) -> str:
        """Get context in a format suitable for inclusion in AI prompts."""
        context = self.get_context(branch_name)
        
        context_parts = []
        
        # User-set context is highest priority
        if context.get("user_set_context"):
            context_parts.append(f"User-provided context: {context['user_set_context']}")
        
        # Include ticket ID if available
        if context.get("parsed_ticket_id") and not context.get("user_set_context"):
            context_parts.append(f"Associated ticket ID from branch name: {context['parsed_ticket_id']}")
        
        # Include keywords if available and no other context
        if context.get("parsed_keywords") and not context_parts:
            keywords = ", ".join(context["parsed_keywords"])
            context_parts.append(f"Keywords extracted from branch name: {keywords}")
        
        if not context_parts:
            return ""
        
        return ". ".join(context_parts) + "."
    
    def execute_set_context(self, context_string: str) -> None:
        """CLI entry point for setting context."""
        try:
            # Check configuration
            try:
                load_config()
            except ConfigError as e:
                from gitwise.cli.init import init_command
                
                components.show_error(str(e))
                if components.safe_confirm("Would you like to run 'gitwise init' now?", default=True):
                    init_command()
                return
            
            branch_name = self.git_manager.get_current_branch()
            if branch_name is None:
                components.show_error("Cannot determine current branch")
                return
            
            if self.set_context(context_string):
                components.show_success(f"Context set for branch '{branch_name}'")
            else:
                components.show_error("Failed to set context")
        except Exception as e:
            components.show_error(f"Error: {str(e)}")
    
    def execute_get_context(self) -> None:
        """CLI entry point for showing current context."""
        try:
            # Check configuration
            try:
                load_config()
            except ConfigError as e:
                from gitwise.cli.init import init_command
                
                components.show_error(str(e))
                if components.safe_confirm("Would you like to run 'gitwise init' now?", default=True):
                    init_command()
                return
            
            branch_name = self.git_manager.get_current_branch()
            if branch_name is None:
                components.show_error("Cannot determine current branch")
                return
            
            context = self.get_context(branch_name)
            
            components.show_section(f"Context for branch '{branch_name}'")
            
            if context.get("user_set_context"):
                components.console.print(
                    f"[bold]User-set context:[/bold] {context['user_set_context']}"
                )
            else:
                components.console.print(
                    "[dim]No user-set context. Use [cyan]gitwise set-context \"your context\"[/cyan] to set.[/dim]"
                )
            
            if context.get("parsed_ticket_id"):
                components.console.print(
                    f"[bold]Ticket ID (from branch):[/bold] {context['parsed_ticket_id']}"
                )
            
            if context.get("parsed_keywords"):
                components.console.print(
                    f"[bold]Keywords (from branch):[/bold] {', '.join(context['parsed_keywords'])}"
                )
            
            if context.get("last_updated"):
                # Convert timestamp to readable date
                import datetime
                update_time = datetime.datetime.fromtimestamp(context["last_updated"])
                components.console.print(
                    f"[dim]Last updated: {update_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
                )
        except Exception as e:
            components.show_error(f"Error: {str(e)}")
    
    def _create_default_context(self) -> Dict[str, Any]:
        """Create a default context structure."""
        return {
            "user_set_context": "",
            "parsed_ticket_id": "",
            "parsed_keywords": [],
            "last_updated": int(time.time())
        }
    
    def _write_context(self, context: Dict[str, Any], branch_name: Optional[str] = None) -> bool:
        """Write context to the appropriate file."""
        try:
            context_path = self.get_branch_context_path(branch_name)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(context_path), exist_ok=True)
            
            # Write context file
            with open(context_path, "w", encoding="utf-8") as f:
                json.dump(context, f, indent=2)
            
            return True
        except Exception as e:
            components.show_error(f"Failed to write context: {str(e)}")
            return False 