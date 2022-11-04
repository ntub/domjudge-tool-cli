from enum import Enum
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

from domjudge_tool_cli.models import Affiliation, CreateUser, ProblemItem, User
from domjudge_tool_cli.services.web.base import BaseDomServerWeb, _get_input_fields


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


class DomServerWeb(BaseDomServerWeb):
    async def login(self) -> None:
        login_form = await self.get(HomePath.LOGIN)
        data = {
            **_get_input_fields(login_form.text),
            "_username": self.username,
            "_password": self.password,
        }
        res = await self.post(HomePath.LOGIN, body=data)

        assert res.url.path == HomePath.JURY, "Login fail."

    async def create_team_and_user(
        self,
        user: CreateUser,
        category_id: int,
        affiliation_id: int,
        enabled: bool = True,
    ) -> Tuple[str, str]:
        res = await self.get(TeamPath.ADD)

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

        res = await self.post(TeamPath.ADD, body=data)
        assert res.url.path != TeamPath.ADD, f"Team create fail. {user.username}"
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
        url = TeamPath.EDIT % user.team_id

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
        url = UserPath.EDIT % user_id

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

    async def delete_users(
        self,
        include: List[str] = None,
        exclude: List[str] = None,
    ):
        include = include if include else []
        include = set(map(lambda it: it.lower(), include))
        exclude = exclude if exclude else []
        exclude = set(map(lambda it: it.lower(), exclude))
        res = await self.get(UserPath.LIST)
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

    async def delete_teams(
        self,
        include: List[str] = None,
        exclude: List[str] = None,
    ):
        include = include if include else []
        include = set(map(lambda it: str(it).lower(), include))
        exclude = exclude if exclude else []
        exclude = set(map(lambda it: str(it).lower(), exclude))
        res = await self.get(TeamPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for row in soup.select("table tbody tr"):
            teamid = row.select("a")[0].text.strip().lower()

            if teamid not in include or teamid in exclude:
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
        res = await self.get(AffiliationPath.ADD)

        data = {
            **_get_input_fields(res.text),
            "team_affiliation[shortname]": shortname,
            "team_affiliation[name]": name,
            "team_affiliation[country]": country,
            "team_affiliation[comments]": "",
        }

        res = await self.post(AffiliationPath.ADD, body=data)
        assert res.url.path != AffiliationPath.ADD, "Affiliation create fail."
        affiliation_id = res.url.path.split("/")[-1]

        return Affiliation(
            id=affiliation_id,
            shortname=shortname,
            name=name,
            country=country,
        )

    async def get_affiliations(self) -> List[Affiliation]:
        res = await self.get(AffiliationPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        objs = []
        for row in soup.select("table tbody tr"):
            affiliation_id = row.select("td a")[0].text.strip()
            shortname = row.select("td a")[1].text.strip()
            name = row.select("td a")[2].text.strip()
            try:
                country = row.select("td a")[3].img.get("alt", "").strip()
            except AttributeError:
                country = row.select("td a")[3].text.strip()

            obj = Affiliation(
                id=affiliation_id,
                shortname=shortname,
                name=name,
                country=country,
            )
            objs.append(obj)

        return objs

    async def get_affiliation(self, name: str) -> Optional[Affiliation]:
        affiliations = await self.get_affiliations()

        for it in affiliations:
            if it.name == name or it.shortname == name:
                return it

        return None

    async def get_problems(
        self,
        exclude: Optional[List[str]] = None,
        only: Optional[List[str]] = None,
    ) -> List[ProblemItem]:
        res = await self.get(ProblemPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        objs = []
        for row in soup.select("table tbody tr"):
            problem_id = row.select("td a")[0].text.strip()
            name = row.select("td a")[1].text.strip()
            time_limit = row.select("td a")[3].text.strip()
            test_data_count = row.select("td a")[6].text.strip()
            export_file_path = str(row.select("td a")[7]["href"]).strip()

            if only and problem_id not in only:
                continue

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
