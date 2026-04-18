"""Tests for Gemini compiler."""

import json

from tests.compilers.test_agents_md import SPEC
from writ_agents.compilers.gemini import GeminiCompiler


def test_gemini_valid_json() -> None:
    compiler = GeminiCompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    assert "model" in data
    assert "systemInstruction" in data


def test_gemini_model() -> None:
    compiler = GeminiCompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    assert data["model"] == "gemini-2.5-pro"


def test_gemini_system_instruction() -> None:
    compiler = GeminiCompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    parts = data["systemInstruction"]["parts"]
    assert len(parts) >= 1
    assert "text" in parts[0]


def test_gemini_function_declarations() -> None:
    compiler = GeminiCompiler()
    output = compiler.compile(SPEC, [])
    data = json.loads(output)
    fns = data["tools"][0]["functionDeclarations"]
    assert len(fns) == 2
