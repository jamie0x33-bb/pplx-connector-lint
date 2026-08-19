"""Lint a Computer skill's connector usage against the live connector schema.

The public surface is deliberately small::

    from pplx_connector_lint import Runtime, check, load

    runtime = load()
    result = check(Path("my-skill"), runtime)
    print(result.summary())
"""

from __future__ import annotations

from ._version import __version__
from .config import Runtime, load
from .errors import (
    ConfigurationError,
    LintError,
    RegistryError,
    SchemaUnavailable,
)
from .rules import Finding, LintResult, check

__all__ = [
    "ConfigurationError",
    "Finding",
    "LintError",
    "LintResult",
    "RegistryError",
    "Runtime",
    "SchemaUnavailable",
    "__version__",
    "check",
    "load",
]
