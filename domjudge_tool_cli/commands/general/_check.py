from pathlib import Path
from typing import Any

import typer

from domjudge_tool_cli.models import DomServerClient
from domjudge_tool_cli.services.api.v4 import GeneralAPI
from domjudge_tool_cli.services.web import DomServerWebGateway


async def get_version(client: DomServerClient) -> None:
    async with GeneralAPI(**client.api_params) as api:
        version = await api.version()
    message = typer.style(
        f"Success connect API v{version}.",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo(message)


async def check_login_website(client: DomServerClient) -> None:
    DomServerWeb = DomServerWebGateway(client.version)
    async with DomServerWeb(**client.api_params) as web:
        await web.login()
        message = typer.style(
            f"Success connect DomJudge {client.version} website.",
            fg=typer.colors.GREEN,
            bold=True,
        )
        typer.echo(message)


def create_config(
    host: str,
    username: str,
    password: str,
    version: str,
    api_version: str,
    disable_ssl: bool = False,
    timeout: float | None = None,
    max_connections: int | None = None,
    max_keepalive_connections: int | None = None,
) -> DomServerClient:
    typer.echo("*" * len(password))
    dom_server = DomServerClient(
        host=host,  # type: ignore[arg-type]
        username=username,
        password=password,
        disable_ssl=disable_ssl,
        timeout=timeout if timeout is not None else 60.0,
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
        version=version,
        api_version=api_version,
    )
    Path("domserver.json").write_text(
        dom_server.model_dump_json(indent=2),
        encoding="utf-8",
    )
    typer.echo("Success config Dom Server.")

    return dom_server


def read_config(path: Path | None = None) -> DomServerClient:
    config_path = path or Path("domserver.json")
    if config_path.exists() and config_path.is_file():
        return DomServerClient.model_validate_json(
            config_path.read_text(encoding="utf-8")
        )

    raise FileNotFoundError(config_path)


def update_config(
    dom_server: DomServerClient,
    **kwargs: Any,
) -> DomServerClient:
    for k, v in kwargs.items():
        if hasattr(dom_server, k):
            setattr(dom_server, k, v)

    Path("domserver.json").write_text(
        dom_server.model_dump_json(indent=2),
        encoding="utf-8",
    )
    typer.echo("Success update config.")

    return dom_server
