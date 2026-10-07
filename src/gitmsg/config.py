"""Optional project configuration for GitMsg."""

from __future__ import annotations

import tomllib
from pathlib import Path

from gitmsg.exceptions import ConfigError
from gitmsg.models import GitMsgConfig

CONFIG_DIR_NAME = ".gitmsg"
CONFIG_FILE_NAME = "config.toml"

DEFAULT_CONFIG_TOML = """\
[gitmsg]
max_message_length = 72
copy_to_clipboard = true
default_scope = ""
"""


def config_path(repo_root: Path) -> Path:
    return repo_root / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def default_config() -> GitMsgConfig:
    return GitMsgConfig()


def _as_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"Invalid {field}: expected an integer.")
    return value


def _as_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"Invalid {field}: expected true or false.")
    return value


def _as_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"Invalid {field}: expected a string.")
    return value


def parse_config_toml(text: str) -> GitMsgConfig:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Malformed GitMsg configuration.\n{exc}") from exc

    section = data.get("gitmsg", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ConfigError("Invalid [gitmsg] table in configuration.")

    config = GitMsgConfig()
    max_length = section.get("max_message_length", config.max_message_length)
    copy_to_clipboard = section.get("copy_to_clipboard", config.copy_to_clipboard)
    default_scope = section.get("default_scope", config.default_scope)
    return GitMsgConfig(
        max_message_length=_as_int(max_length, "max_message_length"),
        copy_to_clipboard=_as_bool(copy_to_clipboard, "copy_to_clipboard"),
        default_scope=_as_str(default_scope, "default_scope"),
    )


def load_config(repo_root: Path) -> GitMsgConfig:
    path = config_path(repo_root)
    if not path.exists():
        return default_config()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Could not read {path}: {exc}") from exc
    return parse_config_toml(text)


def ensure_gitignore_entry(repo_root: Path) -> None:
    gitignore = repo_root / ".gitignore"
    marker = ".gitmsg/"
    if gitignore.exists():
        current = gitignore.read_text(encoding="utf-8")
        if marker in current.splitlines() or any(
            line.strip() == marker for line in current.splitlines()
        ):
            return
        prefix = "" if current.endswith("\n") or current == "" else "\n"
        gitignore.write_text(current + prefix + marker + "\n", encoding="utf-8")
        return
    gitignore.write_text(marker + "\n", encoding="utf-8")


def init_config(repo_root: Path) -> Path:
    directory = repo_root / CONFIG_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    path = config_path(repo_root)
    if not path.exists():
        path.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
    ensure_gitignore_entry(repo_root)
    return path
