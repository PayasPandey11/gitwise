# GitWise

GitWise is an AI-powered git assistant that helps you write better commit messages, create pull requests, and manage your repository with smart automation.

## Features

- **Smart Commit Messages**: Generate conventional commit messages using AI
- **Smart Commit Grouping**: Automatically group related changes into logical commits
- **Pull Request Creation**: Create PRs with AI-generated descriptions and optional labels/checklists
- **Changelog Management**: Generate and maintain changelogs with semantic versioning support
- **Offline LLM Support**: Coming soon! Run GitWise without internet connection

## Installation

### Using pip

```bash
pip install gitwise
```

### Using Make

```bash
# Clone the repository
git clone https://github.com/yourusername/gitwise.git

# Navigate to the project directory
cd gitwise

# Install using make
make install

# For development installation
make install-dev
```

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8
```

## Usage

### Smart Commit Messages

```bash
# Stage changes and create a commit
gitwise add .

# Create a commit with a specific message
gitwise commit -m "your message"

# Use smart commit grouping (default behavior)
gitwise add . --group
```

### Pull Requests

```bash
# Create a PR with AI-generated description
gitwise pr

# Create a PR with labels based on commit types
gitwise pr --use-labels

# Create a PR with a checklist based on changed files
gitwise pr --use-checklist

# Skip general checklist items
gitwise pr --use-checklist --skip-general-checklist
```

### Changelog Management

GitWise helps you maintain a changelog automatically. Here's how to use it effectively:

#### When to Update the Changelog

1. **Before Releases**:
   ```bash
   # Generate changelog for the upcoming release
   gitwise changelog --create-tag
   ```
   - Run this before creating a new release
   - Review and commit the generated CHANGELOG.md
   - Create the version tag

2. **During Development**:
   - Use conventional commit messages (feat:, fix:, etc.)
   - The changelog will automatically categorize your changes

3. **For Pre-releases**:
   ```bash
   # Create an alpha release
   gitwise changelog --create-tag
   # When prompted, type 'alpha'
   
   # Create a beta release
   gitwise changelog --create-tag
   # When prompted, type 'beta'
   
   # Create a release candidate
   gitwise changelog --create-tag
   # When prompted, type 'rc'
   ```

#### Changelog Best Practices

1. **Commit Messages**:
   - Use conventional commit types:
     - `feat:` for new features
     - `fix:` for bug fixes
     - `docs:` for documentation
     - `style:` for formatting
     - `refactor:` for code changes
     - `perf:` for performance
     - `test:` for tests
     - `chore:` for maintenance

2. **Version Numbers**:
   - Follow semantic versioning (MAJOR.MINOR.PATCH)
   - MAJOR: Breaking changes
   - MINOR: New features
   - PATCH: Bug fixes

3. **Pre-release Workflow**:
   ```
   v1.0.0-alpha.1 → v1.0.0-alpha.2 → v1.0.0-beta.1 → v1.0.0-rc.1 → v1.0.0
   ```

4. **Changelog Structure**:
   ```markdown
   # Changelog

   ## v1.1.0
   *Released on 2024-03-20*

   ### Features
   - New feature 1
   - New feature 2

   ### Bug Fixes
   - Fixed issue 1
   - Fixed issue 2
   ```

#### Common Workflows

1. **New Feature Development**:
   ```bash
   # 1. Make your changes
   # 2. Commit with conventional messages
   gitwise commit -m "feat: add new feature"
   
   # 3. Before release, generate changelog
   gitwise changelog --create-tag
   ```

2. **Bug Fix Release**:
   ```bash
   # 1. Fix the bug
   gitwise commit -m "fix: resolve issue"
   
   # 2. Create patch release
   gitwise changelog --create-tag
   ```

3. **Pre-release Testing**:
   ```bash
   # 1. Create alpha release
   gitwise changelog --create-tag
   # Type 'alpha' when prompted
   
   # 2. After testing, create beta
   gitwise changelog --create-tag
   # Type 'beta' when prompted
   ```

### Git Command Passthrough

GitWise supports all standard git commands:

```bash
# Use any git command
gitwise status
gitwise checkout -b feature/new
gitwise log --oneline
```

## Roadmap

### Coming Soon

- **Offline LLM Support**: Run GitWise without internet connection
  - Local model support for commit messages
  - Offline PR description generation
  - Configurable model selection
  - Automatic model updates

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.