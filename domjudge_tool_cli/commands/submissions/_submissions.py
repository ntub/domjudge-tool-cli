import asyncio

import typer

from typing import Optional, List, Any
from enum import Enum

from tablib import Dataset

from domjudge_tool_cli.models import Submission, DomServerClient
from domjudge_tool_cli.services.v4 import SubmissionsAPI, TeamsAPI, ProblemsAPI, DomServerWeb

def gen_submission_dataset(submissions: List[Any]) -> Dataset:
    dataset = Dataset()
    for idx, submission in enumerate(submissions):
        if idx == 0:
            dataset.headers = submission.dict().keys()

        dataset.append(submission.dict().values())

    return dataset

def print_submissions_table(submissions: List[Submission]):
    dataset = gen_submission_dataset(submissions)
    # ["id", "team_id", "problem_id", "language_id", "files", "entry_point", "time", "contest_time", "externalid"]
    for rm_key in ["externalid", "contest_time"]:
        del dataset[rm_key]
    typer.echo(dataset.export("cli", tablefmt="simple"))

def file_path(cid, mode, path, team, problem):
    if mode == 1:
        file_path = f"Teams/{team.name}/Problems/{problem.short_name}/Submissions"
    elif mode == 2:
        file_path = f"Problems/{problem.short_name}/Teams/{team.name}/Submissions"
    else:
        file_path = f"contests/{cid}/submissions"

    if path:
        file_path = f"{path}/{file_path}"

    return file_path

async def get_submissions(
    client: DomServerClient,
    cid: str,
    language_id: Optional[str] = None,
    strict: Optional[bool] = False,
    ids: Optional[List[str]] = None
):
    api = SubmissionsAPI(**client.api_params)
    submissions = await api.all_submissions(cid)

    print_submissions_table(submissions)

async def download_submission_files(
    client: DomServerClient,
    cid: str,
    id: str,
    mode: int,
    path_prefix: Optional[str] = None,
    strict: Optional[bool] = False,
):
    api = SubmissionsAPI(**client.api_params)
    submission = await api.submission(cid, id)

    team_api = TeamsAPI(**client.api_params)
    team = await team_api.team(cid, submission.team_id)

    problem_api = ProblemsAPI(**client.api_params)
    problem = await problem_api.problem(cid, submission.problem_id)

    api = SubmissionsAPI(**client.api_params)
    submission_file = await api.submission_file_name(cid, id)
    submission_filename = submission_file.filename.split('.')[0]

    path = file_path(cid, mode, path_prefix, team, problem)
    api = SubmissionsAPI(**client.api_params)
    await api.submission_files(cid, id, submission_filename, path)

async def download_contest_files(
    client: DomServerClient,
    cid: str,
    mode: int,
    path_prefix: Optional[str] = None,
):
    api = SubmissionsAPI(**client.api_params)
    submissions = await api.all_submissions(cid)

    for submission in submissions:
        team_api = TeamsAPI(**client.api_params)
        team = await team_api.team(cid, submission.team_id)

        problem_api = ProblemsAPI(**client.api_params)
        problem = await problem_api.problem(cid, submission.problem_id)

        id = submission.id
        api = SubmissionsAPI(**client.api_params)
        submission_file = await api.submission_file_name(cid, id)
        submission_filename = submission_file.filename.split('.')[0]

        path = file_path(cid, mode, path_prefix, team, problem)
        api = SubmissionsAPI(**client.api_params)
        await api.submission_files(cid, id, submission_filename, path)
