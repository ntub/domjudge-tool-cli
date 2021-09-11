import typer
import asyncio
import logging

from typing import Optional
from pathlib import Path

from domjudge_tool_cli.models import DomServerClient

from ._check import get_version, create_config, read_config


app = typer.Typer()
general_state = {
    "config": None,
}


def ask_want_to_config():
    host = typer.prompt("What's your dom server host URL?", type=str)
    username = typer.prompt(
        "What's your dom server username?"
        " must be `admin`, `api_reader`, `api_writer` roles.?",
        type=str,
    )
    password = typer.prompt(
        "What's your dom server password?",
        type=str,
        hide_input=True,
    )
    disable_ssl = typer.confirm("Are you want to disable verify the SSL?")
    timeout = typer.prompt(
        "Setup API timeout?",
        type=float,
        default=None,
        show_default=True,
    )
    save = typer.confirm("Are you want to save a config file?")
    if save:
        return create_config(
            host=host,
            username=username,
            password=password,
            disable_ssl=disable_ssl,
            timeout=timeout,
        )

    return DomServerClient(
        host=host,
        username=username,
        password=password,
        disable_ssl=disable_ssl,
        timeout=timeout,
    )


def get_or_ask_config(path: Optional[Path] = None) -> DomServerClient:
    try:
        return read_config(path)
    except Exception as e:
        logging.warning(e)
        return ask_want_to_config()


@app.command()
def check(
    host: Optional[str] = typer.Option(None, help="Dom server host URL.", show_default=False),
    username: Optional[str] = typer.Option(
        None,
        help="Dom server user, must be `admin`, `api_reader`, `api_writer` roles.",
        show_default=False,
    ),
    password: Optional[str] = typer.Option(
        None,
        help="Dom server user password.",
        show_default=False,
    ),
):
    if host and username and password:
        client = DomServerClient(
            host=host,
            username=username,
            password=password,
        )
    else:
        client = get_or_ask_config(general_state["config"])

    asyncio.run(get_version(client))


@app.command()
def config(
    host: str = typer.Argument(..., help="Dom server host URL."),
    username: str = typer.Option(
        ...,
        help="Dom server user, must be `admin`, `api_reader`, `api_writer` roles.",
        prompt=True,
    ),
    password: str = typer.Option(
        ...,
        help="Dom server user password.",
        prompt=True,
        hide_input=True
    ),
    disable_ssl: Optional[bool] = typer.Option(None),
    timeout: Optional[float] = typer.Option(None),
    max_connections: Optional[int] = typer.Option(None),
    max_keepalive_connections: Optional[int] = typer.Option(None),
):
    create_config(
        host=host,
        username=username,
        password=password,
        disable_ssl=disable_ssl,
        timeout=timeout,
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
    )
