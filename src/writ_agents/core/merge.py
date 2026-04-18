"""Merge logic for PartialSpec accumulation during the interview."""

from __future__ import annotations

from writ_agents.core.schema import PartialSpec


def merge_partial(base: PartialSpec, update: PartialSpec) -> PartialSpec:
    """
    Merge update into base. Rules:
    - Non-null update fields overwrite base
    - Null update fields preserve base values
    - List fields use replacement semantics (not append)
    """
    base_data = base.model_dump()
    update_data = update.model_dump()
    merged = {
        key: update_data[key] if update_data[key] is not None else base_data[key]
        for key in base_data
    }
    return PartialSpec.model_validate(merged)


def is_spec_complete(partial: PartialSpec) -> tuple[bool, list[str]]:
    """Check if all required fields are set. Returns (complete, missing_fields)."""
    required = [
        "name",
        "archetype",
        "tagline",
        "purpose",
        "audience",
        "knowledge_sources",
        "tools_needed",
        "guardrails",
        "oversight",
        "personality_traits",
        "system_prompt",
        "target_runtime",
    ]
    data = partial.model_dump()
    missing = [f for f in required if data.get(f) is None]
    return len(missing) == 0, missing
