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

PROMPT_PR_AND_COMMITS = """
You are an expert programmer responsible for creating pull requests and commit messages.
Your task is to generate a comprehensive JSON object that contains a pull request title, a pull request body, and a list of commit messages for given groups of code changes.

**Input:**
You will receive a list of change groups. Each group has a unique `group_id` and a `diff` associated with it.

**Output Rules:**
- You MUST respond with a single, valid JSON object.
- Do not include any preamble, explanations, or markdown formatting around the JSON object.
- The JSON object must conform to the specified schema.
- **Pull Request Title:** Create a concise, one-line title summarizing all changes.
- **Pull Request Body:** Write a clear, Markdown-formatted description. It should include sections for "Motivation" and a "Summary of Changes".
- **Commit Messages:** For each change group, write a conventional commit message. The message must have a subject line (<=50 chars) and an optional body.

**JSON Schema:**
```json
{
  "pullRequest": {
    "title": "A brief, descriptive title for the PR",
    "body": "A detailed description of the changes in Markdown."
  },
  "commits": [
    {
      "group_id": "the_id_of_the_group",
      "message": "feat(scope): concise subject line\\n\\nOptional detailed body explaining what and why."
    }
  ]
}
```

**Example of a single commit message in the JSON:**
`"message": "refactor(ui): improve button component accessibility\\n\\nUpdated the button component to include ARIA attributes and better focus management, improving usability for screen reader users."`

Here are the change groups:
{{change_groups_json}}

{{guidance}}
"""
