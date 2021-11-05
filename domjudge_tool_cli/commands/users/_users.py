import typer

from typing import Optional, List, Any
from enum import Enum

from tablib import Dataset

from domjudge_tool_cli.models import User, DomServerClient
from domjudge_tool_cli.services.v4 import UsersAPI


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
        file: Optional[typer.FileBinaryWrite],
    ):
        dataset = gen_user_dataset(users)
        if file:
            file.write(dataset.export(self.value))
        else:
            with open(f"export_users.{self.value}", "w") as f:
                f.write(dataset.export(self.value))


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
    api = UsersAPI(**client.api_params)
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
    api = UsersAPI(**client.api_params)
    user = await api.get_user(id)
    print_users_table([user])
