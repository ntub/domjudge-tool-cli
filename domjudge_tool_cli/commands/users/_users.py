import asyncio

import typer

from typing import Optional, List, Any
from enum import Enum

from tablib import Dataset

from domjudge_tool_cli.models import User, DomServerClient, CreateUser
from domjudge_tool_cli.services.v4 import UsersAPI, DomServerWeb
from domjudge_tool_cli.utils.password import gen_password


def gen_user_dataset(users: List[Any]) -> Dataset:
    dataset = Dataset()
    for idx, user in enumerate(users):
        if idx == 0:
            dataset.headers = user.dict().keys()

        dataset.append(user.dict().values())

    return dataset


class UserExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"

    def export(
        self,
        users: List[Any],
        file: Optional[typer.FileBinaryWrite] = None,
        name: Optional[str] = None,
    ) -> str:
        dataset = gen_user_dataset(users)
        if file:
            file.write(dataset.export(self.value))
            return file.name
        else:
            if not name:
                name = f"export_users.{self.value}"
            else:
                name = f"{name}.{self.value}"

            with open(name, "w") as f:
                f.write(dataset.export(self.value))
                return name


def print_users_table(users: List[User]):
    dataset = gen_user_dataset(users)
    for rm_key in ["last_login_time", "first_login_time", "roles", "last_ip", "ip"]:
        del dataset[rm_key]
    typer.echo(dataset.export("cli", tablefmt="simple"))


async def get_users(
    client: DomServerClient,
    ids: Optional[List[str]] = None,
    team_id: Optional[str] = None,
    format: Optional[UserExportFormat] = None,
    file: Optional[typer.FileBinaryWrite] = None,
):
    async with UsersAPI(**client.api_params) as api:
        users = await api.all_users(ids, team_id)

    if ids:
        users = list(filter(lambda obj: obj.id in ids, users))

    if team_id:
        users = list(filter(lambda obj: obj.team_id == team_id, users))

    if format:
        format.export(users, file)
    else:
        print_users_table(users)


async def get_user(
    client: DomServerClient,
    id: str,
):
    async with UsersAPI(**client.api_params) as api:
        user = await api.get_user(id)
    print_users_table([user])


async def create_team_and_user(
    client: DomServerClient,
    user: CreateUser,
    category_id: Optional[int] = None,
    affiliation_id: Optional[int] = None,
    user_roles: Optional[List[int]] = None,
    enabled: bool = True,
    password_length: Optional[int] = None,
    password_pattern: Optional[str] = None,
) -> CreateUser:
    if not category_id:
        category_id = client.category_id

    if not affiliation_id:
        affiliation_id = client.affiliation_id

    if not user_roles:
        user_roles = client.user_roles

    if not user.password:
        user.password = gen_password(password_length, password_pattern)

    async with DomServerWeb(**client.api_params) as web:
        await web.login()
        team_id, user_id = await web.create_team_and_user(
            user,
            category_id,
            affiliation_id,
            enabled,
        )
        await web.set_user_password(user_id, user.password, user_roles, enabled)

        return user


async def create_teams_and_users(
    client: DomServerClient,
    file: typer.FileText,
    category_id: Optional[int] = None,
    affiliation_id: Optional[int] = None,
    user_roles: Optional[List[int]] = None,
    enabled: bool = True,
    format: Optional[UserExportFormat] = None,
    ignore_existing: bool = False,
    delete_existing: bool = False,
    password_length: Optional[int] = None,
    password_pattern: Optional[str] = None,
) -> None:
    # api = UsersAPI(**client.api_params)
    # users = await api.all_users()

    if not format:
        format = UserExportFormat.CSV

    users_requests = []
    users = []
    dataset = Dataset().load(file, format=format.value)
    for item in dataset.dict:
        user = CreateUser(**item)
        users.append(user)
        users_requests.append(
            create_team_and_user(
                client,
                user,
                category_id,
                affiliation_id,
                user_roles,
                enabled,
                password_length,
                password_pattern,
            ),
        )

    new_users = []
    with typer.progressbar(
            asyncio.as_completed(users_requests),
            length=len(users_requests),
    ) as progress:
        for task in progress:
            it = await task
            new_users.append(it)

    file_name = format.export(new_users, name="import-users-teams-out")
    typer.echo(file_name)

