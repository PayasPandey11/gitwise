"""AI-powered merge commit message generator."""

from typing import List, Optional

from gitwise.llm.router import get_llm_response
from gitwise.prompts import PROMPT_MERGE_MESSAGE
from .models import MergeAnalysis, ConflictInfo


class MergeMessageGenerator:
    """Generates intelligent merge commit messages."""

    def __init__(self):
        """Initialize the merge message generator."""
        pass

    def generate_message(self, merge_analysis: MergeAnalysis, resolved_conflicts: Optional[List[ConflictInfo]] = None, context: str = "") -> str:
        """
        Generate an AI-powered merge commit message.
        
        Args:
            merge_analysis: MergeAnalysis object with merge details
            resolved_conflicts: List of conflicts that were resolved (if any)
            context: Additional context about the merge
            
        Returns:
            Generated merge commit message
        """
        try:
            # Build the prompt
            prompt = self._build_message_prompt(merge_analysis, resolved_conflicts, context)
            
            # Get AI response
            llm_response = get_llm_response(prompt)
            
            # Clean and format the response
            message = self._format_merge_message(llm_response)
            
            return message
            
        except Exception:
            # Fallback to conventional merge message
            return self._generate_fallback_message(merge_analysis, resolved_conflicts)

    def _build_message_prompt(self, merge_analysis: MergeAnalysis, resolved_conflicts: Optional[List[ConflictInfo]], context: str) -> str:
        """Build the AI prompt for merge message generation."""
        # Create changes summary
        changes_summary = self._create_changes_summary(merge_analysis)
        
        # Create conflicts resolved summary
        conflicts_resolved = "None"
        if resolved_conflicts:
            conflicts_resolved = f"{len(resolved_conflicts)} conflicts resolved:\n"
            for conflict in resolved_conflicts:
                conflicts_resolved += f"  • {conflict.file_path}\n"
        
        # Combine context
        full_context = context
        if merge_analysis.can_fast_forward:
            full_context += "\nThis is a fast-forward merge."
        else:
            full_context += "\nThis is a 3-way merge."
            
        prompt = PROMPT_MERGE_MESSAGE.replace("{{source_branch}}", merge_analysis.source_branch)
        prompt = prompt.replace("{{target_branch}}", merge_analysis.target_branch)
        prompt = prompt.replace("{{changes_summary}}", changes_summary)
        prompt = prompt.replace("{{conflicts_resolved}}", conflicts_resolved)
        prompt = prompt.replace("{{context}}", full_context)
        
        return prompt

    def _create_changes_summary(self, merge_analysis: MergeAnalysis) -> str:
        """Create a summary of changes from the merge analysis."""
        summary = f"Merging {merge_analysis.source_branch} into {merge_analysis.target_branch}\n\n"
        
        # Source branch changes
        source = merge_analysis.source_changes
        if source.total_commits > 0:
            summary += f"Changes from {merge_analysis.source_branch}:\n"
            summary += f"  • {source.total_commits} commits\n"
            
            if source.added_files:
                summary += f"  • {len(source.added_files)} files added\n"
            if source.modified_files:
                summary += f"  • {len(source.modified_files)} files modified\n"
            if source.deleted_files:
                summary += f"  • {len(source.deleted_files)} files deleted\n"
            if source.renamed_files:
                summary += f"  • {len(source.renamed_files)} files renamed\n"
                
            # Include recent commit messages for context
            if source.commit_messages:
                summary += "\nRecent commits:\n"
                for msg in source.commit_messages[:3]:  # Show up to 3 recent commits
                    summary += f"  • {msg}\n"
                if len(source.commit_messages) > 3:
                    summary += f"  • ... and {len(source.commit_messages) - 3} more\n"
        
        # Merge statistics
        summary += f"\nMerge statistics:\n"
        summary += f"  • Total files changed: {merge_analysis.total_files_changed}\n"
        summary += f"  • Conflicts: {len(merge_analysis.conflicts)}\n"
        
        return summary

    def _format_merge_message(self, raw_message: str) -> str:
        """Format and clean the AI-generated merge message."""
        # Remove any leading/trailing whitespace
        message = raw_message.strip()
        
        # Ensure conventional merge format
        lines = message.split('\n')
        subject = lines[0] if lines else ""
        
        # Ensure subject line starts with "Merge" if it doesn't already
        if not subject.lower().startswith('merge'):
            subject = f"Merge branch '{subject}'"
            
        # Ensure subject line is not too long
        if len(subject) > 72:
            # Truncate but keep it meaningful
            subject = subject[:69] + "..."
            
        # Reconstruct message
        if len(lines) > 1:
            body = '\n'.join(lines[1:]).strip()
            if body:
                message = f"{subject}\n\n{body}"
            else:
                message = subject
        else:
            message = subject
            
        return message

    def _generate_fallback_message(self, merge_analysis: MergeAnalysis, resolved_conflicts: Optional[List[ConflictInfo]]) -> str:
        """Generate a conventional merge message when AI is unavailable."""
        subject = f"Merge branch '{merge_analysis.source_branch}'"
        
        # Add body with basic information
        body_parts = []
        
        # Add changes summary
        source = merge_analysis.source_changes
        if source.total_commits > 0:
            if source.total_commits == 1:
                body_parts.append(f"Brings in 1 commit from {merge_analysis.source_branch}")
            else:
                body_parts.append(f"Brings in {source.total_commits} commits from {merge_analysis.source_branch}")
                
        # Add file changes
        changes = []
        if source.added_files:
            changes.append(f"{len(source.added_files)} files added")
        if source.modified_files:
            changes.append(f"{len(source.modified_files)} files modified")
        if source.deleted_files:
            changes.append(f"{len(source.deleted_files)} files deleted")
            
        if changes:
            body_parts.append("Changes: " + ", ".join(changes))
            
        # Add conflict resolution note
        if resolved_conflicts:
            if len(resolved_conflicts) == 1:
                body_parts.append("Resolved 1 merge conflict")
            else:
                body_parts.append(f"Resolved {len(resolved_conflicts)} merge conflicts")
                
        # Combine message
        if body_parts:
            return f"{subject}\n\n" + "\n".join(body_parts)
        else:
            return subject

    def generate_conflict_resolution_notes(self, conflicts: List[ConflictInfo]) -> str:
        """
        Generate notes about conflict resolution for inclusion in commit message.
        
        Args:
            conflicts: List of resolved conflicts
            
        Returns:
            Formatted notes about conflict resolution
        """
        if not conflicts:
            return ""
            
        notes = "\nConflict Resolution:\n"
        
        # Group conflicts by file type
        file_types = {}
        for conflict in conflicts:
            file_ext = conflict.file_path.split('.')[-1] if '.' in conflict.file_path else 'other'
            if file_ext not in file_types:
                file_types[file_ext] = []
            file_types[file_ext].append(conflict.file_path)
            
        # Add notes by file type
        for file_type, files in file_types.items():
            if file_type == 'py':
                notes += f"  • Python files ({len(files)}): Merged code changes carefully\n"
            elif file_type in ['json', 'yaml', 'yml']:
                notes += f"  • Configuration files ({len(files)}): Combined settings appropriately\n"
            elif file_type in ['md', 'rst', 'txt']:
                notes += f"  • Documentation ({len(files)}): Merged content updates\n"
            else:
                notes += f"  • {file_type.upper()} files ({len(files)}): Resolved conflicts\n"
                
        # Add specific file list if there are few conflicts
        if len(conflicts) <= 3:
            notes += "\nFiles with resolved conflicts:\n"
            for conflict in conflicts:
                notes += f"  • {conflict.file_path}\n"
                
        return notes

    def suggest_alternative_messages(self, merge_analysis: MergeAnalysis, resolved_conflicts: Optional[List[ConflictInfo]] = None) -> List[str]:
        """
        Suggest alternative merge messages with different styles.
        
        Args:
            merge_analysis: MergeAnalysis object
            resolved_conflicts: List of resolved conflicts
            
        Returns:
            List of alternative merge message suggestions
        """
        alternatives = []
        
        # Conventional style
        conventional = self._generate_fallback_message(merge_analysis, resolved_conflicts)
        alternatives.append(conventional)
        
        # Detailed style
        if merge_analysis.source_changes.commit_messages:
            detailed = f"Merge branch '{merge_analysis.source_branch}'\n\n"
            detailed += "Includes the following changes:\n"
            for msg in merge_analysis.source_changes.commit_messages[:5]:
                detailed += f"  • {msg}\n"
            if len(merge_analysis.source_changes.commit_messages) > 5:
                detailed += f"  • ... and {len(merge_analysis.source_changes.commit_messages) - 5} more commits\n"
            alternatives.append(detailed)
            
        # Concise style
        concise = f"Merge branch '{merge_analysis.source_branch}'"
        if resolved_conflicts:
            concise += f" (resolved {len(resolved_conflicts)} conflicts)"
        alternatives.append(concise)
        
        # Feature-focused style (if we can detect features)
        if any('feat' in msg.lower() for msg in merge_analysis.source_changes.commit_messages):
            feature_focused = f"Merge feature branch '{merge_analysis.source_branch}'\n\n"
            feature_focused += "New features and improvements from this branch."
            if resolved_conflicts:
                feature_focused += f"\nResolved {len(resolved_conflicts)} merge conflicts."
            alternatives.append(feature_focused)
            
        return alternatives 