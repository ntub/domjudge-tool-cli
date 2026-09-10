import asyncio
from typing import Annotated

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
    cid: Annotated[str, typer.Argument(help="Contest id.")],
    language_id: Annotated[
        str | None,
        typer.Option(help="Language id."),
    ] = None,
    strict: Annotated[bool, typer.Option(help="Strict mode.")] = False,
    ids: Annotated[
        str | None,
        typer.Option(help="submission_id1,submission_id2,submission_id3"),
    ] = None,
) -> None:
    """
    Get contest submission list.
    """
    submission_ids = ids.split(",") if ids else None

    client = get_or_ask_config(general_state["config"])
    asyncio.run(get_submissions(client, cid, language_id, strict, submission_ids))


@app.command()
def submission_file(
    cid: Annotated[str, typer.Argument(help="Contest id.")],
    id: Annotated[str, typer.Argument(help="Submission id.")],
    mode: Annotated[
        int,
        typer.Argument(
            help=(
                "Output path format mode:\n"
                "mode=1: team_name/problem_name/submission_file.\n"
                "mode=2: problem_name/team_name/submission_file.\n"
                "other: contest_id/submission_file"
            ),
        ),
    ] = 2,
    path: Annotated[
        str | None,
        typer.Option(help="Export path."),
    ] = None,
    strict: Annotated[bool, typer.Option(help="Strict mode.")] = False,
    is_extract: Annotated[
        bool,
        typer.Option(help="Extract file?"),
    ] = True,
) -> None:
    """
    Download a submission files.
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
    cid: Annotated[str, typer.Argument(help="Contest id.")],
    language_id: Annotated[
        str | None,
        typer.Option(help="Language id."),
    ] = None,
    mode: Annotated[
        int,
        typer.Argument(
            help=(
                "Output path format mode:\n"
                "mode=1: team_name/problem_name/submission_file.\n"
                "mode=2: problem_name/team_name/submission_file.\n"
                "other: contest_id/submission_file"
            ),
        ),
    ] = 2,
    path: Annotated[
        str | None,
        typer.Option(help="Export path."),
    ] = None,
    strict: Annotated[bool, typer.Option(help="Strict mode.")] = False,
    is_extract: Annotated[
        bool,
        typer.Option(help="Extract file?"),
    ] = True,
) -> None:
    """
    Download all submissions in contest.
    """
    client = get_or_ask_config(general_state["config"])
    asyncio.run(
        download_contest_files(
            client,
            cid,
            language_id,
            mode,
            path,
            strict,
            is_extract,
        )
    )
