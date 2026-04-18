"""Connector resolver: maps business terms from a Spec to catalog entries."""

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from writ_agents.core.json_extract import extract_json_arrays
from writ_agents.core.schema import ResolvedConnector, Spec
from writ_agents.providers.base import LLMProvider
from writ_agents.resolver.catalog import CATALOG, find_by_id
from writ_agents.resolver.prompt import RESOLVER_SYSTEM_PROMPT

_REPAIR_PROMPT = (
    "Your previous reply was not valid JSON. Return ONLY a JSON array of "
    '{"business_term", "connector_id", "confidence"} objects. No prose, no fences.'
)


class _MatchItem(BaseModel):
    business_term: str
    connector_id: str
    confidence: int


def _parse_matches(raw: str) -> list[_MatchItem] | None:
    """Try each balanced JSON array in `raw`; return the first that validates."""
    if not raw:
        return None
    for candidate in extract_json_arrays(raw):
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, list):
            continue
        try:
            return [_MatchItem.model_validate(m) for m in data]
        except ValidationError:
            continue
    return None


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

    conversation: list[dict[str, str]] = [{"role": "user", "content": user_message}]
    raw = await provider.call(conversation, RESOLVER_SYSTEM_PROMPT)
    matches = _parse_matches(raw)

    if matches is None:
        conversation.append({"role": "assistant", "content": raw})
        conversation.append({"role": "user", "content": _REPAIR_PROMPT})
        raw2 = await provider.call(conversation, RESOLVER_SYSTEM_PROMPT)
        matches = _parse_matches(raw2)

    if matches is None:
        return []

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
