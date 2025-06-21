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

# Smart Merge Prompts
PROMPT_CONFLICT_EXPLANATION = """You are a Git merge conflict analysis expert. Analyze the following merge conflict and provide a clear, human-readable explanation.

{{file_content}}

MERGE CONTEXT: {{context}}

Please provide:

1. **SUMMARY**: A brief overview of what the conflict is about (1-2 sentences)

2. **OUR INTENT**: What the current branch was trying to accomplish with its changes

3. **THEIR INTENT**: What the incoming branch was trying to accomplish with its changes  

4. **SUGGESTED APPROACH**: The best strategy to resolve this conflict

5. **RESOLUTION STEPS**: Specific steps to manually resolve the conflict

Focus on understanding the PURPOSE and INTENT behind each change, not just the mechanical differences. Consider:
- What functionality each version is implementing
- Whether changes can be combined or if one should take precedence
- Any potential side effects or dependencies
- The broader context of what this code does

Provide practical, actionable guidance that helps the developer make an informed decision."""

PROMPT_RESOLUTION_STRATEGY = """
Suggest a strategy for resolving the following merge conflicts.

Rules:
- Provide specific, actionable steps
- Suggest multiple approaches if applicable
- Warn about potential risks
- Prioritize preserving functionality
- Be clear about the recommended approach

Conflicts summary:
{{conflicts_summary}}

Files affected: {{files_list}}

Branch context: {{branch_context}}
"""

PROMPT_MERGE_MESSAGE = """
Generate a merge commit message for the following merge operation.

Rules:
- Use format: "Merge branch 'source' into target"
- Add a descriptive body explaining what was merged
- Include conflict resolution notes if applicable
- Follow conventional commit style
- Keep subject line ≤50 characters

Source branch: {{source_branch}}
Target branch: {{target_branch}}

Changes summary:
{{changes_summary}}

Conflicts resolved: {{conflicts_resolved}}

Context: {{context}}
"""

# Commit Grouping Prompt
PROMPT_COMMIT_GROUPING = """You are a Git commit analysis expert. Analyze the provided staged changes and suggest how to group them into logical, cohesive commits.

STAGED CHANGES:
{{staged_changes}}

INSTRUCTIONS:
1. Analyze the actual code changes, not just file paths
2. Group related functionality together (e.g., feature implementation + tests + docs)
3. Separate unrelated changes into different commits
4. Consider semantic relationships between changes
5. Aim for commits that tell a clear story about what was accomplished
6. Each group should represent a single logical unit of work

RESPONSE FORMAT:
Return a valid JSON object with this exact structure:

{
  "groups": [
    {
      "name": "Short descriptive name for the group",
      "description": "What this group of changes accomplishes",
      "files": ["file1.py", "file2.py"],
      "suggested_commit_message": "feat: implement user authentication system",
      "reasoning": "Brief explanation of why these files belong together"
    }
  ],
  "recommendation": "single" or "multiple",
  "overall_description": "High-level summary of all the changes"
}

RULES:
- Only suggest multiple commits if the changes are truly unrelated
- Prefer fewer, more cohesive commits over many small ones
- Include all provided files in exactly one group
- Use conventional commit prefixes (feat:, fix:, docs:, refactor:, etc.)
- Keep commit messages under 50 characters for the subject line
- If changes are closely related, recommend "single" commit
- Return only the JSON, no additional text or explanation
"""
