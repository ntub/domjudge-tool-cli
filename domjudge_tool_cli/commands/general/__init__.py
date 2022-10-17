import asyncio
import logging
from pathlib import Path
from typing import List, Optional

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
    version_list_text = "\n".join(
        [f"({index}\t{ver})" for index, ver in enumerate(SUPPORT_VERSIONS)]
    )
    version_index = typer.prompt(
        f"Setup DOMjudge version?\n{version_list_text}",
        type=int,
        default=0,
        show_default=True,
    )
    version = SUPPORT_VERSIONS[version_index]
    api_version_list_text = "\n".join(
        [f"({index}\t{ver})" for index, ver in enumerate(SUPPORT_API_VERSIONS)]
    )
    api_version_index = typer.prompt(
        f"Setup DOMjudge API version?\n{api_version_list_text}",
        type=int,
        default=0,
        show_default=True,
    )
    api_version = SUPPORT_API_VERSIONS[api_version_index]
    save = typer.confirm("Are you want to save a config file?")
    if save:
        return create_config(
            host=host,
            username=username,
            password=password,
            version=version,
            api_version=api_version,
            disable_ssl=disable_ssl,
            timeout=timeout,
        )

    return DomServerClient(
        host=host,
        username=username,
        password=password,
        version=version,
        api_version=api_version,
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
    host: Optional[str] = typer.Option(
        None, help="Dom server host URL.", show_default=False
    ),
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

    typer.echo(f"Try to connect {client.host}.")
    asyncio.run(get_version(client))
    asyncio.run(check_login_website(client))


@app.command()
def contest_config(
    category_id: Optional[int] = typer.Argument(None, show_default=False),
    affiliation_id: Optional[int] = typer.Argument(None, show_default=False),
    user_roles: Optional[List[int]] = typer.Option(
        None,
        help="ex: role_id,role_id2,role_id3",
        show_default=False,
    ),
):
    client = get_or_ask_config(general_state["config"])

    update_config(
        client,
        category_id=category_id,
        affiliation_id=affiliation_id,
        user_roles=user_roles,
    )


@app.command()
def config(
    host: str = typer.Argument(..., help="Dom server host URL."),
    username: str = typer.Option(
        ...,
        help="Dom server user, must be `admin`, `api_reader`, `api_writer` roles.",
        prompt=True,
    ),
    password: str = typer.Option(
        ..., help="Dom server user password.", prompt=True, hide_input=True
    ),
    version: str = typer.Option(
        ...,
        help="DOMjudge version, ex: 7.3.2",
        prompt=True,
    ),
    api_version: str = typer.Option(
        ...,
        help="DOMjudge API version, ex: v4",
        prompt=True,
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
        version=version,
        api_version=api_version,
        disable_ssl=disable_ssl,
        timeout=timeout,
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
    )
