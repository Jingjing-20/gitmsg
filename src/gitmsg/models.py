"""Structured models used by GitMsg."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ChangeStatus(StrEnum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"


@dataclass(frozen=True)
class FileChange:
    path: str
    status: ChangeStatus
    insertions: int = 0
    deletions: int = 0
    old_path: str | None = None
    similarity: int | None = None
    is_binary: bool = False
    extension: str = ""
    language: str = "unknown"


@dataclass(frozen=True)
class DiffStats:
    files_changed: int
    insertions: int
    deletions: int


@dataclass(frozen=True)
class ParsedDiff:
    files: tuple[FileChange, ...]
    stats: DiffStats
    raw: str = ""


@dataclass(frozen=True)
class ChangeSignal:
    kind: str
    summary: str
    path: str | None = None
    weight: int = 1


@dataclass(frozen=True)
class AnalysisResult:
    parsed: ParsedDiff
    signals: tuple[ChangeSignal, ...]
    summaries: tuple[str, ...]
    categories: tuple[str, ...]
    mixed: bool = False
    mixed_notice: str | None = None


@dataclass(frozen=True)
class Classification:
    change_type: str
    scope: str | None
    confidence: int
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedMessage:
    type: str
    scope: str | None
    description: str
    full: str


@dataclass(frozen=True)
class GitMsgConfig:
    max_message_length: int = 72
    copy_to_clipboard: bool = True
    default_scope: str = ""
    extra: dict[str, object] = field(default_factory=dict)
