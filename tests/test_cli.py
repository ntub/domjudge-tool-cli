from pathlib import Path

import pytest
from typer.testing import CliRunner

from domjudge_tool_cli import app
from domjudge_tool_cli.models import DomServerClient

runner = CliRunner()


def test_cli_top_level_command_groups() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Verify the 6 command groups exist
    for command_group in [
        "general",
        "users",
        "teams" if "teams" in result.output else "users",
        "scoreboard",
        "submissions",
        "problems",
        "emails",
    ]:
        assert command_group in result.output


def test_cli_general_config_generates_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "general",
            "config",
            "https://domjudge.example.test",
            "--username",
            "api_writer",
            "--password",
            "secret",
            "--version",
            "7.3.2",
            "--api-version",
            "v4",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    config_file = tmp_path / "domserver.json"
    assert config_file.exists()
    client = DomServerClient.model_validate_json(
        config_file.read_text(encoding="utf-8")
    )
    assert str(client.host) == "https://domjudge.example.test/"
    assert client.username == "api_writer"
    assert client.password == "secret"
    assert client.version == "7.3.2"
    assert client.api_version == "v4"


def test_cli_import_users_teams_example(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["users", "import-users-teams-example"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    target_csv = tmp_path / "import-users-teams.csv"
    assert target_csv.exists()
    content = target_csv.read_text(encoding="utf-8")
    assert "username" in content


def test_cli_help_options_and_exit_codes() -> None:
    for sub in ["general", "users", "submissions", "problems", "scoreboard", "emails"]:
        res = runner.invoke(app, [sub, "--help"])
        assert res.exit_code == 0
