from enum import Enum

from bs4 import BeautifulSoup

from domjudge_tool_cli.services.api_client import WebClient


class HomePath(str, Enum):
    JURY = "/jury"
    LOGIN = "/login"


class UserPath(str, Enum):
    LIST = "/jury/users"
    ADD = "/jury/users/add"
    EDIT = "/jury/users/%s/edit"


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
