# gitwise

AI-powered git assistant for generating smart commit messages, PR descriptions, and changelogs using OpenAI's GPT models.

## Features
- **Smart Commit Message Generator**: Analyzes staged changes and generates concise, conventional commit messages using GPT.
- **Git Command Passthrough**: Seamlessly use git commands through gitwise (e.g., `gitwise add .`)
- **Smart Push**: Push changes to the same or different branch with interactive prompts
- **Smart PR Creation**: Generate pull requests with AI-powered titles and descriptions
- **Changelog Generator**: Coming soon!

## Installation

### From PyPI (Coming Soon)
```sh
pip install gitwise
```

### From Source
```sh
# Clone the repository
git clone https://github.com/yourusername/gitwise.git
cd gitwise

# Install the package
pip install -e .
```

## Configuration
Set your OpenAI API key as an environment variable:
```sh
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Basic Git Commands
Use `gitwise` just like `git`:
```sh
# Stage changes
gitwise add .

# Check status
gitwise status

# View diff
gitwise diff
```

### Smart Commit
Generate and commit with an AI-powered message:
```sh
# Stage your changes first
gitwise add .

# Generate and commit with a smart message
gitwise commit
```
The commit process will:
1. Analyze your staged changes
2. Generate a commit message
3. Allow you to:
   - [u]se the suggested message
   - [e]dit the message in your default editor
   - [r]egenerate a new message (with optional guidance)
   - [a]bort the commit
4. Create the commit
5. Optionally push the changes

### Smart Push
Push changes to remote repository:
```sh
# Push to the same branch
gitwise push

# Push to a specific branch
gitwise push feature/new-feature
```

The push process will:
1. Show your current branch
2. Ask if you want to push to the same branch
3. If not, prompt for the target branch name
4. Push the changes

### Smart PR Creation
Create a pull request with an AI-generated title and description:
```sh
gitwise pr
```
The PR creation process will:
1. Analyze your commit history since the last common ancestor with main
2. Generate a PR title and description
3. Show you the generated content for review
4. Create the PR using GitHub CLI if available, or show you the content to create it manually

## Example Workflow
```sh
# Stage changes
$ gitwise add .

# Generate and commit with a smart message
$ gitwise commit
Analyzing staged changes...
Suggested commit message:
feat: add user authentication

What would you like to do? [u]se/[e]dit/[r]egenerate/[a]bort (u): r
Enter guidance for the commit message (optional): make it more specific about the auth method
Regenerating commit message with guidance...

Suggested commit message:
feat(auth): implement OAuth2 authentication

What would you like to do? [u]se/[e]dit/[r]egenerate/[a]bort (u): u
Commit created successfully.

# Push changes
$ gitwise push
Push to the same branch (main)? [Y/n]: n
Enter the target branch name [main]: feature/auth
Changes pushed successfully.

# Create PR
$ gitwise pr
Analyzing commits for PR description...

Suggested PR title:
Add OAuth2 Authentication System

Suggested PR description:
## Overview
This PR implements OAuth2 authentication for our application, providing a secure and standardized way for users to sign in.

## Changes
- Added OAuth2 client configuration
- Implemented user authentication flow
- Added token management and refresh logic
- Updated user model to support OAuth2

## Testing
- Added unit tests for authentication flow
- Tested with multiple OAuth providers

Create PR with this title and description? [Y/n]: y
PR created successfully!
```

## License
MIT 