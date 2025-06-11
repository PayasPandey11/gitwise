"""
This module contains the core logic for generating structured content 
from LLMs, such as combined PR descriptions and commit messages.
"""

import json
import re
from typing import List, Dict, Optional

from pydantic import ValidationError

from gitwise.llm.router import get_llm_response
from gitwise.prompts import PROMPT_PR_AND_COMMITS
from gitwise.llm.schemas import GenerationOutput
from gitwise.ui import components


def _extract_json_block(text: str) -> Optional[str]:
    """
    Finds and extracts the first valid JSON block from a string.
    Handles cases where the JSON is embedded in markdown code blocks.
    """
    # Pattern to find JSON within markdown-style code blocks
    pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1)
    else:
        # Fallback for raw JSON that might start with '{' and end with '}'
        # This is less robust but can catch simple cases.
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace : last_brace + 1]

    return None


def generate_pr_and_commits(
    diffs: List[Dict[str, str]], guidance: str = ""
) -> Optional[GenerationOutput]:
    """
    Generates a PR description and commit messages from a list of diffs in one LLM call.

    Args:
        diffs: A list of dictionaries, where each dict contains a 'group_id' and a 'diff'.
        guidance: Optional user-provided guidance to the LLM.

    Returns:
        A GenerationOutput object containing the PR info and commit messages, or None on failure.
    """
    components.show_section("Generating PR and Commit Messages with AI")

    with components.show_spinner("Calling LLM to generate content..."):
        try:
            # Format the diffs into a JSON string for the prompt
            change_groups_json = json.dumps(diffs, indent=2)

            # Format the final prompt
            prompt = PROMPT_PR_AND_COMMITS.replace(
                "{{change_groups_json}}", change_groups_json
            ).replace("{{guidance}}", guidance)

            # Call the LLM
            llm_output = get_llm_response(prompt)

            if not llm_output:
                components.show_error("LLM returned an empty response.")
                return None

        except Exception as e:
            components.show_error(f"Error calling LLM: {e}")
            return None

    with components.show_spinner("Parsing and validating LLM response..."):
        json_block = _extract_json_block(llm_output)

        if not json_block:
            components.show_error("Could not find a JSON block in the LLM response.")
            components.console.print("[bold yellow]LLM Output:[/bold yellow]")
            components.console.print(llm_output)
            return None

        try:
            # Parse the JSON data
            parsed_json = json.loads(json_block)
            # Validate with Pydantic
            generation_data = GenerationOutput.parse_obj(parsed_json)
            return generation_data
        except json.JSONDecodeError:
            components.show_error("Failed to decode JSON from the LLM response.")
            components.console.print("[bold yellow]Extracted Block:[/bold yellow]")
            components.console.print(json_block)
            return None
        except ValidationError as e:
            components.show_error("LLM response did not match the required format.")
            components.console.print(e)
            return None
        except Exception as e:
            components.show_error(f"An unexpected error occurred during parsing: {e}")
            return None 