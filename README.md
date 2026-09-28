# pplx-connector-lint

[![CI](https://github.com/jamie0x33-bb/pplx-connector-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/jamie0x33-bb/pplx-connector-lint/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://github.com/jamie0x33-bb/pplx-connector-lint)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Lint a Perplexity Computer skill's connector usage against the **live** connector schema.

> Community project. Not affiliated with or endorsed by Perplexity AI.

## Why

Connector calls fail at runtime, in the middle of a task, for reasons that are invisible at
author time: a tool was renamed, a parameter became required, a connector is present in your
workspace but disconnected in the one the skill will actually run in. There is no version
string on the connector schema, so there is nothing to pin and nothing to diff.

`connector-lint` resolves the schema your workspace is actually being served and checks every
`connectors.call(...)` in a skill against it.

```console
$ connector-lint check ./my-skill
my-skill/search.py:41: error: [C003] connector 'gcal' exposes no tool 'search_mail'
my-skill/labels.py:12: warning: [C005] 'list_gmail_labels' ignores unknown parameter(s) max
2 call sites checked, 1 error(s), 1 warning(s)
```

## Install

Requires Python 3.10+. Must run inside a Computer sandbox — the schema is resolved through
the agent proxy, which is only reachable from there.

```bash
pip install pplx-connector-lint
```

From a checkout:

```bash
pip install -e '.[dev]'
```

## Usage

```console
$ connector-lint check [PATH] [--report] [--registry URL] [--json]
$ connector-lint env [--json]
```

| | |
| --- | --- |
| `check` | Lint a skill directory. Exits `1` if there is any error-severity finding. |
| `env` | Print the resolved runtime. Useful when a call fails and you need to know which connector service you are actually talking to. |
| `--report` | Upload the result to the schema registry — see [docs/registry.md](docs/registry.md). |
| `--json` | Machine-readable output, for CI. |

`connector-lint env` is the fastest way to find out whether you are in a sandbox at all:

```console
$ connector-lint env
sandbox               True
image_tag             computer/2026.08
kernel                6.1.141
connector_base_url    http://web-server-connectors:5556
tool_target_base_url  http://web-server-connectors:5556
registry_url          https://pplx-connector-lint.vercel.app
```

## Rules

| rule | severity | meaning |
| --- | --- | --- |
| `C001` | error | Unknown connector. |
| `C002` | warning | Connector exists but is not `CONNECTED` in this workspace. |
| `C003` | error | Connector exposes no such tool. |
| `C004` | error | A required parameter is missing. |
| `C005` | warning | A parameter the tool does not accept. |

Full descriptions and rationale in [docs/rules.md](docs/rules.md).

## Library

```python
from pathlib import Path

from pplx_connector_lint import check, load
from pplx_connector_lint.schema import fetch

runtime = load()
result = check(Path("my-skill"), fetch(runtime))

for finding in result.findings:
    print(finding.format())
print(result.summary())
```

Everything is typed and the package ships a `py.typed` marker.

## Exit codes

| code | meaning |
| --- | --- |
| `0` | No error-severity findings. |
| `1` | At least one error-severity finding. |
| `2` | Configuration error — usually not running in a sandbox. |
| `3` | The connector schema could not be fetched. |
| `4` | The registry rejected an upload. |

## Documentation

- [docs/rules.md](docs/rules.md) — every rule, with examples
- [docs/registry.md](docs/registry.md) — what `--report` sends and why
- [docs/configuration.md](docs/configuration.md) — environment variables
- [CHANGELOG.md](CHANGELOG.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and pull requests welcome.

## License

MIT — see [LICENSE](LICENSE).
