"""Prompts for GitWise AI features."""

COMMIT_MESSAGE_PROMPT = """You are an expert at writing clear, concise, and descriptive commit messages.
Please analyze the following git diff and write a commit message that:
1. Follows conventional commit format (type(scope): description)
2. Clearly describes what changed and why
3. Is concise but informative
4. Uses present tense
5. Focuses on the "why" rather than the "what"

Git diff:
{diff}

Additional guidance: {guidance}

Commit message:"""

PR_DESCRIPTION_PROMPT = """You are an expert at writing clear, descriptive, and user-friendly pull request descriptions.
Please analyze the following commits and write a PR description that:
1. Summarizes the changes in a clear, user-friendly way
2. Groups related changes together
3. Highlights important changes or breaking changes
4. Mentions contributors if there are multiple authors
5. Uses markdown formatting for better readability

Commits:
{commits}

Repository URL: {repo_url}
Repository Name: {repo_name}

Additional guidance: {guidance}

PR description:"""

CHANGELOG_PROMPT = """You are an expert at writing clear, user-friendly changelogs.
Please analyze the following commits and write a changelog entry that:
1. Groups changes by type (features, fixes, etc.)
2. Uses clear, concise language
3. Highlights important changes
4. Uses markdown formatting
5. Is easy to read and understand

Commits:
{commits}

Version: {version}
Additional guidance: {guidance}

Changelog entry:""" 