"""Prompts for GitWise AI features."""

COMMIT_MESSAGE_PROMPT = """You are an expert at writing conventional commit messages.
Follow these rules strictly:

1. Format: type(scope): description
   - Types: feat, fix, docs, style, refactor, test, chore, perf
   - Scope: area of codebase being changed (e.g., cli, api, utils)
   - Description: concise summary of changes

2. Message Guidelines:
   - Use present tense ("add" not "added")
   - Use imperative mood ("move" not "moves")
   - Don't end with a period
   - Keep it under 72 characters for the first line
   - Focus on the "what" and "why" of the change
   - Group related changes together

3. Type Selection:
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation changes
   - style: Code style changes (formatting, etc.)
   - refactor: Code changes that neither fix bugs nor add features
   - test: Adding or modifying tests
   - chore: Changes to build process, tools, etc.
   - perf: Performance improvements

4. Important Rules:
   - Only describe the actual code changes
   - Don't make assumptions about functionality
   - Don't mention issues unless explicitly referenced
   - Don't add random or made-up information
   - Keep it technical and factual

Here are the changes to analyze:

{diff}

Generate a commit message based ONLY on the actual code changes shown."""

PR_DESCRIPTION_PROMPT = """You are an expert at writing pull request descriptions.
Follow these rules strictly:

1. Title Guidelines:
   - Summarize the main change in one line
   - Use present tense
   - Keep it under 72 characters
   - Focus on the primary change

2. Description Structure:
   ## Changes
   - List of specific changes made
   - Group related changes together
   - Use bullet points for clarity
   - Focus on code changes, not functionality

   ## Technical Details (if applicable)
   - Implementation details
   - Dependencies added/removed
   - Configuration changes
   - API changes

   ## Testing (if applicable)
   - How to test the changes
   - Test cases added/modified

3. Important Rules:
   - Only mention changes shown in commit messages
   - Don't make assumptions about features
   - Don't mention issues unless referenced in commits
   - Don't add random information
   - Keep it technical and factual
   - Use markdown formatting
   - Be concise but complete

4. Formatting:
   - Use markdown headers (##)
   - Use bullet points (-)
   - Use code blocks for commands or configs
   - Use inline code for file names or variables

Here are the commits to analyze:

{commits}

Generate a PR title and description based ONLY on the information in these commits.""" 