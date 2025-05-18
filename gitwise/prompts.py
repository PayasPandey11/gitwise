"""Prompts for GitWise AI features."""

COMMIT_MESSAGE_PROMPT = """You are an expert at writing clear, concise, and descriptive commit messages.
Please analyze the following git diff and write a commit message that:
1. Follows conventional commit format (type(scope): description).
2. Ensure the first line (subject) is a concise summary (ideally under 72 characters) and can stand alone.
3. If more detail is needed, provide it in a subsequent paragraph (body) after a blank line.
4. Clearly describes what changed and why.
5. Is concise but informative.
6. Uses present tense for the subject line.
7. Focuses on the "why" rather than the "what" for the changes.

Git diff:
{diff}

Additional guidance: {guidance}

Commit message:"""

PR_DESCRIPTION_PROMPT = """You are an expert at writing clear, descriptive, and user-friendly pull request descriptions.
Please analyze the following commits and write a PR description that:
1. Summarizes the changes in a clear, user-friendly way.
2. Groups related changes together under logical headings (e.g., ### Features, ### Bug Fixes, ### Refactoring).
3. Highlights important changes or breaking changes explicitly.
4. Mentions contributors by name if there are multiple authors evident in the commits.
5. Uses markdown formatting for better readability.
6. If commit messages reference issue numbers (e.g., Fixes #123, Closes #456), include these references appropriately in the summary or link to them. Assume standard GitHub markdown.
7. Consider a structure like:
   - **Summary of Changes:** Brief overview.
   - **Key Features/Fixes:** Bullet points of main changes.
   - **Testing Done:** (Suggest placeholder if not inferable: e.g., "Manual testing performed for new feature X.")
   - **Potential Impact:** (e.g., "No breaking changes expected." or "Users will need to update their configuration for Y.")

Commits:
{commits}

Repository URL: {repo_url}
Repository Name: {repo_name}

Additional guidance: {guidance}

PR description:"""

# CHANGELOG_PROMPT was unused and has been removed.
# The actual prompt used for changelog generation is constructed within gitwise/features/changelog.py 