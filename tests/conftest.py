"""Shared test fixtures."""

from __future__ import annotations

from typing import Any

import pytest

from writ_agents.core.schema import InterviewResponse, PartialSpec


class MockProvider:
    """Returns pre-recorded responses in sequence."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0

    async def call(self, conversation: list[dict[str, str]], system: str) -> str:
        if self._index >= len(self._responses):
            raise ValueError("MockProvider ran out of responses")
        response = self._responses[self._index]
        self._index += 1
        return response


@pytest.fixture
def mock_provider_factory() -> Any:
    def _factory(responses: list[str]) -> MockProvider:
        return MockProvider(responses)

    return _factory


def make_interview_response(
    message: str = "Tell me more.",
    confidence: int = 50,
    status: str = "in_progress",
    **partial_kwargs: Any,
) -> str:
    partial = PartialSpec(**partial_kwargs)
    resp = InterviewResponse(
        message=message,
        partial_spec=partial,
        confidence=confidence,
        status=status,  # type: ignore[arg-type]
    )
    return resp.model_dump_json()
