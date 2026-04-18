"""Connector list widget for the reveal screen."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Static

from writ_agents.core.schema import ResolvedConnector


class ConnectorList(Widget):
    """Displays a list of resolved connectors."""

    def __init__(self, connectors: list[ResolvedConnector], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._connectors = connectors

    def compose(self) -> ComposeResult:
        with Vertical():
            if not self._connectors:
                yield Static("No external connections required.")
                return
            for c in self._connectors:
                badge = c.source.upper()
                yield Static(
                    f"{c.icon} **{c.name}** [{badge}]  \u2014 {c.description}",
                    markup=True,
                )
