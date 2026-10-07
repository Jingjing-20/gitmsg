"""Classify staged changes into Conventional Commit types."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from gitmsg.models import AnalysisResult, ChangeStatus, Classification, FileChange

COMMIT_TYPES = (
    "feat",
    "fix",
    "refactor",
    "docs",
    "style",
    "test",
    "chore",
    "perf",
    "build",
    "ci",
    "revert",
)

_GENERIC_SCOPES = {
    "src",
    "lib",
    "libs",
    "app",
    "apps",
    "source",
    "code",
    "pkg",
    "packages",
    "test",
    "tests",
    "doc",
    "docs",
    "dist",
    "build",
    "public",
    "internal",
    "components",
}

_STYLE_EXTENSIONS = {".css", ".scss", ".sass", ".less"}
_FIX_HINTS = ("fix", "bug", "hotfix", "regression", "crash", "error", "handle")
_PERF_HINTS = ("perf", "performance", "optim", "cache")
_REFACTOR_HINTS = ("refactor", "rename", "simplify", "restructure")


def _clean_scope(value: str) -> str | None:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", value.lower().replace("_", "-")).strip("-")
    if not cleaned or cleaned in _GENERIC_SCOPES:
        return None
    return cleaned[:32]


def detect_scope(
    files: tuple[FileChange, ...],
    default_scope: str = "",
) -> str | None:
    if default_scope.strip():
        return _clean_scope(default_scope.strip())

    candidates: list[str] = []
    for file in files:
        parts = Path(file.path.replace("\\", "/")).parts
        dirs = [
            part
            for part in parts[:-1]
            if part not in {".", ".."} and part.lower() not in _GENERIC_SCOPES
        ]
        if dirs:
            cleaned = _clean_scope(dirs[-1])
            if cleaned:
                candidates.append(cleaned)
                continue
        stem = _clean_scope(Path(file.path).stem)
        if stem:
            candidates.append(stem)

    if not candidates:
        return None
    unique = set(candidates)
    if len(unique) == 1:
        return candidates[0]
    common, count = Counter(candidates).most_common(1)[0]
    if count / len(candidates) >= 0.6:
        return common
    return None


def _exclusive_type(categories: tuple[str, ...]) -> str | None:
    unique = set(categories)
    if unique == {"docs"}:
        return "docs"
    if unique == {"tests"}:
        return "test"
    if unique == {"ci"}:
        return "ci"
    if unique <= {"build", "dependencies"} and unique:
        return "build"
    if unique == {"config"}:
        return "chore"
    return None


def _score_types(analysis: AnalysisResult) -> Counter[str]:
    scores: Counter[str] = Counter()
    files = analysis.parsed.files
    categories = analysis.categories
    text = " ".join(
        [
            *analysis.summaries,
            *(file.path for file in files),
            *(signal.summary for signal in analysis.signals),
        ]
    ).lower()

    for category in categories:
        if category == "docs":
            scores["docs"] += 5
        elif category == "tests":
            scores["test"] += 5
        elif category == "ci":
            scores["ci"] += 5
        elif category in {"build", "dependencies"}:
            scores["build"] += 4
        elif category == "schema":
            scores["feat"] += 2
        elif category == "config":
            scores["chore"] += 3
        elif category == "source":
            scores["feat"] += 1

    for signal in analysis.signals:
        if signal.kind == "added_function":
            scores["feat"] += 4
        elif signal.kind == "deleted_function":
            scores["refactor"] += 2
        elif signal.kind == "route":
            scores["feat"] += 3
        elif signal.kind == "added_class":
            scores["feat"] += 3
        elif signal.kind == "error_handling":
            scores["fix"] += 2

    if any(hint in text for hint in _FIX_HINTS):
        scores["fix"] += 4
    if any(hint in text for hint in _PERF_HINTS):
        scores["perf"] += 5
    if any(hint in text for hint in _REFACTOR_HINTS):
        scores["refactor"] += 3
    if "revert" in text:
        scores["revert"] += 6

    if files and all(file.status == ChangeStatus.RENAMED for file in files):
        scores["refactor"] += 5
    if files and all(file.extension in _STYLE_EXTENSIONS for file in files):
        scores["style"] += 6

    added_functions = any(
        signal.kind == "added_function" for signal in analysis.signals
    )
    added_files = any(file.status == ChangeStatus.ADDED for file in files)
    if not added_functions and not added_files and "source" in categories:
        scores["refactor"] += 1

    return scores


def _confidence(
    analysis: AnalysisResult,
    change_type: str,
    scope: str | None,
    exclusive: bool,
) -> int:
    score = 55
    if exclusive:
        score += 30
    if len(analysis.categories) == 1:
        score += 10
    if any(
        signal.kind in {"added_function", "route", "added_class"}
        for signal in analysis.signals
    ):
        score += 8
    if scope:
        score += 5
    if analysis.mixed:
        score -= 20
    if analysis.parsed.stats.files_changed >= 10:
        score -= 10
    if change_type == "chore" and not exclusive:
        score -= 8
    return max(20, min(95, score))


def classify(
    analysis: AnalysisResult,
    *,
    default_scope: str = "",
) -> Classification:
    exclusive = _exclusive_type(analysis.categories)
    scores = _score_types(analysis)
    if exclusive:
        change_type = exclusive
        evidence = [f"all staged files categorized as {exclusive}"]
    elif scores:
        change_type = scores.most_common(1)[0][0]
        evidence = [
            f"{name}={value}" for name, value in scores.most_common(4) if value > 0
        ]
    else:
        change_type = "chore"
        evidence = ["insufficient signals; defaulted to chore"]

    scope = detect_scope(analysis.parsed.files, default_scope=default_scope)
    if analysis.mixed and not default_scope.strip():
        scope = None
        evidence.append("mixed concerns; omitted scope")

    confidence = _confidence(
        analysis, change_type, scope, exclusive=exclusive is not None
    )
    if analysis.mixed_notice:
        evidence.append("mixed staged changes")
    return Classification(
        change_type=change_type,
        scope=scope,
        confidence=confidence,
        evidence=tuple(evidence),
    )


def alternative_classifications(
    analysis: AnalysisResult,
    primary: Classification,
    *,
    default_scope: str = "",
) -> tuple[Classification, ...]:
    """Return close alternative classifications when they are actually useful."""
    scores = _score_types(analysis)
    exclusive = _exclusive_type(analysis.categories)
    if exclusive:
        return ()

    alternatives: list[Classification] = []
    for change_type, value in scores.most_common(4):
        if change_type == primary.change_type or value <= 0:
            continue
        top = scores[primary.change_type]
        if top - value > 3:
            continue
        scope = primary.scope
        alternatives.append(
            Classification(
                change_type=change_type,
                scope=scope,
                confidence=max(20, primary.confidence - 12),
                evidence=(f"alternative type from scoring ({change_type}={value})",),
            )
        )

    if primary.scope:
        alternatives.append(
            Classification(
                change_type=primary.change_type,
                scope=None,
                confidence=max(20, primary.confidence - 8),
                evidence=("alternative without inferred scope",),
            )
        )
    elif default_scope.strip():
        cleaned = _clean_scope(default_scope.strip())
        if cleaned:
            alternatives.append(
                Classification(
                    change_type=primary.change_type,
                    scope=cleaned,
                    confidence=max(20, primary.confidence - 8),
                    evidence=("alternative using configured default scope",),
                )
            )
    return tuple(alternatives[:2])
