"""Tests for PartialSpec merge logic."""

from writ_agents.core.merge import is_spec_complete, merge_partial
from writ_agents.core.schema import PartialSpec


def test_merge_non_null_overwrites() -> None:
    base = PartialSpec(name="Old Name", purpose="old purpose")
    update = PartialSpec(name="New Name")
    result = merge_partial(base, update)
    assert result.name == "New Name"
    assert result.purpose == "old purpose"


def test_merge_null_preserves() -> None:
    base = PartialSpec(name="Keeper", purpose="keep this")
    update = PartialSpec(name=None, purpose=None)
    result = merge_partial(base, update)
    assert result.name == "Keeper"
    assert result.purpose == "keep this"


def test_merge_list_replacement() -> None:
    base = PartialSpec(knowledge_sources=["old source"])
    update = PartialSpec(knowledge_sources=["new source 1", "new source 2"])
    result = merge_partial(base, update)
    assert result.knowledge_sources == ["new source 1", "new source 2"]


def test_merge_empty_partial() -> None:
    base = PartialSpec(name="Base", purpose="base purpose")
    update = PartialSpec()
    result = merge_partial(base, update)
    assert result.name == "Base"


def test_is_spec_complete_true() -> None:
    data = {
        "name": "Test Agent",
        "archetype": "triage",
        "tagline": "I help you...",
        "purpose": "Route emails",
        "audience": "Support team",
        "knowledge_sources": ["email inbox"],
        "tools_needed": ["send message"],
        "guardrails": ["never delete"],
        "oversight": "human_in_loop",
        "personality_traits": ["friendly"],
        "system_prompt": "You are...",
        "target_runtime": "all",
    }
    partial = PartialSpec(**data)
    complete, missing = is_spec_complete(partial)
    assert complete is True
    assert missing == []


def test_is_spec_complete_false() -> None:
    partial = PartialSpec(name="Test", purpose="Route emails")
    complete, missing = is_spec_complete(partial)
    assert complete is False
    assert "tagline" in missing
    assert "audience" in missing
