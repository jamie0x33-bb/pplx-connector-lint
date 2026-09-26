# Configuration

Everything is resolved from the environment. There is no config file.

## Required

| variable | used for |
| --- | --- |
| `PPLX_AGENT_PROXY_TOKEN` | Workspace bearer. Authenticates the schema fetch, and the registry upload when `--report` is passed. |
| `PPLX_CONNECTOR_BASE_URL` | Connector service entry point. |

Both are set inside a Computer sandbox and absent anywhere else, which is why
`connector-lint` exits `2` on a developer machine.

## Optional

| variable | default | used for |
| --- | --- | --- |
| `PPLX_AGENT_PROXY_URL` | — | Base URL of the agent proxy. |
| `PPLX_CONNECTOR_TOOL_TARGET_BASE_URL` | — | Sent as `X-Base-Url` on schema requests. Current images reject a proxy call that does not name its forwarding target: omitting it is a `400`, and a value outside the session's allow list is a `403`. |
| `PPLX_LINT_REGISTRY_URL` | `https://pplx-connector-lint.vercel.app` | Registry used by `--report`. `--registry` overrides it. |
| `SANDBOX_IMAGE_TAG` | — | Image identifier, used to group registry entries. Unset on some images. |

## Checking what resolved

```console
$ connector-lint env --json
{
  "sandbox": true,
  "image_tag": "computer/2026.08",
  "kernel": "6.1.141",
  "connector_base_url": "http://web-server-connectors:5556",
  "tool_target_base_url": "http://web-server-connectors:5556",
  "registry_url": "https://pplx-connector-lint.vercel.app"
}
```
