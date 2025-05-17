# gitwise

AI-powered git assistant for generating smart commit messages, PR descriptions, and changelogs using OpenAI's GPT models.

## Features
- **Smart Commit Message Generator**: Analyzes staged changes and generates concise, conventional commit messages using GPT.
- **Git Command Passthrough**: Seamlessly use git commands through gitwise (e.g., `gitwise add .`)
- **Smart Push**: Push changes to the same or different branch with interactive prompts
- **PR Description Generator**: Coming soon!
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
3. Allow you to edit the message if needed
4. Create the commit
5. Optionally push the changes

Analyzing staged changes...
Suggested commit message:
feat: add user authentication

What would you like to do? [use/edit/regenerate/abort] (use): regenerate
Regenerating commit message...

Suggested commit message:
feat(auth): implement user authentication system

What would you like to do? [use/edit/regenerate/abort] (use): edit
# Editor opens
# After editing:
What would you like to do? [use/edit/regenerate/abort] (use): use
Commit created successfully.

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

## Example Workflow
```sh
# Stage changes
$ gitwise add .

# Generate and commit with a smart message
$ gitwise commit
Analyzing staged changes...
Suggested commit message:
feat: add user authentication

What would you like to do? [use/edit/regenerate/abort] (use): regenerate
Regenerating commit message...

Suggested commit message:
feat(auth): implement user authentication system

What would you like to do? [use/edit/regenerate/abort] (use): edit
# Editor opens
# After editing:
What would you like to do? [use/edit/regenerate/abort] (use): use
Commit created successfully.

Would you like to push these changes? [y/N]: y
Push to the same branch (main)? [Y/n]: n
Enter the target branch name [main]: feature/auth
Changes pushed successfully.
```

## License
MIT 