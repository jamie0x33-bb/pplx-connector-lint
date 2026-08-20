from __future__ import annotations

import pytest

from pplx_connector_lint.errors import SchemaUnavailable
from pplx_connector_lint.schema import parse


def test_parses_connectors_and_tools(schema):
    assert set(schema.connectors) == {"gcal", "notion"}
    assert schema.connectors["gcal"].connected
    assert not schema.connectors["notion"].connected


def test_required_and_optional_parameters_are_split(schema):
    tool = schema.tool("gcal", "search_email")
    assert tool.required == {"query"}
    assert tool.optional == {"limit"}
    assert tool.parameters == {"query", "limit"}


def test_connected_slugs_are_sorted(schema):
    assert schema.connected_slugs == ("gcal",)


def test_missing_tool_returns_none(schema):
    assert schema.tool("gcal", "nope") is None
    assert schema.tool("nope", "search_email") is None


def test_unknown_keys_are_ignored():
    parsed = parse({"connectors": [{"slug": "x", "status": "CONNECTED", "future": 1}]})
    assert parsed.connectors["x"].tools == {}


def test_entries_without_a_slug_are_skipped():
    assert parse({"connectors": [{"status": "CONNECTED"}]}).connectors == {}


def test_non_list_payload_is_rejected():
    with pytest.raises(SchemaUnavailable):
        parse({"connectors": {"gcal": {}}})
