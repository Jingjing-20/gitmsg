from __future__ import annotations

from pathlib import Path

from tests.conftest import run_git as repo_git
from typer.testing import CliRunner

from gitmsg import __version__
from gitmsg.cli import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "staged Git changes" in result.output
    assert "--version" in result.output
    assert "--analyze" in result.output
    assert "--dry-run" in result.output
    assert "--suggest" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"gitmsg {__version__}" in result.output


def test_non_git_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, [])
    assert result.exit_code == 1
    assert "Not a Git repository" in result.output


def test_no_staged_changes(git_repo: Path, monkeypatch) -> None:
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "No staged changes found" in result.output
    assert "git add <files>" in result.output


def test_default_generates_and_copies(git_repo: Path, monkeypatch) -> None:
    copied: list[str] = []
    monkeypatch.setattr(
        "gitmsg.cli.copy_text",
        lambda text: copied.append(text) or True,
    )
    (git_repo / "src").mkdir()
    (git_repo / "src" / "projects.py").write_text(
        "def add_project_filtering():\n    return True\n",
        encoding="utf-8",
    )
    repo_git(["add", "src/projects.py"], cwd=git_repo)
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Files changed: 1" in result.output
    assert "Suggested commit:" in result.output
    assert "Copied to clipboard" in result.output
    assert copied
    assert copied[0].startswith("feat")


def test_dry_run_does_not_copy(git_repo: Path, monkeypatch) -> None:
    copied: list[str] = []
    monkeypatch.setattr(
        "gitmsg.cli.copy_text",
        lambda text: copied.append(text) or True,
    )
    (git_repo / "README.md").write_text("# Docs\n", encoding="utf-8")
    repo_git(["add", "README.md"], cwd=git_repo)
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["--dry-run"])
    assert result.exit_code == 0
    assert "Suggested commit:" in result.output
    assert "Copied to clipboard" not in result.output
    assert copied == []


def test_analyze_does_not_generate_message(git_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr("gitmsg.cli.copy_text", lambda text: True)
    (git_repo / "README.md").write_text("# Docs\n", encoding="utf-8")
    repo_git(["add", "README.md"], cwd=git_repo)
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["--analyze"])
    assert result.exit_code == 0
    assert "Detected changes:" in result.output
    assert "Change type: docs" in result.output
    assert "Suggested commit:" not in result.output
    assert "Copied to clipboard" not in result.output


def test_suggest_mode(git_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr("gitmsg.cli.copy_text", lambda text: True)
    (git_repo / "src").mkdir()
    (git_repo / "src" / "projects.py").write_text(
        "def add_project_filtering():\n    return True\n",
        encoding="utf-8",
    )
    repo_git(["add", "src/projects.py"], cwd=git_repo)
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["--suggest"])
    assert result.exit_code == 0
    assert "Suggested commit:" in result.output or "Suggested commits:" in result.output


def test_nested_directory(git_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr("gitmsg.cli.copy_text", lambda text: True)
    nested = git_repo / "src" / "components"
    nested.mkdir(parents=True)
    (git_repo / "README.md").write_text("# Nested\n", encoding="utf-8")
    repo_git(["add", "README.md"], cwd=git_repo)
    monkeypatch.chdir(nested)
    result = runner.invoke(app, ["--dry-run"])
    assert result.exit_code == 0
    assert "docs" in result.output.lower()


def test_init_creates_config(git_repo: Path, monkeypatch) -> None:
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (git_repo / ".gitmsg" / "config.toml").exists()
    assert ".gitmsg/" in (git_repo / ".gitignore").read_text(encoding="utf-8")


def test_clipboard_failure_is_not_fatal(git_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr("gitmsg.cli.copy_text", lambda _text: False)
    (git_repo / "README.md").write_text("# Docs\n", encoding="utf-8")
    repo_git(["add", "README.md"], cwd=git_repo)
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Could not copy to clipboard" in result.output
    assert "Suggested commit:" in result.output
