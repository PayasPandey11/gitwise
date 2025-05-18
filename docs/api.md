# GitWise API Documentation

GitWise is an AI-powered git assistant that helps you write better commit messages, manage changelogs, and create pull requests. This document provides a comprehensive overview of the GitWise API.

## Core Features

### Commit Management

#### `commit_command(message: str = None, group: bool = False)`

Creates a commit with either a provided message or an AI-generated message based on staged changes.

**Parameters:**
- `message` (str, optional): Commit message to use
- `group` (bool): Whether to group changes and generate a smart commit message

**Example:**
```python
# Commit with provided message
commit_command(message="feat: add new feature")

# Commit with AI-generated message
commit_command(group=True)
```

#### `group_commits(diffs: List[Diff])`

Groups changes into categories based on their type and content.

**Parameters:**
- `diffs` (List[Diff]): List of git diff objects

**Returns:**
- Dictionary with categories as keys and lists of changes as values

**Example:**
```python
groups = group_commits(diffs)
# Returns: {"Features": [...], "Bug Fixes": [...], ...}
```

#### `generate_commit_message(groups: Dict[str, List[str]])`

Generates a conventional commit message from grouped changes.

**Parameters:**
- `groups` (Dict[str, List[str]]): Dictionary of change groups

**Returns:**
- String containing the formatted commit message

**Example:**
```python
message = generate_commit_message({
    "Features": ["new feature"],
    "Bug Fixes": ["fix bug"]
})
```

### Pull Request Management

#### `pr_command(title: str = None, base: str = None, draft: bool = False)`

Creates a pull request with either a provided title or an AI-generated title based on commits.

**Parameters:**
- `title` (str, optional): PR title to use
- `base` (str, optional): Base branch for the PR
- `draft` (bool): Whether to create a draft PR

**Example:**
```python
# Create PR with provided title
pr_command(title="Add new feature")

# Create PR with AI-generated title
pr_command(draft=True)
```

#### `generate_pr_title()`

Generates a PR title based on commit messages since the base branch.

**Returns:**
- String containing the PR title

**Example:**
```python
title = generate_pr_title()
```

#### `generate_pr_description()`

Generates a PR description with categorized changes and breaking changes.

**Returns:**
- String containing the formatted PR description

**Example:**
```python
description = generate_pr_description()
```

### Changelog Management

#### `changelog_command(version: str = None, auto_update: bool = False, setup_hook: bool = False)`

Generates or updates the changelog.

**Parameters:**
- `version` (str, optional): Version to generate changelog for
- `auto_update` (bool): Whether to update the unreleased section
- `setup_hook` (bool): Whether to set up the git commit hook

**Example:**
```python
# Generate changelog for all versions
changelog_command()

# Generate changelog for specific version
changelog_command(version="v1.0.0")

# Update unreleased section
changelog_command(auto_update=True)
```

#### `get_version_tags()`

Retrieves all version tags from the repository.

**Returns:**
- List of version tags sorted by version number

**Example:**
```python
tags = get_version_tags()
```

#### `update_changelog(version: str, commits: List[Commit])`

Updates the CHANGELOG.md file with a new version entry.

**Parameters:**
- `version` (str): Version number
- `commits` (List[Commit]): List of commit objects

**Example:**
```python
update_changelog("v1.0.0", commits)
```

## Utility Functions

### Git Operations

#### `get_current_branch()`

Gets the name of the current branch.

**Returns:**
- String containing the branch name

**Example:**
```python
branch = get_current_branch()
```

#### `get_base_branch()`

Gets the default base branch for the repository.

**Returns:**
- String containing the base branch name

**Example:**
```python
base = get_base_branch()
```

### Validation

#### `validate_commit_message(message: str)`

Validates a commit message against conventional commit format.

**Parameters:**
- `message` (str): Commit message to validate

**Returns:**
- Boolean indicating if the message is valid

**Example:**
```python
is_valid = validate_commit_message("feat: add new feature")
```

#### `validate_branch_name(branch: str)`

Validates a branch name against naming conventions.

**Parameters:**
- `branch` (str): Branch name to validate

**Returns:**
- Boolean indicating if the name is valid

**Example:**
```python
is_valid = validate_branch_name("feature/new-feature")
```

## Best Practices

1. **Commit Messages**
   - Use conventional commit format
   - Include scope when applicable
   - Add breaking change indicators when needed

2. **Branch Names**
   - Use feature/, fix/, docs/ prefixes
   - Use kebab-case for multi-word names
   - Avoid protected branch names

3. **Pull Requests**
   - Create from feature branches
   - Include clear descriptions
   - Use draft PRs for work in progress

4. **Changelog**
   - Keep [Unreleased] section up to date
   - Use semantic versioning
   - Include breaking changes

## Error Handling

All functions raise appropriate exceptions when:
- Git operations fail
- Validation fails
- Required parameters are missing
- No changes are found
- Invalid version formats are used

## Contributing

Contributions to the API are welcome! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. 