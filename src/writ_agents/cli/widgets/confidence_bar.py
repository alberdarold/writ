"""Confidence bar widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class ConfidenceBar(Widget):
    """Shows interview confidence as a progress bar."""

    confidence: reactive[int] = reactive(0)

    DEFAULT_CSS = """
    ConfidenceBar {
        height: 1;
        dock: right;
        width: 20;
    }
    """

    def set_confidence(self, value: int) -> None:
        """Update the confidence value."""
        self.confidence = max(0, min(100, value))

    def compose(self) -> ComposeResult:
        yield Label(f"{self.confidence}%", id="conf-label")
