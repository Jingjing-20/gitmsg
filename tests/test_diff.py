from __future__ import annotations

from pathlib import Path

from tests.conftest import run_git as repo_git

from gitmsg.diff import (
    language_for,
    parse_name_status,
    parse_numstat,
    parse_staged_changes,
    parse_staged_metadata,
    split_rename_path,
)
from gitmsg.models import ChangeStatus


def test_language_for_common_extensions() -> None:
    assert language_for("src/app.py") == "Python"
    assert language_for("src/app.ts") == "TypeScript"
    assert language_for("README.md") == "Markdown"
    assert language_for("unknown.xyz") == "unknown"


def test_split_rename_path_with_braces() -> None:
    old, new = split_rename_path("src/{old => new}/file.py")
    assert old == "src/old/file.py"
    assert new == "src/new/file.py"


def test_parse_name_status_and_numstat_added_modified_deleted() -> None:
    name_status = "A\tsrc/new.py\nM\tsrc/app.py\nD\tdocs/old.md\n"
    numstat = "12\t0\tsrc/new.py\n4\t2\tsrc/app.py\n0\t20\tdocs/old.md\n"
    parsed = parse_staged_metadata(name_status, numstat)
    assert parsed.stats.files_changed == 3
    assert parsed.stats.insertions == 16
    assert parsed.stats.deletions == 22
    by_path = {file.path: file for file in parsed.files}
    assert by_path["src/new.py"].status == ChangeStatus.ADDED
    assert by_path["src/app.py"].status == ChangeStatus.MODIFIED
    assert by_path["docs/old.md"].status == ChangeStatus.DELETED
    assert by_path["src/new.py"].language == "Python"


def test_parse_rename_and_binary() -> None:
    name_status = "R100\tsrc/old.py\tsrc/new.py\nA\tassets/logo.png\n"
    numstat = "0\t0\tsrc/{old => new}.py\n-\t-\tassets/logo.png\n"
    parsed = parse_staged_metadata(name_status, numstat)
    renamed = next(file for file in parsed.files if file.status == ChangeStatus.RENAMED)
    binary = next(file for file in parsed.files if file.path == "assets/logo.png")
    assert renamed.path == "src/new.py"
    assert renamed.old_path == "src/old.py"
    assert renamed.similarity == 100
    assert binary.is_binary is True
    assert parsed.stats.insertions == 0
    assert parsed.stats.files_changed == 2


def test_parse_name_status_copied_file() -> None:
    files = parse_name_status("C080\tlib/util.py\tlib/util_copy.py\n")
    assert files[0].status == ChangeStatus.COPIED
    assert files[0].old_path == "lib/util.py"
    assert files[0].similarity == 80


def test_parse_numstat_rename_without_braces() -> None:
    stats = parse_numstat("3\t1\told.py => new.py\n")
    assert stats["new.py"] == (3, 1, False)


def test_parse_staged_changes_from_git_repo(git_repo: Path) -> None:
    (git_repo / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (git_repo / "README.md").write_text("# Title\n", encoding="utf-8")
    repo_git(["add", "app.py", "README.md"], cwd=git_repo)
    repo_git(["commit", "-m", "initial"], cwd=git_repo)

    (git_repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (git_repo / "new.py").write_text("def added():\n    return 1\n", encoding="utf-8")
    (git_repo / "README.md").unlink()
    repo_git(["add", "-A"], cwd=git_repo)

    parsed = parse_staged_changes(git_repo)
    by_path = {file.path: file for file in parsed.files}
    assert parsed.stats.files_changed == 3
    assert by_path["new.py"].status == ChangeStatus.ADDED
    assert by_path["app.py"].status == ChangeStatus.MODIFIED
    assert by_path["README.md"].status == ChangeStatus.DELETED
    assert parsed.stats.insertions > 0
    assert parsed.stats.deletions > 0
    assert "new.py" in parsed.raw


def test_parse_staged_rename_in_git_repo(git_repo: Path) -> None:
    (git_repo / "old_name.py").write_text("value = 1\n", encoding="utf-8")
    repo_git(["add", "old_name.py"], cwd=git_repo)
    repo_git(["commit", "-m", "initial"], cwd=git_repo)
    repo_git(["mv", "old_name.py", "new_name.py"], cwd=git_repo)

    parsed = parse_staged_changes(git_repo)
    assert len(parsed.files) == 1
    file = parsed.files[0]
    assert file.status == ChangeStatus.RENAMED
    assert file.path == "new_name.py"
    assert file.old_path == "old_name.py"


def test_parse_staged_binary_file(git_repo: Path) -> None:
    (git_repo / "blob.bin").write_bytes(bytes(range(256)))
    repo_git(["add", "blob.bin"], cwd=git_repo)
    parsed = parse_staged_changes(git_repo)
    assert parsed.files[0].is_binary is True
    assert parsed.files[0].status == ChangeStatus.ADDED
