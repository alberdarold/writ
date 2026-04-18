"""Tests for the TOML config writer — particularly escape safety."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from writ_agents.cli import config as config_mod


@pytest.fixture
def tmp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.toml"
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", target)
    return target


def test_save_api_key_with_quote_and_backslash_round_trips(
    tmp_config: Path,
) -> None:
    tricky = 'sk-ant-"quoted"-and\\-backslashed'
    config_mod.save_api_key(tricky)
    parsed = tomllib.loads(tmp_config.read_text())
    assert parsed["provider"]["anthropic_api_key"] == tricky


def test_save_api_key_with_control_chars_round_trips(tmp_config: Path) -> None:
    key = "line1\nline2\ttabbed"
    config_mod.save_api_key(key)
    parsed = tomllib.loads(tmp_config.read_text())
    assert parsed["provider"]["anthropic_api_key"] == key
