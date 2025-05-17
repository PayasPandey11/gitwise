import os
from typing import List, Dict, Tuple
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""Analyze these code changes and create a meaningful commit message.
Focus on the actual code changes, not the functionality or features they implement.
Only mention what was changed in the code.

Here are the changes to analyze:

{diff}"""}
            ],
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to generate commit message: {str(e)}")

def generate_pr_description(commits: List[Dict[str, str]]) -> Tuple[str, str]:
    """Generate a PR title and description based on commit history.
    
    Args:
        commits: List of commit dictionaries containing hash, author, date, and message
    
    Returns:
        Tuple of (title, description)
    """
    system_prompt = """You are an expert at writing pull request descriptions.
Follow these rules:
1. Create a clear, concise title that summarizes the functionality
2. Write a detailed description that:
   - Explains the purpose and functionality of the changes
   - Highlights key features and their impact
   - Mentions any breaking changes
   - Only references issues if they are explicitly mentioned in commit messages
3. Use markdown formatting
4. Keep the tone professional but friendly
5. Focus on functionality and features, not code changes
6. Don't make assumptions about issues or features unless explicitly mentioned
7. Don't include random or made-up information
8. If there's not enough information about functionality, focus on what can be inferred from commit messages"""

    # Format commits for the prompt
    commit_text = "\n".join([
        f"Commit: {c['hash']}\n"
        f"Author: {c['author']}\n"
        f"Date: {c['date']}\n"
        f"Message: {c['message']}\n"
        for c in commits
    ])

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""Analyze these commits and create a PR description.
Focus on the functionality and features being implemented.
Only mention issues if they are explicitly referenced in commit messages.
Don't make assumptions or include random information.

Here are the commits to analyze:

{commit_text}"""}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Split the response into title and description
        content = response.choices[0].message.content.strip()
        lines = content.split('\n')
        title = lines[0]
        description = '\n'.join(lines[1:]).strip()
        
        return title, description
    except Exception as e:
        raise RuntimeError(f"Failed to generate PR description: {str(e)}") 