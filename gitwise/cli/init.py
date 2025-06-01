import os
import typer

from gitwise.config import (ConfigError, config_exists, load_config,
                            write_config)
from gitwise.core.git_manager import GitManager

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
    typer.echo("  3. Online (OpenRouter)")
    backend_choice = typer.prompt("Enter choice [1/2/3]", default="1")
    if backend_choice == "3":
        config["llm_backend"] = "online"
    elif backend_choice == "2":
        config["llm_backend"] = "offline"
    else:
        config["llm_backend"] = "ollama"

    # 3. Backend-specific prompts
    if config["llm_backend"] == "online":
        env_key = os.environ.get("OPENROUTER_API_KEY")
        if env_key:
            masked = env_key[:2] + "***" + env_key[-2:] if len(env_key) > 4 else "***"
            use_env = typer.confirm(
                f"An OpenRouter API key was found in your environment (starts with: {masked}). Use this key?",
                default=True,
            )
            if use_env:
                config["openrouter_api_key"] = env_key.strip()
            else:
                typer.echo(
                    "Enter your OpenRouter API key (see https://openrouter.ai/):"
                )
                api_key = typer.prompt("API key", hide_input=True)
                config["openrouter_api_key"] = api_key.strip()
        else:
            typer.echo("Enter your OpenRouter API key (see https://openrouter.ai/):")
            api_key = typer.prompt("API key", hide_input=True)
            config["openrouter_api_key"] = api_key.strip()

        # ADDED: Prompt for OpenRouter model
        default_online_model = os.environ.get(
            "OPENROUTER_MODEL", "anthropic/claude-3-haiku"
        )
        if typer.confirm(
            f"Set a specific OpenRouter model? (default: {default_online_model})",
            default=False,
        ):
            config["openrouter_model"] = typer.prompt(
                "Model name (e.g., mistralai/mistral-7b-instruct, anthropic/claude-3-opus)",
                default=default_online_model,
            )
        else:
            config[
                "openrouter_model"
            ] = default_online_model  # Explicitly set default if not overriding

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
