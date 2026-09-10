from domjudge_tool_cli.services.web import v7, v8
from domjudge_tool_cli.services.web.base import BaseDomServerWeb

__all__ = [
    "DomServerWebGateway",
]


class DomServerWebGateway:
    version_client: dict[str, type[BaseDomServerWeb]] = {
        "7.3.2": v7.DomServerWeb,
        "7.3.4": v7.DomServerWeb,
        "8.1.3": v8.DomServerWeb,
    }

    def __new__(cls, version: str) -> type[BaseDomServerWeb]:
        if version not in cls.version_client:
            raise ValueError(f"Unsupported DOMjudge version: {version}")
        return cls.version_client[version]
