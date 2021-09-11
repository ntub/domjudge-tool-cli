import typer
import asyncio

from typing import Optional

from domjudge_tool_cli.commands.general import (
    get_or_ask_config,
    general_state,
)

from ._users import UserExportFormat, get_users, get_user


app = typer.Typer()


@app.command()
def user_list(
    ids: Optional[str] = typer.Option(
        None,
        help="user_id1,user_id2,user_id3",
    ),
    team_id: Optional[str] = None,
    format: Optional[UserExportFormat] = None,
    file: Optional[typer.FileBinaryWrite] = typer.Option(
        None,
        help="Export file name",
    )
):
    user_ids = None
    if ids:
        user_ids = ids.split(",")

    client = get_or_ask_config(general_state["config"])
    asyncio.run(get_users(client, user_ids, team_id, format, file))


@app.command()
def user(id: str):
    client = get_or_ask_config(general_state["config"])
    asyncio.run(get_user(client, id))