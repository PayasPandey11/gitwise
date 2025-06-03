import os
import typer

from gitwise.config import ConfigError, config_exists, load_config, write_config
from gitwise.core.git_manager import GitManager
from gitwise.llm.model_presets import (
    get_model_options,
    get_model_by_key,
    validate_custom_model_name,
    get_model_display_info,
    DEFAULT_MODEL
)

app = typer.Typer()


def mask(s):
    if not s:
        return ""
    return s[:2] + "***" + s[-2:] if len(s) > 4 else "***"


def check_git_repo() -> bool:
    try:
        return GitManager().is_git_repo()
    except RuntimeError:
        return False


def check_ollama_running() -> bool:
    try:
        import requests

        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def check_offline_model() -> bool:
    # Placeholder: check for a file or model presence as needed
    # For now, always return True
    return True


def display_provider_options() -> None:
    """Display the online provider options."""
    typer.echo("\nChoose your online LLM provider:")
    typer.echo("  1. Direct Providers (Recommended for Enterprise)")
    typer.echo("     Connect directly to Google, OpenAI, or Anthropic")
    typer.echo("     Better cost control, no third-party proxy")
    typer.echo("")
    typer.echo("  2. OpenRouter (Easy Setup)")
    typer.echo("     Access multiple models through one API")
    typer.echo("     Great for experimentation and beginners")


def get_provider_choice() -> str:
    """Get the user's provider choice."""
    display_provider_options()
    
    choice = typer.prompt("Enter choice [1/2]", default="1")
    
    if choice == "1":
        return "direct"
    elif choice == "2":
        return "openrouter"
    else:
        typer.echo("Invalid choice. Using direct providers.")
        return "direct"


def display_direct_provider_options() -> None:
    """Display direct provider options."""
    typer.echo("\nChoose your direct provider:")
    typer.echo("  1. Google Gemini")
    typer.echo("     Google's latest AI models with multimodal capabilities")
    typer.echo("     Great for coding, analysis, and image understanding")
    typer.echo("")
    typer.echo("  2. OpenAI")
    typer.echo("     GPT models including GPT-4, GPT-4 Turbo")
    typer.echo("     Industry standard for most AI applications")
    typer.echo("")
    typer.echo("  3. Anthropic Claude")
    typer.echo("     Claude models known for safety and instruction following")
    typer.echo("     Excellent for complex reasoning and analysis")


def get_direct_provider_choice() -> str:
    """Get the user's direct provider choice."""
    display_direct_provider_options()
    
    choice = typer.prompt("Enter choice [1/2/3]", default="1")
    
    if choice == "1":
        return "google"
    elif choice == "2":
        return "openai"
    elif choice == "3":
        return "anthropic"
    else:
        typer.echo("Invalid choice. Using Google Gemini.")
        return "google"


def configure_gemini_provider(config: dict) -> None:
    """Configure Google Gemini provider."""
    typer.echo("\n=== Google Gemini Configuration ===")
    
    # Check for existing API key
    env_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if env_key:
        masked = mask(env_key)
        use_env = typer.confirm(
            f"A Google API key was found in your environment (starts with: {masked}). Use this key?",
            default=True,
        )
        if use_env:
            config["google_api_key"] = env_key.strip()
        else:
            typer.echo("Enter your Google API key (get one at https://aistudio.google.com/apikey):")
            api_key = typer.prompt("Google API key", hide_input=True)
            config["google_api_key"] = api_key.strip()
    else:
        typer.echo("Enter your Google API key (get one at https://aistudio.google.com/apikey):")
        api_key = typer.prompt("Google API key", hide_input=True)
        config["google_api_key"] = api_key.strip()
    
    # Configure provider and default model
    config["provider"] = "google"
    
    # Model selection for Gemini
    typer.echo("\nChoose your Gemini model:")
    typer.echo("  1. gemini-1.5-pro (Best Quality)")
    typer.echo("  2. gemini-1.5-flash (Balanced - Recommended)")
    typer.echo("  3. gemini-1.0-pro (Fast)")
    
    model_choice = typer.prompt("Enter choice [1/2/3]", default="2")
    if model_choice == "1":
        config["model"] = "gemini-1.5-pro"
    elif model_choice == "3":
        config["model"] = "gemini-1.0-pro"
    else:
        config["model"] = "gemini-1.5-flash"
    
    typer.echo(f"✓ Configured Google Gemini with model: {config['model']}")


def configure_openai_provider(config: dict) -> None:
    """Configure OpenAI provider."""
    typer.echo("\n=== OpenAI Configuration ===")
    
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        masked = mask(env_key)
        use_env = typer.confirm(
            f"An OpenAI API key was found in your environment (starts with: {masked}). Use this key?",
            default=True,
        )
        if use_env:
            config["openai_api_key"] = env_key.strip()
        else:
            typer.echo("Enter your OpenAI API key (get one at https://platform.openai.com/api-keys):")
            api_key = typer.prompt("OpenAI API key", hide_input=True)
            config["openai_api_key"] = api_key.strip()
    else:
        typer.echo("Enter your OpenAI API key (get one at https://platform.openai.com/api-keys):")
        api_key = typer.prompt("OpenAI API key", hide_input=True)
        config["openai_api_key"] = api_key.strip()
    
    config["provider"] = "openai"
    
    typer.echo("\nChoose your OpenAI model:")
    typer.echo("  1. gpt-4o (Latest, Best Multimodal)")
    typer.echo("  2. gpt-4-turbo (Powerful, Optimized)")
    typer.echo("  3. gpt-3.5-turbo (Fast, Cost-effective - Recommended)")
    
    model_choice = typer.prompt("Enter choice [1/2/3]", default="3")
    if model_choice == "1":
        config["openai_model"] = "gpt-4o"
    elif model_choice == "2":
        config["openai_model"] = "gpt-4-turbo"
    else:
        config["openai_model"] = "gpt-3.5-turbo"
    
    typer.echo(f"✓ Configured OpenAI with model: {config['openai_model']}")


def configure_anthropic_provider(config: dict) -> None:
    """Configure Anthropic provider."""
    typer.echo("\n=== Anthropic Claude Configuration ===")
    
    env_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    if env_key:
        masked = mask(env_key)
        use_env = typer.confirm(
            f"An Anthropic API key was found in your environment (starts with: {masked}). Use this key?",
            default=True,
        )
        if use_env:
            config["anthropic_api_key"] = env_key.strip()
        else:
            typer.echo("Enter your Anthropic API key (get one at https://console.anthropic.com/settings/keys):")
            api_key = typer.prompt("Anthropic API key", hide_input=True)
            config["anthropic_api_key"] = api_key.strip()
    else:
        typer.echo("Enter your Anthropic API key (get one at https://console.anthropic.com/settings/keys):")
        api_key = typer.prompt("Anthropic API key", hide_input=True)
        config["anthropic_api_key"] = api_key.strip()

    config["provider"] = "anthropic"
    
    typer.echo("\nChoose your Anthropic Claude model:")
    typer.echo("  1. claude-3-opus-20240229 (Most Powerful)")
    typer.echo("  2. claude-3-sonnet-20240229 (Balanced)")
    typer.echo("  3. claude-3-haiku-20240307 (Fastest - Recommended)")
    
    model_choice = typer.prompt("Enter choice [1/2/3]", default="3")
    if model_choice == "1":
        config["anthropic_model"] = "claude-3-opus-20240229"
    elif model_choice == "2":
        config["anthropic_model"] = "claude-3-sonnet-20240229"
    else:
        config["anthropic_model"] = "claude-3-haiku-20240307"
        
    typer.echo(f"✓ Configured Anthropic Claude with model: {config['anthropic_model']}")


def display_model_options() -> None:
    """Display the 4 model selection options for online mode."""
    typer.echo("\nChoose your OpenRouter model:")
    typer.echo("  1. Best Model (Most Powerful)")
    typer.echo("     Claude Opus 4 - World's best coding model")
    typer.echo("     Premium pricing, highest quality output")
    typer.echo("")
    typer.echo("  2. Balanced Model (Speed vs Performance) [RECOMMENDED]")
    typer.echo("     Claude 3.7 Sonnet - Popular choice, great balance")
    typer.echo("     Moderate pricing, excellent for most use cases")
    typer.echo("")
    typer.echo("  3. Fastest Model")
    typer.echo("     Claude 3 Haiku - Optimized for speed")
    typer.echo("     Budget-friendly, good for simple tasks")
    typer.echo("")
    typer.echo("  4. Custom Model")
    typer.echo("     Enter your own OpenRouter model name")
    typer.echo("     Full flexibility (e.g., google/gemini-2.0-flash-exp)")


def get_model_choice() -> str:
    """Get the user's model choice and return the selected model name."""
    display_model_options()
    
    choice = typer.prompt("Enter choice [1/2/3/4]", default="2")
    
    if choice == "1":
        model_preset = get_model_by_key("best")
        typer.echo(f"Selected: {model_preset['name']}")
        return model_preset["model"]
    elif choice == "2":
        model_preset = get_model_by_key("balanced")
        typer.echo(f"Selected: {model_preset['name']}")
        return model_preset["model"]
    elif choice == "3":
        model_preset = get_model_by_key("fastest")
        typer.echo(f"Selected: {model_preset['name']}")
        return model_preset["model"]
    elif choice == "4":
        return get_custom_model()
    else:
        typer.echo("Invalid choice. Using balanced model (recommended).")
        return get_model_by_key("balanced")["model"]


def get_custom_model() -> str:
    """Get and validate a custom model name from the user."""
    typer.echo("\nEnter a custom OpenRouter model name.")
    typer.echo("Format: provider/model-name (e.g., google/gemini-2.0-flash-exp)")
    typer.echo("See https://openrouter.ai/models for available models.")
    
    while True:
        custom_model = typer.prompt("Model name").strip()
        
        if validate_custom_model_name(custom_model):
            typer.echo(f"Selected: {custom_model}")
            return custom_model
        else:
            typer.echo("❌ Invalid model name format. Please use 'provider/model-name' format.")
            if not typer.confirm("Try again?", default=True):
                typer.echo("Using balanced model as fallback.")
                return get_model_by_key("balanced")["model"]


def configure_openrouter_provider(config: dict) -> None:
    """Configure OpenRouter provider (legacy)."""
    typer.echo("\n=== OpenRouter Configuration ===")
    
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        masked = mask(env_key)
        use_env = typer.confirm(
            f"An OpenRouter API key was found in your environment (starts with: {masked}). Use this key?",
            default=True,
        )
        if use_env:
            config["openrouter_api_key"] = env_key.strip()
        else:
            typer.echo("Enter your OpenRouter API key (see https://openrouter.ai/):")
            api_key = typer.prompt("API key", hide_input=True)
            config["openrouter_api_key"] = api_key.strip()
    else:
        typer.echo("Enter your OpenRouter API key (see https://openrouter.ai/):")
        api_key = typer.prompt("API key", hide_input=True)
        config["openrouter_api_key"] = api_key.strip()

    # Enhanced model selection with 4 options
    selected_model = get_model_choice()
    config["openrouter_model"] = selected_model
    config["provider"] = "openrouter"
    
    typer.echo(f"✓ Configured OpenRouter with model: {selected_model}")


def init_command():
    typer.echo("\n[gitwise] Initializing GitWise for this project...\n")

    # 1. Check for existing config
    if config_exists():
        try:
            current = load_config()
            typer.echo("A GitWise config already exists:")
            for k, v in current.items():
                if "key" in k:
                    v = mask(v)
                typer.echo(f"  {k}: {v}")
            action = typer.prompt(
                "Overwrite, merge, or abort? [o/m/a]", default="a"
            ).lower()
            if action == "a":
                typer.echo("Aborted.")
                raise typer.Exit()
            elif action == "m":
                config = current.copy()
            else:
                config = {}
        except ConfigError:
            typer.echo("Existing config is corrupt. Overwriting.")
            config = {}
    else:
        config = {}

    # 2. Prompt for backend
    typer.echo("\nWhich LLM backend do you want to use?")
    typer.echo("  1. Ollama (local, default)")
    typer.echo("  2. Offline (bundled model)")
    typer.echo("  3. Online (cloud providers)")
    backend_choice = typer.prompt("Enter choice [1/2/3]", default="1")
    if backend_choice == "3":
        config["llm_backend"] = "online"
    elif backend_choice == "2":
        config["llm_backend"] = "offline"
    else:
        config["llm_backend"] = "ollama"

    # 3. Backend-specific prompts
    if config["llm_backend"] == "online":
        provider_type = get_provider_choice()
        
        if provider_type == "direct":
            direct_provider = get_direct_provider_choice()
            
            if direct_provider == "google":
                configure_gemini_provider(config)
            elif direct_provider == "openai":
                configure_openai_provider(config)
            elif direct_provider == "anthropic":
                configure_anthropic_provider(config)
        else:
            configure_openrouter_provider(config)

    elif config["llm_backend"] == "ollama":
        typer.echo(
            "\n[Reminder] If you use Ollama, make sure the server is running (run 'ollama serve') and your model is pulled. See https://ollama.com/download for help."
        )
        model = typer.prompt("Ollama model name", default="llama3")
        config["ollama_model"] = model.strip()
    elif config["llm_backend"] == "offline":
        typer.echo("\nChecking for offline model...")
        if not check_offline_model():
            typer.echo(
                "[Warning] Offline model not found. Please download it before using offline mode."
            )

    # 4. Local vs global config
    if not check_git_repo():
        typer.echo("[Warning] You are not in a git repository.")
        if not typer.confirm("Continue and apply config globally?", default=True):
            typer.echo("Aborted.")
            raise typer.Exit()
        global_config = True
    else:
        global_config = not typer.confirm(
            "Apply config to this repo only?", default=True
        )

    # 5. Write config
    path = write_config(config, global_config=global_config)
    typer.echo(f"\n[gitwise] Config written to: {path}")

    # 6. Summary & next steps
    typer.echo("\n[gitwise] Setup complete! Config summary:")
    for k, v in config.items():
        if "key" in k:
            v = mask(v)
        typer.echo(f"  {k}: {v}")
    typer.echo("\nYou can now use GitWise commands in this repo!\n")


if __name__ == "__main__":
    app.command()(init_command)
    app()
