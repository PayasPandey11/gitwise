"""PR enhancement features for GitWise."""

import re
import json
import os
from typing import List, Dict, Set, Tuple, Optional
from gitwise.llm import get_llm_response

# Default mapping of commit types to GitHub labels
DEFAULT_COMMIT_TYPE_LABELS = {
    'feat': 'enhancement',
    'fix': 'bug',
    'docs': 'documentation',
    'style': 'style',
    'refactor': 'refactor',
    'test': 'test',
    'chore': 'chore',
    'perf': 'performance',
    'security': 'security',
    'ci': 'ci',
    'build': 'build',
    'revert': 'revert'
}

# Extended file patterns and their checklist items
FILE_PATTERN_CHECKLISTS = {
    r'\.py$': [
        "Added/updated docstrings",
        "Added/updated type hints",
        "Added/updated tests",
        "Updated README if needed",
        "Checked for unused imports",
        "Verified error handling",
        "Added logging if needed"
    ],
    r'\.md$': [
        "Checked for broken links",
        "Verified formatting",
        "Updated table of contents if needed",
        "Checked for proper heading hierarchy",
        "Verified code block syntax",
        "Added alt text for images"
    ],
    r'\.json$': [
        "Validated JSON format",
        "Updated schema if needed",
        "Checked for sensitive data",
        "Verified indentation"
    ],
    r'\.yaml$|\.yml$': [
        "Validated YAML format",
        "Updated schema if needed",
        "Checked for sensitive data",
        "Verified indentation",
        "Checked for duplicate keys"
    ],
    r'\.js$|\.ts$': [
        "Added/updated JSDoc comments",
        "Added/updated tests",
        "Updated README if needed",
        "Checked for unused variables",
        "Verified error handling",
        "Added type definitions if needed"
    ],
    r'\.css$|\.scss$': [
        "Checked browser compatibility",
        "Added/updated comments",
        "Updated style guide if needed",
        "Verified responsive design",
        "Checked for unused styles",
        "Added vendor prefixes if needed"
    ],
    r'\.html$': [
        "Verified accessibility",
        "Checked for proper meta tags",
        "Validated HTML structure",
        "Checked for broken links",
        "Verified responsive design"
    ],
    r'\.sql$': [
        "Added/updated documentation",
        "Checked for SQL injection risks",
        "Verified indexes",
        "Added migration script if needed",
        "Checked for sensitive data"
    ],
    r'\.sh$': [
        "Added/updated documentation",
        "Checked for proper error handling",
        "Verified file permissions",
        "Added shebang line",
        "Checked for shell compatibility"
    ],
    r'\.dockerfile$|Dockerfile': [
        "Added/updated documentation",
        "Checked for security best practices",
        "Verified base image version",
        "Added health check if needed",
        "Checked for unnecessary layers"
    ],
    r'\.env$|\.env\.': [
        "Checked for sensitive data",
        "Added to .gitignore if needed",
        "Provided example file",
        "Updated documentation"
    ],
    r'\.gitignore$': [
        "Checked for necessary patterns",
        "Verified no important files ignored",
        "Added comments for clarity"
    ],
    r'\.editorconfig$': [
        "Verified settings match project",
        "Added comments for clarity",
        "Checked for necessary rules"
    ],
    r'\.eslintrc$|\.prettierrc$': [
        "Verified settings match project",
        "Added comments for clarity",
        "Checked for necessary rules"
    ],
    r'\.github/workflows/.*\.yml$': [
        "Verified workflow triggers",
        "Checked for necessary permissions",
        "Added comments for clarity",
        "Verified environment variables"
    ]
}

def load_custom_labels() -> Dict[str, str]:
    """Load custom label mappings from config file.
    
    Returns:
        Dictionary mapping commit types to custom labels.
    """
    config_path = os.path.expanduser('~/.gitwise/labels.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Invalid labels.json file. Using default labels.")
    return {}

def extract_commit_types(commits: List[Dict[str, str]]) -> Set[str]:
    """Extract commit types from commit messages.
    
    Args:
        commits: List of commit dictionaries containing message.
        
    Returns:
        Set of commit types found in the messages.
    """
    types = set()
    for commit in commits:
        # Match conventional commit format: type(scope): description
        match = re.match(r'^(\w+)(?:\([^)]+\))?:', commit['message'])
        if match:
            commit_type = match.group(1)
            if commit_type in DEFAULT_COMMIT_TYPE_LABELS:
                types.add(commit_type)
    return types

def get_pr_labels(commits: List[Dict[str, str]], use_custom_labels: bool = True) -> List[str]:
    """Get GitHub labels based on commit types.
    
    Args:
        commits: List of commit dictionaries containing message.
        use_custom_labels: Whether to use custom label mappings.
        
    Returns:
        List of GitHub labels to apply.
    """
    commit_types = extract_commit_types(commits)
    labels = DEFAULT_COMMIT_TYPE_LABELS.copy()
    
    if use_custom_labels:
        custom_labels = load_custom_labels()
        labels.update(custom_labels)
    
    return [labels[type_] for type_ in commit_types if type_ in labels]

def get_changed_files(base_branch: str = "origin/main") -> List[str]:
    """Get list of files changed in the PR.
    
    Args:
        base_branch: The base branch to compare against (e.g., "origin/main", "origin/develop").

    Returns:
        List of changed file paths.
    """
    import subprocess
    # Ensure base_branch is prefixed with origin/ if not already, for comparison with remote
    # However, for local diffs against a local base branch, origin/ might not be correct.
    # Assuming base_branch parameter is the correct reference for diffing.
    # For `gh pr create`, the base branch is usually a local branch name like `main` or `develop`.
    # `git diff` needs a commit-ish. If current branch is `feature` and base is `main`,
    # it should be `git diff main...feature` (or main...HEAD if on feature)
    # The `gh pr create` implies changes on the current branch relative to `base_branch`.
    # So we need to find commits on current branch not in base_branch.

    try:
        # Get current branch name
        current_branch_result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
        current_branch = current_branch_result.stdout.strip()

        # Diff current branch against the provided base branch
        # Using three dots `...` for symmetric difference might not be what we want for PR files.
        # We want changes in `current_branch` since it diverged from `base_branch`.
        # `git diff base_branch..current_branch --name-only` is usually correct.
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}..{current_branch}"],
            capture_output=True,
            text=True,
            check=True # Add check=True
        )
        return [f for f in result.stdout.splitlines() if f]
    except subprocess.CalledProcessError as e:
        # Fallback or error handling
        print(f"Warning: Could not get changed files using base '{base_branch}': {e}. Falling back to diff against origin/main if applicable or HEAD.")
        # Fallback to diffing against HEAD, which might show uncommitted changes if not careful,
        # or against a common default if base_branch was problematic.
        # For checklist, it might be better to return empty list or raise if diff fails.
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"], # Diff against HEAD (staged changes for current commit)
                capture_output=True,
                text=True,
                check=True
            )
            print("Warning: Fallback diff is against HEAD, this may not represent all PR changes accurately for checklist.")
            return [f for f in result.stdout.splitlines() if f]
        except subprocess.CalledProcessError:
             print(f"Error: Could not get changed files for checklist generation even with fallback: {e}")
             return []

def generate_checklist(files: List[str], skip_general: bool = False) -> str:
    """Generate a checklist based on changed files.
    
    Args:
        files: List of changed file paths.
        skip_general: Whether to skip general checklist items.
        
    Returns:
        Markdown formatted checklist.
    """
    checklist_items = set()
    
    # Add items based on file patterns
    for file in files:
        for pattern, items in FILE_PATTERN_CHECKLISTS.items():
            if re.search(pattern, file):
                checklist_items.update(items)
    
    # Add general items if not skipped
    if not skip_general:
        checklist_items.update([
            "Code follows project style guide",
            "All tests pass",
            "Documentation is up to date",
            "No sensitive data in changes",
            "Changes are backward compatible",
            "Performance impact considered",
            "Security implications reviewed"
        ])
    
    # Format as markdown checklist
    return "\n".join(f"- [ ] {item}" for item in sorted(checklist_items))

def enhance_pr_description(
    commits: List[Dict[str, str]], 
    description: str,
    use_labels: bool = False,
    use_checklist: bool = False,
    skip_general_checklist: bool = False,
    base_branch_for_checklist: str = "origin/main"
) -> Tuple[str, List[str]]:
    """Enhance PR description with labels and checklist.
    
    Args:
        commits: List of commit dictionaries.
        description: Original PR description.
        use_labels: Whether to add labels (default: False).
        use_checklist: Whether to add checklist (default: False).
        skip_general_checklist: Whether to skip general checklist items (default: False).
        base_branch_for_checklist: The base branch to use for generating the checklist.
        
    Returns:
        Tuple of (enhanced description, labels)
    """
    enhanced_description = description
    labels = []
    
    # Get labels if enabled
    if use_labels:
        labels = get_pr_labels(commits)
    
    # Get changed files and generate checklist if enabled
    if use_checklist:
        files = get_changed_files(base_branch=base_branch_for_checklist)
        if files:
            checklist = generate_checklist(files, skip_general_checklist)
            enhanced_description = f"{description}\n\n## Checklist\n{checklist}"
    
    return enhanced_description, labels 