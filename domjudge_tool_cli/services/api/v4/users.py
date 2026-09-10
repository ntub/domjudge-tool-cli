from typing import Any

from domjudge_tool_cli.models import User
from domjudge_tool_cli.services.api.v4.base import V4Client


class UsersAPI(V4Client):
    async def all_users(
        self,
        ids: list[str] | None = None,
        team_id: str | None = None,
    ) -> list[User]:
        path = self.make_resource("/users")
        params: dict[str, Any] = {}

        if ids:
            params["ids[]"] = ids

        if team_id:
            params["team_id"] = team_id

        result = await self.get(
            path,
            params if params else None,
        )
        return [User.model_validate(it) for it in result]

    async def get_user(
        self,
        id: str,
    ) -> User:
        path = self.make_resource(f"/users/{id}")
        result = await self.get(path)
        return User.model_validate(result)
