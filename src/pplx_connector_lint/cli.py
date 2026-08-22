"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import report, schema
from ._version import __version__
from .config import load
from .errors import LintError
from .rules import check


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="connector-lint",
        description=(
            "Lint a Computer skill's connector usage against the live connector schema."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("check", help="lint a skill directory")
    run.add_argument(
        "path",
        nargs="?",
        default=".",
        type=Path,
        help="skill directory to lint (default: current directory)",
    )
    run.add_argument(
        "--report",
        action="store_true",
        help=(
            "upload the result to the schema registry so it can be compared against other "
            "workspaces on the same image"
        ),
    )
    run.add_argument("--registry", metavar="URL", help="override the registry base URL")
    run.add_argument("--json", action="store_true", help="emit findings as JSON")

    env = sub.add_parser("env", help="show the resolved runtime")
    env.add_argument("--json", action="store_true", help="emit as JSON")

    return parser


def _cmd_check(args: argparse.Namespace) -> int:
    runtime = load(registry_url=args.registry)
    result = check(args.path, schema.fetch(runtime))

    if args.json:
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "call_sites": result.call_sites,
                    "findings": [
                        {
                            "rule": f.rule,
                            "severity": f.severity,
                            "path": str(f.path),
                            "line": f.line,
                            "message": f.message,
                        }
                        for f in result.findings
                    ],
                },
                indent=2,
            )
        )
    else:
        for finding in result.findings:
            print(finding.format(args.path))
        print(result.summary())

    if args.report:
        receipt = report.upload(result, runtime)
        print(report.describe(receipt, runtime))

    return 0 if result.ok else 1


def _cmd_env(args: argparse.Namespace) -> int:
    runtime = load()
    fields = {
        "sandbox": runtime.is_sandbox,
        "image_tag": runtime.image_tag,
        "kernel": runtime.kernel,
        "connector_base_url": runtime.connector_base_url,
        "tool_target_base_url": runtime.tool_target_base_url,
        "registry_url": runtime.registry_url,
    }
    if args.json:
        print(json.dumps(fields, indent=2))
    else:
        width = max(len(k) for k in fields)
        for key, value in fields.items():
            print(f"{key:<{width}}  {value if value is not None else '-'}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    args = _parser().parse_args(argv)
    handler = {"check": _cmd_check, "env": _cmd_env}[args.command]
    try:
        return handler(args)
    except LintError as exc:
        print(f"connector-lint: {exc}", file=sys.stderr)
        return exc.exit_code
