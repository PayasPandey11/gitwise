"""Data models for the Smart Merge feature."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class ConflictType(Enum):
    """Types of merge conflicts."""
    CONTENT = "content"
    DELETE_MODIFY = "delete_modify"
    MODIFY_DELETE = "modify_delete"
    BOTH_MODIFIED = "both_modified"
    BOTH_ADDED = "both_added"


class MergeStrategy(Enum):
    """Merge strategies."""
    AUTO = "auto"
    MANUAL = "manual"
    OURS = "ours"
    THEIRS = "theirs"


@dataclass
class ConflictInfo:
    """Information about a merge conflict in a specific file."""
    file_path: str
    conflict_type: ConflictType
    conflict_lines: List[int]
    our_content: str
    their_content: str
    base_content: Optional[str] = None
    # Enhanced context fields
    before_context: str = ""
    after_context: str = ""
    full_context: str = ""
    full_file_content: str = ""
    start_line: int = 0
    end_line: int = 0
    context_start_line: int = 0
    context_end_line: int = 0


@dataclass
class ConflictExplanation:
    """AI-generated explanation of a merge conflict."""
    summary: str
    our_intent: str
    their_intent: str
    suggested_approach: str
    resolution_steps: List[str]


@dataclass
class BranchChanges:
    """Summary of changes in a branch."""
    added_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    renamed_files: List[Dict[str, str]]  # [{"old": "path1", "new": "path2"}]
    total_commits: int
    commit_messages: List[str]


@dataclass
class MergeAnalysis:
    """Complete analysis of a merge operation."""
    source_branch: str
    target_branch: str
    merge_base: Optional[str]
    conflicts: List[ConflictInfo]
    source_changes: BranchChanges
    target_changes: BranchChanges
    can_fast_forward: bool
    is_clean_merge: bool
    total_files_changed: int


@dataclass
class ResolutionStrategy:
    """AI-suggested strategy for resolving conflicts."""
    strategy_type: MergeStrategy
    description: str
    steps: List[str]
    estimated_difficulty: str  # "easy", "medium", "hard"
    warnings: List[str]
    alternative_strategies: List[Dict[str, Any]]


@dataclass
class MergeOptions:
    """Options for performing a merge operation."""
    strategy: MergeStrategy = MergeStrategy.AUTO
    no_commit: bool = False
    no_ff: bool = False
    squash: bool = False
    edit_message: bool = True
    abort_on_conflict: bool = False


@dataclass
class MergeResult:
    """Result of a merge operation."""
    success: bool
    conflicts_detected: bool
    merge_commit: Optional[str]
    message: str
    conflicts: List[ConflictInfo]
    next_steps: List[str] 