"""Interpret staged file changes and extract semantic signals."""

from __future__ import annotations

import re
from pathlib import Path

from gitmsg.models import (
    AnalysisResult,
    ChangeSignal,
    ChangeStatus,
    FileChange,
    ParsedDiff,
)

_ADDED_FUNCTION = [
    re.compile(r"^\+\s*(?:async\s+)?def\s+([A-Za-z_][\w]*)"),
    re.compile(r"^\+\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][\w]*)"),
    re.compile(r"^\+\s*(?:pub(?:\([^)]+\))?\s+)?(?:async\s+)?fn\s+([A-Za-z_][\w]*)"),
    re.compile(
        r"^\+\s*(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?"
        r"(?:[\w.<>,\[\]?]+\s+)+([A-Za-z_][\w]*)\s*\("
    ),
]

_DELETED_FUNCTION = [
    re.compile(pattern.pattern.replace(r"^\+", r"^-")) for pattern in _ADDED_FUNCTION
]

_ADDED_CLASS = re.compile(
    r"^\+\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_][\w]*)"
)
_DELETED_CLASS = re.compile(
    r"^\-\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_][\w]*)"
)
_ADDED_IMPORT = re.compile(r"^\+\s*(?:import\s+|from\s+\S+\s+import\s+|require\()")
_DELETED_IMPORT = re.compile(r"^\-\s*(?:import\s+|from\s+\S+\s+import\s+|require\()")
_ADDED_EXPORT = re.compile(r"^\+\s*export\s+")
_ROUTE = re.compile(
    r"@(?:app|router|api)\.(?:route|get|post|put|patch|delete)|"
    r"\.(?:get|post|put|patch|delete)\(\s*['\"]\/|"
    r"@(?:Get|Post|Put|Patch|Delete|RequestMapping)\(|"
    r"Route::|"
    r"app\.(?:get|post|put|patch|delete)\(",
    re.IGNORECASE,
)
_AUTH = re.compile(
    r"\b(auth|oauth|jwt|session|password|login|logout|permission|csrf)\b",
    re.IGNORECASE,
)
_VALIDATION = re.compile(r"\b(validat|schema|zod|yup|pydantic)\b", re.IGNORECASE)
_ERROR_HANDLING = re.compile(
    r"\b(try:|except |catch\s*\(|throw |raise |finally:)\b",
    re.IGNORECASE,
)

_DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "requirements.in",
    "pipfile",
    "pipfile.lock",
    "poetry.lock",
    "pyproject.toml",
    "cargo.toml",
    "cargo.lock",
    "go.mod",
    "go.sum",
    "composer.json",
    "composer.lock",
    "gemfile",
    "gemfile.lock",
}

_BUILD_FILES = {
    "makefile",
    "dockerfile",
    "tsconfig.json",
    "webpack.config.js",
    "vite.config.ts",
    "vite.config.js",
    "setup.py",
    "setup.cfg",
    "cmakelists.txt",
}

_MIXED_GROUPS = {
    "source",
    "tests",
    "docs",
    "dependencies",
    "ci",
    "build",
    "schema",
}


def humanize_identifier(name: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    spaced = spaced.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", spaced).strip().lower()


def categorize_path(path: str) -> str:
    posix = path.replace("\\", "/").lower()
    name = Path(path).name.lower()
    parts = posix.split("/")

    if ".github/workflows" in posix or name in {
        ".gitlab-ci.yml",
        "jenkinsfile",
        "azure-pipelines.yml",
    }:
        return "ci"
    if name in _DEPENDENCY_FILES:
        return "dependencies"
    if name in _BUILD_FILES or name.endswith(".dockerfile"):
        return "build"
    if posix.endswith(".sql") or any(
        part in {"migrations", "migration", "alembic", "prisma", "schema"}
        for part in parts
    ):
        return "schema"
    if (
        name.startswith("test_")
        or name.endswith(("_test.py", ".test.js", ".test.ts", ".spec.js", ".spec.ts"))
        or any(part in {"test", "tests", "__tests__", "spec"} for part in parts)
    ):
        return "tests"
    if name == "readme.md" or posix.endswith(".md") or "docs" in parts:
        return "docs"
    if (
        name.endswith((".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf"))
        or "config" in parts
    ):
        return "config"
    return "source"


def _iter_content_lines(raw_diff: str) -> list[str]:
    lines: list[str] = []
    for line in raw_diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+") or line.startswith("-"):
            lines.append(line)
    return lines


def _collect_names(lines: list[str], patterns: list[re.Pattern[str]]) -> list[str]:
    names: list[str] = []
    for line in lines:
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                names.append(match.group(1))
                break
    return names


def analyze_file_signals(file: FileChange, raw_diff: str) -> list[ChangeSignal]:
    signals: list[ChangeSignal] = []
    category = categorize_path(file.path)
    signals.append(
        ChangeSignal(kind="category", summary=category, path=file.path, weight=2)
    )
    signals.append(
        ChangeSignal(
            kind="status",
            summary=file.status.value,
            path=file.path,
            weight=1,
        )
    )

    if file.is_binary:
        signals.append(
            ChangeSignal(kind="binary", summary="binary file", path=file.path, weight=1)
        )
        return signals

    lines = _iter_content_lines(raw_diff)
    added_functions = _collect_names(lines, _ADDED_FUNCTION)
    deleted_functions = _collect_names(lines, _DELETED_FUNCTION)
    for name in added_functions:
        signals.append(
            ChangeSignal(
                kind="added_function",
                summary=f"Added {humanize_identifier(name)}",
                path=file.path,
                weight=3,
            )
        )
    for name in deleted_functions:
        signals.append(
            ChangeSignal(
                kind="deleted_function",
                summary=f"Deleted {humanize_identifier(name)}",
                path=file.path,
                weight=3,
            )
        )

    added_class = next(
        (match for line in lines if (match := _ADDED_CLASS.search(line))),
        None,
    )
    if added_class is not None:
        signals.append(
            ChangeSignal(
                kind="added_class",
                summary=f"Added {humanize_identifier(added_class.group(1))} class",
                path=file.path,
                weight=3,
            )
        )
    if any(_DELETED_CLASS.search(line) for line in lines):
        signals.append(
            ChangeSignal(
                kind="deleted_class", summary="Removed class", path=file.path, weight=2
            )
        )
    if any(_ADDED_IMPORT.search(line) for line in lines):
        signals.append(
            ChangeSignal(kind="import", summary="Updated imports", path=file.path)
        )
    if any(_DELETED_IMPORT.search(line) for line in lines):
        signals.append(
            ChangeSignal(kind="import", summary="Removed imports", path=file.path)
        )
    if any(_ADDED_EXPORT.search(line) for line in lines):
        signals.append(
            ChangeSignal(kind="export", summary="Updated exports", path=file.path)
        )
    if any(_ROUTE.search(line) for line in lines):
        signals.append(
            ChangeSignal(
                kind="route", summary="Updated API routes", path=file.path, weight=3
            )
        )
    if any(_AUTH.search(line) for line in lines) or _AUTH.search(file.path):
        signals.append(
            ChangeSignal(
                kind="auth", summary="Updated authentication", path=file.path, weight=2
            )
        )
    if any(_VALIDATION.search(line) for line in lines):
        signals.append(
            ChangeSignal(
                kind="validation",
                summary="Updated validation",
                path=file.path,
                weight=2,
            )
        )
    if any(_ERROR_HANDLING.search(line) for line in lines):
        signals.append(
            ChangeSignal(
                kind="error_handling",
                summary="Updated error handling",
                path=file.path,
                weight=1,
            )
        )
    return signals


def _file_summaries(file: FileChange, signals: list[ChangeSignal]) -> list[str]:
    named = [
        signal.summary
        for signal in signals
        if signal.kind in {"added_function", "deleted_function", "added_class", "route"}
    ]
    if named:
        return named
    label = Path(file.path).stem.replace("_", " ").replace("-", " ")
    if file.status == ChangeStatus.ADDED:
        return [f"Added {label}"]
    if file.status == ChangeStatus.DELETED:
        return [f"Removed {label}"]
    if file.status == ChangeStatus.RENAMED:
        return [
            f"Renamed {Path(file.old_path or file.path).name} to {Path(file.path).name}"
        ]
    return [f"Updated {label}"]


def _split_raw_diff_by_file(raw: str) -> dict[str, str]:
    chunks: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    header = re.compile(r"^diff --git a/(.+) b/(.+)$")
    for line in raw.splitlines(keepends=True):
        match = header.match(line.rstrip("\n"))
        if match:
            if current is not None:
                chunks[current] = "".join(buffer)
            current = match.group(2)
            buffer = [line]
        elif current is not None:
            buffer.append(line)
    if current is not None:
        chunks[current] = "".join(buffer)
    return chunks


def detect_mixed_changes(categories: tuple[str, ...]) -> tuple[bool, str | None]:
    groups = {category for category in categories if category in _MIXED_GROUPS}
    if "config" in categories and "source" in groups:
        groups.add("config")
    if len(groups) >= 3:
        return True, "Notice: staged changes appear to contain multiple concerns."
    return False, None


def analyze(parsed: ParsedDiff) -> AnalysisResult:
    """Derive categories, signals, and summaries from a parsed staged diff."""
    per_file_raw = _split_raw_diff_by_file(parsed.raw)
    all_signals: list[ChangeSignal] = []
    summaries: list[str] = []
    categories: list[str] = []

    for file in parsed.files:
        raw = per_file_raw.get(file.path, parsed.raw)
        file_signals = analyze_file_signals(file, raw)
        all_signals.extend(file_signals)
        categories.append(categorize_path(file.path))
        summaries.extend(_file_summaries(file, file_signals))

    unique_summaries = tuple(dict.fromkeys(summaries))
    unique_categories = tuple(dict.fromkeys(categories))
    mixed, notice = detect_mixed_changes(unique_categories)
    return AnalysisResult(
        parsed=parsed,
        signals=tuple(all_signals),
        summaries=unique_summaries[:8],
        categories=unique_categories,
        mixed=mixed,
        mixed_notice=notice,
    )
