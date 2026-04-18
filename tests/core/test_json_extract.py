"""Tests for balanced-brace JSON extraction."""

from __future__ import annotations

from writ_agents.core.json_extract import extract_json_arrays, extract_json_objects


def test_extracts_single_object() -> None:
    assert extract_json_objects('{"a": 1}') == ['{"a": 1}']


def test_extracts_two_separate_objects() -> None:
    # The old greedy regex would merge these into one span.
    raw = '{"a": 1}  noise  {"b": 2}'
    assert extract_json_objects(raw) == ['{"a": 1}', '{"b": 2}']


def test_ignores_braces_inside_strings() -> None:
    raw = '{"msg": "has a } in it", "ok": true}'
    assert extract_json_objects(raw) == [raw]


def test_handles_nested_objects() -> None:
    raw = '{"outer": {"inner": 1}} trailing'
    assert extract_json_objects(raw) == ['{"outer": {"inner": 1}}']


def test_respects_escaped_quotes() -> None:
    raw = r'{"msg": "she said \"hi\" } ", "n": 1}'
    assert extract_json_objects(raw) == [raw]


def test_extract_arrays() -> None:
    raw = '[{"a":1}, {"b":2}]'
    assert extract_json_arrays(raw) == [raw]


def test_no_match_returns_empty() -> None:
    assert extract_json_objects("nothing here") == []
    assert extract_json_arrays("still nothing") == []
