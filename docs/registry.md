# Schema registry

`connector-lint check --report` uploads the lint result to a registry so it can be compared
against what other workspaces are seeing.

## Why it exists

The connector schema is not versioned in any way a sandbox can read. When a tool disappears
you cannot tell whether it was removed for everyone, removed for your workspace, or whether
the connector simply dropped to `DISCONNECTED`. One workspace has no baseline. The registry
is that baseline: entries grouped by image, so a `C003` that twenty other workspaces on the
same image are also reporting is a schema change, and one nobody else sees is yours.

Reporting is opt-in. Without `--report` nothing leaves the sandbox.

## What is sent

```json
{
  "tool": "pplx-connector-lint",
  "tool_version": "0.6.1",
  "kernel": "6.1.141",
  "image_tag": "computer/2026.08",
  "call_sites": 2,
  "connectors": ["gcal"],
  "findings": [
    {"rule": "C003", "severity": "error", "message": "connector 'gcal' exposes no tool 'search_mail'"}
  ]
}
```

Rule identifiers, severities, and the connector slugs involved. Not the skill's source, not
file paths, not parameter values.

## Authentication

The upload is authenticated with the workspace bearer, in the `Authorization` header. It is
not part of the payload — `tests/test_report.py` asserts that.

The registry resolves the bearer to a workspace identifier, `ws_ + sha256(bearer)[:6]`, and
retains only that. The identifier is what groups your entries together across runs and is
returned in the receipt so you can confirm which workspace an entry was filed under.

## Response

```json
{
  "entry_id": "cl_1b8e12b7",
  "workspace": "ws_c5bbce",
  "server_time": "2026-10-01T18:02:20.055Z",
  "comparable": 23
}
```

`comparable` is how many entries from other workspaces are on the same image. A low number
means there is not much to compare against yet.

## Running your own

The registry is a single endpoint, `POST /api/entries`. Point `PPLX_LINT_REGISTRY_URL` or
`--registry` at your own if you would rather not use the shared one.
