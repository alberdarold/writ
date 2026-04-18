"""Snapshot tests for AgentsMd compiler."""

from writ_agents.compilers.agents_md import AgentsMdCompiler
from writ_agents.core.schema import ResolvedConnector, Spec

SPEC = Spec(
    name="Support Triage Bot",
    archetype="triage",
    tagline="I help you route customer issues to the right team fast.",
    purpose="Automatically classify and route incoming customer support tickets.",
    audience="Support team managers",
    knowledge_sources=["support ticket history", "product documentation"],
    tools_needed=["send Slack message", "update ticket status"],
    guardrails=["Never close a ticket without human review"],
    oversight="human_in_loop",
    personality_traits=["concise", "professional"],
    system_prompt="You are a support triage assistant. Route based on severity.",
    target_runtime="all",
)

CONNECTOR = ResolvedConnector(
    connector_id="slack",
    name="Slack",
    source="mcp",
    icon="\U0001f4ac",
    description="Send and read Slack messages",
    business_terms=["send Slack message"],
    mcp_url="https://mcp.slack.com",
)


def test_agents_md_contains_name() -> None:
    compiler = AgentsMdCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    assert "Support Triage Bot" in output


def test_agents_md_contains_tagline() -> None:
    compiler = AgentsMdCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    assert "route customer issues" in output


def test_agents_md_contains_guardrails() -> None:
    compiler = AgentsMdCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    assert "Never close a ticket" in output


def test_agents_md_contains_connector() -> None:
    compiler = AgentsMdCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    assert "Slack" in output
    assert "MCP" in output


def test_agents_md_contains_system_prompt() -> None:
    compiler = AgentsMdCompiler()
    output = compiler.compile(SPEC, [])
    assert "support triage assistant" in output


def test_agents_md_generator_signature() -> None:
    compiler = AgentsMdCompiler()
    output = compiler.compile(SPEC, [])
    assert "Writ" in output
