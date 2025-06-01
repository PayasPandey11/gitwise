"""Offline LLM support for GitWise (default mode, using microsoft/phi-2)."""
import contextlib
import io
import os
import sys
import warnings
from typing import Any, Optional

# Suppress HuggingFace tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Global state for the loaded model and tokenizer
_tokenizer = None
_model = None
_pipeline = None
_model_ready = False

class OfflineModelError(Exception):
    pass

def _load_offline_model(model_name: Optional[str] = None) -> Any:
    global _tokenizer, _model, _pipeline, _model_ready

    # Moved imports inside to be lazily loaded and allow module to import even if deps are missing initially.
    # The `ensure_offline_model_ready` flow (via `download_offline_model`) will handle prompting for install.
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    except ImportError as e:
        # This error will be caught by ensure_offline_model_ready if called through that path.
        # If _load_offline_model is called directly and these are missing, it's a problem.
        print(f"[gitwise] CRITICAL: Core dependencies (PyTorch/Transformers) missing for offline mode: {e}")
        print("[gitwise] Please run 'pip install gitwise[offline]' or ensure PyTorch and Transformers are installed.")
        _model_ready = False # Explicitly ensure not ready
        # Re-raise to make it clear that loading cannot proceed.
        # Callers like `ensure_offline_model_ready` might catch this and attempt install.
        raise OfflineModelError("Core dependencies (PyTorch/Transformers) missing.") from e

    effective_model_name = model_name or os.environ.get(
        "GITWISE_OFFLINE_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    )

    # Check if already loaded and matches the requested model
    if _model_ready and _pipeline is not None and hasattr(_pipeline, 'model') and _pipeline.model.name_or_path == effective_model_name:
        return

    print(f"[gitwise] Loading offline model \'{effective_model_name}\' (this may take a minute the first time).")
    try:
        # Suppress transformers/tokenizers info and warnings during model load
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                _tokenizer = AutoTokenizer.from_pretrained(effective_model_name)
                _model = AutoModelForCausalLM.from_pretrained(effective_model_name, torch_dtype=torch.float32)
                _pipeline = pipeline(
                    "text-generation", model=_model, tokenizer=_tokenizer, device=-1 # -1 for CPU
                )
        _model_ready = True
        print(f"[gitwise] Offline model \'{effective_model_name}\' loaded successfully.")
    except Exception as e: 
        # Catches errors during AutoTokenizer.from_pretrained, AutoModelForCausalLM.from_pretrained, or pipeline()
        # This could be due to model files not found (e.g. after a failed download), corrupt files, or other issues.
        print(f"[gitwise] Failed to load offline model \'{effective_model_name}\': {e}")
        _model_ready = False # Ensure model is not marked as ready
        # Raise a specific error that can be caught by the caller if needed.
        raise OfflineModelError(f"Failed to load offline model \'{effective_model_name}\'. Ensure it is downloaded and not corrupt. Original error: {e}") from e

def get_llm_response(prompt: str, **kwargs) -> str:
    ensure_offline_model_ready() # This will attempt to load or prompt for download if necessary
    if not _model_ready or _pipeline is None:
        raise OfflineModelError("Offline model is not available or failed to load. Cannot generate response.")

    prompt = prompt[-2048:] # Truncate prompt if too long for some models
    try:
        # Suppress any further console output from underlying libraries during inference
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            outputs = _pipeline(
                prompt, max_new_tokens=128, do_sample=True, temperature=0.7, pad_token_id=_tokenizer.eos_token_id
            )
        return outputs[0]["generated_text"][len(prompt) :].strip()
    except Exception as e:
        raise RuntimeError(f"Offline LLM inference failed: {e}") from e

def ensure_offline_model_ready():
    """Ensures the offline model is loaded, attempting download if necessary."""
    global _model_ready
    if _model_ready:
        return
    
    from gitwise.llm.download import download_offline_model # Local import to avoid circularity at top level
    
    try:
        _load_offline_model() # Attempt to load first (might succeed if already downloaded)
    except OfflineModelError as e:
        # This means _load_offline_model failed, possibly due to missing files or core deps.
        # If it's due to missing files, download_offline_model will handle it.
        # If it's due to missing core deps (ImportError raised from _load_offline_model), 
        # download_offline_model will also attempt to install them.
        print(f"[gitwise] Offline model not loaded ({e}). Attempting download/setup...")
        download_offline_model() # This function will print its own messages and may sys.exit or prompt for install
        # After download_offline_model, try loading again.
        # If download_offline_model prompted for install and exited, this won't be reached.
        try:
            _load_offline_model()
            if not _model_ready:
                 raise OfflineModelError("Offline model failed to load even after download attempt.")
        except Exception as load_after_download_e:
            # Catch any error during the load attempt after download
            raise OfflineModelError(f"Failed to load offline model after download attempt: {load_after_download_e}") from load_after_download_e
    except Exception as e_final_load_attempt:
        # Catch any other unexpected error during the initial _load_offline_model call
        _model_ready = False
        raise OfflineModelError(f"Unexpected error ensuring offline model readiness: {e_final_load_attempt}") from e_final_load_attempt
