"""Tests for OAS YAML compiler."""

import yaml

from tests.compilers.test_agents_md import CONNECTOR, SPEC
from writ_agents.compilers.oas import OASCompiler


def test_oas_valid_yaml() -> None:
    compiler = OASCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    data = yaml.safe_load(output)
    assert data is not None


def test_oas_api_version() -> None:
    compiler = OASCompiler()
    output = compiler.compile(SPEC, [])
    data = yaml.safe_load(output)
    assert data["apiVersion"] == "openagentspec.dev/v1"


def test_oas_kind() -> None:
    compiler = OASCompiler()
    output = compiler.compile(SPEC, [])
    data = yaml.safe_load(output)
    assert data["kind"] == "Agent"


def test_oas_spec_fields() -> None:
    compiler = OASCompiler()
    output = compiler.compile(SPEC, [])
    data = yaml.safe_load(output)
    assert data["spec"]["archetype"] == "triage"
    assert "systemPrompt" in data["spec"]
    assert "guardrails" in data["spec"]


def test_oas_connectors() -> None:
    compiler = OASCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    data = yaml.safe_load(output)
    assert len(data["spec"]["connectors"]) == 1
    assert data["spec"]["connectors"][0]["id"] == "slack"
