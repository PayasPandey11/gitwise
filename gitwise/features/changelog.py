"""Changelog generation feature for GitWise."""

import subprocess
from typing import List, Dict, Optional
from gitwise.llm import get_llm_response
from gitwise.gitutils import get_commit_history

def get_version_tags() -> List[str]:
    """Get all version tags from the repository.
    
    Returns:
        List of version tags sorted by creation date.
    """
    result = subprocess.run(
        ["git", "tag", "--sort=-creatordate"],
        capture_output=True,
        text=True
    )
    return [tag for tag in result.stdout.splitlines() if tag]

def get_commits_between_tags(start_tag: Optional[str], end_tag: str) -> List[Dict[str, str]]:
    """Get commits between two tags.
    
    Args:
        start_tag: Starting tag (exclusive). If None, gets all commits up to end_tag.
        end_tag: Ending tag (inclusive).
        
    Returns:
        List of commit dictionaries.
    """
    range_spec = f"{start_tag}..{end_tag}" if start_tag else end_tag
    result = subprocess.run(
        ["git", "log", range_spec, "--pretty=format:%H|%s|%an"],
        capture_output=True,
        text=True
    )
    
    commits = []
    for line in result.stdout.splitlines():
        if line:
            hash_, message, author = line.split("|")
            commits.append({
                "hash": hash_,
                "message": message,
                "author": author
            })
    return commits

def categorize_changes(commits: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Categorize commits by type.
    
    Args:
        commits: List of commit dictionaries.
        
    Returns:
        Dictionary mapping commit types to lists of commits.
    """
    categories = {
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Style": [],
        "Refactor": [],
        "Performance": [],
        "Tests": [],
        "Chores": [],
        "Other": []
    }
    
    type_mapping = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "docs": "Documentation",
        "style": "Style",
        "refactor": "Refactor",
        "perf": "Performance",
        "test": "Tests",
        "chore": "Chores"
    }
    
    for commit in commits:
        message = commit["message"]
        # Check for conventional commit format
        if ":" in message:
            type_ = message.split(":")[0].lower()
            if type_ in type_mapping:
                categories[type_mapping[type_]].append(commit)
                continue
        categories["Other"].append(commit)
    
    return categories

def generate_changelog_entry(version: str, commits: List[Dict[str, str]]) -> str:
    """Generate a changelog entry for a version.
    
    Args:
        version: Version number.
        commits: List of commit dictionaries.
        
    Returns:
        Markdown formatted changelog entry.
    """
    # Categorize commits
    categories = categorize_changes(commits)
    
    # Generate changelog entry
    changelog = f"## {version}\n\n"
    
    # Add date
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ad", "--date=short", f"v{version}"],
        capture_output=True,
        text=True
    )
    date = result.stdout.strip()
    changelog += f"*Released on {date}*\n\n"
    
    # Add categorized changes
    for category, category_commits in categories.items():
        if category_commits:
            changelog += f"### {category}\n\n"
            for commit in category_commits:
                # Extract the description part after the type
                message = commit["message"]
                if ":" in message:
                    message = message.split(":", 1)[1].strip()
                changelog += f"- {message}\n"
            changelog += "\n"
    
    return changelog

def changelog_command(version: Optional[str] = None) -> None:
    """Generate a changelog for the repository.
    
    Args:
        version: Optional version to generate changelog for. If not provided,
                generates changelog for all versions.
    """
    try:
        # Get version tags
        tags = get_version_tags()
        if not tags:
            print("No version tags found in the repository.")
            print("Create a version tag using: git tag v1.0.0")
            return
        
        if version:
            if version not in tags:
                print(f"Version {version} not found in repository tags.")
                print("Available versions:", ", ".join(tags))
                return
            tags = [version]
        
        # Generate changelog
        changelog = "# Changelog\n\n"
        
        # Process each version
        for i, tag in enumerate(tags):
            start_tag = tags[i + 1] if i + 1 < len(tags) else None
            commits = get_commits_between_tags(start_tag, tag)
            if commits:
                changelog += generate_changelog_entry(tag, commits)
        
        # Write to CHANGELOG.md
        with open("CHANGELOG.md", "w") as f:
            f.write(changelog)
        
        print(f"✅ Changelog generated successfully: CHANGELOG.md")
        
    except Exception as e:
        print(f"❌ Error generating changelog: {str(e)}")
        print("Please make sure you have version tags in your repository.") 