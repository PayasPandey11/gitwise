"""LLM integration for GitWise."""

import os
from typing import List, Dict, Tuple, Optional
from openai import OpenAI
from gitwise.prompts import COMMIT_MESSAGE_PROMPT, PR_DESCRIPTION_PROMPT
from git import Commit

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
            max_tokens=1000,  # Increased from 500 to allow for longer responses
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

def generate_pr_title(commits: List[Commit]) -> str:
    """Generate a title for a pull request based on commit messages.
    
    Args:
        commits: List of commits to analyze for the PR title
        
    Returns:
        str: A concise, descriptive title for the PR
    """
    if not commits:
        return "Update"
        
    # Get the first commit message as base
    first_commit = commits[0].message.split('\n')[0]
    
    # If it's a conventional commit, use the description part
    if ':' in first_commit:
        title = first_commit.split(':', 1)[1].strip()
    else:
        title = first_commit
        
    # If there are multiple commits, indicate that
    if len(commits) > 1:
        title = f"{title} (+{len(commits)-1} more commits)"
        
    return title

def generate_pr_description(prompt: str) -> str:
    """Generate a description for a pull request using LLM.
    
    Args:
        prompt: The prompt containing commit information and instructions
        
    Returns:
        str: A detailed description of the changes
    """
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Please generate a concise PR description based only on the information provided."}
    ]
    
    return get_llm_response(messages) 