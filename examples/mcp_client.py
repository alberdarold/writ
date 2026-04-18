"""Agent-to-agent example: script a complete spec build via Writ's MCP tools.

This shows what another agent would do if it connected to `writ mcp-serve`.
It skips the MCP wire protocol and drives the server's tool functions
directly — the actual calls an MCP client would make look identical.
"""

from __future__ import annotations

import asyncio
import os

from writ_agents.mcp.server import build_server
from writ_agents.providers.anthropic import AnthropicProvider


async def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY to run this example.")
        return

    mcp, _store = build_server(provider_factory=lambda: AnthropicProvider())
    tools = {t.name: t.fn for t in mcp._tool_manager._tools.values()}  # type: ignore[attr-defined]

    # Option A: one-shot — agent-to-agent shortcut
    print(">>> writ_one_shot: full description in a single call\n")
    r = await tools["writ_one_shot"](
        description=(
            "A Slack triage assistant for our support team. It reads the "
            "#support channel, classifies each message as billing/technical/"
            "general and urgency as low/medium/high. For high urgency it "
            "pages the on-call via PagerDuty. It never closes a ticket "
            "without a human review. Audience is our 6-person support team."
        )
    )
    if "spec" not in r:
        print("Failed:", r)
        return
    spec = r["spec"]
    print(f"Got spec: {spec['name']} — confidence {r['confidence']}\n")

    # Option B: resolve connectors, then compile all formats
    print(">>> writ_resolve_connectors\n")
    resolved = await tools["writ_resolve_connectors"](spec=spec)
    for c in resolved["connectors"]:
        print(f"  {c['icon']} {c['name']}  <- {', '.join(c['business_terms'])}")

    print("\n>>> writ_compile_all\n")
    compiled = await tools["writ_compile_all"](
        spec=spec, connectors=resolved["connectors"]
    )
    for fmt, out in compiled["formats"].items():
        print(f"--- {fmt}{out['extension']} ({len(out['content'])} chars) ---")

    print("\n>>> Multi-turn interview alternative\n")
    r = await tools["writ_interview_start"](
        initial_description="I need a helper for customer returns"
    )
    sid = r["session_id"]
    print(f"Agent: {r['message']}  (session {sid})")

    # Simulated agent-side answers
    answers = [
        "Our ops team handles returns — about 8 people",
        "It should look up the order in Shopify and draft an email response",
        "Never issue refunds over $500 without manager approval",
    ]
    for a in answers:
        r = await tools["writ_interview_answer"](session_id=sid, answer=a)
        print(f"\nUser: {a}\nAgent: {r['message']}  [{r['confidence']}%]")
        if r["status"] == "ready":
            print(f"\nReady! Got spec: {r['spec']['name']}")
            break


if __name__ == "__main__":
    asyncio.run(main())
