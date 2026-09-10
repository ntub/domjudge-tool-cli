from typing import Any

import httpx
from pydantic import BaseModel, HttpUrl


class DomServerClient(BaseModel):
    host: HttpUrl
    username: str
    password: str
    disable_ssl: bool = False
    timeout: float = 60.0
    max_connections: int | None = None
    max_keepalive_connections: int | None = None
    category_id: int | None = None
    affiliation_id: int | None = None
    affiliation_country: str | None = "TWN"
    user_roles: list[int] | None = None
    version: str = "7.3.2"
    api_version: str = "v4"

    @property
    def get_timeout(self) -> httpx.Timeout | None:
        if self.timeout is not None:
            return httpx.Timeout(self.timeout)
        return None

    @property
    def get_limits(self) -> httpx.Limits | None:
        if (
            self.max_connections is not None
            or self.max_keepalive_connections is not None
        ):
            return httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=self.max_keepalive_connections,
            )
        return None

    @property
    def api_params(self) -> dict[str, Any]:
        return {
            "host": str(self.host),
            "username": self.username,
            "password": self.password,
            "disable_ssl": self.disable_ssl,
            "timeout": self.get_timeout,
            "limits": self.get_limits,
        }
