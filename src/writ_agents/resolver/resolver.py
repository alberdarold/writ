"""Connector resolver: maps business terms from a Spec to catalog entries."""

from __future__ import annotations

import json

from pydantic import BaseModel

from writ_agents.core.schema import ResolvedConnector, Spec
from writ_agents.providers.base import LLMProvider
from writ_agents.resolver.catalog import CATALOG, find_by_id
from writ_agents.resolver.prompt import RESOLVER_SYSTEM_PROMPT


class _MatchItem(BaseModel):
    business_term: str
    connector_id: str
    confidence: int


async def resolve_connectors(
    spec: Spec, provider: LLMProvider
) -> list[ResolvedConnector]:
    """Resolve business terms in a spec to catalog connector entries."""
    terms = list(spec.knowledge_sources) + list(spec.tools_needed)
    if not terms:
        return []

    catalog_summary = "\n".join(
        f"- {c.id}: {c.name} ({', '.join(c.aliases[:4])})" for c in CATALOG
    )
    user_message = (
        f"Terms to match:\n{json.dumps(terms)}\n\nCatalog:\n{catalog_summary}"
    )

    raw = await provider.call(
        [{"role": "user", "content": user_message}],
        RESOLVER_SYSTEM_PROMPT,
    )

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    matches = [_MatchItem.model_validate(m) for m in json.loads(raw)]

    # Group by connector_id
    grouped: dict[str, list[str]] = {}
    for match in matches:
        grouped.setdefault(match.connector_id, []).append(match.business_term)

    result: list[ResolvedConnector] = []
    for connector_id, business_terms in grouped.items():
        entry = find_by_id(connector_id)
        if entry is None:
            entry = find_by_id("manual")
        if entry is None:
            continue
        result.append(
            ResolvedConnector(
                connector_id=entry.id,
                name=entry.name,
                source=entry.source,  # type: ignore[arg-type]
                icon=entry.icon,
                description=entry.description,
                business_terms=business_terms,
                mcp_url=entry.mcp_url,
            )
        )

    return result
