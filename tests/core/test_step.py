"""Tests for the stateless interview_step driver."""

from __future__ import annotations

import json

import pytest

from tests.conftest import MockProvider
from writ_agents.core.session import InterviewSession
from writ_agents.core.step import _parse_response, interview_step


def _make_response(**kwargs: object) -> str:
    defaults: dict[str, object] = {
        "message": "Tell me more.",
        "confidence": 50,
        "status": "in_progress",
        "partial_spec": {},
    }
    defaults.update(kwargs)
    return json.dumps(defaults)


COMPLETE_PARTIAL = {
    "name": "Support Bot",
    "archetype": "triage",
    "tagline": "I help route support tickets.",
    "purpose": "Route incoming support emails to the right team.",
    "audience": "Support managers",
    "knowledge_sources": ["support tickets"],
    "tools_needed": ["send Slack message"],
    "guardrails": ["Never close without approval"],
    "oversight": "human_in_loop",
    "personality_traits": ["friendly", "concise"],
    "system_prompt": "You are a support triage assistant.",
    "target_runtime": "all",
}


@pytest.mark.asyncio
async def test_step_bootstraps_on_empty_session() -> None:
    provider = MockProvider([_make_response(message="What problem?")])
    session = InterviewSession()
    result = await interview_step(session, provider)
    assert result.status == "in_progress"
    assert "What problem?" in result.message
    assert session.conversation[0]["content"] == "[START_INTERVIEW]"


@pytest.mark.asyncio
async def test_step_returns_ready_with_spec_when_complete() -> None:
    provider = MockProvider(
        [
            _make_response(message="Opening", confidence=10),
            _make_response(
                message="All set!",
                confidence=95,
                status="ready",
                partial_spec=COMPLETE_PARTIAL,
            ),
        ]
    )
    session = InterviewSession()
    await interview_step(session, provider)
    result = await interview_step(session, provider, user_input="go ahead")
    assert result.status == "ready"
    assert result.spec is not None
    assert result.spec.name == "Support Bot"


@pytest.mark.asyncio
async def test_step_rejects_ready_with_incomplete_partial() -> None:
    # LLM says ready but partial is missing fields -> should loop back
    incomplete = {k: v for k, v in COMPLETE_PARTIAL.items() if k != "guardrails"}
    provider = MockProvider(
        [
            _make_response(message="Opening"),
            _make_response(
                message="Claiming ready",
                status="ready",
                confidence=90,
                partial_spec=incomplete,
            ),
            _make_response(message="Let me fix that"),
        ]
    )
    session = InterviewSession()
    await interview_step(session, provider)
    result = await interview_step(session, provider, user_input="go")
    assert result.status == "in_progress"
    assert result.spec is None


@pytest.mark.asyncio
async def test_step_repair_on_invalid_json() -> None:
    provider = MockProvider(["NOT JSON", _make_response(message="Recovered")])
    session = InterviewSession()
    result = await interview_step(session, provider)
    assert result.status == "in_progress"
    assert "Recovered" in result.message


@pytest.mark.asyncio
async def test_step_error_after_double_invalid_json() -> None:
    provider = MockProvider(["bad1", "bad2"])
    session = InterviewSession()
    result = await interview_step(session, provider)
    assert result.status == "error"
    assert session.status == "error"


@pytest.mark.asyncio
async def test_step_ignores_empty_user_input_after_bootstrap() -> None:
    provider = MockProvider([_make_response(message="opening")])
    session = InterviewSession()
    await interview_step(session, provider)
    # Second call with empty input should not consume a response
    result = await interview_step(session, provider, user_input="   ")
    assert result.status == "in_progress"
    # Only one assistant message in conversation
    assistants = [m for m in session.conversation if m["role"] == "assistant"]
    assert len(assistants) == 1


def test_parse_response_strips_markdown_fence() -> None:
    raw = '```json\n{"message": "hi", "confidence": 50, "status": "in_progress", "partial_spec": {}}\n```'
    parsed = _parse_response(raw)
    assert parsed is not None
    assert parsed.message == "hi"


def test_parse_response_handles_trailing_prose() -> None:
    raw = 'Here you go:\n{"message": "hi", "confidence": 50, "status": "in_progress", "partial_spec": {}}\n(hope this helps!)'
    parsed = _parse_response(raw)
    assert parsed is not None


def test_parse_response_returns_none_on_garbage() -> None:
    assert _parse_response("") is None
    assert _parse_response("not json at all") is None
    assert _parse_response("{broken") is None
