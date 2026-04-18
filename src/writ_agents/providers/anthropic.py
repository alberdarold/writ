"""Anthropic Claude provider — used for interview + connector resolution."""

from __future__ import annotations

import asyncio
import os
import tomllib
from pathlib import Path

from anthropic import (
    APIConnectionError,
    APIStatusError,
    AsyncAnthropic,
    InternalServerError,
    RateLimitError,
)

DEFAULT_MODEL = "claude-sonnet-4-5"
CONFIG_PATH = Path.home() / ".writ" / "config.toml"

_RETRY_ERRORS: tuple[type[Exception], ...] = (
    RateLimitError,
    APIConnectionError,
    InternalServerError,
)
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0  # seconds; doubles each attempt


def _load_api_key() -> str | None:
    """Load API key from env var or ~/.writ/config.toml."""
    if key := os.environ.get("ANTHROPIC_API_KEY"):
        return key
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        val = config.get("provider", {}).get("anthropic_api_key")
        return val if isinstance(val, str) else None
    return None


class AnthropicProvider:
    """Async Anthropic provider with retries + prompt caching on the system block."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 2048,
    ) -> None:
        resolved_key = api_key or _load_api_key()
        if not resolved_key:
            raise ValueError(
                "No Anthropic API key found. Set ANTHROPIC_API_KEY env var "
                "or run 'writ create' to configure."
            )
        self._client = AsyncAnthropic(api_key=resolved_key)
        self._model = model
        self._max_tokens = max_tokens

    async def call(self, conversation: list[dict[str, str]], system: str) -> str:
        """Call Claude with conversation + system prompt. Returns first text block."""
        # Prompt caching on the system block. Anthropic activates caching only
        # when the cached content exceeds ~1024 tokens for Sonnet/Opus; shorter
        # prompts pass through without savings but the hint is harmless.
        system_blocks = [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    system=system_blocks,  # type: ignore[arg-type]
                    messages=conversation,  # type: ignore[arg-type]
                )
                break
            except _RETRY_ERRORS as e:
                last_err = e
                if attempt == _MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(_BACKOFF_BASE * (2**attempt))
            except APIStatusError:
                raise
        else:  # pragma: no cover — defensive
            if last_err is not None:
                raise last_err

        for block in response.content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                return text
        return ""
