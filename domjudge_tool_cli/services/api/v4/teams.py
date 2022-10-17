from io import BytesIO
from typing import List, Optional

from domjudge_tool_cli.models import Team
from domjudge_tool_cli.services.api.v4.base import V4Client


class TeamsAPI(V4Client):
    async def all_teams(
        self,
        cid: str,
    ) -> List[Team]:
        path = self.make_resource(f"/contests/{cid}/teams")
        result = await self.get(path)
        return list(map(lambda it: Team(**it), result))

    async def team(self, cid: str, id: str) -> Team:
        path = self.make_resource(f"/contests/{cid}/teams/{id}")
        result = await self.get(path)
        return Team(**result)
