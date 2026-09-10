from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from domjudge_tool_cli.models import Affiliation, CreateUser, ProblemItem, User
from domjudge_tool_cli.services.api_client import WebClient


def _get_input_fields(page: str) -> dict[str, str | None]:
    soup = BeautifulSoup(page, "html.parser")
    data: dict[str, str | None] = {}

    for ele in soup.select("input"):
        name = ele.get("name")
        val = ele.get("value")
        if isinstance(name, str):
            data[name] = val if isinstance(val, str) else None

    for tag in soup.select("select"):
        name = tag.get("name")
        if isinstance(name, str):
            option = tag.select_one("option[selected]")
            if option is not None:
                val = option.get("value")
                data[name] = val if isinstance(val, str) else None
            else:
                data[name] = None

    return data


class BaseDomServerWeb(WebClient, ABC):
    @abstractmethod
    async def login(self) -> None: ...

    @abstractmethod
    async def create_team_and_user(
        self,
        user: CreateUser,
        category_id: int,
        affiliation_id: int,
        enabled: bool = True,
    ) -> tuple[str, str]: ...

    @abstractmethod
    async def update_team(
        self,
        user: User,
        category_id: int,
        affiliation_id: int,
        enabled: bool = True,
    ) -> tuple[str, str]: ...

    @abstractmethod
    async def set_user_password(
        self,
        user_id: str,
        password: str,
        user_roles: list[int],
        enabled: bool = True,
    ) -> None: ...

    @abstractmethod
    async def delete_users(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> None: ...

    @abstractmethod
    async def delete_teams(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> None: ...

    @abstractmethod
    async def create_affiliation(
        self,
        shortname: str,
        name: str,
        country: str = "TWN",
    ) -> Affiliation: ...

    @abstractmethod
    async def get_affiliations(self) -> list[Affiliation]: ...

    @abstractmethod
    async def get_affiliation(self, name: str) -> Affiliation | None: ...

    @abstractmethod
    async def get_problems(
        self,
        exclude: list[str] | None = None,
        only: list[str] | None = None,
    ) -> list[ProblemItem]: ...
