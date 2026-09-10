import importlib.metadata

import domjudge_tool_cli


def test_version() -> None:
    expected_version = importlib.metadata.version("domjudge-tool-cli")
    assert domjudge_tool_cli.__version__ == expected_version
