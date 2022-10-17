from typing import List, Optional

from domjudge_tool_cli.models import JudgementType
from domjudge_tool_cli.services.api.v4.base import V4Client


class JudgementTypeAPI(V4Client):
    async def all_judgement_types(
        self,
        cid: str,
        strict: Optional[bool] = False,
        ids: Optional[List[str]] = None,
    ) -> List[JudgementType]:
        path = self.make_resource(f"/contests/{cid}/judgement-types")
        params = dict()

        if ids:
            params["ids[]"] = ids

        if strict:
            params["strict"] = strict

        response = await self.get(
            path,
            params if params else None,
        )

        return list(map(lambda it: JudgementType(**it), response))

    async def judgement_type(
        self, cid: str, id: str, strict: Optional[bool] = False
    ) -> JudgementType:
        path = self.make_resource(f"/contests/{cid}/judgement-types/{id}")
        params = dict()

        if strict:
            params["strict"] = strict

        result = await self.get(
            path,
            params if params else None,
        )
        return JudgementType(**result)
