"""Command-line interface for GitMsg."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from gitmsg import __version__
from gitmsg.analyzer import analyze
from gitmsg.classifier import alternative_classifications, classify
from gitmsg.clipboard import copy_text
from gitmsg.config import init_config, load_config
from gitmsg.diff import parse_staged_changes
from gitmsg.exceptions import GitMsgError
from gitmsg.generator import generate
from gitmsg.git import find_repo_root, has_staged_changes
from gitmsg.models import (
    AnalysisResult,
    Classification,
    GeneratedMessage,
    GitMsgConfig,
)

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)

app = typer.Typer(
    name="gitmsg",
    help="Generate Conventional Commit messages from staged Git changes.",
    add_completion=False,
    no_args_is_help=False,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
)


@dataclass(frozen=True)
class PipelineResult:
    repo_root: Path
    config: GitMsgConfig
    analysis: AnalysisResult
    classification: Classification
    message: GeneratedMessage
    alternatives: tuple[GeneratedMessage, ...]


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"gitmsg {__version__}")
        raise typer.Exit()


def _print_no_staged_changes() -> None:
    console.print("No staged changes found.\n")
    console.print("Stage your changes first:\n")
    console.print("  git add <files>")


def _print_analysis(analysis: AnalysisResult) -> None:
    stats = analysis.parsed.stats
    console.print("GitMsg\n")
    console.print("Analyzing staged changes...\n")
    console.print(f"Files changed: {stats.files_changed}")
    console.print(f"Insertions: +{stats.insertions}")
    console.print(f"Deletions: -{stats.deletions}\n")
    if analysis.summaries:
        console.print("Detected changes:")
        for summary in analysis.summaries:
            console.print(f"  • {summary}")
        console.print()
    if analysis.mixed_notice:
        console.print(f"{analysis.mixed_notice}\n")


def _print_classification(classification: Classification) -> None:
    console.print(f"Change type: {classification.change_type}")
    console.print(f"Scope: {classification.scope or '(none)'}")
    console.print(f"Confidence: {classification.confidence}%\n")


def _print_message(message: GeneratedMessage) -> None:
    console.print("Suggested commit:\n")
    console.print(f"  {message.full}\n")


def run_pipeline(cwd: Path | str | None = None) -> PipelineResult:
    repo_root = find_repo_root(cwd)
    config = load_config(repo_root)
    if not has_staged_changes(repo_root):
        _print_no_staged_changes()
        raise typer.Exit(0)
    analysis = analyze(parse_staged_changes(repo_root))
    classification = classify(analysis, default_scope=config.default_scope)
    message = generate(
        analysis,
        classification,
        max_length=config.max_message_length,
    )
    alternatives: list[GeneratedMessage] = []
    for alt in alternative_classifications(
        analysis,
        classification,
        default_scope=config.default_scope,
    ):
        generated = generate(
            analysis,
            alt,
            max_length=config.max_message_length,
        )
        if generated.full != message.full:
            alternatives.append(generated)
    return PipelineResult(
        repo_root=repo_root,
        config=config,
        analysis=analysis,
        classification=classification,
        message=message,
        alternatives=tuple(alternatives),
    )


def _copy_message(message: GeneratedMessage, *, enabled: bool) -> None:
    if not enabled:
        return
    if copy_text(message.full):
        console.print("✓ Copied to clipboard")
        return
    console.print("Could not copy to clipboard.\n")
    console.print("Suggested commit:\n")
    console.print(f"  {message.full}")


def _select_suggestion(
    primary: GeneratedMessage,
    alternatives: tuple[GeneratedMessage, ...],
) -> GeneratedMessage:
    candidates = (primary, *alternatives)
    unique: list[GeneratedMessage] = []
    seen: set[str] = set()
    for item in candidates:
        if item.full in seen:
            continue
        seen.add(item.full)
        unique.append(item)
    if len(unique) == 1:
        return unique[0]

    console.print("Suggested commits:\n")
    for index, item in enumerate(unique, start=1):
        console.print(f"{index}. {item.full}")
    console.print()

    if not sys.stdin.isatty():
        return unique[0]

    choice = typer.prompt("Select", default=1, type=int)
    if choice < 1 or choice > len(unique):
        err_console.print("Invalid selection; using the first suggestion.")
        return unique[0]
    return unique[choice - 1]


def execute(
    *,
    analyze_only: bool = False,
    dry_run: bool = False,
    suggest: bool = False,
    cwd: Path | str | None = None,
) -> None:
    try:
        result = run_pipeline(cwd)
    except GitMsgError as exc:
        err_console.print(str(exc))
        raise typer.Exit(1) from exc
    _print_analysis(result.analysis)
    if analyze_only:
        console.print(f"Change type: {result.classification.change_type}")
        console.print(f"Scope: {result.classification.scope or '(none)'}")
        console.print(f"Confidence: {result.classification.confidence}%")
        return

    _print_classification(result.classification)
    selected = result.message
    if suggest:
        selected = _select_suggestion(result.message, result.alternatives)
        if selected is not result.message or result.alternatives:
            console.print(f"Suggested commit:\n\n  {selected.full}\n")
        else:
            _print_message(selected)
    else:
        _print_message(selected)

    should_copy = result.config.copy_to_clipboard and not dry_run
    _copy_message(selected, enabled=should_copy)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the GitMsg version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
    analyze_mode: Annotated[
        bool,
        typer.Option(
            "--analyze",
            help="Show analysis only; do not generate a commit message.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Generate a message without copying it to the clipboard.",
        ),
    ] = False,
    suggest: Annotated[
        bool,
        typer.Option(
            "--suggest",
            help="Show alternative commit messages when useful.",
        ),
    ] = False,
) -> None:
    """Analyze staged Git changes and suggest a Conventional Commit message."""
    if ctx.invoked_subcommand is not None:
        return
    execute(analyze_only=analyze_mode, dry_run=dry_run, suggest=suggest)


@app.command("init")
def init_command() -> None:
    """Create optional `.gitmsg/config.toml` in the current repository."""
    try:
        repo_root = find_repo_root()
        path = init_config(repo_root)
    except GitMsgError as exc:
        err_console.print(str(exc))
        raise typer.Exit(1) from exc
    console.print(f"Wrote {path}")
    console.print("Added .gitmsg/ to .gitignore if it was missing.")


def run() -> None:
    """Console-script entry point with application-level error handling."""
    try:
        app()
    except GitMsgError as exc:
        err_console.print(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    run()
