"""Pydantic models for Writ's core data structures."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "0.1.0"

INVALID_NAMES = {"my agent", "your agent", "ai agent", "untitled", "agent"}


class PartialSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    archetype: str | None = None
    tagline: str | None = None
    purpose: str | None = None
    audience: str | None = None
    knowledge_sources: list[str] | None = None
    tools_needed: list[str] | None = None
    guardrails: list[str] | None = None
    oversight: (
        Literal["human_in_loop", "sample_review", "team_review", "autonomous"] | None
    ) = None
    personality_traits: list[str] | None = None
    system_prompt: str | None = None
    target_runtime: Literal["claude", "openai", "gemini", "all"] | None = None


class Spec(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1)
    archetype: str = Field(min_length=1)
    tagline: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    knowledge_sources: list[str]
    tools_needed: list[str]
    guardrails: list[str]
    oversight: Literal["human_in_loop", "sample_review", "team_review", "autonomous"]
    personality_traits: list[str]
    system_prompt: str = Field(min_length=1)
    target_runtime: Literal["claude", "openai", "gemini", "all"]
    schema_version: str = SCHEMA_VERSION

    @field_validator("name")
    @classmethod
    def name_not_placeholder(cls, v: str) -> str:
        if v.strip().lower() in INVALID_NAMES:
            raise ValueError(f"Name '{v}' is a placeholder. Provide a real name.")
        return v

    @classmethod
    def from_partial(cls, partial: PartialSpec) -> Spec:
        """Promote a complete PartialSpec to a Spec. Raises if any field missing."""
        data = partial.model_dump(exclude_none=False)
        data["schema_version"] = SCHEMA_VERSION
        return cls.model_validate(data)


class InterviewResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str = Field(min_length=1, description="Message shown to the user")
    partial_spec: PartialSpec = Field(default_factory=PartialSpec)
    confidence: int = Field(ge=0, le=100)
    status: Literal["in_progress", "ready"] = "in_progress"


class ResolvedConnector(BaseModel):
    connector_id: str
    name: str
    source: Literal["mcp", "oauth", "manual"]
    icon: str
    description: str
    business_terms: list[str]
    mcp_url: str | None = None


# Event types for the interview async generator
class AwaitingInputEvent(BaseModel):
    prompt: str = ""


class AgentMessageEvent(BaseModel):
    message: str


class SpecUpdateEvent(BaseModel):
    partial_spec: PartialSpec
    confidence: int


class InterviewCompleteEvent(BaseModel):
    spec: Spec
    confidence: int


class InterviewErrorEvent(BaseModel):
    message: str
    recoverable: bool


InterviewEvent = (
    AwaitingInputEvent
    | AgentMessageEvent
    | SpecUpdateEvent
    | InterviewCompleteEvent
    | InterviewErrorEvent
)
