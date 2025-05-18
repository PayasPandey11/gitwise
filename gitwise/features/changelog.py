"""Changelog generation feature for GitWise."""

import subprocess
import re
from typing import List, Dict, Optional, Tuple, NamedTuple
from gitwise.llm import get_llm_response
from gitwise.gitutils import get_commit_history
import typer

class VersionInfo(NamedTuple):
    """Version information with pre-release and build metadata."""
    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None
    build_metadata: Optional[str] = None

    def __lt__(self, other: 'VersionInfo') -> bool:
        """Compare versions according to semver spec."""
        # Compare main version numbers
        if (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch):
            return True
        if (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch):
            return False
        
        # If main versions are equal, compare pre-release
        if self.pre_release is None and other.pre_release is None:
            return False
        if self.pre_release is None:
            return False  # No pre-release is greater than pre-release
        if other.pre_release is None:
            return True  # Pre-release is less than no pre-release
        
        # Compare pre-release identifiers
        self_parts = self.pre_release.split('.')
        other_parts = other.pre_release.split('.')
        
        for i in range(max(len(self_parts), len(other_parts))):
            if i >= len(self_parts):
                return True  # Shorter pre-release is less
            if i >= len(other_parts):
                return False  # Longer pre-release is greater
            
            # Try to compare as numbers first
            try:
                self_num = int(self_parts[i])
                other_num = int(other_parts[i])
                if self_num != other_num:
                    return self_num < other_num
            except ValueError:
                # Compare as strings if not numbers
                if self_parts[i] != other_parts[i]:
                    return self_parts[i] < other_parts[i]
        
        return False

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

def get_latest_version() -> Optional[str]:
    """Get the latest version tag from the repository.
    
    Returns:
        Latest version tag or None if no tags exist.
    """
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        capture_output=True,
        text=True
    )
    tags = [tag for tag in result.stdout.splitlines() if tag]
    return tags[0] if tags else None

def get_latest_pre_release(version_type: str) -> Optional[str]:
    """Get the latest pre-release version of a specific type.
    
    Args:
        version_type: Type of pre-release (e.g., 'alpha', 'beta', 'rc').
        
    Returns:
        Latest pre-release version string or None if none found.
    """
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        capture_output=True,
        text=True
    )
    
    pattern = re.compile(f"v\\d+\\.\\d+\\.\\d+-{version_type}\\.(\\d+)")
    latest_num = 0
    
    for tag in result.stdout.splitlines():
        match = pattern.match(tag)
        if match:
            num = int(match.group(1))
            latest_num = max(latest_num, num)
    
    return f"{version_type}.{latest_num + 1}" if latest_num > 0 else f"{version_type}.1"

def parse_version(version: str) -> VersionInfo:
    """Parse version string into components.
    
    Args:
        version: Version string (e.g., "v1.2.3-alpha.1+build.123").
        
    Returns:
        VersionInfo tuple with version components.
        
    Raises:
        ValueError: If version format is invalid.
    """
    # Remove 'v' prefix
    version = version.lstrip('v')
    
    # Split into main version and pre-release/build
    main_version, *extras = version.split('+', 1)
    build_metadata = extras[0] if extras else None
    
    # Split main version and pre-release
    main_version, *pre_release = main_version.split('-', 1)
    pre_release = pre_release[0] if pre_release else None
    
    # Parse main version
    try:
        major, minor, patch = map(int, main_version.split('.'))
    except ValueError:
        raise ValueError("Version must be in format vX.Y.Z")
    
    # Validate pre-release format if present
    if pre_release:
        if not re.match(r'^[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*$', pre_release):
            raise ValueError("Pre-release must be in format: alpha.1, beta.2, rc.1, etc.")
    
    return VersionInfo(major, minor, patch, pre_release, build_metadata)

def format_version(version: VersionInfo) -> str:
    """Format VersionInfo into version string.
    
    Args:
        version: VersionInfo tuple.
        
    Returns:
        Formatted version string.
    """
    version_str = f"v{version.major}.{version.minor}.{version.patch}"
    if version.pre_release:
        version_str += f"-{version.pre_release}"
    if version.build_metadata:
        version_str += f"+{version.build_metadata}"
    return version_str

def analyze_commits_for_version(commits: List[Dict[str, str]]) -> Dict[str, bool]:
    """Analyze commits to determine version bump type.
    
    Args:
        commits: List of commit dictionaries.
        
    Returns:
        Dictionary with version bump indicators.
    """
    analysis = {
        "has_breaking": False,
        "has_feature": False,
        "has_fix": False,
        "has_docs": False,
        "has_perf": False,
        "has_refactor": False,
        "has_test": False,
        "has_style": False,
        "has_chore": False
    }
    
    for commit in commits:
        message = commit["message"].lower()
        
        # Check for breaking changes
        if "!" in message or "breaking" in message:
            analysis["has_breaking"] = True
        
        # Check commit types
        if message.startswith("feat:"):
            analysis["has_feature"] = True
        elif message.startswith("fix:"):
            analysis["has_fix"] = True
        elif message.startswith("docs:"):
            analysis["has_docs"] = True
        elif message.startswith("perf:"):
            analysis["has_perf"] = True
        elif message.startswith("refactor:"):
            analysis["has_refactor"] = True
        elif message.startswith("test:"):
            analysis["has_test"] = True
        elif message.startswith("style:"):
            analysis["has_style"] = True
        elif message.startswith("chore:"):
            analysis["has_chore"] = True
    
    return analysis

def suggest_next_version(commits: List[Dict[str, str]]) -> Tuple[str, str]:
    """Suggest the next version based on commit types.
    
    Args:
        commits: List of commit dictionaries.
        
    Returns:
        Tuple of (suggested version, explanation).
    """
    # Get latest version
    latest_version = get_latest_version()
    if not latest_version:
        return "v1.0.0", "First release"
    
    try:
        current_version = parse_version(latest_version)
    except ValueError:
        return "v1.0.0", "Invalid current version format, starting fresh"
    
    # Analyze commits
    analysis = analyze_commits_for_version(commits)
    
    # Determine version bump and explanation
    if analysis["has_breaking"]:
        new_version = VersionInfo(current_version.major + 1, 0, 0)
        explanation = "Breaking changes detected"
    elif analysis["has_feature"]:
        new_version = VersionInfo(current_version.major, current_version.minor + 1, 0)
        explanation = "New features added"
    elif any([analysis["has_fix"], analysis["has_perf"], analysis["has_refactor"]]):
        new_version = VersionInfo(current_version.major, current_version.minor, current_version.patch + 1)
        explanation = "Bug fixes and improvements"
    else:
        new_version = VersionInfo(current_version.major, current_version.minor, current_version.patch + 1)
        explanation = "Minor changes and updates"
    
    return format_version(new_version), explanation

def validate_version_input(version: str, current_version: Optional[VersionInfo] = None) -> Optional[str]:
    """Validate and normalize version input.
    
    Args:
        version: User input version string.
        current_version: Current version to compare against.
        
    Returns:
        Normalized version string or None if invalid.
    """
    # Add v prefix if missing
    if not version.startswith('v'):
        version = f"v{version}"
    
    try:
        # Try parsing to validate
        new_version = parse_version(version)
        
        # Compare with current version if provided
        if current_version and new_version <= current_version:
            print(f"❌ New version must be greater than current version: {format_version(current_version)}")
            return None
            
        return version
    except ValueError as e:
        print(f"❌ Invalid version: {str(e)}")
        print("Version must be in format: vX.Y.Z[-pre-release][+build]")
        print("Examples:")
        print("  v1.0.0")
        print("  v1.0.0-alpha.1")
        print("  v1.0.0-beta.2")
        print("  v1.0.0-rc.1")
        print("  v1.0.0+build.123")
        return None

def create_version_tag(version: str, message: Optional[str] = None) -> None:
    """Create a version tag.
    
    Args:
        version: Version string.
        message: Optional tag message.
    """
    if not message:
        # Generate tag message from commits
        commits = get_commits_between_tags(get_latest_version(), "HEAD")
        categories = categorize_changes(commits)
        
        message_parts = []
        for category, category_commits in categories.items():
            if category_commits:
                message_parts.append(f"{category}:")
                for commit in category_commits[:3]:  # Show top 3 commits per category
                    msg = commit["message"]
                    if ":" in msg:
                        msg = msg.split(":", 1)[1].strip()
                    message_parts.append(f"- {msg}")
                if len(category_commits) > 3:
                    message_parts.append(f"- ... and {len(category_commits) - 3} more")
                message_parts.append("")
        
        message = "\n".join(message_parts)
    
    # Create annotated tag
    subprocess.run(
        ["git", "tag", "-a", version, "-m", message],
        check=True
    )
    print(f"✅ Created version tag: {version}")

def changelog_command(version: Optional[str] = None, create_tag: bool = False) -> None:
    """Generate a changelog for the repository.
    
    Args:
        version: Optional version to generate changelog for. If not provided,
                generates for all versions.
        create_tag: Whether to create a new version tag if none exists.
    """
    try:
        # Get version tags
        tags = get_version_tags()
        
        if not tags:
            if create_tag:
                # Get commits since last tag
                commits = get_commits_between_tags(None, "HEAD")
                if not commits:
                    print("No commits found to create a version tag.")
                    return
                
                # Suggest next version
                suggested_version, explanation = suggest_next_version(commits)
                print(f"\nSuggested version: {suggested_version}")
                print(f"Reason: {explanation}")
                print("\nEnter version number or press Enter to use suggested version.")
                print("You can use pre-release versions (e.g., v1.0.0-alpha.1) or build metadata (e.g., v1.0.0+build.123)")
                print("For pre-releases, you can use:")
                print("  alpha - for early development releases")
                print("  beta  - for testing releases")
                print("  rc    - for release candidates")
                manual_version = input().strip()
                
                if manual_version:
                    # Check if it's a pre-release type shortcut
                    if manual_version.lower() in ['alpha', 'beta', 'rc']:
                        pre_release_type = manual_version.lower()
                        suggested_base = parse_version(suggested_version)
                        pre_release = get_latest_pre_release(pre_release_type)
                        manual_version = f"v{suggested_base.major}.{suggested_base.minor}.{suggested_base.patch}-{pre_release}"
                        print(f"Using pre-release version: {manual_version}")
                    
                    version_to_use = validate_version_input(manual_version)
                    if not version_to_use:
                        return
                else:
                    version_to_use = suggested_version
                
                if typer.confirm(f"Create version tag {version_to_use}?", default=True):
                    create_version_tag(version_to_use)
                    tags = [version_to_use]
                else:
                    print("No version tag created. Changelog generation cancelled.")
                    return
            else:
                print("No version tags found in the repository.")
                print("Run 'gitwise changelog --create-tag' to create a version tag.")
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