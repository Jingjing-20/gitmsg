from __future__ import annotations

from pathlib import Path

import pytest
from tests.conftest import run_git as repo_git
from typer.testing import CliRunner

from gitmsg.config import parse_config_toml
from gitmsg.diff import parse_staged_changes
from gitmsg.exceptions import ConfigError
from gitmsg.models import ChangeStatus

runner = CliRunner()


def _stage_and_invoke(
    git_repo: Path,
    monkeypatch,
    args: list[str] | None = None,
    copy_ok: bool = True,
):
    from gitmsg.cli import app

    monkeypatch.setattr("gitmsg.cli.copy_text", lambda _text: copy_ok)
    monkeypatch.chdir(git_repo)
    return runner.invoke(app, args or ["--dry-run"])


def test_empty_repository_has_no_staged_changes(git_repo: Path, monkeypatch) -> None:
    result = _stage_and_invoke(git_repo, monkeypatch, args=[])
    assert result.exit_code == 0
    assert "No staged changes found" in result.output


def test_large_diff_is_parsed(git_repo: Path) -> None:
    lines = [f"value_{index} = {index}" for index in range(400)]
    (git_repo / "big.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
    repo_git(["add", "big.py"], cwd=git_repo)
    parsed = parse_staged_changes(git_repo)
    assert parsed.stats.files_changed == 1
    assert parsed.stats.insertions >= 400
    assert parsed.files[0].path == "big.py"


def test_utf8_content_and_filename(git_repo: Path, monkeypatch) -> None:
    path = git_repo / "说明.py"
    path.write_text("def 问候():\n    return '你好'\n", encoding="utf-8")
    repo_git(["add", "说明.py"], cwd=git_repo)
    parsed = parse_staged_changes(git_repo)
    assert parsed.files[0].path.endswith("说明.py")
    result = _stage_and_invoke(git_repo, monkeypatch)
    assert result.exit_code == 0
    assert "Suggested commit:" in result.output


def test_binary_and_deleted_files(git_repo: Path) -> None:
    (git_repo / "keep.py").write_text("keep = True\n", encoding="utf-8")
    (git_repo / "gone.py").write_text("gone = True\n", encoding="utf-8")
    repo_git(["add", "keep.py", "gone.py"], cwd=git_repo)
    repo_git(["commit", "-m", "initial"], cwd=git_repo)
    (git_repo / "blob.bin").write_bytes(bytes(range(256)))
    (git_repo / "gone.py").unlink()
    repo_git(["add", "-A"], cwd=git_repo)
    parsed = parse_staged_changes(git_repo)
    by_path = {file.path: file for file in parsed.files}
    assert by_path["blob.bin"].is_binary is True
    assert by_path["gone.py"].status == ChangeStatus.DELETED


def test_mixed_changes_notice(git_repo: Path, monkeypatch) -> None:
    (git_repo / "src").mkdir()
    (git_repo / "src" / "auth.py").write_text(
        "def login():\n    return True\n", encoding="utf-8"
    )
    (git_repo / "README.md").write_text("# Docs\n", encoding="utf-8")
    (git_repo / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
    repo_git(["add", "src/auth.py", "README.md", "package.json"], cwd=git_repo)
    result = _stage_and_invoke(git_repo, monkeypatch)
    assert result.exit_code == 0
    assert "multiple concerns" in result.output


def test_malformed_config_is_reported(git_repo: Path, monkeypatch) -> None:
    config_dir = git_repo / ".gitmsg"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "this is not = valid toml\n", encoding="utf-8"
    )
    (git_repo / "README.md").write_text("# Docs\n", encoding="utf-8")
    repo_git(["add", "README.md"], cwd=git_repo)
    result = _stage_and_invoke(git_repo, monkeypatch)
    assert result.exit_code == 1
    assert "Malformed GitMsg configuration" in result.output
    assert "Traceback" not in result.output


def test_copy_to_clipboard_can_be_disabled(git_repo: Path, monkeypatch) -> None:
    from gitmsg.cli import app

    copied: list[str] = []
    monkeypatch.setattr(
        "gitmsg.cli.copy_text",
        lambda text: copied.append(text) or True,
    )
    config_dir = git_repo / ".gitmsg"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "\n".join(
            [
                "[gitmsg]",
                "copy_to_clipboard = false",
                "max_message_length = 72",
                'default_scope = ""',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (git_repo / "README.md").write_text("# Docs\n", encoding="utf-8")
    repo_git(["add", "README.md"], cwd=git_repo)
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert copied == []
    assert "Copied to clipboard" not in result.output
    assert "Suggested commit:" in result.output


def test_invalid_max_message_length() -> None:
    with pytest.raises(ConfigError, match="max_message_length"):
        parse_config_toml("[gitmsg]\nmax_message_length = 3\n")


def test_init_does_not_overwrite_existing_config(git_repo: Path, monkeypatch) -> None:
    from gitmsg.cli import app

    monkeypatch.chdir(git_repo)
    first = runner.invoke(app, ["init"])
    assert first.exit_code == 0
    config = git_repo / ".gitmsg" / "config.toml"
    config.write_text(
        "\n".join(
            [
                "[gitmsg]",
                "max_message_length = 60",
                "copy_to_clipboard = true",
                'default_scope = "api"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    second = runner.invoke(app, ["init"])
    assert second.exit_code == 0
    text = config.read_text(encoding="utf-8")
    assert 'default_scope = "api"' in text
    assert "max_message_length = 60" in text
