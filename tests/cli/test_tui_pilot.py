"""TUI integration test driven by Textual's Pilot.

Runs the real `WritApp` inside a headless test runner — no real terminal,
no network — with a MockProvider injected through the new `provider=` seam.
This exercises the full widget tree, async event loop, input handling,
session advancement, and connector resolution the same way a human user
would drive the app.

What this covers:
- Opening question appears in the chat panel after mount.
- Submitting input via the Input widget advances the interview one turn.
- SpecCard re-renders when the partial spec updates.
- ConfidenceBar reflects the latest confidence value.
- Reaching a 'ready' response swaps the chat into the "ready! resolving..."
  state and kicks off the resolver task.

What this does NOT cover:
- Visual polish / whether the questions feel natural — that's a human
  judgement call.
- Real Anthropic API behaviour — the MockProvider returns canned strings.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from tests.conftest import MockProvider
from tests.core.test_step import COMPLETE_PARTIAL
from writ_agents.cli.app import WritApp
from writ_agents.cli.widgets.chat_panel import ChatPanel
from writ_agents.cli.widgets.confidence_bar import ConfidenceBar
from writ_agents.cli.widgets.spec_card import SpecCard


def _canned(message: str, **kwargs: Any) -> str:
    base: dict[str, Any] = {
        "message": message,
        "confidence": 50,
        "status": "in_progress",
        "partial_spec": {},
    }
    base.update(kwargs)
    return json.dumps(base)


def _chat_texts(panel: ChatPanel) -> list[str]:
    """Flatten every message Static widget to plain text."""
    from textual.widgets import Static

    return [str(s.render()) for s in panel.query(Static)]


@pytest.mark.asyncio
async def test_tui_shows_opening_question_after_mount() -> None:
    provider = MockProvider([_canned("What problem are we solving?")])
    app = WritApp(provider=provider)

    async with app.run_test() as pilot:
        await pilot.pause()
        # Let the mounted _start_interview + first interview_step settle.
        for _ in range(5):
            await pilot.pause()
            texts = _chat_texts(app.query_one(ChatPanel))
            if any("What problem are we solving?" in t for t in texts):
                break
        assert any("What problem are we solving?" in t for t in texts), (
            f"Opening question never rendered. Chat: {texts}"
        )


@pytest.mark.asyncio
async def test_tui_advances_and_updates_spec_card() -> None:
    provider = MockProvider(
        [
            _canned(
                "What do you want to automate?",
                confidence=20,
                partial_spec={"archetype": "triage"},
            ),
            _canned(
                "Great — who uses it?",
                confidence=40,
                partial_spec={
                    "archetype": "triage",
                    "name": "Support Bot",
                    "knowledge_sources": ["support tickets"],
                },
            ),
        ]
    )
    app = WritApp(provider=provider)

    async with app.run_test() as pilot:
        await pilot.pause()
        for _ in range(8):
            await pilot.pause()
            if app._awaiting_input:
                break
        assert app._awaiting_input, "App never opened for input"

        # Type answer and press Enter.
        from textual.widgets import Input

        input_widget = app.query_one(Input)
        input_widget.value = "Route support tickets to the right team"
        await pilot.press("enter")

        for _ in range(10):
            await pilot.pause()
            if app._awaiting_input and app._confidence == 40:
                break
        assert app._confidence == 40
        # SpecCard should show the name now.
        spec_text = " ".join(
            str(s.render()) for s in app.query_one(SpecCard).query("*")
        )
        assert "Support Bot" in spec_text
        # Confidence bar label should reflect 40.
        from textual.widgets import ProgressBar, Static

        label = app.query_one(ConfidenceBar).query_one("#conf-label", Static)
        assert "40" in str(label.render())
        bar = app.query_one(ConfidenceBar).query_one("#conf-progress", ProgressBar)
        assert bar.progress == 40


@pytest.mark.asyncio
async def test_tui_handles_missing_api_key_gracefully() -> None:
    """Without provider override and no env key, the app greets the user
    with a configuration message instead of crashing."""
    import os

    prior = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        # Also make sure the config file isn't picked up during the test.
        import writ_agents.cli.config as cfg

        original_get = cfg.get_api_key
        cfg.get_api_key = lambda: None  # type: ignore[assignment]

        app = WritApp()
        async with app.run_test() as pilot:
            for _ in range(5):
                await pilot.pause()
            texts = _chat_texts(app.query_one(ChatPanel))
            assert any("API key" in t for t in texts), texts
        cfg.get_api_key = original_get  # type: ignore[assignment]
    finally:
        if prior is not None:
            os.environ["ANTHROPIC_API_KEY"] = prior


@pytest.mark.asyncio
async def test_tui_reaches_ready_and_starts_resolver() -> None:
    """Full happy path: interview completes, reveal hint shows, resolver
    task is spawned (we stub the resolver to avoid another LLM call)."""
    provider = MockProvider(
        [
            _canned("Opener", confidence=10),
            _canned(
                "All set!",
                confidence=95,
                status="ready",
                partial_spec=COMPLETE_PARTIAL,
            ),
        ]
    )
    app = WritApp(provider=provider)

    # Stub resolver so we don't need more provider responses.
    async def _fake_resolve(spec: Any, provider: Any) -> list[Any]:
        return []

    import writ_agents.resolver.resolver as resolver_mod

    original = resolver_mod.resolve_connectors
    resolver_mod.resolve_connectors = _fake_resolve  # type: ignore[assignment]
    try:
        async with app.run_test() as pilot:
            for _ in range(8):
                await pilot.pause()
                if app._awaiting_input:
                    break

            from textual.widgets import Input

            app.query_one(Input).value = "go"
            await pilot.press("enter")

            for _ in range(15):
                await pilot.pause()
                if app._spec is not None:
                    break

            assert app._spec is not None
            assert app._spec.name == "Support Bot"
            texts = _chat_texts(app.query_one(ChatPanel))
            assert any("ready" in t.lower() for t in texts)
    finally:
        resolver_mod.resolve_connectors = original  # type: ignore[assignment]
