import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer

from domjudge_tool_cli.models import DomServerClient
from domjudge_tool_cli.services import SUPPORT_API_VERSIONS, SUPPORT_VERSIONS

from ._check import (
    check_login_website,
    create_config,
    get_version,
    read_config,
    update_config,
)

app = typer.Typer()
general_state: dict[str, Path | None] = {
    "config": None,
}


def ask_want_to_config() -> DomServerClient:
    host = typer.prompt("What's your dom server host URL?", type=str)
    username = typer.prompt(
        "What's your dom server user?",
        help="must be `admin`, `api_reader`, `api_writer` roles.",
        type=str,
    )
    password = typer.prompt(
        "What's your dom server user password?",
        type=str,
        hide_input=True,
    )

    typer.echo("We are support DOMjudge versions: ")
    for idx, version in enumerate(SUPPORT_VERSIONS):
        typer.echo(f"[{idx}] {version}")

    version_idx = typer.prompt(
        "Select your DOMjudge version: ",
        default=0,
        type=int,
    )
    version = SUPPORT_VERSIONS[version_idx]

    typer.echo("We are support DOMjudge API versions: ")
    for idx, api_version in enumerate(SUPPORT_API_VERSIONS):
        typer.echo(f"[{idx}] {api_version}")

    api_version_idx = typer.prompt(
        "Select your DOMjudge API version: ",
        default=0,
        type=int,
    )
    api_version = SUPPORT_API_VERSIONS[api_version_idx]

    disable_ssl = typer.confirm(
        "Disable SSL verification?",
        default=False,
    )

    timeout = typer.prompt(
        "Request timeout (seconds)",
        default=60.0,
        type=float,
    )

    return create_config(
        host=host,
        username=username,
        password=password,
        version=version,
        api_version=api_version,
        disable_ssl=disable_ssl,
        timeout=timeout,
    )


def get_or_ask_config(path: Path | None = None) -> DomServerClient:
    try:
        return read_config(path)
    except FileNotFoundError:
        logging.warning("Not find dom server config file, want to config.")
        return ask_want_to_config()


@app.command()
def check(
    host: Annotated[
        str | None,
        typer.Option(help="Dom server host URL.", show_default=False),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option(
            help="Dom server user, must be `admin`, `api_reader`, `api_writer` roles.",
            show_default=False,
        ),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            help="Dom server user password.",
            show_default=False,
        ),
    ] = None,
) -> None:
    if host and username and password:
        client = DomServerClient(
            host=host,  # type: ignore[arg-type]
            username=username,
            password=password,
        )
    else:
        client = get_or_ask_config(general_state["config"])

    typer.echo(f"Try to connect {client.host}.")
    asyncio.run(get_version(client))
    asyncio.run(check_login_website(client))


@app.command()
def contest_config(
    category_id: Annotated[
        int | None,
        typer.Argument(show_default=False),
    ] = None,
    affiliation_id: Annotated[
        int | None,
        typer.Argument(show_default=False),
    ] = None,
    user_roles: Annotated[
        list[int] | None,
        typer.Option(
            help="ex: role_id,role_id2,role_id3",
            show_default=False,
        ),
    ] = None,
) -> None:
    client = get_or_ask_config(general_state["config"])

    update_config(
        client,
        category_id=category_id,
        affiliation_id=affiliation_id,
        user_roles=user_roles,
    )


@app.command()
def config(
    host: Annotated[str, typer.Argument(help="Dom server host URL.")],
    username: Annotated[
        str,
        typer.Option(
            help="Dom server user, must be `admin`, `api_reader`, `api_writer` roles.",
            prompt=True,
        ),
    ],
    password: Annotated[
        str,
        typer.Option(help="Dom server user password.", prompt=True, hide_input=True),
    ],
    version: Annotated[
        str,
        typer.Option(
            help="DOMjudge version, ex: 7.3.2",
            prompt=True,
        ),
    ],
    api_version: Annotated[
        str,
        typer.Option(
            help="DOMjudge API version, ex: v4",
            prompt=True,
        ),
    ],
    disable_ssl: Annotated[bool, typer.Option()] = False,
    timeout: Annotated[float | None, typer.Option()] = None,
    max_connections: Annotated[int | None, typer.Option()] = None,
    max_keepalive_connections: Annotated[int | None, typer.Option()] = None,
) -> None:
    create_config(
        host=host,
        username=username,
        password=password,
        version=version,
        api_version=api_version,
        disable_ssl=disable_ssl,
        timeout=timeout,
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
    )
