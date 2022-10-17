from domjudge_tool_cli.services.api_client import APIClient


class V4Client(APIClient):
    API_VERSION = "v4"
    API_PREFIX = f"/api/{API_VERSION}"

    def make_resource(self, path: str) -> str:
        return f"{self.API_PREFIX}{path}"
