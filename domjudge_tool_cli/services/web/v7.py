from enum import StrEnum

from bs4 import BeautifulSoup

from domjudge_tool_cli.exceptions import FormSubmitError
from domjudge_tool_cli.models import Affiliation, CreateUser, ProblemItem, User
from domjudge_tool_cli.services.web.base import (
    BaseDomServerWeb,
    _get_form_feedback,
    _get_input_fields,
)


class HomePath(StrEnum):
    JURY = "/jury"
    LOGIN = "/login"


class UserPath(StrEnum):
    LIST = "/jury/users"
    ADD = "/jury/users/add"
    EDIT = "/jury/users/%s/edit"


class TeamPath(StrEnum):
    LIST = "/jury/teams"
    ADD = "/jury/teams/add"
    EDIT = "/jury/teams/%s/edit"


class AffiliationPath(StrEnum):
    LIST = "/jury/affiliations"
    ADD = "/jury/affiliations/add"


class ProblemPath(StrEnum):
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
        if res.url.path != HomePath.JURY:
            raise FormSubmitError(
                "Login fail.",
                path=HomePath.LOGIN,
                details=_get_form_feedback(res.text),
            )

    async def create_team_and_user(
        self,
        user: CreateUser,
        category_id: int,
        affiliation_id: int,
        enabled: bool = True,
    ) -> tuple[str, str]:
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
        if res.url.path == TeamPath.ADD:
            raise FormSubmitError(
                f"Team create fail. {user.username}",
                path=TeamPath.ADD,
                details=_get_form_feedback(res.text),
            )
        team_id = res.url.path.split("/")[-1]

        res = await self.get(res.url.path)  # Go to team view page.

        soup = BeautifulSoup(res.text, "html.parser")
        user_link = soup.select_one(".container-fluid a")
        if user_link is None or not user_link.get("href"):
            raise ValueError(
                f"DOMjudge 7 create_team_and_user: failed to find user link on team page {res.url.path}"
            )
        user_id = str(user_link["href"]).split("/")[-1]

        return team_id, user_id

    async def update_team(
        self,
        user: User,
        category_id: int,
        affiliation_id: int,
        enabled: bool = True,
    ) -> tuple[str, str]:
        if not user.team_id:
            raise ValueError("User must have team_id to update team")
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
        if res.url.path == url:
            raise FormSubmitError(
                f"Team update fail. {user.username}",
                path=url,
                details=_get_form_feedback(res.text),
            )
        team_id = res.url.path.split("/")[-1]

        res = await self.get(res.url.path)  # Go to team view page.

        soup = BeautifulSoup(res.text, "html.parser")
        user_link = soup.select_one(".container-fluid a")
        if user_link is None or not user_link.get("href"):
            raise ValueError(
                f"DOMjudge 7 update_team: failed to find user link on team page {res.url.path}"
            )
        user_id = str(user_link["href"]).split("/")[-1]

        return team_id, user_id

    async def set_user_password(
        self,
        user_id: str,
        password: str,
        user_roles: list[int],
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

        if res.url.path == url:
            # DOMjudge re-rendered the form, so the password was rejected.
            raise FormSubmitError(
                f"User set password fail. {user_id}",
                path=url,
                details=_get_form_feedback(res.text),
            )

    async def delete_users(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> int:
        """Delete matching users and return how many were deleted.

        Returns 0 when nothing matched, so callers can confirm a cleanup
        actually happened instead of assuming success from a silent no-op.
        """
        include_set = {it.lower() for it in (include or [])}
        exclude_set = {it.lower() for it in (exclude or [])}
        res = await self.get(UserPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for row in soup.select("table tbody tr"):
            a_tags = row.select("a")
            if not a_tags:
                continue
            name = a_tags[0].text.strip()
            lower_name = name.lower()
            if lower_name not in include_set or lower_name in exclude_set:
                continue

            href = a_tags[-1].get("href")
            if not isinstance(href, str):
                continue
            links.append(self.post(href))

        for task in links:
            res = await task
            res.raise_for_status()

        return len(links)

    async def delete_teams(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> int:
        """Delete matching teams and return how many were deleted."""
        include_set = {str(it).lower() for it in (include or [])}
        exclude_set = {str(it).lower() for it in (exclude or [])}
        res = await self.get(TeamPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for row in soup.select("table tbody tr"):
            a_tags = row.select("a")
            if len(a_tags) < 2:
                continue
            teamid = a_tags[0].text.strip().lower()

            if teamid not in include_set or teamid in exclude_set:
                continue

            href = a_tags[-2].get("href")
            if not isinstance(href, str):
                continue
            links.append(self.post(href))

        for task in links:
            res = await task
            res.raise_for_status()

        return len(links)

    async def delete_affiliation(self, affiliation_id: str) -> int:
        """Delete one affiliation by id and report how many rows were deleted."""
        res = await self.get(AffiliationPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        target = str(affiliation_id).strip().lower()
        for row in soup.select("table tbody tr"):
            a_tags = row.select("a")
            if len(a_tags) < 2:
                continue
            row_id = a_tags[0].text.strip().lower()
            if row_id != target:
                continue

            href = a_tags[-1].get("href")
            if not isinstance(href, str):
                continue
            post_res = await self.post(href)
            post_res.raise_for_status()
            return 1

        return 0

    async def get_min_password_length(self) -> int | None:
        """Read the minimum password length DOMjudge renders on its user form.

        DOMjudge 7.x does not enforce or advertise a minimum, so the attribute
        is absent and this returns None rather than inventing a value.
        """
        res = await self.get(UserPath.ADD)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        fields = soup.find_all("input", attrs={"name": "user[plainPassword]"})
        if not fields:
            return None
        raw = fields[0].get("minlength")
        if not isinstance(raw, str) or not raw.strip().isdigit():
            return None
        return int(raw)

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
        if res.url.path == AffiliationPath.ADD:
            raise FormSubmitError(
                "Affiliation create fail.",
                path=AffiliationPath.ADD,
                details=_get_form_feedback(res.text),
            )
        affiliation_id = res.url.path.split("/")[-1]

        return Affiliation(
            id=affiliation_id,
            shortname=shortname,
            name=name,
            country=country,
        )

    async def get_affiliations(self) -> list[Affiliation]:
        res = await self.get(AffiliationPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        objs = []
        for row in soup.select("table tbody tr"):
            links = row.select("td a")
            if len(links) < 4:
                raise ValueError(
                    f"DOMjudge 7 get_affiliations: unexpected table row structure, expected at least 4 link elements, got {len(links)}"
                )
            affiliation_id = links[0].text.strip()
            shortname = links[1].text.strip()
            name = links[2].text.strip()
            img = links[3].find("img")
            alt_val = img.get("alt") if img is not None else None
            if isinstance(alt_val, str):
                country = alt_val.strip()
            else:
                country = links[3].text.strip()

            obj = Affiliation(
                id=affiliation_id,
                shortname=shortname,
                name=name,
                country=country,
            )
            objs.append(obj)

        return objs

    async def get_affiliation(self, name: str) -> Affiliation | None:
        affiliations = await self.get_affiliations()

        for it in affiliations:
            if it.name == name or it.shortname == name:
                return it

        return None

    async def get_problems(
        self,
        exclude: list[str] | None = None,
        only: list[str] | None = None,
    ) -> list[ProblemItem]:
        res = await self.get(ProblemPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        objs = []
        for row in soup.select("table tbody tr"):
            links = row.select("td a")
            if len(links) < 8:
                raise ValueError(
                    f"DOMjudge 7 get_problems: unexpected table row structure, expected at least 8 link elements, got {len(links)}"
                )
            problem_id = links[0].text.strip()
            name = links[1].text.strip()
            time_limit = links[3].text.strip()
            test_data_count = links[6].text.strip()
            href = links[7].get("href")
            if not isinstance(href, str):
                raise ValueError(
                    "DOMjudge 7 get_problems: missing href attribute on export link"
                )
            export_file_path = href.strip()

            if only and problem_id not in only:
                continue

            if exclude and problem_id in exclude:
                continue

            obj = ProblemItem(
                id=problem_id,
                name=name,
                time_limit=int(time_limit),
                test_data_count=int(test_data_count),
                export_file_path=export_file_path,
            )
            objs.append(obj)

        return objs
