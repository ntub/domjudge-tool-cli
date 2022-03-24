import asyncio
from enum import Enum
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

from domjudge_tool_cli.models import Affiliation, CreateUser, ProblemItem, User
from domjudge_tool_cli.services.api_client import WebClient


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
    EDIT = "/jury/teams/%s/edit"


class AffiliationPath(str, Enum):
    LIST = "/jury/affiliations"
    ADD = "/jury/affiliations/add"


class ProblemPath(str, Enum):
    LIST = "/jury/problems"
    ADD = "/jury/problems/add"


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
        assert res.url.path != TeamPath.ADD.value, f"Team create fail. {user.username}"
        team_id = res.url.path.split("/")[-1]

        res = await self.get(res.url.path)  # Go to team view page.

        soup = BeautifulSoup(res.text, "html.parser")
        user_link = soup.select_one(".container-fluid a")
        user_id = user_link["href"].split("/")[-1]

        return team_id, user_id

    async def update_team(
        self,
        user: User,
        category_id: int,
        affiliation_id: int,
        enabled: bool = True,
    ) -> Tuple[str, str]:
        url = TeamPath.EDIT.value % user.team_id

        res = await self.get(url)

        data = {
            **_get_input_fields(res.text),
            "team[name]": user.username,
            "team[displayName]": user.name,
            "team[affiliation]": str(affiliation_id),
            "team[enabled]": "1" if enabled else "0",
            "team[category]": str(category_id),
        }

        if "team[contests][]" in data and data["team[contests][]"] is None:
            data.pop("team[contests][]")

        res = await self.post(url, body=data)
        assert res.url.path != url, f"Team update fail. {user.username}"
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
            "user[plainPassword]": password,
            "user[enabled]": "1" if enabled else "0",
            "user[user_roles][]": user_roles_data,
        }

        res = await self.post(url, body=data)
        res.raise_for_status()

        assert res.url.path != url, f"User set password fail. {user_id}"

    async def delete_users(self, include=None, exclude=None):
        include = include if include else []
        include = set(map(lambda it: it.lower(), include))
        exclude = exclude if exclude else []
        exclude = set(map(lambda it: it.lower(), exclude))
        res = await self.get(UserPath.LIST.value)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for row in soup.select("table tbody tr"):
            name = row.select("a")[0].text.strip()
            lower_name = name.lower()
            if lower_name not in include or lower_name in exclude:
                continue

            link = row.select("a")[-1]["href"]
            links.append(self.post(link))

        for task in links:
            res = await task
            res.raise_for_status()

    async def delete_teams(self, include=None, exclude=None):
        include = include if include else []
        include = set(map(lambda it: it.lower(), include))
        exclude = exclude if exclude else []
        exclude = set(map(lambda it: it.lower(), exclude))
        res = await self.get(TeamPath.LIST.value)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for row in soup.select("table tbody tr"):
            name = row.select("a")[2].text.strip()
            lower_name = name.lower()
            if lower_name not in include or lower_name in exclude:
                continue
            link = row.select("a")[-2]["href"]
            links.append(self.post(link))

        for task in links:
            res = await task
            res.raise_for_status()

    async def create_affiliation(
        self,
        shortname: str,
        name: str,
        country: str = "TWN",
    ) -> Affiliation:
        res = await self.get(AffiliationPath.ADD.value)

        data = {
            **_get_input_fields(res.text),
            "team_affiliation[shortname]": shortname,
            "team_affiliation[name]": name,
            "team_affiliation[country]": country,
            "team_affiliation[comments]": "",
        }

        res = await self.post(AffiliationPath.ADD.value, body=data)
        assert res.url.path != AffiliationPath.ADD.value, "Affiliation create fail."
        affiliation_id = res.url.path.split("/")[-1]

        return Affiliation(
            id=affiliation_id,
            shortname=shortname,
            name=name,
            country=country,
        )

    async def get_affiliations(self) -> List[Affiliation]:
        res = await self.get(AffiliationPath.LIST.value)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        objs = []
        for row in soup.select("table tbody tr"):
            affiliation_id = row.select("td a")[0].text.strip()
            shortname = row.select("td a")[1].text.strip()
            name = row.select("td a")[2].text.strip()
            country = row.select("td a")[3].img.get("alt", "").strip()
            obj = Affiliation(
                id=affiliation_id,
                shortname=shortname,
                name=name,
                country=country,
            )
            objs.append(obj)

        return objs

    async def get_affiliation(self, name) -> Optional[Affiliation]:
        affiliations = await self.get_affiliations()

        for it in affiliations:
            if it.name == name or it.shortname == name:
                return it

        return None

    async def get_problems(
        self,
        exclude: Optional[List[str]] = None,
    ) -> List[ProblemItem]:
        res = await self.get(ProblemPath.LIST.value)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        objs = []
        for row in soup.select("table tbody tr"):
            problem_id = row.select("td a")[0].text.strip()
            name = row.select("td a")[1].text.strip()
            time_limit = row.select("td a")[3].text.strip()
            test_data_count = row.select("td a")[6].text.strip()
            export_file_path = str(row.select("td a")[7]["href"]).strip()

            if problem_id in exclude:
                continue

            obj = ProblemItem(
                id=problem_id,
                name=name,
                time_limit=time_limit,
                test_data_count=test_data_count,
                export_file_path=export_file_path,
            )
            objs.append(obj)

        return objs
