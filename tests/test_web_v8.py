import urllib.parse
from pathlib import Path

import httpx
import pytest

from domjudge_tool_cli.exceptions import FormSubmitError
from domjudge_tool_cli.models import CreateUser, User
from domjudge_tool_cli.services.web import v8

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "web" / "v8"


def read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def parse_post_data(request: httpx.Request) -> dict[str, list[str]]:
    content = request.content.decode("utf-8")
    return urllib.parse.parse_qs(content, keep_blank_values=True)


def create_mock_client(handler) -> v8.DomServerWeb:
    web = v8.DomServerWeb("https://example.test", "admin", "secret")
    web.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.test",
    )
    return web


# ---------------------------------------------------------------------------
# 1. Login
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_login_success() -> None:
    login_html = read_fixture("login.html")
    landing_html = read_fixture("post_login_landing.html")
    captured_posts: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/login" and request.method == "GET":
            return httpx.Response(200, text=login_html)
        if request.url.path == "/login" and request.method == "POST":
            captured_posts.append(parse_post_data(request))
            return httpx.Response(302, headers={"Location": "/jury"})
        if request.url.path == "/jury" and request.method == "GET":
            return httpx.Response(200, text=landing_html)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        await web.login()

    assert len(captured_posts) == 1
    post = captured_posts[0]
    assert post["_csrf_token"] == ["TEST_CSRF_TOKEN"]
    assert post["_username"] == ["admin"]
    assert post["_password"] == ["secret"]


@pytest.mark.anyio
async def test_login_stayed_on_login_fails() -> None:
    login_html = read_fixture("login.html")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/login":
            return httpx.Response(200, text=login_html)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        with pytest.raises(FormSubmitError, match="Login fail."):
            await web.login()


@pytest.mark.anyio
async def test_login_401_raises_http_status_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    web = create_mock_client(handler)
    async with web:
        with pytest.raises(httpx.HTTPStatusError):
            await web.login()


# ---------------------------------------------------------------------------
# 2. Create Team and User
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_team_and_user_success() -> None:
    add_form = read_fixture("team_add_form.html")
    team_view = read_fixture("team_view.html")
    captured_posts: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/teams/add" and request.method == "GET":
            return httpx.Response(200, text=add_form)
        if request.url.path == "/jury/teams/add" and request.method == "POST":
            captured_posts.append(parse_post_data(request))
            return httpx.Response(302, headers={"Location": "/jury/teams/99"})
        if request.url.path == "/jury/teams/99" and request.method == "GET":
            return httpx.Response(200, text=team_view)
        return httpx.Response(404)

    web = create_mock_client(handler)
    user = CreateUser(username="team-alpha", name="Team Alpha")
    async with web:
        team_id, user_id = await web.create_team_and_user(
            user=user,
            category_id=3,
            affiliation_id=8,
            enabled=True,
        )

    assert team_id == "99"
    assert user_id == "7"
    assert len(captured_posts) == 1
    post = captured_posts[0]
    assert post["team[name]"] == ["team-alpha"]
    assert post["team[displayName]"] == ["Team Alpha"]
    assert post["team[category]"] == ["3"]
    assert post["team[affiliation]"] == ["8"]
    assert post["team[penalty]"] == ["0"]
    assert post["team[enabled]"] == ["1"]
    assert post["team[addUserForTeam]"] == ["create-new-user"]
    assert post["team[newUsername]"] == ["team-alpha"]
    assert "team[users][0][username]" not in post


@pytest.mark.anyio
async def test_create_team_and_user_stayed_on_form_fails() -> None:
    add_form = read_fixture("team_add_form.html")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/teams/add":
            return httpx.Response(200, text=add_form)
        return httpx.Response(404)

    web = create_mock_client(handler)
    user = CreateUser(username="team-alpha", name="Team Alpha")
    async with web:
        with pytest.raises(FormSubmitError, match="Team create fail. team-alpha"):
            await web.create_team_and_user(user, 3, 8)


@pytest.mark.anyio
async def test_create_team_and_user_missing_user_link() -> None:
    add_form = read_fixture("team_add_form.html")
    broken_view = "<html><body><table><tr><th>No User</th></tr></table></body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/teams/add" and request.method == "GET":
            return httpx.Response(200, text=add_form)
        if request.url.path == "/jury/teams/add" and request.method == "POST":
            return httpx.Response(302, headers={"Location": "/jury/teams/99"})
        if request.url.path == "/jury/teams/99":
            return httpx.Response(200, text=broken_view)
        return httpx.Response(404)

    web = create_mock_client(handler)
    user = CreateUser(username="team-alpha", name="Team Alpha")
    async with web:
        with pytest.raises(ValueError, match="failed to find user link on team page"):
            await web.create_team_and_user(user, 3, 8)


# ---------------------------------------------------------------------------
# 3. Update Team
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_update_team_success() -> None:
    edit_form = read_fixture("team_edit_form.html")
    team_view = read_fixture("team_view.html")
    captured_posts: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/teams/99/edit" and request.method == "GET":
            return httpx.Response(200, text=edit_form)
        if request.url.path == "/jury/teams/99/edit" and request.method == "POST":
            captured_posts.append(parse_post_data(request))
            return httpx.Response(302, headers={"Location": "/jury/teams/99"})
        if request.url.path == "/jury/teams/99" and request.method == "GET":
            return httpx.Response(200, text=team_view)
        return httpx.Response(404)

    web = create_mock_client(handler)
    user = User(
        id="7",
        username="team-alpha",
        name="Team Alpha",
        team_id="99",
    )
    async with web:
        team_id, user_id = await web.update_team(
            user=user,
            category_id=4,
            affiliation_id=8,
            enabled=False,
        )

    assert team_id == "99"
    assert user_id == "7"
    assert len(captured_posts) == 1
    post = captured_posts[0]
    assert post["team[name]"] == ["team-alpha"]
    assert post["team[displayName]"] == ["Team Alpha"]
    assert post["team[category]"] == ["4"]
    assert post["team[affiliation]"] == ["8"]
    assert post["team[penalty]"] == ["20"]  # Preserved from edit snapshot
    assert post["team[enabled]"] == ["0"]
    assert "team[addUserForTeam]" not in post
    assert "team[newUsername]" not in post


@pytest.mark.anyio
async def test_update_team_missing_team_id_raises() -> None:
    user = User(id="7", username="team-alpha", name="Team Alpha", team_id=None)
    web = create_mock_client(lambda r: httpx.Response(200))
    async with web:
        with pytest.raises(ValueError, match="User must have team_id"):
            await web.update_team(user, 4, 8)


@pytest.mark.anyio
async def test_update_team_stayed_on_form_fails() -> None:
    edit_form = read_fixture("team_edit_form.html")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/teams/99/edit":
            return httpx.Response(200, text=edit_form)
        return httpx.Response(404)

    web = create_mock_client(handler)
    user = User(id="7", username="team-alpha", name="Team Alpha", team_id="99")
    async with web:
        with pytest.raises(FormSubmitError, match="Team update fail. team-alpha"):
            await web.update_team(user, 4, 8)


# ---------------------------------------------------------------------------
# 4. Set User Password & Roles
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_set_user_password_empty_roles_preserves_fixture_role() -> None:
    edit_form = read_fixture("user_edit_form.html")
    captured_posts: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/users/7/edit" and request.method == "GET":
            return httpx.Response(200, text=edit_form)
        if request.url.path == "/jury/users/7/edit" and request.method == "POST":
            captured_posts.append(parse_post_data(request))
            return httpx.Response(302, headers={"Location": "/jury/users/7"})
        if request.url.path == "/jury/users/7":
            return httpx.Response(200)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        await web.set_user_password(
            user_id="7",
            password="new-password",
            user_roles=[],
            enabled=True,
        )

    assert len(captured_posts) == 1
    post = captured_posts[0]
    assert post["user[plainPassword]"] == ["new-password"]
    assert post["user[enabled]"] == ["1"]
    # Empty user_roles must preserve the fixture's pre-selected role "3"
    assert post["user[user_roles][]"] == ["3"]


@pytest.mark.anyio
async def test_set_user_password_overrides_roles_when_specified() -> None:
    edit_form = read_fixture("user_edit_form.html")
    captured_posts: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/users/7/edit" and request.method == "GET":
            return httpx.Response(200, text=edit_form)
        if request.url.path == "/jury/users/7/edit" and request.method == "POST":
            captured_posts.append(parse_post_data(request))
            return httpx.Response(302, headers={"Location": "/jury/users/7"})
        if request.url.path == "/jury/users/7":
            return httpx.Response(200)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        await web.set_user_password(
            user_id="7",
            password="new-password",
            user_roles=[3, 5],
            enabled=False,
        )

    assert len(captured_posts) == 1
    post = captured_posts[0]
    assert post["user[plainPassword]"] == ["new-password"]
    assert post["user[enabled]"] == ["0"]
    assert post["user[user_roles][]"] == ["3", "5"]


@pytest.mark.anyio
async def test_set_user_password_stayed_on_form_fails() -> None:
    edit_form = read_fixture("user_edit_form.html")
    rejected_page = (
        edit_form
        + "<div class='alert alert-danger'>Password should be 10+ chars.</div>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/users/7/edit":
            return httpx.Response(200, text=rejected_page)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        with pytest.raises(FormSubmitError, match="User set password fail. 7") as exc:
            await web.set_user_password("7", "new-password", [3])

    # The reason DOMjudge rendered must reach the caller, not just a bare failure.
    assert "Password should be 10+ chars." in str(exc.value)
    assert exc.value.details == ["Password should be 10+ chars."]
    assert exc.value.path == "/jury/users/7/edit"


# ---------------------------------------------------------------------------
# 5. Affiliations
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_affiliation_success() -> None:
    add_form = read_fixture("affiliation_add_form.html")
    captured_posts: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/affiliations/add" and request.method == "GET":
            return httpx.Response(200, text=add_form)
        if request.url.path == "/jury/affiliations/add" and request.method == "POST":
            captured_posts.append(parse_post_data(request))
            return httpx.Response(302, headers={"Location": "/jury/affiliations/8"})
        if request.url.path == "/jury/affiliations/8":
            return httpx.Response(200)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        aff = await web.create_affiliation(
            shortname="course001",
            name="Example University",
            country="TWN",
        )

    assert aff.id == "8"
    assert aff.shortname == "course001"
    assert aff.name == "Example University"
    assert aff.country == "TWN"

    assert len(captured_posts) == 1
    post = captured_posts[0]
    assert post["team_affiliation[shortname]"] == ["course001"]
    assert post["team_affiliation[name]"] == ["Example University"]
    assert post["team_affiliation[country]"] == ["TWN"]
    assert "team_affiliation[internalcomments]" in post
    assert "team_affiliation[comments]" not in post


@pytest.mark.anyio
async def test_create_affiliation_stayed_on_form_fails() -> None:
    add_form = read_fixture("affiliation_add_form.html")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/affiliations/add":
            return httpx.Response(200, text=add_form)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        with pytest.raises(FormSubmitError, match="Affiliation create fail."):
            await web.create_affiliation("short", "name")


@pytest.mark.anyio
async def test_get_affiliations_and_get_affiliation() -> None:
    list_html = read_fixture("affiliations_list.html")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/affiliations":
            return httpx.Response(200, text=list_html)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        affs = await web.get_affiliations()
        assert len(affs) == 1
        assert affs[0].id == "8"
        assert affs[0].shortname == "course001"
        assert affs[0].name == "Example University"
        assert affs[0].country == "TWN"

        found_by_name = await web.get_affiliation("Example University")
        assert found_by_name is not None
        assert found_by_name.shortname == "course001"

        found_by_short = await web.get_affiliation("course001")
        assert found_by_short is not None
        assert found_by_short.name == "Example University"

        not_found = await web.get_affiliation("non-existent")
        assert not_found is None


@pytest.mark.anyio
async def test_get_affiliations_malformed_row_raises() -> None:
    html = "<table><tbody><tr><td><a>only one</a></td></tr></tbody></table>"
    web = create_mock_client(lambda r: httpx.Response(200, text=html))
    async with web:
        with pytest.raises(ValueError, match="unexpected table row structure"):
            await web.get_affiliations()


# ---------------------------------------------------------------------------
# 6. Delete Users and Teams (GET confirmation then POST snapshot)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_users_confirms_then_posts() -> None:
    users_html = read_fixture("users.html")
    confirm_html = read_fixture("user_delete_confirm.html")
    confirm_gets: list[str] = []
    delete_posts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/users" and request.method == "GET":
            return httpx.Response(200, text=users_html)
        if request.url.path == "/jury/users/11/delete" and request.method == "GET":
            confirm_gets.append(request.url.path)
            return httpx.Response(200, text=confirm_html)
        if request.url.path == "/jury/users/11/delete" and request.method == "POST":
            delete_posts.append(request.url.path)
            return httpx.Response(302, headers={"Location": "/jury/users"})
        if "/jury/users/22/delete" in request.url.path:
            pytest.fail("Excluded user delete path must not be called")
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        deleted = await web.delete_users(
            include=["anne26a", "cindy950093"],
            exclude=["cindy950093"],
        )

    assert deleted == 1
    assert confirm_gets == ["/jury/users/11/delete"]
    assert delete_posts == ["/jury/users/11/delete"]


@pytest.mark.anyio
async def test_delete_teams_confirms_then_posts_second_to_last_anchor() -> None:
    teams_html = read_fixture("teams.html")
    confirm_html = read_fixture("team_delete_confirm.html")
    confirm_gets: list[str] = []
    delete_posts: list[str] = []
    clarification_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal clarification_called
        if request.url.path == "/jury/teams" and request.method == "GET":
            return httpx.Response(200, text=teams_html)
        if request.url.path == "/jury/teams/10/delete" and request.method == "GET":
            confirm_gets.append(request.url.path)
            return httpx.Response(200, text=confirm_html)
        if request.url.path == "/jury/teams/10/delete" and request.method == "POST":
            delete_posts.append(request.url.path)
            return httpx.Response(302, headers={"Location": "/jury/teams"})
        if "clarifications" in request.url.path:
            clarification_called = True
            return httpx.Response(200)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        deleted = await web.delete_teams(include=["10"], exclude=None)

    assert deleted == 1
    assert confirm_gets == ["/jury/teams/10/delete"]
    assert delete_posts == ["/jury/teams/10/delete"]
    assert not clarification_called


@pytest.mark.anyio
async def test_delete_users_and_teams_inverted_filter_quirk() -> None:
    users_html = read_fixture("users.html")
    teams_html = read_fixture("teams.html")
    delete_hit = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal delete_hit
        if "delete" in request.url.path:
            delete_hit = True
        if request.url.path == "/jury/users":
            return httpx.Response(200, text=users_html)
        if request.url.path == "/jury/teams":
            return httpx.Response(200, text=teams_html)
        return httpx.Response(200)

    web = create_mock_client(handler)
    async with web:
        # Nil or empty include must delete zero rows (Python inverted filter quirk)
        assert await web.delete_users(include=None) == 0
        assert await web.delete_users(include=[]) == 0
        assert await web.delete_teams(include=None) == 0
        assert await web.delete_teams(include=[]) == 0

    assert not delete_hit


@pytest.mark.anyio
async def test_delete_reports_zero_when_identifier_matches_no_row() -> None:
    """A padded or wrong identifier matches nothing.

    The count is what lets a caller detect a no-op cleanup instead of assuming
    the row is gone because no exception was raised.
    """
    users_html = read_fixture("users.html")
    teams_html = read_fixture("teams.html")
    delete_hit = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal delete_hit
        if "delete" in request.url.path:
            delete_hit = True
        if request.url.path == "/jury/users":
            return httpx.Response(200, text=users_html)
        if request.url.path == "/jury/teams":
            return httpx.Response(200, text=teams_html)
        return httpx.Response(200)

    web = create_mock_client(handler)
    async with web:
        assert await web.delete_users(include=["  anne26a  "]) == 0
        assert await web.delete_teams(include=[" 10 "]) == 0

    assert not delete_hit


# ---------------------------------------------------------------------------
# 7. Get Problems
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_problems_parses_columns_and_export_link() -> None:
    problems_html = read_fixture("problems.html")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jury/problems":
            return httpx.Response(200, text=problems_html)
        return httpx.Response(404)

    web = create_mock_client(handler)
    async with web:
        problems = await web.get_problems()
        assert len(problems) == 3

        p1 = problems[0]
        assert p1.id == "1"
        assert p1.name == "Hello World"
        assert p1.time_limit == 5
        assert p1.test_data_count == 1
        assert p1.export_file_path == "/jury/problems/1/export"

        p2 = problems[1]
        assert p2.id == "2"
        assert p2.name == "Float special compare test"
        assert p2.time_limit == 5
        assert p2.test_data_count == 4
        assert p2.export_file_path == "/jury/problems/2/export"

        # Test filtering: only
        only_p1 = await web.get_problems(only=["1"])
        assert len(only_p1) == 1
        assert only_p1[0].id == "1"

        # Test filtering: exclude
        exclude_p2 = await web.get_problems(exclude=["2"])
        assert len(exclude_p2) == 2
        assert [p.id for p in exclude_p2] == ["1", "3"]


@pytest.mark.anyio
async def test_get_problems_malformed_rows_raise() -> None:
    bad_html = "<table><tbody><tr><td><a>1</a></td></tr></tbody></table>"
    web = create_mock_client(lambda r: httpx.Response(200, text=bad_html))
    async with web:
        with pytest.raises(ValueError, match="unexpected table row structure"):
            await web.get_problems()

    missing_id_html = (
        "<table><tbody><tr>"
        + "".join(f"<td>{i}</td>" for i in range(12))
        + "</tr></tbody></table>"
    )
    web2 = create_mock_client(lambda r: httpx.Response(200, text=missing_id_html))
    async with web2:
        with pytest.raises(ValueError, match="problem row id missing"):
            await web2.get_problems()
