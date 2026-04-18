"""Basic usage example for writ-agents.

Drives the interview through the low-level `interview_step` primitive — the
same API the TUI and MCP server use. This avoids the generator-asend pattern,
which must not be mixed with `async for`.
"""

from __future__ import annotations

import asyncio
import os

from writ_agents.compilers.agents_md import AgentsMdCompiler
from writ_agents.compilers.claude import ClaudeCompiler
from writ_agents.core.session import InterviewSession
from writ_agents.core.step import interview_step


async def main() -> None:
    from writ_agents.providers.anthropic import AnthropicProvider

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY to run this example.")
        return

    provider = AnthropicProvider(api_key=api_key)
    session = InterviewSession()

    answers = iter(
        [
            "I want something to handle our customer support emails and route them to the right team.",
            "Our support managers — about 5 people.",
            "It should read emails, look up the customer's history in our helpdesk, and Slack the right team lead.",
            "Never close a ticket without a human signing off. Never reply directly to customers.",
            "Friendly but concise. Professional.",
            "Let's call it Support Router.",
        ]
    )

    # Kick off with the opening question.
    result = await interview_step(session, provider)
    print(f"\nAgent: {result.message}\n[Confidence: {result.confidence}%]")

    while result.status == "in_progress":
        try:
            user_reply = next(answers)
        except StopIteration:
            print("\n(No more scripted answers — stopping.)")
            return
        print(f"\nUser: {user_reply}")
        result = await interview_step(session, provider, user_input=user_reply)
        print(f"\nAgent: {result.message}\n[Confidence: {result.confidence}%]")

    if result.status == "error":
        print(f"\nError: {result.error}")
        return

    assert result.spec is not None
    spec = result.spec
    print("\n=== Interview Complete! ===\n")
    print(f"Name: {spec.name}")
    print(f"Tagline: {spec.tagline}")
    print("\n--- AGENTS.md output ---\n")
    print(AgentsMdCompiler().compile(spec, []))
    print("\n--- Claude JSON output ---\n")
    print(ClaudeCompiler().compile(spec, []))


if __name__ == "__main__":
    asyncio.run(main())
