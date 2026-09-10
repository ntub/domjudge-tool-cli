from typing import Any, Self

import httpx


class BaseClient:
    def __init__(
        self,
        host: str,
        disable_ssl: bool = False,
        timeout: httpx.Timeout | None = None,
        limits: httpx.Limits | None = None,
        **extra_params: Any,
    ):
        self.host = host
        parameters: dict[str, Any] = {"base_url": host}

        if disable_ssl:
            parameters["verify"] = False

        if timeout is not None:
            parameters["timeout"] = timeout

        if limits is not None:
            parameters["limits"] = limits

        parameters.update(extra_params)
        self._parameters = parameters
        self.client = self.new_client()

    def new_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**self._parameters)

    async def __aenter__(self) -> Self:
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def is_closed(self) -> bool:
        return self.client.is_closed


class APIClient(BaseClient):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        disable_ssl: bool = False,
        timeout: httpx.Timeout | None = None,
        limits: httpx.Limits | None = None,
    ):
        self.username = username
        self.password = password
        super().__init__(
            host=host,
            disable_ssl=disable_ssl,
            timeout=timeout,
            limits=limits,
            auth=httpx.BasicAuth(username, password),
        )

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        r = await self.client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    async def get_file(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> bytes:
        r = await self.client.get(path, params=params)
        r.raise_for_status()
        return r.content


class WebClient(BaseClient):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        disable_ssl: bool = False,
        timeout: httpx.Timeout | None = None,
        limits: httpx.Limits | None = None,
    ):
        self.username = username
        self.password = password
        super().__init__(
            host=host,
            disable_ssl=disable_ssl,
            timeout=timeout,
            limits=limits,
        )

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        r = await self.client.get(
            path,
            params=params,
            follow_redirects=True,
        )
        r.raise_for_status()
        return r

    async def post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        r = await self.client.post(
            path,
            data=body,
            follow_redirects=True,
        )
        r.raise_for_status()
        return r
