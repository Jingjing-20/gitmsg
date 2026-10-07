from typer.testing import CliRunner

from gitmsg import __version__
from gitmsg.cli import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "staged Git changes" in result.output
    assert "--version" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"gitmsg {__version__}" in result.output
