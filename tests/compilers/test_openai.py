"""Tests for OpenAI compiler."""

import json

from tests.compilers.test_agents_md import SPEC
from writ_agents.compilers.openai import OpenAICompiler


def test_openai_valid_json() -> None:
    compiler = OpenAICompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    assert "name" in data
    assert "instructions" in data


def test_openai_kebab_name() -> None:
    compiler = OpenAICompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    assert data["name"] == "support-triage-bot"


def test_openai_model() -> None:
    compiler = OpenAICompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    assert data["model"] == "gpt-5"


def test_openai_tools_from_tools_needed() -> None:
    compiler = OpenAICompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    tool_names = [t["function"]["name"] for t in data["tools"]]
    assert len(tool_names) == 2
