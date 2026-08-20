from __future__ import annotations

import pytest

from pplx_connector_lint.config import Runtime
from pplx_connector_lint.schema import parse

LISTING = {
    "connectors": [
        {
            "slug": "gcal",
            "status": "CONNECTED",
            "tools": [
                {
                    "name": "search_email",
                    "parameters": {
                        "query": {"required": True},
                        "limit": {"required": False},
                    },
                },
                {"name": "list_gmail_labels", "parameters": {}},
            ],
        },
        {
            "slug": "notion",
            "status": "DISCONNECTED",
            "tools": [{"name": "search", "parameters": {"query": {"required": True}}}],
        },
    ]
}


@pytest.fixture
def schema():
    return parse(LISTING)


@pytest.fixture
def runtime():
    return Runtime(
        proxy_url="https://proxy.example/agent_pass_through",
        token="agp_test-token",
        connector_base_url="http://connectors.example:5556",
        tool_target_base_url="http://web-server-connectors:5556",
        registry_url="https://registry.example",
        image_tag="computer/2026.08",
        kernel="6.1.141",
    )
