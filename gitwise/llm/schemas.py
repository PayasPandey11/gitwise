"""Pydantic schemas for structured LLM responses."""

from typing import List
from pydantic import BaseModel, Field


class CommitMessage(BaseModel):
    """Schema for a single commit message."""

    group_id: str = Field(
        ...,
        description="The identifier for the group of changes this commit corresponds to.",
    )
    message: str = Field(..., description="The full commit message (subject and body).")


class PRInfo(BaseModel):
    """Schema for the Pull Request title and body."""

    title: str = Field(..., description="The title of the pull request.")
    body: str = Field(..., description="The body of the pull request in Markdown.")


class GenerationOutput(BaseModel):
    """
    The root schema for the combined generation of PR and commit messages.
    The LLM is expected to return a JSON object that conforms to this structure.
    """

    pull_request: PRInfo = Field(
        ...,
        alias="pullRequest",
        description="The generated title and body for the pull request.",
    )
    commits: List[CommitMessage] = Field(
        ...,
        description="A list of commit messages, one for each group of changes.",
    )

    class Config:
        allow_population_by_field_name = True 