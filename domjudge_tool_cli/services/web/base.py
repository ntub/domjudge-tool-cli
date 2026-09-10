from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from domjudge_tool_cli.models import Affiliation, CreateUser, ProblemItem, User
from domjudge_tool_cli.services.api_client import WebClient


def _get_input_fields(page: str) -> dict[str, str | list[str]]:
    soup = BeautifulSoup(page, "html.parser")
    data: dict[str, str | list[str]] = {}

    for ele in soup.find_all(["input", "textarea", "select"]):
        name = ele.get("name")
        if not isinstance(name, str) or not name:
            continue

        if ele.name == "input":
            type_attr = ele.get("type")
            type_ = type_attr.lower() if isinstance(type_attr, str) else "text"
            if type_ in ("checkbox", "radio"):
                if ele.get("checked") is None:
                    continue
                if ele.has_attr("value"):
                    val = ele.get("value")
                    val_str = val if isinstance(val, str) else ""
                else:
                    val_str = "on"

                if name in data:
                    existing = data[name]
                    if isinstance(existing, list):
                        existing.append(val_str)
                    else:
                        data[name] = [existing, val_str]
                else:
                    data[name] = val_str
            else:
                val = ele.get("value")
                data[name] = val if isinstance(val, str) else ""
        elif ele.name == "textarea":
            data[name] = ele.text
        elif ele.name == "select":
            selected_opts = ele.select("option[selected]")
            if not selected_opts:
                continue
            vals: list[str] = []
            for opt in selected_opts:
                opt_val = opt.get("value")
                vals.append(opt_val if isinstance(opt_val, str) else "")
            if len(vals) == 1:
                data[name] = vals[0]
            else:
                data[name] = vals
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
