from typing import Any

from domjudge_tool_cli.models import JudgementType
from domjudge_tool_cli.services.api.v4.base import V4Client


class JudgementTypeAPI(V4Client):
    async def all_judgement_types(
        self,
        cid: str,
        strict: bool = False,
        ids: list[str] | None = None,
    ) -> list[JudgementType]:
        path = self.make_resource(f"/contests/{cid}/judgement-types")
        params: dict[str, Any] = {}

        if ids:
            params["ids[]"] = ids

        if strict:
            params["strict"] = strict

        response = await self.get(
            path,
            params if params else None,
        )

        return [JudgementType.model_validate(it) for it in response]

    async def judgement_type(
        self, cid: str, id: str, strict: bool = False
    ) -> JudgementType:
        path = self.make_resource(f"/contests/{cid}/judgement-types/{id}")
        params: dict[str, Any] = {}

        if strict:
            params["strict"] = strict

        result = await self.get(
            path,
            params if params else None,
        )
        return JudgementType.model_validate(result)
