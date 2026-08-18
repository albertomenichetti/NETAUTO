# Codex implementation prompt — M2-S04

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Implement exactly:

```text
M2-S04 — Runtime settings, startup revision guard and Core Health
```

Work directly on branch:

```text
M2
```

The reviewer-owned starting baseline is:

```text
2b89f4ce79272554721ff694dd8ae8e32e7fab25
docs(m2): accept S03 and open S04
```

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    reviewer-owned COMPLETED
M2-S04    READY
M2-S05    BLOCKED
```

Implement the complete vertically coherent S04 capability:

```text
exact immutable runtime Settings and source precedence
one worker-owned AsyncEngine / bounded pool
unique installed Alembic-head discovery
same-engine exact current-revision inspection
fixed ten-second pre-serving startup guard
engine disposal on every failed/cancelled startup path
Core Health application model and service
same-engine PostgreSQL SELECT 1 probe
strict GET /health/core wire contract
fixed two-second whole-probe deadline
M2-VER-22 and M2-VER-23 traceability and executed evidence
```

Do not start `M2-S05`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not add or use GitHub Actions, encoded patches, workflow-dispatched implementation, or artifact-mediated source publication.

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
docs/architecture/persistence.md
docs/architecture/api.md
docs/architecture/verification.md

# Active M2 authorities
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Active execution aid
docs/milestones/M2/wip/M2-S04-codex-prompt.md
```

Confirm from the repository that:

```text
checked-out branch                    M2
origin/M2 ancestry                    includes 2b89f4ce...
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S03                                COMPLETED
M2-S04                                READY or IN PROGRESS
M2-S05                                BLOCKED
relevant architecture reopen          none
TEST_DATABASE_URL                     externally supplied and usable
```

Inspect the current implementation and tests, including at least:

```text
src/netauto/settings.py
src/netauto/persistence/engine.py
src/netauto/persistence/uow.py
src/netauto/entrypoints/http.py
src/netauto/entrypoints/api/common.py
src/netauto/entrypoints/api/errors.py
src/netauto/migrations/env.py
src/netauto/migrations/versions/0001_m2_durable_kernel.py

tests/test_settings.py
tests/test_http_composition.py
tests/test_object_scope.py
tests/test_migrations.py
tests/test_schema_metadata.py
tests/test_m2_traceability.py
all current business API and full-regression targets
```

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` is mandatory for all T2/T5/runtime claims. Do not provision a database, invent credentials, use Docker/Testcontainers, substitute SQLite, fall back to localhost, or silently use `NETAUTO_DATABASE_URL` as the automated-test authority. Tests may inject the externally supplied test URL explicitly into runtime `Settings`.

If repository state or a frozen authority conflicts with this task, stop only the affected point and report it. Do not modify frozen architecture to fit the current code.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
Settings expansion and validation
NETAUTO_SECRETS_DIR bootstrap composition
exact engine/pool keyword mapping
one-engine RuntimeContext composition
installed Alembic graph discovery
same-engine actual revision inspection
startup revision guard and safe bootstrap failures
FastAPI lifespan ordering and cleanup
Core Health application/service/probe/HTTP route
M2-VER-22 and M2-VER-23 evidence
public route inventory: 63 business + 1 operational
S04 traceability and negative-surface checks
```

## 2.2 Out of scope

Do not add or implement:

```text
M2-S05 or M2-S06 CLI commands, parser, transport or REPL
console entrypoint changes
HTTPX/prompt-toolkit runtime dependency moves
release-version change
runtime.pylock.toml generation or release-lock workflow
full S07 wheel/Linux installation procedure
systemd, Docker, Kubernetes or process-manager assets
server-side TLS, authentication, authorization or observability redesign
host, port or worker fields in NETAUTO Settings
Health authentication, second listener or dynamic health registry
automatic migration, stamp, repair or schema introspection fallback
new business routes, DTOs, failures or semantics
new mutation, concurrency scenario, lock, gate or retry cause
schema, migration, index or durable revision changes
dependency or `uv.lock` changes
M1 bridge, backfill, stamp path or dual decoder
```

Preserve exactly:

```text
15 authoritative tables
one Alembic base / one head
root revision 0001_m2_kernel
compare_metadata == []
41 mutations + 22 reads = 63 business operations
83 concurrency scenarios
21 safety predicates
three advisory gates
four row-lock modes
```

S04 adds one operational HTTP route. The final HTTP inventory after this slice is:

```text
63 /api/v1/core business operations
1  GET /health/core operational operation
64 total public HTTP operations
```

Do not mix the Health route into the 63-command business/CLI registry.

No dependency, schema, migration, index, revision or `uv.lock` change is expected or authorized by this slice.

---

# 3. Existing implementation to evolve, not bypass

The current baseline already provides:

```text
Settings
    database_url
    log_level
    explicit init > environment > file-secret ordering
    no import-time singleton
    no dotenv source

RuntimeContext
    one lazy AsyncEngine
    one UnitOfWorkFactory

FastAPI composition
    explicit build_app(settings)
    no-argument create_app() factory
    process lifespan disposal
    business routers and canonical error handlers

installed migration graph
    src/netauto/migrations
    one root revision
```

Refactor this baseline into the frozen S04 realization. Do not create parallel settings classes, a second runtime context, a second engine factory, a Health-specific pool, a startup-only engine or a separate expected-revision constant.

The current `build_app(settings)` and `create_app()` factory boundary must remain side-effect-free with respect to network/database I/O. The first active checkout occurs inside lifespan startup through the schema guard.

---

# 4. Exact runtime Settings

## 4.1 Exact field inventory

The immutable `Settings` model owns exactly:

```text
database_url: str
log_level: CRITICAL | ERROR | WARNING | INFO | DEBUG
pool_size: int
max_overflow: int
pool_timeout: float
pool_recycle: int | null
pool_pre_ping: bool
```

Defaults and constraints are exactly:

```text
database_url
    required
    valid SQLAlchemy URL
    driver exactly postgresql+psycopg

log_level
    default INFO

pool_size
    default 10
    integer >= 1
    boolean forbidden

max_overflow
    default 20
    integer >= 0
    -1 / unlimited forbidden
    boolean forbidden

pool_timeout
    default 5.0 seconds
    finite numeric value > 0
    NaN and infinities forbidden
    boolean forbidden

pool_recycle
    default null
    when present, positive whole seconds
    zero, negative, fractional and boolean values forbidden

pool_pre_ping
    default false
    strict boolean after settings-source parsing
```

Environment names are exactly:

```text
NETAUTO_DATABASE_URL
NETAUTO_LOG_LEVEL
NETAUTO_POOL_SIZE
NETAUTO_MAX_OVERFLOW
NETAUTO_POOL_TIMEOUT
NETAUTO_POOL_RECYCLE
NETAUTO_POOL_PRE_PING
```

Do not add `NETAUTO_HOST`, `NETAUTO_PORT`, `NETAUTO_WORKERS`, database host fragments, profile names, generic config files, runtime reload or a mutable global singleton.

Importing `netauto.settings` must perform no environment/filesystem read and instantiate no settings object.

## 4.2 Secret-directory bootstrap selector

`NETAUTO_SECRETS_DIR` is a bootstrap-only source selector, not a `Settings` field.

The production composition root must:

```text
read NETAUTO_SECRETS_DIR once when loading Settings
if absent
    -> enable no implicit secret directory
if present
    -> require an absolute path
    -> require that it exists
    -> require a directory
    -> fail startup on any invalid explicit path
    -> pass it explicitly as the pydantic-settings secrets directory
```

The canonical file is:

```text
<NETAUTO_SECRETS_DIR>/NETAUTO_DATABASE_URL
```

A single final newline may be ignored by the file-secret source.

Exact precedence is:

```text
1. explicit constructor/test values
2. direct NETAUTO_* environment variables
3. files in explicit NETAUTO_SECRETS_DIR
4. safe code defaults
```

A valid direct `NETAUTO_DATABASE_URL` must override the file. An invalid explicitly selected secret directory must fail even if a direct database environment value is also available; do not silently ignore or fall back from an invalid bootstrap selector.

Do not enable dotenv or parent-directory discovery.

Provide one explicit composition helper, conceptually `load_settings()`, used by `create_app()`. Tests may continue to construct `Settings(...)` directly.

## 4.3 Safe handling

The database URL must never be emitted through:

```text
normal startup/shutdown logs
safe schema-guard exceptions
Health responses
OpenAPI examples
status/evidence text
command-line composition
```

Do not log parsed username, host, port, database name, query options or transport details.

---

# 5. One runtime AsyncEngine and bounded pool

Evolve `build_runtime_context` so it consumes the complete validated Settings value and maps exactly:

```python
create_async_engine(
    settings.database_url,
    isolation_level="READ COMMITTED",
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    pool_recycle=(-1 if settings.pool_recycle is None else settings.pool_recycle),
    pool_pre_ping=settings.pool_pre_ping,
)
```

Do not add a custom unbounded pool, `NullPool`, reserved Health connection or second runtime engine.

One `RuntimeContext` per worker owns exactly one process-lifetime engine. That same engine must back:

```text
business UnitOfWorkFactory
CoherentReadUnitOfWork through the same factory
startup current-revision inspection
PostgreSQLHealthProbe
```

The engine remains lazy. Constructing `Settings`, `RuntimeContext`, `FastAPI`, or OpenAPI performs no network checkout.

Add permanent evidence for:

```text
exact create_async_engine keyword values
pool_recycle null -> -1
realized pool capacity and finite boundaries
one object identity shared by UoW, coherent read, guard and Health
no second engine created during startup or a Health request
one independent engine per separately constructed worker/app lifespan
```

All constructed engines must be disposed on:

```text
normal lifespan shutdown
schema-guard mismatch
schema-guard unavailability
schema-guard timeout
invalid installed graph
Health/service composition failure after engine creation
cancelled startup after engine creation
any other composition failure after engine construction
```

Do not swallow cancellation while performing cleanup.

---

# 6. Installed Alembic graph and startup revision guard

Implement the bootstrap infrastructure conceptually under:

```text
src/netauto/runtime/__init__.py
src/netauto/runtime/schema_guard.py
```

Local decomposition may vary, but there must be one authority and no hard-coded expected revision.

## 6.1 Bounded bootstrap types and operations

Provide bounded infrastructure values conceptually equivalent to:

```text
MigrationGraphInvalid
SchemaGuardUnavailable
SchemaRevisionMismatch

discover_unique_shipped_head()
load_current_database_heads(engine)
require_exact_schema_revision(engine)

CORE_STARTUP_SCHEMA_GUARD_TIMEOUT_SECONDS = 10.0
```

These are bootstrap/infrastructure exceptions. They are not `ApplicationFailure` values and do not become HTTP error codes.

Safe exception/log messages may identify only bounded categories and expected/actual revision IDs/counts when readable. They must not include DSN, credentials, host, SQL, stack detail or raw driver text.

## 6.2 Unique installed graph discovery

Build an in-memory Alembic `Config` and set exactly:

```text
script_location = netauto:migrations
```

Load it through:

```text
ScriptDirectory.from_config(...)
```

Require:

```text
len(get_bases()) == 1
len(get_heads()) == 1
```

The unique `get_heads()` element is the expected revision.

The runtime expected head must not come from:

```text
migration filename parsing
0001_m2_kernel or another handwritten constant
package version
operator alembic.ini
environment variable
database state
application metadata
```

If a concrete filesystem path is ever necessary, use `importlib.resources.files()` and `as_file()` for the complete operation lifetime. Do not copy migration resources into an unmanaged persistent directory.

Add evidence for:

```text
actual installed graph -> one base and one head
zero base
multiple bases
zero head
multiple heads
unreadable/invalid graph
source checkout not required for graph discovery
```

Invalid graph composition rejects startup.

## 6.3 Same-engine current-head inspection

Use a borrowed connection from the runtime AsyncEngine and the Alembic `MigrationContext` adapter, conceptually:

```python
async with engine.connect() as connection:
    actual_heads = await connection.run_sync(
        lambda sync_connection:
            MigrationContext.configure(sync_connection).get_current_heads()
    )
```

The inspection:

```text
uses the same runtime engine/pool
performs no business UoW
performs no commit
accesses no application table
writes no alembic_version state
```

Normalize only for order. Startup is compatible exactly when the actual set is the singleton expected head.

Reject every other state:

```text
database unreachable or checkout/query failure
missing alembic_version table
base / no current row
older or different revision
newer revision
unknown revision
multiple current heads
indeterminate or malformed current-head result
```

No table/column/index introspection or `compare_metadata` may replace exact revision equality at runtime.

## 6.4 Whole-guard timeout

The fixed production boundary is:

```text
10.0 seconds
```

One native-asyncio outer deadline covers the complete guard:

```text
installed graph discovery
pool checkout
initial connection
revision query
run_sync adapter
connection cleanup
classification
```

Tests may inject or monkeypatch a smaller deadline seam, but the production constant is fixed and is not a setting.

Timeout raises one safe bounded bootstrap failure. No retry is allowed.

## 6.5 No migration or repair

The startup call graph must never:

```text
import/call alembic.command.upgrade
import/call alembic.command.stamp
write alembic_version
create/drop/alter application structures
invoke migration env.py
repair a mismatch
retry indefinitely
```

Add static/AST and runtime regressions against these paths. Do not weaken the existing “lifespan does not execute migrations” regression merely because the new guard now performs a real checkout; adapt it with valid injected/real guard prerequisites and retain the original assertion.

---

# 7. Exact ASGI composition and worker lifecycle

Preserve the public Uvicorn factory:

```text
netauto.entrypoints.http:create_app
```

`create_app()` loads Settings once through the explicit composition helper. `build_app(settings)` remains suitable for direct test injection and performs no network I/O.

Each FastAPI lifespan must execute semantically in this exact order:

```text
1. configure logging from settings.log_level
2. build one RuntimeContext from complete Settings
3. discover and validate the unique installed Alembic head
4. inspect current heads through runtime.engine
5. require exact singleton equality
6. compose PostgreSQLHealthProbe(runtime.engine)
7. compose CoreHealthService(probe)
8. publish runtime and Health service in application state
9. enter serving
10. on shutdown, await runtime.engine.dispose()
```

Do not publish a usable runtime/Health service before the guard succeeds.

If any step after engine construction fails or startup is cancelled:

```text
dispose the engine completely
re-raise the original safe bootstrap/cancellation outcome
never enter the lifespan yield/serving boundary
```

A failed worker serves neither `/api/v1/core` nor `/health/core`. Route registration/OpenAPI construction before lifespan is not serving; the lifespan must fail before the application can accept requests.

Every app/worker instance performs its own guard and owns its own engine. Do not add a process-global cached guard result, “first worker” flag, mutable runtime singleton or cross-worker in-memory authority.

After successful startup, a later database outage does not shut down or re-run the guard; the process remains an HTTP worker and Health returns its bounded 503 result.

Provide explicit local test seams through ordinary Python injection/monkeypatching. Do not add a DI/container framework.

---

# 8. Core Health application capability

Health is an operational application capability, not a domain aggregate. Add no module under `netauto.domain`.

Use the conceptual ownership:

```text
src/netauto/application/health.py
src/netauto/persistence/health.py
src/netauto/entrypoints/api/health.py
```

## 8.1 Application model

Implement exactly:

```text
HealthStatus
    ok
    error

ComponentHealth
    status
    message: optional safe string

CoreHealthResult
    app_status
    db_status
    execution_time_ms: non-negative integer
    derived is_ready convenience predicate

DatabaseHealthProbe protocol
DatabaseProbeUnavailable
DatabaseProbeTimedOut
CoreHealthService
```

For every valid M2 `CoreHealthService` result:

```text
app_status.status = ok
app_status.message = absent
```

No warning/degraded state, score, details map, plugin registry or arbitrary component collection is allowed.

## 8.2 Service pipeline and exact messages

The service owns:

```text
CORE_DATABASE_HEALTH_TIMEOUT_SECONDS = 2.0
```

It is fixed and not configurable.

One `check()` call must:

```text
capture monotonic start
establish app_status ok
execute exactly one probe attempt under one native asyncio timeout
classify success / expected unavailable / timeout
wait for probe cleanup/unwind
capture monotonic end
derive execution_time_ms
return one complete result
```

Exact DB results:

```text
success
    status  ok
    message absent

timeout, including pool timeout
    status  error
    message "database readiness check timed out"

expected connection/protocol/query unavailability
    status  error
    message "database readiness check failed"
```

Monotonic conversion is exactly:

```text
elapsed_ns = max(0, end_ns - start_ns)
execution_time_ms = elapsed_ns // 1_000_000
```

Zero is valid.

The service must not:

```text
retry
back off
cache
spawn background work
use a business UnitOfWork
query Alembic
repair/rebuild the engine
raise ApplicationFailure for an ordinary readiness result
catch BaseException
swallow cancellation
normalize an unexpected programming defect to 503
```

Catch only the two owned expected probe exceptions and the outer timeout. Unexpected failures propagate to the existing HTTP unexpected-failure boundary and become the canonical safe 500.

The monotonic clock/probe must be injectable ordinary Python seams for deterministic T1 evidence.

## 8.3 PostgreSQLHealthProbe

The adapter uses the exact same `AsyncEngine` object stored in RuntimeContext.

It executes exactly one active textual Core statement:

```sql
SELECT 1
```

Success requires an exact integer scalar `1`; do not accept an arbitrary truthy result.

The probe lifecycle is:

```text
engine.connect()
-> execute SELECT 1
-> consume scalar
-> exit connection context
```

It performs no explicit commit, business UoW, coherent-read UoW, AUTOCOMMIT, `SET TRANSACTION`, Alembic query or NETAUTO table access. Any implicit transaction is cleaned up by connection-context exit.

Translate only a finite explicit infrastructure family:

```text
SQLAlchemy pool TimeoutError
    -> DatabaseProbeTimedOut

expected SQLAlchemy/DBAPI connection, protocol or query failure
    -> DatabaseProbeUnavailable

unexpected scalar/result shape
    -> DatabaseProbeUnavailable
```

Do not catch generic `Exception` or `BaseException`. Preserve raw errors only as internal causes where useful; never copy raw text into application/public messages.

The two-second outer service deadline covers:

```text
pool wait
connect/checkout
pre-ping when configured
SELECT 1
result consumption
normal/cancelled connection cleanup
```

A cancelled/in-flight connection must be closed or invalidated through the SQLAlchemy async boundary before the check returns. Do not add a PostgreSQL `statement_timeout` authority.

## 8.4 Deterministic pool-starvation behavior

Add real-PostgreSQL evidence with an engine configured approximately as:

```text
pool_size = 1
max_overflow = 0
pool_timeout > 2.0
```

Hold its sole connection from a test controller, then execute Health through the same engine.

Prove:

```text
Health returns timeout status near the dedicated two-second boundary
it does not wait for the longer configured pool_timeout
the result body/message are exact
connection cleanup completes
release the held connection
a subsequent Health check succeeds
no engine/pool rebuild occurred
```

Use bounded tolerance for scheduler/cancellation cleanup overhead. Do not make a wall-clock sleep the scheduling authority; the held real pool connection is the deterministic boundary.

A test-only blocking probe may additionally prove the application timeout/cancellation seam.

---

# 9. Exact `/health/core` HTTP adapter

Register exactly one operational route:

```text
GET /health/core
```

Do not add `GET /health`, another Health route, a business-style Health route, metrics, liveness, startup, readiness aliases or a separate listener.

The route obtains the already-composed `CoreHealthService` from application state. It must not read Settings, build an engine, construct a probe/pool or run the startup guard per request.

## 9.1 Strict request

The operation accepts:

```text
no query parameters
no request body
```

Reuse the delivered strict helpers:

```text
validate_query(request, ())
NoBody
```

Unknown/repeated query parameters or any non-empty body, including `{}`, return:

```text
400 invalid_request
canonical bounded business error envelope
zero Health probe calls
```

They are not readiness 503 results.

## 9.2 Exact DTO

Component DTO:

```text
status: ok | error
message: optional string, omitted when absent
```

Core DTO:

```text
app_status
    component DTO

db_status
    component DTO

execution_time_ms
    integer >= 0
```

Never serialize `message: null`.

## 9.3 Status and headers

```text
result.is_ready true
    -> 200

result.is_ready false
    -> 503
    -> complete Core Health DTO, not an HTTPException detail envelope
```

Every valid 200 and 503 response includes exactly:

```text
Cache-Control: no-store
```

OpenAPI must declare the same Core Health DTO for both 200 and 503.

Unexpected service defects continue through the existing global handler:

```text
500
{"code":"internal_error", ...}
```

Do not misreport them as `db_status=error`.

Valid Health bodies/messages must never contain:

```text
database URL
credentials
username
host or port
SQL text
SQLSTATE
constraint/table/column names
raw SQLAlchemy/Psycopg text
stack trace
pool internals
```

Health performs no Alembic call, revision check or remediation after startup.

---

# 10. Traceability and exact inventories

Extend the singular machine-checkable M2 registry without creating a second authority.

Add exact target ownership for:

```text
M2-VER-22 — Exact startup revision gate
M2-VER-23 — Core readiness contract
```

Conceptually:

```text
S04_BUNDLE_TARGETS = {
    "M2-VER-22": ...,
    "M2-VER-23": ...,
}
```

Update `M2_EVIDENCE_TO_TARGETS` so only bundles owned through S04 are `IMPLEMENTED` with real non-empty targets.

Keep honest:

```text
M2-VER-01 ... M2-VER-23 owned by completed/current slices
    -> IMPLEMENTED with exact target sets

M2-VER-24 and later
    -> DESIGNED until their owning slices

M2-VER-31 / 32
    -> still S08-owned
```

Do not mark static bundle state `PASS`; executed PASS belongs in candidate evidence/status.

Add an exact operational-route delta:

```text
S04_PUBLIC_ROUTE_DELTA = {
    ("GET", "/health/core")
}
```

Permanent inventory tests must prove:

```text
41 business mutations
22 business reads
63 business operations
1 operational Health operation
64 total public HTTP operations
no GET /health aggregate
no extra route
```

Update existing route-closure tests by separating `/api/v1/core` operations from operational routes. Do not simply change the business-read count from 22 to 23.

Preserve exactly:

```text
16 M2 outcomes
32 acceptance criteria
32 evidence bundles
41 mutations
83 concurrency scenarios
21 predicates
all S00/S01/S02/S03 targets and recipe maps
```

Add static/AST negative evidence for:

```text
no hard-coded expected revision in runtime code
no alembic.command upgrade/stamp in startup call graph
no migration or schema DDL from Health
no second engine/Health pool
no Settings read inside Health route
no UnitOfWork use inside Health
no retry/cache/dynamic registry
no database URL logging/response mapping
no S05/CLI surface
```

---

# 11. Mandatory evidence

Use the smallest focused tests first, then every full S04 and regression gate.

## 11.1 Settings and engine T1/T2 evidence

Cover at minimum:

```text
exact seven-field inventory and defaults
all invalid finite boundaries
strict bool-versus-int behavior
canonical postgresql+psycopg URL only
constructor > env > explicit secret file > default precedence
NETAUTO_DATABASE_URL file and final-newline handling
invalid relative/missing/non-directory NETAUTO_SECRETS_DIR fails
invalid selector does not silently fall back to direct environment
no dotenv/implicit secret discovery
no import-time Settings instance/read
exact create_async_engine keyword mapping
lazy construction performs no network I/O
same engine identity for mutation/coherent UoW, guard and Health
separate app instances own separate engines
normal/failing/cancelled startup disposal
```

## 11.2 Startup-guard T2/T5 evidence

Against real PostgreSQL and controlled test seams, cover:

```text
installed graph has one base and one head
expected head discovered from ScriptDirectory
actual exact head -> lifespan enters
missing alembic_version table -> reject
base / empty version table -> reject
old/different revision -> reject
newer revision -> reject
unknown revision -> reject
multiple current heads -> reject
unreadable/query failure -> reject
unreachable database -> reject through deterministic injected infrastructure failure
zero/multiple installed bases/heads -> reject
whole-guard timeout -> reject
safe non-leaking diagnostics
no endpoint reaches serving on rejection
every separately built worker/app executes its own guard
no automatic upgrade/stamp/repair
no handwritten expected revision constant
```

Restore the externally supplied test database to the unique expected head after every destructive revision-state test. Do not leave `alembic_version` or application structures altered for subsequent tests.

## 11.3 Health T0/T1 evidence

Cover:

```text
exact status/result vocabulary
is_ready derivation
success
probe unavailable
owned probe timeout
two-second outer timeout
one call and no retry
exact controlled messages
unexpected defect propagation
cancellation propagation
cleanup completes before end-time measurement
negative elapsed floor
sub-millisecond zero
integer millisecond floor
```

## 11.4 Health real-PostgreSQL T2 evidence

Cover:

```text
same runtime engine identity
exact SELECT 1 only
exact integer scalar 1
no NETAUTO table or Alembic query
no explicit commit
connection returned cleanly after success
finite expected failure translation
pool-starvation two-second deadline while pool_timeout > 2
later recovery on the same engine
no dedicated Health engine/connection reserve
```

Use SQLAlchemy statement instrumentation where helpful, but real PostgreSQL is required for these claims.

## 11.5 HTTP/lifespan T4 evidence

Cover:

```text
GET /health/core only
healthy -> 200 exact DTO
unavailable -> 503 exact DTO
timeout -> 503 exact DTO
message omitted when absent
Cache-Control no-store on 200 and 503
unknown query -> 400 and zero probes
repeated query -> 400 and zero probes
non-empty body -> 400 and zero probes
unexpected service error -> safe 500, not 503
OpenAPI 200 and 503 share Core Health DTO
business inventory remains exactly 63
total public HTTP inventory becomes exactly 64
build_app/create_app/OpenAPI remain network-side-effect-free
failed guard prevents lifespan serving
successful startup composes runtime then Health
shutdown disposes the exact runtime engine
```

## 11.6 Bounded installed-wheel T9 evidence owned by S04

Build the candidate wheel and execute a bounded installed-package test outside the Git checkout that proves only S04-owned behavior:

```text
import installed netauto package, not the source tree
resolve netauto:migrations from the installed distribution
discover one shipped head without a source path
construct the installed server factory without network I/O
with a real head database, enter installed lifespan and obtain Health 200
with a guard failure, installed lifespan does not enter serving
```

A temporary isolated environment may reuse the already locked test dependencies through an explicit local mechanism, but it must install/import the candidate wheel and must not use an editable/source-path import.

Do not use this bounded evidence to claim or implement S07's full versioned release, embedded runtime lock, CLI packaging, Linux procedure or process-operation scope.

## 11.7 Preserved regressions

Re-run at minimum:

```text
all current settings and HTTP composition tests
all API inventory/scope tests
M1, S00 and complete M2 traceability
schema metadata and migration tests
complete deterministic PostgreSQL concurrency suite
all non-PostgreSQL regressions
full repository suite
```

No normative test may be skipped, xfailed or hidden by generic rerun. Timeout is a hang guard only.

---

# 12. Mandatory commands and gate

Run and report exact commands, counts and durations.

## 12.1 Build and static quality

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

## 12.2 Focused S04 evidence

Run the exact collected targets for:

```text
Settings/source precedence and pool mapping
schema-guard pure and real-PostgreSQL matrix
lifespan startup/failure/disposal
Health application service
Health real-PostgreSQL probe and pool starvation
Health HTTP/OpenAPI/strict-request contract
installed-wheel S04 smoke
M2-VER-22 and M2-VER-23 traceability
64-operation public inventory
negative startup/Health surface
```

## 12.3 Cross-boundary regressions

At minimum run:

```text
uv run pytest -q \
  tests/test_settings.py \
  tests/test_http_composition.py \
  tests/test_object_scope.py \
  tests/test_m2_traceability.py \
  <new S04 settings/guard/health/installed targets> -ra

uv run pytest -q \
  tests/test_schema_metadata.py \
  tests/test_migrations.py -ra

uv run pytest -q \
  tests/test_m1_traceability.py \
  tests/test_m2_s00_traceability.py \
  tests/test_m2_traceability.py -ra

uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

Adapt filenames only when the implementation places focused S04 tests elsewhere. Do not omit an obligation.

The complete suite must run with the externally supplied `TEST_DATABASE_URL` and include every PostgreSQL test. Report:

```text
CPython version
PostgreSQL server version
uv version
collection count
focused bundle counts
PostgreSQL count
non-PostgreSQL count
full-suite count and duration
skip / xfail / rerun census
supported-path SQLSTATE 40P01 census
```

S04 introduces no new T3 scenario, but every accepted S03 concurrency target must remain green and supported-path `40P01` must remain zero.

## 12.4 Unchanged-boundary verification

Explicitly verify and report:

```text
15 authoritative tables
one Alembic base / one head
0001_m2_kernel file and revision unchanged
compare_metadata == []
no schema/migration/index diff
no pyproject dependency or uv.lock diff
41 mutations + 22 business reads unchanged
1 Health operation added; total HTTP = 64
83 scenarios and 21 predicates unchanged
no CLI/packaging/S05 surface
obsolete Actions/payload material absent
```

---

# 13. Status, commits and publication

Keep this execution aid in the working tree until reviewer acceptance:

```text
docs/milestones/M2/wip/M2-S04-codex-prompt.md
```

At implementation start, `status.md` may record `M2-S04 IN PROGRESS` with an honest current task. Do not change any prior reviewer-owned completion record.

Use intentional commits, normally separating:

```text
S04 implementation and permanent evidence
candidate evidence/status
optional provenance-only correction when necessary
```

Only after every required focused, real-PostgreSQL, installed-package and full-repository gate passes may `status.md` record:

```text
M2-S04 — CANDIDATE READY FOR REVIEW
reviewer decision pending
M2-S05 — BLOCKED
```

Codex must not declare:

```text
M2-S04 COMPLETED
M2-S05 READY or IN PROGRESS
milestone DELIVERED
```

If `TEST_DATABASE_URL` is unavailable, a required installed-package test cannot run, a startup/Health requirement fails, a sensitive value leaks, the guard invokes migration, a second engine is required, or an architecture/documentation contradiction appears:

```text
do not mark CANDIDATE READY FOR REVIEW
do not start M2-S05
leave an honest IN PROGRESS or STOP state
record the exact blocker and completed partial work
```

Push normally to `origin/M2` and verify:

```text
local HEAD == origin/M2 == remote M2
working tree clean
ahead/behind 0/0
no PR
no GitHub Actions or encoded publication mechanism
```

---

# 14. Required handoff

Report verified facts only:

```text
cycle / slice / branch
starting baseline
implementation, evidence and provenance commits
remote synchronization and clean tree

Settings
    exact fields/defaults/validation
    source precedence
    secret-dir behavior
    engine keyword mapping

Runtime composition
    one-engine identity proof
    worker independence
    disposal matrix

Startup guard
    discovered shipped base/head
    real current-head success
    full mismatch/unavailable/timeout matrix
    no migration/repair and no hard-coded revision
    no serving on failure

Health
    exact application statuses/messages/timing
    exact SELECT 1 and same-engine proof
    pool-starvation deadline/recovery
    HTTP 200/503/400/500 results
    no-store and OpenAPI result
    leakage-negative evidence

Traceability
    M2-VER-22 target set/result
    M2-VER-23 target set/result
    63 business + 1 operational = 64 HTTP inventory
    preserved 41 / 83 / 21 registries

Installed-package S04 smoke
focused and complete command results
CPython / PostgreSQL / uv versions
skip / xfail / rerun / 40P01 census
unchanged schema/migration/dependency/lockfile statement
status = CANDIDATE READY FOR REVIEW or honest partial state
```
