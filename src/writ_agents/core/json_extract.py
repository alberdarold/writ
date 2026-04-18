"""Balanced JSON substring extraction.

The previous regex-based extractor (`\\{.*\\}` with DOTALL) was greedy and
matched from the first `{` to the last `}` in the input, which breaks when an
LLM emits two JSON blocks (e.g. a fenced example followed by the real reply).
These helpers scan for balanced objects/arrays while respecting string
literals and escape sequences.
"""

from __future__ import annotations


def _extract(raw: str, open_ch: str, close_ch: str) -> list[str]:
    results: list[str] = []
    depth = 0
    start = -1
    in_string = False
    escape = False
    for i, ch in enumerate(raw):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == open_ch:
            if depth == 0:
                start = i
            depth += 1
        elif ch == close_ch and depth > 0:
            depth -= 1
            if depth == 0 and start != -1:
                results.append(raw[start : i + 1])
                start = -1
    return results


def extract_json_objects(raw: str) -> list[str]:
    """Return every balanced `{...}` substring in `raw`, in order."""
    return _extract(raw, "{", "}")


def extract_json_arrays(raw: str) -> list[str]:
    """Return every balanced `[...]` substring in `raw`, in order."""
    return _extract(raw, "[", "]")
