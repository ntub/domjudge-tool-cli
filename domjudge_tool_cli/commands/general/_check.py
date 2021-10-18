import typer

from typing import Optional
from pathlib import Path

from domjudge_tool_cli.models import DomServerClient
from domjudge_tool_cli.services.v4 import GeneralAPI


async def get_version(client: DomServerClient):
    api = GeneralAPI(**client.api_params)
    version = await api.version()
    message = typer.style(
        f"Success connect API v{version}.",
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



