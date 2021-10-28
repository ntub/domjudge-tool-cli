import os

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


@app.command()
def import_users_teams_example():
    import domjudge_tool_cli

    file_name = "import-users-teams.csv"
    file_path = os.path.join(
        domjudge_tool_cli.__path__[0],
        "templates",
        "csv",
        file_name,
    )
    new_file_path = os.path.join(os.getcwd(), file_name)
    with open(file_path, encoding='utf-8') as template_file:
        content = template_file.read()

    with open(new_file_path, 'w', encoding='utf-8') as file:
        file.write(content)

    typer.echo(new_file_path)