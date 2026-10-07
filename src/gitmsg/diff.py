"""Parse staged Git diffs into structured file changes and statistics."""

from __future__ import annotations

import re
from pathlib import Path

from gitmsg.git import get_staged_diff, get_staged_name_status, get_staged_numstat
from gitmsg.models import ChangeStatus, DiffStats, FileChange, ParsedDiff

_LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".php": "PHP",
    ".java": "Java",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".sql": "SQL",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ps1": "shell",
    ".bat": "shell",
    ".cmd": "shell",
}

_STATUS_LETTERS = {
    "A": ChangeStatus.ADDED,
    "M": ChangeStatus.MODIFIED,
    "D": ChangeStatus.DELETED,
    "T": ChangeStatus.MODIFIED,
}

_RENAME_FIELD = re.compile(r"^(.*)\{(.*?) => (.*?)\}(.*)$")
_STATUS_SCORE = re.compile(r"^([ACDMRT])(\d{1,3})?$")


def extension_for(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix:
        return suffix
    name = Path(path).name.lower()
    if name in {".gitignore", ".gitattributes", ".dockerignore"}:
        return name
    return ""


def language_for(path: str) -> str:
    ext = extension_for(path)
    return _LANGUAGE_BY_EXTENSION.get(ext, "unknown")


def unquote_git_path(path: str) -> str:
    """Decode Git C-quoted paths such as `"\\350\\257\\264.py"`."""
    if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
        inner = path[1:-1]
        try:
            return (
                inner.encode("utf-8")
                .decode("unicode_escape")
                .encode("latin-1")
                .decode("utf-8")
            )
        except UnicodeError:
            return inner
    return path


def split_rename_path(field: str) -> tuple[str, str]:
    """Split a Git numstat/summary path that may include ` => `."""
    match = _RENAME_FIELD.match(field)
    if match:
        prefix, old, new, suffix = match.groups()
        return f"{prefix}{old}{suffix}", f"{prefix}{new}{suffix}"
    if " => " in field:
        old, new = field.split(" => ", 1)
        return old, new
    return field, field


def parse_name_status(text: str) -> list[FileChange]:
    files: list[FileChange] = []
    for raw_line in text.splitlines():
        line = raw_line.strip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        match = _STATUS_SCORE.match(parts[0])
        if match is None:
            continue
        letter, score = match.groups()
        similarity = int(score) if score is not None else None
        if letter == "R":
            if len(parts) < 3:
                continue
            old_path, path = unquote_git_path(parts[1]), unquote_git_path(parts[2])
            status = ChangeStatus.RENAMED
        elif letter == "C":
            if len(parts) < 3:
                continue
            old_path, path = unquote_git_path(parts[1]), unquote_git_path(parts[2])
            status = ChangeStatus.COPIED
        else:
            status = _STATUS_LETTERS.get(letter)
            if status is None:
                continue
            path = unquote_git_path(parts[1])
            old_path = None
        files.append(
            FileChange(
                path=path,
                status=status,
                old_path=old_path,
                similarity=similarity,
                extension=extension_for(path),
                language=language_for(path),
            )
        )
    return files


def parse_numstat(text: str) -> dict[str, tuple[int, int, bool]]:
    """Map new path -> (insertions, deletions, is_binary)."""
    stats: dict[str, tuple[int, int, bool]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, removed, path_field = parts[0], parts[1], parts[2]
        _, new_path = split_rename_path(unquote_git_path(path_field))
        if added == "-" or removed == "-":
            stats[new_path] = (0, 0, True)
            continue
        stats[new_path] = (int(added), int(removed), False)
    return stats


def combine_name_status_and_numstat(
    files: list[FileChange],
    numstat: dict[str, tuple[int, int, bool]],
) -> tuple[FileChange, ...]:
    combined: list[FileChange] = []
    for file in files:
        insertions, deletions, is_binary = numstat.get(file.path, (0, 0, False))
        combined.append(
            FileChange(
                path=file.path,
                status=file.status,
                insertions=insertions,
                deletions=deletions,
                old_path=file.old_path,
                similarity=file.similarity,
                is_binary=is_binary,
                extension=file.extension,
                language=file.language,
            )
        )
    return tuple(combined)


def summarize_stats(files: tuple[FileChange, ...]) -> DiffStats:
    insertions = sum(file.insertions for file in files if not file.is_binary)
    deletions = sum(file.deletions for file in files if not file.is_binary)
    return DiffStats(
        files_changed=len(files),
        insertions=insertions,
        deletions=deletions,
    )


def parse_staged_metadata(name_status: str, numstat: str, raw: str = "") -> ParsedDiff:
    files = combine_name_status_and_numstat(
        parse_name_status(name_status),
        parse_numstat(numstat),
    )
    return ParsedDiff(files=files, stats=summarize_stats(files), raw=raw)


def parse_staged_changes(cwd: Path | str | None = None) -> ParsedDiff:
    """Read staged Git metadata and return a structured diff."""
    return parse_staged_metadata(
        get_staged_name_status(cwd),
        get_staged_numstat(cwd),
        raw=get_staged_diff(cwd),
    )
