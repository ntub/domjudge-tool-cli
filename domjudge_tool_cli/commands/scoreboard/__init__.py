import csv
from typing import Annotated, Any

import httpx
import typer
from bs4 import BeautifulSoup

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config

app = typer.Typer()


def titles(items: list[Any]) -> list[str]:
    headers = ["Rank", "TeamAffiliation", "TeamName", "SolvedCount", "Score"]
    for item in items:
        title = item.get("title", "") if hasattr(item, "get") else ""
        if isinstance(title, str) and title.startswith("problem "):
            headers.append(title[8:])
    return headers


def get_element_empty(element: Any) -> str:
    value = ""
    if element:
        value = element.text.strip()
    return value


def scores(element: Any) -> list[str]:
    data: list[str] = []
    # Rank
    data.append(get_element_empty(element.find("td", class_="scorepl")))
    # TeamAffiliation
    affiliation_element = element.find("td", class_="scoretn")
    affiliation = ""
    if affiliation_element and affiliation_element.find("span", class_="univ"):
        affiliation = affiliation_element.find("span", class_="univ").text.strip()
    data.append(affiliation)
    # TeamName
    team_name = ""
    if affiliation_element and affiliation_element.find("span"):
        team_name = affiliation_element.find("span").text.split()[-1]
    data.append(team_name)
    # SolvedCount
    data.append(get_element_empty(element.find("td", class_="scorenc")))
    # Score
    data.append(get_element_empty(element.find("td", class_="scorett")))
    # Problem Score
    for el in element.find_all("td", class_="score_cell"):
        s = el.text.strip().split()
        if not s:
            data.append("")
        elif len(s) == 1:
            data.append(s[0])
        elif len(s) == 2:
            data.append("{}/{}".format(*s))
        else:
            data.append("{}/{} {}".format(*s))
    return data


def summary(element: Any) -> list[str]:
    data = [""] * 3
    data.append(get_element_empty(element.find("td", class_="scorenc")))
    data.append(get_element_empty(element.find("td", class_="scorett")))
    for el in element.find_all("td", class_="score_cell"):
        data.append(get_element_empty(el))
    return data


@app.command()
def export(
    cid: Annotated[int, typer.Argument(help="Contest id.")],
    filename: Annotated[str, typer.Option(help="Export filename.")] = "export",
    url: Annotated[str | None, typer.Option(help="Scoreboard URL.")] = None,
    path_prefix: Annotated[str | None, typer.Option(help="Path prefix.")] = None,
) -> None:
    if not url:
        client = get_or_ask_config(general_state["config"])
        host_str = str(client.host).rstrip("/")
        url = f"{host_str}/public?static=1"

    cookies = {"domjudge_cid": f"{cid}"} if cid else None

    res = httpx.get(url, cookies=cookies, follow_redirects=True).content
    soup = BeautifulSoup(res, "html.parser")

    header_row = soup.find("tr", class_="scoreheader")
    if header_row is None:
        raise ValueError("Failed to find scoreheader row in scoreboard HTML")

    data: list[list[str]] = [titles(header_row.find_all("th"))]

    table = soup.find("table", class_="scoreboard")
    if table is None:
        raise ValueError("Failed to find scoreboard table in scoreboard HTML")

    tbody = table.find("tbody")
    elements = tbody.find_all("tr") if tbody else table.find_all("tr")

    for element in elements:
        if element.find("td", class_="scoresummary"):
            data.append(summary(element))
        else:
            data.append(scores(element))

    file_path = f"{filename}.csv"
    if path_prefix:
        file_path = f"{path_prefix}/{file_path}"

    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)
