"""Textual TUI application for Writ."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Input

from writ_agents.cli.widgets.chat_panel import ChatPanel
from writ_agents.cli.widgets.spec_card import SpecCard
from writ_agents.core.schema import (
    AgentMessageEvent,
    AwaitingInputEvent,
    InterviewCompleteEvent,
    InterviewErrorEvent,
    PartialSpec,
    Spec,
    SpecUpdateEvent,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class WritApp(App[None]):
    """Main Writ TUI application."""

    CSS_PATH = "styles.tcss"
    TITLE = "Writ"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+r", "restart", "Restart"),
        Binding("ctrl+e", "export", "Export", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._spec: Spec | None = None
        self._partial: PartialSpec = PartialSpec()
        self._confidence: int = 0
        self._generator: AsyncGenerator[object, str | None] | None = None
        self._awaiting_input = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            yield ChatPanel(id="chat")
            yield SpecCard(id="spec")
        yield Input(placeholder="Describe your agent...", id="input")
        yield Footer()

    async def on_mount(self) -> None:
        """Start the interview on mount."""
        await self._start_interview()

    async def _start_interview(self) -> None:
        from writ_agents.cli.config import get_api_key
        from writ_agents.core.interview import run_interview
        from writ_agents.providers.anthropic import AnthropicProvider

        chat = self.query_one(ChatPanel)

        key = get_api_key()
        if not key:
            chat.add_agent_message(
                "Welcome to Writ! To get started, I need your Anthropic API key.\n"
                "Please set the ANTHROPIC_API_KEY environment variable and restart."
            )
            return

        try:
            provider = AnthropicProvider(api_key=key)
        except ValueError as e:
            chat.add_agent_message(f"Configuration error: {e}")
            return

        self._generator = run_interview(provider)
        chat.show_thinking(True)

        async def _run() -> None:
            gen = self._generator
            if gen is None:
                return
            try:
                async for event in gen:
                    if isinstance(event, AgentMessageEvent):
                        chat.show_thinking(False)
                        chat.add_agent_message(event.message)
                    elif isinstance(event, SpecUpdateEvent):
                        self._partial = event.partial_spec
                        self._confidence = event.confidence
                        spec_card = self.query_one(SpecCard)
                        spec_card.update_spec(event.partial_spec)
                    elif isinstance(event, AwaitingInputEvent):
                        self._awaiting_input = True
                        input_widget = self.query_one(Input)
                        input_widget.disabled = False
                        input_widget.focus()
                    elif isinstance(event, InterviewCompleteEvent):
                        self._spec = event.spec
                        chat.add_agent_message(
                            f"\u2705 Your agent **{event.spec.name}** is ready! "
                            "Press Ctrl+E to export all formats."
                        )
                        self._awaiting_input = False
                    elif isinstance(event, InterviewErrorEvent):
                        chat.add_agent_message(f"\u26a0\ufe0f {event.message}")
                        self._awaiting_input = False
            except Exception as e:
                chat.add_agent_message(f"Unexpected error: {e}")

        asyncio.create_task(_run())

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        if not self._awaiting_input or not event.value.strip():
            return

        chat = self.query_one(ChatPanel)
        input_widget = self.query_one(Input)

        user_text = event.value.strip()
        input_widget.value = ""
        input_widget.disabled = True
        self._awaiting_input = False

        chat.add_user_message(user_text)
        chat.show_thinking(True)

        if self._generator is not None:
            with contextlib.suppress(StopAsyncIteration):
                await self._generator.asend(user_text)

    def action_export(self) -> None:
        """Export the compiled spec."""
        if self._spec is None:
            self.query_one(ChatPanel).add_agent_message(
                "The interview isn't complete yet. Keep answering questions!"
            )
            return
        from writ_agents.cli.screens.reveal import RevealScreen

        self.push_screen(RevealScreen(self._spec, []))

    def action_restart(self) -> None:
        """Restart the interview."""
        self._spec = None
        self._partial = PartialSpec()
        self._confidence = 0
        self._generator = None
        self._awaiting_input = False
        chat = self.query_one(ChatPanel)
        chat.clear()
        spec_card = self.query_one(SpecCard)
        spec_card.clear()
        asyncio.create_task(self._start_interview())
