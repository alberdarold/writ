"""Confidence scoring utilities."""

from __future__ import annotations

from writ_agents.core.schema import PartialSpec

FIELD_WEIGHTS: dict[str, int] = {
    "purpose": 15,
    "audience": 10,
    "tools_needed": 15,
    "knowledge_sources": 10,
    "guardrails": 10,
    "oversight": 10,
    "personality_traits": 5,
    "name": 5,
    "tagline": 5,
    "archetype": 5,
    "system_prompt": 10,
}


def compute_confidence(partial: PartialSpec) -> int:
    """Compute a 0-100 confidence score based on which fields are populated."""
    data = partial.model_dump()
    score = 0
    for field, weight in FIELD_WEIGHTS.items():
        val = data.get(field)
        if val is not None:
            if isinstance(val, list) and len(val) == 0:
                continue
            score += weight
    return min(score, 100)
