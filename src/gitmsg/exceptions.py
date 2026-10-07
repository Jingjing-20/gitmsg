"""Application-level exceptions for GitMsg."""

from __future__ import annotations

from pathlib import Path


class GitMsgError(Exception):
    """Base exception for expected GitMsg failures."""


class GitNotInstalledError(GitMsgError):
    """Raised when the Git executable cannot be found."""

    def __init__(self) -> None:
        super().__init__("Git is not installed or was not found on PATH.")


class NotAGitRepositoryError(GitMsgError):
    """Raised when the current directory is not inside a Git working tree."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            "Not a Git repository.\n\n"
            "GitMsg must be run from inside a Git working tree.\n"
            f"Current directory: {path}"
        )


class GitCommandError(GitMsgError):
    """Raised when a Git command fails unexpectedly."""

    def __init__(self, args: list[str], returncode: int, stderr: str) -> None:
        command = " ".join(["git", *args])
        details = stderr.strip() or f"exit code {returncode}"
        super().__init__(f"Git command failed ({returncode}): {command}\n{details}")
        self.args_list = args
        self.returncode = returncode
        self.stderr = stderr


class ConfigError(GitMsgError):
    """Raised when `.gitmsg/config.toml` cannot be read or parsed."""
