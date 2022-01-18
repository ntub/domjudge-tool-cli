from io import BytesIO
from typing import Optional, List

from domjudge_tool_cli.models import Problem
from .base import V4Client


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
