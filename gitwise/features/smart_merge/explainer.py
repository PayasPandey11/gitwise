"""AI-powered conflict explanation component."""

from typing import Optional

from gitwise.llm.router import get_llm_response
from gitwise.prompts import PROMPT_CONFLICT_EXPLANATION
from .models import ConflictInfo, ConflictExplanation


class ConflictExplainer:
    """Provides AI-powered explanations of merge conflicts."""

    def __init__(self):
        """Initialize the conflict explainer."""
        pass

    def explain_conflict(self, conflict: ConflictInfo, context: str = "") -> ConflictExplanation:
        """
        Generate an AI-powered explanation of a merge conflict.
        
        Args:
            conflict: ConflictInfo object containing conflict details
            context: Additional context about the merge operation
            
        Returns:
            ConflictExplanation with human-readable explanation
        """
        try:
            # Prepare the prompt
            prompt = self._build_explanation_prompt(conflict, context)
            
            # Get AI response
            llm_response = get_llm_response(prompt)
            
            # Parse the response into structured explanation
            explanation = self._parse_explanation_response(llm_response)
            
            return explanation
            
        except Exception as e:
            # Fallback to basic explanation if AI fails
            return self._generate_fallback_explanation(conflict)

    def _build_explanation_prompt(self, conflict: ConflictInfo, context: str) -> str:
        """Build the AI prompt for conflict explanation with enhanced context."""
        # Determine file type context
        file_context = self._get_file_context(conflict.file_path)
        
        # Decide whether to use full file or just context based on file size
        use_full_file = len(conflict.full_file_content.splitlines()) <= 100
        
        if use_full_file:
            # For smaller files, provide the complete file content
            content_for_ai = f"""
=== FULL FILE CONTENT ({conflict.file_path}) ===
{conflict.full_file_content}

=== CONFLICT LOCATION ===
Lines {conflict.start_line + 1}-{conflict.end_line + 1} have conflicts.

=== OUR VERSION (Current Branch) ===
{conflict.our_content}

=== THEIR VERSION (Incoming Branch) ===
{conflict.their_content}
"""
        else:
            # For larger files, provide context window around the conflict
            content_for_ai = f"""
=== CONTEXT AROUND CONFLICT ({conflict.file_path}) ===
Showing lines {conflict.context_start_line + 1}-{conflict.context_end_line + 1}

{conflict.full_context}

=== CONFLICT DETAILS ===
Location: Lines {conflict.start_line + 1}-{conflict.end_line + 1}

Our Version (Current Branch):
{conflict.our_content}

Their Version (Incoming Branch):
{conflict.their_content}
"""
        
        # Combine all context
        full_context = f"{file_context}. {context}".strip()
        
        prompt = PROMPT_CONFLICT_EXPLANATION.replace("{{file_path}}", conflict.file_path)
        prompt = prompt.replace("{{file_content}}", content_for_ai)
        prompt = prompt.replace("{{context}}", full_context)
        
        # Legacy support for older prompt format
        prompt = prompt.replace("{{our_content}}", conflict.our_content or "No content")
        prompt = prompt.replace("{{their_content}}", conflict.their_content or "No content")
        
        return prompt

    def _get_file_context(self, file_path: str) -> str:
        """Get context about the file type and purpose."""
        file_lower = file_path.lower()
        
        if file_path.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs')):
            return "This is a source code file"
        elif file_path.endswith(('.md', '.rst', '.txt')):
            return "This is a documentation file"
        elif file_path.endswith(('.json', '.yaml', '.yml', '.toml', '.ini')):
            return "This is a configuration file"
        elif file_path.endswith(('.html', '.css', '.scss', '.less')):
            return "This is a web frontend file"
        elif 'test' in file_lower:
            return "This is a test file"
        elif 'config' in file_lower:
            return "This is a configuration file"
        elif 'readme' in file_lower:
            return "This is a README documentation file"
        else:
            return "This is a project file"

    def _parse_explanation_response(self, response: str) -> ConflictExplanation:
        """
        Parse the AI response into a structured ConflictExplanation.
        
        This is a simplified parser - could be enhanced with more sophisticated parsing.
        """
        lines = response.strip().split('\n')
        
        # Initialize with defaults
        summary = ""
        our_intent = ""
        their_intent = ""
        suggested_approach = ""
        resolution_steps = []
        
        # Simple parsing logic
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for section indicators
            if 'summary' in line.lower() or 'overview' in line.lower():
                current_section = 'summary'
                continue
            elif 'our' in line.lower() and ('changes' in line.lower() or 'intent' in line.lower()):
                current_section = 'our_intent'
                continue
            elif 'their' in line.lower() and ('changes' in line.lower() or 'intent' in line.lower()):
                current_section = 'their_intent'
                continue
            elif 'approach' in line.lower() or 'solution' in line.lower():
                current_section = 'approach'
                continue
            elif 'steps' in line.lower() or 'resolution' in line.lower():
                current_section = 'steps'
                continue
            
            # Assign content to sections
            if current_section == 'summary':
                summary += line + " "
            elif current_section == 'our_intent':
                our_intent += line + " "
            elif current_section == 'their_intent':
                their_intent += line + " "
            elif current_section == 'approach':
                suggested_approach += line + " "
            elif current_section == 'steps':
                if line.startswith(('-', '*', '1.', '2.', '3.')):
                    resolution_steps.append(line)
            else:
                # If no section identified, add to summary
                if not summary:
                    summary += line + " "
        
        # If parsing didn't work well, use the full response as summary
        if not summary and not our_intent and not their_intent:
            summary = response[:200] + "..." if len(response) > 200 else response
            
        return ConflictExplanation(
            summary=summary.strip() or "Conflict detected in file",
            our_intent=our_intent.strip() or "Current branch modifications",
            their_intent=their_intent.strip() or "Incoming branch modifications",
            suggested_approach=suggested_approach.strip() or "Manual resolution required",
            resolution_steps=resolution_steps or ["Review both changes", "Choose appropriate resolution", "Test the result"]
        )

    def _generate_fallback_explanation(self, conflict: ConflictInfo) -> ConflictExplanation:
        """Generate a basic explanation when AI is unavailable."""
        file_type = self._get_file_context(conflict.file_path)
        
        return ConflictExplanation(
            summary=f"Merge conflict detected in {conflict.file_path}. Both branches modified the same section.",
            our_intent="Current branch has local modifications to this section.",
            their_intent="Incoming branch has different modifications to the same section.",
            suggested_approach="Review both sets of changes and manually combine them appropriately.",
            resolution_steps=[
                f"Open {conflict.file_path} in your editor",
                "Look for conflict markers (<<<<<<< ======= >>>>>>>)",
                "Review both versions of the conflicted code",
                "Choose or combine the changes as appropriate",
                "Remove conflict markers",
                "Test your changes"
            ]
        )

    def explain_multiple_conflicts(self, conflicts: list[ConflictInfo], context: str = "") -> dict[str, ConflictExplanation]:
        """
        Explain multiple conflicts efficiently.
        
        Args:
            conflicts: List of ConflictInfo objects
            context: Additional context about the merge
            
        Returns:
            Dictionary mapping file paths to their explanations
        """
        explanations = {}
        
        for conflict in conflicts:
            try:
                explanation = self.explain_conflict(conflict, context)
                explanations[conflict.file_path] = explanation
            except Exception:
                # Continue with other conflicts even if one fails
                explanations[conflict.file_path] = self._generate_fallback_explanation(conflict)
                
        return explanations

    def get_conflict_summary(self, conflicts: list[ConflictInfo]) -> str:
        """
        Generate a high-level summary of all conflicts.
        
        Args:
            conflicts: List of ConflictInfo objects
            
        Returns:
            Human-readable summary of all conflicts
        """
        if not conflicts:
            return "No conflicts detected."
            
        total_conflicts = len(conflicts)
        file_types = {}
        
        for conflict in conflicts:
            file_ext = conflict.file_path.split('.')[-1] if '.' in conflict.file_path else 'unknown'
            file_types[file_ext] = file_types.get(file_ext, 0) + 1
            
        summary = f"Found {total_conflicts} conflict(s) across {len(file_types)} file type(s):\n"
        
        for file_type, count in file_types.items():
            summary += f"  • {count} {file_type} file(s)\n"
            
        return summary.strip() 