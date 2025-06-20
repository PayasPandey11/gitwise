"""Main controller for the Smart Merge feature."""

import tempfile
from typing import Optional

import typer

from gitwise.config import ConfigError, get_llm_backend, load_config
from gitwise.core.git_manager import GitManager
from gitwise.features.context import ContextFeature
from gitwise.ui import components
from gitwise.llm.offline import ensure_offline_model_ready

from .analyzer import MergeAnalyzer
from .explainer import ConflictExplainer
from .resolver import ResolutionSuggester
from .message_generator import MergeMessageGenerator
from .models import MergeOptions, MergeResult, MergeStrategy


class MergeController:
    """Main controller for Smart Merge operations."""

    def __init__(self, git_manager: Optional[GitManager] = None):
        """Initialize the merge controller."""
        self.git_manager = git_manager or GitManager()
        self.analyzer = MergeAnalyzer(self.git_manager)
        self.explainer = ConflictExplainer()
        self.resolver = ResolutionSuggester()
        self.message_generator = MergeMessageGenerator()

    def execute_merge(
        self,
        source_branch: str,
        options: Optional[MergeOptions] = None,
        auto_confirm: bool = False
    ) -> MergeResult:
        """Execute the complete smart merge workflow."""
        if options is None:
            options = MergeOptions()

        try:
            # Configuration check
            try:
                load_config()
            except ConfigError as e:
                components.show_error(str(e))
                return MergeResult(
                    success=False,
                    conflicts_detected=False,
                    merge_commit=None,
                    message="Configuration error",
                    conflicts=[],
                    next_steps=["Run 'gitwise init' to configure GitWise"]
                )

            # Show LLM backend info
            backend = get_llm_backend()
            components.show_section(f"[AI] LLM Backend: {backend}")

            # Step 1: Analyze the merge
            components.show_section(f"🔍 Analyzing merge: {source_branch}")
            
            try:
                with components.show_spinner("Analyzing merge scenario..."):
                    analysis = self.analyzer.analyze_merge(source_branch)
            except RuntimeError as e:
                components.show_error(str(e))
                return MergeResult(
                    success=False,
                    conflicts_detected=False,
                    merge_commit=None,
                    message=str(e),
                    conflicts=[],
                    next_steps=["Check branch names and repository state"]
                )

            # Step 2: Display analysis results
            self._display_merge_analysis(analysis)

            # Step 3: Handle merge based on conflicts
            if analysis.is_clean_merge:
                return self._handle_clean_merge(analysis, auto_confirm)
            else:
                return self._handle_conflicts(analysis, auto_confirm)

        except Exception as e:
            components.show_error(f"Unexpected error during merge: {str(e)}")
            return MergeResult(
                success=False,
                conflicts_detected=False,
                merge_commit=None,
                message=f"Error: {str(e)}",
                conflicts=[],
                next_steps=["Check repository state and try again"]
            )

    def _display_merge_analysis(self, analysis):
        """Display the merge analysis results."""
        components.show_section("📊 Merge Analysis")
        
        components.console.print(f"[bold]Source:[/bold] {analysis.source_branch}")
        components.console.print(f"[bold]Target:[/bold] {analysis.target_branch}")
        
        if analysis.can_fast_forward:
            components.console.print("✅ [green]Fast-forward merge possible[/green]")
        else:
            components.console.print("🔄 [yellow]3-way merge required[/yellow]")
            
        if analysis.is_clean_merge:
            components.console.print("✅ [green]No conflicts detected[/green]")
        else:
            components.console.print(f"⚠️  [yellow]{len(analysis.conflicts)} conflict(s) detected[/yellow]")

    def _handle_clean_merge(self, analysis, auto_confirm):
        """Handle a clean merge without conflicts."""
        components.show_section("✅ Clean Merge")
        
        if not (auto_confirm or typer.confirm(f"Proceed with merging {analysis.source_branch}?", default=True)):
            return MergeResult(
                success=False,
                conflicts_detected=False,
                merge_commit=None,
                message="Cancelled by user",
                conflicts=[],
                next_steps=[]
            )

        # Generate merge message
        with components.show_spinner("Generating merge commit message..."):
            merge_message = self.message_generator.generate_message(analysis)

        # Perform the merge
        try:
            success = self.git_manager._run_git_command([
                "merge", analysis.source_branch, "-m", merge_message
            ], check=False).returncode == 0
                
            if success:
                components.show_success("✅ Merge completed successfully!")
                return MergeResult(
                    success=True,
                    conflicts_detected=False,
                    merge_commit="HEAD",
                    message="Merge completed successfully",
                    conflicts=[],
                    next_steps=[]
                )
            else:
                return MergeResult(
                    success=False,
                    conflicts_detected=False,
                    merge_commit=None,
                    message="Merge operation failed",
                    conflicts=[],
                    next_steps=["Check git status"]
                )
        except Exception as e:
            return MergeResult(
                success=False,
                conflicts_detected=False,
                merge_commit=None,
                message=f"Merge error: {str(e)}",
                conflicts=[],
                next_steps=["Check repository state"]
            )

    def _handle_conflicts(self, analysis, auto_confirm):
        """Handle merge conflicts with AI assistance."""
        components.show_section("⚠️ Conflicts Detected")
        
        # Show conflict summary
        conflict_summary = self.explainer.get_conflict_summary(analysis.conflicts)
        components.console.print(conflict_summary)
        
        # Explain conflicts with AI
        components.show_section("🧠 AI Conflict Analysis")
        
        with components.show_spinner("Analyzing conflicts..."):
            explanations = self.explainer.explain_multiple_conflicts(analysis.conflicts)
        
        # Display explanations
        for file_path, explanation in explanations.items():
            components.console.print(f"\n[bold]📁 {file_path}[/bold]")
            components.console.print(f"[cyan]{explanation.summary}[/cyan]")
                
        # Get resolution strategy
        components.show_section("💡 Resolution Strategy")
        
        with components.show_spinner("Generating resolution strategy..."):
            strategy = self.resolver.suggest_strategy(analysis.conflicts)
            
        components.console.print(f"[bold]Approach:[/bold] {strategy.description}")
        components.console.print(f"[bold]Difficulty:[/bold] {strategy.estimated_difficulty}")
        
        components.console.print("\n[bold]Steps:[/bold]")
        for step in strategy.steps:
            components.console.print(f"  {step}")
            
        # Start merge for manual resolution
        components.show_section("🛠️ Manual Resolution Required")
        
        if auto_confirm or typer.confirm("Start merge for manual resolution?", default=True):
            self.git_manager.attempt_merge(analysis.source_branch, no_commit=True)
                
            components.console.print("\n[bold green]✅ Conflict markers created[/bold green]")
            components.console.print("Resolve conflicts manually, then run:")
            components.console.print("  [bold cyan]gitwise merge --continue[/bold cyan]")
            
            return MergeResult(
                success=False,
                conflicts_detected=True,
                merge_commit=None,
                message="Manual resolution required",
                conflicts=analysis.conflicts,
                next_steps=[
                    "Resolve conflicts in the listed files",
                    "Run 'gitwise merge --continue'"
                ]
            )
        else:
            return MergeResult(
                success=False,
                conflicts_detected=True,
                merge_commit=None,
                message="Cancelled by user",
                conflicts=analysis.conflicts,
                next_steps=[]
            )

    def continue_merge(self, auto_confirm: bool = False) -> MergeResult:
        """Continue a merge after conflicts have been resolved."""
        if not self.git_manager.is_merge_in_progress():
            components.show_error("No merge in progress")
            return MergeResult(
                success=False,
                conflicts_detected=False,
                merge_commit=None,
                message="No merge in progress",
                conflicts=[],
                next_steps=["Start a new merge operation"]
            )

        # Check for remaining conflicts
        remaining_conflicts = self.git_manager.get_merge_conflicts()
        if remaining_conflicts:
            components.show_warning(f"Still have {len(remaining_conflicts)} unresolved conflicts:")
            for file_path in remaining_conflicts:
                components.console.print(f"  ⚠️  {file_path}")
            
            return MergeResult(
                success=False,
                conflicts_detected=True,
                merge_commit=None,
                message="Conflicts still exist",
                conflicts=[],
                next_steps=[
                    "Resolve remaining conflicts manually",
                    "Run 'gitwise merge --continue' when done"
                ]
            )

        # Complete merge
        components.show_section("🎯 Completing merge")
        
        try:
            if auto_confirm or typer.confirm("Complete the merge?", default=True):
                success = self.git_manager.continue_merge()
                if success:
                    components.show_success("✅ Merge completed successfully!")
                    return MergeResult(
                        success=True,
                        conflicts_detected=False,
                        merge_commit="HEAD",
                        message="Merge completed",
                        conflicts=[],
                        next_steps=[]
                    )
                else:
                    components.show_error("Failed to complete merge")
                    return MergeResult(
                        success=False,
                        conflicts_detected=False,
                        merge_commit=None,
                        message="Failed to complete merge",
                        conflicts=[],
                        next_steps=["Check git status and resolve any issues"]
                    )
            else:
                components.show_warning("Merge completion cancelled")
                return MergeResult(
                    success=False,
                    conflicts_detected=False,
                    merge_commit=None,
                    message="Cancelled by user",
                    conflicts=[],
                    next_steps=["Run 'gitwise merge --continue' when ready"]
                )
        except Exception as e:
            components.show_error(f"Error completing merge: {str(e)}")
            return MergeResult(
                success=False,
                conflicts_detected=False,
                merge_commit=None,
                message=f"Error: {str(e)}",
                conflicts=[],
                next_steps=["Check repository state"]
            )

    def abort_merge(self) -> MergeResult:
        """Abort an ongoing merge operation."""
        if not self.git_manager.is_merge_in_progress():
            components.show_warning("No merge in progress to abort")
            return MergeResult(
                success=True,
                conflicts_detected=False,
                merge_commit=None,
                message="No merge in progress",
                conflicts=[],
                next_steps=[]
            )

        try:
            components.show_section("🚫 Aborting merge")
            success = self.git_manager.abort_merge()
            
            if success:
                components.show_success("✅ Merge aborted successfully")
                return MergeResult(
                    success=True,
                    conflicts_detected=False,
                    merge_commit=None,
                    message="Merge aborted",
                    conflicts=[],
                    next_steps=[]
                )
            else:
                components.show_error("Failed to abort merge")
                return MergeResult(
                    success=False,
                    conflicts_detected=False,
                    merge_commit=None,
                    message="Failed to abort merge",
                    conflicts=[],
                    next_steps=["Check git status and repository state"]
                )
        except Exception as e:
            components.show_error(f"Error aborting merge: {str(e)}")
            return MergeResult(
                success=False,
                conflicts_detected=False,
                merge_commit=None,
                message=f"Error: {str(e)}",
                conflicts=[],
                next_steps=["Check repository state"]
            ) 