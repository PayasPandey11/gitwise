from typing import List, Dict, Optional
import os
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)

def render_pr_description(
    pr_title: str,
    summary: str,
    commits: List[Dict[str, str]],
    motivation: str = "",
    checklist: str = ""
) -> str:
    """
    Render the PR description template with the given variables.
    """
    template = env.get_template("pr_description.md")
    return template.render(
        pr_title=pr_title,
        summary=summary,
        commits=commits,
        motivation=motivation,
        checklist=checklist
    )

def render_commit_message(
    type_: str,
    scope: Optional[str],
    description: str,
    body: str = "",
    breaking_change: str = ""
) -> str:
    """
    Render the commit message template with the given variables.
    """
    template = env.get_template("commit_message.md")
    scope_str = f"({scope})" if scope else ""
    return template.render(
        type=type_,
        scope=scope_str,
        description=description,
        body=body,
        breaking_change=breaking_change
    ) 