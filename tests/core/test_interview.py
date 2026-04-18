"""Tests for the interview loop with mock provider."""

from __future__ import annotations

import json

import pytest

from tests.conftest import MockProvider
from writ_agents.core.schema import (
    AgentMessageEvent,
    AwaitingInputEvent,
    InterviewErrorEvent,
)


def _make_response(**kwargs: object) -> str:
    defaults: dict[str, object] = {
        "message": "Tell me more.",
        "confidence": 50,
        "status": "in_progress",
        "partial_spec": {},
    }
    defaults.update(kwargs)
    return json.dumps(defaults)


def _ready_response(partial_spec_data: dict[str, object]) -> str:
    return json.dumps(
        {
            "message": "Your agent is ready!",
            "confidence": 90,
            "status": "ready",
            "partial_spec": partial_spec_data,
        }
    )


COMPLETE_PARTIAL = {
    "name": "Support Bot",
    "archetype": "triage",
    "tagline": "I help route support tickets.",
    "purpose": "Route incoming support emails to the right team.",
    "audience": "Support managers",
    "knowledge_sources": ["support tickets", "product docs"],
    "tools_needed": ["send Slack message", "update ticket"],
    "guardrails": ["Never close tickets without approval"],
    "oversight": "human_in_loop",
    "personality_traits": ["friendly", "concise"],
    "system_prompt": "You are a support triage assistant. Route tickets based on severity.",
    "target_runtime": "all",
}


@pytest.mark.asyncio
async def test_interview_first_message() -> None:
    provider = MockProvider([_make_response(message="What problem are you solving?")])

    from writ_agents.core.interview import run_interview

    gen = run_interview(provider)

    events = []
    async for event in gen:
        events.append(event)
        if isinstance(event, AwaitingInputEvent):
            break

    agent_msgs = [e for e in events if isinstance(e, AgentMessageEvent)]
    assert len(agent_msgs) >= 1
    assert "What problem are you solving?" in agent_msgs[0].message


@pytest.mark.asyncio
async def test_interview_invalid_json_triggers_repair() -> None:
    """First response is invalid JSON, second is the repair."""
    repair_response = _make_response(message="Let's continue.")
    provider = MockProvider(["NOT VALID JSON {{{", repair_response])

    from writ_agents.core.interview import run_interview

    gen = run_interview(provider)

    events = []
    async for event in gen:
        events.append(event)
        if isinstance(event, AwaitingInputEvent):
            break

    # Should have recovered
    agent_msgs = [e for e in events if isinstance(e, AgentMessageEvent)]
    assert len(agent_msgs) >= 1


@pytest.mark.asyncio
async def test_interview_double_invalid_json_errors() -> None:
    """Two consecutive invalid JSON responses cause an error."""
    provider = MockProvider(["bad json 1", "bad json 2"])

    from writ_agents.core.interview import run_interview

    gen = run_interview(provider)

    events = []
    async for event in gen:
        events.append(event)

    errors = [e for e in events if isinstance(e, InterviewErrorEvent)]
    assert len(errors) >= 1
    assert not errors[0].recoverable
