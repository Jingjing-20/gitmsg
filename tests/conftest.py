from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

GIT = "git"


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "GitMsg Test",
        "GIT_AUTHOR_EMAIL": "gitmsg-test@example.com",
        "GIT_COMMITTER_NAME": "GitMsg Test",
        "GIT_COMMITTER_EMAIL": "gitmsg-test@example.com",
    }
    return subprocess.run(
        [GIT, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        env=env,
    )


def init_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    run_git(["init"], cwd=path)
    run_git(["config", "user.name", "GitMsg Test"], cwd=path)
    run_git(["config", "user.email", "gitmsg-test@example.com"], cwd=path)
    run_git(["config", "commit.gpgsign", "false"], cwd=path)
    return path


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    return init_git_repo(tmp_path / "repo")
