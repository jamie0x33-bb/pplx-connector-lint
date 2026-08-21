"""Lint rules.

Each rule compares a connector call found in a skill's source against the live schema.
Rules are pure: they take parsed call sites and a :class:`~pplx_connector_lint.schema.Schema`
and return findings. Everything involving I/O lives in :mod:`pplx_connector_lint.schema`.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from .schema import Schema

#: ``connectors.call("gcal", "search_email", ...)`` and the dotted equivalent.
_CALL = re.compile(r"""connectors\.call\(\s*["']([\w-]+)["']\s*,\s*["']([\w-]+)["']""")


@dataclass(frozen=True, slots=True)
class CallSite:
    """One connector call found in a skill's source."""

    path: Path
    line: int
    connector: str
    tool: str
    keywords: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class Finding:
    """A single lint result."""

    rule: str
    severity: str
    path: Path
    line: int
    message: str

    def format(self, root: Path | None = None) -> str:
        relative = root and self.path.is_relative_to(root)
        shown = self.path.relative_to(root) if relative else self.path
        return f"{shown}:{self.line}: {self.severity}: [{self.rule}] {self.message}"


@dataclass(frozen=True, slots=True)
class LintResult:
    """The outcome of a lint run."""

    findings: tuple[Finding, ...]
    call_sites: int
    connectors_seen: tuple[str, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == "error")

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if not self.findings:
            return f"{self.call_sites} call sites checked, no findings"
        return (
            f"{self.call_sites} call sites checked, "
            f"{len(self.errors)} error(s), "
            f"{len(self.findings) - len(self.errors)} warning(s)"
        )


def _keywords(source: str, line: int) -> frozenset[str]:
    """Best-effort extraction of keyword argument names at a call site."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return frozenset()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node, "lineno", None) == line:
            return frozenset(kw.arg for kw in node.keywords if kw.arg)
    return frozenset()


def collect(root: Path) -> list[CallSite]:
    """Find every connector call under ``root``."""
    sites: list[CallSite] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in _CALL.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            sites.append(
                CallSite(
                    path=path,
                    line=line,
                    connector=match.group(1),
                    tool=match.group(2),
                    keywords=_keywords(source, line),
                )
            )
    return sites


def evaluate(sites: list[CallSite], schema: Schema) -> list[Finding]:
    """Apply every rule to every call site."""
    findings: list[Finding] = []

    for site in sites:
        connector = schema.connectors.get(site.connector)

        if connector is None:
            findings.append(
                Finding(
                    rule="C001",
                    severity="error",
                    path=site.path,
                    line=site.line,
                    message=f"unknown connector {site.connector!r}",
                )
            )
            continue

        if not connector.connected:
            findings.append(
                Finding(
                    rule="C002",
                    severity="warning",
                    path=site.path,
                    line=site.line,
                    message=(
                        f"connector {site.connector!r} is {connector.status}; "
                        "this call will fail until it is connected"
                    ),
                )
            )

        tool = connector.tools.get(site.tool)
        if tool is None:
            findings.append(
                Finding(
                    rule="C003",
                    severity="error",
                    path=site.path,
                    line=site.line,
                    message=(
                        f"connector {site.connector!r} exposes no tool {site.tool!r}"
                    ),
                )
            )
            continue

        missing = tool.required - site.keywords
        if missing and site.keywords:
            findings.append(
                Finding(
                    rule="C004",
                    severity="error",
                    path=site.path,
                    line=site.line,
                    message=(
                        f"{site.tool!r} requires {', '.join(sorted(missing))}"
                    ),
                )
            )

        unknown = site.keywords - tool.parameters
        if unknown:
            findings.append(
                Finding(
                    rule="C005",
                    severity="warning",
                    path=site.path,
                    line=site.line,
                    message=(
                        f"{site.tool!r} ignores unknown parameter(s) "
                        f"{', '.join(sorted(unknown))}"
                    ),
                )
            )

    return findings


def check(root: Path, schema: Schema) -> LintResult:
    """Lint every connector call under ``root`` against ``schema``."""
    sites = collect(root)
    return LintResult(
        findings=tuple(evaluate(sites, schema)),
        call_sites=len(sites),
        connectors_seen=tuple(sorted({s.connector for s in sites})),
    )
