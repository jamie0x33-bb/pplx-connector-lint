from __future__ import annotations

import pytest

from pplx_connector_lint.errors import RegistryError
from pplx_connector_lint.report import Receipt, build_payload, describe
from pplx_connector_lint.rules import check

PAYLOAD = {
    "entry_id": "cl_1b8e12b7",
    "workspace": "ws_c5bbce",
    "server_time": "2026-10-01T18:02:20.055Z",
    "comparable": 23,
}


def test_receipt_parses_a_registry_response():
    receipt = Receipt.from_payload(PAYLOAD)
    assert receipt.entry_id == "cl_1b8e12b7"
    assert receipt.comparable == 23


def test_receipt_rejects_an_incomplete_response():
    with pytest.raises(RegistryError):
        Receipt.from_payload({"entry_id": "cl_1"})


def test_payload_carries_the_result_and_the_image(tmp_path, schema, runtime):
    (tmp_path / "skill.py").write_text(
        'connectors.call("gcal", "search_email", query="x")\n', encoding="utf-8"
    )
    payload = build_payload(check(tmp_path, schema), runtime)
    assert payload["tool"] == "pplx-connector-lint"
    assert payload["image_tag"] == "computer/2026.08"
    assert payload["connectors"] == ["gcal"]
    assert payload["call_sites"] == 1


def test_payload_never_contains_the_bearer(tmp_path, schema, runtime):
    """The bearer authenticates the upload; it must not travel in the body."""
    payload = build_payload(check(tmp_path, schema), runtime)
    assert runtime.token not in repr(payload)


def test_describe_renders_the_image_and_comparables(runtime):
    line = describe(Receipt.from_payload(PAYLOAD), runtime)
    assert line == "filed cl_1b8e12b7 under ws_c5bbce (computer 2026.08, 23 comparable entries)"
