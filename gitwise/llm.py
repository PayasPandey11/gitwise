import os
from typing import List, Dict, Tuple
from openai import OpenAI
from gitwise.prompts import COMMIT_MESSAGE_PROMPT, PR_DESCRIPTION_PROMPT

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_llm_response(messages: List[Dict[str, str]]) -> str:
    """Get response from LLM API.
    
    Args:
        messages: List of message dictionaries with role and content.
        
    Returns:
        The response text from the LLM.
    """
    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3-opus",  # Using Claude 3 Opus for best results
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            extra_headers={
                "HTTP-Referer": "https://github.com/PayasPandey11/gitwise",  # Your repo URL
                "X-Title": "gitwise",  # Your project name
            }
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to get LLM response: {str(e)}")

def generate_commit_message(diff: str, guidance: str = None) -> str:
    """Generate a commit message based on the diff.
    
    Args:
        diff: The git diff to analyze
        guidance: Optional guidance for regenerating the commit message
    """
    system_prompt = COMMIT_MESSAGE_PROMPT
    if guidance:
        system_prompt += f"\n\nAdditional guidance: {guidance}"

    messages = [
        {"role": "system", "content": system_prompt.format(diff=diff)},
        {"role": "user", "content": "Please generate a commit message based only on the actual code changes shown."}
    ]
    
    return get_llm_response(messages)

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
    
    messages = [
        {"role": "system", "content": PR_DESCRIPTION_PROMPT.format(commits=commit_text)},
        {"role": "user", "content": "Please generate a PR title and description based only on the actual changes shown in the commits."}
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