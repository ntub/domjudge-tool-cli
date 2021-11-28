import typer

from typing import Optional
from pathlib import Path

from .commands import (
    general,
    users,
    scoreboard,
)

__version__ = "0.1.0"

app = typer.Typer()

app.add_typer(general.app, name="general")
app.add_typer(users.app, name="users")
app.add_typer(scoreboard.app, name="scoreboard")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
    ),
    config: Optional[Path] = typer.Option(
        None,
        help="Dom server config JSON file",
        envvar="DOMSERVER_CONFIG",
    ),
):
    if config:
        if verbose:
            typer.echo(f"Dom server config file: {config}")
        general.general_state["config"] = config
