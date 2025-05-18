# GitWise

GitWise is an AI-powered git assistant that helps you write better commit messages, create pull requests, and manage your git workflow more efficiently.

## Features

- **Smart Commit Messages**: Generate conventional commit messages using AI
- **Smart Commit Grouping**: Automatically group related changes into separate commits
- **Pull Request Creation**: Create PRs with AI-generated descriptions
- **Push with PR Option**: Push changes with the option to create a PR

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gitwise.git

# Navigate to the project directory
cd gitwise

# Install the package
pip install -e .
```

## Usage

### Smart Commit Messages

```bash
# Stage your changes
git add .

# Create a commit with an AI-generated message
gitwise commit

# Or use smart commit grouping
gitwise commit --group
```

### Smart Commit Grouping

GitWise can automatically group related changes into separate commits:

```bash
# Stage your changes
git add .

# The command will prompt you to use smart grouping (default: Yes)
gitwise add .

# Or explicitly use smart grouping
gitwise commit --group
```

This will:
1. Analyze your staged changes
2. Group related changes together
3. Create separate commits for each group
4. Generate appropriate commit messages for each group

### Pull Requests

```bash
# Create a PR with AI-generated description
gitwise pr

# Add labels based on commit types
gitwise pr --use-labels

# Add a checklist based on changed files
gitwise pr --use-checklist
```

### Push Changes

```bash
# Push changes to remote
gitwise push

# Force push if needed
gitwise push --force
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.