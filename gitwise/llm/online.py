"""Online LLM support for GitWise (OpenRouter/OpenAI)."""
import os
from typing import List, Dict, Union
from openai import OpenAI
from gitwise.prompts import COMMIT_MESSAGE_PROMPT, PR_DESCRIPTION_PROMPT

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_llm_response(prompt_or_messages: Union[str, List[Dict[str, str]]]) -> str:
    """Get response from online LLM (OpenRouter/OpenAI)."""
    try:
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
            raise RuntimeError("Authentication failed (401). Please set OPENROUTER_API_KEY.") from e
        raise RuntimeError(f"Error getting LLM response: {str(e)}") from e 