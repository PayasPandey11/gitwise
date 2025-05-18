"""Changelog generation feature for GitWise."""

import subprocess
import re
from typing import List, Dict, Optional, Tuple, NamedTuple
from gitwise.llm import get_llm_response
from gitwise.gitutils import get_commit_history
from gitwise.prompts import CHANGELOG_SYSTEM_PROMPT_TEMPLATE, CHANGELOG_USER_PROMPT_TEMPLATE
import typer
from datetime import datetime
import os
import json
from gitwise.core import git
from gitwise.ui import components
import tempfile

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

def get_repository_info() -> Dict[str, str]:
    """Get repository information.
    
    Returns:
        Dictionary with repository information.
    """
    info = {}
    
    # Get repository URL
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True
    )
    info["url"] = result.stdout.strip()
    
    # Get repository name
    if info["url"]:
        # Extract name from URL
        match = re.search(r"[:/]([^/]+/[^/]+?)(?:\.git)?$", info["url"])
        if match:
            info["name"] = match.group(1)
    
    return info

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

def generate_changelog(commits: List[Dict], version: Optional[str] = None) -> str:
    """Generate a changelog from commits.
    
    Args:
        commits: List of commit dictionaries.
        version: Optional version string.
        
    Returns:
        Formatted changelog string.
    """
    # Prepare commit messages for LLM
    commit_text = "\n".join([
        f"- {commit['message']} ({commit['author']})"
        for commit in commits
    ])
    
    # Get repository info
    repo_info = get_repository_info()
    repo_name = repo_info.get("name", "the repository")
    
    # Generate changelog using LLM
    prompt_version_guidance = f"Generate the detailed changelog entries for version {version} of {repo_name}. " if version else f"Generate a summary of recent changes for {repo_name}. "
    
    system_prompt = CHANGELOG_SYSTEM_PROMPT_TEMPLATE.format(repo_name=repo_name)
    user_prompt = CHANGELOG_USER_PROMPT_TEMPLATE.format(
        guidance_text=prompt_version_guidance,
        commit_text=commit_text
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        llm_content = get_llm_response(messages)
        
        # Construct the full version block
        if version:
            date = datetime.now().strftime("%Y-%m-%d")
            version_header = f"## {version} ({date})\n"
            full_version_block = f"{version_header}{llm_content.strip()}\n\n"
        else:
            # This case is for generating content not tied to a specific new version tag (e.g. for an unreleased section if we used LLM there)
            # For now, generate_changelog is mainly called with a version by changelog_command.
            # If called without version, it implies general summary.
            full_version_block = f"{llm_content.strip()}\n\n"
            
        return full_version_block
    except Exception as e:
        components.show_error(f"Could not generate changelog: {str(e)}")
        return ""

def update_changelog(version: str, commits: List[Dict[str, str]]) -> None:
    """Update the changelog file.
    
    Args:
        version: Version string.
        commits: List of commit dictionaries.
    """
    # Generate release notes
    release_notes = generate_changelog(commits, version)
    
    # Read existing changelog
    changelog_path = "CHANGELOG.md"
    existing_content = ""
    if os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            existing_content = f.read()
    
    # Prepare new changelog entry
    date = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"## {version} ({date})\n\n{release_notes}\n\n"
    
    # Update changelog
    if existing_content:
        # Insert new entry after the title
        if existing_content.startswith("# "):
            title_end = existing_content.find("\n", existing_content.find("\n") + 1)
            updated_content = existing_content[:title_end + 1] + "\n" + new_entry + existing_content[title_end + 1:]
        else:
            updated_content = new_entry + existing_content
    else:
        updated_content = f"# Changelog\n\n{new_entry}"
    
    # Write updated changelog
    with open(changelog_path, "w") as f:
        f.write(updated_content)

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

def get_unreleased_changes() -> List[Dict[str, str]]:
    """Get all commits since the last version tag.
    
    Returns:
        List of commit dictionaries.
    """
    latest_version = get_latest_version()
    return get_commits_between_tags(latest_version, "HEAD")

def update_unreleased_changelog() -> None:
    """Update the unreleased section of the changelog."""
    # Get unreleased changes
    commits = get_unreleased_changes()
    if not commits:
        return
    
    # Read existing changelog
    changelog_path = "CHANGELOG.md"
    existing_content = ""
    if os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            existing_content = f.read()
    
    # Generate unreleased section
    categories = categorize_changes(commits)
    unreleased_content = "## [Unreleased]\n\n"
    
    # Add categorized changes
    for category, category_commits in categories.items():
        if category_commits:
            unreleased_content += f"### {category}\n\n"
            for commit in category_commits:
                msg = commit["message"]
                if ":" in msg:
                    msg = msg.split(":", 1)[1].strip()
                unreleased_content += f"- {msg}\n"
            unreleased_content += "\n"
    
    # Update changelog
    if existing_content:
        # Check if unreleased section exists
        if "## [Unreleased]" in existing_content:
            # Replace existing unreleased section
            pattern = r"## \[Unreleased\].*?(?=## \[|\Z)"
            updated_content = re.sub(pattern, unreleased_content, existing_content, flags=re.DOTALL)
        else:
            # Add unreleased section after title
            if existing_content.startswith("# "):
                title_end = existing_content.find("\n", existing_content.find("\n") + 1)
                updated_content = existing_content[:title_end + 1] + "\n" + unreleased_content + existing_content[title_end + 1:]
            else:
                updated_content = unreleased_content + existing_content
    else:
        updated_content = f"# Changelog\n\n{unreleased_content}"
    
    # Write updated changelog
    with open(changelog_path, "w") as f:
        f.write(updated_content)

def commit_hook() -> None:
    """Git commit hook to update changelog."""
    try:
        update_unreleased_changelog()
    except Exception as e:
        print(f"Warning: Could not update changelog: {str(e)}")

def setup_commit_hook() -> None:
    """Set up git commit hook for automatic changelog updates."""
    hook_path = ".git/hooks/pre-commit"
    hook_content = """#!/bin/sh
# Update changelog before commit
gitwise changelog --auto-update
"""
    
    # Create hook directory if it doesn't exist
    os.makedirs(os.path.dirname(hook_path), exist_ok=True)
    
    # Write hook file
    with open(hook_path, "w") as f:
        f.write(hook_content)
    
    # Make hook executable
    os.chmod(hook_path, 0o755)
    print("✅ Git commit hook installed for automatic changelog updates")

def get_commits_since_last_tag() -> List[Dict]:
    """Get commits since the last tag."""
    try:
        # Get the last tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True
        )
        last_tag = result.stdout.strip() if result.stdout.strip() else None

        # Get commits since last tag
        if last_tag:
            result = subprocess.run(
                ["git", "log", f"{last_tag}..HEAD", "--pretty=format:%H|%s|%an"],
                capture_output=True,
                text=True
            )
        else:
            # If no tags, get all commits
            result = subprocess.run(
                ["git", "log", "--pretty=format:%H|%s|%an"],
                capture_output=True,
                text=True
            )

        if not result.stdout.strip():
            return []

        commits = []
        for line in result.stdout.strip().split('\n'):
            hash_, message, author = line.split('|')
            commits.append({
                'hash': hash_,
                'message': message,
                'author': author
            })

        return commits
    except Exception as e:
        components.show_error(f"Failed to get commits: {str(e)}")
        return []

def changelog_command(
    version: Optional[str] = None,
    output_file: Optional[str] = None,
    format: str = "markdown",
    auto_update: bool = False
) -> None:
    """Generate a changelog from commits since the last tag.
    
    Args:
        version: Optional version string for the changelog
        output_file: Optional output file path
        format: Output format (markdown or json)
        auto_update: Whether to automatically update the changelog without prompts
    """
    try:
        if auto_update and not version:
            # If auto-update is called (likely by a hook) and no version is specified,
            # assume it's for updating the [Unreleased] section.
            components.show_section("Auto-updating Unreleased Changelog")
            with components.show_spinner("Updating [Unreleased] section..."):
                try:
                    update_unreleased_changelog() # This function handles its own commit gathering
                    components.show_success("[Unreleased] section updated successfully.")
                except Exception as e:
                    components.show_error(f"Failed to auto-update changelog: {str(e)}")
            return

        # Get commits since last tag
        components.show_section("Analyzing Changes")
        with components.show_spinner("Checking for commits...") as progress:
            commits = get_commits_since_last_tag()
            if not commits:
                components.show_warning("No commits found to generate changelog")
                return

        # Suggest next version if not provided
        if not version:
            suggested_v, reason = suggest_next_version(commits)
            components.show_prompt(
                f"No version specified. Suggested version based on commits (reason: {reason}): {suggested_v}",
                options=["Use suggested version", "Enter manually", "Cancel"],
                default="Use suggested version"
            )
            choice = typer.prompt("", type=int, default=1)
            if choice == 1:
                version = suggested_v
            elif choice == 2:
                version_input = typer.prompt("Enter version (e.g., v1.2.3 or 1.2.3)")
                version = validate_version_input(version_input, current_version=parse_version(get_latest_version()) if get_latest_version() else None)
                if not version:
                    components.show_error("Invalid version format. Changelog generation cancelled.")
                    return
            else:
                components.show_warning("Changelog generation cancelled.")
                return
        else: # Validate user-provided version
            latest_parsed = parse_version(get_latest_version()) if get_latest_version() else None
            validated_version = validate_version_input(version, current_version=latest_parsed)
            if not validated_version:
                components.show_error("Invalid version format or not greater than current. Changelog generation cancelled.")
                return
            version = validated_version

        # Show commits that will be included
        components.show_section("Commits to Include")
        for commit in commits:
            components.console.print(f"[bold cyan]{commit['hash'][:7]}[/bold cyan] {commit['message']}")

        # Generate changelog content for the new version
        components.show_section("Generating Changelog Content for " + version)
        with components.show_spinner("Analyzing changes...") as progress:
            new_version_changelog_content = generate_changelog(commits, version)

        # Show the generated changelog for the new version
        components.show_section(f"Generated Content for {version}")
        components.console.print(new_version_changelog_content)

        if not auto_update:
            # Ask about saving
            components.show_prompt(
                f"Would you like to add this content for {version} to {output_file or 'CHANGELOG.md'}?",
                options=["Yes", "Edit content before adding", "No"],
                default="Yes"
            )
            choice = typer.prompt("", type=int, default=1)

            if choice == 3:  # No
                components.show_warning("Changelog update cancelled")
                return

            if choice == 2:  # Edit
                with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w+") as tf:
                    tf.write(new_version_changelog_content) # Write only the new version's content
                    tf.flush()
                    editor = os.environ.get("EDITOR", "vi")
                    subprocess.run([editor, tf.name], check=True)
                    tf.seek(0)
                    new_version_changelog_content = tf.read().strip()
                    if not new_version_changelog_content.strip().startswith(f"## {version}"):
                        # Ensure the header is still there after edit, or add it back
                        date = datetime.now().strftime("%Y-%m-%d")
                        new_version_changelog_content = f"## {version} ({date})\n{new_version_changelog_content}\n\n"
                    else:
                        new_version_changelog_content += "\n\n" # Ensure blank lines after

                os.unlink(tf.name)
                components.show_section(f"Edited Content for {version}")
                components.console.print(new_version_changelog_content)

                components.show_prompt(
                    "Proceed with adding this edited content?",
                    options=["Yes", "No"],
                    default="Yes"
                )
                if not typer.confirm("", default=True):
                    components.show_warning("Changelog update cancelled")
                    return

        # Save/Update the changelog file
        target_changelog_file = output_file or "CHANGELOG.md"
        components.show_section(f"Updating {target_changelog_file}")
        with components.show_spinner(f"Saving to {target_changelog_file}...") as progress:
            try:
                existing_content = ""
                if os.path.exists(target_changelog_file):
                    with open(target_changelog_file, "r") as f:
                        existing_content = f.read()
                
                updated_content = ""
                changelog_title = "# Changelog\n\n"
                unreleased_section_regex = re.compile(r"(^##\s+\[Unreleased\].*?)(?=^##\s+v?\d+\.\d+\.\d+|^\Z)", re.MULTILINE | re.DOTALL)
                
                unreleased_match = unreleased_section_regex.search(existing_content)
                
                if existing_content.startswith(changelog_title):
                    if unreleased_match:
                        # Insert after unreleased section
                        insert_point = unreleased_match.end(0)
                        updated_content = existing_content[:insert_point] + new_version_changelog_content + existing_content[insert_point:]
                    else:
                        # Insert after title
                        updated_content = changelog_title + new_version_changelog_content + existing_content[len(changelog_title):]
                else: # No existing changelog or no title
                    updated_content = changelog_title + new_version_changelog_content + existing_content

                with open(target_changelog_file, "w") as f:
                    f.write(updated_content.strip() + "\n") # Ensure a trailing newline
                components.show_success(f"Changelog updated in {target_changelog_file}")
            except Exception as e:
                components.show_error(f"Failed to update changelog: {str(e)}")

    except Exception as e:
        components.show_error(str(e))

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