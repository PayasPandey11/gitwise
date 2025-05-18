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

def generate_pr_description(commits: List[Commit]) -> str:
    """Generate a description for a pull request based on commit messages.
    
    Args:
        commits: List of commits to analyze for the PR description
        
    Returns:
        str: A detailed description of the changes
    """
    if not commits:
        return "No changes to describe."
        
    # Group commits by type
    commit_groups = {}
    for commit in commits:
        message = commit.message.split('\n')[0]
        if ':' in message:
            commit_type = message.split(':', 1)[0].strip()
            description = message.split(':', 1)[1].strip()
        else:
            commit_type = "other"
            description = message
            
        if commit_type not in commit_groups:
            commit_groups[commit_type] = []
        commit_groups[commit_type].append(description)
    
    # Build the description
    description = "## Changes\n"
    
    # Add each group of changes
    for commit_type, messages in commit_groups.items():
        if commit_type != "other":
            description += f"\n### {commit_type.title()}\n"
            for msg in messages:
                description += f"- {msg}\n"
    
    # Add other changes if any
    if "other" in commit_groups:
        description += "\n### Other Changes\n"
        for msg in commit_groups["other"]:
            description += f"- {msg}\n"
            
    return description 