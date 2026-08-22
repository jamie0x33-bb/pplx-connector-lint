from __future__ import annotations

import json

import pytest

from pplx_connector_lint import cli


@pytest.fixture
def sandbox(monkeypatch, schema, runtime):
    monkeypatch.setattr(cli, "load", lambda **_: runtime)
    monkeypatch.setattr(cli.schema, "fetch", lambda _: schema)
    return runtime


def test_check_reports_a_clean_skill(tmp_path, sandbox, capsys):
    (tmp_path / "skill.py").write_text(
        'connectors.call("gcal", "search_email", query="x")\n', encoding="utf-8"
    )
    assert cli.main(["check", str(tmp_path)]) == 0
    assert "no findings" in capsys.readouterr().out


def test_check_exits_non_zero_on_an_error(tmp_path, sandbox, capsys):
    (tmp_path / "skill.py").write_text('connectors.call("slack", "post")\n', encoding="utf-8")
    assert cli.main(["check", str(tmp_path)]) == 1
    assert "C001" in capsys.readouterr().out


def test_check_emits_json(tmp_path, sandbox, capsys):
    (tmp_path / "skill.py").write_text('connectors.call("slack", "post")\n', encoding="utf-8")
    cli.main(["check", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["findings"][0]["rule"] == "C001"


def test_env_lists_the_resolved_runtime(sandbox, capsys):
    assert cli.main(["env"]) == 0
    assert "computer/2026.08" in capsys.readouterr().out


def test_configuration_errors_are_reported_without_a_traceback(monkeypatch, capsys):
    from pplx_connector_lint.errors import ConfigurationError

    def boom(**_):
        raise ConfigurationError("PPLX_AGENT_PROXY_TOKEN is not set.")

    monkeypatch.setattr(cli, "load", boom)
    assert cli.main(["env"]) == 2
    assert "PPLX_AGENT_PROXY_TOKEN" in capsys.readouterr().err
