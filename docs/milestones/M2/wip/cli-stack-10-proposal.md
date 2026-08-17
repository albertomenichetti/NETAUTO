# M2 Technology Proposal — STACK-10 Official HTTP CLI

**Status:** RATIFICATION PROPOSAL — CONSOLIDATION REQUIRED BEFORE M2 ARCHITECTURE FREEZE

**Authority:** TECHNOLOGY REVIEW INPUT — NON-NORMATIVE UNTIL CONSOLIDATED

## Purpose

This document records the project-wide technology decision selected by:

```text
docs/milestones/M2/architecture/cli.md
```

It is intentionally separate from the CLI semantic architecture because terminal and HTTP-client technologies are project-wide implementation choices.

The decision becomes authoritative only after explicit consolidation in:

```text
docs/general/technology_baseline.md
```

as a ratified `STACK-10` entry.

No dependency or implementation change is authorized by this proposal alone.

---

## Proposed STACK-10 — official HTTP CLI and terminal interaction

**Proposed status:** RATIFIED.

### Capability boundary

NETAUTO has one official operator/client CLI with:

```text
interactive asynchronous REPL
non-interactive single-command mode
public HTTP-only execution
complete same-release business API coverage
```

The CLI is not a wrapper for Uvicorn, Alembic, pytest or uv and is not an alternate application-service interface.

### HTTP client

```text
HTTPX AsyncClient
```

is the canonical CLI HTTP transport.

Required use:

```text
one scoped client per connected endpoint/session or non-interactive command
native asyncio
connection pooling
verified HTTPS
explicit finite timeouts
redirect following disabled
no automatic retry
```

HTTPX remains a client/infrastructure dependency. Its request/response types do not cross into the CLI command/result model or server application/domain layers.

The initial compatible project range should follow the already-used HTTPX major compatibility policy, conceptually:

```text
httpx>=0.28,<1
```

The exact version is resolved and committed through `uv.lock` during implementation.

### Interactive terminal

```text
prompt_toolkit 3.x
```

is the canonical REPL terminal toolkit.

Required use:

```text
PromptSession
prompt_async()
line editing
in-memory history integration
Ctrl-R reverse search
Ctrl-D and Ctrl-C key behavior
terminal clear support
```

`prompt_toolkit` owns terminal mechanics only. It does not own NETAUTO grammar, command registration, dispatch, state, HTTP behavior or output semantics.

The initial compatibility range should be:

```text
prompt-toolkit>=3.0,<4
```

with exact resolution through `uv.lock`.

### Process and parsing baseline

NETAUTO uses standard-library mechanisms for the remaining CLI substrate:

```text
argparse
    -> process mode and -n invocation

shlex
    -> interactive POSIX tokenization

json
    -> structured inline/file values and machine output

pathlib
    -> explicit file-backed JSON input

asyncio
    -> process coroutine and async terminal/HTTP integration
```

No general CLI framework is selected.

### Explicitly not selected

```text
Typer
Click
cmd2
Rich as a semantic/output authority
stdlib readline as the cross-platform REPL foundation
dynamic OpenAPI command generation
CLI plugin framework
```

Rationale:

```text
Typer/Click
    -> strong conventional subcommand frameworks
    -> do not naturally own the required long-lived custom REPL grammar
    -> would add a second command-description authority

cmd2
    -> larger command framework and sync-oriented command model
    -> unnecessary when NETAUTO already owns grammar and dispatch

Rich
    -> optional presentation library not required for deterministic text
    -> no semantic output should depend on terminal styling

stdlib readline
    -> platform and async integration burden
    -> more custom editing/history/key plumbing

OpenAPI generation
    -> generated schema is transport description, not semantic command authority
    -> same-release static registry is intentionally verified instead
```

### Architecture ownership

```text
prompt_toolkit
    -> terminal editing and key handling

HTTPX
    -> HTTP connection and request/response mechanics

Python standard library
    -> process/token/JSON/file primitives

NETAUTO CLI architecture
    -> command grammar
    -> selectors
    -> state machine
    -> static registry
    -> wire validation
    -> outputs and errors
```

### Dependency and packaging consequences

After implementation is authorized:

```text
pyproject.toml
    -> HTTPX becomes a runtime dependency, not dev-only
    -> prompt-toolkit becomes a runtime dependency
    -> project.scripts exposes netauto

uv.lock
    -> exact dependency resolution updated and reviewed

one NETAUTO wheel
    -> includes CLI modules and console entrypoint
```

The dependency change must not add:

```text
Typer
Click
cmd2
Rich
an alternative HTTP client
```

without a later explicit technology decision.

### Testing consequences

The ratified testing stack is extended, not replaced.

```text
HTTP transport
    -> HTTPX MockTransport / ASGI integration where appropriate

terminal behavior
    -> pure state-machine tests
    -> Linux PTY/process tests for Ctrl-R/Ctrl-D/Ctrl-C

package
    -> installed console-entrypoint verification
```

No fake HTTP or terminal test may be used to claim server PostgreSQL guarantees.

### Security consequences

The technology realization must preserve:

```text
HTTPS verification enabled
no insecure bypass
no native credential storage
no URL userinfo
no cookie persistence
no hidden retry
no persistent command history
```

HTTPX environment support may consume administered standard proxy/trust configuration; it does not create a NETAUTO profile or identity authority.

---

## Alignment with the existing technology baseline

The proposal is compatible with:

```text
STACK-01
    native asyncio and explicit I/O

STACK-03
    Pydantic transport validation without domain ownership

STACK-05
    explicit composition and no DI container

STACK-07
    pytest/pytest-asyncio and layered verification

STACK-08
    uv, Hatchling, Ruff, Pyright strict and src layout

STACK-09
    Uvicorn remains the server entrypoint
    Alembic remains the migration entrypoint
    the new CLI is a genuine NETAUTO HTTP client rather than a wrapper
```

STACK-09's statement that the delivered baseline has no custom operator CLI is superseded for M2 only after STACK-10 is ratified and the M2 architecture set is frozen.

---

## Ratification checklist

Before M2 architecture freeze:

```text
[ ] explicitly approve this technology choice
[ ] consolidate the decision as STACK-10 in technology_baseline.md
[ ] update the baseline status range to include STACK-10
[ ] update STACK-09's custom-CLI paragraph to reference STACK-10
[ ] ensure runtime-deployment.md owns wheel/dependency consequences
[ ] remove this item from architecture open points
```

During authorized implementation:

```text
[ ] update pyproject.toml runtime dependencies and project.scripts
[ ] update uv.lock
[ ] implement the neutral transport DTO boundary
[ ] execute CLI/PTY/package evidence from M2-VER-25 ... M2-VER-28
```

No contract reopening is required because the technology only realizes already-frozen CLI behavior.
