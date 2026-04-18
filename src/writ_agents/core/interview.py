"""Core async interview loop — a thin generator over `interview_step`.

Prefer `interview_step` directly for any non-streaming caller (MCP, HTTP, CLI).
The generator is only a convenience for push-driven consumers (the TUI).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from writ_agents.core.schema import (
    AgentMessageEvent,
    AwaitingInputEvent,
    InterviewCompleteEvent,
    InterviewErrorEvent,
    SpecUpdateEvent,
)
from writ_agents.core.session import InterviewSession
from writ_agents.core.step import interview_step
from writ_agents.providers.base import LLMProvider

InterviewEvent = (
    AwaitingInputEvent
    | AgentMessageEvent
    | SpecUpdateEvent
    | InterviewCompleteEvent
    | InterviewErrorEvent
)


async def run_interview(
    provider: LLMProvider,
    initial_input: str | None = None,
    session: InterviewSession | None = None,
) -> AsyncGenerator[InterviewEvent, str | None]:
    """Drive an interview as an async generator of events.

    IMPORTANT: callers must drive the generator with a single consumer. Do not
    mix `async for` with external `asend()` — that causes concurrent generator
    advances. The correct pattern is to drive the generator manually with
    `asend`, or consume with `async for` and never call `asend`.
    """
    session = session or InterviewSession()

    result = await interview_step(session, provider, user_input=initial_input)
    yield AgentMessageEvent(message=result.message)
    yield SpecUpdateEvent(
        partial_spec=result.partial_spec, confidence=result.confidence
    )
    if result.status == "error":
        yield InterviewErrorEvent(
            message=result.error or "Unknown error", recoverable=False
        )
        return
    if result.status == "ready" and result.spec is not None:
        yield InterviewCompleteEvent(spec=result.spec, confidence=result.confidence)
        return

    while True:
        user_input: str | None = yield AwaitingInputEvent()
        if not user_input or not user_input.strip():
            continue
        result = await interview_step(session, provider, user_input=user_input)
        yield AgentMessageEvent(message=result.message)
        yield SpecUpdateEvent(
            partial_spec=result.partial_spec, confidence=result.confidence
        )
        if result.status == "error":
            yield InterviewErrorEvent(
                message=result.error or "Unknown error", recoverable=False
            )
            return
        if result.status == "ready" and result.spec is not None:
            yield InterviewCompleteEvent(spec=result.spec, confidence=result.confidence)
            return
