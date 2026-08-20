"""Resolve the live connector schema through the agent proxy.

The connector schema is not versioned in any way a sandbox can read, so the only reliable
baseline is whatever the connector service is serving right now. This module fetches it and
normalises it into the shape the rules in :mod:`pplx_connector_lint.rules` expect.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .config import Runtime
from .errors import SchemaUnavailable

_TIMEOUT = 20


@dataclass(frozen=True, slots=True)
class Tool:
    """One callable tool on a connector."""

    name: str
    required: frozenset[str] = field(default_factory=frozenset)
    optional: frozenset[str] = field(default_factory=frozenset)

    @property
    def parameters(self) -> frozenset[str]:
        """Every parameter the tool accepts."""
        return self.required | self.optional


@dataclass(frozen=True, slots=True)
class Connector:
    """One connector and the tools it exposes."""

    slug: str
    status: str
    tools: dict[str, Tool] = field(default_factory=dict)

    @property
    def connected(self) -> bool:
        return self.status.upper() == "CONNECTED"


@dataclass(frozen=True, slots=True)
class Schema:
    """A snapshot of the connector surface available to one workspace."""

    connectors: dict[str, Connector] = field(default_factory=dict)

    def tool(self, connector: str, tool: str) -> Tool | None:
        """Look up a tool, or ``None`` if either the connector or the tool is absent."""
        found = self.connectors.get(connector)
        return found.tools.get(tool) if found else None

    @property
    def connected_slugs(self) -> tuple[str, ...]:
        return tuple(sorted(c.slug for c in self.connectors.values() if c.connected))


def _request(runtime: Runtime, path: str) -> Any:
    """Issue an authenticated GET against the agent proxy.

    The workspace bearer authenticates the call. Current images additionally require the
    forwarding target to be named in ``X-Base-Url``; see
    :attr:`~pplx_connector_lint.config.Runtime.tool_target_base_url`.
    """
    url = f"{runtime.proxy_url.rstrip('/')}{path}"
    request = urllib.request.Request(url, method="GET")
    request.add_header("authorization", f"Bearer {runtime.token}")
    request.add_header("accept", "application/json")
    if runtime.tool_target_base_url:
        request.add_header("X-Base-Url", runtime.tool_target_base_url)

    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover - network path
        raise SchemaUnavailable(
            f"connector service returned {exc.code} for {path}"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover - network path
        raise SchemaUnavailable(f"connector service unreachable: {exc}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - network path
        raise SchemaUnavailable("connector service returned a non-JSON body") from exc


def parse(payload: Any) -> Schema:
    """Normalise a connector-service payload into a :class:`Schema`.

    Tolerant by design: the service has changed this shape twice without a version bump, so
    unknown keys are ignored rather than raising.
    """
    raw = payload.get("connectors", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw, list):
        raise SchemaUnavailable("connector listing was not a list")

    connectors: dict[str, Connector] = {}
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("slug") or entry.get("name")
        if not slug:
            continue

        tools: dict[str, Tool] = {}
        for tool in entry.get("tools", []) or []:
            if not isinstance(tool, dict):
                continue
            tool_name = tool.get("name")
            if not tool_name:
                continue
            params = tool.get("parameters", {}) or {}
            required = {k for k, v in params.items() if isinstance(v, dict) and v.get("required")}
            tools[tool_name] = Tool(
                name=tool_name,
                required=frozenset(required),
                optional=frozenset(set(params) - required),
            )

        connectors[slug] = Connector(
            slug=slug,
            status=str(entry.get("status", "UNKNOWN")),
            tools=tools,
        )

    return Schema(connectors=connectors)


def fetch(runtime: Runtime) -> Schema:
    """Fetch and parse the live connector schema for this workspace."""
    return parse(_request(runtime, "/rest/connector-service/connectors"))
