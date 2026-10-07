from __future__ import annotations

from gitmsg.analyzer import analyze
from gitmsg.classifier import classify
from gitmsg.generator import generate, to_imperative
from gitmsg.models import (
    AnalysisResult,
    ChangeStatus,
    Classification,
    DiffStats,
    FileChange,
    ParsedDiff,
)


def test_to_imperative() -> None:
    assert to_imperative("Added project filtering") == "add project filtering"
    assert to_imperative("Updated project rendering.") == "update project rendering"


def test_generate_feat_with_scope() -> None:
    raw = """\
diff --git a/src/projects.py b/src/projects.py
--- a/src/projects.py
+++ b/src/projects.py
@@ -0,0 +1,2 @@
+def add_project_filtering():
+    return True
"""
    parsed = ParsedDiff(
        files=(
            FileChange(
                path="src/projects.py",
                status=ChangeStatus.MODIFIED,
                insertions=2,
                extension=".py",
                language="Python",
            ),
        ),
        stats=DiffStats(files_changed=1, insertions=2, deletions=0),
        raw=raw,
    )
    analysis = analyze(parsed)
    message = generate(analysis, classify(analysis))
    assert message.full == "feat(projects): add project filtering"
    assert len(message.full) <= 72


def test_generate_respects_length_limit() -> None:
    analysis = AnalysisResult(
        parsed=ParsedDiff(
            files=(FileChange(path="src/module.py", status=ChangeStatus.MODIFIED),),
            stats=DiffStats(files_changed=1, insertions=1, deletions=0),
        ),
        signals=(),
        summaries=("Added an extremely long description that should be shortened",),
        categories=("source",),
    )
    classification = Classification(
        change_type="feat",
        scope="module",
        confidence=70,
        evidence=(),
    )
    message = generate(analysis, classification, max_length=40)
    assert len(message.full) <= 40
    assert message.full.startswith("feat(module):")
