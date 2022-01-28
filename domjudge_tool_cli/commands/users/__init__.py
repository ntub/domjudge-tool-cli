import asyncio
import os
from typing import List, Optional

import typer

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config

from ._users import (UserExportFormat, create_teams_and_users,
                     delete_teams_and_users, get_user, get_users)

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
    ),
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
    with open(file_path, encoding="utf-8") as template_file:
        content = template_file.read()

    with open(new_file_path, "w", encoding="utf-8") as file:
        file.write(content)

    typer.echo(new_file_path)


@app.command()
def import_users_teams(
    file: typer.FileText = typer.Argument(...),
    category_id: Optional[int] = typer.Option(None),
    affiliation_id: Optional[int] = typer.Option(None),
    user_roles: Optional[List[int]] = typer.Option(None),
    enabled: bool = typer.Option(True),
    format: Optional[UserExportFormat] = None,
    ignore_existing: bool = typer.Option(False),
    delete_existing: bool = typer.Option(False),
    password_length: Optional[int] = typer.Option(None),
    password_pattern: Optional[str] = typer.Option(None),
):
    client = get_or_ask_config(general_state["config"])
    asyncio.run(
        create_teams_and_users(
            client,
            file,
            category_id,
            affiliation_id,
            user_roles,
            enabled,
            format,
            ignore_existing,
            delete_existing,
            password_length,
            password_pattern,
        ),
    )


@app.command()
def rm_teams_and_users(
    include: Optional[List[str]] = typer.Option(None),
    exclude: Optional[List[str]] = typer.Option(None),
):
    client = get_or_ask_config(general_state["config"])
    asyncio.run(
        delete_teams_and_users(
            client,
            include,
            exclude,
        ),
    )
