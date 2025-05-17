import openai

def generate_commit_message(diff: str) -> str:
    """
    Generate a commit message using OpenAI's GPT-3.5/4 API.
    """
    prompt = (
        "Given the following git diff, write a single-line, conventional commit message. "
        "Do not include 'Commit message:' in your response.\n"
        f"Diff:\n{diff}\nCommit message:"
    )
    client = openai.OpenAI()  # This will use the OPENAI_API_KEY from your environment
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-4"
        messages=[{"role": "user", "content": prompt}],
        max_tokens=32,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip().split('\n')[0] 