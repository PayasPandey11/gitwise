"""CLI command for smart merge functionality."""

import typer

from gitwise.features.smart_merge import MergeController
from gitwise.features.smart_merge.models import MergeOptions, MergeStrategy
from gitwise.ui import components


def merge_command_cli(
    source_branch: str,
    strategy: str = "auto",
    no_commit: bool = False,
    no_ff: bool = False,
    squash: bool = False,
    edit_message: bool = True,
    continue_merge: bool = False,
    abort_merge: bool = False,
    auto_confirm: bool = False
) -> None:
    """
    Execute smart merge with AI assistance.
    
    Args:
        source_branch: Branch to merge from
        strategy: Merge strategy (auto, manual, ours, theirs)
        no_commit: Don't create merge commit automatically
        no_ff: Create merge commit even for fast-forward
        squash: Squash commits from source branch
        edit_message: Allow editing merge message
        continue_merge: Continue merge after resolving conflicts
        abort_merge: Abort ongoing merge
        auto_confirm: Skip interactive prompts
    """
    controller = MergeController()
    
    try:
        if abort_merge:
            # Abort ongoing merge
            result = controller.abort_merge()
            if not result.success:
                components.show_error(result.message)
                raise typer.Exit(code=1)
            return
            
        if continue_merge:
            # Continue merge after conflict resolution
            result = controller.continue_merge(auto_confirm=auto_confirm)
            if not result.success:
                components.show_error(result.message)
                if result.next_steps:
                    components.console.print("\n[bold]Next steps:[/bold]")
                    for step in result.next_steps:
                        components.console.print(f"  • {step}")
                raise typer.Exit(code=1)
            return
            
        # Regular merge operation
        if not source_branch:
            components.show_error("Source branch is required for merge operations")
            raise typer.Exit(code=1)
            
        # Create merge options
        merge_strategy = MergeStrategy.AUTO
        if strategy == "manual":
            merge_strategy = MergeStrategy.MANUAL
        elif strategy == "ours":
            merge_strategy = MergeStrategy.OURS
        elif strategy == "theirs":
            merge_strategy = MergeStrategy.THEIRS
            
        options = MergeOptions(
            strategy=merge_strategy,
            no_commit=no_commit,
            no_ff=no_ff,
            squash=squash,
            edit_message=edit_message
        )
        
        # Execute merge
        result = controller.execute_merge(
            source_branch=source_branch,
            options=options,
            auto_confirm=auto_confirm
        )
        
        if not result.success:
            if result.conflicts_detected:
                # Conflicts detected - this is expected
                components.console.print(f"\n[yellow]{result.message}[/yellow]")
                if result.next_steps:
                    components.console.print("\n[bold]Next steps:[/bold]")
                    for step in result.next_steps:
                        components.console.print(f"  • {step}")
            else:
                # Actual error
                components.show_error(result.message)
                if result.next_steps:
                    components.console.print("\n[bold]Next steps:[/bold]")
                    for step in result.next_steps:
                        components.console.print(f"  • {step}")
                raise typer.Exit(code=1)
        else:
            components.show_success("Merge completed successfully!")
            
    except KeyboardInterrupt:
        components.show_warning("\nMerge operation interrupted")
        components.console.print("You can:")
        components.console.print("  • Resume with: gitwise merge --continue")
        components.console.print("  • Abort with: gitwise merge --abort")
        raise typer.Exit(code=1)
    except Exception as e:
        components.show_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(code=1) 