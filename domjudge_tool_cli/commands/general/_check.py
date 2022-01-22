from pathlib import Path
from typing import Any, Dict, Optional

import typer

from domjudge_tool_cli.models import DomServerClient
from domjudge_tool_cli.services.v4 import DomServerWeb, GeneralAPI


async def get_version(client: DomServerClient):
    async with GeneralAPI(**client.api_params) as api:
        version = await api.version()
    message = typer.style(
        f"Success connect API v{version}.",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo(message)


async def check_login_website(client: DomServerClient):
    async with DomServerWeb(**client.api_params) as web:
        await web.login()
        message = typer.style(
            f"Success connect DomJudge website.",
            fg=typer.colors.GREEN,
            bold=True,
        )
        typer.echo(message)


def create_config(
    host: str,
    username: str,
    password: str,
    disable_ssl: bool = typer.Option(False),
    timeout: Optional[float] = None,
    max_connections: Optional[int] = None,
    max_keepalive_connections: Optional[int] = None,
) -> DomServerClient:
    typer.echo("*" * len(password))
    dom_server = DomServerClient(
        host=host,
        username=username,
        password=password,
        disable_ssl=disable_ssl or False,
        timeout=timeout,
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
    )
    with open("domserver.json", "wb+") as f:
        f.write(dom_server.json().encode())
        typer.echo("Success config Dom Server.")

    return dom_server


def read_config(path: Optional[Path] = None) -> DomServerClient:
    if not path:
        path = Path("domserver.json")

    if path.exists() and path.is_file():
        client = DomServerClient.parse_file(path)
        return client

    raise FileNotFoundError(path)


def update_config(
    dom_server: DomServerClient,
    **kwargs: Dict[str, Any],
) -> DomServerClient:
    for k, v in kwargs.items():
        if hasattr(dom_server, k):
            setattr(dom_server, k, v)

    with open("domserver.json", "wb+") as f:
        f.write(dom_server.json().encode())
        typer.echo("Success update config.")

    return dom_server
