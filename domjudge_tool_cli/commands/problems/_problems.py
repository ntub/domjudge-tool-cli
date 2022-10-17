from typing import List, Optional

import aiofiles
import typer
from aiofiles import os as aio_os

from domjudge_tool_cli.models import DomServerClient
from domjudge_tool_cli.services.web import DomServerWebGateway


async def download_problems_zips(
    client: DomServerClient,
    exclude: Optional[List[str]] = None,
    only: Optional[List[str]] = None,
    folder: Optional[str] = None,
) -> None:
    if not folder:
        folder = "export_problems"

    is_dir = await aio_os.path.isdir(folder)
    if not is_dir:
        await aio_os.makedirs(folder, exist_ok=True)

    DomServerWeb = DomServerWebGateway(client.version)
    async with DomServerWeb(**client.api_params) as web:
        await web.login()
        problems = await web.get_problems(exclude, only)

        with typer.progressbar(problems, label="Download problems:") as progress:
            for problem in progress:
                export_file_path = problem.export_file_path
                disk_file_path = f"{folder}/{problem.id}_{problem.name}.zip"
                disk_file_path = disk_file_path.replace(" ", "-")
                if not export_file_path:
                    continue

                r = await web.get(export_file_path)
                async with aiofiles.open(disk_file_path, mode="wb") as f:
                    await f.write(r.content)

        typer.echo(f"Processed {len(problems)} problems.")
