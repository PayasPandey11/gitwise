"""LLM integration for GitWise."""

import os
from typing import List, Dict, Tuple, Optional, Union
from openai import OpenAI
from gitwise.prompts import COMMIT_MESSAGE_PROMPT, PR_DESCRIPTION_PROMPT
from git import Commit

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_llm_response(prompt_or_messages: Union[str, List[Dict[str, str]]]) -> str:
    """Get response from LLM.
    
    Args:
        prompt_or_messages: Either a string prompt or a list of message dictionaries
        
    Returns:
        LLM response as a string
        
    Raises:
        RuntimeError: If there's an error getting the response
    """
    try:
        # Convert string prompt to message list if needed
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        else:
            messages = prompt_or_messages
            
        response = client.chat.completions.create(
            model="anthropic/claude-3-opus",
            messages=messages,
            extra_headers={
                "HTTP-Referer": "https://github.com/payas/gitwise",
                "X-Title": "GitWise"
            }
        )
        
        if not response.choices or not response.choices[0].message:
            raise RuntimeError("Empty response from LLM")
            
        return response.choices[0].message.content.strip()
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 401:
            error_message = (
                "Authentication failed (401). Please ensure your OPENROUTER_API_KEY is correctly set "
                "as an environment variable and that the key is valid. "
                "You can get a key from OpenRouter.ai."
            )
            raise RuntimeError(error_message) from e
        elif hasattr(e, 'message') and isinstance(e.message, str) and 'No auth credentials found' in e.message:
            # Catching the specific error message structure from the log
            error_message = (
                "Authentication failed. No auth credentials found. Please ensure your OPENROUTER_API_KEY is correctly set "
                "as an environment variable and that the key is valid. "
                "You can get a key from OpenRouter.ai."
            )
            raise RuntimeError(error_message) from e
        raise RuntimeError(f"Error getting LLM response: {str(e)}") from e

def generate_commit_message(diff: str, guidance: str = "") -> str:
    """Generate a commit message from a git diff."""
    prompt = COMMIT_MESSAGE_PROMPT.format(diff=diff, guidance=guidance)
    return get_llm_response(prompt)

def generate_pr_title(commits: List[Dict[str, str]]) -> str:
    """Generate a PR title from a list of commits."""
    if not commits:
        return ""
    
    # Use the first commit message as the base for the title
    first_commit = commits[0]
    title = first_commit["message"].split("\n")[0]  # Get first line
    
    # If there are multiple commits, indicate that
    if len(commits) > 1:
        title = f"{title} (+{len(commits)-1} more commits)"
    
    return title

def generate_pr_description(commits: List[Dict[str, str]], repo_url: str, repo_name: str, guidance: str = "") -> str:
    """Generate a PR description from a list of commits."""
    # Format commits for the prompt
    formatted_commits = "\n".join([
        f"Commit: {commit['message']}\nAuthor: {commit['author']}\n"
        for commit in commits
    ])
    
    prompt = PR_DESCRIPTION_PROMPT.format(
        commits=formatted_commits,
        repo_url=repo_url,
        repo_name=repo_name,
        guidance=guidance
    )
    return get_llm_response(prompt) 