from domjudge_tool_cli.models import Problem
from domjudge_tool_cli.services.api.v4.base import V4Client


class ProblemsAPI(V4Client):
    async def all_problems(
        self,
        cid: str,
    ) -> list[Problem]:
        path = self.make_resource(f"/contests/{cid}/problems")
        result = await self.get(path)
        return [Problem.model_validate(it) for it in result]

    async def problem(self, cid: str, id: str) -> Problem:
        path = self.make_resource(f"/contests/{cid}/problems/{id}")
        result = await self.get(path)
        return Problem.model_validate(result)
