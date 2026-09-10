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
        "8.3": v8.DomServerWeb,
        "8.3.1": v8.DomServerWeb,
    }

    def __new__(cls, version: str) -> type[BaseDomServerWeb]:
        version = version.strip()
        if version in cls.version_client:
            return cls.version_client[version]
        if version == "7.3" or version.startswith("7.3."):
            return v7.DomServerWeb
        if version == "8.3" or version.startswith("8.3."):
            return v8.DomServerWeb
        raise ValueError(f"Unsupported DOMjudge version: {version}")
