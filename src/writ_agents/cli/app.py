"""Textual TUI application for Writ."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Input

from writ_agents.cli.widgets.chat_panel import ChatPanel
from writ_agents.cli.widgets.confidence_bar import ConfidenceBar
from writ_agents.cli.widgets.spec_card import SpecCard
from writ_agents.core.schema import PartialSpec, ResolvedConnector, Spec
from writ_agents.core.session import InterviewSession

if TYPE_CHECKING:
    from writ_agents.providers.base import LLMProvider


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
        self._session: InterviewSession | None = None
        self._provider: LLMProvider | None = None
        self._connectors: list[ResolvedConnector] = []
        self._awaiting_input = False
        self._interview_task: asyncio.Task[None] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield ConfidenceBar(id="confidence")
        with Horizontal(id="main"):
            yield ChatPanel(id="chat")
            yield SpecCard(id="spec")
        yield Input(placeholder="Describe your agent...", id="input")
        yield Footer()

    async def on_mount(self) -> None:
        await self._start_interview()

    async def _start_interview(self) -> None:
        from writ_agents.cli.config import get_api_key
        from writ_agents.providers.anthropic import AnthropicProvider

        chat = self.query_one(ChatPanel)
        input_widget = self.query_one(Input)
        input_widget.disabled = True

        key = get_api_key()
        if not key:
            chat.add_agent_message(
                "Welcome to Writ! I need your Anthropic API key to continue.\n"
                "Set ANTHROPIC_API_KEY and restart, or run `writ config` to save it."
            )
            return

        try:
            self._provider = AnthropicProvider(api_key=key)
        except ValueError as e:
            chat.add_agent_message(f"Configuration error: {e}")
            return

        self._session = InterviewSession()
        chat.show_thinking(True)
        await self._advance(user_input=None)

    async def _advance(self, user_input: str | None) -> None:
        """Drive the interview one step. Safe to call from the input handler."""
        from writ_agents.core.step import interview_step

        assert self._provider is not None
        assert self._session is not None
        chat = self.query_one(ChatPanel)

        try:
            result = await interview_step(
                self._session, self._provider, user_input=user_input
            )
        except Exception as e:
            chat.show_thinking(False)
            chat.add_agent_message(f"\u26a0\ufe0f Provider error: {e}")
            return

        chat.show_thinking(False)

        self._partial = result.partial_spec
        self._confidence = result.confidence
        self.query_one(SpecCard).update_spec(result.partial_spec)
        self.query_one(ConfidenceBar).set_confidence(result.confidence)

        if result.message:
            chat.add_agent_message(result.message)

        if result.status == "error":
            chat.add_agent_message(f"\u26a0\ufe0f {result.error or 'Unknown error'}")
            self._awaiting_input = False
            return

        if result.status == "ready" and result.spec is not None:
            self._spec = result.spec
            chat.add_agent_message(
                f"\u2705 Your agent **{result.spec.name}** is ready! Resolving connectors..."
            )
            asyncio.create_task(self._resolve_and_announce())
            self._awaiting_input = False
            return

        self._awaiting_input = True
        input_widget = self.query_one(Input)
        input_widget.disabled = False
        input_widget.focus()

    async def _resolve_and_announce(self) -> None:
        from writ_agents.resolver.resolver import resolve_connectors

        chat = self.query_one(ChatPanel)
        if self._spec is None or self._provider is None:
            return
        try:
            self._connectors = await resolve_connectors(self._spec, self._provider)
        except Exception as e:
            chat.add_agent_message(f"(Connector resolution failed: {e})")
            self._connectors = []
            return
        count = len(self._connectors)
        chat.add_agent_message(
            f"Resolved {count} connector(s). Press **Ctrl+E** to export all formats."
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
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
        await self._advance(user_input=user_text)

    def action_export(self) -> None:
        if self._spec is None:
            self.query_one(ChatPanel).add_agent_message(
                "The interview isn't complete yet. Keep answering questions!"
            )
            return
        from writ_agents.cli.screens.reveal import RevealScreen

        self.push_screen(RevealScreen(self._spec, self._connectors))

    def action_restart(self) -> None:
        self._spec = None
        self._partial = PartialSpec()
        self._confidence = 0
        self._session = None
        self._connectors = []
        self._awaiting_input = False
        self.query_one(ChatPanel).clear()
        self.query_one(SpecCard).clear()
        self.query_one(ConfidenceBar).set_confidence(0)
        asyncio.create_task(self._start_interview())
