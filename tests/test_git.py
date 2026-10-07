from __future__ import annotations

from pathlib import Path

import pytest
from tests.conftest import run_git as repo_git

from gitmsg.exceptions import GitCommandError, NotAGitRepositoryError
from gitmsg.git import find_repo_root, get_staged_diff, has_staged_changes, run_git


def test_find_repo_root_from_repository(git_repo: Path) -> None:
    assert find_repo_root(git_repo).resolve() == git_repo.resolve()


def test_find_repo_root_from_nested_directory(git_repo: Path) -> None:
    nested = git_repo / "src" / "components"
    nested.mkdir(parents=True)
    assert find_repo_root(nested).resolve() == git_repo.resolve()


def test_find_repo_root_rejects_non_git_directory(tmp_path: Path) -> None:
    with pytest.raises(NotAGitRepositoryError) as exc_info:
        find_repo_root(tmp_path)
    assert "Not a Git repository" in str(exc_info.value)


def test_has_staged_changes_is_false_when_empty(git_repo: Path) -> None:
    assert has_staged_changes(git_repo) is False


def test_has_staged_changes_detects_added_file(git_repo: Path) -> None:
    (git_repo / "example.py").write_text("print('hello')\n", encoding="utf-8")
    repo_git(["add", "example.py"], cwd=git_repo)
    assert has_staged_changes(git_repo) is True


def test_get_staged_diff_returns_cached_content(git_repo: Path) -> None:
    (git_repo / "example.py").write_text("print('hello')\n", encoding="utf-8")
    repo_git(["add", "example.py"], cwd=git_repo)
    diff = get_staged_diff(git_repo)
    assert "example.py" in diff
    assert "print('hello')" in diff


def test_get_staged_diff_ignores_unstaged_changes(git_repo: Path) -> None:
    tracked = git_repo / "tracked.py"
    tracked.write_text("original\n", encoding="utf-8")
    repo_git(["add", "tracked.py"], cwd=git_repo)
    repo_git(["commit", "-m", "initial"], cwd=git_repo)

    tracked.write_text("unstaged\n", encoding="utf-8")
    (git_repo / "unstaged.py").write_text("not added\n", encoding="utf-8")

    assert has_staged_changes(git_repo) is False
    assert get_staged_diff(git_repo) == ""


def test_run_git_unknown_command_raises(git_repo: Path) -> None:
    with pytest.raises(GitCommandError):
        run_git(["this-command-does-not-exist"], cwd=git_repo)
