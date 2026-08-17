# M2 Official CLI Architecture

**Status:** DRAFT — CLI DESIGN COMPLETE — API/HEALTH/RUNTIME/VERIFICATION/STACK-10 CROSS-CHECK PASSED — FINAL CLOSURE PENDING

**Authority:** NORMATIVE M2 ARCHITECTURE DRAFT

## Authority and scope

This document owns the M2 official NETAUTO CLI architecture for:

```text
interactive REPL and non-interactive process modes
connection and output state machines
endpoint-root and HTTP transport behavior
static command grammar and command registry
human-oriented selector resolution
structured input parsing and file-backed JSON values
complete 63-operation business API mapping
Health-backed /connect and /status behavior
FORMATTED and JSON output contracts
local/remote/transport/protocol failure handling
terminal editing, help and in-memory history
same-release compatibility and packaging handoff
CLI-specific verification hooks
```

Its implementation authority, once the complete M2 architecture set is frozen, is:

```text
docs/milestones/M2/contract.md
    FINAL / FROZEN CLI outcomes
+
docs/milestones/M2/architecture/api.md
    exact 63-operation business HTTP inventory and wire contract
+
docs/milestones/M2/architecture/health.md
    exact /health/core readiness contract
+
docs/milestones/M2/architecture/verification.md
    M2-VER-25 ... M2-VER-28 and dependent evidence obligations
+
docs/general/technology_baseline.md
    ratified CLI transport and terminal technology
+
this document
    official client realization
```

This document does not own:

```text
server-side business or Health semantics
    -> relationship.md, api.md and health.md

persistence, schema or transaction behavior
    -> persistence.md, concurrency-matrix.md and concurrency.md

wheel content, release metadata and Linux installation
    -> runtime-deployment.md

executed evidence and final delivery records
    -> verification.md and future steps.md
```

The CLI remains a client of the public HTTP surface. Sharing transport-only DTO definitions or command metadata with the server package does not authorize an application-service, Unit-of-Work or database execution path.

Discovery under `../wip/netauto-cli.md` is superseded by this document for the areas owned here.

---

## 1. Governing client boundary

The authority direction is:

```text
NETAUTO HTTP API
    -> resource identity
    -> command semantics
    -> success/failure outcome
    -> request/response wire shape

official CLI
    -> parse operator intent
    -> resolve permitted human selectors through public GET requests
    -> invoke the public HTTP operation
    -> validate the same-release response
    -> present the result
```

The CLI never:

```text
imports or invokes application services as an execution path
creates a PostgreSQL engine or UnitOfWork
reads database_url
executes Alembic
reimplements domain admission or migration logic
changes an HTTP failure into a different business outcome
guesses among ambiguous resources
creates a second identity authority
```

Local validation may reject malformed CLI syntax or an input that cannot be represented by the target HTTP contract. Mutable-state and domain validation remain server authority.

---

## 2. Process modes and entrypoint

The wheel exposes exactly one console entrypoint:

```text
netauto
```

Conceptual package entry:

```toml
[project.scripts]
netauto = "netauto.cli.main:main"
```

The synchronous console function owns only process bootstrapping and runs one native-asyncio main coroutine.

### 2.1 Interactive mode

```text
netauto
```

opens:

```text
netauto>
```

Initial state is always:

```text
connection = DISCONNECTED
output     = FORMATTED
history    = empty in-memory session history
```

No localhost, port, previous endpoint, profile or environment-derived server is assumed.

### 2.2 Non-interactive mode

The exact canonical invocation is:

```text
netauto -n <endpoint-root> <resource> <operation> [selector] [parameter=value ...]
```

Rules:

```text
exactly one remote operation
no REPL
no local /command
no prompt or confirmation
no missing-value interaction
JSON output only
one process result
```

Any other process-level argument shape is a local CLI error.

M2 introduces no second long-form mode, command alias framework or granular process-exit taxonomy.

---

## 3. Ratified technology realization

The CLI architecture selects the following project-wide technology decision, captured for ratification as the proposed `STACK-10` in `../wip/cli-stack-10-proposal.md`.

M2 uses:

```text
HTTP client
    -> HTTPX AsyncClient

terminal/REPL
    -> prompt_toolkit PromptSession.prompt_async()

process option parsing
    -> Python stdlib argparse or equivalent explicit stdlib parsing

REPL tokenization
    -> Python stdlib shlex, POSIX mode

JSON and file input
    -> Python stdlib json + pathlib
```

It does not adopt:

```text
Typer
Click
cmd2
Rich as an output authority
dynamic OpenAPI command generation
a plugin command framework
```

The technology owns transport and terminal mechanics only. NETAUTO owns grammar, state, command registry, selector semantics, output and errors.

---

## 4. Conceptual module ownership

The conceptual package is:

```text
src/netauto/cli/
    main.py
        console entrypoint and process mode selection

    model.py
        immutable CLI command, result, trace and error values

    registry.py
        static local-command and 63-operation remote registry
        parameter schemas
        route/method/status mapping
        response-validator and renderer mapping

    parser.py
        argv and REPL token parsing
        parameter decoding
        JSON/file-backed values

    selectors.py
        human selector classification
        deterministic public-GET resolution
        per-command selector memoization

    transport.py
        endpoint validation
        HTTPX client lifecycle
        request/response capture
        timeout, TLS, redirect and cookie policy

    protocol.py
        transport-only request/response validation
        canonical business-error and Health decoding

    execution.py
        selector plan
        primary HTTP operation
        optional FORMATTED enrichment
        result/error construction

    render.py
        FORMATTED renderers
        canonical JSON trace serialization

    repl.py
        PromptSession
        session state
        local commands
        history and key behavior
```

M2 factors transport-only Pydantic DTOs from route modules into the neutral package:

```text
src/netauto/transport/http/
```

This package is the single implementation authority for request, response, business-error and Health wire models consumed by both the server adapters and the official CLI. It:

```text
contains no FastAPI Request/Response objects
contains no application service or persistence import
does not own semantics
is imported by server adapters and the CLI only for wire validation
```

The static command registry remains separate from DTO classes and is the sole CLI command/help/dispatch authority. Sharing DTO classes never shares route execution, application services or persistence.

---

## 5. Endpoint-root contract

An endpoint root is accepted only when all conditions hold:

```text
absolute URL
scheme exactly http or https, case-normalized
host present
optional explicit port
path empty or "/"
no username or password
no query
no fragment
```

Examples:

```text
valid
    http://127.0.0.1:8000
    https://netauto.example.test
    https://[2001:db8::10]:8443/

invalid
    netauto.example.test
    ftp://netauto.example.test
    https://user:secret@netauto.example.test
    https://netauto.example.test/api/v1/core
    https://netauto.example.test?profile=x
```

A trailing root slash is normalized away. The normalized value is the base for exact paths:

```text
<root>/api/v1/core/...
<root>/health/core
```

The CLI does not support a custom URL prefix or proxy path rewrite as an M2 compatibility contract.

---

## 6. HTTP transport policy

### 6.1 Client lifecycle

Interactive mode owns at most one current endpoint client.

```text
CONNECTED(endpoint)
    -> one scoped AsyncClient for that endpoint

/connect new-endpoint
    -> close and discard any previous client first
    -> create candidate client
    -> validate Health
    -> adopt only on success

/disconnect or /exit
    -> close current client
```

Non-interactive mode creates one scoped client for the supplied endpoint and closes it after the command.

The CLI does not construct a new client inside every selector or enrichment request; one command reuses its scoped client and connection pool.

### 6.2 TLS and trust

```text
https
    -> certificate verification enabled
    -> hostname verification enabled
    -> administered runtime/system trust environment

http
    -> permitted only within the frozen trusted-boundary contract
```

The client may use the administered standard environment for proxy and trust-store discovery; this does not create a NETAUTO profile or credential authority.

The CLI has no:

```text
--insecure
verify=false
custom per-command CA
client certificate
credential profile
Authorization parameter
```

URL userinfo is forbidden.

### 6.3 Redirect, cookie and authentication behavior

```text
follow_redirects = false
no Cookie request state
no persistence of Set-Cookie
no native authentication header
```

A redirect is observed as the response actually returned and is not followed as a hidden exchange.

### 6.4 Timeouts and retries

The client uses finite transport timeouts:

```text
connect timeout = 5 seconds
pool timeout    = 5 seconds
read timeout    = 30 seconds
write timeout   = 30 seconds
```

These are CLI transport constants, not server SLAs or M2 runtime settings.

Each planned HTTP request is attempted once:

```text
no HTTP retry
no redirect retry
no semantic mutation retry
```

Server-side semantic retry remains entirely inside the server operation defined by the concurrency architecture.

### 6.5 Request headers

The CLI explicitly sends:

```text
Accept: application/json
User-Agent: netauto/<release-version>
Content-Type: application/json
    only when a JSON body exists
```

It sends no cookie or authorization state.

---

## 7. Interactive session state machine

State is exactly:

```text
DISCONNECTED
or
CONNECTED(normalized_endpoint_root)
```

Output mode is independently:

```text
FORMATTED
JSON
```

### 7.1 Remote command while disconnected

A remote command in `DISCONNECTED` fails locally:

```text
code = cli_not_connected
exchanges = []
```

It does not attempt implicit connection or localhost discovery.

### 7.2 `/connect <endpoint-root>`

Pipeline:

```text
1. require exactly one endpoint argument
2. discard and close any current connection
3. normalize/validate the new endpoint
4. create a candidate HTTP client
5. execute exactly GET /health/core
6. require:
       HTTP 200
       valid exact Core Health DTO
       app_status.status == ok
       db_status.status == ok
7. success:
       adopt candidate client
       state = CONNECTED
8. any failure:
       close candidate
       state = DISCONNECTED
```

A prior endpoint is never restored after failed replacement intent.

`503`, redirect, business-error body, malformed JSON, invalid Health DTO and transport failure all fail connection.

### 7.3 `/disconnect`

```text
close current client if any
clear endpoint
state = DISCONNECTED
no HTTP exchange
```

It is locally idempotent.

### 7.4 `/status`

```text
DISCONNECTED
    -> local status only
    -> no HTTP exchange

CONNECTED
    -> exactly GET /health/core
    -> valid ready 200 keeps CONNECTED
    -> every other outcome closes client and becomes DISCONNECTED
```

### 7.5 State after ordinary remote commands

```text
valid HTTP response, including business 4xx/5xx
    -> transport reached the endpoint
    -> preserve CONNECTED

business-response protocol error
    -> preserve CONNECTED
    -> report cli_protocol_error

HTTPX transport failure
    -> close client
    -> state = DISCONNECTED
```

`/connect` and `/status` are stricter because their purpose is to establish or revalidate session connection state.

---

## 8. Local REPL commands

The exact local inventory is:

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

No local token is sent to the business API.

### 8.1 `/output`

```text
/output JSON
/output FORMATTED
```

The argument is case-sensitive and exact.

The state change applies before the command acknowledgment is rendered:

```text
/output JSON
    -> acknowledgment is JSON

/output FORMATTED
    -> acknowledgment is formatted text
```

### 8.2 `/help`

Help is generated only from the installed static registry.

```text
/help
    -> grammar, local commands and resources

/help <resource>
    -> exact operation list

/help <resource> <operation>
    -> selector type
    -> required/optional parameters and types
    -> exact HTTP operation
    -> concise examples
```

Help requires no endpoint and performs no OpenAPI request.

### 8.3 `/history`

The CLI maintains a separate in-memory chronological list of non-empty submitted lines.

```text
/history
    -> shows all lines completed before the current invocation
    -> includes local and remote commands
    -> numbered from 1
```

The `/history` invocation is appended after its result is rendered.

M2 deliberately does not persist history across process restarts. This closes the NICE-TO-HAVE decision and avoids silently writing command values to disk.

### 8.4 `/clear`

Clears the current terminal display and preserves:

```text
connection state
output mode
in-memory history
current static registry
```

### 8.5 `/exit` and terminal keys

```text
/exit
    -> close transport
    -> normal process exit

Ctrl-D on an empty prompt
    -> equivalent to /exit

Ctrl-R
    -> reverse search over current in-memory history

Ctrl-C while editing
    -> cancel current input buffer
    -> keep REPL/session state
```

One command error never terminates the REPL.

---

## 9. Remote command grammar

Canonical grammar:

```text
<resource> <operation> [selector] [parameter=value ...]
```

Rules:

```text
resource
    singular lowercase token

operation
    lowercase token
    compound words kebab-case

selector
    the only optional positional token after operation
    required only by the CommandSpec
    at most one

parameters
    every remaining token contains one "="
    split at the first "="
    names are snake_case and operation-specific
    duplicate name is invalid
    order is non-semantic

--parameter / --parameter=value
    not accepted as a second grammar
```

The command is parsed and completely locally validated before selector requests begin.

### 9.1 Tokenization

Interactive input uses POSIX `shlex` tokenization.

Non-interactive mode receives shell-tokenized argv and does not run a second shell expansion or `shlex` pass.

Examples:

```text
object rename server01 canonical_name="server 01"

object create \
    template_id=infra.vm \
    properties='{"hostname":"vm01","cpu":4}'
```

Shell variables, globbing and command substitution—when used—are shell behavior before NETAUTO receives argv and are not CLI semantics.

---

## 10. Parameter value decoding

Every parameter has one type in the static registry.

### 10.1 Simple carriers

```text
positive integer
    -> [1-9][0-9]*

boolean
    -> true | false

closed enum
    -> exact API spelling

UUID/exact selector
    -> textual UUID

string
    -> decoded token text

nullable string
    -> null means JSON null
    -> a JSON-quoted string literal may express the literal string "null"

date/datetime/primitive lexical values
    -> passed as strings under the API contract
```

Boolean is never accepted as integer.

### 10.2 Structured JSON

Parameters declared as JSON object, array or general JSON value accept:

```text
parameter=<inline-json>
parameter=@path/to/file.json
```

The file is read once as UTF-8 relative to the process current working directory unless absolute. Directories, unreadable files, invalid UTF-8 and invalid JSON are local errors.

There is no stdin sentinel, YAML/TOML input or custom nested DSL.

Recommended shell-safe inline form:

```text
properties='{"hostname":"vm01"}'
operations='[{"op":"REMOVE","property":"comment"}]'
```

### 10.3 Omission versus null

Omitted CLI parameter means the HTTP field/query is omitted.

```text
parameter absent
    -> omission

parameter=null
    -> explicit null only for a registry field that permits null

explicit null on an omission-only field
    -> local invalid parameter
    -> no HTTP request
```

The CLI does not replace explicit null with a server default.

### 10.4 Complete arrays and candidates

For `properties`, `components`, `perspectives`, `endpoint_template_ids`, `resolutions` and `operations`, the supplied JSON value is complete caller intent.

The CLI does not merge repeated parameters or apply array-order mutation semantics where the API defines none.

---

## 11. Human selector system

### 11.1 Selector kinds

```text
DataType
    UUID or qualified name <namespace>.<name>

ObjectTemplate
    UUID or qualified name <namespace>.<name>

Object
    UUID or exact canonical_name convenience selector

RelationshipDefinition
    UUID only

Relationship
    UUID only

RelationshipResolution
    UUID only
```

A syntactically valid UUID always has exact-ID precedence over a human-name interpretation.

### 11.2 DataType/ObjectTemplate lookup

A qualified name is split at the final dot:

```text
namespace = every preceding segment
name      = final segment
```

Resolution uses the exact public list route with:

```text
namespace=<namespace>
name=<name>
limit=2
```

Outcomes:

```text
0 items
    -> cli_selector_not_found

1 item and next_cursor null
    -> resolved ID

>1 items or next_cursor non-null
    -> cli_selector_ambiguous
```

Multiple matches for a server-unique qualified name are treated as protocol/invariant failure, but the operator still receives the bounded ambiguity result.

### 11.3 Object lookup

A non-UUID Object selector uses:

```text
GET /api/v1/core/objects
    canonical_name=<input>
    limit=2
```

Outcomes are the same zero/one/many rules. Ambiguity requires an explicit UUID.

### 11.4 Nested selector fields

The same selector policy applies recursively to command parameters and JSON members declared by the registry:

```text
datatype_id
    -> DataType selector

template_id
parent_template_id
target_template_id
endpoint_template_ids[]
perspectives[].template_id
declaring-template convenience inputs where accepted
    -> ObjectTemplate selector

object_id
parent_object_id
child_object_id
from_object_id
to_object_id
destination_object_id
    -> Object selector

relationship_definition_id
relationship_id
resolution_id
    -> UUID-only exact selector
```

The CLI rewrites human values to the exact UUID fields expected by the HTTP request.

It does not change field names or send human names to UUID carriers.

### 11.5 Deterministic selector plan

Before the primary request:

```text
1. traverse selector-bearing fields in CommandSpec order
2. preserve JSON array order for discovery only
3. de-duplicate identical (selector-kind, input) pairs
4. resolve sequentially in first-occurrence order
5. rewrite the request candidate
```

There is one per-command memoization map and no cross-command selector cache. Mutable Object names are therefore never reused from a stale prior command.

Every lookup exchange is recorded.

### 11.6 Selector failures

Selector failures are CLI-local result categories:

```text
cli_selector_not_found
cli_selector_ambiguous
cli_selector_invalid
```

Details are bounded:

```text
selector_kind
input
up to two matched IDs for ambiguity
```

No primary mutation/read request is sent after selector failure.

An HTTP or transport failure during lookup retains its remote/transport classification.

---

## 12. Static command registry and complete API coverage

One immutable registry drives:

```text
parser
help
selector planning
HTTP request construction
expected success statuses
response validation
FORMATTED renderer selection
coverage verification
```

A command key is:

```text
(resource, operation)
```

and is unique.

The registry has exactly:

```text
datatype                 14
object-template          16
object                   13
relationship-definition  14
relationship              5
lifecycle-event           1
                         ---
total                    63
```

`*` below means required. `?` means optional. Selector resolution follows §11.

| Resource | Operation | HTTP | Selector | Parameters | Result |
|---|---|---|---|---|---|
| `datatype` | `create` | `POST /api/v1/core/datatypes` | — | namespace*, name*, base_type*, description?, constraints? | created aggregate |
| `datatype` | `create-next` | `POST /api/v1/core/datatypes/{datatype_id}/create-next` | DataType | source_version* | exact version |
| `datatype` | `revise` | `POST /api/v1/core/datatypes/{datatype_id}/versions/{version}/revise` | DataType | version*, expected_revision*, constraints* | exact version |
| `datatype` | `publish` | `POST /api/v1/core/datatypes/{datatype_id}/versions/{version}/publish` | DataType | version*, expected_revision* | exact version |
| `datatype` | `set-default` | `POST /api/v1/core/datatypes/{datatype_id}/set-default` | DataType | version* | stable resource |
| `datatype` | `clear-default` | `POST /api/v1/core/datatypes/{datatype_id}/clear-default` | DataType | — | stable resource |
| `datatype` | `deprecate` | `POST /api/v1/core/datatypes/{datatype_id}/versions/{version}/deprecate` | DataType | version* | exact version |
| `datatype` | `delete-draft` | `DELETE /api/v1/core/datatypes/{datatype_id}/versions/{version}` | DataType | version*, expected_revision* | no content |
| `datatype` | `delete` | `DELETE /api/v1/core/datatypes/{datatype_id}` | DataType | — | no content |
| `datatype` | `set-description` | `POST /api/v1/core/datatypes/{datatype_id}/set-description` | DataType | description* (nullable) | stable resource |
| `datatype` | `list` | `GET /api/v1/core/datatypes` | — | namespace?, name?, cursor?, limit? | page |
| `datatype` | `get` | `GET /api/v1/core/datatypes/{datatype_id}` | DataType | — | stable resource |
| `datatype` | `list-versions` | `GET /api/v1/core/datatypes/{datatype_id}/versions` | DataType | status?, cursor?, limit? | page |
| `datatype` | `get-version` | `GET /api/v1/core/datatypes/{datatype_id}/versions/{version}` | DataType | version* | exact version |
| `object-template` | `create` | `POST /api/v1/core/object-templates` | — | namespace*, name*, abstract*, description?, parent_template_id?, parent_version?, properties?, components? | created aggregate |
| `object-template` | `create-next` | `POST /api/v1/core/object-templates/{template_id}/create-next` | ObjectTemplate | source_version* | exact version |
| `object-template` | `revise` | `POST /api/v1/core/object-templates/{template_id}/versions/{version}/revise` | ObjectTemplate | version*, expected_revision*, parent_version?, properties*, components* | exact version |
| `object-template` | `publish` | `POST /api/v1/core/object-templates/{template_id}/versions/{version}/publish` | ObjectTemplate | version*, expected_revision* | exact version |
| `object-template` | `set-default` | `POST /api/v1/core/object-templates/{template_id}/set-default` | ObjectTemplate | version* | stable resource |
| `object-template` | `clear-default` | `POST /api/v1/core/object-templates/{template_id}/clear-default` | ObjectTemplate | — | stable resource |
| `object-template` | `deprecate` | `POST /api/v1/core/object-templates/{template_id}/versions/{version}/deprecate` | ObjectTemplate | version* | exact version |
| `object-template` | `delete-draft` | `DELETE /api/v1/core/object-templates/{template_id}/versions/{version}` | ObjectTemplate | version*, expected_revision* | no content |
| `object-template` | `delete` | `DELETE /api/v1/core/object-templates/{template_id}` | ObjectTemplate | — | no content |
| `object-template` | `set-description` | `POST /api/v1/core/object-templates/{template_id}/set-description` | ObjectTemplate | description* (nullable) | stable resource |
| `object-template` | `list` | `GET /api/v1/core/object-templates` | — | namespace?, name?, abstract?, parent_template_id?, cursor?, limit? | page |
| `object-template` | `get` | `GET /api/v1/core/object-templates/{template_id}` | ObjectTemplate | — | stable resource |
| `object-template` | `list-versions` | `GET /api/v1/core/object-templates/{template_id}/versions` | ObjectTemplate | status?, cursor?, limit? | page |
| `object-template` | `get-version` | `GET /api/v1/core/object-templates/{template_id}/versions/{version}` | ObjectTemplate | version* | exact version |
| `object-template` | `get-effective-schema` | `GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema` | ObjectTemplate | version* | projection |
| `object-template` | `list-relationship-capabilities` | `GET /api/v1/core/object-templates/{template_id}/relationship-capabilities` | ObjectTemplate | name?, cursor?, limit? | page |
| `object` | `create` | `POST /api/v1/core/objects` | — | template_id*, template_version?, canonical_name?, properties? | resource |
| `object` | `rename` | `POST /api/v1/core/objects/{object_id}/rename` | Object | canonical_name* | resource |
| `object` | `data-change` | `POST /api/v1/core/objects/{object_id}/data-change` | Object | operations* | resource |
| `object` | `schema-change` | `POST /api/v1/core/objects/{object_id}/schema-change` | Object | target_version* | resource |
| `object` | `attach` | `POST /api/v1/core/objects/{parent_object_id}/attach` | Object | slot_name*, child_object_id* | projection |
| `object` | `detach` | `POST /api/v1/core/objects/{parent_object_id}/detach` | Object | slot_name*, child_object_id* | no content |
| `object` | `delete` | `DELETE /api/v1/core/objects/{object_id}` | Object | — | no content |
| `object` | `list` | `GET /api/v1/core/objects` | — | template_id?, template_version?, canonical_name?, cursor?, limit? | page |
| `object` | `get` | `GET /api/v1/core/objects/{object_id}` | Object | — | resource |
| `object` | `list-components` | `GET /api/v1/core/objects/{object_id}/components` | Object | slot_name?, cursor?, limit? | page |
| `object` | `get-owner` | `GET /api/v1/core/objects/{object_id}/owner` | Object | — | nullable projection |
| `object` | `list-relationships` | `GET /api/v1/core/objects/{object_id}/relationships` | Object | relationship_definition_id?, name?, cursor?, limit? | page |
| `object` | `list-lifecycle-events` | `GET /api/v1/core/objects/{object_id}/lifecycle-events` | Object | kind?, destination_object_id?, relationship_id?, relationship_definition_id?, relationship_name?, occurred_from?, occurred_to?, cursor?, limit? | page |
| `relationship-definition` | `create` | `POST /api/v1/core/relationship-definitions` | — | symmetric*, perspectives? / endpoint_template_ids? + name?, properties? | created aggregate |
| `relationship-definition` | `rename` | `POST /api/v1/core/relationship-definitions/{relationship_definition_id}/rename` | RelationshipDefinition | resolutions? / name? (shape-dependent) | stable resource |
| `relationship-definition` | `create-next` | `POST /api/v1/core/relationship-definitions/{relationship_definition_id}/create-next` | RelationshipDefinition | source_version* | exact version |
| `relationship-definition` | `set-default` | `POST /api/v1/core/relationship-definitions/{relationship_definition_id}/set-default` | RelationshipDefinition | version* | stable resource |
| `relationship-definition` | `clear-default` | `POST /api/v1/core/relationship-definitions/{relationship_definition_id}/clear-default` | RelationshipDefinition | — | stable resource |
| `relationship-definition` | `revise` | `POST /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/revise` | RelationshipDefinition | version*, expected_revision*, properties* | exact version |
| `relationship-definition` | `publish` | `POST /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/publish` | RelationshipDefinition | version*, expected_revision* | exact version |
| `relationship-definition` | `deprecate` | `POST /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/deprecate` | RelationshipDefinition | version* | exact version |
| `relationship-definition` | `delete-draft` | `DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}` | RelationshipDefinition | version*, expected_revision* | no content |
| `relationship-definition` | `delete` | `DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}` | RelationshipDefinition | — | no content |
| `relationship-definition` | `list` | `GET /api/v1/core/relationship-definitions` | — | cursor?, limit? | page |
| `relationship-definition` | `get` | `GET /api/v1/core/relationship-definitions/{relationship_definition_id}` | RelationshipDefinition | — | stable resource |
| `relationship-definition` | `list-versions` | `GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions` | RelationshipDefinition | status?, cursor?, limit? | page |
| `relationship-definition` | `get-version` | `GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}` | RelationshipDefinition | version* | exact version |
| `relationship` | `create` | `POST /api/v1/core/relationships` | — | resolution_id*, from_object_id*, to_object_id*, relationship_definition_version?, properties? | resource |
| `relationship` | `data-change` | `POST /api/v1/core/relationships/{relationship_id}/data-change` | Relationship | operations* | resource |
| `relationship` | `schema-change` | `POST /api/v1/core/relationships/{relationship_id}/schema-change` | Relationship | target_version* | resource |
| `relationship` | `delete` | `DELETE /api/v1/core/relationships/{relationship_id}` | Relationship | — | no content |
| `relationship` | `get` | `GET /api/v1/core/relationships/{relationship_id}` | Relationship | — | resource |
| `lifecycle-event` | `list` | `GET /api/v1/core/lifecycle-events` | — | kind?, object_id?, destination_object_id?, relationship_id?, relationship_definition_id?, relationship_name?, occurred_from?, occurred_to?, cursor?, limit? | page |

The registry count and exact `(method, path)` set must equal the canonical 63-operation inventory in `api.md`. No operation alias counts as coverage and no business-style Health command is added.

---

## 13. Structured request specifics

The command registry mirrors the exact API field names.

### 13.1 DataType

```text
constraints
    -> JSON object

description
    -> nullable string

base_type
    -> exact PrimitiveType identifier
```

`create`, `revise`, defaults, lifecycle and generation-token semantics are not reinterpreted.

### 13.2 ObjectTemplate

`properties` is a JSON array of exact property declarations. Human `datatype_id` values are recursively resolved.

`components` is a JSON array of exact component declarations. Human `target_template_id` values are recursively resolved.

`parent_template_id` accepts ObjectTemplate selector. `parent_version` omission retains the API's default-resolution meaning where valid.

`revise` requires both:

```text
properties
components
```

including explicit empty arrays.

### 13.3 Object

```text
properties
    -> JSON object

operations
    -> JSON array of SET/REMOVE variants
```

`attach` and `detach` use the primary positional Object selector as parent and resolve `child_object_id` under the Object selector policy.

### 13.4 RelationshipDefinition

CREATE uses exact discriminated shapes:

```text
symmetric=false
    perspectives=<two-item JSON array>
    properties?=<JSON array>

symmetric=true
    endpoint_template_ids=<two-item JSON array>
    name=<identifier>
    properties?=<JSON array>
```

RENAME uses:

```text
non-symmetric
    resolutions=<complete two-item JSON array>

symmetric
    name=<identifier>
```

The CLI may locally validate mutually exclusive shape fields, but it does not fetch the current Definition merely to choose a variant. The operator supplies one valid shape; server semantic validation remains final.

RDV `properties` declarations recursively resolve DataType selectors.

### 13.5 Factual Relationship

CREATE uses UUID-only `resolution_id`, Object selectors for endpoints, optional exact version and complete JSON property object.

DATA_CHANGE uses one JSON operation array. SCHEMA_CHANGE uses one positive exact target version.

The CLI never accepts endpoint tuples as a selector for an existing Relationship.

### 13.6 Lifecycle filters

`kind` uses the exact API vocabulary.

Object-like filter fields may use Object selectors. Relationship/Definition identities remain UUID-only.

Datetime strings are passed under the canonical API lexical contract without client timezone inference.

---

## 14. HTTP execution pipeline

A remote command executes:

```text
1. parse/token validation
2. typed parameter decoding
3. deterministic selector plan
4. selector GET exchanges
5. request candidate validation
6. primary HTTP exchange
7. expected-status and response-contract validation
8. JSON result or optional FORMATTED enrichment
9. final render
```

### 14.1 No mandatory Health preflight

Remote REPL commands use the currently connected client directly.

Non-interactive commands invoke their requested operation directly.

Neither performs an implicit `GET /health/core`.

### 14.2 Expected success

CommandSpec defines exact success status:

```text
GET/normal mutation
    -> 200

create
    -> 201

bodyless delete/detach
    -> 204
```

A `204` response must have no body. `200`/`201` success must have valid JSON matching the operation's transport model.

### 14.3 Remote business error

A non-success response matching the canonical business error body is returned as:

```text
source      = remote
code        = server code
message     = server message
details     = server bounded details
http_status = actual status
```

The CLI does not remap it to a local business code.

### 14.4 Protocol failure

Examples:

```text
unexpected success status
success body missing or malformed
204 with a body
business error status with invalid error DTO
unexpected redirect
invalid JSON/content contract
```

produce:

```text
code = cli_protocol_error
```

They are not reclassified as domain failure.

---

## 15. JSON output contract

JSON mode emits exactly one top-level JSON object.

### 15.1 Top-level shape

```json
{
  "status": "ok",
  "command": {
    "resource": "datatype",
    "operation": "get",
    "selector": "core.string",
    "parameters": {}
  },
  "exchanges": [],
  "result": {},
  "error": null
}
```

Exact fields:

```text
status
    ok | error

command
    null only when process/line parsing failed before a command key existed
    otherwise original parsed resource/operation/selector/parameter intent

exchanges
    ordered list of every attempted HTTP exchange

result
    primary successful HTTP body
    null for successful 204/local bodyless command or any error

error
    null on success
    structured error on failure
```

### 15.2 Exchange shape

```json
{
  "request": {
    "method": "GET",
    "url": "https://host/api/v1/core/datatypes",
    "query": {
      "namespace": ["core"],
      "name": ["string"],
      "limit": ["2"]
    },
    "headers": {
      "accept": ["application/json"],
      "user-agent": ["netauto/<release-version>"]
    },
    "body": null
  },
  "response": {
    "status_code": 200,
    "headers": {
      "content-type": ["application/json"]
    },
    "body_format": "json",
    "body": {}
  },
  "elapsed_ms": 4
}
```

Rules:

```text
method
    uppercase

url
    normalized absolute URL without duplicated query object

query
    lower-case names
    values are ordered arrays of exact sent strings

headers
    lower-case names
    ordered arrays of values
    request headers are captured after request construction
    response headers are those received

body
    actual logical JSON request value or null

response
    null when no HTTP response was received

body_format
    json | text | none

elapsed_ms
    non-negative integer from monotonic timing
```

A transport-failed attempted request remains one exchange with `response = null`; the top-level error contains the controlled transport category.

### 15.3 Error shape

```json
{
  "source": "selector",
  "code": "cli_selector_ambiguous",
  "message": "The Object selector is ambiguous.",
  "details": {},
  "http_status": null
}
```

`source` is exactly:

```text
local
selector
transport
remote
protocol
```

For local commands the `command` value uses:

```text
resource = "local"
operation = command name without the leading slash
selector/parameters = the submitted local arguments
```

Raw Python/HTTPX exception text is not required by the JSON contract.

### 15.4 Trace transparency

Every selector lookup and primary/enrichment exchange that actually occurs is included once and in execution order.

Bodies and received headers included in this explicit operator-selected trace are not field-redacted. This is not operational logging.

The CLI nevertheless emits no native credentials, rejects URL userinfo, sends no auth/cookie state and never includes private TLS key material.

### 15.5 Interactive versus non-interactive JSON

Interactive JSON mode uses the same schema for local and remote commands. Local commands have an empty exchange list.

Non-interactive stdout contains exactly this object followed by a newline and no surrounding prose.

---

## 16. FORMATTED output contract

FORMATTED exists only in the interactive REPL.

Rules:

```text
plain deterministic UTF-8 text
no color or terminal style carries semantic meaning
exact IDs remain visible even when names are resolved
no silent truncation of values
pages show next_cursor when non-null
errors show source/code/message/status and bounded details
no Python stack trace
```

### 16.1 Mutations

A mutation displays only the requested operation's direct response:

```text
HTTP status
Location when present
returned identifiers/projection
or bodyless success target
```

It performs no hidden post-mutation GET.

### 16.2 Lists

List/page commands render the primary page only.

They do not perform one enrichment request per item. This prevents an unbounded N+1 client path.

The renderer includes:

```text
canonical page items
item exact IDs
next_cursor or explicit end-of-page indication
```

### 16.3 Bounded single-resource enrichment

The following FORMATTED reads have required client-side enrichment:

```text
datatype get-version
    -> stable DataType GET for qualified name

object-template get
    -> stable parent lineage chain

object-template get-version
    -> exact parent-version chain
    -> owning/parent/declaring templates as qualified names
    -> property DataTypes as qualified names
    -> component target templates as qualified names

object-template get-effective-schema
    -> owning and declaring templates
    -> property DataTypes
    -> component target templates

object get
    -> stable ObjectTemplate qualified name

object get-owner
    -> parent Object canonical name when non-null
    -> slot declaring ObjectTemplate qualified name

relationship-definition get
    -> Resolution endpoint templates as qualified names

relationship-definition get-version
    -> property DataTypes as qualified names

relationship get
    -> distinct endpoint Object canonical names
```

Resolution rules:

```text
all enrichment uses public GET routes
identical IDs are memoized per command
lineage traversal stops at root
cycle, missing resource or invalid response is protocol/corruption failure
no partial formatted result is emitted
```

No list command, lifecycle page or mutation performs these per-item enrichments.

### 16.4 JSON mode does not enrich for presentation

Interactive JSON and non-interactive commands execute:

```text
selector lookups
+
primary operation
```

They do not execute FORMATTED-only enrichment. Their trace therefore contains all and only the requests needed by that mode.

---

## 17. Local and remote failure taxonomy

### 17.1 Local codes

The finite CLI-local catalog includes:

```text
cli_invalid_invocation
cli_invalid_command
cli_missing_selector
cli_unexpected_selector
cli_missing_parameter
cli_unexpected_parameter
cli_duplicate_parameter
cli_invalid_parameter
cli_json_error
cli_file_error
cli_not_connected
cli_internal_error
```

### 17.2 Selector codes

```text
cli_selector_invalid
cli_selector_not_found
cli_selector_ambiguous
```

### 17.3 Transport/protocol codes

```text
cli_transport_error
cli_protocol_error
```

Remote server error codes remain the server's exact 23-code catalog and are not prefixed or altered.

### 17.4 Connection-state consequences

```text
local/selector error
    -> no state change

remote business error
    -> preserve CONNECTED

business protocol error
    -> preserve CONNECTED

transport error
    -> DISCONNECTED

/connect or /status non-ready/protocol/HTTP error
    -> DISCONNECTED
```

### 17.5 REPL lifetime

All command failures render one result and return to the prompt.

An unexpected CLI programming defect is caught only at the outer command-loop boundary, rendered as controlled `cli_internal_error`, and the process may terminate only when safe session continuation cannot be guaranteed. This code is not a server business code.

---

## 18. Non-interactive process contract

For:

```text
netauto -n ...
```

```text
success
    -> stdout one JSON result
    -> exit 0

any command failure
    -> stdout one JSON error result
    -> exit 1
```

Stderr is empty for normal local, selector, remote, transport and protocol command outcomes.

Stderr is reserved for a failure outside the structured command-result boundary, such as inability to initialize stdout encoding or an unrecoverable bootstrap defect. The process still attempts a structured stdout result whenever possible.

No prompt, confirmation or retry is permitted.

---

## 19. Same-release compatibility and versioning

The CLI and server ship in the same versioned `netauto` wheel.

```text
CLI release X + server release X
    -> supported and verified

CLI release X + server release Y
    -> no M2 guarantee
```

The CLI sends its release version only as ordinary `User-Agent` metadata. There is no:

```text
version-negotiation endpoint
minimum/maximum server check
automatic mismatch refusal
cross-release compatibility matrix
```

Same-release response validation failure is `cli_protocol_error` and is a blocking implementation/integration defect.

---

## 20. Security and data-handling boundary

The CLI owns no credential storage and no secret profile.

```text
no endpoint persistence
no output-mode persistence
no command-history persistence
no auth token
no client certificate
no insecure TLS bypass
```

File-backed JSON is read only for the current command and is not copied to a CLI cache.

Explicit JSON trace may contain business payload values and is operator-visible output. The operator owns stdout redirection and file permissions.

Formatted output and local errors do not expose stack traces or raw transport exceptions.

---

## 21. Verification realization

Primary bundles:

```text
M2-VER-25
    interactive state machine

M2-VER-26
    interactive connection behavior

M2-VER-27
    non-interactive process contract

M2-VER-28
    operation coverage and authority boundary
```

Supporting bundles:

```text
M2-VER-23
    exact Health consumption

M2-VER-24
    wheel entrypoint and same release

M2-VER-29
    CLI invocation on installed Linux baseline

M2-VER-30
    TLS/trust boundary
```

### 21.1 Pure/application CLI tests

Cover:

```text
registry count and uniqueness
all parameter parsers
omission versus null
inline/file JSON
selector traversal/de-duplication
state-machine transitions
connection-state error policy
JSON trace serialization
formatted no-partial behavior
help generated from registry
in-memory history semantics
```

### 21.2 HTTP adapter tests

Using HTTPX controlled transport/ASGI integration:

```text
selector zero/one/many
all selector request shapes
expected status/body validation
business error preservation
transport/protocol distinction
no redirect follow
no cookie persistence
no Health preflight for remote/-n commands
/connect and /status exact Health behavior
all actual exchanges captured once and ordered
```

### 21.3 Exact 63-operation coverage

A machine-checkable registry compares:

```text
API_EXPECTED_OPERATIONS
    exact 63 (method, path-template) entries

CLI_REMOTE_OPERATIONS
    exact 63 CommandSpec entries
```

Required assertions:

```text
sets equal
command keys unique
no extra business-style Health command
every spec has parameter schema, expected status and response validator
every help entry derives from the same spec
```

### 21.4 Import/boundary tests

Static dependency checks prove that modules under `netauto.cli` do not import:

```text
netauto.application service implementations
netauto.persistence
SQLAlchemy
Psycopg
Alembic
FastAPI route functions
```

Importing neutral transport-only DTOs is permitted.

### 21.5 Terminal/process tests

Linux PTY/process evidence covers:

```text
initial prompt/state
Ctrl-R
Ctrl-D
Ctrl-C input cancellation
REPL continuation after errors
/clear state preservation
stdout/stderr/exit behavior
no persistent history file
```

### 21.6 Negative-surface checks

Prove absence of:

```text
default endpoint
named profile
credential store
--insecure
generic --header
dynamic OpenAPI command generation
direct DB/service execution
hidden mutation enrichment
mandatory Health preflight in -n
cross-release negotiation
persistent command history
```

---

## 22. Cross-owner consistency

### 22.1 API

The registry maps exactly the API owner’s 63 operations and exact parameter names. It adds no route, lookup API, error code or identity.

### 22.2 Health

`/connect` and `/status` require the exact ready `200` Health result. The CLI does not reinterpret Health timeout, query or startup behavior.

### 22.3 Runtime/deployment

`runtime-deployment.md` must confirm:

```text
netauto console entrypoint ships in the wheel
HTTPX and prompt_toolkit are runtime dependencies
one release version is used
CLI-only installation needs no database_url
installed invocation works outside a Git checkout
```

### 22.4 Verification

This design supplies exact hooks for `M2-VER-25 ... 28` and the 63-operation equality registry. Executed tests remain implementation/final evidence.

### 22.5 AS-IS

The CLI is additive. It does not change the delivered server API, application UoW, persistence or concurrency behavior.

---

## 23. Traceability and closure

Primary ownership:

```text
M2-OUT-12
    official complete HTTP CLI

M2-AC-25
    interactive state machine

M2-AC-26
    connection behavior

M2-AC-27
    non-interactive contract

M2-AC-28
    coverage and authority boundary

M2-VER-25 ... M2-VER-28
    complete evidence bundles
```

Supporting responsibility:

```text
M2-OUT-13 / M2-AC-24
    console entrypoint in the one wheel

M2-OUT-15 / M2-AC-30
    verified HTTPS and no credential/insecure mode
```

Architecture-draft closure:

```text
process modes and exact invocation                 CLOSED
endpoint and HTTP transport policy                 CLOSED
REPL state and local command semantics             CLOSED
grammar and typed input parsing                    CLOSED
human selectors and nested resolution              CLOSED
static 63-operation registry                       CLOSED
FORMATTED output/enrichment                        CLOSED
JSON trace schema                                  CLOSED
remote/local/transport/protocol errors              CLOSED
non-interactive stdout/stderr/exit                  CLOSED
history/help/terminal behavior                     CLOSED
same-release and security boundary                  CLOSED
verification hooks and negative surface            CLOSED
API/Health/runtime/verification/STACK-10 cross-check PASS
technology selection and project-wide authority      CLOSED
```

No CLI-specific architecture decision remains open in this owner.

This document remains `NOT FROZEN` until:

- final owner-by-owner traceability confirms every M2-OUT/M2-AC/M2-VER path;
- the complete M2 architecture set passes contract, AS-IS, authority, terminology and normative-hygiene consistency closure.

Executed CLI tests are implementation-slice and final-delivery evidence, not architecture-freeze prerequisites.
