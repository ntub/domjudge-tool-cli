from typing import Any

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


def gen_submission_dataset(submissions: list[Any]) -> Dataset:
    dataset = Dataset()
    for idx, submission in enumerate(submissions):
        sub_dict = submission.model_dump()
        if idx == 0:
            dataset.headers = list(sub_dict.keys())

        dataset.append(list(sub_dict.values()))

    return dataset


def print_submissions_table(submissions: list[Submission]) -> None:
    dataset = gen_submission_dataset(submissions)
    typer.echo(dataset.export("cli", tablefmt="simple"))


def file_path(
    cid: str,
    mode: int,
    path: str | None,
    team: Any,
    problem: Any,
) -> str:
    team_name = getattr(team, "name", str(team))
    problem_name = getattr(problem, "short_name", None) or getattr(
        problem, "name", str(problem)
    )

    if mode == 1:
        filepath = f"team_{team_name}/problem_{problem_name}"
    elif mode == 2:
        filepath = f"problem_{problem_name}/team_{team_name}"
    else:
        filepath = f"contest_{cid}"

    if path:
        filepath = f"{path}/{filepath}"

    return filepath


def index_by_id(objs: list[Any]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for obj in objs:
        data[obj.id] = obj
    return data


async def judgement_submission_mapping(
    client: DomServerClient,
    cid: str,
) -> dict[str, str]:
    async with JudgementTypeAPI(**client.api_params) as api:
        judgement_types = await api.all_judgement_types(cid)

    async with JudgementAPI(**client.api_params) as api:
        judgements = await api.all_judgements(cid)

    judgement_type_mapping = {
        item.id: str(item.name).lower().replace(" ", "_") for item in judgement_types
    }
    return {
        item.submission_id: judgement_type_mapping.get(
            item.judgement_type_id or "", "NoJudgement"
        )
        for item in judgements
    }


async def get_submissions(
    client: DomServerClient,
    cid: str,
    language_id: str | None = None,
    strict: bool = False,
    ids: list[str] | None = None,
) -> None:
    async with SubmissionsAPI(**client.api_params) as api:
        submissions = await api.all_submissions(
            cid,
            language_id,
            strict,
            ids,
        )

        print_submissions_table(submissions)


async def download_submission_files(
    client: DomServerClient,
    cid: str,
    id: str,
    mode: int = 2,
    path: str | None = None,
    strict: bool = False,
    is_extract: bool = True,
) -> None:
    judgement_mapping = await judgement_submission_mapping(client, cid)

    async with (
        SubmissionsAPI(**client.api_params) as api,
        TeamsAPI(**client.api_params) as teams_api,
        ProblemsAPI(**client.api_params) as problems_api,
    ):
        submission = await api.submission(cid, id)
        team = await teams_api.team(cid, submission.team_id)
        problem = await problems_api.problem(cid, submission.problem_id)

        filepath = file_path(cid, mode, path, team, problem)
        judgement = judgement_mapping.get(
            submission.id,
            "NoJudgement",
        )
        filename = f"{team.name}_{problem.name}_{judgement}"

        await api.submission_files(
            cid,
            id,
            filename,
            filepath,
            strict,
            is_extract,
        )


async def download_contest_files(
    client: DomServerClient,
    cid: str,
    language_id: str | None = None,
    mode: int = 2,
    path: str | None = None,
    strict: bool = False,
    is_extract: bool = True,
) -> None:
    judgement_mapping = await judgement_submission_mapping(client, cid)

    async with (
        SubmissionsAPI(**client.api_params) as api,
        TeamsAPI(**client.api_params) as teams_api,
        ProblemsAPI(**client.api_params) as problems_api,
    ):
        submissions = await api.all_submissions(cid, language_id, strict)
        teams = index_by_id(await teams_api.all_teams(cid))
        problems = index_by_id(await problems_api.all_problems(cid))

        count = 0
        with typer.progressbar(submissions) as progress:
            for submission in progress:
                team = teams.get(submission.team_id)
                problem = problems.get(submission.problem_id)
                if not team or not problem:
                    continue

                filepath = file_path(cid, mode, path, team, problem)
                judgement = judgement_mapping.get(
                    submission.id,
                    "NoJudgement",
                )
                filename = f"{team.name}_{problem.name}_{judgement}"

                await api.submission_files(
                    cid,
                    submission.id,
                    filename,
                    filepath,
                    strict,
                    is_extract,
                )
                count += 1

        typer.echo(f"Download {count} submissions.")
