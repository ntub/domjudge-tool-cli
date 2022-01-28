import asyncio
from typing import List, Optional

import typer

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config

from ._submissions import (download_contest_files, download_submission_files,
                           get_submissions)

app = typer.Typer()


@app.command()
def submission_list(
    cid: str,
    language_id: Optional[str] = None,
    strict: Optional[bool] = False,
    ids: Optional[List[str]] = None,
):
    submission_ids = None
    if ids:
        submission_ids = ids.split(",")

    client = get_or_ask_config(general_state["config"])
    asyncio.run(get_submissions(client, cid, language_id, strict, submission_ids))


@app.command()
def submission_file(
    cid: str,
    id: str,
    mode: int = 2,
    path: Optional[str] = None,
    strict: Optional[bool] = False,
):
    client = get_or_ask_config(general_state["config"])
    asyncio.run(download_submission_files(client, cid, id, mode, path, strict))


@app.command()
def contest_files(
    cid: str,
    mode: int = 2,
    path: Optional[str] = None,
):
    client = get_or_ask_config(general_state["config"])
    asyncio.run(download_contest_files(client, cid, mode, path))
