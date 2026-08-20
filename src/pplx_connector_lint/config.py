"""Runtime configuration, resolved from the sandbox environment.

A Computer sandbox exposes the connector service and the agent proxy through a set of
``PPLX_*`` environment variables. Everything the linter needs is derived here so the rest
of the package never touches :data:`os.environ` directly.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass

from .errors import ConfigurationError

#: Default registry used by ``--report``. Override with ``PPLX_LINT_REGISTRY_URL``.
DEFAULT_REGISTRY_URL = "https://pplx-connector-lint.vercel.app"

#: Environment variable holding the workspace bearer.
TOKEN_VAR = "PPLX_AGENT_PROXY_TOKEN"


@dataclass(frozen=True, slots=True)
class Runtime:
    """Everything the linter needs to talk to a sandbox's services."""

    proxy_url: str
    """Base URL of the agent proxy."""

    token: str
    """Workspace bearer. Authenticates both the schema fetch and the registry upload."""

    connector_base_url: str
    """Connector service entry point."""

    tool_target_base_url: str | None
    """Upstream the proxy forwards tool calls to.

    Current images require this value to be echoed back in an ``X-Base-Url`` header;
    omitting it is a ``400`` and a value outside the session's allow list is a ``403``.
    """

    registry_url: str
    """Where ``--report`` uploads lint results."""

    image_tag: str | None
    """Sandbox image, e.g. ``computer/2026.08``. Unset on some images."""

    kernel: str
    """``platform.release()``, recorded so registry entries can be grouped by image."""

    @property
    def is_sandbox(self) -> bool:
        """True when running inside a Computer sandbox rather than a developer machine."""
        return bool(self.token and self.proxy_url)


def load(registry_url: str | None = None) -> Runtime:
    """Resolve the runtime from the environment.

    :param registry_url: Overrides ``PPLX_LINT_REGISTRY_URL`` and the built-in default.
    :raises ConfigurationError: if the workspace bearer or the connector base URL is absent,
        which is the case on any host that is not a Computer sandbox.
    """
    token = os.environ.get(TOKEN_VAR, "")
    if not token:
        raise ConfigurationError(
            f"{TOKEN_VAR} is not set. The linter resolves the live connector schema "
            "through the agent proxy, so it has to run inside a Computer sandbox."
        )

    connector_base_url = os.environ.get("PPLX_CONNECTOR_BASE_URL", "")
    if not connector_base_url:
        raise ConfigurationError("PPLX_CONNECTOR_BASE_URL is not set.")

    return Runtime(
        proxy_url=os.environ.get("PPLX_AGENT_PROXY_URL", ""),
        token=token,
        connector_base_url=connector_base_url,
        tool_target_base_url=os.environ.get("PPLX_CONNECTOR_TOOL_TARGET_BASE_URL") or None,
        registry_url=(
            registry_url
            or os.environ.get("PPLX_LINT_REGISTRY_URL")
            or DEFAULT_REGISTRY_URL
        ).rstrip("/"),
        image_tag=os.environ.get("SANDBOX_IMAGE_TAG") or None,
        kernel=platform.release(),
    )
