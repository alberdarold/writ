"""CLI configuration management."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

CONFIG_DIR = Path.home() / ".writ"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, object]:
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "rb") as f:
        data: dict[str, object] = tomllib.load(f)
        return data


def save_api_key(key: str) -> None:
    ensure_config_dir()
    config = load_config()
    provider = config.setdefault("provider", {})
    assert isinstance(provider, dict)
    provider["anthropic_api_key"] = key
    _write_config(config)


def _escape_toml_string(v: str) -> str:
    """Escape a value for a TOML basic string (quoted with ")."""
    out: list[str] = []
    for ch in v:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return "".join(out)


def _write_config(config: dict[str, object]) -> None:
    lines: list[str] = []
    for section, values in config.items():
        lines.append(f"[{section}]")
        assert isinstance(values, dict)
        for k, v in values.items():
            lines.append(f'{k} = "{_escape_toml_string(str(v))}"')
        lines.append("")
    CONFIG_FILE.write_text("\n".join(lines))


def get_api_key() -> str | None:
    if key := os.environ.get("ANTHROPIC_API_KEY"):
        return key
    cfg = load_config()
    provider = cfg.get("provider", {})
    assert isinstance(provider, dict)
    val = provider.get("anthropic_api_key")
    return str(val) if val is not None else None
