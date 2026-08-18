# Codex implementation prompt — M2-S05

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Implement exactly:

```text
M2-S05 — Official CLI HTTP core and non-interactive mode
```

Work directly on branch:

```text
M2
```

The reviewer-owned starting baseline is:

```text
bd342146679e405365ab93e4a60ca85b60834161
docs(m2): accept S04 and open S05
```

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    reviewer-owned COMPLETED
M2-S04    reviewer-owned COMPLETED
M2-S05    READY
M2-S06    BLOCKED
```

Deliver the complete vertically coherent S05 capability:

```text
neutral shared HTTP wire DTO package
HTTPX runtime dependency and official console entrypoint
HTTP-only CLI core model
exact immutable 63-operation static registry
strict remote-command grammar and typed values
inline and file-backed JSON input
endpoint-root normalization and secure transport policy
deterministic top-level and nested selector resolution
same-release response and business-error validation
transparent ordered HTTP exchange trace
exact non-interactive stdout / stderr / exit contract
bounded installed/console-entrypoint supporting evidence
M2-VER-27 primary evidence
supporting M2-VER-24 / M2-VER-28 / M2-VER-30 evidence paths
```

Do not start `M2-S06`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not add or use GitHub Actions, encoded patches, workflow-dispatched implementation, or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before editing, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Delivered AS-IS authorities
docs/architecture/README.md
docs/architecture/api.md
docs/architecture/verification.md

# Active M2 authorities
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Ratified technology
docs/general/technology_baseline.md
    STACK-01
    STACK-03
    STACK-07
    STACK-08
    STACK-09
    STACK-10

# Active execution aid
docs/milestones/M2/wip/M2-S05-codex-prompt.md
```

The following WIP documents may be inspected only as historical discovery/cross-check material and never as authority:

```text
docs/milestones/M2/wip/netauto-cli.md
docs/milestones/M2/wip/cli-architecture-cross-check.md
docs/milestones/M2/wip/cli-stack-10-proposal.md
```

`architecture/cli.md`, the ratified `STACK-10`, `steps.md` and `status.md` supersede them wherever wording differs.

Confirm from the repository that:

```text
checked-out branch                    M2
origin/M2 ancestry                    includes bd342146...
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S04                                reviewer-owned COMPLETED
M2-S05                                READY or IN PROGRESS
M2-S06                                BLOCKED
relevant architecture reopen          none
STACK-10                              RATIFIED
```

Inspect the current implementation and tests, including at least:

```text
pyproject.toml
uv.lock
src/netauto/__init__.py
src/netauto/entrypoints/http.py
src/netauto/entrypoints/api/common.py
src/netauto/entrypoints/api/errors.py
src/netauto/entrypoints/api/health.py
src/netauto/entrypoints/api/datatypes.py
src/netauto/entrypoints/api/objecttemplates.py
src/netauto/entrypoints/api/objects.py
src/netauto/entrypoints/api/relationshipdefinitions.py
src/netauto/entrypoints/api/relationships.py
src/netauto/failures.py

# Expected new implementation roots
src/netauto/transport/http/
src/netauto/cli/

tests/test_object_scope.py
tests/test_m2_traceability.py
tests/test_health_api.py
tests/test_http_composition.py
all current API modules and route-inventory tests
all complete regression targets
```

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` remains mandatory for the full repository gate and preserved PostgreSQL claims. Do not provision a database, invent credentials, use Docker/Testcontainers, substitute SQLite or fall back to localhost.

S05 CLI correctness itself is public-HTTP client correctness. Do not use `TEST_DATABASE_URL`, application services or persistence as a substitute for HTTP evidence.

If repository state or a frozen authority conflicts with this task, stop only the affected point and report it. Do not modify frozen architecture to fit convenient code.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
neutral HTTP request/response/error/Health DTO package
server route adaptation to the neutral DTO authority
HTTPX promotion to runtime dependency
netauto console entrypoint
non-interactive `-n` process parsing
static 63-operation registry
registry-owned parameter/help/selector/dispatch/validation metadata
strict typed parameter decoding
omission versus explicit null
inline JSON and @file.json
endpoint-root validation
HTTPX AsyncClient lifecycle and policy
deterministic selector plan and per-command memoization
primary HTTP dispatch
success/error/protocol validation
transparent exchange capture
canonical JSON process result
stdout/stderr/exit behavior
M2-VER-27 and bounded supporting bundle evidence
```

## 2.2 Out of scope

Do not implement or expose:

```text
M2-S06 interactive REPL
PromptSession or prompt_async()
/connect
/disconnect
/status
/output
/help runtime command
/history
/clear
/exit
Ctrl-R / Ctrl-C / Ctrl-D behavior
FORMATTED runtime output or enrichment execution
persistent or in-memory REPL history
prompt_toolkit dependency promotion

M2-S07 release-version change
runtime.pylock.toml
full installed Linux operating procedure
server start/stop/restart procedure
release-directory layout
full packaging acceptance

M2-S08 integrated final traceability closure
M2-S09 final acceptance or delivery

new server route, DTO field or business behavior
new Health route or business-style Health command
schema, migration, table, constraint or index change
application-service or persistence execution from CLI
new auth, credential, header or profile model
--insecure / verify=false
custom per-command CA or client certificate
generic --header or Authorization parameter
redirect following
cookie persistence
retry or backoff
OpenAPI-generated command registry
plugin command framework
Typer, Click, cmd2 or Rich authority
```

The no-argument interactive invocation is S06-owned. During S05, only the exact `-n` invocation is supported. Every other process shape must fail locally through the bounded structured invocation-error boundary; it must not start a partial prompt, invent local commands or silently choose an endpoint.

Preserve exactly:

```text
15 authoritative tables
one Alembic base / one head
root revision 0001_m2_kernel
compare_metadata == []
41 mutations + 22 reads = 63 business HTTP operations
1 GET /health/core operational operation
64 total public server HTTP operations
83 concurrency scenarios
21 safety predicates
three advisory gates
four row-lock modes
completed S04 Settings/startup/Health behavior
```

---

# 3. Dependency, entrypoint and release boundary

## 3.1 HTTPX runtime promotion

Move the already-ratified compatible dependency:

```text
httpx>=0.28,<1
```

from development-only dependency ownership into `[project].dependencies`.

It must not remain duplicated in the dev group merely to make tests pass.

Update `uv.lock` through the normal locked workflow. Preserve the already reviewed exact HTTPX resolution unless the lock tool proves an unavoidable compatible metadata change. Do not opportunistically upgrade unrelated packages.

## 3.2 Console entrypoint

Expose exactly:

```toml
[project.scripts]
netauto = "netauto.cli.main:main"
```

The console function is synchronous process bootstrapping only and runs one native-asyncio coroutine.

The S05 supported process form is exactly:

```text
netauto -n <endpoint-root> <resource> <operation>
    [selector] [parameter=value ...]
```

Do not add:

```text
--non-interactive alias
-h / --help as a second public command authority
--version
--endpoint
profile/config options
server/migration wrapper commands
```

If stdlib `argparse` is used, disable automatic options that would create an unauthorized public process grammar.

## 3.3 Deferred release work

Do not change:

```text
project version 0.1.0
release metadata strategy
embedded runtime lock
wheel filename/version policy
```

Those are S07-owned.

Do not add `prompt-toolkit` in S05. Its ratification is already authoritative, but dependency promotion and first runtime use belong to S06 with the REPL.

Allowed dependency/configuration diff for this slice is limited to:

```text
httpx promoted to runtime dependency
netauto console script added
corresponding uv.lock root-project metadata update
```

No other dependency or toolchain change is authorized.

---

# 4. Neutral shared HTTP wire DTO authority

Create one neutral package conceptually under:

```text
src/netauto/transport/__init__.py
src/netauto/transport/http/__init__.py
src/netauto/transport/http/common.py
src/netauto/transport/http/errors.py
src/netauto/transport/http/health.py
src/netauto/transport/http/datatypes.py
src/netauto/transport/http/objecttemplates.py
src/netauto/transport/http/objects.py
src/netauto/transport/http/relationshipdefinitions.py
src/netauto/transport/http/relationships.py
src/netauto/transport/http/lifecycle.py
```

Local module decomposition may differ, but there must be one implementation authority for every public HTTP wire model consumed by server adapters and CLI response/request validation.

Move/share the complete public wire model set:

```text
strict request-body base model
all business request DTOs
all success response DTOs
all page/summary/projection DTOs
complete lifecycle discriminated response models
canonical business-error DTO
Core Health component/result DTOs
```

The neutral package:

```text
may import stdlib, Pydantic and plain domain enums/value aliases where required
contains no FastAPI Request/Response/Depends/APIRouter object
contains no application service import
contains no persistence import
contains no SQLAlchemy, Psycopg or Alembic import
contains no route function
contains no HTTP dispatch
owns wire shape only, not semantics
```

The server route modules must import the neutral classes and preserve the existing explicit domain/application-to-wire mapping.

It is acceptable for route modules to re-export imported DTO names for source-test compatibility, but they must not define competing Pydantic wire classes.

Keep FastAPI-only helpers in the adapter layer, including:

```text
Request access
Response/status/header mutation
NoBody dependency
query/path extraction
service lookup from app.state
route registration
```

The refactor must preserve exactly:

```text
all paths and methods
request omission/null behavior
strict extra-field rejection
status codes
Location headers
success bodies
business-error envelopes
Health bodies
OpenAPI schemas and discriminators
```

Add permanent static/import evidence proving:

```text
neutral package has no forbidden imports
CLI imports no FastAPI route module
server route modules use neutral DTO identities
no duplicate public DTO authority remains
CLI-only import does not load Settings, application services or persistence
```

Do not move domain or application semantics into Pydantic validators merely because the models are shared.

---

# 5. CLI package and immutable model

Create the S05 CLI core conceptually under:

```text
src/netauto/cli/__init__.py
src/netauto/cli/main.py
src/netauto/cli/model.py
src/netauto/cli/registry.py
src/netauto/cli/parser.py
src/netauto/cli/selectors.py
src/netauto/cli/transport.py
src/netauto/cli/protocol.py
src/netauto/cli/execution.py
src/netauto/cli/render.py
```

Do not create `repl.py` or import `prompt_toolkit` in this slice.

Local names may vary, but ownership must remain singular.

## 5.1 Immutable values

Provide immutable, typed values for at least:

```text
CommandKey
ParsedCommand
ParameterSpec
CommandSpec
SelectorKind
ParameterKind / value codec
Request plan
HTTP request trace
HTTP response trace
HTTP exchange trace
CLI error source
CLI error value
CLI result value
expected response validator
formatted renderer selector metadata
```

The model must not expose HTTPX request/response objects as command/result authority.

Use ordinary Python immutable dataclasses/enums/mappings or an equally strict local realization.

## 5.2 Finite CLI-local catalog

The local catalog is exactly:

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

Selector codes are exactly:

```text
cli_selector_invalid
cli_selector_not_found
cli_selector_ambiguous
```

Transport/protocol codes are exactly:

```text
cli_transport_error
cli_protocol_error
```

Error sources are exactly:

```text
local
selector
transport
remote
protocol
```

Remote business errors preserve the server code, message, details and actual HTTP status without prefixing or semantic remapping.

Messages for CLI-owned errors must be deterministic, bounded and free of raw Python/HTTPX/OS exception text.

Do not catch `BaseException`. Cancellation, `KeyboardInterrupt` and `SystemExit` must not be converted into an ordinary remote result.

The outer non-interactive command boundary may convert an unexpected ordinary `Exception` into bounded `cli_internal_error` when a structured stdout result can still be emitted safely.

---

# 6. Exact immutable 63-operation registry

Create one static immutable registry. It is the sole CLI authority for:

```text
command grammar
parameter order and requiredness
parameter type and nullability
path/query/body placement
selector kind and traversal
HTTP method and path template
expected success status
Location/body expectations
response DTO validator
help metadata
FORMATTED renderer selector metadata
coverage evidence
```

The registry must not be generated from OpenAPI at runtime or test time.

Command keys are unique `(resource, operation)` pairs.

Exact family census:

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

Exact operation keys:

```text
datatype
    create
    create-next
    revise
    publish
    set-default
    clear-default
    deprecate
    delete-draft
    delete
    set-description
    list
    get
    list-versions
    get-version

object-template
    create
    create-next
    revise
    publish
    set-default
    clear-default
    deprecate
    delete-draft
    delete
    set-description
    list
    get
    list-versions
    get-version
    get-effective-schema
    list-relationship-capabilities

object
    create
    rename
    data-change
    schema-change
    attach
    detach
    delete
    list
    get
    list-components
    get-owner
    list-relationships
    list-lifecycle-events

relationship-definition
    create
    rename
    create-next
    set-default
    clear-default
    revise
    publish
    deprecate
    delete-draft
    delete
    list
    get
    list-versions
    get-version

relationship
    create
    data-change
    schema-change
    delete
    get

lifecycle-event
    list
```

Encode the exact method/path/selector/parameter/result table from `architecture/cli.md` §12. Do not infer field names from convenience or current Python parameter names.

Every spec must define:

```text
exact method
exact path template
whether a top-level selector is absent/required
ordered ParameterSpec set
required versus optional
nullable versus omission-only
simple/JSON/enum carrier
path/query/body destination
nested selector traversal
exact expected success status
body required/forbidden
neutral response DTO or bodyless validator
Location requirement where owned by the API contract
stable help text/examples
FORMATTED renderer key for S06
```

Success statuses are exact:

```text
ordinary GET / mutation        200
create/create-next              201
bodyless delete/detach          204
```

Do not accept another 2xx status as equivalent.

For `204`:

```text
response body must be absent
result = null
```

For `200`/`201`:

```text
valid JSON body is mandatory
body must validate against the operation's neutral response DTO
```

Where the API contract owns `Location`, same-release validation must reject an absent or malformed Location as protocol failure.

Add a machine-checkable equality assertion:

```text
actual server business OpenAPI operations
    == static CLI remote method/path-template set
    == exact 63
```

Health remains outside the registry:

```text
GET /health/core
    not a business command
    not counted among 63
```

S05 does not yet implement `/connect` or `/status`.

---

# 7. Non-interactive process and command parsing

## 7.1 Exact process form

Accept only:

```text
netauto -n <endpoint-root> <resource> <operation>
    [selector] [parameter=value ...]
```

Rules:

```text
-n is exact and required in S05
endpoint root is required
resource and operation are required
no local /command is accepted
no prompt is opened
no missing value is requested interactively
no confirmation is requested
no second shell/shlex pass is applied to argv
```

Every other process shape yields one structured `cli_invalid_invocation` result and exit `1` when stdout is usable.

A process parse failure before a command key exists uses:

```text
command = null
exchanges = []
```

## 7.2 Remote grammar

After endpoint-root:

```text
<resource> <operation> [selector] [parameter=value ...]
```

Enforce:

```text
resource singular lowercase
operation lowercase / kebab-case
only one optional positional selector after operation
every remaining token contains one '='
split parameter at first '='
parameter name snake_case and operation-specific
duplicate parameter invalid
parameter order non-semantic
no --parameter grammar
```

Parse and locally validate the complete command shape before any HTTP exchange.

## 7.3 Command echo

The JSON result `command` value retains the operator's decoded logical intent before selector rewriting:

```text
resource
operation
original selector or null
decoded parameter values with human selectors preserved
```

Do not replace the command echo with server-resolved UUID values. Actual rewritten UUID carriers appear only in the traced HTTP request.

---

# 8. Typed parameter decoding

Every parameter type comes only from the static registry.

## 8.1 Simple carriers

Implement exactly:

```text
positive integer
    regex [1-9][0-9]*
    bool forbidden

boolean
    exact true | false

closed enum
    exact API spelling

UUID/exact selector
    textual UUID

string
    decoded argv token

nullable string
    token null -> JSON null
    JSON-quoted string literal can express literal "null"

date/datetime/primitive lexical values
    remain strings under the API contract
```

No generic scalar coercion is allowed.

## 8.2 Structured JSON

Registry fields declared as JSON object, array or general JSON accept:

```text
parameter=<inline-json>
parameter=@path/to/file.json
```

File rules:

```text
read exactly once
UTF-8 only
relative to process current working directory unless absolute
regular readable file only
no directory
no stdin sentinel
no YAML/TOML
invalid UTF-8 -> cli_file_error
unreadable/missing -> cli_file_error
invalid JSON -> cli_json_error
```

Do not include raw OS/decoder exception text in the result.

## 8.3 Omission versus null

Preserve exactly:

```text
parameter absent
    -> omit from HTTP carrier

parameter=null
    -> explicit JSON null only when ParameterSpec permits null

null on omission-only/non-null field
    -> local cli_invalid_parameter
    -> no HTTP exchange
```

Do not replace explicit null with a default.

## 8.4 Complete structured intent

The following are complete caller-provided arrays/candidates:

```text
properties
components
perspectives
endpoint_template_ids
resolutions
operations
```

Do not merge repeated values, infer omitted declarations or create another nested DSL.

## 8.5 Shape-dependent RelationshipDefinition commands

Locally validate only the frozen transport shape:

```text
CREATE symmetric=false
    perspectives required
    endpoint_template_ids/name forbidden as alternate shape

CREATE symmetric=true
    endpoint_template_ids and name required
    perspectives forbidden as alternate shape

RENAME non-symmetric shape
    resolutions supplied

RENAME symmetric shape
    name supplied
```

Do not fetch the current Definition merely to choose a variant. The operator supplies a valid shape and the server remains semantic authority.

---

# 9. Endpoint-root and HTTPX transport

## 9.1 Endpoint-root validation

Accept only an endpoint root satisfying all:

```text
absolute URL
scheme exactly http or https after case normalization
host present
optional explicit port
path empty or '/'
no username/password
no query
no fragment
```

Normalize one trailing root slash away.

Do not accept a custom base path such as `/api/v1/core`.

Do not echo credential-bearing rejected userinfo into bounded local diagnostics.

## 9.2 One scoped client

One non-interactive command creates one scoped `httpx.AsyncClient`, reuses it for all selector and primary requests, then closes it.

Do not construct one client per lookup.

Production policy is exact:

```text
verify                     enabled/default
hostname verification      enabled
follow_redirects           false
connect timeout            5.0 s
pool timeout               5.0 s
read timeout               30.0 s
write timeout              30.0 s
automatic retry            none
```

The administered standard proxy/trust environment may be honored. It does not create a NETAUTO profile.

## 9.3 Headers

Explicitly send:

```text
Accept: application/json
User-Agent: netauto/<installed-distribution-version>
Content-Type: application/json only when a JSON body exists
```

Derive release version from installed distribution metadata. Do not introduce a second handwritten `__version__` authority and do not change the project release in S05.

Send no:

```text
Authorization
Cookie
native credential header
```

## 9.4 No cookie persistence

A selector or primary response may contain `Set-Cookie`, but no later request may contain a derived `Cookie` header.

One command may reuse a connection pool; it must not reuse server cookie state.

Add a regression in which a selector lookup returns `Set-Cookie` and the primary request is observed without `Cookie`.

## 9.5 Redirects and attempts

A redirect is not followed. It is one actual exchange followed by `cli_protocol_error` unless it is a canonical server business error, which a redirect is not.

Each planned request is attempted once. No HTTPX transport retries, redirect retries or command retries are allowed.

Add controlled transport evidence that counts exactly one attempt on connect/read failure.

## 9.6 TLS evidence

Provide deterministic local HTTPS evidence without an external network dependency:

```text
trusted test CA + matching hostname
    -> success

untrusted CA
    -> cli_transport_error

hostname mismatch
    -> cli_transport_error
```

Use the administered trust mechanism, such as a test-controlled standard CA environment, rather than adding a public per-command CA option.

Permanently prove absence of:

```text
--insecure
verify=false
skip-verify
custom CA command option
client certificate option
URL userinfo
```

Do not add a new runtime/dev dependency solely to create the TLS fixture unless it is separately ratified. A local deterministic stdlib/fixture realization is preferred.

---

# 10. Deterministic selector system

## 10.1 Top-level selector kinds

Implement exactly:

```text
DataType
    UUID or qualified name namespace.name

ObjectTemplate
    UUID or qualified name namespace.name

Object
    UUID or exact canonical_name

RelationshipDefinition
    UUID only

Relationship
    UUID only

RelationshipResolution
    UUID only
```

A syntactically valid UUID always wins over human-name interpretation.

## 10.2 DataType/ObjectTemplate qualified lookup

Split a qualified name at the final dot:

```text
namespace = all preceding segments
name = final segment
```

Both parts must be non-empty.

Use the exact public list route with:

```text
namespace=<namespace>
name=<name>
limit=2
```

Outcomes:

```text
0 items
    -> cli_selector_not_found

1 item and next_cursor is null
    -> resolved UUID

more than one item or next_cursor non-null
    -> cli_selector_ambiguous
```

## 10.3 Object lookup

For a non-UUID Object selector use:

```text
GET /api/v1/core/objects
canonical_name=<input>
limit=2
```

Use the same zero/one/many rules.

## 10.4 UUID-only selectors

For RelationshipDefinition, Relationship and Resolution:

```text
valid UUID
    -> use directly

non-UUID
    -> cli_selector_invalid
    -> no lookup
```

Do not invent endpoint tuples, names or topology identities for these resources.

## 10.5 Nested selector fields

Apply the same selector policy recursively to fields declared by CommandSpec:

```text
DataType selector
datatype_id

ObjectTemplate selector
template_id
parent_template_id
target_template_id
endpoint_template_ids[]
perspectives[].template_id
declaring-template convenience fields when the API accepts them

Object selector
object_id
parent_object_id
child_object_id
from_object_id
to_object_id
destination_object_id

UUID-only
relationship_definition_id
relationship_id
resolution_id
```

Rewrite only the actual HTTP request candidate. Preserve field names and emit UUID values in UUID carriers.

## 10.6 Deterministic plan

Before the primary request:

```text
1. traverse top-level and nested selector-bearing fields in CommandSpec order
2. preserve JSON array order for discovery
3. deduplicate identical (selector-kind, input) pairs
4. resolve sequentially in first-occurrence order
5. rewrite the request candidate
```

Use exactly one per-command memoization map.

No selector result may survive into another command.

Add evidence for:

```text
top-level UUID precedence
qualified DataType zero/one/many
qualified ObjectTemplate zero/one/many
Object canonical_name zero/one/many
nested arrays and objects
first-occurrence ordering
deduplication
no cross-command cache
up to two matched IDs in ambiguity details
no primary request after selector failure
```

Every lookup actually attempted appears once and in order in the exchange trace.

A lookup HTTP business error, transport failure or protocol failure retains that classification; do not relabel it as selector-not-found.

---

# 11. HTTP request construction and protocol validation

## 11.1 Exact request construction

Use only CommandSpec metadata to construct:

```text
path parameters
ordered multi-value query parameters
optional JSON body
```

Omitted values are not sent.

Use the exact API field names. Do not rename human-friendly parameters on the wire.

After selector rewriting, validate the request body against the neutral request DTO before sending it.

No application command or service object is constructed.

## 11.2 Success response

For exact expected success:

```text
200/201
    JSON required
    neutral response DTO validation required

204
    no body allowed
```

A malformed same-release success is `cli_protocol_error`.

Do not return a partial successfully decoded body.

## 11.3 Canonical remote business error

For non-success responses:

```text
body must be valid canonical business-error DTO
server code/message/details preserved
actual HTTP status preserved
result = null
source = remote
```

Validate the finite same-release code/status contract where the shared wire catalog provides it. A code/status mismatch is protocol failure, not a remapped remote business error.

## 11.4 Protocol error

At minimum classify as `cli_protocol_error`:

```text
unexpected success status
missing/malformed success JSON
success DTO mismatch
204 with body
missing required Location
redirect response
non-success invalid business-error DTO
business code/status mismatch
invalid JSON/content contract
```

If an HTTP response exists, retain it in the exchange trace.

Do not expose raw Pydantic/HTTPX exception text.

## 11.5 HTTP-only boundary

Production modules under `netauto.cli` must not import or invoke:

```text
netauto.application service implementations
netauto.persistence
SQLAlchemy
Psycopg
Alembic
FastAPI route functions
RuntimeContext
Settings
UnitOfWorkFactory
```

Neutral transport DTO imports are permitted.

Add AST/import-closure tests and negative runtime controls proving that `netauto -n`:

```text
works without NETAUTO_DATABASE_URL
creates no database engine
performs no Alembic operation
uses only observed HTTP requests
```

---

# 12. Transparent exchange trace

Every actual request attempt creates exactly one exchange entry in execution order.

## 12.1 Top-level result

Emit exactly one object with fields:

```text
status      ok | error
command     parsed command or null
exchanges   ordered list
result      successful primary body or null
error       structured error or null
```

On success:

```text
status = ok
error = null
```

On failure:

```text
status = error
result = null
```

## 12.2 Request trace

Capture after HTTP request construction:

```text
method
    uppercase

url
    normalized absolute URL

query
    lower-case names
    ordered arrays of exact sent string values

headers
    lower-case names
    ordered arrays of actual sent values

body
    actual logical JSON value or null
```

The trace must prove absence of authorization/cookie state.

## 12.3 Response trace

When a response exists:

```text
status_code
headers as lower-case -> ordered value arrays
body_format = json | text | none
body = decoded JSON, text or null
```

When transport fails before a response:

```text
response = null
```

Always include:

```text
elapsed_ms
    non-negative integer
    monotonic elapsed time
```

## 12.4 Exact transparency

Trace all and only requests that actually occur:

```text
selector lookups
primary operation
```

S05 JSON mode performs no FORMATTED enrichment and no Health preflight.

Do not include planned-but-unattempted requests.

Do not duplicate exchanges at transport and execution layers.

Bodies and received headers in the explicit operator-selected trace are not field-redacted, but the CLI itself must create no credential/auth/cookie state.

Add tests comparing the recorded exchange list with a controlled server/transport request log for:

```text
direct command
selector + primary command
deduplicated nested selectors
remote business error
redirect/protocol error
transport failure
```

---

# 13. Exact non-interactive stdout, stderr and exit

For every supported `netauto -n` outcome:

```text
stdout
    exactly one JSON object
    followed by exactly one newline
    no prose, prompt or traceback

success
    exit 0

local / selector / remote / transport / protocol / bounded internal failure
    exit 1

stderr
    empty for every normal structured command outcome
```

Stderr is reserved only for an unrecoverable process defect outside the structured result boundary, such as inability to initialize/write stdout.

Use deterministic standard-library JSON serialization. UUIDs, enums, dates and other wire values must serialize to their canonical JSON carriers.

Required process tests include:

```text
successful selectorless read
successful UUID-selected read or bodyless command
local invalid invocation
unknown command
missing/duplicate/invalid parameter
file/JSON failure
selector not found
selector ambiguous
remote business error
transport error
protocol error
inner unexpected ordinary Exception -> cli_internal_error
```

For local syntax/decoding failures:

```text
exchanges = []
```

No prompt, confirmation, retry or interactive read from stdin is permitted.

---

# 14. Bounded S05 packaging and same-release support

S07 owns the final versioned wheel and Linux operating baseline. S05 nevertheless must provide bounded supporting evidence for the newly introduced console client.

At minimum prove:

```text
uv build includes netauto.cli and netauto.transport.http modules
wheel metadata contains exact netauto console entrypoint
CLI import comes from candidate wheel in the bounded installed test
CLI invocation requires no database_url
CLI invocation does not initialize server, engine or Alembic
same installed distribution version is used in User-Agent
non-interactive process contract works against a controlled local HTTP endpoint
```

Do not generate or claim:

```text
embedded runtime.pylock.toml
final release version
complete S07 wheel closure
manual Linux production procedure
server process operating acceptance
```

Installed/subprocess evidence may use an isolated temporary environment and the already locked local dependency set, but it must not import `netauto` from the source checkout.

---

# 15. Traceability and evidence state

Extend the singular registry in `tests/test_m2_traceability.py`. Do not create a second traceability authority.

## 15.1 Primary S05 bundle

Add exact real targets for:

```text
M2-VER-27 — Non-interactive CLI contract
```

The candidate may report `M2-VER-27 PASS` only when every mandatory S05 target has executed successfully.

## 15.2 Supporting bundle paths

Add explicit supporting target ownership for:

```text
M2-VER-24
    console entrypoint and bounded wheel import/invocation only

M2-VER-28
    static 63-operation equality
    selector behavior
    HTTP-only/import boundary
    transparent trace

M2-VER-30
    endpoint userinfo rejection
    HTTPS trust/hostname behavior
    no insecure/auth/cookie surface
```

Use conceptually distinct registries such as:

```text
S05_PRIMARY_BUNDLE_TARGETS
S05_SUPPORTING_BUNDLE_TARGETS
```

The static evidence state vocabulary remains:

```text
DESIGNED
IMPLEMENTED
```

Concrete targets make a bundle `IMPLEMENTED`; executed candidate PASS belongs in status/evidence, not in the static registry.

Be honest about primary ownership:

```text
M2-VER-27
    S05 primary and eligible for complete candidate PASS

M2-VER-24
    S07 primary; S05 provides only bounded support

M2-VER-28
    S06 primary; S05 provides registry/selector/boundary support

M2-VER-30
    S07 primary; S05 provides transport-security support
```

Do not claim complete PASS for the three supporting bundles in S05.

Keep:

```text
M2-VER-25 / 26
    DESIGNED until S06

M2-VER-29
    DESIGNED until S07

M2-VER-31 / 32
    DESIGNED until S08
```

## 15.3 Exact inventories

Permanent traceability must prove:

```text
16 outcomes unchanged
32 acceptance criteria unchanged
32 evidence bundle IDs unchanged
41 mutation operations unchanged
22 business reads unchanged
63 server business operations unchanged
1 Health operation unchanged
64 total server HTTP operations unchanged
63 CLI remote CommandSpec entries
83 scenarios unchanged
21 predicates unchanged
```

The CLI registry excludes Health and interactive local commands.

---

# 16. Mandatory evidence

Use the smallest focused tests first, then every complete gate.

## 16.1 Neutral DTO refactor

Prove:

```text
server OpenAPI paths/methods/schemas unchanged
request strictness unchanged
response DTOs unchanged
error/Health DTOs unchanged
route modules use neutral model identities
no duplicate DTO class authority
neutral package forbidden-import closure
```

Run all affected server API tests.

## 16.2 Registry and parser T0/T1/T10

Cover:

```text
63 exact command keys
family counts 14/16/13/14/5/1
unique keys
exact method/path set equality
all specs have parameters/status/validator/help/renderer metadata
process -n exact grammar
unknown/invalid command
selector presence/absence
required/optional/duplicate/unexpected parameters
all simple carriers
omission versus null
inline JSON
file JSON read-once behavior
RelationshipDefinition discriminated shapes
```

Use table/property tests where they materially strengthen finite codec behavior, without weakening exact examples.

## 16.3 Selector T1/T8

Cover every selector family and nested traversal:

```text
UUID precedence
qualified DataType
qualified ObjectTemplate
Object canonical name
UUID-only Definition/Relationship/Resolution
zero / one / many
next_cursor ambiguity
deduplication
first-occurrence order
nested arrays/objects
no cross-command cache
no primary request after failure
```

## 16.4 Transport/protocol T8

Cover:

```text
endpoint valid/invalid matrix
exact timeout policy
one scoped client per command
client reused across lookups/primary
verified HTTPS success
untrusted CA failure
hostname mismatch failure
redirect not followed
Set-Cookie not persisted
no auth/cookie request state
one attempt/no retry
exact required headers
200/201/204 validation
Location validation
remote error preservation
protocol failure families
transport failure response=null
exchange count/order/body/query/header capture
```

## 16.5 Non-interactive subprocess T8/T9

Run the real console entrypoint in subprocess form for:

```text
success -> stdout JSON / stderr empty / exit 0
local error -> stdout JSON / stderr empty / exit 1
selector exchange sequence
remote error
transport error
protocol error
no Health preflight
no prompt/confirmation/stdin read
```

At least one bounded candidate-wheel invocation must import the installed candidate rather than the source tree.

## 16.6 Boundary/negative surface T10

Prove absence of:

```text
application/persistence/DB/Alembic execution imports
Settings/database_url requirement
server/route function import
second command registry
OpenAPI command generation
Health business command
prompt_toolkit / REPL/local commands
FORMATTED execution
--insecure / generic headers / credentials
redirect following
cookie persistence
retry/backoff
profile/default endpoint
persistent history
S06/S07 surface
```

---

# 17. Mandatory commands and final gate

Run and report exact commands, counts and durations.

## 17.1 Dependency/build/static quality

```text
uv lock
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Use `uv lock` only for the authorized dependency/entrypoint metadata change. Do not upgrade unrelated packages.

## 17.2 Focused S05 evidence

Run exact collected targets for:

```text
neutral DTO identity and OpenAPI preservation
registry 63/63 equality
parser and parameter codecs
selector families and nested resolution
endpoint/transport/security policy
protocol and trace
non-interactive subprocess contract
bounded wheel/entrypoint support
M2-VER-27
supporting M2-VER-24/28/30 targets
CLI negative surface
```

## 17.3 Cross-boundary regressions

At minimum run:

```text
all business API tests affected by DTO movement
Health API and S04 runtime regressions
route/error/inventory closure
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py
tests/test_schema_metadata.py
tests/test_migrations.py
uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

The full repository suite must use the externally supplied `TEST_DATABASE_URL` and include all PostgreSQL tests.

No normative test may be skipped, xfailed or hidden by generic rerun.

Report:

```text
CPython version
PostgreSQL server version
uv version
collection count
focused DTO/registry/parser/selector/transport/process counts
M2-VER-27 count
supporting bundle counts
PostgreSQL count
non-PostgreSQL count
full-suite count and duration
skip / xfail / rerun census
warning census
supported-path 40P01 / unexpected 40001 census
```

S05 adds no concurrency scenario, but all accepted S03 scenarios must remain green.

## 17.4 Unchanged-boundary verification

Explicitly verify and report:

```text
15 authoritative tables
one Alembic base / one head
0001_m2_kernel unchanged
compare_metadata == []
no schema/migration/index diff
only authorized pyproject/uv.lock changes
project version unchanged
41 mutations + 22 server business reads unchanged
1 Health route unchanged
64 total server HTTP operations unchanged
63 CLI remote specs exact
83 scenarios and 21 predicates unchanged
no S06/S07 surface
obsolete Actions/payload material absent
```

---

# 18. Implementation and publication discipline

Work directly on `M2`.

Use normal source edits, tests, commits and push. Do not create a PR.

A reasonable publication sequence is:

```text
implementation commit(s)
    -> CLI/DTO/dependency implementation and permanent tests

evidence/status commit
    -> candidate evidence and state only after all mandatory gates pass

optional provenance commit
    -> only when needed to record the exact final remote-tested commit
```

Do not delete this prompt while the slice remains open.

Do not edit frozen contract/architecture/steps to fit implementation.

## 18.1 Status transitions

At implementation start, `status.md` may become:

```text
M2-S05 — IN PROGRESS
```

Only after every mandatory gate passes may Codex publish:

```text
M2-S05 — CANDIDATE READY FOR REVIEW
```

Codex must never assign:

```text
M2-S05 — COMPLETED
M2-S06 — READY or IN PROGRESS
```

Those remain reviewer-owned.

If any mandatory environment, target or requirement is unavailable:

```text
leave M2-S05 IN PROGRESS or BLOCKED as appropriate
record the exact blocker
publish only explicitly partial work
never claim candidate-ready
```

## 18.2 Final remote verification

After pushing the candidate:

```text
verify local HEAD == origin/M2 == remote M2
verify ahead/behind 0/0
verify working tree clean
rerun the complete mandatory suite on the exact final remote commit
```

If the post-push rerun changes evidence or reveals a failure, publish the corrected state and repeat. Do not hand off an unverified provenance commit.

---

# 19. Required handoff

The final handoff must report:

```text
cycle / slice / branch
starting baseline
implementation commit(s)
evidence/status commit
final remote HEAD
local/origin/remote synchronization
working-tree state
```

Summarize implementation by boundary:

```text
neutral DTO refactor
runtime dependency and console entrypoint
CLI model/registry/parser
selector system
HTTPX transport/security
protocol/trace
non-interactive process
traceability
```

Report exact facts:

```text
63 / 63 CLI remote operations
family census 14 / 16 / 13 / 14 / 5 / 1
M2-VER-27 status and target count
supporting M2-VER-24/28/30 targets without overclaim
stdout/stderr/exit variants tested
selector families tested
TLS trusted/untrusted/mismatch results
redirect/cookie/retry results
all dependency/lock changes
all commands, counts and durations
environment versions
skip/xfail/rerun/warnings
40P01/40001 census
```

Explicitly state:

```text
M2-S05 is CANDIDATE READY FOR REVIEW, not COMPLETED
M2-S06 remains BLOCKED
no interactive REPL or FORMATTED runtime was introduced
no PR or GitHub Action was created
```

If a requirement was not executed, a finding remains or the full externally supplied PostgreSQL suite did not pass, do not use candidate-ready wording.
