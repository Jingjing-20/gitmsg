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
    "update staged changes",
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


def _split_verb_object(summary: str) -> tuple[str, str]:
    first, _, rest = summary.partition(" ")
    if first and rest:
        return first, rest
    return "", summary


def _fit_listed_objects(verb: str, objects: list[str], budget: int) -> str:
    """Return ``verb obj1, obj2, ...`` containing as many objects as fit.

    When some objects do not fit, an ``and more`` suffix is appended so the
    caller still knows that additional changes were omitted. If ``and more``
    still does not fit, the last selected object is dropped so the suffix can
    be used instead of a raw ``...`` truncation.
    """
    prefix = f"{verb} " if verb else ""
    remaining = budget - len(prefix)
    if remaining <= 0:
        return truncate_description(f"{prefix}{objects[0]}", budget)

    selected: list[str] = []
    used = 0
    for obj in objects:
        delta = len(obj) + (2 if selected else 0)
        if used + delta > remaining:
            break
        selected.append(obj)
        used += delta

    if not selected:
        return truncate_description(f"{prefix}{objects[0]}", budget)

    def join(items: list[str]) -> str:
        return f"{prefix}{', '.join(items)}"

    if len(selected) < len(objects):
        suffix = " and more"
        result = join(selected)
        if len(result) + len(suffix) <= budget:
            return result + suffix
        if len(selected) > 1:
            dropped = join(selected[:-1])
            if len(dropped) + len(suffix) <= budget:
                return dropped + suffix
        result = result[: budget - 3].rstrip(" ,") + "..."
    return join(selected)


def _combine_summaries(summaries: list[str], budget: int) -> str:
    """Merge several imperative summaries into one description.

    Summaries that share a leading verb (e.g. ``update``) are collapsed into a
    single ``verb a, b, c`` phrase so that multiple staged changes are reflected
    in the commit message instead of only the first one.
    """
    parsed = [_split_verb_object(s) for s in summaries]
    verbs = [verb for verb, _ in parsed]
    common_verb = verbs[0] if verbs and all(v == verbs[0] for v in verbs) else ""

    if common_verb:
        objects = [obj for _, obj in parsed]
        return _fit_listed_objects(common_verb, objects, budget)

    joined = ", ".join(summaries)
    if len(joined) <= budget:
        return joined
    return truncate_description(joined, budget)


def _description_from_analysis(analysis: AnalysisResult, budget: int) -> str:
    usable = [
        to_imperative(summary)
        for summary in analysis.summaries
        if to_imperative(summary) and to_imperative(summary).lower() not in _VAGUE
    ]
    if not usable:
        files = analysis.parsed.files
        if len(files) == 1:
            name = files[0].path.replace("\\", "/").rsplit("/", 1)[-1]
            return f"update {name}"
        return "update staged changes"
    if len(usable) == 1:
        return truncate_description(usable[0], budget)
    return _combine_summaries(usable, budget)


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
    prefix = (
        f"{classification.change_type}({classification.scope}): "
        if classification.scope
        else f"{classification.change_type}: "
    )
    budget = max(8, max_length - len(prefix))
    description = _description_from_analysis(analysis, budget)
    description = truncate_description(description, budget)
    full = format_commit(classification.change_type, classification.scope, description)
    return GeneratedMessage(
        type=classification.change_type,
        scope=classification.scope,
        description=description,
        full=full,
    )
