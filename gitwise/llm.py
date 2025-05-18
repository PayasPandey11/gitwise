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

def get_llm_response(prompt: str) -> str:
    """Get response from LLM."""
    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3-opus",
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": "https://github.com/payas/gitwise",
                "X-Title": "GitWise"
            }
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Error getting LLM response: {str(e)}")

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