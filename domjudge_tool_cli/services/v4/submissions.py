from typing import List, Optional

import aiofiles
from aiofiles import os as aio_os

from domjudge_tool_cli.models import Submission, SubmissionFile
from domjudge_tool_cli.services.v4.base import V4Client


class SubmissionsAPI(V4Client):
    async def all_submissions(
        self,
        cid: str,
        language_id: Optional[str] = None,
        strict: Optional[bool] = False,
        ids: Optional[List[str]] = None,
    ) -> List[Submission]:
        path = self.make_resource(f"/contests/{cid}/submissions")
        params = dict()

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

        return list(map(lambda it: Submission(**it), result))

    async def submission(self, cid: str, id: str) -> Submission:
        path = self.make_resource(f"/contests/{cid}/submissions/{id}")
        result = await self.get(path)
        return Submission(**result)

    async def submission_files(
        self,
        cid: str,
        id: str,
        filename: str,
        file_path: Optional[str] = None,
        strict: Optional[bool] = False,
    ) -> any:
        is_dir = await aio_os.path.isdir(file_path)
        if not is_dir:
            await aio_os.makedirs(file_path, exist_ok=True)

        path = self.make_resource(f"/contests/{cid}/submissions/{id}/files")
        result = await self.get_file(path)
        async with aiofiles.open(f"{file_path}/{id}-{filename}.zip", "wb") as f:
            await f.write(result)

    async def submission_file_name(
        self,
        cid: str,
        id: str,
    ) -> SubmissionFile:

        path = self.make_resource(f"/contests/{cid}/submissions/{id}/source-code")
        result = await self.get(path)
        return SubmissionFile(**result[0])
