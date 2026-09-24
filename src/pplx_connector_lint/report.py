"""Upload a lint result to the shared schema registry.

Connector schema drift is invisible from inside one workspace: a tool that disappears for
you may still be present for everyone else, and there is no version string to compare. The
registry exists so a result can be checked against what other workspaces are seeing on the
same image.

Uploads are authenticated with the workspace bearer. Only the derived workspace identifier
is retained by the registry; see :doc:`../docs/registry`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from ._version import __version__
from .config import Runtime
from .errors import RegistryError
from .rules import LintResult

_TIMEOUT = 15


@dataclass(frozen=True, slots=True)
class Receipt:
    """What the registry returns for an accepted upload."""

    entry_id: str
    workspace: str
    server_time: str
    comparable: int
    """How many entries from other workspaces are on the same image."""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Receipt:
        try:
            return cls(
                entry_id=payload["entry_id"],
                workspace=payload["workspace"],
                server_time=payload["server_time"],
                comparable=int(payload.get("comparable", 0)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RegistryError(f"registry returned an unusable response: {payload!r}") from exc


def build_payload(result: LintResult, runtime: Runtime) -> dict[str, Any]:
    """Assemble the registry entry for a lint result.

    The bearer is **not** part of the payload — it travels in the ``Authorization`` header
    and the registry resolves it to a workspace identifier on receipt.
    """
    return {
        "tool": "pplx-connector-lint",
        "tool_version": __version__,
        "kernel": runtime.kernel,
        "image_tag": runtime.image_tag,
        "call_sites": result.call_sites,
        "connectors": list(result.connectors_seen),
        "findings": [
            {"rule": f.rule, "severity": f.severity, "message": f.message}
            for f in result.findings
        ],
    }


def upload(result: LintResult, runtime: Runtime) -> Receipt:
    """Send a lint result to the registry and return its receipt.

    :raises RegistryError: on any non-2xx response or unreachable registry.
    """
    body = json.dumps(build_payload(result, runtime)).encode("utf-8")
    request = urllib.request.Request(
        f"{runtime.registry_url}/api/entries",
        data=body,
        method="POST",
    )
    request.add_header("content-type", "application/json")
    request.add_header("authorization", f"Bearer {runtime.token}")
    request.add_header("user-agent", f"pplx-connector-lint/{__version__}")

    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover - network path
        detail = exc.read().decode("utf-8", "replace")[:200]
        raise RegistryError(f"registry returned {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover - network path
        raise RegistryError(f"registry unreachable: {exc}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - network path
        raise RegistryError("registry returned a non-JSON body") from exc

    return Receipt.from_payload(payload)


def describe(receipt: Receipt, runtime: Runtime) -> str:
    """Render the one-line confirmation shown after a successful upload.

    The image is reported as ``<family> <major>.<minor>`` so entries read the same way they
    are grouped on the registry's history page.
    """
    family, version = runtime.image_tag.split("/", 1)
    major, minor = (int(part) for part in version.split(".", 1))
    return (
        f"filed {receipt.entry_id} under {receipt.workspace} "
        f"({family} {major}.{minor:02d}, {receipt.comparable} comparable entries)"
    )
