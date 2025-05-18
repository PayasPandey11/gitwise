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

def get_changed_files() -> List[str]:
    """Get list of files changed in the PR.
    
    Returns:
        List of changed file paths.
    """
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main..."],
        capture_output=True,
        text=True
    )
    return [f for f in result.stdout.splitlines() if f]

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
    use_labels: bool = True,
    use_checklist: bool = True,
    skip_general_checklist: bool = False
) -> Tuple[str, List[str]]:
    """Enhance PR description with labels and checklist.
    
    Args:
        commits: List of commit dictionaries.
        description: Original PR description.
        use_labels: Whether to add labels.
        use_checklist: Whether to add checklist.
        skip_general_checklist: Whether to skip general checklist items.
        
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
        files = get_changed_files()
        checklist = generate_checklist(files, skip_general_checklist)
        enhanced_description = f"{description}\n\n## Checklist\n{checklist}"
    
    return enhanced_description, labels 