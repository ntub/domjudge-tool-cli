import csv
from typing import Optional

import httpx
import typer
from bs4 import BeautifulSoup

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config

app = typer.Typer()


def titles(items):
    headers = ["Rank", "TeamAffiliation", "TeamName", "SolvedCount", "Score"]
    for item in items:
        title = item["title"]
        if title.startswith("problem "):
            headers.append(title[8:])
    return headers


def get_element_empty(element) -> str:
    value = ""
    if element:
        value = element.text.strip()
    return value


def scores(element):
    data = []
    # Rank
    data.append(
            get_element_empty(
                    element.find("td", class_="scorepl"),
            ),
    )
    # TeamAffiliation
    affiliation_element = element.find("td", class_="scoretn")
    affiliation = ""
    if affiliation_element and affiliation_element.find("span", class_="univ"):
        affiliation = affiliation_element.find("span", class_="univ").text.strip()
    data.append(affiliation)
    # TeamName
    team_name_element = element.find("td", class_="scoretn")
    team_name = ""
    if team_name_element and team_name_element.find("span"):
        team_name = element.find("span").text.split()[-1]
    data.append(team_name)
    # SolvedCount
    data.append(
            get_element_empty(
                    element.find("td", class_="scorenc"),
            ),
    )
    # Score
    data.append(
            get_element_empty(
                    element.find("td", class_="scorett"),
            ),
    )
    # Problem Score
    for el in element.find_all("td", class_="score_cell"):
        s = el.text.strip().split()
        if len(s) == 0:
            data.append("")
        elif len(s) == 2:
            data.append("{} {}".format(*s))
        elif len(s) == 3:
            data.append("{}/{} {}".format(*s))
    return data


def summary(element):
    data = [""] * 3
    data.append(element.find("td", class_="scorenc").text.strip())
    data.append("")
    for el in element.find_all("td")[3:]:
        data.append("/".join(el.text.split()))
    return data


@app.command()
def export(
    cid: int,
    filename: str = "export",
    url: Optional[str] = None,
    path_prefix: Optional[str] = None,
):
    if not url:
        client = get_or_ask_config(general_state["config"])
        url = f"{client.host}/public?static=1"

    cookies = None
    if cid:
        cookies = {"domjudge_cid": f"{cid}"}

    res = httpx.get(url, cookies=cookies).content
    soup = BeautifulSoup(res, "html.parser")

    data = []
    data.append(titles(soup.find("tr", class_="scoreheader").find_all("th")))

    elements = soup.find("table", class_="scoreboard").find("tbody").find_all("tr")
    for element in elements:
        if element.find("td", class_="scoresummary"):
            data.append(summary(element))
        else:
            data.append(scores(element))

    file_path = f"{filename}.csv"
    if path_prefix:
        file_path = f"{path_prefix}/{file_path}"

    with open(file_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)
