"""Git CLI integration for repository detection and staged changes."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from gitmsg.exceptions import (
    GitCommandError,
    GitNotInstalledError,
    NotAGitRepositoryError,
)

GIT_EXECUTABLE = "git"


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("LC_ALL", "C")
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_git(
    args: list[str],
    *,
    cwd: Path | str | None = None,
) -> str:
    """Run a Git command and return stdout.

    Raises GitNotInstalledError, NotAGitRepositoryError, or GitCommandError.
    """
    working_dir = Path(cwd) if cwd is not None else Path.cwd()
    try:
        result = subprocess.run(
            [GIT_EXECUTABLE, *args],
            cwd=working_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=_git_env(),
        )
    except FileNotFoundError as exc:
        raise GitNotInstalledError() from exc

    if result.returncode == 0:
        return result.stdout

    stderr = result.stderr.strip()
    combined = f"{stderr}\n{result.stdout}".lower()
    if "not a git repository" in combined:
        raise NotAGitRepositoryError(working_dir)
    raise GitCommandError(args, result.returncode, result.stderr)


def find_repo_root(cwd: Path | str | None = None) -> Path:
    """Return the repository toplevel using Git itself."""
    output = run_git(["rev-parse", "--show-toplevel"], cwd=cwd)
    root = output.strip()
    if not root:
        working_dir = Path(cwd) if cwd is not None else Path.cwd()
        raise NotAGitRepositoryError(working_dir)
    return Path(root)


def has_staged_changes(cwd: Path | str | None = None) -> bool:
    """Return True when `git diff --cached` contains changes.

    `git diff --quiet` exits 1 when a diff exists and 0 when it does not.
    """
    working_dir = Path(cwd) if cwd is not None else Path.cwd()
    try:
        result = subprocess.run(
            [GIT_EXECUTABLE, "diff", "--cached", "--quiet"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=_git_env(),
        )
    except FileNotFoundError as exc:
        raise GitNotInstalledError() from exc

    if result.returncode == 0:
        return False
    if result.returncode == 1:
        return True

    stderr = result.stderr.strip()
    combined = f"{stderr}\n{result.stdout}".lower()
    if "not a git repository" in combined:
        raise NotAGitRepositoryError(working_dir)
    raise GitCommandError(
        ["diff", "--cached", "--quiet"],
        result.returncode,
        result.stderr,
    )


def get_staged_diff(cwd: Path | str | None = None) -> str:
    """Return the staged unified diff (`git diff --cached`)."""
    return run_git(
        ["diff", "--cached", "--no-color", "--no-ext-diff", "--find-renames"],
        cwd=cwd,
    )


def get_staged_name_status(cwd: Path | str | None = None) -> str:
    """Return staged `--name-status` output, including renames and copies."""
    return run_git(
        ["diff", "--cached", "--name-status", "-M", "-C"],
        cwd=cwd,
    )


def get_staged_numstat(cwd: Path | str | None = None) -> str:
    """Return staged `--numstat` output, including renames and copies."""
    return run_git(
        ["diff", "--cached", "--numstat", "-M", "-C"],
        cwd=cwd,
    )
