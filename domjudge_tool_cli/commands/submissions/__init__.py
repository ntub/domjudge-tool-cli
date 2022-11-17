import asyncio
from typing import List, Optional

import typer

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config
from domjudge_tool_cli.commands.submissions._submissions import (
    download_contest_files,
    download_submission_files,
    get_submissions,
)

app = typer.Typer()


@app.command()
def submission_list(
    cid: str,
    language_id: Optional[str] = None,
    strict: Optional[bool] = False,
    ids: Optional[List[str]] = None,
):
    """
    Console log submissions.
    Args:
        cid: *Contest id.
        language_id:
        strict:
        ids: Submission ids.
    """
    submission_ids = None
    if ids:
        submission_ids = ids.split(",")

    client = get_or_ask_config(general_state["config"])
    asyncio.run(get_submissions(client, cid, language_id, strict, submission_ids))


@app.command()
def submission_file(
    cid: str,
    id: str,
    mode: int = typer.Argument(
        default=2,
        help="""
            Output path format mode:\n
            mode=1: team_name/problem_name/submission_file.
            mode=2: problem_name/team_name/submission_file.
            other: contest_id/submission_file
            """,
    ),
    path: Optional[str] = None,
    strict: Optional[bool] = False,
    is_extract: bool = True,
):
    """
    Download a submission source code files.
    Args:
        cid: Contest id.
        id: Submission id.
        mode: Output path format mode.
        path: Output path.
        strict:
        is_extract: unzip file if true.
    """
    client = get_or_ask_config(general_state["config"])
    asyncio.run(
        download_submission_files(
            client,
            cid,
            id,
            mode,
            path,
            strict,
            is_extract,
        )
    )


@app.command()
def contest_files(
    cid: str,
    mode: int = typer.Argument(
        default=2,
        help="""
        Output path format mode:\n
        mode=1: team_name/problem_name/submission_file.
        mode=2: problem_name/team_name/submission_file.
        other: contest_id/submission_file
        """,
    ),
    path: Optional[str] = None,
    strict: Optional[bool] = False,
    is_extract: bool = True,
):
    """
    Download a contest all submissions source code files.
    Args:
        cid: Contest id.
        mode: Output path format mode.
        path: Output path.
        strict:
        is_extract: unzip file if true.
    """
    client = get_or_ask_config(general_state["config"])
    asyncio.run(
        download_contest_files(
            client,
            cid,
            mode,
            path,
            strict,
            is_extract,
        )
    )
