from __future__ import annotations

from pplx_connector_lint.rules import check, collect


def write(tmp_path, body):
    path = tmp_path / "skill.py"
    path.write_text(body, encoding="utf-8")
    return path


def test_clean_skill_has_no_findings(tmp_path, schema):
    write(tmp_path, 'connectors.call("gcal", "search_email", query="hi", limit=5)\n')
    result = check(tmp_path, schema)
    assert result.ok
    assert result.call_sites == 1
    assert result.summary() == "1 call sites checked, no findings"


def test_unknown_connector_is_an_error(tmp_path, schema):
    write(tmp_path, 'connectors.call("slack", "post")\n')
    findings = check(tmp_path, schema).findings
    assert [f.rule for f in findings] == ["C001"]
    assert findings[0].severity == "error"


def test_disconnected_connector_is_a_warning(tmp_path, schema):
    write(tmp_path, 'connectors.call("notion", "search", query="x")\n')
    result = check(tmp_path, schema)
    assert [f.rule for f in result.findings] == ["C002"]
    assert result.ok


def test_unknown_tool_is_an_error(tmp_path, schema):
    write(tmp_path, 'connectors.call("gcal", "send_fax", to="x")\n')
    assert [f.rule for f in check(tmp_path, schema).findings] == ["C003"]


def test_missing_required_parameter_is_an_error(tmp_path, schema):
    write(tmp_path, 'connectors.call("gcal", "search_email", limit=5)\n')
    assert [f.rule for f in check(tmp_path, schema).findings] == ["C004"]


def test_unknown_parameter_is_a_warning(tmp_path, schema):
    write(tmp_path, 'connectors.call("gcal", "search_email", query="x", folder="y")\n')
    result = check(tmp_path, schema)
    assert [f.rule for f in result.findings] == ["C005"]
    assert result.ok


def test_findings_carry_the_call_site_line(tmp_path, schema):
    write(tmp_path, '\n\nconnectors.call("slack", "post")\n')
    assert check(tmp_path, schema).findings[0].line == 3


def test_vendored_directories_are_skipped(tmp_path, schema):
    vendored = tmp_path / ".venv" / "lib"
    vendored.mkdir(parents=True)
    (vendored / "dep.py").write_text('connectors.call("slack", "post")\n', encoding="utf-8")
    assert collect(tmp_path) == []


def test_unparseable_source_still_yields_the_call_site(tmp_path, schema):
    write(tmp_path, 'connectors.call("gcal", "search_email", query=)\n')
    assert check(tmp_path, schema).call_sites == 1
