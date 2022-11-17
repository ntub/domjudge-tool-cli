from typing import Any, Dict, List, Optional

import typer
from tablib import Dataset

from domjudge_tool_cli.models import DomServerClient, Submission
from domjudge_tool_cli.services.api.v4 import (
    JudgementAPI,
    JudgementTypeAPI,
    ProblemsAPI,
    SubmissionsAPI,
    TeamsAPI,
)


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
        filepath = f"team_{team.name}/problem_{problem.short_name}"
    elif mode == 2:
        filepath = f"problem_{problem.short_name}/team_{team.name}"
    else:
        filepath = f"contest_{cid}"

    if path:
        filepath = f"{path}/{filepath}"

    return filepath


def index_by_id(objs):
    data = dict()
    for obj in objs:
        data[obj.id] = obj
    return data


async def judgement_submission_mapping(
    client: DomServerClient,
    cid: str,
) -> Dict[str, str]:
    async with JudgementTypeAPI(**client.api_params) as api:
        judgement_types = await api.all_judgement_types(cid)

    async with JudgementAPI(**client.api_params) as api:
        judgements = await api.all_judgements(cid)

    judgement_type_mapping = {
        item.id: str(item.name).lower().replace(" ", "_") for item in judgement_types
    }
    return {
        item.submission_id: judgement_type_mapping.get(item.judgement_type_id)
        for item in judgements
    }


async def get_submissions(
    client: DomServerClient,
    cid: str,
    language_id: Optional[str] = None,
    strict: Optional[bool] = False,
    ids: Optional[List[str]] = None,
):
    async with SubmissionsAPI(**client.api_params) as api:
        submissions = await api.all_submissions(
            cid,
            language_id=language_id,
            strict=strict,
            ids=ids,
        )

        print_submissions_table(submissions)


async def download_submission_files(
    client: DomServerClient,
    cid: str,
    id: str,
    mode: int,
    path_prefix: Optional[str] = None,
    strict: Optional[bool] = False,
    is_extract: bool = True,
):
    judgement_mapping = await judgement_submission_mapping(client, cid)
    async with SubmissionsAPI(**client.api_params) as api:
        submission = await api.submission(cid, id)

        async with TeamsAPI(**client.api_params) as team_api:
            team = await team_api.team(cid, submission.team_id)

        async with ProblemsAPI(**client.api_params) as problem_api:
            problem = await problem_api.problem(cid, submission.problem_id)

        submission_file = await api.submission_file_name(cid, id)
        submission_filename = submission_file.filename.split(".")[0]
        judgement_name = judgement_mapping.get(id)
        submission_filename = f"{submission_filename}_{judgement_name}"

        path = file_path(cid, mode, path_prefix, team, problem)
        typer.echo(f"Output path: {path}.")
        await api.submission_files(
            cid,
            id,
            submission_filename,
            path,
            strict,
            is_extract,
        )


async def download_contest_files(
    client: DomServerClient,
    cid: str,
    mode: int,
    path_prefix: Optional[str] = None,
    strict: Optional[bool] = False,
    is_extract: bool = True,
):
    judgement_mapping = await judgement_submission_mapping(client, cid)
    typer.echo(f"Download contest files, cid: {cid}.")
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

            if (
                submission.team_id not in teams_mapping
                or submission.problem_id not in problems_mapping
            ):
                return

            team = teams_mapping[submission.team_id]
            problem = problems_mapping[submission.problem_id]
            judgement_name = judgement_mapping.get(id)

            path = file_path(cid, mode, path_prefix, team, problem)
            await api.submission_files(
                cid,
                id,
                judgement_name,
                path,
                strict,
                is_extract,
            )

        count = 0
        with typer.progressbar(submissions) as progress:
            for task in progress:
                count += 1
                await get_source_codes(task)
        typer.echo(f"Download {count} submissions.")
