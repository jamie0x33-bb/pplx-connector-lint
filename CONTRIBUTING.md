# Contributing

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
ruff check .
```

CI runs `ruff` and `pytest` on 3.10 through 3.13. Both must pass before a pull request is
merged.

## Testing against a live schema

Most of the test suite runs anywhere: the schema is a fixture, and `tests/conftest.py` builds
a `Runtime` by hand. Nothing in CI touches a sandbox.

That is also the main gap in coverage. Anything that depends on how a real image behaves —
the shape the connector service actually returns, which environment variables are set, how
`--report` renders — is only exercised when someone runs the tool inside a Computer sandbox.
CI cannot do it, because the agent proxy is not reachable from a GitHub runner.

So if you are reporting a bug that only shows up in a sandbox, please include:

1. The output of `connector-lint env`.
2. The full traceback, not just the last line.
3. The image, if you know it. `SANDBOX_IMAGE_TAG` is unset on some images, in which case say
   so explicitly — "unset" is useful information.

## Rules

A new rule needs an entry in `docs/rules.md`, a test in `tests/test_rules.py`, and a
`CHANGELOG.md` line. Keep rules pure: they take call sites and a schema, and return findings.
Anything that performs I/O belongs in `schema.py` or `report.py`.

Severity is a judgement about whether the call will fail at runtime. `error` means it will.
`warning` means it might, or that it will silently not do what the author meant.
