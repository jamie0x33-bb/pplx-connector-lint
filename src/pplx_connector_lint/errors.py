"""Exception hierarchy.

Every error the CLI reports deliberately derives from :class:`LintError` so
``__main__`` can render a clean message instead of a traceback.
"""

from __future__ import annotations


class LintError(Exception):
    """Base class for every error raised by this package."""

    exit_code = 1


class ConfigurationError(LintError):
    """The environment does not provide what the linter needs."""

    exit_code = 2


class SchemaUnavailable(LintError):
    """The live connector schema could not be fetched."""

    exit_code = 3


class RegistryError(LintError):
    """The registry rejected an upload."""

    exit_code = 4
