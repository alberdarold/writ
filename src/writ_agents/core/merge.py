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


REQUIRED_FIELDS: list[str] = [
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


def is_spec_complete(partial: PartialSpec) -> tuple[bool, list[str]]:
    """Check if all required fields are set. Returns (complete, missing_fields).

    Empty lists count as missing — this matches `compute_confidence`, which
    also ignores empty lists. An agent with zero guardrails isn't truly
    complete.
    """
    data = partial.model_dump()
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        val = data.get(field)
        if val is None or (isinstance(val, list) and len(val) == 0):
            missing.append(field)
    return len(missing) == 0, missing
