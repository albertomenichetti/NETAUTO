# M2 Core Health Architecture Cross-Check

**Status:** PASS — HEALTH DESIGN COMPLETE — RUNTIME/CLI OWNER REVIEW AND IMPLEMENTATION EVIDENCE PENDING

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

## Review target

```text
docs/milestones/M2/architecture/health.md
```

The review compares the Health realization with:

```text
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/verification.md

docs/milestones/M2/wip/health-api.md
docs/milestones/M2/wip/runtime-configuration-production-deployment.md
docs/milestones/M2/wip/netauto-cli.md

docs/architecture/api.md
docs/architecture/persistence.md
docs/architecture/verification.md
docs/general/technology_baseline.md

current HTTP composition, runtime engine, UoW and strict-request helpers
on branch M2
```

## Closure summary

```text
readiness semantic alignment                PASS
exact /health/core wire realization          PASS
application/probe boundary                   PASS
same runtime engine/pool policy              PASS
active PostgreSQL query                      PASS — SELECT 1
fixed two-second timeout scope               PASS
monotonic execution timing                   PASS
safe message/failure boundary                PASS
malformed-request separation                 PASS
startup-schema responsibility separation     PASS
transaction/UoW compatibility                PASS
concurrency wait-graph compatibility          PASS
verification M2-VER-23 path                  PASS
CLI/deployment dependency compatibility       PASS
open Health-specific architecture point       0
contract reopening                            NOT REQUIRED
implementation evidence                       PENDING by governance
```

## Material findings

### 1. Health must observe the real business pool

A dedicated Health engine, pool or reserved connection could report healthy while ordinary business operations are unable to obtain a runtime connection.

The accepted design therefore uses:

```text
one process runtime AsyncEngine/pool
    -> business persistence
    -> PostgreSQLHealthProbe
```

Pool saturation that exceeds the fixed deadline is a valid not-ready result.

This does not make Health a business Unit of Work. The probe uses one direct operational connection context and never commits.

### 2. The two-second timeout must include pool checkout

The current runtime pool timeout may be configured above two seconds. Relying on it would violate the dedicated Health deadline.

The accepted boundary wraps the complete probe call:

```text
pool wait
connection acquisition / configured pre-ping
SELECT 1
result consumption
probe cleanup
```

The fixed application deadline wins over a longer pool timeout. Scheduler/cancellation cleanup may add small elapsed overhead, so verification uses tolerance while proving the check does not wait for the longer pool timeout.

### 3. The active query is exactly `SELECT 1`

The Health database probe must prove an actual PostgreSQL round trip without duplicating schema or business checks.

```sql
SELECT 1
```

is sufficient and intentionally accesses no NETAUTO table.

Consequences:

```text
schema revision remains startup-guard authority
business aggregate validity remains business-read authority
Health owns connectivity/readiness only
```

### 4. `app_status` has no synthetic M2 failure probe

The application component is `ok` when the mapped application operation is executing and can return a bounded result.

M2 does not invent:

```text
FastAPI self-diagnostics
event-loop registry
module callbacks
dynamic application checks
```

An unexpected code/composition defect propagates to safe HTTP `500`; it is not disguised as `app_status=error` and `503`.

The shared DTO shape remains extensible without claiming a nonexistent current check.

### 5. Expected readiness failure and internal defect remain distinct

Only finite database outcomes become a valid `503` result:

```text
deadline / pool timeout
    -> "database readiness check timed out"

expected SQLAlchemy/driver/connect/query failure
    -> "database readiness check failed"
```

No raw exception text crosses the application boundary.

Unexpected programming errors and task cancellation are not caught by a broad exception handler. This preserves the project error/logging boundary and prevents false readiness diagnostics.

### 6. Health is not part of the semantic mutation/UoW matrix

The accepted probe:

```text
performs no current-state DML
uses no NETAUTO table
acquires no advisory gate
acquires no explicit row lock
emits no lifecycle event
```

It therefore adds no mutation to the 41-mutation census and no safety predicate to the 21-predicate catalog.

The operation may contend only for pool/network/database execution capacity. No supported row-lock wait cycle is introduced.

### 7. Startup revision mismatch cannot be reported through Health

The directed dependency remains:

```text
build runtime
-> exact shipped-head startup guard
-> serving permitted
-> /health/core available
```

If the guard fails, no HTTP route is served. Health performs no Alembic lookup and no migration.

After successful startup, a later database outage is represented by `503`.

### 8. The HTTP adapter must omit absent messages

The wire contract requires:

```text
message absent
not
message = null
```

The accepted FastAPI realization therefore needs response serialization that excludes `None`, plus the same Core Health DTO declaration for `200` and `503`.

Every valid Health result includes:

```text
Cache-Control: no-store
```

Malformed body/query input is validated before the probe and produces canonical `400 invalid_request` with zero probe calls.

### 9. Verification remains implementable after architecture freeze

`M2-VER-23` now has concrete seams and deterministic evidence paths:

```text
T1
    fake probe + monotonic clock

T2
    real SELECT 1
    deterministic pool starvation with pool_timeout > 2

T4
    exact 200/503/body/header/error behavior

T9
    installed-wheel startup/runtime check
```

A network blackhole is not required as the normative timeout orchestrator. Real pool starvation supplies a deterministic PostgreSQL/runtime proof; a blocking fake verifies the application deadline.

No executed implementation evidence is claimed by this review.

## Cross-owner result

### Contract

```text
M2-OUT-11  covered
M2-AC-23   concretely realizable
no Scope/Non-goal/delta change
```

### API

```text
route and strict request       aligned
component/response shape       aligned
200 / 503                      aligned
safe message boundary          aligned
Cache-Control no-store         aligned
no business envelope on 503    aligned
```

### Persistence/concurrency

```text
same runtime engine             aligned
business UoW unaffected         aligned
no table/row/advisory lock      aligned
no new semantic mutation        aligned
no deadlock-proof change        required
```

### Verification

```text
M2-VER-23 assertions             all have owners/hooks
M2-VER-22 dependency             preserved
M2-VER-26 CLI hook               preserved
M2-VER-29 deployment hook        preserved
negative Health surface          covered
```

### Runtime/CLI handoff

The remaining owner reviews are limited to composition consumption:

```text
runtime-deployment.md
    -> startup guard before serving
    -> same engine and installed-wheel inclusion
    -> shutdown ordering

cli.md
    -> exact DTO validation for /connect and /status
```

They may not redefine the Health query, timeout, result or public route.

## Final result

```text
Health architecture design      COMPLETE
contract compatibility          PASS
API compatibility               PASS
persistence/concurrency         PASS
verification-design coverage    PASS
Health-specific open point      0
runtime/CLI owner review        PENDING
implementation evidence         PENDING
contract reopening              NOT REQUIRED
```
