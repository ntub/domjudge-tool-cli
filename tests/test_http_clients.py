import asyncio

import httpx
import pytest

from domjudge_tool_cli.services.api.v4.users import UsersAPI
from domjudge_tool_cli.services.api_client import APIClient, BaseClient, WebClient


def test_base_client_lifecycle() -> None:
    async def run() -> None:
        async with BaseClient("https://example.test") as client:
            assert not client.is_closed
        assert client.is_closed

    asyncio.run(run())


def test_api_client_get_success_and_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v4/users":
            return httpx.Response(
                200,
                json=[{"id": "1", "username": "alice", "name": "Alice"}],
            )
        return httpx.Response(401, json={"message": "Unauthorized"})

    transport = httpx.MockTransport(handler)

    async def run_success() -> None:
        client = APIClient("https://example.test", "admin", "secret")
        # Replace inner client with mock transport
        client.client = httpx.AsyncClient(
            transport=transport,
            base_url="https://example.test",
        )
        data = await client.get("/api/v4/users")
        assert len(data) == 1
        assert data[0]["username"] == "alice"

    async def run_error() -> None:
        client = APIClient("https://example.test", "admin", "wrong")
        client.client = httpx.AsyncClient(
            transport=transport,
            base_url="https://example.test",
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get("/api/v4/forbidden")
        assert exc_info.value.response.status_code == 401

    asyncio.run(run_success())
    asyncio.run(run_error())


def test_users_api_model_validation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {"id": "1", "username": "u1", "name": "User 1"},
                {"id": "2", "username": "u2", "name": "User 2"},
            ],
        )

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        api = UsersAPI("https://example.test", "admin", "secret")
        api.client = httpx.AsyncClient(
            transport=transport,
            base_url="https://example.test",
        )
        users = await api.all_users()
        assert len(users) == 2
        assert users[0].id == "1"
        assert users[1].username == "u2"

    asyncio.run(run())


def test_web_client_follow_redirects() -> None:
    recorded_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        if request.url.path == "/old-path":
            return httpx.Response(
                302,
                headers={"Location": "https://example.test/new-path"},
            )
        return httpx.Response(200, text="OK")

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        client = WebClient("https://example.test", "user", "pass")
        client.client = httpx.AsyncClient(
            transport=transport,
            base_url="https://example.test",
        )
        res = await client.get("/old-path")
        assert res.status_code == 200
        assert str(res.url) == "https://example.test/new-path"

    asyncio.run(run())
