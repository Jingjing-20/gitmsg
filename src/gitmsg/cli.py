"""Command-line interface for GitMsg."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

from gitmsg import __version__
from gitmsg.exceptions import GitMsgError

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)

app = typer.Typer(
    name="gitmsg",
    help="Generate Conventional Commit messages from staged Git changes.",
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"gitmsg {__version__}")
        raise typer.Exit()


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
) -> None:
    """Analyze staged Git changes and suggest a Conventional Commit message."""
    if ctx.invoked_subcommand is not None:
        return


def run() -> None:
    """Console-script entry point with application-level error handling."""
    try:
        app()
    except GitMsgError as exc:
        err_console.print(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    run()
