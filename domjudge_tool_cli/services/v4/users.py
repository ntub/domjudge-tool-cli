from typing import List, Optional

from domjudge_tool_cli.models import User

from .base import V4Client


class UsersAPI(V4Client):
    async def all_users(
        self,
        ids: Optional[List[str]] = None,
        team_id: Optional[str] = None,
    ) -> List[User]:
        path = self.make_resource("/users")
        params = dict()

        if ids:
            params["ids[]"] = ids

        if team_id:
            params["team_id"] = team_id

        result = await self.get(
            path,
            params if params else None,
        )
        return list(map(lambda it: User(**it), result))

    async def get_user(
        self,
        id: str,
    ) -> User:
        path = self.make_resource(f"/users/{id}")

        result = await self.get(path)
        return User(**result)
