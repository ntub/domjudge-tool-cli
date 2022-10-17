import asyncio
from typing import List, Optional

import typer

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config
from domjudge_tool_cli.commands.problems._problems import download_problems_zips

app = typer.Typer()


@app.command()
def download_problems(
    exclude: Optional[List[str]] = typer.Option(None, help="ex: problemId1,problemId2"),
    only: Optional[List[str]] = typer.Option(None, help="ex: problemId1,problemId2"),
    folder: Optional[str] = typer.Option(
        None,
        help="Export folder name",
    ),
):
    if len(exclude) == 1 and isinstance(exclude[0], str):
        exclude = exclude[0].split(",")

    if len(only) == 1 and isinstance(only[0], str):
        only = only[0].split(",")

    client = get_or_ask_config(general_state["config"])
    asyncio.run(download_problems_zips(client, exclude, only, folder))
