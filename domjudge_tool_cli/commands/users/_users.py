from enum import StrEnum
from typing import Any

import typer
from tablib import Dataset

from domjudge_tool_cli.models import CreateUser, DomServerClient, User
from domjudge_tool_cli.services.api.v4 import UsersAPI
from domjudge_tool_cli.services.web import DomServerWebGateway
from domjudge_tool_cli.utils.password import gen_password


def gen_user_dataset(users: list[Any]) -> Dataset:
    dataset = Dataset()
    for idx, user in enumerate(users):
        user_dict = user.model_dump()
        if idx == 0:
            dataset.headers = list(user_dict.keys())

        dataset.append(list(user_dict.values()))

    return dataset


class UserExportFormat(StrEnum):
    JSON = "json"
    CSV = "csv"

    def export(
        self,
        users: list[Any],
        file: typer.FileTextWrite | None = None,
        name: str | None = None,
    ) -> str:
        dataset = gen_user_dataset(users)
        exported = dataset.export(self.value)
        text_content = exported if isinstance(exported, str) else str(exported)
        if file:
            file.write(text_content)
            return getattr(file, "name", "output")
        else:
            if not name:
                filename = f"export_users.{self.value}"
            else:
                filename = f"{name}.{self.value}"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(text_content)
                return filename


def print_users_table(users: list[User]) -> None:
    dataset = gen_user_dataset(users)
    for user_row in dataset:
        roles_index = dataset.headers.index("roles")
        dataset[roles_index] = ",".join(user_row[roles_index])

    typer.echo(dataset.export("cli", tablefmt="simple"))


async def get_users(
    client: DomServerClient,
    ids: list[str] | None = None,
    team_id: str | None = None,
    format: UserExportFormat | None = None,
    file: typer.FileTextWrite | None = None,
) -> None:
    async with UsersAPI(**client.api_params) as api:
        users = await api.all_users(ids, team_id)

    if ids:
        users = [obj for obj in users if obj.id in ids]

    if team_id:
        users = [obj for obj in users if obj.team_id == team_id]

    if format:
        format.export(users, file)
    else:
        print_users_table(users)


async def get_user(
    client: DomServerClient,
    id: str,
) -> None:
    async with UsersAPI(**client.api_params) as api:
        user = await api.get_user(id)
    print_users_table([user])


async def create_team_and_user(
    client: DomServerClient,
    user: CreateUser,
    category_id: int,
    affiliation_id: int,
    user_roles: list[int],
    enabled: bool = True,
    password_length: int = 10,
    password_pattern: str | None = None,
    new_password: bool = False,
) -> CreateUser:
    if not category_id:
        raise ValueError("Missing category_id")

    if not affiliation_id:
        raise ValueError("Missing affiliation_id")

    if not user_roles:
        raise ValueError("Missing user_roles")

    DomServerWeb = DomServerWebGateway(client.version)
    async with DomServerWeb(**client.api_params) as web:
        await web.login()

        if user.is_exist:
            user_model = User(**user.model_dump())
            team_id, user_id = await web.update_team(
                user_model,
                category_id,
                affiliation_id,
                enabled,
            )
        else:
            team_id, user_id = await web.create_team_and_user(
                user,
                category_id,
                affiliation_id,
                enabled,
            )

        if not user.password or new_password:
            password = gen_password(password_length, password_pattern)
            await web.set_user_password(
                user_id,
                password,
                user_roles,
                enabled,
            )
            user.password = password

        return user


async def create_teams_and_users(
    client: DomServerClient,
    file: typer.FileText,
    category_id: int,
    affiliation_id: int,
    user_roles: list[int],
    enabled: bool = True,
    format: UserExportFormat | None = None,
    delete_existing: bool = False,
    ignore_existing: bool = False,
    password_length: int = 10,
    password_pattern: str | None = None,
    new_password: bool = False,
) -> None:
    async with UsersAPI(**client.api_params) as api:
        existing_list = await api.all_users()

    existing_users: dict[str, User] = {it.username: it for it in existing_list}

    if not format:
        format = UserExportFormat.CSV

    input_file: Any = file
    if format == UserExportFormat.CSV:
        input_file = file.read().replace("\ufeff", "")

    users: list[Any] = []
    delete_users: list[str] = []
    dataset = Dataset().load(input_file, format=format.value)

    for item in dataset.dict:
        item["email"] = None if not item.get("email") else item["email"]
        user = CreateUser(**item)

        username = user.username
        if username in existing_users:
            existing_user = existing_users[username]

            if delete_existing:
                delete_users.append(existing_user.username)

            if ignore_existing:
                typer.echo(f"User {user.username} is ignored")
                continue

            if not delete_existing and not ignore_existing:
                existing_user.update(**item)
                users.append(existing_user)
                continue

        users.append(user)

    if delete_users:
        delete_teams = [
            existing_users[username].team_id
            for username in delete_users
            if existing_users[username].team_id
        ]
        DomServerWeb = DomServerWebGateway(client.version)
        async with DomServerWeb(**client.api_params) as web:
            await web.login()
            typer.echo("Delete existing users.")
            await web.delete_users(delete_users)
            typer.echo("Delete existing teams.")
            await web.delete_teams([t for t in delete_teams if t])

    new_users: list[CreateUser] = []
    with typer.progressbar(users) as progress:
        for user_obj in progress:
            new_user = await create_team_and_user(
                client,
                user_obj,
                category_id,
                affiliation_id,
                user_roles,
                enabled,
                password_length,
                password_pattern,
                new_password,
            )
            new_users.append(new_user)

    if new_users:
        file_name = format.export(new_users, name="import-users-teams-out")
        typer.echo(file_name)


async def delete_teams_and_users(
    client: DomServerClient,
    delete_users: list[str],
    delete_teams: list[str],
) -> None:
    default_ignore_users = ["admin", "judgehost", client.username]
    delete_users_set = {it for it in delete_users if it not in default_ignore_users}

    DomServerWeb = DomServerWebGateway(client.version)
    async with DomServerWeb(**client.api_params) as web:
        await web.login()
        typer.echo(f"Delete existing users: {','.join(delete_users_set)}")
        await web.delete_users(list(delete_users_set))
        typer.echo(f"Delete existing teams: {','.join(delete_teams)}")
        await web.delete_teams(delete_teams)
