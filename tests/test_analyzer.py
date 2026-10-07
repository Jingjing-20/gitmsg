from __future__ import annotations

from gitmsg.analyzer import analyze, categorize_path, humanize_identifier
from gitmsg.diff import parse_staged_metadata
from gitmsg.models import ChangeStatus, DiffStats, FileChange, ParsedDiff


def _parsed(files: list[FileChange], raw: str) -> ParsedDiff:
    return ParsedDiff(
        files=tuple(files),
        stats=DiffStats(files_changed=len(files), insertions=1, deletions=0),
        raw=raw,
    )


def test_humanize_identifier() -> None:
    assert humanize_identifier("add_project_filtering") == "add project filtering"
    assert humanize_identifier("addProjectFiltering") == "add project filtering"


def test_categorize_paths() -> None:
    assert categorize_path("tests/test_users.py") == "tests"
    assert categorize_path("README.md") == "docs"
    assert categorize_path(".github/workflows/ci.yml") == "ci"
    assert categorize_path("package.json") == "dependencies"
    assert categorize_path("alembic/versions/0001_init.py") == "schema"
    assert categorize_path("src/projects.py") == "source"


def test_analyze_added_python_function() -> None:
    raw = """\
diff --git a/src/projects.py b/src/projects.py
index 111..222 100644
--- a/src/projects.py
+++ b/src/projects.py
@@ -1,0 +1,3 @@
+def add_project_filtering():
+    return True
+
"""
    parsed = _parsed(
        [
            FileChange(
                path="src/projects.py",
                status=ChangeStatus.MODIFIED,
                insertions=3,
                extension=".py",
                language="Python",
            )
        ],
        raw,
    )
    result = analyze(parsed)
    assert "Add project filtering" in result.summaries
    assert "source" in result.categories
    assert any(signal.kind == "added_function" for signal in result.signals)


def test_analyze_test_and_docs_files() -> None:
    parsed = parse_staged_metadata(
        "A\ttests/test_users.py\nM\tREADME.md\n",
        "10\t0\ttests/test_users.py\n2\t1\tREADME.md\n",
        raw="",
    )
    result = analyze(parsed)
    assert result.categories == ("tests", "docs")
    assert result.mixed is False


def test_analyze_detects_routes() -> None:
    raw = """\
diff --git a/api.py b/api.py
--- a/api.py
+++ b/api.py
@@ -1,0 +1,2 @@
+@app.get("/users")
+def users():
"""
    parsed = _parsed(
        [
            FileChange(
                path="api.py",
                status=ChangeStatus.MODIFIED,
                insertions=2,
                extension=".py",
                language="Python",
            )
        ],
        raw,
    )
    result = analyze(parsed)
    assert any(signal.kind == "route" for signal in result.signals)


def test_analyze_detects_mixed_changes() -> None:
    parsed = parse_staged_metadata(
        "M\tsrc/auth.py\nM\tREADME.md\nM\tpackage.json\n",
        "4\t1\tsrc/auth.py\n2\t0\tREADME.md\n3\t1\tpackage.json\n",
        raw="",
    )
    result = analyze(parsed)
    assert result.mixed is True
    assert result.mixed_notice is not None
    assert "multiple concerns" in result.mixed_notice


def test_analyze_dependencies_and_ci() -> None:
    parsed = parse_staged_metadata(
        "M\tpyproject.toml\nA\t.github/workflows/test.yml\n",
        "2\t0\tpyproject.toml\n20\t0\t.github/workflows/test.yml\n",
        raw="",
    )
    result = analyze(parsed)
    assert "dependencies" in result.categories
    assert "ci" in result.categories
