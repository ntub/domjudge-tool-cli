import importlib.metadata
from pathlib import Path
from typing import Annotated

import typer

from .commands import emails, general, problems, scoreboard, submissions, users

__version__ = importlib.metadata.version("domjudge-tool-cli")

app = typer.Typer()

app.add_typer(general.app, name="general")
app.add_typer(users.app, name="users")
app.add_typer(scoreboard.app, name="scoreboard")
app.add_typer(submissions.app, name="submissions")
app.add_typer(problems.app, name="problems")
app.add_typer(emails.app, name="emails")


@app.callback()
def main(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
        ),
    ] = False,
    config: Annotated[
        Path | None,
        typer.Option(
            help="Dom server config JSON file",
            envvar="DOMSERVER_CONFIG",
        ),
    ] = None,
) -> None:
    if config:
        if verbose:
            typer.echo(f"Dom server config file: {config}")
        general.general_state["config"] = config
