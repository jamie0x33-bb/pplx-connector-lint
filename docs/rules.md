# Rules

Every rule compares a `connectors.call(...)` site against the live connector schema for the
workspace the linter is running in.

Severity is a judgement about runtime behaviour: `error` means the call will fail, `warning`
means it might, or that it will silently do something other than what the author meant. Only
`error` affects the exit code.

## C001 — unknown connector

**error.** The connector slug does not appear in the schema at all.

```python
connectors.call("slack", "post_message", channel="#eng")
```

Usually a typo, or a skill written against a workspace that has a connector this one does
not. The schema is per-workspace, so "it works on mine" is not evidence.

## C002 — connector is not connected

**warning.** The connector exists but its status is not `CONNECTED`.

```python
connectors.call("notion", "search", query="roadmap")
```

The call will fail until someone connects it. It is a warning rather than an error because
the skill may be intended for a workspace where it is connected, and connecting it is a
user action rather than a code change.

## C003 — unknown tool

**error.** The connector exists but exposes no tool by that name.

```python
connectors.call("gcal", "search_mail", query="invoice")   # it is search_email
```

This is the most common finding in practice, because tool names change without notice and
there is no deprecation period.

## C004 — missing required parameter

**error.** The schema marks a parameter required and the call site does not pass it.

```python
connectors.call("gcal", "search_email", limit=5)   # query is required
```

Only reported when at least one keyword argument was parsed at the call site. A call that
forwards a `**kwargs` dict is not flagged, because the linter cannot see what is in it.

## C005 — unknown parameter

**warning.** The call passes a keyword the tool does not accept.

```python
connectors.call("gcal", "search_email", query="x", folder="INBOX")
```

Unknown parameters are dropped rather than rejected, so this is the failure mode where the
call returns `200` and quietly ignores half of what you asked for. Worth treating as an
error in CI even though the linter does not.
