import typer
from typing import List

def yes_option() -> bool:
    return typer.Option(
        False,
        "--yes", "-y",
        help="Automatically answer 'yes' to all prompts"
    )

def base_option() -> str:
    return typer.Option(
        None,
        "--base", "-b", 
        help="Base branch for the operation"
    )

def title_option() -> str:
    return typer.Option(
        None,
        "--title", "-t",
        help="Custom title"
    )

def draft_option() -> bool:
    return typer.Option(
        False,
        "--draft", "-d",
        help="Create in draft mode"
    )

def labels_option() -> bool:
    return typer.Option(
        False,
        "--labels", "-l",
        help="Add relevant labels automatically"
    )

def checklist_option() -> bool:
    return typer.Option(
        False,
        "--checklist", "-c",
        help="Add context-aware checklist"
    )

def files_argument() -> List[str]:
    return typer.Argument(
        None,
        help="Files to process"
    )

def group_option() -> bool:
    return typer.Option(
        False,
        "--group", "-g", 
        help="Enable intelligent grouping"
    )

COMMAND_HELP = {
    "add": "Stage files with interactive selection",
    "commit": "Create commits with AI-generated messages",
    "push": "Push changes to remote repository with optional PR creation",
    "pr": "Create pull requests with AI-generated descriptions", 
    "merge": "Perform smart merges with conflict analysis",
    "changelog": "Generate and maintain changelogs",
    "context": "Manage contextual information per branch",
    "init": "Initialize GitWise configuration"
}

class StandardParams:
    @staticmethod
    def auto_confirm() -> bool:
        return yes_option()
    
    @staticmethod
    def pr_creation() -> tuple:
        return (
            labels_option(),
            checklist_option(), 
            draft_option(),
            base_option(),
            title_option()
        )
    
    @staticmethod
    def base_branch() -> str:
        return base_option()
    
    @staticmethod
    def output_format() -> str:
        return typer.Option("markdown", "--format", "-f", help="Output format")

def validate_version_string(version: str) -> str:
    if not version:
        return version
    
    if version.startswith('v'):
        version = version[1:]
    
    import re
    if not re.match(r'^\d+\.\d+\.\d+', version):
        raise typer.BadParameter(
            "Version must be in semantic version format (e.g., 1.2.3)"
        )
    
    return version

def validate_branch_name(branch: str) -> str:
    if not branch:
        return branch
    
    import re
    if not re.match(r'^[a-zA-Z0-9/_-]+$', branch):
        raise typer.BadParameter("Branch name contains invalid characters")
    
    return branch

ERROR_MESSAGES = {
    "no_files": "No files specified and no default files found",
    "config_required": "Configuration required. Run 'gitwise init' first",
    "llm_unavailable": "LLM backend unavailable: {reason}",
    "network_error": "Network error: {reason}",
    "api_key_missing": "API key required for {provider}"
}

def get_error_message(key: str, **kwargs) -> str:
    template = ERROR_MESSAGES.get(key, key)
    return template.format(**kwargs) if kwargs else template

def format_success_message(message: str) -> str:
    return f"✅ {message}"

def format_error_message(message: str) -> str:
    return f"❌ {message}"

def format_warning_message(message: str) -> str:
    return f"⚠️ {message}"