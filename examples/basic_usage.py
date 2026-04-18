"""Basic usage example for writ-agents."""

from __future__ import annotations

import asyncio
import os

from writ_agents.compilers.agents_md import AgentsMdCompiler
from writ_agents.compilers.claude import ClaudeCompiler
from writ_agents.core.schema import (
    AgentMessageEvent,
    AwaitingInputEvent,
    InterviewCompleteEvent,
    InterviewErrorEvent,
    SpecUpdateEvent,
)


async def main() -> None:
    """Run a simple non-interactive demo interview."""
    from writ_agents.core.interview import run_interview
    from writ_agents.providers.anthropic import AnthropicProvider

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY to run this example.")
        return

    provider = AnthropicProvider(api_key=api_key)

    # Scripted answers for a quick demo
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

    gen = run_interview(provider)

    async for event in gen:
        if isinstance(event, AgentMessageEvent):
            print(f"\nAgent: {event.message}\n")
        elif isinstance(event, AwaitingInputEvent):
            try:
                user_reply = next(answers)
                print(f"User: {user_reply}")
                await gen.asend(user_reply)
            except StopIteration:
                print("(No more scripted answers — stopping)")
                break
        elif isinstance(event, SpecUpdateEvent):
            print(f"[Confidence: {event.confidence}%]")
        elif isinstance(event, InterviewCompleteEvent):
            print("\n=== Interview Complete! ===\n")
            spec = event.spec
            print(f"Name: {spec.name}")
            print(f"Tagline: {spec.tagline}")
            print("\n--- AGENTS.md output ---\n")
            compiler = AgentsMdCompiler()
            print(compiler.compile(spec, []))
            print("\n--- Claude JSON output ---\n")
            claude = ClaudeCompiler()
            print(claude.compile(spec, []))
        elif isinstance(event, InterviewErrorEvent):
            print(f"Error: {event.message}")
            break


if __name__ == "__main__":
    asyncio.run(main())
