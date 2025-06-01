"""Offline LLM support for GitWise (default mode, using microsoft/phi-2)."""
import contextlib
import io
import os
import sys
import warnings

# Suppress HuggingFace tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

MODEL_NAME = os.environ.get(
    "GITWISE_OFFLINE_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
)

try:
    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
except ImportError as e:
    print(f"[gitwise] CRITICAL: ImportError in offline.py: {e}")
    print(
        "[gitwise] This likely means your 'transformers' version is too old or not installed correctly."
    )
    print(
        "[gitwise] Please run: pip install --upgrade 'transformers>=4.36.0' 'torch>=2.0.0'"
    )
    sys.exit(1)
else:
    _model = None
    _tokenizer = None
    _pipe = None
    _model_ready = False

    def _ensure_model():
        global _model, _tokenizer, _pipe, _model_ready
        if _model_ready:
            return
        # Check if model is present in cache
        cache_dir = os.path.expanduser(os.getenv("HF_HOME", "~/.cache/huggingface"))
        model_dir = os.path.join(
            cache_dir, "hub", f"models--{MODEL_NAME.replace('/', '--')}"
        )
        if not os.path.exists(model_dir):
            print(
                f"[gitwise] The offline model ({MODEL_NAME}) is not present (~1.7GB download required).\n"
            )
            print("[gitwise] No AI features will work until the model is downloaded.")
            confirm = (
                input("Would you like to download it now? [y/N]: ").strip().lower()
            )
            if confirm != "y":
                print(
                    "[gitwise] Offline model download cancelled. Cannot proceed with AI features."
                )
                sys.exit(1)
            print(
                f"[gitwise] Downloading {MODEL_NAME}... (this may take a few minutes)"
            )
            try:
                # Download with huggingface_hub snapshot_download
                snapshot_download(repo_id=MODEL_NAME, local_files_only=False)
                print(f"[gitwise] Model downloaded successfully.")
            except Exception as e:
                print(f"[gitwise] Download failed: {e}")
                sys.exit(1)
        print(
            f"[gitwise] Loading offline model '{MODEL_NAME}' (this may take a minute the first time)..."
        )
        # Suppress transformers/tokenizers info and warnings during model load
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
                _model = AutoModelForCausalLM.from_pretrained(
                    MODEL_NAME, torch_dtype=torch.float32
                )
                _pipe = pipeline(
                    "text-generation", model=_model, tokenizer=_tokenizer, device=-1
                )
        _model_ready = True

    def get_llm_response(prompt: str, **kwargs) -> str:
        _ensure_model()
        # At this point, model is ready. Only now should any spinner/analysis message be shown by the caller.
        prompt = prompt[-2048:]
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                outputs = _pipe(
                    prompt, max_new_tokens=128, do_sample=True, temperature=0.7
                )
            return outputs[0]["generated_text"][len(prompt) :].strip()
        except Exception as e:
            raise RuntimeError(f"Offline LLM inference failed: {e}")

    def ensure_offline_model_ready():
        _ensure_model()
