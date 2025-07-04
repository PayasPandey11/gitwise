"""Branch creation with context feature for GitWise."""

import re
from typing import Optional

import typer

from gitwise.config import ConfigError, load_config
from gitwise.core.git_manager import GitManager
from gitwise.features.context import ContextFeature
from gitwise.ui import components


class BranchFeature:
    """Handles branch creation with context gathering."""

    def __init__(self):
        """Initialize BranchFeature with GitManager and ContextFeature."""
        self.git_manager = GitManager()
        self.context_feature = ContextFeature()

    def _validate_branch_name(self, branch_name: str) -> bool:
        """Validate branch name follows git conventions."""
        # Basic git branch name validation
        if not branch_name:
            return False
        
        # Check for invalid characters
        invalid_chars = [' ', '~', '^', ':', '?', '*', '[', '\\', '..', '@{', '//']
        for char in invalid_chars:
            if char in branch_name:
                return False
        
        # Cannot start or end with slash or dot
        if branch_name.startswith('/') or branch_name.endswith('/'):
            return False
        if branch_name.startswith('.') or branch_name.endswith('.'):
            return False
        
        return True

    def _detect_work_type(self, branch_name: str) -> str:
        """Detect work type from branch name prefix."""
        prefixes = {
            'feature/': 'feature',
            'feat/': 'feature',
            'bugfix/': 'bugfix',
            'fix/': 'bugfix',
            'hotfix/': 'hotfix',
            'chore/': 'chore',
            'docs/': 'docs',
            'refactor/': 'refactor',
            'test/': 'test',
            'release/': 'release'
        }
        
        for prefix, work_type in prefixes.items():
            if branch_name.startswith(prefix):
                return work_type
        
        return 'feature'  # Default to feature

    def _extract_ticket_id(self, text: str) -> Optional[str]:
        """Extract ticket ID from branch name or context."""
        # Common ticket patterns: PROJ-123, ABC-1234, etc.
        patterns = [
            r'[A-Z]+-\d+',  # JIRA style
            r'#\d+',        # GitHub issue style
            r'[A-Z]{2,}-\d+'  # Other tracking systems
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().upper()
        
        return None

    def execute_branch(
        self,
        branch_name: str,
        context: Optional[str] = None,
        ticket: Optional[str] = None,
        checkout: bool = False,
        from_branch: Optional[str] = None
    ) -> None:
        """Create a new branch with context."""
        try:
            # Config check
            try:
                load_config()
            except ConfigError as e:
                from gitwise.cli.init import init_command
                components.show_error(str(e))
                if typer.confirm("Would you like to run 'gitwise init' now?", default=True):
                    init_command()
                return

            # Validate branch name
            if not self._validate_branch_name(branch_name):
                components.show_error(f"Invalid branch name: '{branch_name}'")
                components.console.print("Branch names cannot contain spaces, ~, ^, :, ?, *, [, \\, .., @{, //")
                return

            # Check if branch already exists
            existing_branches = self.git_manager._run_git_command(
                ["branch", "--list", branch_name],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            if existing_branches:
                components.show_error(f"Branch '{branch_name}' already exists")
                return

            # Get base branch
            if from_branch == "current":
                from_branch = self.git_manager.get_current_branch()
            elif from_branch is None:
                # Default to main/master
                main_branch = self.git_manager._run_git_command(
                    ["symbolic-ref", "refs/remotes/origin/HEAD"],
                    capture_output=True,
                    text=True,
                    check=False
                ).stdout.strip()
                
                if main_branch:
                    from_branch = main_branch.split('/')[-1]
                else:
                    # Fallback to common names
                    for branch in ["main", "master"]:
                        if self.git_manager._run_git_command(
                            ["show-ref", "--verify", f"refs/heads/{branch}"],
                            check=False
                        ).returncode == 0:
                            from_branch = branch
                            break
                    else:
                        from_branch = self.git_manager.get_current_branch()

            # Show branch creation info
            components.console.print(f"\n🌿 Creating branch: [green]{branch_name}[/green] from '[cyan]{from_branch}[/cyan]'\n")

            # Interactive mode if no context provided
            if context is None:
                context = typer.prompt(
                    "📝 What are you working on? (required)",
                    prompt_suffix="\n   > "
                )
                
                if not context or len(context.strip()) < 10:
                    components.show_error("Context must be at least 10 characters")
                    return
                
                context = context.strip()

            # Get ticket ID if not provided
            if ticket is None:
                # First try to extract from branch name
                ticket = self._extract_ticket_id(branch_name)
                
                # If not found, ask user
                if not ticket:
                    ticket_input = typer.prompt(
                        "\n🎫 Ticket/Issue ID? (optional, press Enter to skip)",
                        prompt_suffix="\n   > ",
                        default=""
                    )
                    if ticket_input:
                        ticket = ticket_input.strip()

            # Create the branch
            spinner = components.show_spinner(f"Creating branch '{branch_name}'...")
            spinner.start()
            
            try:
                # Create branch from base
                if checkout:
                    # Create and checkout
                    self.git_manager._run_git_command(
                        ["checkout", "-b", branch_name, from_branch],
                        check=True
                    )
                else:
                    # Just create the branch without switching
                    self.git_manager._run_git_command(
                        ["branch", branch_name, from_branch],
                        check=True
                    )
                
                # Prepare context data
                context_data = {
                    "user_set_context": context,
                    "parsed_ticket_id": ticket or self._extract_ticket_id(context) or "",
                    "parsed_keywords": self.context_feature.extract_keywords(branch_name),
                    "work_type": self._detect_work_type(branch_name),
                    "parent_branch": from_branch,
                    "branch_name": branch_name,
                    "auto_detected": {
                        "ticket_from_name": self._extract_ticket_id(branch_name) or "",
                        "type_from_prefix": self._detect_work_type(branch_name)
                    }
                }
                
                # Store context
                self.context_feature.set_context(context_data, branch_name)
                
                spinner.stop()
                components.console.line()
                
                # Success message
                if checkout:
                    components.show_success(f"✅ Switched to new branch '{branch_name}' with context!")
                else:
                    components.show_success(f"✅ Branch '{branch_name}' created with context!")
                    components.console.print(f"💡 Run [cyan]'git checkout {branch_name}'[/cyan] to switch to it")
                
                # Show context summary
                components.console.print("\n[dim]Context stored:[/dim]")
                components.console.print(f"  • Description: {context}")
                if ticket:
                    components.console.print(f"  • Ticket: {ticket}")
                components.console.print(f"  • Type: {context_data['work_type']}")
                
            except Exception as e:
                spinner.stop()
                components.show_error(f"Failed to create branch: {e}")
                
                # If we created and checked out, switch back
                if checkout and self.git_manager.get_current_branch() == branch_name:
                    self.git_manager._run_git_command(["checkout", from_branch], check=False)
                
                raise

        except Exception as e:
            components.show_error(f"Error: {e}")
            raise typer.Exit(code=1)