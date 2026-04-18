"""Anthropic Claude provider implementation."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from anthropic import AsyncAnthropic

DEFAULT_MODEL = "claude-sonnet-4-5"
CONFIG_PATH = Path.home() / ".writ" / "config.toml"


def _load_api_key() -> str | None:
    """Load API key from env var or config file."""
    if key := os.environ.get("ANTHROPIC_API_KEY"):
        return key
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        return config.get("provider", {}).get("anthropic_api_key")  # type: ignore[no-any-return]
    return None


class AnthropicProvider:
    """Wraps the Anthropic async SDK for use as an LLMProvider."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL) -> None:
        resolved_key = api_key or _load_api_key()
        if not resolved_key:
            raise ValueError(
                "No Anthropic API key found. Set ANTHROPIC_API_KEY env var "
                "or run 'writ create' to configure."
            )
        self._client = AsyncAnthropic(api_key=resolved_key)
        self._model = model

    async def call(self, conversation: list[dict[str, str]], system: str) -> str:
        """Call Claude with conversation history and system prompt."""
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system,
            messages=conversation,  # type: ignore[arg-type]
        )
        block = response.content[0]
        return str(block.text)  # type: ignore[union-attr]
