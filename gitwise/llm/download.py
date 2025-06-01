import os
import sys
import shutil
import subprocess


def download_offline_model(model_name=None):
    """Check and download the offline model if not present. Print status and disk usage."""
    try:
        import torch
        from huggingface_hub import snapshot_download
    except ImportError:
        print("[gitwise] Offline mode requires 'transformers' and 'torch'.")
        print("You can install them with: pip install gitwise[offline]")
        auto = input("Would you like to install them now? [y/N]: ").strip().lower()
        if auto == "y":
            # import subprocess # Removed from here

            cmd = [sys.executable, "-m", "pip", "install", "gitwise[offline]"]
            print(f"[gitwise] Running: {' '.join(cmd)}")
            subprocess.run(cmd)
            print("[gitwise] Please re-run your command after install.")
        return
    model_name = model_name or os.environ.get(
        "GITWISE_OFFLINE_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    )
    print(f"[gitwise] Checking for offline model: {model_name}")
    # Default cache dir
    cache_dir = os.path.expanduser(os.getenv("HF_HOME", "~/.cache/huggingface"))
    model_dir = os.path.join(
        cache_dir, "hub", f"models--{model_name.replace('/', '--')}"
    )
    if os.path.exists(model_dir):
        print(f"[gitwise] Model already present at: {model_dir}")
        try:
            # import shutil # Removed from here

            size = shutil.disk_usage(model_dir).used // (1024 * 1024)
            print(f"[gitwise] Model disk usage: ~{size} MB")
        except Exception:
            pass
        return
    print(
        f"[gitwise] Model not found. It will be downloaded (e.g., TinyLlama-1.1B is ~4-5GB, smaller quantized versions may exist)."
    )
    confirm = input("Proceed with download? [y/N]: ").strip().lower()
    if confirm != "y":
        print("[gitwise] Download cancelled.")
        return
    print(f"[gitwise] Downloading {model_name} ...")
    try:
        path = snapshot_download(repo_id=model_name, local_files_only=False)
        print(f"[gitwise] Model downloaded to: {path}")
    except Exception as e:
        print(f"[gitwise] Download failed: {e}")
