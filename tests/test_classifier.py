from __future__ import annotations

from gitmsg.analyzer import analyze
from gitmsg.classifier import classify, detect_scope
from gitmsg.diff import parse_staged_metadata
from gitmsg.models import ChangeStatus, DiffStats, FileChange, ParsedDiff


def test_classify_docs_only() -> None:
    parsed = parse_staged_metadata(
        "M\tREADME.md\n",
        "3\t1\tREADME.md\n",
        raw="",
    )
    result = classify(analyze(parsed))
    assert result.change_type == "docs"
    assert result.confidence >= 80
    assert "docs" in " ".join(result.evidence)


def test_classify_tests_only() -> None:
    parsed = parse_staged_metadata(
        "A\ttests/test_users.py\n",
        "12\t0\ttests/test_users.py\n",
        raw="",
    )
    result = classify(analyze(parsed))
    assert result.change_type == "test"


def test_classify_ci_only() -> None:
    parsed = parse_staged_metadata(
        "A\t.github/workflows/ci.yml\n",
        "20\t0\t.github/workflows/ci.yml\n",
        raw="",
    )
    result = classify(analyze(parsed))
    assert result.change_type == "ci"


def test_classify_build_dependencies() -> None:
    parsed = parse_staged_metadata(
        "M\tpackage.json\n",
        "2\t1\tpackage.json\n",
        raw="",
    )
    result = classify(analyze(parsed))
    assert result.change_type == "build"


def test_classify_feat_from_added_function() -> None:
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
    result = classify(analyze(parsed))
    assert result.change_type == "feat"
    assert result.scope == "projects"


def test_classify_fix_from_hints() -> None:
    raw = """\
diff --git a/src/auth.py b/src/auth.py
--- a/src/auth.py
+++ b/src/auth.py
@@ -1 +1,2 @@
-def login():
+def login():
+    raise ValueError('fix missing user ID')
"""
    parsed = ParsedDiff(
        files=(
            FileChange(
                path="src/auth.py",
                status=ChangeStatus.MODIFIED,
                insertions=1,
                extension=".py",
                language="Python",
            ),
        ),
        stats=DiffStats(files_changed=1, insertions=1, deletions=0),
        raw=raw,
    )
    result = classify(analyze(parsed))
    assert result.change_type == "fix"
    assert result.scope == "auth"


def test_detect_scope_omitted_when_mixed() -> None:
    parsed = parse_staged_metadata(
        "M\tsrc/auth.py\nM\tREADME.md\nM\tpackage.json\n",
        "4\t1\tsrc/auth.py\n2\t0\tREADME.md\n3\t1\tpackage.json\n",
        raw="",
    )
    result = classify(analyze(parsed))
    assert result.scope is None
    assert result.confidence < 80


def test_detect_scope_from_common_directory() -> None:
    files = (
        FileChange(path="src/users/api.py", status=ChangeStatus.MODIFIED),
        FileChange(path="src/users/model.py", status=ChangeStatus.MODIFIED),
    )
    assert detect_scope(files) == "users"
