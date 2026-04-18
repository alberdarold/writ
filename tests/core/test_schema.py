"""Tests for core Pydantic schemas."""

import pytest
from pydantic import ValidationError

from writ_agents.core.schema import (
    SCHEMA_VERSION,
    InterviewResponse,
    PartialSpec,
    Spec,
)

VALID_SPEC_DATA = {
    "name": "Support Triage Bot",
    "archetype": "triage",
    "tagline": "I help you route customer issues to the right team fast.",
    "purpose": "Automatically classify and route incoming customer support tickets.",
    "audience": "Support team managers",
    "knowledge_sources": ["support ticket history", "product documentation"],
    "tools_needed": ["send Slack message", "update ticket status"],
    "guardrails": ["Never close a ticket without human review"],
    "oversight": "human_in_loop",
    "personality_traits": ["concise", "professional", "empathetic"],
    "system_prompt": "You are a support triage assistant...",
    "target_runtime": "all",
}


def test_spec_valid() -> None:
    spec = Spec.model_validate(VALID_SPEC_DATA)
    assert spec.name == "Support Triage Bot"
    assert spec.schema_version == SCHEMA_VERSION


def test_spec_placeholder_name_rejected() -> None:
    data = {**VALID_SPEC_DATA, "name": "my agent"}
    with pytest.raises(ValidationError):
        Spec.model_validate(data)


def test_spec_placeholder_name_case_insensitive() -> None:
    data = {**VALID_SPEC_DATA, "name": "AI Agent"}
    with pytest.raises(ValidationError):
        Spec.model_validate(data)


def test_spec_empty_name_rejected() -> None:
    data = {**VALID_SPEC_DATA, "name": ""}
    with pytest.raises(ValidationError):
        Spec.model_validate(data)


def test_spec_invalid_oversight() -> None:
    data = {**VALID_SPEC_DATA, "oversight": "always_manual"}
    with pytest.raises(ValidationError):
        Spec.model_validate(data)


def test_spec_extra_fields_ignored() -> None:
    data = {**VALID_SPEC_DATA, "unknown_field": "ignored"}
    spec = Spec.model_validate(data)
    assert not hasattr(spec, "unknown_field")


def test_interview_response_confidence_bounds() -> None:
    with pytest.raises(ValidationError):
        InterviewResponse(message="hi", confidence=101, status="in_progress")
    with pytest.raises(ValidationError):
        InterviewResponse(message="hi", confidence=-1, status="in_progress")


def test_interview_response_valid() -> None:
    resp = InterviewResponse(
        message="What problem are you solving?",
        partial_spec=PartialSpec(purpose="route support tickets"),
        confidence=30,
        status="in_progress",
    )
    assert resp.confidence == 30


def test_partial_spec_all_none() -> None:
    p = PartialSpec()
    assert p.name is None
    assert p.knowledge_sources is None


def test_spec_from_partial() -> None:
    partial = PartialSpec(**{k: v for k, v in VALID_SPEC_DATA.items()})
    spec = Spec.from_partial(partial)
    assert spec.name == "Support Triage Bot"


def test_spec_from_partial_missing_field() -> None:
    data = {k: v for k, v in VALID_SPEC_DATA.items() if k != "purpose"}
    partial = PartialSpec(**data)
    with pytest.raises(ValidationError):
        Spec.from_partial(partial)
