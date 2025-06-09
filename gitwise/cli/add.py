"""Add command CLI definition for GitWise."""

from typing import List

from ..features.add import AddFeature  # UPDATED: Import the new feature class


def add_command_cli(files: List[str] = None, auto_confirm: bool = False) -> None:
    """CLI entry point for staging files. Delegates to AddFeature."""
    add_feature_instance = AddFeature()
    add_feature_instance.execute_add(files, auto_confirm=auto_confirm)
