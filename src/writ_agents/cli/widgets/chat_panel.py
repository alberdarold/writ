"""Chat panel widget showing conversation history."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.markup import escape
from textual.widget import Widget
from textual.widgets import Static


class ChatPanel(Widget):
    """Scrollable chat panel with conversation history."""

    DEFAULT_CSS = """
    ChatPanel {
        border: solid $surface;
        padding: 1 2;
        height: 100%;
    }
    .user-message {
        text-align: right;
        background: $surface;
        padding: 0 1;
        margin: 0 0 1 8;
        border: solid $accent;
    }
    .agent-message {
        text-align: left;
        padding: 0 0 1 0;
        margin: 0 8 1 0;
    }
    .thinking {
        color: $text-muted;
        padding: 0 0 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="messages")

    def add_user_message(self, text: str) -> None:
        """Add a user message bubble."""
        scroll = self.query_one("#messages", VerticalScroll)
        scroll.mount(Static(escape(text), classes="user-message"))
        scroll.scroll_end(animate=False)

    def add_agent_message(self, text: str) -> None:
        """Add an agent message."""
        thinking = self.query(".thinking")
        if thinking:
            thinking.first(Static).remove()
        scroll = self.query_one("#messages", VerticalScroll)
        scroll.mount(Static(text, classes="agent-message", markup=True))
        scroll.scroll_end(animate=False)

    def show_thinking(self, visible: bool) -> None:
        """Show or hide the thinking indicator."""
        existing = self.query(".thinking")
        if visible and not existing:
            scroll = self.query_one("#messages", VerticalScroll)
            scroll.mount(Static("\u25cf \u25cf \u25cf", classes="thinking"))
            scroll.scroll_end(animate=False)
        elif not visible and existing:
            for w in existing:
                w.remove()

    def clear(self) -> None:
        """Clear all messages."""
        scroll = self.query_one("#messages", VerticalScroll)
        for w in scroll.query("*"):
            w.remove()
