import asyncio
from typing import List, Optional

import typer

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config
from domjudge_tool_cli.commands.problems._problems import \
    download_problems_zips

app = typer.Typer()


@app.command()
def download_problems(
    exclude: Optional[List[str]] = typer.Option(None),
    folder: Optional[str] = typer.Option(
        None,
        help="Export folder name",
    ),
):
    client = get_or_ask_config(general_state["config"])
    asyncio.run(download_problems_zips(client, exclude, folder))
