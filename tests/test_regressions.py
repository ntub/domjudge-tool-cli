import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from domjudge_tool_cli import app
from domjudge_tool_cli.commands.submissions._submissions import (
    file_path,
    judgement_submission_mapping,
)
from domjudge_tool_cli.commands.users._users import (
    create_team_and_user,
    delete_teams_and_users,
)
from domjudge_tool_cli.models import (
    Affiliation,
    CreateUser,
    DomServerClient,
    Judgement,
    JudgementType,
    ProblemItem,
    Team,
    User,
)

runner = CliRunner()


def test_rm_teams_and_users_has_include_and_exclude_options() -> None:
    res = runner.invoke(app, ["users", "rm-teams-and-users", "--help"])
    assert res.exit_code == 0
    assert "--include" in res.output
    assert "--exclude" in res.output


def test_submissions_file_path_layout() -> None:
    team = Team(id="1", name="TeamAlpha", group_ids=["1"])
    problem = ProblemItem(id="A", name="Problem A", time_limit=1, test_data_count=2)

    # mode 1 without custom path
    p1 = file_path("42", 1, None, team, problem)
    assert p1 == "team_TeamAlpha/problem_Problem A"
    assert not p1.startswith("None/")

    # mode 2 without custom path
    p2 = file_path("42", 2, None, team, problem)
    assert p2 == "problem_Problem A/team_TeamAlpha"

    # mode 1 with custom path
    p3 = file_path("42", 1, "/tmp/export", team, problem)
    assert p3.startswith("/tmp/export/")


def test_create_team_and_user_with_supplied_password() -> None:
    client = DomServerClient(
        host="https://domserver.example.test",  # type: ignore[arg-type]
        username="admin",
        password="password",
        category_id=1,
        affiliation_id=2,
        user_roles=[3],
    )
    user = CreateUser(
        username="alice",
        name="Alice",
        password="explicit_secret_password",
    )

    mock_web = AsyncMock()
    mock_web.__aenter__.return_value = mock_web
    mock_web.__aexit__.return_value = None
    mock_web.login.return_value = None
    mock_web.create_team_and_user.return_value = ("team_10", "user_10")
    mock_web.set_user_password.return_value = None

    mock_cls = MagicMock(return_value=mock_web)
    mock_gateway_cls = MagicMock(return_value=mock_cls)

    with patch(
        "domjudge_tool_cli.commands.users._users.DomServerWebGateway",
        mock_gateway_cls,
    ):
        result = asyncio.run(
            create_team_and_user(
                client=client,
                user=user,
            )
        )

    assert result.username == "alice"
    assert result.password == "explicit_secret_password"
    # Ensure set_user_password was called with the supplied password
    mock_web.set_user_password.assert_awaited_once_with(
        "user_10",
        "explicit_secret_password",
        [3],
        True,
    )


def test_create_team_and_user_with_existing_user() -> None:
    client = DomServerClient(
        host="https://domserver.example.test",  # type: ignore[arg-type]
        username="admin",
        password="password",
        category_id=1,
        affiliation_id=2,
        user_roles=[3],
    )
    existing_user = User(
        id="u99",
        username="bob",
        name="Bob",
        team_id="t99",
    )

    mock_web = AsyncMock()
    mock_web.__aenter__.return_value = mock_web
    mock_web.__aexit__.return_value = None
    mock_web.login.return_value = None
    mock_web.update_team.return_value = ("t99", "u99")
    mock_web.set_user_password.return_value = None

    mock_cls = MagicMock(return_value=mock_web)
    mock_gateway_cls = MagicMock(return_value=mock_cls)

    with patch(
        "domjudge_tool_cli.commands.users._users.DomServerWebGateway",
        mock_gateway_cls,
    ):
        result = asyncio.run(
            create_team_and_user(
                client=client,
                user=existing_user,
            )
        )

    assert isinstance(result, CreateUser)
    assert result.username == "bob"
    mock_web.update_team.assert_awaited_once()
    mock_web.set_user_password.assert_awaited_once()


def test_create_team_and_user_resolves_per_user_affiliation() -> None:
    client = DomServerClient(
        host="https://domserver.example.test",  # type: ignore[arg-type]
        username="admin",
        password="password",
        category_id=1,
        affiliation_id=2,
        user_roles=[3],
    )
    user = CreateUser(
        username="carol",
        name="Carol",
        affiliation="Custom Affiliation",
    )

    mock_web = AsyncMock()
    mock_web.__aenter__.return_value = mock_web
    mock_web.__aexit__.return_value = None
    mock_web.login.return_value = None
    mock_web.get_affiliation.return_value = None
    mock_web.create_affiliation.return_value = Affiliation(
        id="999",
        shortname="Custom Affiliation",
        name="Custom Affiliation",
        country="TWN",
    )
    mock_web.create_team_and_user.return_value = ("team_50", "user_50")
    mock_web.set_user_password.return_value = None

    mock_cls = MagicMock(return_value=mock_web)
    mock_gateway_cls = MagicMock(return_value=mock_cls)

    with patch(
        "domjudge_tool_cli.commands.users._users.DomServerWebGateway",
        mock_gateway_cls,
    ):
        asyncio.run(
            create_team_and_user(
                client=client,
                user=user,
            )
        )

    mock_web.get_affiliation.assert_awaited_once_with("Custom Affiliation")
    mock_web.create_affiliation.assert_awaited_once_with(
        "Custom Affiliation",
        "Custom Affiliation",
        "TWN",
    )
    mock_web.create_team_and_user.assert_awaited_once_with(
        user,
        1,
        999,
        True,
    )


def test_judgement_submission_mapping_logic() -> None:
    client = DomServerClient(
        host="https://domserver.example.test",  # type: ignore[arg-type]
        username="admin",
        password="password",
    )

    mock_types_api = AsyncMock()
    mock_types_api.__aenter__.return_value = mock_types_api
    mock_types_api.__aexit__.return_value = None
    mock_types_api.all_judgement_types.return_value = [
        JudgementType(id="AC", name="Correct", penalty=False, solved=True),
        JudgementType(id="WA", name="Wrong Answer", penalty=True, solved=False),
    ]

    mock_judgements_api = AsyncMock()
    mock_judgements_api.__aenter__.return_value = mock_judgements_api
    mock_judgements_api.__aexit__.return_value = None
    mock_judgements_api.all_judgements.return_value = [
        Judgement(id="j1", submission_id="sub_100", judgement_type_id="AC", valid=True),
        Judgement(id="j2", submission_id="sub_101", judgement_type_id="WA", valid=True),
    ]

    with (
        patch(
            "domjudge_tool_cli.commands.submissions._submissions.JudgementTypeAPI",
            return_value=mock_types_api,
        ),
        patch(
            "domjudge_tool_cli.commands.submissions._submissions.JudgementAPI",
            return_value=mock_judgements_api,
        ),
    ):
        mapping = asyncio.run(judgement_submission_mapping(client, "1"))

    assert mapping["sub_100"] == "correct"
    assert mapping["sub_101"] == "wrong_answer"


def test_delete_teams_and_users_normalizes_casing() -> None:
    client = DomServerClient(
        host="https://domserver.example.test",  # type: ignore[arg-type]
        username="admin",
        password="password",
    )

    mock_users_api = AsyncMock()
    mock_users_api.__aenter__.return_value = mock_users_api
    mock_users_api.__aexit__.return_value = None
    mock_users_api.all_users.return_value = [
        User(id="1", username="admin", name="Admin", team_id="t1"),
        User(id="2", username="student1", name="Student 1", team_id="t2"),
    ]

    mock_web = AsyncMock()
    mock_web.__aenter__.return_value = mock_web
    mock_web.__aexit__.return_value = None
    mock_cls = MagicMock(return_value=mock_web)
    mock_gateway_cls = MagicMock(return_value=mock_cls)

    with (
        patch(
            "domjudge_tool_cli.commands.users._users.UsersAPI",
            return_value=mock_users_api,
        ),
        patch(
            "domjudge_tool_cli.commands.users._users.DomServerWebGateway",
            mock_gateway_cls,
        ),
    ):
        # Attempt to delete Admin with uppercase casing
        asyncio.run(
            delete_teams_and_users(
                client=client,
                include=["Admin", "student1"],
            )
        )

    # admin should be filtered out
    mock_web.delete_users.assert_awaited_once_with(
        ["student1"],
        ["admin", "judgehost", "admin"],
    )
    mock_web.delete_teams.assert_awaited_once_with(["t2"], ["t1"])
