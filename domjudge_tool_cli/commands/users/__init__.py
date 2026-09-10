import asyncio
import importlib.resources
import os
from typing import Annotated

import typer

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config
from domjudge_tool_cli.commands.users._users import (
    UserExportFormat,
    create_teams_and_users,
    delete_teams_and_users,
    get_user,
    get_users,
)

__all__ = [
    "user_list",
    "user",
    "import_users_teams_example",
    "import_users_teams",
    "rm_teams_and_users",
]


app = typer.Typer()


@app.command()
def user_list(
    ids: Annotated[
        str | None,
        typer.Option(help="user_id1,user_id2,user_id3"),
    ] = None,
    team_id: Annotated[str | None, typer.Option(help="Team id")] = None,
    format: Annotated[
        UserExportFormat | None,
        typer.Option(help="Export file format."),
    ] = None,
    file: Annotated[
        typer.FileTextWrite | None,
        typer.Option(help="Export file name"),
    ] = None,
) -> None:
    """
    Get DOMjudge users info.
    """
    user_ids = ids.split(",") if ids else None

    client = get_or_ask_config(general_state["config"])
    asyncio.run(get_users(client, user_ids, team_id, format, file))


@app.command()
def user(id: Annotated[str, typer.Argument(help="User id.")]) -> None:
    """
    Get DOMjudge user info by ID.
    """
    client = get_or_ask_config(general_state["config"])
    asyncio.run(get_user(client, id))


@app.command()
def import_users_teams_example() -> None:
    """
    Import users and teams example csv file.
    """
    file_name = "import-users-teams.csv"
    template_resource = importlib.resources.files("domjudge_tool_cli").joinpath(
        "templates", "csv", file_name
    )
    content = template_resource.read_text(encoding="utf-8")
    new_file_path = os.path.join(os.getcwd(), file_name)
    with open(new_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    typer.echo(new_file_path)


@app.command()
def import_users_teams(
    file: Annotated[typer.FileText, typer.Argument(help="Users CSV file.")],
    category_id: Annotated[int | None, typer.Option(help="Category ID")] = None,
    affiliation_id: Annotated[int | None, typer.Option(help="Affiliation ID")] = None,
    user_roles: Annotated[
        list[int] | None,
        typer.Option(help="Roles ID, default is 3 (Team Member)"),
    ] = None,
    enabled: Annotated[bool, typer.Option(help="User and team is enabled?")] = True,
    format: Annotated[
        UserExportFormat | None,
        typer.Option(help="File format, default is CSV"),
    ] = None,
    delete_existing: Annotated[
        bool,
        typer.Option(help="Delete existing users and teams"),
    ] = False,
    ignore_existing: Annotated[
        bool,
        typer.Option(help="Ignore existing users and teams"),
    ] = False,
    password_length: Annotated[int, typer.Option(help="Generate password length")] = 10,
    password_pattern: Annotated[
        str | None,
        typer.Option(help="Generate password pattern"),
    ] = None,
    new_password: Annotated[
        bool,
        typer.Option(help="Set new password for existing user"),
    ] = False,
) -> None:
    client = get_or_ask_config(general_state["config"])
    category_id = category_id or client.category_id
    affiliation_id = affiliation_id or client.affiliation_id
    user_roles = user_roles or client.user_roles

    if category_id is None:
        raise ValueError("Missing category_id")

    if affiliation_id is None:
        raise ValueError("Missing affiliation_id")

    if user_roles is None:
        raise ValueError("Missing user_roles")

    asyncio.run(
        create_teams_and_users(
            client,
            file,
            category_id,
            affiliation_id,
            user_roles,
            enabled,
            format,
            delete_existing,
            ignore_existing,
            password_length,
            password_pattern,
            new_password,
        )
    )


@app.command()
def rm_teams_and_users(
    delete_users: Annotated[
        list[str],
        typer.Option("--user", help="Delete user usernames"),
    ],
    delete_teams: Annotated[
        list[str],
        typer.Option("--team", help="Delete team ids"),
    ],
) -> None:
    client = get_or_ask_config(general_state["config"])
    asyncio.run(
        delete_teams_and_users(
            client,
            delete_users,
            delete_teams,
        )
    )
