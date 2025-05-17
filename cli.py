import typer
import subprocess
import tempfile
import os

app = typer.Typer(help="gitwise: AI-powered git assistant")

# --- LLM Integration ---
def bitnet_llm(diff: str) -> str:
    """Generate a commit message using BitNet via Hugging Face transformers."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model_id = "microsoft/bitnet-b1.58-2B-4T"
    # Cache model and tokenizer
    if not hasattr(bitnet_llm, "model"):
        typer.echo("Loading BitNet model (first run may take a while)...")
        bitnet_llm.tokenizer = AutoTokenizer.from_pretrained(model_id)
        bitnet_llm.model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=torch.bfloat16
        )
        bitnet_llm.model.eval()
    tokenizer = bitnet_llm.tokenizer
    model = bitnet_llm.model
    # Prompt template
    prompt = (
        "You are an expert software engineer. "
        "Write a concise, conventional commit message for the following git diff.\n"
        "Diff:\n" + diff + "\nCommit message:"
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=32)
    # Decode only the new tokens
    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[-1]:], skip_special_tokens=True)
    # Clean up response
    return response.strip().split("\n")[0]

@app.command()
def commit():
    """Generate a smart commit message for staged changes."""
    # Get the real staged diff
    try:
        result = subprocess.run([
            "git", "diff", "--cached"
        ], capture_output=True, text=True, check=True)
        staged_diff = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        typer.echo("Error running git diff --cached.")
        raise typer.Exit(code=1)

    if not staged_diff:
        typer.echo("No staged changes found. Please stage your changes first.")
        raise typer.Exit(code=0)

    typer.echo("Analyzing staged changes:\n")
    typer.echo(staged_diff[:1000] + ("\n... (truncated) ..." if len(staged_diff) > 1000 else ""))
    # Generate commit message using BitNet LLM
    commit_message = bitnet_llm(staged_diff)
    typer.echo(f"\nSuggested commit message:\n{commit_message}\n")

    # Allow user to edit the commit message
    edit = typer.confirm("Would you like to edit the commit message?", default=False)
    final_message = commit_message
    if edit:
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
            tf.write(commit_message)
            tf.flush()
            editor = os.environ.get("EDITOR", "vi")
            subprocess.run([editor, tf.name])
            tf.seek(0)
            final_message = tf.read().strip()
        os.unlink(tf.name)
        typer.echo(f"\nEdited commit message:\n{final_message}\n")

    confirm = typer.confirm("Use this commit message?", default=True)
    if confirm:
        try:
            subprocess.run(["git", "commit", "-m", final_message], check=True)
            typer.echo("Commit created successfully.")
        except subprocess.CalledProcessError:
            typer.echo("Error running git commit.")
            raise typer.Exit(code=1)
    else:
        typer.echo("Aborted. No commit made.")

@app.command()
def pr():
    """Generate a PR message for the current branch."""
    typer.echo("PR message generation coming soon!")

@app.command()
def changelog():
    """Generate a changelog from commit history."""
    typer.echo("Changelog generation coming soon!")

if __name__ == "__main__":
    app() 