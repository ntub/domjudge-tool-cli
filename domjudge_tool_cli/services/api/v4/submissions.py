import logging
import os
import shutil
from glob import glob
from pathlib import Path
from typing import Any

import aiofiles
from aiofiles import os as aio_os

from domjudge_tool_cli.models import Submission, SubmissionFile
from domjudge_tool_cli.services.api.v4.base import V4Client

unpack_archive = aio_os.wrap(shutil.unpack_archive)


class SubmissionsAPI(V4Client):
    async def all_submissions(
        self,
        cid: str,
        language_id: str | None = None,
        strict: bool = False,
        ids: list[str] | None = None,
    ) -> list[Submission]:
        path = self.make_resource(f"/contests/{cid}/submissions")
        params: dict[str, Any] = {}

        if ids:
            params["ids[]"] = ids

        if strict:
            params["strict"] = strict

        if language_id:
            params["language_id"] = language_id

        result = await self.get(
            path,
            params if params else None,
        )

        return [Submission.model_validate(it) for it in result]

    async def submission(self, cid: str, id: str) -> Submission:
        path = self.make_resource(f"/contests/{cid}/submissions/{id}")
        result = await self.get(path)
        return Submission.model_validate(result)

    async def submission_files(
        self,
        cid: str,
        id: str,
        filename: str,
        file_path: str | None = None,
        strict: bool = False,
        is_extract: bool = False,
    ) -> str:
        target_dir = str(Path(file_path or ".").expanduser().resolve())
        is_dir = await aio_os.path.isdir(target_dir)
        if not is_dir:
            await aio_os.makedirs(target_dir, exist_ok=True)

        path = self.make_resource(f"/contests/{cid}/submissions/{id}/files")
        result = await self.get_file(path)
        file_name = f"{filename}_{id}.zip"
        zip_path = Path(target_dir) / file_name
        async with aiofiles.open(zip_path, "wb") as f:
            await f.write(result)

        if is_extract:
            async with aiofiles.tempfile.TemporaryDirectory() as temp_dir:
                await unpack_archive(zip_path, temp_dir, "zip")
                files = list(glob(str(temp_dir) + "/*"))
                if not files:
                    logging.warning(f"{zip_path} unzip fail!")
                    return ""
                file = files[0]
                file_ex = os.path.splitext(file)[-1]
                await aio_os.rename(
                    file,
                    Path(target_dir) / f"{filename}_{id}{file_ex}",
                )
                await aio_os.remove(zip_path)

        return file_name

    async def submission_file_name(
        self,
        cid: str,
        id: str,
    ) -> SubmissionFile:
        path = self.make_resource(f"/contests/{cid}/submissions/{id}/source-code")
        result = await self.get(path)
        return SubmissionFile.model_validate(result[0])
