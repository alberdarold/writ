"""Confidence bar widget — shows interview completion as a progress readout."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import ProgressBar, Static

_BUCKETS = [
    (0, "discovering..."),
    (30, "learning the shape"),
    (60, "filling gaps"),
    (85, "nearly ready"),
    (100, "ready to compile"),
]


def _label_for(value: int) -> str:
    label = _BUCKETS[0][1]
    for threshold, text in _BUCKETS:
        if value >= threshold:
            label = text
    return f"{value}% — {label}"


class ConfidenceBar(Widget):
    """Single-row progress readout mounted above the main split."""

    DEFAULT_CSS = """
    ConfidenceBar {
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }
    ConfidenceBar > Static {
        width: 40;
    }
    ConfidenceBar > ProgressBar {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(_label_for(0), id="conf-label")
        yield ProgressBar(total=100, show_eta=False, id="conf-progress")

    def set_confidence(self, value: int) -> None:
        value = max(0, min(100, value))
        try:
            label = self.query_one("#conf-label", Static)
            bar = self.query_one("#conf-progress", ProgressBar)
        except Exception:
            return
        label.update(_label_for(value))
        bar.update(progress=value)
