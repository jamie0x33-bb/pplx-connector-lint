from __future__ import annotations

import pytest

from pplx_connector_lint.config import DEFAULT_REGISTRY_URL, load
from pplx_connector_lint.errors import ConfigurationError

BASE = {
    "PPLX_AGENT_PROXY_TOKEN": "agp_test-token",
    "PPLX_AGENT_PROXY_URL": "https://proxy.example/agent_pass_through",
    "PPLX_CONNECTOR_BASE_URL": "http://connectors.example:5556",
}


@pytest.fixture
def env(monkeypatch):
    for key in (
        "PPLX_LINT_REGISTRY_URL",
        "SANDBOX_IMAGE_TAG",
        "PPLX_CONNECTOR_TOOL_TARGET_BASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in BASE.items():
        monkeypatch.setenv(key, value)
    return monkeypatch


def test_loads_from_the_environment(env):
    runtime = load()
    assert runtime.token == "agp_test-token"
    assert runtime.is_sandbox
    assert runtime.registry_url == DEFAULT_REGISTRY_URL


def test_missing_token_is_a_configuration_error(env):
    env.delenv("PPLX_AGENT_PROXY_TOKEN")
    with pytest.raises(ConfigurationError, match="PPLX_AGENT_PROXY_TOKEN"):
        load()


def test_missing_connector_base_url_is_a_configuration_error(env):
    env.delenv("PPLX_CONNECTOR_BASE_URL")
    with pytest.raises(ConfigurationError, match="PPLX_CONNECTOR_BASE_URL"):
        load()


def test_registry_argument_wins_over_the_environment(env):
    env.setenv("PPLX_LINT_REGISTRY_URL", "https://from-env.example")
    assert load(registry_url="https://explicit.example").registry_url == "https://explicit.example"


def test_registry_url_loses_its_trailing_slash(env):
    env.setenv("PPLX_LINT_REGISTRY_URL", "https://registry.example/")
    assert load().registry_url == "https://registry.example"


def test_absent_optional_variables_resolve_to_none(env):
    runtime = load()
    assert runtime.image_tag is None
    assert runtime.tool_target_base_url is None


def test_image_tag_is_read_when_present(env):
    env.setenv("SANDBOX_IMAGE_TAG", "computer/2026.08")
    assert load().image_tag == "computer/2026.08"
