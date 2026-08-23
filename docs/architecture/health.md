# Core Health — Current AS-IS

## Purpose and authority

This document owns Core readiness meaning, application/probe behavior and runtime
resource use. [`api.md`](api.md) owns the wire DTO and status mapping;
[`runtime-deployment.md`](runtime-deployment.md) owns startup compatibility,
engine composition and serving lifecycle.

## Readiness meaning

`GET /health/core` answers whether an already-started worker can execute its
Health application path and complete one active PostgreSQL round trip now. It is
not a liveness-only signal, schema-revision check, capacity SLA, diagnostics dump
or aggregate for future subsystems.

The exact component set is:

```text
app_status
db_status
```

Each component uses only `ok` or `error` and an optional controlled `message`.
The complete result also contains a non-negative integer `execution_time_ms`.
Readiness is true only when both components are `ok`.

Reaching the application operation makes `app_status = ok`; there is no secondary
framework self-test. An unexpected programming/composition defect propagates to
the safe canonical 500 boundary and is not disguised as a component error.

## Application pipeline

One `check()` call:

```text
capture monotonic start
set app_status = ok
perform exactly one database probe under the fixed deadline
classify success, owned timeout or expected unavailability
wait for probe cleanup
capture monotonic end
return one complete result
```

There is no retry, cache, backoff, background check, business Unit of Work,
Alembic query or repair.

The fixed full-probe deadline is:

```text
CORE_DATABASE_HEALTH_TIMEOUT_SECONDS = 2.0
```

It covers pool wait, checkout/connection, configured pre-ping, query, result
consumption and cleanup. It is not configurable. Timeout yields the controlled
message `database readiness check timed out`; expected database unavailability
yields `database readiness check failed`. Cancellation is never swallowed.

Elapsed time uses a monotonic clock, conceptually `perf_counter_ns()`:

```text
max(0, end_ns - start_ns) // 1_000_000
```

Sub-millisecond execution may report zero. Scheduler and cancellation-cleanup
overhead may place the HTTP completion slightly beyond two seconds without
changing the semantic probe deadline.

## PostgreSQL probe

The probe borrows the same process-local SQLAlchemy `AsyncEngine` and pool used by
business work. There is no Health engine, pool, reserved connection or direct DSN
bypass.

It executes exactly:

```sql
SELECT 1
```

Success requires the exact integer scalar `1`. The operation uses
`AsyncEngine.connect()`, consumes the scalar and closes the connection context.
Any implicit transaction is rolled back on context exit; Health never commits or
touches a NETAUTO table.

Expected pool, driver, connection, protocol and query failures are translated to
owned application exceptions without exposing raw text. A cancelled in-flight
connection is closed or invalidated before completion and is not returned as
known-good.

## HTTP behavior

The route accepts no query parameter and no body. Strict request validation occurs
before the probe.

```text
app ok + db ok       -> 200 complete Health DTO
app ok + db error    -> 503 complete Health DTO
malformed request    -> 400 invalid_request; zero probe calls
unexpected defect    -> safe canonical 500
```

Valid 200/503 responses include `Cache-Control: no-store`. Optional messages are
omitted, not serialized as null. Controlled output contains no URL, credential,
host, port, SQL text, SQLSTATE, schema object, stack or driver detail.

## Startup and runtime boundary

The exact Alembic revision guard is a separate pre-serving operation. If database
reachability or exact revision validation fails at startup, the worker exposes
neither business nor Health routes.

After successful startup, later PostgreSQL loss leaves the process HTTP-capable;
Health returns the bounded 503 result. The endpoint does not migrate, repair,
rebuild the engine or stop the process.

Each Uvicorn worker owns its own application, engine/pool, probe and service.
Health reports only the worker handling the request. Shutdown owns no Health-only
resource; the shared engine is disposed after serving ends.

## Concurrency and security boundary

Health is read-only operational work outside the 41-mutation matrix. It takes no
NETAUTO advisory gate or explicit row lock and has no semantic restart budget.
Pool saturation that prevents checkout within two seconds is a legitimate
not-ready observation.

Health shares the business listener and administratively trusted reachability
boundary. It has no separate listener, authentication scheme, metrics/tracing
surface or public database topology.

## Durable verification

Verification covers exact vocabulary, one attempt, controlled messages,
monotonic timing, cancellation/cleanup, real PostgreSQL `SELECT 1`, shared-engine
identity, deterministic pool starvation and recovery, strict HTTP carriers,
200/503/500 mapping, cache header, OpenAPI DTO identity, absence of Alembic and
installed-wheel behavior. Fakes prove only application classification; the
PostgreSQL claim requires the real external test target.
