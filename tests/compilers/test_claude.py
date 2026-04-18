"""Tests for Claude compiler."""

import json

from tests.compilers.test_agents_md import CONNECTOR, SPEC
from writ_agents.compilers.claude import ClaudeCompiler


def test_claude_valid_json() -> None:
    compiler = ClaudeCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    data = json.loads(output)
    assert "model" in data
    assert "system" in data


def test_claude_model_field() -> None:
    compiler = ClaudeCompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    assert data["model"] == "claude-opus-4-7"


def test_claude_mcp_servers() -> None:
    compiler = ClaudeCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    data = json.loads(output)
    assert len(data["mcp_servers"]) == 1
    assert data["mcp_servers"][0]["type"] == "url"


def test_claude_metadata() -> None:
    compiler = ClaudeCompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    assert data["metadata"]["archetype"] == "triage"
    assert "guardrails" in data["metadata"]
