"""Tests for the connector resolver."""

from __future__ import annotations

import json

import pytest

from tests.compilers.test_agents_md import SPEC
from tests.conftest import MockProvider
from writ_agents.resolver.resolver import resolve_connectors


def _make_resolver_response(matches: list[dict[str, object]]) -> str:
    return json.dumps(matches)


@pytest.mark.asyncio
async def test_resolver_returns_connectors() -> None:
    matches: list[dict[str, object]] = [
        {
            "business_term": "support ticket history",
            "connector_id": "zendesk",
            "confidence": 90,
        },
        {
            "business_term": "product documentation",
            "connector_id": "notion",
            "confidence": 80,
        },
        {
            "business_term": "send Slack message",
            "connector_id": "slack",
            "confidence": 95,
        },
        {
            "business_term": "update ticket status",
            "connector_id": "zendesk",
            "confidence": 88,
        },
    ]
    provider = MockProvider([_make_resolver_response(matches)])
    connectors = await resolve_connectors(SPEC, provider)
    connector_ids = {c.connector_id for c in connectors}
    assert "slack" in connector_ids
    assert "zendesk" in connector_ids


@pytest.mark.asyncio
async def test_resolver_repairs_invalid_json() -> None:
    valid = _make_resolver_response(
        [
            {
                "business_term": "send Slack message",
                "connector_id": "slack",
                "confidence": 95,
            }
        ]
    )
    provider = MockProvider(["this is not json at all", valid])
    connectors = await resolve_connectors(SPEC, provider)
    assert any(c.connector_id == "slack" for c in connectors)


@pytest.mark.asyncio
async def test_resolver_returns_empty_on_double_failure() -> None:
    provider = MockProvider(["garbage one", "garbage two"])
    connectors = await resolve_connectors(SPEC, provider)
    assert connectors == []


@pytest.mark.asyncio
async def test_resolver_deduplicates() -> None:
    # Two terms map to the same connector
    matches: list[dict[str, object]] = [
        {
            "business_term": "support ticket history",
            "connector_id": "zendesk",
            "confidence": 90,
        },
        {
            "business_term": "update ticket status",
            "connector_id": "zendesk",
            "confidence": 88,
        },
        {
            "business_term": "send Slack message",
            "connector_id": "slack",
            "confidence": 95,
        },
        {
            "business_term": "product documentation",
            "connector_id": "notion",
            "confidence": 80,
        },
    ]
    provider = MockProvider([_make_resolver_response(matches)])
    connectors = await resolve_connectors(SPEC, provider)
    zendesk_entries = [c for c in connectors if c.connector_id == "zendesk"]
    assert len(zendesk_entries) == 1
    assert len(zendesk_entries[0].business_terms) == 2
