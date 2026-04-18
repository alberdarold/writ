"""Tests for confidence scoring."""

from __future__ import annotations

from writ_agents.core.confidence import compute_confidence
from writ_agents.core.merge import is_spec_complete
from writ_agents.core.schema import PartialSpec


def test_empty_partial_scores_zero() -> None:
    assert compute_confidence(PartialSpec()) == 0


def test_confidence_caps_at_100() -> None:
    partial = PartialSpec(
        name="X",
        archetype="Q&A",
        tagline="I help.",
        purpose="answer",
        audience="users",
        knowledge_sources=["faq"],
        tools_needed=["search"],
        guardrails=["never lie"],
        oversight="autonomous",
        personality_traits=["friendly"],
        system_prompt="You are...",
        target_runtime="all",
    )
    assert compute_confidence(partial) == 100


def test_empty_list_does_not_count() -> None:
    partial = PartialSpec(name="X", purpose="y", guardrails=[], tools_needed=[])
    # Only name(5) + purpose(15) = 20
    assert compute_confidence(partial) == 20


def test_empty_list_also_counted_incomplete() -> None:
    """Critical alignment with compute_confidence: empty lists = missing."""
    data = {
        "name": "X",
        "archetype": "Q&A",
        "tagline": "I help.",
        "purpose": "y",
        "audience": "u",
        "knowledge_sources": ["faq"],
        "tools_needed": [],  # empty
        "guardrails": ["never"],
        "oversight": "autonomous",
        "personality_traits": ["kind"],
        "system_prompt": "...",
        "target_runtime": "all",
    }
    partial = PartialSpec(**data)  # type: ignore[arg-type]
    complete, missing = is_spec_complete(partial)
    assert complete is False
    assert "tools_needed" in missing
