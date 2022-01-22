import asyncio
from typing import Any, List, Optional

import typer
from tablib import Dataset

from domjudge_tool_cli.models import DomServerClient, Submission
from domjudge_tool_cli.services.v4 import ProblemsAPI, SubmissionsAPI, TeamsAPI


def gen_submission_dataset(submissions: List[Any]) -> Dataset:
    dataset = Dataset()
    for idx, submission in enumerate(submissions):
        if idx == 0:
            dataset.headers = submission.dict().keys()

        dataset.append(submission.dict().values())

    return dataset


def print_submissions_table(submissions: List[Submission]):
    dataset = gen_submission_dataset(submissions)
    # ["id", "team_id", "problem_id", "language_id",
    # "files", "entry_point", "time", "contest_time", "externalid"]
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


def index_by_id(objs):
    data = dict()
    for obj in objs:
        data[obj.id] = obj
    return data


async def get_submissions(
    client: DomServerClient,
    cid: str,
    language_id: Optional[str] = None,
    strict: Optional[bool] = False,
    ids: Optional[List[str]] = None,
):
    async with SubmissionsAPI(**client.api_params) as api:
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
    async with SubmissionsAPI(**client.api_params) as api:
        submission = await api.submission(cid, id)

        async with TeamsAPI(**client.api_params) as team_api:
            team = await team_api.team(cid, submission.team_id)

        async with ProblemsAPI(**client.api_params) as problem_api:
            problem = await problem_api.problem(cid, submission.problem_id)

        submission_file = await api.submission_file_name(cid, id)
        submission_filename = submission_file.filename.split(".")[0]

        path = file_path(cid, mode, path_prefix, team, problem)
        await api.submission_files(cid, id, submission_filename, path)


async def download_contest_files(
    client: DomServerClient,
    cid: str,
    mode: int,
    path_prefix: Optional[str] = None,
):
    async with SubmissionsAPI(**client.api_params) as api:
        submissions = await api.all_submissions(cid)

        async with TeamsAPI(**client.api_params) as team_api:
            teams = await team_api.all_teams(cid)
            teams_mapping = index_by_id(teams)

        async with ProblemsAPI(**client.api_params) as problem_api:
            problems = await problem_api.all_problems(cid)
            problems_mapping = index_by_id(problems)

        async def get_source_codes(submission) -> None:
            id = submission.id
            team = teams_mapping[submission.team_id]
            problem = problems_mapping[submission.problem_id]

            submission_file = await api.submission_file_name(cid, id)
            submission_filename = submission_file.filename.split(".")[0]

            path = file_path(cid, mode, path_prefix, team, problem)
            await api.submission_files(cid, id, submission_filename, path)

        with typer.progressbar(submissions) as progress:
            for task in progress:
                await get_source_codes(task)
