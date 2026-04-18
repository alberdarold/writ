"""Core async interview loop."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from pydantic import ValidationError

from writ_agents.core.merge import is_spec_complete, merge_partial
from writ_agents.core.prompt import INTERVIEW_SYSTEM_PROMPT
from writ_agents.core.schema import (
    AgentMessageEvent,
    AwaitingInputEvent,
    InterviewCompleteEvent,
    InterviewErrorEvent,
    InterviewResponse,
    PartialSpec,
    Spec,
    SpecUpdateEvent,
)
from writ_agents.providers.base import LLMProvider

REPAIR_PROMPT = (
    "Your previous response was not valid JSON matching the required schema. "
    "Please return ONLY a JSON object with keys: message, partial_spec, confidence, status. "
    "No markdown, no explanation — just the JSON object."
)

InterviewEvent = (
    AwaitingInputEvent
    | AgentMessageEvent
    | SpecUpdateEvent
    | InterviewCompleteEvent
    | InterviewErrorEvent
)


def _parse_response(raw: str) -> InterviewResponse | None:
    """Parse and validate an LLM response string as InterviewResponse."""
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        data = json.loads(cleaned)
        return InterviewResponse.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        return None


async def run_interview(
    provider: LLMProvider,
    initial_input: str | None = None,
) -> AsyncGenerator[InterviewEvent, str | None]:
    """
    Async generator driving the Writ interview loop.

    Yields events:
    - AwaitingInputEvent: waiting for user to type
    - AgentMessageEvent: LLM message to display
    - SpecUpdateEvent: spec state changed
    - InterviewCompleteEvent: interview done, full spec ready
    - InterviewErrorEvent: unrecoverable error
    """
    conversation: list[dict[str, str]] = []
    accumulated = PartialSpec()
    confidence = 0

    # Bootstrap
    conversation.append({"role": "user", "content": "[START_INTERVIEW]"})
    raw = await provider.call(conversation, INTERVIEW_SYSTEM_PROMPT)

    parsed = _parse_response(raw)
    if parsed is None:
        # Try repair
        conversation.append({"role": "assistant", "content": raw})
        conversation.append({"role": "user", "content": REPAIR_PROMPT})
        raw2 = await provider.call(conversation, INTERVIEW_SYSTEM_PROMPT)
        parsed = _parse_response(raw2)
        if parsed is None:
            yield InterviewErrorEvent(
                message="LLM returned invalid JSON twice at startup.", recoverable=False
            )
            return
        conversation.append({"role": "assistant", "content": raw2})
    else:
        conversation.append({"role": "assistant", "content": raw})

    accumulated = merge_partial(accumulated, parsed.partial_spec)
    confidence = parsed.confidence

    yield AgentMessageEvent(message=parsed.message)
    yield SpecUpdateEvent(partial_spec=accumulated, confidence=confidence)

    while True:
        user_input: str | None = yield AwaitingInputEvent()

        if not user_input or not user_input.strip():
            continue

        conversation.append({"role": "user", "content": user_input})
        raw = await provider.call(conversation, INTERVIEW_SYSTEM_PROMPT)

        parsed = _parse_response(raw)
        if parsed is None:
            conversation.append({"role": "assistant", "content": raw})
            conversation.append({"role": "user", "content": REPAIR_PROMPT})
            raw2 = await provider.call(conversation, INTERVIEW_SYSTEM_PROMPT)
            parsed = _parse_response(raw2)
            if parsed is None:
                yield InterviewErrorEvent(
                    message="LLM returned invalid JSON twice.", recoverable=False
                )
                return
            conversation.append({"role": "assistant", "content": raw2})
        else:
            conversation.append({"role": "assistant", "content": raw})

        accumulated = merge_partial(accumulated, parsed.partial_spec)
        confidence = parsed.confidence

        yield AgentMessageEvent(message=parsed.message)
        yield SpecUpdateEvent(partial_spec=accumulated, confidence=confidence)

        if parsed.status == "ready":
            complete, missing = is_spec_complete(accumulated)
            if not complete:
                # Tell LLM it's not actually ready
                missing_str = ", ".join(missing)
                repair = (
                    f"The spec is not complete yet. Missing fields: {missing_str}. "
                    "Please continue the interview to gather these."
                )
                conversation.append({"role": "user", "content": repair})
                raw3 = await provider.call(conversation, INTERVIEW_SYSTEM_PROMPT)
                parsed3 = _parse_response(raw3)
                if parsed3 is None:
                    yield InterviewErrorEvent(
                        message="LLM failed to handle incomplete spec.",
                        recoverable=False,
                    )
                    return
                conversation.append({"role": "assistant", "content": raw3})
                accumulated = merge_partial(accumulated, parsed3.partial_spec)
                confidence = parsed3.confidence
                yield AgentMessageEvent(message=parsed3.message)
                yield SpecUpdateEvent(partial_spec=accumulated, confidence=confidence)
                continue

            try:
                spec = Spec.from_partial(accumulated)
            except Exception as e:
                yield InterviewErrorEvent(
                    message=f"Failed to build final spec: {e}", recoverable=False
                )
                return

            yield InterviewCompleteEvent(spec=spec, confidence=confidence)
            return
