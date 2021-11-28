import asyncio
from enum import Enum
from typing import Tuple, List, Callable

from bs4 import BeautifulSoup

from domjudge_tool_cli.services.api_client import WebClient
from domjudge_tool_cli.models import CreateUser


class HomePath(str, Enum):
    JURY = "/jury"
    LOGIN = "/login"


class UserPath(str, Enum):
    LIST = "/jury/users"
    ADD = "/jury/users/add"
    EDIT = "/jury/users/%s/edit"


class TeamPath(str, Enum):
    LIST = "/jury/teams"
    ADD = "/jury/teams/add"


def _get_input_fields(page: str) -> dict:
    soup = BeautifulSoup(page, "html.parser")

    data = {ele.get("name"): ele.get("value") for ele in soup.select("input")}

    select_tags = soup.select("select")
    for tag in select_tags:
        option = tag.select_one("option[selected]")
        data[tag.get("name")] = option.get("value") if option else None

    data.pop(None, None)  # remove no name fields
    return data


class DomServerWeb(WebClient):
    async def login(self) -> None:
        login_form = await self.get(HomePath.LOGIN.value)
        data = {
            **_get_input_fields(login_form.text),
            "_username": self.username,
            "_password": self.password,
        }
        res = await self.post(HomePath.LOGIN.value, body=data)

        assert res.url.path == HomePath.JURY.value, "Login fail."

    async def create_team_and_user(
        self,
        user: CreateUser,
        category_id: int,
        affiliation_id: int,
        enabled: bool = True,
    ) -> Tuple[str, str]:
        res = await self.get(TeamPath.ADD.value)

        data = {
            **_get_input_fields(res.text),
            "team[name]": user.username,
            "team[displayName]": user.name,
            "team[affiliation]": str(affiliation_id),
            "team[enabled]": "1" if enabled else "0",
            "team[addUserForTeam]": "1",  # '1' -> Yes
            "team[users][0][username]": user.username,
            "team[category]": str(category_id),
        }

        if "team[contests][]" in data and data["team[contests][]"] is None:
            data.pop("team[contests][]")

        res = await self.post(TeamPath.ADD.value, body=data)
        assert res.url.path != TeamPath.ADD.value, "Team create fail."
        team_id = res.url.path.split("/")[-1]

        res = await self.get(res.url.path)  # Go to team view page.

        soup = BeautifulSoup(res.text, "html.parser")
        user_link = soup.select_one(".container-fluid a")
        user_id = user_link["href"].split("/")[-1]

        return team_id, user_id

    async def set_user_password(
        self,
        user_id: str,
        password: str,
        user_roles: List[int],
        enabled: bool = True,
    ) -> None:
        url = UserPath.EDIT.value % user_id

        res = await self.get(url)

        user_roles_data = list(map(str, user_roles))

        data = {
            **_get_input_fields(res.text),
            'user[plainPassword]': password,
            'user[enabled]': "1" if enabled else "0",
            'user[user_roles][]': user_roles_data,
        }

        res = await self.post(url, body=data)
        res.raise_for_status()

        assert res.url.path != url, 'User set password fail.'

    async def delete_users(self, include=None):
        include = include if include else []
        include = set(map(lambda it: it.lower(), include))
        res = await self.get(TeamPath.LIST.value)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, 'html.parser')
        links = []
        for row in soup.select('table tbody tr'):
            name = row.select('a')[0].text.strip()
            if name.lower() not in include:
                continue

            link = row.select('a')[-1]['href']
            links.append(self.post(link))

        for task in asyncio.as_completed(links):
            res = await task
            res.raise_for_status()

    async def delete_teams(self, include=None):
        include = include if include else []
        include = set(map(lambda it: it.lower(), include))
        res = await self.get(TeamPath.LIST.value)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, 'html.parser')
        links = []
        for row in soup.select('table tbody tr'):
            name = row.select('a')[2].text.strip()
            if name.lower() not in include:
                continue
            link = row.select('a')[-2]['href']
            links.append(self.post(link))

        for task in asyncio.as_completed(links):
            res = await task
            res.raise_for_status()
