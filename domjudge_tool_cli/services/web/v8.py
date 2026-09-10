from enum import StrEnum

from bs4 import BeautifulSoup

from domjudge_tool_cli.models import Affiliation, CreateUser, ProblemItem, User
from domjudge_tool_cli.services.web.base import BaseDomServerWeb, _get_input_fields


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


class AddUserForTeam(StrEnum):
    CREATE_NEW = "create-new-user"
    ADD_EXISTING = "add-existing-user"
    DONT_ADD = "dont-add-user"


def _parse_time_limit(raw: str) -> int:
    s = raw.strip()
    if s.endswith("s"):
        s = s[:-1].strip()
    return int(s) if s else 0


def _extract_user_id_from_team_view(html: str, view_path: str, operation: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    user_link = soup.select_one('a[href^="/jury/users/"]')
    if user_link is None or not user_link.get("href"):
        raise ValueError(
            f"DOMjudge 8 {operation}: failed to find user link on team page {view_path}"
        )
    href = str(user_link["href"]).strip()
    user_id = href.rstrip("/").split("/")[-1]
    if not user_id:
        raise ValueError(
            f"DOMjudge 8 {operation}: failed to extract user id from {href} on team page {view_path}"
        )
    return user_id


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
            raise AssertionError("Login fail.")

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
            "team[category]": str(category_id),
            "team[affiliation]": str(affiliation_id),
            "team[enabled]": "1" if enabled else "0",
            "team[penalty]": "0",
            "team[addUserForTeam]": AddUserForTeam.CREATE_NEW.value,
            "team[newUsername]": user.username,
        }

        res = await self.post(TeamPath.ADD, body=data)
        if res.url.path == TeamPath.ADD:
            raise AssertionError(f"Team create fail. {user.username}")

        team_id = res.url.path.rstrip("/").split("/")[-1]

        team_view_res = await self.get(res.url.path)
        user_id = _extract_user_id_from_team_view(
            team_view_res.text, res.url.path, "create_team_and_user"
        )

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
            "team[category]": str(category_id),
            "team[affiliation]": str(affiliation_id),
            "team[enabled]": "1" if enabled else "0",
        }

        res = await self.post(url, body=data)
        if res.url.path == url:
            raise AssertionError(f"Team update fail. {user.username}")

        team_id = res.url.path.rstrip("/").split("/")[-1]

        team_view_res = await self.get(res.url.path)
        user_id = _extract_user_id_from_team_view(
            team_view_res.text, res.url.path, "update_team"
        )

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

        data = {
            **_get_input_fields(res.text),
            "user[plainPassword]": password,
            "user[enabled]": "1" if enabled else "0",
        }

        if user_roles:
            data["user[user_roles][]"] = [str(r) for r in user_roles]

        res = await self.post(url, body=data)
        res.raise_for_status()

        if res.url.path == url:
            raise AssertionError(f"User set password fail. {user_id}")

    async def _confirm_and_post_delete(self, href: str) -> None:
        confirm_res = await self.get(href)
        confirm_res.raise_for_status()
        form_data = _get_input_fields(confirm_res.text)
        post_res = await self.post(href, body=form_data)
        post_res.raise_for_status()

    async def delete_users(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> None:
        include_set = {it.lower() for it in (include or [])}
        exclude_set = {it.lower() for it in (exclude or [])}
        res = await self.get(UserPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        delete_hrefs: list[str] = []
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
            delete_hrefs.append(href)

        for href in delete_hrefs:
            await self._confirm_and_post_delete(href)

    async def delete_teams(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> None:
        include_set = {it.lower() for it in (include or [])}
        exclude_set = {it.lower() for it in (exclude or [])}
        res = await self.get(TeamPath.LIST)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        delete_hrefs: list[str] = []
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
            delete_hrefs.append(href)

        for href in delete_hrefs:
            await self._confirm_and_post_delete(href)

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
        }

        res = await self.post(AffiliationPath.ADD, body=data)
        if res.url.path == AffiliationPath.ADD:
            raise AssertionError("Affiliation create fail.")
        affiliation_id = res.url.path.rstrip("/").split("/")[-1]

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
            if len(links) < 5:
                raise ValueError(
                    f"DOMjudge 8 get_affiliations: unexpected table row structure, expected at least 5 link elements, got {len(links)}"
                )
            affiliation_id = links[0].text.strip()
            shortname = links[2].text.strip()
            name = links[3].text.strip()
            img = links[4].find("img")
            alt_val = img.get("alt") if img is not None else None
            if isinstance(alt_val, str):
                country = alt_val.strip()
            else:
                country = links[4].text.strip()
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
            cells = row.select("td")
            if len(cells) < 8:
                raise ValueError(
                    f"DOMjudge 8 get_problems: unexpected table row structure, expected at least 8 cells, got {len(cells)}"
                )

            id_anchor = cells[0].find("a")
            problem_id = id_anchor.text.strip() if id_anchor is not None else ""
            if not problem_id:
                raise ValueError("DOMjudge 8 get_problems: problem row id missing")

            if only and problem_id not in only:
                continue

            if exclude and problem_id in exclude:
                continue

            name_anchor = cells[1].find("a")
            name = name_anchor.text.strip() if name_anchor is not None else ""

            time_limit_anchor = cells[4].find("a")
            time_limit_raw = (
                time_limit_anchor.text.strip() if time_limit_anchor is not None else ""
            )
            time_limit = _parse_time_limit(time_limit_raw)

            test_cases_anchor = cells[7].find("a")
            test_cases_raw = (
                test_cases_anchor.text.strip() if test_cases_anchor is not None else ""
            )
            test_data_count = int(test_cases_raw) if test_cases_raw else 0

            export_link = row.select_one('a[title="export problem as zip-file"]')
            if export_link is None:
                export_link = row.select_one('a[href$="/export"]')
            if export_link is None or not export_link.get("href"):
                raise ValueError(
                    "DOMjudge 8 get_problems: missing export link on problem row"
                )

            export_file_path = str(export_link["href"]).strip()

            obj = ProblemItem(
                id=problem_id,
                name=name,
                time_limit=time_limit,
                test_data_count=test_data_count,
                export_file_path=export_file_path,
            )
            objs.append(obj)

        return objs
