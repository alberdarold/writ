"""End-to-end MCP stdio integration test.

Spawns `python -m writ_agents.cli mcp-serve` as a real subprocess and drives
it with the MCP client SDK over stdio. Unlike `test_mcp_server.py` (which
pulls tool callables out of FastMCP directly), this exercises the actual
wire protocol — list_tools, call_tool, list_resources, read_resource — the
way Claude Desktop or another MCP client would.

Only non-LLM tools are called, so no ANTHROPIC_API_KEY is required.
"""

from __future__ import annotations

import json
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from tests.core.test_step import COMPLETE_PARTIAL

_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "writ_agents.cli", "mcp-serve", "--transport", "stdio"],
)


def _text_of(result: object) -> str:
    """Flatten MCP TextContent blocks into a single string."""
    parts: list[str] = []
    contents = getattr(result, "content", None) or []
    for c in contents:
        t = getattr(c, "text", None)
        if isinstance(t, str):
            parts.append(t)
    return "\n".join(parts)


@pytest.mark.asyncio
async def test_mcp_stdio_lists_expected_tools() -> None:
    async with (
        stdio_client(_SERVER_PARAMS) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        listing = await session.list_tools()
        names = {t.name for t in listing.tools}
    expected = {
        "writ_interview_start",
        "writ_interview_answer",
        "writ_one_shot",
        "writ_compile",
        "writ_compile_all",
        "writ_resolve_connectors",
        "writ_list_connectors",
        "writ_list_compilers",
        "writ_get_session",
        "writ_end_session",
    }
    missing = expected - names
    assert not missing, f"Missing tools over the wire: {missing}"


@pytest.mark.asyncio
async def test_mcp_stdio_list_connectors_and_compilers() -> None:
    async with (
        stdio_client(_SERVER_PARAMS) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        connectors_result = await session.call_tool("writ_list_connectors", {})
        compilers_result = await session.call_tool("writ_list_compilers", {})

    connectors_payload = json.loads(_text_of(connectors_result))
    assert len(connectors_payload["catalog"]) >= 10
    assert any(c["id"] == "slack" for c in connectors_payload["catalog"])

    compilers_payload = json.loads(_text_of(compilers_result))
    names = {f["name"] for f in compilers_payload["formats"]}
    assert names == {"agents-md", "claude", "openai", "gemini", "oas"}


@pytest.mark.asyncio
async def test_mcp_stdio_compile_round_trip() -> None:
    spec = {**COMPLETE_PARTIAL, "schema_version": "0.1.0"}
    async with (
        stdio_client(_SERVER_PARAMS) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool(
            "writ_compile", {"spec": spec, "format": "agents-md"}
        )
    payload = json.loads(_text_of(result))
    assert payload["format"] == "agents-md"
    assert payload["extension"] == ".md"
    assert "Support Bot" in payload["content"]


@pytest.mark.asyncio
async def test_mcp_stdio_compile_all_returns_five_formats() -> None:
    spec = {**COMPLETE_PARTIAL, "schema_version": "0.1.0"}
    async with (
        stdio_client(_SERVER_PARAMS) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool("writ_compile_all", {"spec": spec})
    payload = json.loads(_text_of(result))
    assert set(payload["formats"].keys()) == {
        "agents-md",
        "claude",
        "openai",
        "gemini",
        "oas",
    }


@pytest.mark.asyncio
async def test_mcp_stdio_resources() -> None:
    async with (
        stdio_client(_SERVER_PARAMS) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        listing = await session.list_resources()
        uris = {str(r.uri) for r in listing.resources}
        assert "writ://catalog" in uris
        assert "writ://schema" in uris

        catalog_resp = await session.read_resource("writ://catalog")  # type: ignore[arg-type]
        catalog_text = "\n".join(
            getattr(c, "text", "") or "" for c in catalog_resp.contents
        )
        catalog = json.loads(catalog_text)
        assert isinstance(catalog, list) and len(catalog) >= 10

        schema_resp = await session.read_resource("writ://schema")  # type: ignore[arg-type]
        schema_text = "\n".join(
            getattr(c, "text", "") or "" for c in schema_resp.contents
        )
        schema = json.loads(schema_text)
        assert "Spec" in schema and "PartialSpec" in schema
