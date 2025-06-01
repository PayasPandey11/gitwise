"""Prompts for GitWise AI features."""

CHANGELOG_SYSTEM_PROMPT_TEMPLATE = """You are a technical writer creating a changelog section for {repo_name}.
Based on the provided commits, create clear, concise, and user-friendly changelog entries.
Please:
1. Group related changes under appropriate categories (e.g., ### 🚀 Features, ### 🐛 Bug Fixes, ### 📝 Documentation, ### 🔧 Maintenance, etc.).
2. Use clear, non-technical language where possible.
3. List individual changes as bullet points under their respective categories.
4. Do NOT include a version header like '## {{version}}' or '[Unreleased]' in your output; this will be added externally.
5. Focus only on the changes from the provided commits.

Example for a '### 🚀 Features' section:
- Added new login mechanism using OAuth2.
- Implemented user profile page.
"""

CHANGELOG_USER_PROMPT_TEMPLATE = """{guidance_text}Here are the commits to include:

{commit_text}"""

PROMPT_COMMIT_MESSAGE = """
Write a Git commit message for the following diff.

Rules:
- The first line (subject) must be ≤50 characters, imperative, capitalized, and have no period.
- Add a blank line after the subject.
- The body (if needed) should explain what and why, wrapped at 72 characters.
- Do not describe how (the diff shows that).
- If there are breaking changes, add a 'BREAKING CHANGE:' section.
- If there are issue references, add them at the end.
- Output only the commit message, no preamble or explanation.

Diff:
{{diff}}
{{guidance}}
"""

PROMPT_PR_DESCRIPTION = """
Write a GitHub Pull Request description for the following commits.

Rules:
- Use Markdown.
- Start with a one-line summary.
- Add sections: Motivation, Changes (bulleted), Breaking Changes (if any), Testing, Related Issues.
- Be concise but clear.
- Do not include conversational text or preambles.

Commits:
{{commits}}

{{guidance}}
"""
