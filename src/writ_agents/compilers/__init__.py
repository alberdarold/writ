"""Compiler registry — single source of truth for all built-in compilers."""

from __future__ import annotations

from writ_agents.compilers.agents_md import AgentsMdCompiler
from writ_agents.compilers.base import Compiler
from writ_agents.compilers.claude import ClaudeCompiler
from writ_agents.compilers.gemini import GeminiCompiler
from writ_agents.compilers.oas import OASCompiler
from writ_agents.compilers.openai import OpenAICompiler

COMPILERS: dict[str, Compiler] = {
    "agents-md": AgentsMdCompiler(),
    "claude": ClaudeCompiler(),
    "openai": OpenAICompiler(),
    "gemini": GeminiCompiler(),
    "oas": OASCompiler(),
}


def format_choices() -> list[str]:
    return list(COMPILERS.keys())


__all__ = [
    "AgentsMdCompiler",
    "COMPILERS",
    "ClaudeCompiler",
    "Compiler",
    "GeminiCompiler",
    "OASCompiler",
    "OpenAICompiler",
    "format_choices",
]
