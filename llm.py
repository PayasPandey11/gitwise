import os
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
4. Focus on the "why" not the "what"
5. Use present tense
6. Don't end with a period"""

    if guidance:
        system_prompt += f"\n\nAdditional guidance: {guidance}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here are the changes to analyze:\n\n{diff}"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to generate commit message: {str(e)}") 