"""Tests for the MCP server surface — exercises tools without a real MCP client."""

from __future__ import annotations

import json

import pytest

from tests.conftest import MockProvider
from tests.core.test_step import COMPLETE_PARTIAL, _make_response
from writ_agents.mcp.server import build_server


def _provider_factory(responses: list[str]):
    provider = MockProvider(responses)

    def factory() -> MockProvider:
        return provider

    return factory


def _call_tool(mcp, name: str):
    """Pull the underlying callable out of a FastMCP tool."""
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None, f"tool {name} not found"
    return tool.fn


@pytest.mark.asyncio
async def test_interview_start_creates_session() -> None:
    factory = _provider_factory([_make_response(message="What's up?")])
    mcp, store = build_server(provider_factory=factory)

    start = _call_tool(mcp, "writ_interview_start")
    result = await start()
    assert result["status"] == "in_progress"
    assert "What's up?" in result["message"]
    assert result["session_id"] in store.list_ids()


@pytest.mark.asyncio
async def test_interview_answer_advances_session() -> None:
    factory = _provider_factory(
        [
            _make_response(message="Opening"),
            _make_response(
                message="Done!",
                status="ready",
                confidence=95,
                partial_spec=COMPLETE_PARTIAL,
            ),
        ]
    )
    mcp, store = build_server(provider_factory=factory)

    start = _call_tool(mcp, "writ_interview_start")
    answer = _call_tool(mcp, "writ_interview_answer")

    r1 = await start()
    r2 = await answer(session_id=r1["session_id"], answer="route support tickets")
    assert r2["status"] == "ready"
    assert "spec" in r2
    assert r2["spec"]["name"] == "Support Bot"


@pytest.mark.asyncio
async def test_one_shot_returns_spec() -> None:
    factory = _provider_factory(
        [
            _make_response(
                message="Here you go",
                status="ready",
                confidence=95,
                partial_spec=COMPLETE_PARTIAL,
            )
        ]
    )
    mcp, _ = build_server(provider_factory=factory)
    one_shot = _call_tool(mcp, "writ_one_shot")

    r = await one_shot(description="A support triage bot for our team")
    assert "spec" in r
    assert r["spec"]["name"] == "Support Bot"


@pytest.mark.asyncio
async def test_compile_tool_returns_content() -> None:
    mcp, _ = build_server(provider_factory=_provider_factory([]))
    compile_tool = _call_tool(mcp, "writ_compile")

    spec = {**COMPLETE_PARTIAL, "schema_version": "0.1.0"}
    r = await compile_tool(spec=spec, format="agents-md")
    assert r["format"] == "agents-md"
    assert "Support Bot" in r["content"]
    assert r["extension"] == ".md"


@pytest.mark.asyncio
async def test_compile_all_tool() -> None:
    mcp, _ = build_server(provider_factory=_provider_factory([]))
    compile_all = _call_tool(mcp, "writ_compile_all")

    spec = {**COMPLETE_PARTIAL, "schema_version": "0.1.0"}
    r = await compile_all(spec=spec)
    assert set(r["formats"].keys()) == {
        "agents-md",
        "claude",
        "openai",
        "gemini",
        "oas",
    }
    assert "Support Bot" in r["formats"]["agents-md"]["content"]


def test_list_connectors_tool() -> None:
    mcp, _ = build_server(provider_factory=_provider_factory([]))
    list_tool = _call_tool(mcp, "writ_list_connectors")
    r = list_tool()
    assert len(r["catalog"]) >= 10
    assert any(c["id"] == "slack" for c in r["catalog"])


def test_list_compilers_tool() -> None:
    mcp, _ = build_server(provider_factory=_provider_factory([]))
    list_tool = _call_tool(mcp, "writ_list_compilers")
    r = list_tool()
    names = {f["name"] for f in r["formats"]}
    assert "agents-md" in names
    assert "oas" in names


@pytest.mark.asyncio
async def test_session_lifecycle() -> None:
    factory = _provider_factory([_make_response(message="opening")])
    mcp, store = build_server(provider_factory=factory)

    start = _call_tool(mcp, "writ_interview_start")
    get_session = _call_tool(mcp, "writ_get_session")
    end_session = _call_tool(mcp, "writ_end_session")

    r = await start()
    sid = r["session_id"]
    info = get_session(session_id=sid)
    assert info["status"] == "in_progress"
    assert info["turns"] >= 1

    ended = end_session(session_id=sid)
    assert ended["deleted"] is True
    assert get_session(session_id=sid) == {"error": f"No session '{sid}'"}


@pytest.mark.asyncio
async def test_resolve_connectors_tool() -> None:
    # Interview step responses consumed during compile not needed; one resolver call:
    resolver_response = json.dumps(
        [
            {
                "business_term": "support tickets",
                "connector_id": "zendesk",
                "confidence": 90,
            },
            {
                "business_term": "send Slack message",
                "connector_id": "slack",
                "confidence": 95,
            },
        ]
    )
    factory = _provider_factory([resolver_response])
    mcp, _ = build_server(provider_factory=factory)

    resolve = _call_tool(mcp, "writ_resolve_connectors")
    spec = {**COMPLETE_PARTIAL, "schema_version": "0.1.0"}
    r = await resolve(spec=spec)
    ids = {c["connector_id"] for c in r["connectors"]}
    assert "slack" in ids
    assert "zendesk" in ids
