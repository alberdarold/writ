"""Stateless one-step driver for the interview.

This is the lowest common denominator API: given a session and (optionally)
user input, advance the interview by exactly one LLM turn. All callers (TUI,
CLI, MCP server) build on this.
"""

from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, ValidationError

from writ_agents.core.merge import is_spec_complete, merge_partial
from writ_agents.core.prompt import INTERVIEW_SYSTEM_PROMPT
from writ_agents.core.schema import (
    InterviewResponse,
    PartialSpec,
    Spec,
)
from writ_agents.core.session import InterviewSession
from writ_agents.providers.base import LLMProvider

BOOTSTRAP_TOKEN = "[START_INTERVIEW]"
REPAIR_PROMPT = (
    "Your previous response was not valid JSON matching the required schema. "
    "Return ONLY a JSON object with keys: message, partial_spec, confidence, status. "
    "No markdown, no prose."
)
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class StepResult(BaseModel):
    """Result of advancing the interview by one turn."""

    message: str
    partial_spec: PartialSpec
    confidence: int
    status: Literal["in_progress", "ready", "error"]
    spec: Spec | None = None
    error: str | None = None


def _parse_response(raw: str) -> InterviewResponse | None:
    """Extract and validate an InterviewResponse from a raw LLM string.

    Robust to fenced code blocks and trailing prose — grabs the first JSON
    object it finds.
    """
    if not raw:
        return None
    candidates: list[str] = []
    stripped = raw.strip()
    if stripped.startswith("{"):
        candidates.append(stripped)
    match = _JSON_RE.search(raw)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            return InterviewResponse.model_validate(json.loads(candidate))
        except (json.JSONDecodeError, ValidationError):
            continue
    return None


async def _call_with_repair(
    session: InterviewSession, provider: LLMProvider
) -> InterviewResponse | None:
    """Call the provider, parse, attempt one repair on failure."""
    raw = await provider.call(session.conversation, INTERVIEW_SYSTEM_PROMPT)
    parsed = _parse_response(raw)
    if parsed is not None:
        session.conversation.append({"role": "assistant", "content": raw})
        return parsed
    # Repair attempt
    session.conversation.append({"role": "assistant", "content": raw})
    session.conversation.append({"role": "user", "content": REPAIR_PROMPT})
    raw2 = await provider.call(session.conversation, INTERVIEW_SYSTEM_PROMPT)
    parsed2 = _parse_response(raw2)
    if parsed2 is not None:
        session.conversation.append({"role": "assistant", "content": raw2})
        return parsed2
    return None


async def interview_step(
    session: InterviewSession,
    provider: LLMProvider,
    user_input: str | None = None,
) -> StepResult:
    """Advance an interview by one turn.

    - First call (empty conversation): sends the bootstrap token, returns the
      opening question.
    - Subsequent calls: appends the user input and returns the next question
      or the completed spec.
    """
    if session.status in ("ready", "error"):
        return StepResult(
            message="",
            partial_spec=session.accumulated,
            confidence=session.confidence,
            status=session.status if session.status != "ready" else "ready",
            spec=session.spec,
            error=session.error,
        )

    if not session.conversation:
        opening = (
            user_input.strip() if user_input and user_input.strip() else BOOTSTRAP_TOKEN
        )
        session.conversation.append({"role": "user", "content": opening})
    else:
        if not user_input or not user_input.strip():
            return StepResult(
                message="",
                partial_spec=session.accumulated,
                confidence=session.confidence,
                status="in_progress",
            )
        session.conversation.append({"role": "user", "content": user_input.strip()})

    parsed = await _call_with_repair(session, provider)
    if parsed is None:
        session.status = "error"
        session.error = "LLM returned invalid JSON twice."
        return StepResult(
            message="",
            partial_spec=session.accumulated,
            confidence=session.confidence,
            status="error",
            error=session.error,
        )

    session.accumulated = merge_partial(session.accumulated, parsed.partial_spec)
    session.confidence = parsed.confidence

    if parsed.status == "ready":
        complete, missing = is_spec_complete(session.accumulated)
        if not complete:
            session.conversation.append(
                {
                    "role": "user",
                    "content": (
                        "The spec is not complete yet. Missing fields: "
                        f"{', '.join(missing)}. Keep interviewing to fill them."
                    ),
                }
            )
            parsed = await _call_with_repair(session, provider)
            if parsed is None:
                session.status = "error"
                session.error = "LLM failed to recover from incomplete spec."
                return StepResult(
                    message="",
                    partial_spec=session.accumulated,
                    confidence=session.confidence,
                    status="error",
                    error=session.error,
                )
            session.accumulated = merge_partial(
                session.accumulated, parsed.partial_spec
            )
            session.confidence = parsed.confidence
            session.status = "in_progress"
            return StepResult(
                message=parsed.message,
                partial_spec=session.accumulated,
                confidence=session.confidence,
                status="in_progress",
            )
        try:
            spec = Spec.from_partial(session.accumulated)
        except Exception as e:
            session.status = "error"
            session.error = f"Failed to build spec: {e}"
            return StepResult(
                message=parsed.message,
                partial_spec=session.accumulated,
                confidence=session.confidence,
                status="error",
                error=session.error,
            )
        session.spec = spec
        session.status = "ready"
        return StepResult(
            message=parsed.message,
            partial_spec=session.accumulated,
            confidence=session.confidence,
            status="ready",
            spec=spec,
        )

    session.status = "in_progress"
    return StepResult(
        message=parsed.message,
        partial_spec=session.accumulated,
        confidence=session.confidence,
        status="in_progress",
    )
