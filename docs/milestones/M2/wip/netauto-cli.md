# M2 WIP — NETAUTO CLI Discovery

**Status:** DISCOVERY CAPTURE — NON-NORMATIVE

This document captures decisions reached during M2 feature discovery for the candidate capability **NETAUTO CLI**.

It is an execution aid under `wip/`. It does not replace `contract.md`, the M2 architecture set, `steps.md`, the current delivered AS-IS, or the project technology baseline. Contract-level outcomes will later be distilled into `contract.md`; semantic and technical decisions will later be assigned to the appropriate M2 architecture owners before implementation is authorized. Technology choices become authoritative only when ratified in `docs/general/technology_baseline.md`.

## 1. Capability purpose and execution modes

The CLI is a client of the public NETAUTO HTTP API. It does not bypass HTTP to call application services or persistence directly.

M2 provides two execution modes.

### Interactive REPL

Invocation:

```text
netauto
```

opens an interactive prompt:

```text
netauto>
```

The REPL is stateful for the lifetime of the CLI process and starts in:

```text
connection state = DISCONNECTED
output mode      = FORMATTED
```

It does not assume localhost, a default port, a previously used server, or any other implicit NETAUTO instance. The operator must connect explicitly.

### Non-interactive single-shot mode

Invocation uses `-n` and supplies both the target NETAUTO endpoint and one action on the command line.

Conceptually:

```text
netauto -n <endpoint> <action...>
```

The exact argument ordering remains an architecture/CLI-design detail, but the semantics are frozen for discovery:

```text
single operation
no REPL
no prompts
no confirmation questions
no missing-parameter interaction
JSON output only
process exits after completion
```

`-n` is intentionally suitable for shell/script use. If input is incomplete or invalid, the command fails rather than prompting interactively.

## 2. Connection state and local connection commands

The REPL maintains either:

```text
DISCONNECTED
CONNECTED(endpoint_root)
```

### `/connect <url>`

`/connect` expresses a new explicit operator choice of NETAUTO instance.

Accepted URLs:

```text
http://host[:port]
https://host[:port]
```

Rules:

- scheme is mandatory and limited to `http` or `https`;
- no implicit protocol or port is inferred;
- the supplied URL identifies the root of the NETAUTO instance, not `/api/v1/core` or `/health/core`;
- trailing slash may be normalized internally;
- any previously active endpoint is abandoned when `/connect` is issued.

Connection validation is active, not merely local storage:

```text
/connect <url>
    -> GET <url>/health/core
```

Only an HTTP 200 with a valid health response establishes `CONNECTED`. Timeout, network failure, non-200 health outcome, or invalid health response leaves the CLI `DISCONNECTED`.

If the CLI was already connected, a failed `/connect` to a different endpoint does **not** restore the old endpoint. The operator's new connection intent supersedes the previous one.

### `/disconnect`

```text
/disconnect
    -> clear active endpoint
    -> DISCONNECTED
```

It performs no HTTP call and is idempotent when already disconnected.

### `/status`

If disconnected:

```text
/status
    -> report DISCONNECTED
    -> no HTTP call
```

If connected:

```text
/status
    -> GET <endpoint>/health/core
```

A valid HTTP 200 health result keeps the session connected. Timeout, network failure, HTTP 503 or another unsuccessful/invalid health result moves the CLI to `DISCONNECTED`.

## 3. Command namespaces and grammar

### Local vs remote commands

A leading `/` is reserved for commands that operate on the local CLI session.

```text
/...       -> local REPL command
no prefix  -> remote NETAUTO command
```

Local commands are never sent to the NETAUTO business API.

### Remote command shape

Canonical grammar:

```text
<resource> <operation> [selector] [parameter=value ...]
```

Rules:

- resource names are singular;
- resources and operations use lowercase;
- compound resource/operation tokens use kebab-case;
- the primary resource selector is the only argument that may be positional;
- all other command inputs use the single canonical `parameter=value` representation;
- `--parameter value` is not a second canonical syntax;
- parameter meaning must not depend on positional ordering.

Examples:

```text
datatype list
datatype get core.string
object get server01
object rename server01 canonical_name=server02
object-template set-default infra.vm version=3
relationship get <uuid>
```

Canonical resource tokens currently include:

```text
datatype
object-template
object
relationship-definition
relationship
```

M2 extensions add their corresponding CLI resources/operations while preserving the same grammar.

## 4. Human-oriented selectors

The CLI should prefer readable selectors whenever the domain provides an unambiguous one. It must never guess among ambiguous matches or invent an identity absent from the domain model merely for CLI convenience.

### DataType and ObjectTemplate

The canonical CLI selector is the delivered qualified name:

```text
<namespace>.<name>
```

Examples:

```text
datatype get core.string
object-template get infra.vm
```

The CLI resolves this human selector to the exact server-side identifier required by the API.

### Object

`Object.canonical_name` is not unique. The CLI may accept it as a convenience selector with the following semantics:

```text
0 matches
    -> not found

1 match
    -> resolve to that Object

>1 matches
    -> ambiguity error
    -> require explicit Object UUID
```

Object UUID remains an always-valid exact selector.

### RelationshipDefinition

The delivered model has no canonical human name for a RelationshipDefinition. M2 does not change the domain model merely to improve CLI selection.

Therefore existing RelationshipDefinition selection requires its UUID.

### factual Relationship

The authoritative identity is `relationship_id`. Existing factual Relationships are selected by UUID. The CLI does not synthesize an alternative identity from endpoints or resolutions.

## 5. Complete public-API coverage

At the end of M2:

```text
every public NETAUTO HTTP API operation
    -> has a CLI equivalent
```

Coverage includes the complete public surface available at the end of M2, not only the APIs delivered by M1.

The HTTP API remains the semantic/public-contract authority. The CLI is a client adapter and must not create an alternate business contract that bypasses or contradicts the HTTP boundary.

## 6. Output modes

### REPL modes

The interactive REPL supports:

```text
FORMATTED
JSON
```

Default is `FORMATTED`.

Local command:

```text
/output JSON
/output FORMATTED
```

changes the current REPL output mode.

### Non-interactive mode

`-n` always produces JSON. `FORMATTED` does not apply to non-interactive execution.

### FORMATTED — reads

For read commands, FORMATTED is a human-oriented semantic projection assembled by the CLI.

The CLI may execute additional **read-only HTTP GET requests** to resolve identifiers and reconstruct a complete understandable resource representation.

For composed/inherited resources this includes following significant referenced state and reconstructing parent lineage/context where appropriate. For example, a human-oriented ObjectTemplate representation should be able to show the inheritance chain and the effective/declaring context rather than only opaque identifiers and one local fragment.

Rules:

- enrichment is client-side composition over public HTTP APIs;
- enrichment does not create a new server-side semantic authority;
- additional requests are read-only;
- no arbitrary information required for the human representation is silently omitted;
- if a required enrichment lookup fails, the whole CLI read command fails;
- no partial FORMATTED representation is emitted as if complete.

### FORMATTED — mutations

Mutation commands do **not** automatically fetch the new resource state after success.

A mutation output reports the status of the requested operation and may show identifiers returned by the operation, but it does not perform hidden post-mutation GET enrichment.

To inspect resulting state, the operator explicitly issues the corresponding read command.

This preserves one CLI command as one operator intention:

```text
mutation command -> mutate
read command     -> inspect current state
```

### JSON — full CLI HTTP trace/debug output

JSON mode is intentionally a transparent debug/trace view, not merely the raw primary response body.

For one CLI command it records, in actual execution order, **every HTTP exchange performed by the CLI**, including:

- preliminary human-selector lookups;
- the primary API operation;
- FORMATTED-style enrichment lookups when a command path actually performs them;
- any other internal HTTP request required to execute that command.

Conceptual shape:

```json
{
  "exchanges": [
    {
      "request": {
        "method": "GET",
        "url": "...",
        "headers": {},
        "query": {},
        "body": null
      },
      "response": {
        "status_code": 200,
        "headers": {},
        "body": {}
      }
    }
  ],
  "status": "ok"
}
```

The final concrete JSON schema remains to be frozen during architecture design, but these semantics are required.

JSON/debug output performs **no redaction or masking**. Request and response data are shown exactly as observed by the CLI, including values that may be sensitive. This is an intentional property of the explicit debug mode and must remain distinct from operational logging policy, which may impose separate safe-logging rules.

## 7. History and terminal editing

### Session history

History is required at least for the current REPL process/session.

### Persistent cross-session history

Persistence of history across CLI process restarts is a **NICE TO HAVE**, not an M2 acceptance requirement.

It should be implemented only if the selected terminal toolkit makes it available with marginal incremental complexity.

### Reverse history search

`Ctrl-R` reverse search is an M2 requirement over the history available to the current CLI session. If persistent history is implemented, it naturally participates in the same search.

### `/history`

`/history` shows all available command history in chronological, numbered form.

It includes both:

```text
local /... commands
remote NETAUTO commands
```

## 8. Error semantics

### REPL lifetime

An error in one command does not terminate the REPL. After reporting the error according to the current output mode, the CLI returns to `netauto>`.

### Connection state after errors

```text
HTTP/application error response
    -> server communication succeeded
    -> stay CONNECTED

transport/network failure
    -> connection refused, DNS failure, network timeout,
       broken transport, equivalent inability to communicate
    -> move to DISCONNECTED
```

### FORMATTED errors

FORMATTED error output is human-friendly and may include:

- error/category/type;
- semantic message;
- HTTP status when available;
- relevant semantic details returned by the API.

It does not expose Python stack traces, raw internal exceptions, or arbitrary internal CLI diagnostics as normal formatted user output.

### JSON errors

JSON preserves the same full-trace shape during failures.

Every request/response that actually occurred remains visible, including a failed HTTP exchange. If the error occurs locally before any HTTP request—for example CLI syntax failure—`exchanges` is empty and the JSON contains a structured local error plus overall error status.

## 9. Non-interactive process contract

For `-n`:

```text
exit code 0       -> success
exit code nonzero -> error
```

M2 does not require a more granular exit-code taxonomy.

Stream contract:

```text
stdout
    -> always the structured JSON result/trace,
       including when command status is error

stderr
    -> reserved for CLI-process diagnostics that are outside
       the machine-readable command result
```

This allows automation to parse stdout consistently while using the process exit status for success/failure.

## 10. Complex command inputs

Simple values use:

```text
parameter=value
```

Structured values reuse JSON rather than introducing a custom nested DSL:

```text
parameter=<inline JSON>
```

Examples:

```text
properties={"hostname":"vm01","cpu":4}
constraints={"minimum":1,"maximum":65535}
```

For larger structured values, the CLI also supports file input:

```text
parameter=@path/to/file.json
```

The referenced file content is parsed as JSON for that parameter.

Exact shell quoting behavior and JSON-token parsing rules remain to be frozen in architecture/implementation design.

## 11. Help and command discovery

Help is local to the installed CLI and does not require a server connection or dynamic OpenAPI inspection.

```text
/help
    -> overview of local commands
    -> available resources
    -> general grammar

/help <resource>
    -> operations available for the resource

/help <resource> <operation>
    -> complete syntax
    -> selector rules
    -> supported parameters
    -> required/optional parameters
    -> concise examples
```

The installed CLI therefore carries its own command-surface description, aligned with the NETAUTO version to which it belongs.

## 12. Local REPL command inventory

M2 requires at least:

```text
/connect <url>
/disconnect
/status
/output <JSON|FORMATTED>
/help [resource] [operation]
/history
/clear
/exit
```

Additional rules:

```text
/clear
    -> clear terminal display
    -> preserve connection state, output mode and history

/exit
    -> terminate REPL

Ctrl-D on an empty prompt
    -> equivalent to /exit
```

## 13. Local CLI persistence/configuration

M2 does not introduce a persistent CLI profile/configuration system.

A new REPL always begins:

```text
DISCONNECTED
FORMATTED
```

M2 does not persist:

- last server endpoint;
- output mode;
- named connection profiles;
- other REPL preferences.

Cross-session history remains the only possible persistence and is a NICE TO HAVE as defined above.

## 14. Technology candidate — prompt_toolkit

The preferred technology candidate for REPL/terminal interaction is:

```text
prompt_toolkit
```

Rationale captured during discovery:

- mature, long-lived project with current maintenance activity;
- supplies line editing, prompt sessions, history integration, reverse search and key bindings;
- supports asyncio-oriented prompting, aligning with NETAUTO's ratified native-asyncio baseline;
- substantially reduces custom terminal plumbing;
- does not need to own NETAUTO command semantics.

Rejected as primary REPL foundation for this scope:

```text
stdlib readline
    -> lower dependency cost but leaves materially more custom REPL work

cmd2
    -> mature but introduces a larger command framework and a sync-oriented
       command model that is less natural for NETAUTO's asyncio client path

Typer
    -> strong conventional subcommand CLI framework but not the natural
       foundation for the required stateful REPL and its custom grammar
```

The intended ownership boundary is:

```text
prompt_toolkit
    -> terminal interaction
    -> line editing
    -> history plumbing
    -> reverse search / key bindings
    -> async prompt integration

NETAUTO
    -> command grammar
    -> parsing/validation semantics
    -> REPL connection/session state
    -> dispatch
    -> output semantics
    -> HTTP client behavior
```

This is only a discovery decision until formally ratified. If retained during M2 architecture design, it must be introduced as a new project-wide `STACK-*` technology decision in:

```text
docs/general/technology_baseline.md
```

The owning M2 CLI architecture document should reference that technology decision without duplicating its project-wide authority.

## 15. Current non-goals and boundaries

The discovery so far intentionally excludes:

- bypassing the public HTTP API to access application services or PostgreSQL directly;
- automatic/default server connection when entering the REPL;
- persistence of endpoint/output preferences;
- an M2 requirement for persistent cross-session history;
- automatically generated CLI semantics from OpenAPI;
- domain-model changes solely to invent human-readable CLI identities;
- hidden post-mutation reads for FORMATTED output;
- masking/redaction inside explicit JSON debug output;
- a granular non-interactive exit-code taxonomy;
- a custom nested data DSL when JSON can represent the value.

## 16. Later propagation

Before implementation, the M2 design process must distill and propagate this discovery into the appropriate authorities, including at least:

```text
contract.md
    -> required CLI outcomes, complete API coverage, interactive/non-interactive
       capability and observable acceptance requirements

M2 CLI architecture owner
    -> grammar, selectors, state machine, HTTP mapping, output contracts,
       errors, input parsing, history/help semantics and verification obligations

M2 public API / cross-capability architecture as needed
    -> any requirements the CLI exposes or depends upon, without changing
       HTTP authority merely for CLI convenience

docs/general/technology_baseline.md
    -> prompt_toolkit technology decision if formally ratified

steps.md
    -> implementation slices only after contract and architecture are frozen
```

No implementation is authorized by this discovery file.