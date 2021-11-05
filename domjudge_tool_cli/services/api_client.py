import httpx

from functools import cached_property
from typing import Dict, Any, Optional


class BaseClient:
    def __init__(
        self,
        host: str,
        disable_ssl: Optional[bool] = None,
        timeout: Optional[httpx.Timeout] = None,
        limits: Optional[httpx.Limits] = None,
    ):
        self.host = host
        self._parameters = dict(base_url=host)

        if disable_ssl:
            self._parameters["verify_ssl"] = False

        if timeout:
            self._parameters["timeout"] = timeout

        if limits:
            self._parameters["limits"] = limits


class APIClient(BaseClient):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        disable_ssl: Optional[bool] = None,
        timeout: Optional[httpx.Timeout] = None,
        limits: Optional[httpx.Limits] = None,
    ):
        self.username = username
        self.password = password
        self._parameters = dict(
            base_url=host,
            auth=httpx.BasicAuth(username, password),
        )
        super().__init__(host, disable_ssl, timeout, limits)

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


class WebClient(BaseClient):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        disable_ssl: Optional[bool] = None,
        timeout: Optional[httpx.Timeout] = None,
        limits: Optional[httpx.Limits] = None,
    ):
        self.username = username
        self.password = password
        super().__init__(host, disable_ssl, timeout, limits)
        self.client = httpx.AsyncClient(**self._parameters)

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        r = await self.client.get(  # type: httpx.Response
            path,
            params=params,
            allow_redirects=True,
        )
        r.raise_for_status()
        return r

    async def post(
        self,
        path: str,
        body: Dict[str, Any],
    ) -> httpx.Response:
        r = await self.client.post(  # type: httpx.Response
            path,
            data=body,
            allow_redirects=True,
        )
        r.raise_for_status()
        return r

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
