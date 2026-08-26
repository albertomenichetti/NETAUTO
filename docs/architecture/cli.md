# Official CLI — Current AS-IS

## Purpose and authority

This document owns the official NETAUTO command-line client: process modes,
grammar, selectors, HTTP transport, session state, rendering and process results.
[`api.md`](api.md) is the sole operation/wire authority and
[`health.md`](health.md) owns readiness semantics. The CLI is always an HTTP
client; it never invokes application services or persistence directly.

## Entrypoint and modes

The versioned wheel exposes one console script:

```text
netauto = netauto.cli.main:main
```

Interactive invocation:

```text
netauto
```

opens the asynchronous `netauto>` REPL with exact initial state:

```text
connection = DISCONNECTED
output = FORMATTED
history = empty process-local history
```

Non-interactive invocation is exactly:

```text
netauto -n <endpoint-root> <resource> <operation>
    [selector] [parameter=value ...]
```

It executes one remote operation, prints one JSON result, prompts for nothing and
performs no implicit Health preflight.

## Client authority boundary

The API defines identity, semantics, status, request and response. The CLI:

```text
parses operator intent
resolves permitted human selectors through public GET requests
constructs one registered public request
validates the same-release response
renders the observed result and exchanges
```

It does not read `database_url`, create an engine/Unit of Work, execute Alembic,
perform mutable-state validation, invent domain identity or guess among ambiguous
resources. Neutral HTTP DTOs may be shared with server adapters; application,
persistence, SQLAlchemy, Psycopg, Alembic and FastAPI route execution remain
outside the CLI import closure.

## Endpoint and HTTP transport

An endpoint root is an absolute `http` or `https` URL with host and optional port,
an empty or `/` path, and no userinfo, query or fragment. The trailing slash is
normalized away. There is no default endpoint, profile or automatic discovery.

One interactive CONNECTED session owns one persistent HTTPX `AsyncClient`.
Non-interactive mode owns one client for its command. A command reuses that client
for selectors, primary request and bounded presentation enrichment.

Transport policy is exact:

```text
follow redirects          false
cookie persistence        none
native auth headers       none
HTTP retry                none
connect/pool timeout      5 seconds
read/write timeout        30 seconds
Accept                    application/json
User-Agent                netauto/<distribution-version>
Content-Type              application/json only with a body
```

HTTPS verifies certificate trust and hostname through the administered runtime
environment. There is no `--insecure`, `verify=false`, custom per-command CA,
client certificate or credential store. Plain HTTP is valid only inside the
trusted reachability boundary defined by
[`runtime-deployment.md`](runtime-deployment.md).

## Interactive state machine

Connection state is exactly `DISCONNECTED` or `CONNECTED(endpoint)`. Output mode
is independently `FORMATTED` or `JSON`.

The exact eight local commands are:

```text
/connect <endpoint-root>
/disconnect
/status
/output <JSON|FORMATTED>
/help [resource] [operation]
/history
/clear
/exit
```

`/connect` closes any current client, validates the candidate endpoint, performs
exactly `GET /health/core` and adopts the client only for a valid ready 200 DTO.
Any transport, protocol, HTTP or not-ready result leaves the session disconnected;
a failed replacement never restores the prior endpoint.

`/disconnect` closes locally and is idempotent. `/status` performs no HTTP while
disconnected and exactly one Health check while connected; every non-ready or
invalid outcome closes the client. An ordinary remote business response,
including a valid error response, preserves CONNECTED; a transport failure clears
it. A business protocol error is reported but preserves the reached endpoint.

`/output` changes mode before rendering its acknowledgment. `/help` is generated
only from the installed static registry and performs no OpenAPI request.
`/history` reports non-empty submitted lines in chronological one-based order and
is itself appended after rendering. `/clear` preserves connection, mode and
history. `/exit` closes transport and exits normally.

Terminal behavior:

```text
Ctrl-C while editing or searching  cancel current input; retain session
Ctrl-D on an empty prompt           /exit
Ctrl-R                              reverse search current process history
```

Command errors return to the prompt. No history, endpoint or output mode is
persisted across processes.

## Remote grammar and typed inputs

Canonical grammar:

```text
<resource> <operation> [selector] [parameter=value ...]
```

Resources are singular lowercase tokens; compound operations are kebab-case.
There is at most one positional selector. Parameter names are operation-specific
snake_case, split on the first `=`, unique and order-insensitive. `--parameter`
forms are not a second grammar. Interactive tokenization uses POSIX `shlex`;
non-interactive argv is not shell-parsed a second time.

Registry parameter kinds are positive integer, boolean, closed enum, UUID,
string/nullable string, datetime, JSON object/array/value and nested selector
carriers. Boolean is not integer. Structured values accept inline JSON or
`@path/to/file.json`, read once as UTF-8. There is no stdin sentinel, YAML/TOML or
custom nested DSL.

Omission means the HTTP field is omitted. `parameter=null` produces parsed
`None` only for a nullable registry field; request planning then applies the
parameter location:

```text
nullable QUERY None -> exact lexical query value null
nullable BODY None  -> JSON null
PATH None           -> invalid
```

The scalar serializer does not accept `None` generically. Complete candidate
arrays/maps remain complete caller intent; the CLI does not merge repeated
values or reinterpret ordering.

## Selector resolution

Top-level selector kinds are:

| Resource | Accepted selector |
|---|---|
| DataType | UUID or `<namespace>.<name>` |
| ObjectTemplate | UUID or `<namespace>.<name>` |
| Object | UUID or exact `canonical_name` |
| RelationshipDefinition | UUID only |
| Relationship | UUID only |
| RelationshipResolution | UUID only |

A syntactically valid UUID always has exact-ID precedence. Human names resolve
through exact public list filters with `limit=2`: zero gives
`cli_selector_not_found`, exactly one gives its UUID, and multiple/continued
results give bounded `cli_selector_ambiguous`. The same policy recursively
resolves registered nested ID fields.

One command traverses selector-bearing fields in registry order, preserves array
order for discovery, deduplicates identical `(kind,input)` pairs and resolves
sequentially. Memoization and the execution ledger are fresh per command; mutable
names are never carried into a later command.

### ObjectTemplate parent selector tri-state

The `object-template list` parameter `parent_template_id` is a nullable QUERY
parameter with an ObjectTemplate selector. Its exact behavior is:

```text
omitted
    -> no parent selector target
    -> no parent query pair

UUID
    -> exact-ID precedence
    -> canonical UUID query pair

<namespace>.<name>
    -> bounded ObjectTemplate discovery
    -> resolved UUID query pair

null
    -> parsed None
    -> zero selector-discovery GETs
    -> lexical parent_template_id=null query pair
```

Explicit null is a terminal nullable-selector value and never enters selector
lookup. The server owns the corresponding omitted/root/exact-parent filtering
and cursor presence distinction. `parent_filter_set` is not a CLI parameter.

## Static operation registry

One immutable registry drives parsing, help, selector planning, request
construction, expected status, response validation and renderer selection. Its
exact census is:

```text
datatype                 14
object-template          16
object                   13
relationship-definition 14
relationship              5
lifecycle-event           1
                         --
remote business total    63
local commands             8
```

Its `(method,path-template)` set equals the 63 business operations in
[`api.md`](api.md). `/connect` and `/status` consume `/health/core`; Health is not
a redundant business command. Every registered example parses under its own spec.

## Execution and result validation

A remote command executes:

```text
parse and local typed validation
deterministic selector GET plan
request candidate validation
one primary HTTP exchange
status/body/Location validation
optional FORMATTED GET-only enrichment
render
```

Successful status is exact: ordinary reads/mutations 200, creates 201 with exact
Location, and bodyless deletes/detach 204 with no body. A canonical server error
preserves its status/code/message/details. Invalid JSON, unexpected status/body,
redirect or malformed server DTO is `cli_protocol_error`. HTTPX failures are one
`cli_transport_error` attempt. Raw exception text and stack traces are not public
CLI output.

### Registered `201 Created` Location protocol

The exact eight registered `201 Created` operations are DataType create and
create-next, ObjectTemplate create and create-next, Object create,
RelationshipDefinition create and create-next, and Relationship create. Each has
one Location template interpreted by the closed NETAUTO grammar:

```text
{segment}
{segment.segment...}
segment = [a-z][a-z0-9_]*
```

For each token, exact `request_values` key presence wins. Otherwise the token is
resolved by dot-separated traversal through the already validated response JSON
object. Only `str` and `int` excluding `bool` can materialize a token. Replacement
is literal; Python `str.format`, `format_map`, array indexing, attribute access,
wildcards, conversions and format specifications are outside the grammar.

The registered templates use one common mechanism:

```text
datatype create
    /api/v1/core/datatypes/{datatype.id}
datatype create-next
    /api/v1/core/datatypes/{datatype_id}/versions/{version}
object-template create
    /api/v1/core/object-templates/{object_template.id}
object-template create-next
    /api/v1/core/object-templates/{template_id}/versions/{version}
object create
    /api/v1/core/objects/{id}
relationship-definition create
    /api/v1/core/relationship-definitions/{relationship_definition.id}
relationship-definition create-next
    /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
relationship create
    /api/v1/core/relationships/{id}
```

A registered create succeeds only after the expected status and body validate,
the actual response contains exactly one `Location`, the expected value is
materializable, and actual equals expected exactly. Missing, repeated,
mismatching or non-materializable Location state is `cli_protocol_error`. A
canonical successful response does not become `cli_internal_error` solely from
Location processing. No Location normalization or hidden post-mutation GET is
performed.

Every attempted exchange is recorded once, in order. An observed response is
retained even when later tracing/cleanup fails; a pre-send failure records no
exchange and a send failure records one exchange with `response = null`.

## JSON output

JSON mode emits one stable object:

```text
status      ok | error
command     parsed original intent or null before a safe command exists
exchanges   ordered actual exchange snapshots
result      successful primary body, otherwise null
error       null or structured source/code/message/details/http_status
```

Error source is exactly `local`, `selector`, `transport`, `remote` or `protocol`.
Request/response snapshots are recursively detached immutable values and include
method, normalized URL, query, bounded relevant headers, logical body, response
status/body format/body and non-negative monotonic elapsed milliseconds.

Non-interactive stdout is exactly this object plus newline. Success exits 0; any
structured command failure exits 1. Stderr is empty for normal structured
outcomes and reserved for unrecoverable process bootstrap diagnostics.

## FORMATTED output

FORMATTED mode exists only in the REPL and uses deterministic plain UTF-8 text.
Exact IDs remain visible; color/style is never semantic; pages show their cursor.

Mutations display only their direct response and perform no hidden GET. Lists
render only the primary page and never perform per-item N+1 enrichment. Registered
single-resource reads may perform bounded public GET enrichment for human names
and exact lineage context. Enrichment is identity-validated, memoized within the
command and complete-or-fail; it never emits a partial complete-looking result.
JSON mode performs no presentation-only enrichment.

## Failure catalogue

Local codes are finite:

```text
cli_invalid_invocation  cli_invalid_command
cli_missing_selector    cli_unexpected_selector
cli_missing_parameter   cli_unexpected_parameter
cli_duplicate_parameter cli_invalid_parameter
cli_json_error           cli_file_error
cli_not_connected        cli_internal_error
cli_selector_invalid     cli_selector_not_found
cli_selector_ambiguous   cli_transport_error
cli_protocol_error
```

Remote business codes remain the exact API catalogue without prefix or remapping.
Cancellation and other `BaseException` values are not normalized as ordinary
command failures.

## Packaging and compatibility

CLI and server ship in the same `netauto` wheel and distribution version. Equal
release versions are the supported pair. There is no negotiation endpoint or
cross-release guarantee. CLI-only import/invocation requires no database setting
and loads no server composition or persistence path.

## Durable verification

Verification machine-checks the 63/63 registry equality, eight local commands,
parser and examples, selector zero/one/many behavior, fresh ledger/memo state,
transport policy, truthful exchange snapshots, process channels, PTY-visible
Ctrl-C/Ctrl-D/Ctrl-R behavior, no persistent history, HTTP-only imports,
FORMATTED enrichment bounds, installed-wheel operation and trusted/untrusted/
hostname-mismatch HTTPS cases. It also proves the exact eight-operation 201
Location census and grammar/protocol matrix, plus ObjectTemplate omission, UUID,
human-selector and explicit-null behavior with zero discovery for null.
