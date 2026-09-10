import pytest

from domjudge_tool_cli.services.web import DomServerWebGateway, v7, v8
from domjudge_tool_cli.services.web.base import _get_input_fields

# ---------------------------------------------------------------------------
# 1. Gateway routing tests (DOMjudge version family routing)
# ---------------------------------------------------------------------------


def test_gateway_legacy_versions_preserved() -> None:
    assert DomServerWebGateway("7.3.2") is v7.DomServerWeb
    assert DomServerWebGateway("7.3.4") is v7.DomServerWeb
    assert DomServerWebGateway("8.1.3") is v8.DomServerWeb


def test_gateway_v8_family_routing() -> None:
    assert DomServerWebGateway("8.3") is v8.DomServerWeb
    assert DomServerWebGateway("8.3.1") is v8.DomServerWeb
    assert DomServerWebGateway("8.3.2") is v8.DomServerWeb


def test_gateway_v7_family_routing() -> None:
    assert DomServerWebGateway("7.3") is v7.DomServerWeb
    assert DomServerWebGateway("7.3.9") is v7.DomServerWeb


def test_gateway_unsupported_versions_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported DOMjudge version: 8.31"):
        DomServerWebGateway("8.31")

    with pytest.raises(ValueError, match="Unsupported DOMjudge version: 9.0.0"):
        DomServerWebGateway("9.0.0")

    with pytest.raises(ValueError, match="Unsupported DOMjudge version: 8.1"):
        DomServerWebGateway("8.1")

    with pytest.raises(ValueError, match="Unsupported DOMjudge version: 8.2.0"):
        DomServerWebGateway("8.2.0")


# ---------------------------------------------------------------------------
# 2. Focused form parser tests (matching Go parse_test.go)
# ---------------------------------------------------------------------------


def test_parse_form_fields_all_input_types_included() -> None:
    html = """
<form>
  <input type="hidden" name="_csrf_token" value="ABC">
  <input type="text" name="_username" value="alice">
  <input type="password" name="_password" value="">
  <input type="submit" name="login" value="Sign in">
</form>"""
    got = _get_input_fields(html)
    assert got == {
        "_csrf_token": "ABC",
        "_username": "alice",
        "_password": "",
        "login": "Sign in",
    }


def test_parse_form_fields_nameless_inputs_dropped() -> None:
    html = """
<form>
  <input type="hidden" value="orphan">
  <input type="text" name="kept" value="ok">
</form>"""
    got = _get_input_fields(html)
    assert "" not in got
    assert None not in got
    assert got.get("kept") == "ok"
    assert len(got) == 1


def test_parse_form_fields_checked_inputs_only() -> None:
    html = """
<form>
  <input type="checkbox" name="user[user_roles][]" value="1">
  <input type="checkbox" name="user[user_roles][]" value="3" checked="checked">
  <input type="checkbox" name="user[user_roles][]" value="11">
  <input type="checkbox" name="implicit" checked="checked">
  <input type="radio" name="enabled" value="1" checked="checked">
  <input type="radio" name="enabled" value="0">
</form>"""
    got = _get_input_fields(html)
    assert got.get("user[user_roles][]") == "3"
    assert got.get("implicit") == "on"
    assert got.get("enabled") == "1"


def test_parse_form_fields_multiple_checked_checkboxes_same_name() -> None:
    html = """
<form>
  <input type="checkbox" name="roles" value="1" checked>
  <input type="checkbox" name="roles" value="2">
  <input type="checkbox" name="roles" value="3" checked>
</form>"""
    got = _get_input_fields(html)
    assert got.get("roles") == ["1", "3"]


def test_parse_form_fields_selects_take_selected_option() -> None:
    html = """
<form>
  <select name="team[category]">
    <option value="1">First</option>
    <option value="2" selected="selected">Second</option>
    <option value="3">Third</option>
  </select>
</form>"""
    got = _get_input_fields(html)
    assert got.get("team[category]") == "2"


def test_parse_form_fields_selects_with_no_selected_option_are_absent() -> None:
    html = """
<form>
  <select name="team[contests][]">
    <option value="1">A</option>
    <option value="2">B</option>
  </select>
</form>"""
    got = _get_input_fields(html)
    assert "team[contests][]" not in got


def test_parse_form_fields_multi_select_all_selected_values_preserved() -> None:
    html = """
<form>
  <select name="team[contests][]" multiple="multiple">
    <option value="1">A</option>
    <option value="2" selected="selected">B</option>
    <option value="3" selected="selected">C</option>
    <option value="5" selected="selected">E</option>
  </select>
</form>"""
    got = _get_input_fields(html)
    assert got.get("team[contests][]") == ["2", "3", "5"]


def test_parse_form_fields_textarea_included() -> None:
    html = """
<form>
  <textarea name="team[members]">Alice
Bob
Charlie</textarea>
  <textarea name="team[comments]">  trimmed leading/trailing whitespace inside textarea is preserved  </textarea>
  <textarea>orphan-textarea-no-name</textarea>
</form>"""
    got = _get_input_fields(html)
    assert got.get("team[members]") == "Alice\nBob\nCharlie"
    assert (
        got.get("team[comments]")
        == "  trimmed leading/trailing whitespace inside textarea is preserved  "
    )
    assert "" not in got
    assert None not in got


def test_parse_form_fields_empty_html() -> None:
    got = _get_input_fields("")
    assert got == {}
