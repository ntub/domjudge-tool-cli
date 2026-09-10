import asyncio
from typing import Annotated

import typer

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config
from domjudge_tool_cli.commands.problems._problems import download_problems_zips

app = typer.Typer()


@app.command()
def download_problems(
    exclude: Annotated[
        str | None,
        typer.Option(help="ex: problemId1,problemId2"),
    ] = None,
    only: Annotated[
        str | None,
        typer.Option(help="ex: problemId1,problemId2"),
    ] = None,
    folder: Annotated[
        str | None,
        typer.Option(help="Export folder name"),
    ] = None,
) -> None:
    exclude_list = exclude.split(",") if exclude else None
    only_list = only.split(",") if only else None

    client = get_or_ask_config(general_state["config"])
    asyncio.run(download_problems_zips(client, exclude_list, only_list, folder))
