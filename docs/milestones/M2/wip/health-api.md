# M2 WIP — Health API Discovery

**Status:** DISCOVERY CAPTURE — NON-NORMATIVE

This document captures decisions reached during M2 feature discovery for the candidate capability **Health API**.

It is an execution aid under `wip/`. It does not replace `contract.md`, the M2 architecture set, `steps.md`, or the current delivered AS-IS. Contract-level outcomes will later be distilled into `contract.md`; semantic/technical decisions will later be assigned to the appropriate M2 architecture owners before implementation is authorized.

## 1. Namespace and route

Health is an operational capability, separate from the versioned kernel business API.

M2 introduces:

```text
GET /health/core
```

The namespace is:

```text
/health
```

and is intentionally separate from:

```text
/api/v1/core
```

M2 does not require a top-level aggregate `GET /health` endpoint.

The namespace is intended to remain extensible for future capability-specific endpoints, for example:

```text
/health/core
/health/discovery
/health/automation
/health/<future-capability>
```

M2 does not introduce a dynamic health registry, plugin health mechanism, dependency graph, or generic aggregation mechanism.

## 2. Semantic meaning

`GET /health/core` represents the runtime readiness of the NETAUTO core, not merely HTTP-process liveness.

M2 intentionally keeps the readiness model small. The endpoint models two current status dimensions:

```text
app_status
db_status
```

### Application status

`app_status` is `ok` when the health endpoint has reached and can execute its mapped application health logic.

M2 does not introduce an internal synthetic FastAPI/Uvicorn self-diagnostic beyond successful execution of the health function itself.

### Database status

`db_status` is determined by an active PostgreSQL connectivity check using a simple query.

M2 checks no other runtime dependency.

## 3. Status shape

Both application and database status use the same stable object shape so future extensions do not require changing the structural contract.

Conceptual status object:

```text
status
    -> required
    -> "ok" | "error"

message
    -> optional string
    -> absent when unnecessary
    -> safe controlled diagnostic text
```

Example healthy response body:

```json
{
  "app_status": {
    "status": "ok"
  },
  "db_status": {
    "status": "ok"
  },
  "execution_time_ms": 12
}
```

Example database failure:

```json
{
  "app_status": {
    "status": "ok"
  },
  "db_status": {
    "status": "error",
    "message": "connection to database failed"
  },
  "execution_time_ms": 27
}
```

`app_status.message` is part of the stable status shape even though M2 does not currently require a case that populates it.

Status messages must not expose raw PostgreSQL/SQLAlchemy exceptions, credentials, database URLs, usernames, host details, or other sensitive/internal diagnostic material.

## 4. HTTP status semantics

The HTTP response status represents overall core readiness.

```text
HTTP 200
    -> every required component status is "ok"

HTTP 503 Service Unavailable
    -> at least one required component status is "error"
```

Health failure still returns the complete structured health response. It does not pass through the normal `/api/v1/core` business-error envelope.

For the M2 model, the concrete runtime partial-failure case is:

```text
app_status = ok
db_status = error
-> HTTP 503
```

## 5. Runtime database check and timeout

The database health check uses a simple PostgreSQL query sufficient to prove runtime connectivity.

The check has a dedicated timeout:

```text
2 seconds
```

The health contract does not rely solely on the normal database connection-pool timeout.

A database health-check timeout produces:

```text
db_status.status = "error"
db_status.message = safe timeout diagnostic
HTTP 503
```

The exact query and implementation mechanism remain architecture/implementation concerns.

## 6. Execution timing

Every health response contains:

```text
execution_time_ms
```

Semantics:

```text
type
    -> integer

unit
    -> milliseconds

meaning
    -> total server-side execution time of the core health operation

measurement interval
    -> from entry into health-check execution
       through completion of all checks

excludes
    -> client/network HTTP latency
```

`execution_time_ms` is present on both success and failure responses.

The clock/measuring primitive is an architecture/implementation choice; a monotonic elapsed-time source is expected rather than wall-clock difference.

## 7. Relationship with startup schema compatibility

Runtime health and startup schema compatibility are separate responsibilities.

The production deployment discovery establishes a startup schema guard requiring exact equality between:

```text
Alembic head included with the installed NETAUTO release
and
the current database Alembic revision
```

If that guard fails, the worker must not enter serving state.

Therefore `/health/core` does **not** repeat Alembic revision/schema compatibility checks. Its database check is a runtime connectivity/readiness probe only.

Conceptually:

```text
startup
    -> database reachable as required for bootstrap
    -> exact schema revision guard
    -> serving permitted only on success

runtime /health/core
    -> application status
    -> simple PostgreSQL connectivity check
```

## 8. Scope boundaries

### In scope for M2

- operational `/health` namespace;
- `GET /health/core`;
- readiness rather than process-only liveness semantics;
- application and PostgreSQL status objects;
- binary `ok` / `error` state model;
- safe optional status message;
- HTTP 200 / 503 readiness mapping;
- full structured body on health failure;
- simple active PostgreSQL query;
- dedicated two-second DB-check timeout;
- total `execution_time_ms` in every response;
- extensible capability-oriented health route pattern.

### Out of scope for M2

- generic `GET /health` aggregation;
- dynamic health-check registration;
- plugin health framework;
- health dependency graphs;
- health checks for non-core future subsystems;
- advanced degraded/warning/unknown states;
- metrics/monitoring platform integration;
- schema revision checking inside `/health/core`;
- replacing startup schema compatibility with runtime health.

## 9. Later authority propagation

Before implementation is authorized, the relevant M2 authorities will need to own at least:

- public/operational HTTP contract for `/health/core`;
- application health operation semantics;
- PostgreSQL check and timeout behavior;
- safe failure-message boundary;
- startup-guard interaction;
- API verification obligations for exact response shape and HTTP status behavior.
