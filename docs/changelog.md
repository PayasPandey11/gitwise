# Changelog Feature Documentation

The changelog feature in GitWise provides automated changelog generation and management. It helps maintain a clear record of changes in your project by automatically categorizing commits and generating well-formatted changelog entries.

## Features

- Automatic version detection and changelog generation
- Smart categorization of changes based on commit messages
- Support for conventional commit messages
- Automatic inclusion of release dates
- Clean markdown formatting
- Pre-commit hook for automatic updates
- Unreleased changes tracking

## API Reference

### `get_version_tags()`

Retrieves all version tags from the repository.

**Returns:**
- List of version tags sorted by version number

**Example:**
```python
tags = get_version_tags()
# Returns: [v1.0.0, v1.1.0, v2.0.0]
```

### `get_commits_between_tags(start_tag, end_tag)`

Fetches all commits between two version tags.

**Parameters:**
- `start_tag` (str): Starting version tag
- `end_tag` (str): Ending version tag

**Returns:**
- List of commit objects

**Example:**
```python
commits = get_commits_between_tags("v1.0.0", "v1.1.0")
```

### `categorize_changes(commits)`

Categorizes commits by type based on conventional commit messages.

**Parameters:**
- `commits` (list): List of commit objects

**Returns:**
- Dictionary with categories as keys and lists of commits as values

**Categories:**
- Features
- Bug Fixes
- Documentation
- Performance
- Security
- Breaking Changes
- Other

**Example:**
```python
categories = categorize_changes(commits)
# Returns: {"Features": [...], "Bug Fixes": [...], ...}
```

### `generate_changelog_entry(version, commits)`

Generates a markdown formatted changelog entry for a specific version.

**Parameters:**
- `version` (str): Version number
- `commits` (list): List of commit objects

**Returns:**
- String containing the formatted changelog entry

**Example:**
```python
entry = generate_changelog_entry("v1.0.0", commits)
```

### `get_repository_info()`

Gets information about the current repository.

**Returns:**
- Dictionary containing repository URL and name

**Example:**
```python
info = get_repository_info()
# Returns: {"url": "https://github.com/user/repo.git", "name": "repo"}
```

### `generate_release_notes(commits, repo_info)`

Generates user-friendly release notes from commits.

**Parameters:**
- `commits` (list): List of commit objects
- `repo_info` (dict): Repository information

**Returns:**
- String containing formatted release notes

**Example:**
```python
notes = generate_release_notes(commits, repo_info)
```

### `update_changelog(version, commits)`

Updates the CHANGELOG.md file with a new version entry.

**Parameters:**
- `version` (str): Version number
- `commits` (list): List of commit objects

**Example:**
```python
update_changelog("v1.0.0", commits)
```

### `get_unreleased_changes()`

Gets all commits since the last version tag.

**Returns:**
- List of commit objects

**Example:**
```python
changes = get_unreleased_changes()
```

### `update_unreleased_changelog(commits)`

Updates the [Unreleased] section of the changelog.

**Parameters:**
- `commits` (list): List of commit objects

**Example:**
```python
update_unreleased_changelog(commits)
```

### `commit_hook()`

Git pre-commit hook that updates the changelog.

**Example:**
```python
commit_hook()
```

### `setup_commit_hook()`

Sets up the git pre-commit hook for automatic changelog updates.

**Example:**
```python
setup_commit_hook()
```

## Command Line Interface

### `gitwise changelog [version]`

Generates a changelog for the repository.

**Options:**
- `version`: Optional version number to generate changelog for
- `--auto-update`: Update the unreleased section
- `--setup-hook`: Set up the git commit hook

**Examples:**
```bash
# Generate changelog for all versions
gitwise changelog

# Generate changelog for specific version
gitwise changelog v1.0.0

# Update unreleased section
gitwise changelog --auto-update

# Set up commit hook
gitwise changelog --setup-hook
```

## Best Practices

1. **Use Conventional Commits**
   - Start commit messages with type: `feat:`, `fix:`, `docs:`, etc.
   - This ensures proper categorization in the changelog

2. **Version Tags**
   - Use semantic versioning: `v1.0.0`, `v1.1.0`, etc.
   - Tag releases after merging to main branch

3. **Changelog Maintenance**
   - Keep the [Unreleased] section up to date
   - Review changelog entries before releases
   - Use the pre-commit hook for automatic updates

4. **Release Process**
   ```bash
   # 1. Update unreleased section
   gitwise changelog --auto-update
   
   # 2. Create version tag
   git tag v1.0.0
   
   # 3. Generate release notes
   gitwise changelog v1.0.0
   ```

## Troubleshooting

1. **Missing Version Tags**
   - Ensure tags are properly created with `git tag`
   - Check tag format matches semantic versioning

2. **Commit Hook Issues**
   - Verify hook installation with `gitwise changelog --setup-hook`
   - Check hook permissions in `.git/hooks/pre-commit`

3. **Changelog Format**
   - Ensure CHANGELOG.md exists
   - Maintain proper markdown formatting
   - Keep [Unreleased] section at the top

## Contributing

Contributions to the changelog feature are welcome! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. 