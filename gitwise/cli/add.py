"""Add command CLI definition for GitWise."""

from typing import List

from ..features.add import AddFeature  # UPDATED: Import the new feature class

# No longer need os, GitManager, specific feature commands, or config directly here
# import typer # Typer is used by the @app.command decorator, so it might still be needed implicitly or explicitly for that context.
# For now, assuming it's handled by the main app, if not we'll add it back.


# from ..ui import components # UI calls are now in AddFeature


# The add_command function itself will be registered with Typer in cli/__init__.py
# This file will now primarily define how that command delegates to the feature class.


def add_command_cli(files: List[str] = None, auto_confirm: bool = False) -> None:
    """CLI entry point for staging files. Delegates to AddFeature."""
    add_feature_instance = AddFeature()
    add_feature_instance.execute_add(files, auto_confirm=auto_confirm)
