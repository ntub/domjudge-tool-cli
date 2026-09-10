from domjudge_tool_cli.models import (
    Affiliation,
    CreateUser,
    DomServerClient,
    Judgement,
    Problem,
    ProblemItem,
    Submission,
    SubmissionFile,
    Team,
    User,
)


def test_user_minimal_fields() -> None:
    user = User.model_validate(
        {
            "id": "1",
            "username": "coder",
            "name": "Coder Name",
        }
    )
    assert user.id == "1"
    assert user.username == "coder"
    assert user.name == "Coder Name"
    assert user.email is None
    assert user.last_login_time is None
    assert user.team is None
    assert user.roles == []
    assert user.enabled is True


def test_create_user_from_user() -> None:
    user = User.model_validate(
        {
            "id": "42",
            "username": "user42",
            "name": "User 42",
            "email": "user42@example.com",
        }
    )
    create_user = CreateUser.from_user(user, password="secret_password")
    assert create_user.username == "user42"
    assert create_user.name == "User 42"
    assert create_user.email == "user42@example.com"
    assert create_user.password == "secret_password"
    assert create_user.is_exist is True


def test_user_update() -> None:
    user = User.model_validate(
        {
            "id": "1",
            "username": "u1",
            "name": "Old Name",
        }
    )
    user.update(name="New Name", id="ignored_id", username="ignored_user")
    assert user.name == "New Name"
    assert user.id == "1"
    assert user.username == "u1"


def test_domserver_client_api_params() -> None:
    client = DomServerClient(
        host="https://domjudge.example.com/api",  # type: ignore[arg-type]
        username="judge_admin",
        password="judge_password",
        disable_ssl=True,
        timeout=30.0,
        max_connections=10,
        max_keepalive_connections=5,
    )
    params = client.api_params
    assert isinstance(params["host"], str)
    assert params["host"] == "https://domjudge.example.com/api"
    assert params["username"] == "judge_admin"
    assert params["password"] == "judge_password"
    assert params["disable_ssl"] is True
    assert params["timeout"] is not None
    assert params["limits"] is not None


def test_affiliation_optional_fields() -> None:
    affil = Affiliation.model_validate(
        {
            "shortname": "NTUB",
            "name": "National Taipei University of Business",
            "country": "TWN",
        }
    )
    assert affil.id is None
    assert affil.team_affiliation is None
    assert affil.shortname == "NTUB"


def test_submission_and_judgement_optional_fields() -> None:
    sub = Submission.model_validate(
        {
            "id": "100",
            "team_id": "2",
            "problem_id": "A",
        }
    )
    assert sub.id == "100"
    assert sub.language_id is None
    assert sub.files is None

    sub_file = SubmissionFile.model_validate({"id": "f1"})
    assert sub_file.id == "f1"
    assert sub_file.filename is None

    judgement = Judgement.model_validate(
        {
            "id": "j1",
            "submission_id": "100",
            "valid": True,
        }
    )
    assert judgement.id == "j1"
    assert judgement.judgement_type_id is None
    assert judgement.judgehost is None
    assert judgement.max_run_time is None


def test_team_and_problem_models() -> None:
    team = Team.model_validate(
        {
            "id": "t1",
            "name": "Team 1",
            "group_ids": ["g1"],
        }
    )
    assert team.id == "t1"
    assert team.affiliation is None
    assert team.nationality is None

    problem = Problem.model_validate(
        {
            "id": "p1",
            "ordinal": 1,
            "short_name": "A",
            "label": "A",
            "time_limit": 1,
            "externalid": "ext1",
            "name": "Problem A",
            "test_data_count": 5,
        }
    )
    assert problem.rgb is None
    assert problem.color is None

    item = ProblemItem.model_validate(
        {
            "id": "p1",
            "time_limit": 1,
            "test_data_count": 5,
            "name": "Problem A",
        }
    )
    assert item.export_file_path is None
