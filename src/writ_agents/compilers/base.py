"""Compiler protocol definition."""

from __future__ import annotations

from typing import Protocol

from writ_agents.core.schema import ResolvedConnector, Spec


class Compiler(Protocol):
    """Protocol all compilers must implement."""

    format_name: str
    file_extension: str

    def compile(self, spec: Spec, connectors: list[ResolvedConnector]) -> str:
        """Compile a Spec to string output."""
        ...
