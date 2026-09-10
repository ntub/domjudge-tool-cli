from domjudge_tool_cli.models import Team
from domjudge_tool_cli.services.api.v4.base import V4Client


class TeamsAPI(V4Client):
    async def all_teams(
        self,
        cid: str,
    ) -> list[Team]:
        path = self.make_resource(f"/contests/{cid}/teams")
        result = await self.get(path)
        return [Team.model_validate(it) for it in result]

    async def team(self, cid: str, id: str) -> Team:
        path = self.make_resource(f"/contests/{cid}/teams/{id}")
        result = await self.get(path)
        return Team.model_validate(result)
