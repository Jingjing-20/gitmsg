"""Generate Conventional Commit messages from analysis and classification."""

from __future__ import annotations

import re

from gitmsg.models import AnalysisResult, Classification, GeneratedMessage

_LEADING_VERBS = (
    ("added ", "add "),
    ("updated ", "update "),
    ("removed ", "remove "),
    ("deleted ", "remove "),
    ("renamed ", "rename "),
    ("fixed ", "fix "),
)

_VAGUE = {
    "update stuff",
    "changes",
    "modified files",
    "fix issue",
    "update code",
    "update files",
}


def to_imperative(summary: str) -> str:
    text = summary.strip().rstrip(".").rstrip("!")
    lowered = text[:1].lower() + text[1:] if text else text
    for prefix, replacement in _LEADING_VERBS:
        if lowered.startswith(prefix):
            lowered = replacement + lowered[len(prefix) :]
            break
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _description_from_analysis(analysis: AnalysisResult) -> str:
    for summary in analysis.summaries:
        candidate = to_imperative(summary)
        if candidate and candidate.lower() not in _VAGUE:
            return candidate
    files = analysis.parsed.files
    if len(files) == 1:
        name = files[0].path.replace("\\", "/").rsplit("/", 1)[-1]
        return f"update {name}"
    return "update staged changes"


def truncate_description(description: str, budget: int) -> str:
    if budget <= 0:
        return ""
    if len(description) <= budget:
        return description
    truncated = description[:budget].rsplit(" ", 1)[0].rstrip("-:,")
    return truncated or description[:budget]


def format_commit(change_type: str, scope: str | None, description: str) -> str:
    if scope:
        return f"{change_type}({scope}): {description}"
    return f"{change_type}: {description}"


def generate(
    analysis: AnalysisResult,
    classification: Classification,
    *,
    max_length: int = 72,
) -> GeneratedMessage:
    description = _description_from_analysis(analysis)
    prefix = (
        f"{classification.change_type}({classification.scope}): "
        if classification.scope
        else f"{classification.change_type}: "
    )
    description = truncate_description(description, max(8, max_length - len(prefix)))
    full = format_commit(classification.change_type, classification.scope, description)
    return GeneratedMessage(
        type=classification.change_type,
        scope=classification.scope,
        description=description,
        full=full,
    )
