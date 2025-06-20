"""Merge analysis component for detecting and analyzing merge scenarios."""

import os
from typing import List, Optional

from gitwise.core.git_manager import GitManager
from .models import (
    MergeAnalysis,
    BranchChanges,
    ConflictInfo,
    ConflictType
)


class MergeAnalyzer:
    """Analyzes merge scenarios and detects conflicts."""

    def __init__(self, git_manager: Optional[GitManager] = None):
        """Initialize the analyzer with a GitManager instance."""
        self.git_manager = git_manager or GitManager()

    def analyze_merge(self, source_branch: str, target_branch: Optional[str] = None) -> MergeAnalysis:
        """
        Perform a comprehensive analysis of a merge between two branches.
        
        Args:
            source_branch: The branch to merge from
            target_branch: The branch to merge into (defaults to current branch)
            
        Returns:
            MergeAnalysis object with complete merge information
        """
        if not target_branch:
            target_branch = self.git_manager.get_current_branch()
            if not target_branch:
                raise RuntimeError("Could not determine target branch")

        # Verify branches exist
        if not self.git_manager.can_merge(source_branch, target_branch):
            raise RuntimeError(f"Cannot merge {source_branch} into {target_branch}")

        # Get merge base
        merge_base = self.git_manager.get_merge_base(source_branch, target_branch)
        
        # Check if fast-forward is possible
        can_fast_forward = self.git_manager.can_fast_forward(source_branch, target_branch)
        
        # Get branch changes
        source_changes = self._get_branch_changes(source_branch, merge_base)
        target_changes = self._get_branch_changes(target_branch, merge_base)
        
        # Attempt merge to detect conflicts (without committing)
        conflicts = self._detect_conflicts(source_branch)
        
        # Calculate total files changed
        all_changed_files = set(
            source_changes.added_files + source_changes.modified_files + source_changes.deleted_files +
            target_changes.added_files + target_changes.modified_files + target_changes.deleted_files
        )
        
        return MergeAnalysis(
            source_branch=source_branch,
            target_branch=target_branch,
            merge_base=merge_base,
            conflicts=conflicts,
            source_changes=source_changes,
            target_changes=target_changes,
            can_fast_forward=can_fast_forward,
            is_clean_merge=len(conflicts) == 0,
            total_files_changed=len(all_changed_files)
        )

    def _get_branch_changes(self, branch: str, merge_base: Optional[str]) -> BranchChanges:
        """Get summary of changes in a branch since merge base."""
        if not merge_base:
            return BranchChanges(
                added_files=[],
                modified_files=[],
                deleted_files=[],
                renamed_files=[],
                total_commits=0,
                commit_messages=[]
            )

        try:
            # Get files changed
            result = self.git_manager._run_git_command([
                "diff", "--name-status", f"{merge_base}..{branch}"
            ], check=False)
            
            added_files = []
            modified_files = []
            deleted_files = []
            renamed_files = []
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if not line.strip():
                        continue
                    
                    status = line[0]
                    file_path = line[2:] if len(line) > 2 else ""
                    
                    if status == 'A':
                        added_files.append(file_path)
                    elif status == 'M':
                        modified_files.append(file_path)
                    elif status == 'D':
                        deleted_files.append(file_path)
                    elif status.startswith('R'):
                        # Renamed file format: R100\told_name\tnew_name
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            renamed_files.append({"old": parts[1], "new": parts[2]})

            # Get commits
            commits = self.git_manager.get_commits_between(merge_base, branch)
            commit_messages = [commit.get("message", "") for commit in commits]
            
            return BranchChanges(
                added_files=added_files,
                modified_files=modified_files,
                deleted_files=deleted_files,
                renamed_files=renamed_files,
                total_commits=len(commits),
                commit_messages=commit_messages
            )
            
        except Exception:
            return BranchChanges(
                added_files=[],
                modified_files=[],
                deleted_files=[],
                renamed_files=[],
                total_commits=0,
                commit_messages=[]
            )

    def _detect_conflicts(self, source_branch: str) -> List[ConflictInfo]:
        """
        Detect merge conflicts by attempting a dry-run merge.
        
        Args:
            source_branch: The branch to merge from
            
        Returns:
            List of ConflictInfo objects for each conflicted file
        """
        conflicts = []
        
        # Save current state
        original_head = None
        try:
            original_head = self.git_manager._run_git_command(
                ["rev-parse", "HEAD"], check=True
            ).stdout.strip()
        except RuntimeError:
            return conflicts

        try:
            # Attempt merge without committing
            merge_success = self.git_manager.attempt_merge(source_branch, no_commit=True)
            
            if not merge_success:
                # Get list of conflicted files
                conflicted_files = self.git_manager.get_merge_conflicts()
                
                for file_path in conflicted_files:
                    conflict_info = self._create_conflict_info(file_path)
                    if conflict_info:
                        conflicts.append(conflict_info)
                        
        except Exception:
            pass
        finally:
            # Reset to original state
            try:
                if self.git_manager.is_merge_in_progress():
                    self.git_manager.abort_merge()
                if original_head:
                    self.git_manager._run_git_command(
                        ["reset", "--hard", original_head], check=False
                    )
            except Exception:
                pass
                
        return conflicts

    def _create_conflict_info(self, file_path: str) -> Optional[ConflictInfo]:
        """Create ConflictInfo object for a conflicted file with enhanced context."""
        conflict_data = self.git_manager.get_conflict_content(file_path)
        if not conflict_data:
            return None
        
        # Get the first conflict (could be enhanced to handle multiple conflicts per file)
        conflicts = conflict_data.get("conflicts", [])
        if not conflicts:
            return None
        
        # For now, focus on the first conflict in the file
        # TODO: Could be enhanced to handle multiple conflicts per file
        first_conflict = conflicts[0]
        
        return ConflictInfo(
            file_path=file_path,
            conflict_lines=list(range(first_conflict["start_line"], first_conflict["end_line"] + 1)),
            our_content=first_conflict["our_content"],
            their_content=first_conflict["their_content"],
            base_content=None,  # Could be enhanced to get common ancestor content
            before_context=first_conflict["before_context"],
            after_context=first_conflict["after_context"],
            full_context=first_conflict["full_context"],
            full_file_content=conflict_data["full_content"],
            start_line=first_conflict["start_line"],
            end_line=first_conflict["end_line"],
            context_start_line=first_conflict["context_start_line"],
            context_end_line=first_conflict["context_end_line"]
        )

    def get_merge_preview(self, source_branch: str, target_branch: Optional[str] = None) -> str:
        """
        Get a preview of what the merge would look like.
        
        Args:
            source_branch: The branch to merge from
            target_branch: The branch to merge into
            
        Returns:
            A formatted string describing the merge preview
        """
        try:
            analysis = self.analyze_merge(source_branch, target_branch)
            
            preview = f"Merge Preview: {analysis.source_branch} → {analysis.target_branch}\n"
            preview += f"{'=' * 50}\n"
            
            if analysis.can_fast_forward:
                preview += "✅ Fast-forward merge possible\n"
            else:
                preview += "🔄 3-way merge required\n"
                
            if analysis.is_clean_merge:
                preview += "✅ No conflicts detected\n"
            else:
                preview += f"⚠️  {len(analysis.conflicts)} conflict(s) detected\n"
                
            # Summary of changes
            preview += f"\nChanges from {analysis.source_branch}:\n"
            if analysis.source_changes.added_files:
                preview += f"  + {len(analysis.source_changes.added_files)} file(s) added\n"
            if analysis.source_changes.modified_files:
                preview += f"  ~ {len(analysis.source_changes.modified_files)} file(s) modified\n"
            if analysis.source_changes.deleted_files:
                preview += f"  - {len(analysis.source_changes.deleted_files)} file(s) deleted\n"
                
            return preview
            
        except Exception as e:
            return f"Error generating merge preview: {str(e)}" 