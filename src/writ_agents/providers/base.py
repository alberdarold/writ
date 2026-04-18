"""Protocol definition for LLM providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal interface all LLM providers must implement."""

    async def call(self, conversation: list[dict[str, str]], system: str) -> str:
        """Call the LLM with a conversation history and system prompt."""
        ...
