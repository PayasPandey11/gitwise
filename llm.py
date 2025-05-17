def generate_commit_message(diff: str) -> str:
    """
    Generate a commit message using Zephyr-7B-Beta via Hugging Face transformers.
    Args:
        diff (str): The git diff to summarize.
    Returns:
        str: A single-line, conventional commit message.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model_id = "HuggingFaceH4/zephyr-7b-beta"
    if not hasattr(generate_commit_message, "model"):
        print("Loading Zephyr-7B-Beta model (first run may take a while)...")
        generate_commit_message.tokenizer = AutoTokenizer.from_pretrained(model_id)
        generate_commit_message.model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=torch.bfloat16
        )
        generate_commit_message.model.eval()
    tokenizer = generate_commit_message.tokenizer
    model = generate_commit_message.model
    prompt = (
        "Given the following git diff, write a single-line, conventional commit message. "
        "Do not include 'Commit message:' in your response.\n"
        "Diff:\n" + diff + "\nCommit message:"
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=16)
    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[-1]:], skip_special_tokens=True)
    # Remove any leading 'Commit message:' and whitespace
    response = response.replace("Commit message:", "").strip().split("\n")[0]
    return response 