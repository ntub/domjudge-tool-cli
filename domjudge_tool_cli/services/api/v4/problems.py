from io import BytesIO
from typing import List, Optional

from domjudge_tool_cli.models import Problem
from domjudge_tool_cli.services.api.v4.base import V4Client


class ProblemsAPI(V4Client):
    async def all_problems(
        self,
        cid: str,
    ) -> List[Problem]:
        path = self.make_resource(f"/contests/{cid}/problems")
        result = await self.get(path)
        return list(map(lambda it: Problem(**it), result))

    async def problem(self, cid: str, id: str) -> Problem:
        path = self.make_resource(f"/contests/{cid}/problems/{id}")
        result = await self.get(path)
        return Problem(**result)
