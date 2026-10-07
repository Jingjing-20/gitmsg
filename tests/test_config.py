from __future__ import annotations

from pathlib import Path

import pytest

from gitmsg.config import init_config, load_config, parse_config_toml
from gitmsg.exceptions import ConfigError


def test_default_config_when_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    assert config.max_message_length == 72
    assert config.copy_to_clipboard is True
    assert config.default_scope == ""


def test_parse_config_toml() -> None:
    config = parse_config_toml(
        """
[gitmsg]
max_message_length = 50
copy_to_clipboard = false
default_scope = "api"
"""
    )
    assert config.max_message_length == 50
    assert config.copy_to_clipboard is False
    assert config.default_scope == "api"


def test_malformed_config() -> None:
    with pytest.raises(ConfigError):
        parse_config_toml("this is not toml =")


def test_init_config_writes_files(tmp_path: Path) -> None:
    path = init_config(tmp_path)
    assert path.exists()
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".gitmsg/" in gitignore
    loaded = load_config(tmp_path)
    assert loaded.max_message_length == 72
