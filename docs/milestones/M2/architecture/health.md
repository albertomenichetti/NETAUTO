# M2 Core Health Architecture

**Status:** DRAFT — HEALTH DESIGN COMPLETE — API/CLI/RUNTIME/VERIFICATION/TRACEABILITY/CONSISTENCY CLOSURE PASSED — READY FOR FREEZE REVIEW

**Authority:** NORMATIVE M2 ARCHITECTURE DRAFT

## Authority and scope

This document owns the M2 Core Health application and infrastructure realization for:

```text
Core readiness meaning
application health operation and result model
active PostgreSQL readiness probe
fixed two-second database-check timeout
monotonic execution-time measurement
safe database-failure classification
HTTP-adapter integration behind the wire contract in api.md
startup/runtime ownership handoff
Health-specific verification hooks
```

Its implementation authority, once the complete M2 architecture set is frozen, is:

```text
docs/milestones/M2/contract.md
    FINAL / FROZEN Health outcomes
+
docs/milestones/M2/architecture/api.md
    exact /health/core wire contract
+
docs/milestones/M2/architecture/verification.md
    M2-VER-23 and dependent evidence obligations
+
docs/general/technology_baseline.md
    asyncio, SQLAlchemy Core, FastAPI and testing baseline
+
this document
    application/probe/runtime realization
```

This document does not own:

```text
request/response DTO shape, status codes or Cache-Control
    -> api.md

engine/pool settings, startup revision guard, serving and deployment
    -> runtime-deployment.md

CLI connection-state behavior
    -> cli.md

executed evidence and final acceptance records
    -> verification.md and future steps.md
```

Discovery under `../wip/health-api.md` is superseded by this document for the areas owned here.

---

## 1. Governing readiness meaning

M2 exposes exactly one Core operational readiness operation:

```text
GET /health/core
```

It answers:

```text
can this already-started Core worker execute its Health application path
and complete an active PostgreSQL round trip now?
```

It does not answer:

```text
is the process merely alive?
is the database schema revision compatible?
are future subsystems healthy?
is the deployment highly available?
are performance or capacity SLAs being met?
```

The M2 component set is closed and exact:

```text
app_status
db_status
```

There is no dynamic registry, generic aggregate, dependency graph, plugin mechanism or degraded/warning state.

A valid returned Health result is ready only when every required component is `ok`.

---

## 2. Architecture boundaries and modules

Health is an operational application capability. It is not a domain aggregate and introduces no module under `netauto.domain`.

The conceptual module ownership is:

```text
src/netauto/application/health.py
    HealthStatus
    ComponentHealth
    CoreHealthResult
    DatabaseHealthProbe protocol
    DatabaseProbeUnavailable
    DatabaseProbeTimedOut
    CoreHealthService
    fixed database timeout
    monotonic elapsed-time conversion

src/netauto/persistence/health.py
    PostgreSQLHealthProbe
    exact SELECT 1 execution
    SQLAlchemy/driver failure translation
    borrowed-connection cleanup

src/netauto/entrypoints/api/health.py
    /health router
    strict request validation
    response DTO mapping
    200 / 503 selection
    Cache-Control: no-store

src/netauto/entrypoints/http.py
    composition of the probe and service from the process runtime engine
    inclusion of the Health router
    serving only after successful startup validation
```

The inward application port is `DatabaseHealthProbe`. The SQLAlchemy adapter implements that port. Application code does not import SQLAlchemy exception or connection types.

The existing business services and `UnitOfWorkFactory` remain unchanged by this ownership split.

---

## 3. Application result model

### 3.1 Status vocabulary

The application vocabulary is exactly:

```text
ok
error
```

A component result contains:

```text
status
message: optional safe string
```

The application result contains:

```text
app_status: ComponentHealth
db_status: ComponentHealth
execution_time_ms: non-negative integer
```

A derived, non-wire convenience predicate may be:

```text
is_ready
    -> app_status.status == ok
       and db_status.status == ok
```

No third status, numeric score, warning list or arbitrary diagnostics map is introduced.

### 3.2 Application component meaning

For every valid M2 Core Health result returned by `CoreHealthService`:

```text
app_status.status = ok
app_status.message = absent
```

Reaching and executing the mapped application operation is the M2 application check. No synthetic FastAPI/Uvicorn self-test, event-loop probe, module registry or internal callback graph is added.

The shared component shape permits `app_status = error` as a stable carrier for a future explicitly designed check, but M2 has no normal producer for that state.

An unexpected programming/composition failure is not disguised as `app_status = error`. It propagates to the existing unexpected HTTP failure boundary and produces the canonical safe `500 internal_error` response.

---

## 4. CoreHealthService pipeline

`CoreHealthService.check()` performs one bounded operation:

```text
1. capture monotonic start time
2. establish app_status = ok
3. execute exactly one DatabaseHealthProbe attempt under the fixed deadline
4. classify database success, timeout or expected unavailability
5. capture monotonic end time after probe cleanup/classification
6. derive execution_time_ms
7. return one complete CoreHealthResult
```

The service does not:

```text
retry
back off
cache a prior result
run checks in the background
open a business Unit of Work
query Alembic state
repair a connection or schema
raise ApplicationFailure for an ordinary readiness failure
```

### 4.1 Success

```text
probe completes successfully
    -> db_status.status = ok
    -> message absent
```

### 4.2 Dedicated timeout

The fixed application constant is:

```text
CORE_DATABASE_HEALTH_TIMEOUT_SECONDS = 2.0
```

It is not an M2 setting and is not overridden by deployment configuration.

The service uses native asyncio timeout semantics around the complete probe call. A deadline expiration produces:

```text
db_status.status = error
db_status.message = "database readiness check timed out"
```

A SQLAlchemy pool timeout raised before the outer deadline is classified through the same timeout result.

### 4.3 Expected database unavailability

A translated connection, protocol, driver or query-execution failure produces:

```text
db_status.status = error
db_status.message = "database readiness check failed"
```

The exact public message set is deliberately finite and controlled.

### 4.4 Unexpected failure and cancellation

The service catches only:

```text
its own probe-unavailable exception
its own probe-timeout exception
the outer asyncio timeout result
```

It does not catch `BaseException` and does not swallow task cancellation. Unexpected application defects propagate to the existing unexpected-failure handler.

This distinction prevents a code defect from being misreported as an ordinary PostgreSQL readiness condition.

---

## 5. PostgreSQLHealthProbe

### 5.1 Runtime authority

The probe uses the same process-local `AsyncEngine` and connection pool as business persistence.

```text
business operations
    -> runtime AsyncEngine / pool

Health database check
    -> the same runtime AsyncEngine / pool
```

M2 does not create:

```text
a dedicated Health engine
a dedicated Health pool
a reserved Health connection
a direct DSN path bypassing the runtime engine
```

This is intentional. A worker unable to obtain a connection from its real runtime pool is not ready to serve normal database-backed work.

### 5.2 Exact active query

The probe executes exactly one active PostgreSQL statement:

```sql
SELECT 1
```

The canonical SQLAlchemy realization is a textual Core statement through an `AsyncConnection` obtained from `AsyncEngine.connect()`.

Success requires one scalar result equal to integer `1`.

The query intentionally references no NETAUTO table. It verifies:

```text
pool checkout
PostgreSQL connection/protocol usability
SQL execution
result round trip
```

It does not verify:

```text
Alembic revision
NETAUTO table existence
application data integrity
specific table privileges
business-query performance
```

### 5.3 Transaction behavior

The Health probe is not a semantic business Unit of Work.

```text
AsyncEngine.connect()
-> execute SELECT 1
-> consume the scalar result
-> close the connection context
```

If SQLAlchemy starts an implicit transaction, connection-context exit rolls it back. The probe never commits and never uses `UnitOfWorkFactory` or `CoherentReadUnitOfWork`.

No `AUTOCOMMIT`, session mutation or `SET TRANSACTION` statement is required.

### 5.4 Failure translation

The persistence adapter translates only expected SQLAlchemy/driver infrastructure outcomes into the application port exceptions.

```text
SQLAlchemy pool TimeoutError
    -> DatabaseProbeTimedOut

SQLAlchemy connection/DBAPI/protocol/query failure
    -> DatabaseProbeUnavailable

unexpected result carrier instead of scalar 1
    -> DatabaseProbeUnavailable
```

Raw exception text is retained only as an internal cause where useful for diagnostics. It is never copied into the application result or public response.

Programming errors outside the finite expected infrastructure family are not normalized by a broad catch-all.

### 5.5 Timeout and connection cleanup

The two-second outer deadline covers:

```text
pool wait
connection establishment/check-out behavior
configured pool pre-ping when enabled
SELECT 1 execution
result consumption
normal probe completion
```

On timeout or cancellation, the borrowed connection must be closed or invalidated through the SQLAlchemy async context boundary before the probe attempt is considered finished. A connection whose in-flight operation was cancelled must not be returned to the pool as known-good merely to produce the Health response.

The active deadline is authoritative even when configured `pool_timeout` is greater than two seconds. If another configured timeout fails earlier, that earlier failure is classified normally.

The semantic deadline is two seconds for the probe attempt. Scheduler and cancellation-cleanup overhead may make the final HTTP elapsed time slightly greater than 2000 milliseconds; verification uses a bounded tolerance and proves that the operation does not wait for a longer pool timeout.

M2 does not add a second PostgreSQL `statement_timeout` authority for this constant query.

---

## 6. Execution-time measurement

The application service uses a monotonic elapsed-time source, conceptually:

```text
time.perf_counter_ns()
```

Measurement begins immediately on entry to `CoreHealthService.check()` and ends after the database result has been classified and probe resources have unwound.

The conversion is:

```text
elapsed_ns = max(0, end_ns - start_ns)
execution_time_ms = elapsed_ns // 1_000_000
```

Consequences:

```text
integer output
zero is valid for a sub-millisecond operation
no wall-clock adjustment can make elapsed time negative
```

The value includes application-side check execution and excludes client/network latency and ordinary HTTP response serialization after the result is returned.

A monotonic clock dependency may be injected into the service for deterministic T1 verification. Production composition uses the standard monotonic clock.

---

## 7. Readiness failure boundary

A valid Health request has three result families.

### 7.1 Ready

```text
app_status = ok
db_status  = ok
-> HTTP 200
```

### 7.2 Not ready

```text
app_status = ok
db_status  = error
-> HTTP 503
-> complete Core Health DTO
```

Timeout and expected PostgreSQL failure are readiness outcomes, not business `ApplicationFailure` instances.

### 7.3 Unexpected internal failure

If the application cannot produce a valid bounded result because of an unexpected defect:

```text
-> existing global unexpected-failure handling
-> HTTP 500
-> canonical {code, message, details}
-> no internal leakage
```

A 500 internal transport failure is not rewritten as a false `503 db_status=error`.

### 7.4 Safe diagnostics

Valid Health component messages are exactly the controlled phrases defined by this document. They contain no:

```text
database URL
credentials
username
host or port
server address
SQL text
SQLSTATE
constraint/table/column name
raw SQLAlchemy/Psycopg exception
stack trace
pool internals
```

The response does not disclose whether failure occurred during checkout, connect, pre-ping or query execution, except for the bounded timeout versus generic-failure distinction.

---

## 8. HTTP adapter realization

The operational adapter is conceptually:

```text
src/netauto/entrypoints/api/health.py
```

with:

```text
APIRouter(prefix="/health", tags=["health"])
GET /core
```

### 8.1 Strict request handling

The route:

```text
accepts no query parameters
accepts no request body
```

It reuses the delivered strict helpers:

```text
validate_query(request, ())
NoBody
```

Strict validation occurs before invoking `CoreHealthService`.

Unknown/repeated query parameters or a non-empty body produce:

```text
400 invalid_request
canonical bounded error body
no database probe
```

They do not produce a Health DTO or `503`.

### 8.2 DTO mapping

The adapter owns only mapping from application values to the exact DTO defined by `api.md`.

The component `message` field is omitted when absent. The FastAPI response configuration must therefore exclude `None` rather than serializing:

```json
{"message": null}
```

The `503` OpenAPI response declares the same Core Health DTO as the successful response.

### 8.3 Status and cache header

The adapter derives the status from the complete application result:

```text
is_ready = true  -> 200
is_ready = false -> 503
```

Every valid `200` or `503` Core Health response includes exactly the required cache directive:

```text
Cache-Control: no-store
```

The adapter sets the status and returns the DTO directly. It does not raise `HTTPException` for an ordinary not-ready result, because doing so would replace the required body.

### 8.4 Composition lookup

The route obtains one already-composed `CoreHealthService` from application state. It does not build an engine, read settings or construct a new pool per request.

The composition root remains explicit and testable; FastAPI dependency overrides are not the application composition authority.

---

## 9. Composition, startup and shutdown

### 9.1 Process composition

The HTTP composition root creates one process-lifetime Health service from the same process-lifetime runtime engine.

Conceptually:

```text
load settings
-> build runtime AsyncEngine/pool
-> perform exact startup schema guard
-> compose PostgreSQLHealthProbe(runtime.engine)
-> compose CoreHealthService(probe)
-> publish application state
-> enter serving
```

The exact installed-head discovery and startup-guard implementation remain owned by `runtime-deployment.md`. That owner must preserve the ordering above semantically: no Health endpoint is served before the schema guard succeeds.

### 9.2 Startup failure

If database reachability or exact revision validation fails during startup:

```text
worker does not enter serving
/api/v1/core is unavailable
/health/core is unavailable
```

Health is not a degraded startup mode and is not the diagnostic replacement for startup logs/process status.

### 9.3 Runtime loss after startup

If PostgreSQL becomes unavailable after a successful startup:

```text
worker remains an HTTP process
GET /health/core -> 503 bounded result
```

The endpoint performs no migration, engine rebuild or process shutdown.

### 9.4 Worker model and shutdown

Every Uvicorn worker owns its own:

```text
application instance
runtime engine/pool
PostgreSQLHealthProbe
CoreHealthService
```

A Health request reports the worker that handled it; M2 introduces no cross-worker aggregation.

Graceful serving shutdown stops accepting new work, allows or cancels in-flight requests according to the ASGI server lifecycle, and disposes the runtime engine after request serving ends. The Health service owns no separate resource that requires independent shutdown.

---

## 10. Transaction and concurrency posture

Health is read-only operational work and is not added to the 41-mutation semantic matrix.

It acquires:

```text
no NETAUTO advisory gate
no explicit row lock
no model/data current-state lock
no semantic write Unit of Work
```

`SELECT 1` references no NETAUTO row. It cannot participate in the application row-lock ordering graph or emit lifecycle events.

Concurrent Health requests:

```text
may execute independently
may check out separate pooled connections
may wait on pool capacity
```

M2 adds no process-global Health mutex, result cache or rate limiter. Pool saturation that prevents checkout within the fixed deadline is a legitimate `503` readiness observation.

Health uses no semantic whole-UoW restart budget. It performs one attempt only.

---

## 11. Relationship with CLI and deployment

### 11.1 Interactive CLI

`cli.md` consumes the wire contract as follows:

```text
/connect
    -> GET /health/core

/status while connected
    -> GET /health/core
```

Health does not define CLI state, endpoint parsing or transport-failure behavior.

The CLI must validate both:

```text
HTTP 200
and
exact valid Core Health DTO
```

before establishing/retaining CONNECTED state.

### 11.2 Non-interactive CLI

Health does not become a mandatory preflight for:

```text
netauto -n ...
```

The requested business operation is invoked directly.

### 11.3 Deployment readiness

The manual Linux procedure uses `GET /health/core` only after:

```text
wheel installation
explicit Alembic realization
successful worker startup/schema guard
```

The deployment procedure may use any normal HTTP client. Installation and startup do not require the official CLI.

---

## 12. Security, transport and observability boundary

Health uses the same listener, trusted access boundary and optional external TLS termination as the business API.

M2 introduces no:

```text
Health-specific authentication
public unauthenticated Internet guarantee
separate Health port/listener
mTLS identity
network-policy automation
```

The endpoint contains only the bounded status contract and does not reveal database topology.

Health is not:

```text
a metrics endpoint
a tracing span API
a logging redesign
a diagnostics dump
```

Expected readiness failures are normal bounded operational results. This document does not require per-probe `ERROR` logging or raw exception logging. Unexpected failures continue to use the project-wide outer error/logging boundary.

---

## 13. Verification realization

Primary evidence is owned by:

```text
M2-VER-23 — Core readiness contract
```

Health also supplies hooks consumed by:

```text
M2-VER-22 — no Health serving before successful startup guard
M2-VER-26 — CLI /connect and /status
M2-VER-29 — Linux readiness procedure
M2-VER-30 — trusted transport boundary
```

### 13.1 T0/T1 application evidence

Pure/application verification covers:

```text
component/result invariants
ready derivation
success, timeout and unavailable classification
exact controlled messages
unexpected exception propagation
cancellation not swallowed
monotonic floor conversion including sub-millisecond zero
no retry
one probe call per result
```

The probe protocol and monotonic clock are explicit test seams. Fakes do not claim PostgreSQL evidence.

### 13.2 T2 real-PostgreSQL evidence

Real PostgreSQL verification covers:

```text
same runtime AsyncEngine/pool is used
exact SELECT 1 returns scalar 1
no commit or application-table access
connection is returned cleanly after success
```

A deterministic pool-starvation scenario uses a small test engine such as:

```text
pool_size = 1
max_overflow = 0
pool_timeout > 2 seconds
one connection deliberately held by the test controller
```

The Health attempt must time out near the fixed two-second deadline instead of waiting for the longer pool timeout. After releasing the held connection, a later check must succeed, proving bounded cleanup and recovery.

A test-only blocking probe may supplement this to prove the application timeout boundary. Network-blackhole timing is not the normative orchestration mechanism.

### 13.3 T4 HTTP evidence

API verification covers the exact inventory and behavior:

```text
GET /health/core only
no GET /health aggregate
no body/query on valid request
healthy -> 200 exact DTO
DB failure -> 503 exact DTO
timeout -> 503 exact DTO
message omitted when absent
Cache-Control: no-store on 200 and 503
malformed request -> 400 invalid_request and zero probe calls
unexpected service defect -> safe 500, not false 503
OpenAPI declares 200 and 503 Core Health DTO
```

Injected internal failure text containing credentials, URL, host, SQLSTATE or SQL must never appear in a valid Health response.

### 13.4 T9 installed-runtime evidence

Installed-wheel verification covers:

```text
Health router and application modules ship in the wheel
installed server starts only after the revision guard
healthy installed worker returns 200
runtime database loss returns 503
no Git checkout is required
```

### 13.5 Negative evidence

Static/runtime verification proves absence of:

```text
Alembic queries from the Health path
migration calls
Health result caching
multiple probe retries
dedicated Health engine/pool
dynamic health registry
separate listener
schema/table readiness query
raw exception-to-message mapping
```

No T3 mutation scenario is added solely for Health because the operation owns no mutable kernel predicate or row-lock mechanism.

---

## 14. AS-IS and cross-owner consistency

### 14.1 AS-IS application/runtime compatibility

The delivered composition already owns one process-lifetime engine and explicit application services. M2 adds one operational service without changing:

```text
business Unit-of-Work ownership
READ COMMITTED mutation isolation
coherent business-read isolation
business route namespace
business failure catalog
persistence metadata
concurrency lock graph
```

Using `AsyncEngine.connect()` directly for this operational probe is intentional and does not weaken the rule that one semantic business mutation owns one UoW.

### 14.2 API compatibility

This document realizes the exact `api.md` Health contract:

```text
GET /health/core
strict no-body/no-query request
component shape
200 / 503
complete body on not-ready
message omission
Cache-Control: no-store
safe diagnostics
```

It introduces no additional route, field, status or error code.

### 14.3 Persistence/concurrency compatibility

The query uses no NETAUTO table and no explicit lock. It adds no wait edge to the supported mutation graph and no schema requirement beyond PostgreSQL connectivity.

### 14.4 Verification compatibility

The design supplies a concrete implementation and test path for every assertion in `M2-VER-23` without requiring implementation evidence before architecture freeze.

### 14.5 Startup/runtime handoff

`runtime-deployment.md` confirms:

```text
same engine/pool composition
revision guard before serving
Health service availability after guard
engine disposal after serving
installed-wheel inclusion
```

The confirmed composition does not change this document's observable Health behavior or database-probe semantics.

No contract reopening is required.

---

## 15. Traceability and closure

Primary ownership:

```text
M2-OUT-11
    Core runtime readiness endpoint

M2-AC-23
    Core readiness contract

M2-VER-23
    complete required evidence bundle
```

Supporting responsibility:

```text
M2-OUT-12 / M2-AC-26
    Health-backed interactive CLI connection state

M2-OUT-14 / M2-AC-29
    post-start readiness verification

M2-OUT-15 / M2-AC-30
    shared trust and transport boundary
```

Architecture-draft closure:

```text
readiness meaning                               CLOSED
application result model                        CLOSED
application/probe module boundary               CLOSED
same-engine/pool policy                         CLOSED
exact active PostgreSQL query                   CLOSED
fixed timeout and cleanup semantics             CLOSED
monotonic execution timing                      CLOSED
safe failure classification                     CLOSED
HTTP-adapter realization                        CLOSED
startup-versus-runtime responsibility           CLOSED
transaction/concurrency posture                 CLOSED
verification hooks and negative evidence        CLOSED
AS-IS/API/CLI/runtime/verification cross-check   PASS
```

No Health-specific design decision remains open in this owner.

Runtime composition, CLI consumption, traceability and consistency closure have passed.

This document remains `NOT FROZEN` only until the dedicated architecture-set freeze transition is explicitly approved and committed.

Executed Health tests are implementation-slice and final-delivery evidence, not architecture-freeze prerequisites.
