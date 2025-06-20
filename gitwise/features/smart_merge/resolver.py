"""AI-powered conflict resolution strategy suggester."""

from typing import List, Dict, Any

from gitwise.llm.router import get_llm_response
from gitwise.prompts import PROMPT_RESOLUTION_STRATEGY
from .models import ConflictInfo, ResolutionStrategy, MergeStrategy


class ResolutionSuggester:
    """Provides AI-powered suggestions for resolving merge conflicts."""

    def __init__(self):
        """Initialize the resolution suggester."""
        pass

    def suggest_strategy(self, conflicts: List[ConflictInfo], context: str = "") -> ResolutionStrategy:
        """
        Generate AI-powered resolution strategy for conflicts.
        
        Args:
            conflicts: List of ConflictInfo objects
            context: Additional context about the merge operation
            
        Returns:
            ResolutionStrategy with detailed suggestions
        """
        try:
            # Analyze conflict patterns
            patterns = self._analyze_conflict_patterns(conflicts)
            
            # Build AI prompt
            prompt = self._build_strategy_prompt(conflicts, patterns, context)
            
            # Get AI response
            llm_response = get_llm_response(prompt)
            
            # Parse response into strategy
            strategy = self._parse_strategy_response(llm_response, conflicts)
            
            return strategy
            
        except Exception:
            # Fallback to basic strategy if AI fails
            return self._generate_fallback_strategy(conflicts)

    def _analyze_conflict_patterns(self, conflicts: List[ConflictInfo]) -> Dict[str, Any]:
        """Analyze conflicts to identify common patterns."""
        patterns = {
            "file_types": {},
            "conflict_types": {},
            "complexity": "medium",
            "common_patterns": []
        }
        
        # Analyze file types
        for conflict in conflicts:
            file_ext = conflict.file_path.split('.')[-1] if '.' in conflict.file_path else 'unknown'
            patterns["file_types"][file_ext] = patterns["file_types"].get(file_ext, 0) + 1
            
            # Track conflict types
            patterns["conflict_types"][conflict.conflict_type.value] = \
                patterns["conflict_types"].get(conflict.conflict_type.value, 0) + 1
        
        # Determine complexity
        if len(conflicts) == 1:
            patterns["complexity"] = "easy"
        elif len(conflicts) > 5:
            patterns["complexity"] = "hard"
            
        # Identify common patterns
        if patterns["file_types"].get("py", 0) > 0:
            patterns["common_patterns"].append("python_code")
        if patterns["file_types"].get("json", 0) > 0 or patterns["file_types"].get("yaml", 0) > 0:
            patterns["common_patterns"].append("configuration")
        if any("test" in c.file_path.lower() for c in conflicts):
            patterns["common_patterns"].append("test_files")
        if any("readme" in c.file_path.lower() for c in conflicts):
            patterns["common_patterns"].append("documentation")
            
        return patterns

    def _build_strategy_prompt(self, conflicts: List[ConflictInfo], patterns: Dict[str, Any], context: str) -> str:
        """Build the AI prompt for resolution strategy."""
        # Create conflicts summary
        conflicts_summary = f"{len(conflicts)} conflicts detected:\n"
        for conflict in conflicts:
            conflicts_summary += f"  • {conflict.file_path} ({conflict.conflict_type.value})\n"
            
        # Create files list
        files_list = ", ".join([c.file_path for c in conflicts])
        
        # Enhanced context with patterns
        branch_context = f"{context}\n\nDetected patterns:"
        if patterns["common_patterns"]:
            branch_context += f"\n  • File types: {list(patterns['file_types'].keys())}"
            branch_context += f"\n  • Complexity: {patterns['complexity']}"
            branch_context += f"\n  • Common patterns: {', '.join(patterns['common_patterns'])}"
        
        prompt = PROMPT_RESOLUTION_STRATEGY.replace("{{conflicts_summary}}", conflicts_summary)
        prompt = prompt.replace("{{files_list}}", files_list)
        prompt = prompt.replace("{{branch_context}}", branch_context)
        
        return prompt

    def _parse_strategy_response(self, response: str, conflicts: List[ConflictInfo]) -> ResolutionStrategy:
        """Parse AI response into a structured ResolutionStrategy."""
        lines = response.strip().split('\n')
        
        # Initialize defaults
        strategy_type = MergeStrategy.MANUAL
        description = ""
        steps = []
        estimated_difficulty = "medium"
        warnings = []
        alternative_strategies = []
        
        # Parse response
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for section indicators
            if 'strategy' in line.lower() or 'approach' in line.lower():
                current_section = 'strategy'
                if 'manual' in line.lower():
                    strategy_type = MergeStrategy.MANUAL
                elif 'auto' in line.lower():
                    strategy_type = MergeStrategy.AUTO
                continue
            elif 'steps' in line.lower() or 'resolution' in line.lower():
                current_section = 'steps'
                continue
            elif 'warning' in line.lower() or 'caution' in line.lower():
                current_section = 'warnings'
                continue
            elif 'difficulty' in line.lower():
                current_section = 'difficulty'
                if 'easy' in line.lower():
                    estimated_difficulty = 'easy'
                elif 'hard' in line.lower():
                    estimated_difficulty = 'hard'
                continue
            elif 'alternative' in line.lower():
                current_section = 'alternatives'
                continue
            
            # Assign content to sections
            if current_section == 'strategy':
                description += line + " "
            elif current_section == 'steps':
                if line.startswith(('-', '*', '1.', '2.', '3.', '4.', '5.')):
                    steps.append(line)
            elif current_section == 'warnings':
                if line.startswith(('-', '*', '!')):
                    warnings.append(line)
            elif current_section == 'alternatives':
                if line.startswith(('-', '*')):
                    alternative_strategies.append({"description": line, "complexity": "medium"})
            else:
                # Default to description if no section
                if not description:
                    description += line + " "
        
        # Generate default steps if none were parsed
        if not steps:
            steps = self._generate_default_steps(conflicts)
            
        return ResolutionStrategy(
            strategy_type=strategy_type,
            description=description.strip() or "Manual resolution of conflicts required",
            steps=steps,
            estimated_difficulty=estimated_difficulty,
            warnings=warnings,
            alternative_strategies=alternative_strategies
        )

    def _generate_default_steps(self, conflicts: List[ConflictInfo]) -> List[str]:
        """Generate default resolution steps based on conflicts."""
        steps = [
            "1. Review each conflicted file individually",
            "2. Understand the intent behind both sets of changes"
        ]
        
        for i, conflict in enumerate(conflicts, 3):
            steps.append(f"{i}. Resolve conflicts in {conflict.file_path}")
            
        steps.extend([
            f"{len(conflicts) + 3}. Remove all conflict markers",
            f"{len(conflicts) + 4}. Test the merged result",
            f"{len(conflicts) + 5}. Commit the resolution"
        ])
        
        return steps

    def _generate_fallback_strategy(self, conflicts: List[ConflictInfo]) -> ResolutionStrategy:
        """Generate a basic strategy when AI is unavailable."""
        file_list = ", ".join([c.file_path for c in conflicts])
        
        # Determine difficulty based on number and types of conflicts
        if len(conflicts) == 1:
            difficulty = "easy"
        elif len(conflicts) <= 3:
            difficulty = "medium"
        else:
            difficulty = "hard"
            
        steps = [
            "1. Open each conflicted file in your preferred editor",
            "2. Look for conflict markers: <<<<<<< ======= >>>>>>>",
            "3. Review both versions of the conflicted sections",
            "4. Choose the appropriate resolution for each conflict",
            "5. Remove all conflict markers",
            "6. Test your changes thoroughly",
            "7. Stage and commit the resolved files"
        ]
        
        warnings = []
        if len(conflicts) > 3:
            warnings.append("Multiple conflicts detected - take extra care to maintain functionality")
        if any("test" in c.file_path.lower() for c in conflicts):
            warnings.append("Test files are conflicted - ensure test suite still passes")
        if any(c.file_path.endswith(('.json', '.yaml', '.yml')) for c in conflicts):
            warnings.append("Configuration files are conflicted - verify syntax after resolution")
            
        return ResolutionStrategy(
            strategy_type=MergeStrategy.MANUAL,
            description=f"Manual resolution required for {len(conflicts)} conflict(s) in: {file_list}",
            steps=steps,
            estimated_difficulty=difficulty,
            warnings=warnings,
            alternative_strategies=[
                {
                    "description": "Use git mergetool for guided resolution",
                    "complexity": "medium"
                },
                {
                    "description": "Abort merge and reapply changes manually",
                    "complexity": "hard"
                }
            ]
        )

    def suggest_file_specific_strategy(self, conflict: ConflictInfo) -> Dict[str, str]:
        """
        Suggest file-specific resolution approach.
        
        Args:
            conflict: ConflictInfo for a specific file
            
        Returns:
            Dictionary with file-specific suggestions
        """
        file_path = conflict.file_path.lower()
        suggestions = {}
        
        if file_path.endswith('.py'):
            suggestions = {
                "approach": "Review both code changes for logic conflicts",
                "tools": "Use Python syntax highlighting and linting",
                "testing": "Run unit tests after resolution"
            }
        elif file_path.endswith(('.json', '.yaml', '.yml')):
            suggestions = {
                "approach": "Merge configuration values carefully",
                "tools": "Validate JSON/YAML syntax after changes",
                "testing": "Test application with new configuration"
            }
        elif file_path.endswith(('.md', '.rst', '.txt')):
            suggestions = {
                "approach": "Combine documentation changes logically",
                "tools": "Preview rendered documentation",
                "testing": "Check for broken links or formatting"
            }
        elif 'test' in file_path:
            suggestions = {
                "approach": "Merge test cases without duplication",
                "tools": "Run the specific test file",
                "testing": "Ensure all tests pass after resolution"
            }
        else:
            suggestions = {
                "approach": "Review changes based on file purpose",
                "tools": "Use appropriate editor for file type",
                "testing": "Test functionality affected by this file"
            }
            
        return suggestions 