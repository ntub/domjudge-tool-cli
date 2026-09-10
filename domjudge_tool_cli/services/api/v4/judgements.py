from typing import Any

from domjudge_tool_cli.models import Judgement
from domjudge_tool_cli.services.api.v4.base import V4Client


class JudgementAPI(V4Client):
    async def all_judgements(
        self,
        cid: str,
        submission_id: str | None = None,
        result: str | None = None,
        strict: bool = False,
        ids: list[str] | None = None,
    ) -> list[Judgement]:
        path = self.make_resource(f"/contests/{cid}/judgements")
        params: dict[str, Any] = {}

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

        return [Judgement.model_validate(it) for it in response]

    async def judgement(self, cid: str, id: str) -> Judgement:
        path = self.make_resource(f"/contests/{cid}/judgements/{id}")
        result = await self.get(path)
        return Judgement.model_validate(result)
