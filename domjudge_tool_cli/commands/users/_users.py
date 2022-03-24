from enum import Enum
from typing import Any, Dict, List, Optional, Union

import typer
from tablib import Dataset

from domjudge_tool_cli.models import CreateUser, DomServerClient, User
from domjudge_tool_cli.services.v4 import DomServerWeb, UsersAPI
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
    user: Union[CreateUser, User],
    category_id: Optional[int] = None,
    affiliation_id: Optional[int] = None,
    user_roles: Optional[List[int]] = None,
    enabled: bool = True,
    password_length: Optional[int] = None,
    password_pattern: Optional[str] = None,
) -> CreateUser:
    if not category_id:
        category_id = client.category_id

    if not user_roles:
        user_roles = client.user_roles

    if not user.password:
        user.password = gen_password(password_length, password_pattern)

    async with DomServerWeb(**client.api_params) as web:
        await web.login()
        if not affiliation_id and not user.affiliation:
            affiliation_id = client.affiliation_id
        elif user.affiliation:
            affiliation = await web.get_affiliation(user.affiliation)

            if affiliation:
                affiliation_id = affiliation.id
            else:
                name = user.affiliation
                affiliation = await web.create_affiliation(
                    name,
                    name,
                    client.affiliation_country,
                )
                affiliation_id = affiliation.id

        if isinstance(user, User):
            team_id, user_id = await web.update_team(
                user,
                category_id,
                affiliation_id,
                enabled,
            )
            user = CreateUser.from_user(user)
        else:
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
    async with UsersAPI(**client.api_params) as api:
        users = await api.all_users()

    existing_users: Dict[str, User] = {it.username.lower(): it for it in users}

    if not format:
        format = UserExportFormat.CSV

    input_file = file
    if format == UserExportFormat.CSV:
        input_file = file.read().replace("\ufeff", "")

    users = []
    delete_users = []
    dataset = Dataset().load(input_file, format=format.value)

    for item in dataset.dict:
        item["email"] = None if not item.get("email") else item["email"]
        user = CreateUser(**item)

        username = user.username.lower()
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
        async with DomServerWeb(**client.api_params) as web:
            await web.login()
            typer.echo("Delete existing users.")
            await web.delete_users(delete_users)
            typer.echo("Delete existing teams.")
            await web.delete_teams(delete_users)

    new_users = []
    with typer.progressbar(users) as progress:
        for user in progress:
            new_user = await create_team_and_user(
                client,
                user,
                category_id,
                affiliation_id,
                user_roles,
                enabled,
                password_length,
                password_pattern,
            )
            new_users.append(new_user)

    if new_users:
        file_name = format.export(new_users, name="import-users-teams-out")
        typer.echo(file_name)


async def delete_teams_and_users(
    client: DomServerClient,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> None:
    default_ignore_users = ["admin", "judgehost", client.username]

    async with UsersAPI(**client.api_params) as api:
        users = await api.all_users()

    existing_users = [it.username for it in users]

    if not exclude:
        exclude = default_ignore_users

    if not include:
        include = existing_users

    if include:
        include = list(
            filter(
                lambda it: it not in default_ignore_users,
                include,
            )
        )

    async with DomServerWeb(**client.api_params) as web:
        await web.login()
        typer.echo("Delete users.")
        await web.delete_users(include, exclude)
        typer.echo("Delete teams.")
        await web.delete_teams(include, exclude)
