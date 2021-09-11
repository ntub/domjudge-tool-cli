import httpx

from functools import cached_property
from typing import Dict, Any, Optional


class APIClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        disable_ssl: Optional[bool] = None,
        timeout: Optional[httpx.Timeout] = None,
        limits: Optional[httpx.Limits] = None,
    ):
        self.host = host
        self.username = username
        self.password = password
        self._parameters = dict(
            base_url=host,
            auth=httpx.BasicAuth(username, password),
        )

        if disable_ssl:
            self._parameters["verify_ssl"] = False

        if timeout:
            self._parameters["timeout"] = timeout

        if limits:
            self._parameters["limits"] = limits

    @cached_property
    def client(self) -> "httpx.AsyncClient":
        return httpx.AsyncClient(**self._parameters)

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        async with self.client as client:
            r = await client.get(path, params=params)  # type: httpx.Response
            r.raise_for_status()
            return r.json()
