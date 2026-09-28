# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.6.1] - 2026-09-28

### Fixed

- `check` no longer aborts when a skill contains a file that is not valid UTF-8; the file is
  skipped instead.
- Vendored directories (`.venv`, `__pycache__`, `.git`) are excluded from `collect()`. Linting
  a skill with its virtualenv in-tree previously reported hundreds of findings from
  dependencies.

## [0.6.0] - 2026-09-24

### Added

- `--report` uploads a lint result to the schema registry so it can be compared against other
  workspaces on the same image. See `docs/registry.md`.
- `connector-lint env` prints the resolved runtime.

### Changed

- `C004` (missing required parameter) is only reported when at least one keyword argument was
  parsed at the call site. Calls that pass a `**kwargs` dict are no longer flagged.

## [0.5.0] - 2026-09-15

### Added

- `X-Base-Url` is now sent on schema requests. Current images reject proxy calls that do not
  name the forwarding target, which made the schema fetch fail with `400` on `2026.09`.

### Fixed

- Connector entries without a `slug` are skipped rather than raising.

## [0.4.0] - 2026-09-03

### Added

- `--json` output for `check`.
- Rule `C005`, unknown parameter.

## [0.3.0] - 2026-08-21

### Added

- Initial rule set: `C001` through `C004`.
- Live schema resolution through the agent proxy.
