import os
from typing import List, Dict, Tuple
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def generate_commit_message(diff: str, guidance: str = None) -> str:
    """Generate a commit message based on the diff.
    
    Args:
        diff: The git diff to analyze
        guidance: Optional guidance for regenerating the commit message
    """
    system_prompt = """You are an expert at writing conventional commit messages.
Follow these rules:
1. Use conventional commit format: type(scope): description
2. Types: feat, fix, docs, style, refactor, test, chore
3. Keep it concise but descriptive
4. Focus on the code changes, not the functionality
5. Use present tense
6. Don't end with a period
7. Group related changes together in a single commit message
8. If changes are part of a larger feature or refactor, mention the overall goal
9. Avoid splitting related changes into multiple commits
10. If changes are part of a feature implementation, use a consistent scope
11. For CLI changes, use 'cli' as the scope
12. For feature implementations, use the feature name as the scope
13. Only mention code changes, not functionality or features
14. Don't make assumptions about issues or features unless explicitly mentioned in the diff"""

    if guidance:
        system_prompt += f"\n\nAdditional guidance: {guidance}"

    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3-opus",  # Using Claude 3 Opus for best results
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""Analyze these code changes and create a meaningful commit message.
Focus on the actual code changes, not the functionality or features they implement.
Only mention what was changed in the code.

Here are the changes to analyze:

{diff}"""}
            ],
            temperature=0.7,
            max_tokens=100,
            extra_headers={
                "HTTP-Referer": "https://github.com/PayasPandey11/gitwise",  # Your repo URL
                "X-Title": "gitwise",  # Your project name
            }
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to generate commit message: {str(e)}")

def generate_pr_description(commits: List[Dict[str, str]]) -> Tuple[str, str]:
    """Generate a PR title and description from commit history.
    
    Args:
        commits: List of commit dictionaries containing hash, message, and author.
        
    Returns:
        Tuple of (title, description)
    """
    # Format commits for the prompt
    commit_text = "\n".join([
        f"Commit: {c['hash']}\n"
        f"Author: {c['author']}\n"
        f"Message: {c['message']}\n"
        for c in commits
    ])
    
    system_prompt = """You are an expert at writing pull request descriptions.
Follow these rules:
1. Create a clear, concise title that summarizes the changes
2. Write a detailed description that:
   - Summarizes the key changes
   - Groups related changes together
   - Highlights any breaking changes
   - Mentions any new features
   - Notes any bug fixes
3. Use markdown formatting
4. Keep the description professional and technical
5. Focus on the "what" and "why" of the changes
6. If there are multiple authors, acknowledge their contributions
7. If there are related issues, reference them
8. If there's not enough information about functionality, ask for more details

Here are the commits to analyze:

{commits}

Generate a PR title and description based on these commits."""

    messages = [
        {"role": "system", "content": system_prompt.format(commits=commit_text)},
        {"role": "user", "content": "Please generate a PR title and description."}
    ]
    
    response = get_llm_response(messages)
    
    # Split response into title and description
    parts = response.split("\n\n", 1)
    if len(parts) == 2:
        title = parts[0].strip()
        description = parts[1].strip()
    else:
        # If we can't split properly, use the whole response as description
        title = "Update codebase"
        description = response.strip()
    
    return title, description 