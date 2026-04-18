"""Spec card widget showing the evolving agent spec."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from writ_agents.core.schema import PartialSpec


class SpecCard(Widget):
    """Right-side panel showing the evolving spec."""

    DEFAULT_CSS = """
    SpecCard {
        border: solid $surface;
        padding: 1 2;
        height: 100%;
    }
    .spec-empty {
        text-align: center;
        color: $text-muted;
        padding: 4 2;
    }
    .spec-name {
        text-style: bold;
        color: $text;
    }
    .spec-archetype {
        color: $accent;
        text-style: italic;
    }
    .spec-tagline {
        color: $text-muted;
        padding: 0 0 1 0;
    }
    .spec-section-title {
        color: $accent;
        text-style: bold;
        padding: 1 0 0 0;
    }
    .spec-chip {
        border: solid $surface;
        padding: 0 1;
        margin: 0 1 0 0;
    }
    .chip-danger {
        border: solid $error;
        color: $error;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="spec-scroll"):
            yield Static(
                "\U0001f916\n\nYour agent will appear here\nas you answer questions",
                classes="spec-empty",
                id="spec-empty",
            )

    def update_spec(self, partial: PartialSpec) -> None:
        """Re-render the spec card from a partial spec."""
        scroll = self.query_one("#spec-scroll", VerticalScroll)
        for w in scroll.query("*"):
            w.remove()

        data = partial.model_dump()
        has_any = any(v is not None for v in data.values())
        if not has_any:
            scroll.mount(
                Static(
                    "\U0001f916\n\nYour agent will appear here\nas you answer questions",
                    classes="spec-empty",
                )
            )
            return

        if data.get("archetype"):
            scroll.mount(
                Static(f"\u25c6 {data['archetype'].upper()}", classes="spec-archetype")
            )
        if data.get("name"):
            scroll.mount(Static(str(data["name"]), classes="spec-name"))
        if data.get("tagline"):
            scroll.mount(Static(str(data["tagline"]), classes="spec-tagline"))

        if data.get("personality_traits"):
            scroll.mount(Static("\U0001f464 PERSONALITY", classes="spec-section-title"))
            chips = "  ".join(f"[{t}]" for t in data["personality_traits"])
            scroll.mount(Static(chips))

        if data.get("knowledge_sources"):
            scroll.mount(Static("\U0001f4da KNOWS ABOUT", classes="spec-section-title"))
            for ks in data["knowledge_sources"]:
                scroll.mount(Static(f"\u25e6 {ks}"))

        if data.get("tools_needed"):
            scroll.mount(Static("\u26a1 CAN DO", classes="spec-section-title"))
            for t in data["tools_needed"]:
                scroll.mount(Static(f"\u25e6 {t}"))

        if data.get("guardrails"):
            scroll.mount(Static("\U0001f6ab WILL NEVER", classes="spec-section-title"))
            for g in data["guardrails"]:
                scroll.mount(Static(f"\u26d4 {g}", classes="chip-danger"))

        if data.get("oversight"):
            label = str(data["oversight"]).replace("_", " ").title()
            scroll.mount(Static("\u2705 OVERSIGHT", classes="spec-section-title"))
            scroll.mount(Static(f"[{label}]"))

    def clear(self) -> None:
        """Reset to empty state."""
        scroll = self.query_one("#spec-scroll", VerticalScroll)
        for w in scroll.query("*"):
            w.remove()
        scroll.mount(
            Static(
                "\U0001f916\n\nYour agent will appear here\nas you answer questions",
                classes="spec-empty",
            )
        )
