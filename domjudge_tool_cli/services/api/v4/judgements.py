from typing import List, Optional

from domjudge_tool_cli.models import Judgement
from domjudge_tool_cli.services.api.v4.base import V4Client


class JudgementAPI(V4Client):
    async def all_judgements(
        self,
        cid: str,
        submission_id: Optional[str] = None,
        result: Optional[str] = None,
        strict: Optional[bool] = False,
        ids: Optional[List[str]] = None,
    ) -> List[Judgement]:
        path = self.make_resource(f"/contests/{cid}/judgements")
        params = dict()

        if ids:
            params["ids[]"] = ids

        if strict:
            params["strict"] = strict

        if result:
            params["result"] = result

        if submission_id:
            params["submission_id"] = submission_id

        response = await self.get(
            path,
            params if params else None,
        )

        return list(map(lambda it: Judgement(**it), response))

    async def judgement(self, cid: str, id: str) -> Judgement:
        path = self.make_resource(f"/contests/{cid}/judgements/{id}")
        result = await self.get(path)
        return Judgement(**result)
