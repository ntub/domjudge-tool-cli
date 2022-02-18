from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, HttpUrl


class DomServerClient(BaseModel):
    host: HttpUrl
    username: str
    password: str
    disable_ssl: bool = False
    timeout: Optional[float] = None
    max_connections: Optional[int] = None
    max_keepalive_connections: Optional[int] = None
    category_id: Optional[int] = None
    affiliation_id: Optional[int] = None
    affiliation_country: Optional[str] = "TWN"
    user_roles: Optional[List[int]] = None

    @property
    def get_timeout(self) -> Optional["httpx.Timeout"]:
        if self.timeout:
            return httpx.Timeout(self.timeout)

    @property
    def get_limits(self) -> Optional["httpx.Limits"]:
        if self.max_connections or self.max_keepalive_connections:
            return httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=self.max_keepalive_connections,
            )

    @property
    def api_params(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "username": self.username,
            "password": self.password,
            "disable_ssl": self.disable_ssl,
            "timeout": self.get_timeout,
            "limits": self.get_limits,
        }
