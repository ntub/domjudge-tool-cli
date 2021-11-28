import os
import typer
import httpx
import csv

from enum import Enum
from typing import Optional, Tuple, List

from bs4 import BeautifulSoup

app = typer.Typer()

def titles(items):
    headers = ['Rank', 'TeamAffiliation', 'TeamName', 'SolvedCount', 'Score']
    for item in items:
        title = item['title']
        if title.startswith('problem '):
            headers.append(title[8:])
    return headers

def scores(element):
    data = []
    # Rank
    data.append(element.find('td', class_='scorepl').text.strip())
    # TeamAffiliation
    data.append(element.find('td', class_='scoretn').find('span', class_='univ').text.strip())
    # TeamName
    data.append(element.find('td', class_='scoretn').find('span').text.split()[-1])
    # SolvedCount
    data.append(element.find('td', class_='scorenc').text.strip())
    # Score
    data.append(element.find('td', class_='scorett').text.strip())
    # Problem Score
    for el in element.find_all('td', class_='score_cell'):
        s = el.text.strip().split()
        if len(s) == 0:
            data.append('')
        elif len(s) == 2:
            data.append("{} {}".format(*s))
        elif len(s) == 3:
            data.append("{}/{} {}".format(*s))
    return data

def summary(element):
    data = [''] * 3
    data.append(element.find('td', class_='scorenc').text.strip())
    data.append('')
    for el in element.find_all('td')[3:]:
        data.append('/'.join(el.text.split()))
    return data

@app.command()
def export(
    url: str,
    filename: str = 'export',
    path_prefix: Optional[str] = None,
):
    res = httpx.get(url).content
    soup = BeautifulSoup(res, "html.parser")
    
    data = []
    data.append(titles(soup.find('tr', class_='scoreheader').find_all('th')))

    elements = soup.find('table', class_='scoreboard').find('tbody').find_all('tr')
    for element in elements:
        if element.find('td', id='scoresummary'):
            data.append(summary(element))
        else:
            data.append(scores(element))
    
    file_path = f"{filename}.csv"
    if path_prefix:
        file_path = f"{path_prefix}/{file_path}"

    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)