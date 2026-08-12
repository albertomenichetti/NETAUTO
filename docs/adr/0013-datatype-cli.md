# ADR 0013: DataType CLI

## Status

Accepted

## Context

NETAUTO needs a command-line interface for DataTypes while preserving the
REST-first architecture and avoiding a second execution path into backend
code.

## Decision

The CLI is REST-only. It does not import application, domain, persistence, or
API implementation modules. Typer is the command framework, and a synchronous
HTTPX client is the transport. The server root is configured by `--api-url` or
`NETAUTO_API_URL`, defaulting to `http://127.0.0.1:8000`. The CLI supports
human and JSON output modes, writes success to stdout and errors to stderr,
and uses stable exit codes `0/1/2/3/4`. Inline constraints use
`NAME=JSON_VALUE`. JSON file bodies mirror REST request bodies exactly, and
`--file -` reads stdin. There is no YAML, no current/latest behavior, and no
server startup fallback. The server remains authoritative for domain
semantics; the CLI performs only transport and input-syntax validation.
Arbitrary-size JSON integers must be preserved.

The DataType CLI exists inside the broader NETAUTO CLI, whose current
top-level groups are:

- `datatype`
- `object-template`
- `object`
- `relationship-definition`
- `relationship`

## Consequences

The CLI remains a thin, automatable HTTP client, and backend rules stay
centralized in the server.
