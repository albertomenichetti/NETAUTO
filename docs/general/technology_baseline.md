# NETAUTO — Technology Baseline

**Status:** CURRENT / EXTENSIBLE — `STACK-01` through `STACK-09` are RATIFIED. Future technology decisions are non-authoritative until explicitly ratified and consolidated here.

## 1. Scope and authority

This document defines project-wide implementation technology choices that are not cycle-specific domain architecture.

It is subordinate, for semantic behavior, to the current delivered architecture in `docs/architecture/` and to any explicit frozen delta of the active milestone or fix. A technology choice may realize a semantic contract but may not reinterpret it.

Cycle-local `wip/` material remains non-normative. Technology decisions become authoritative only when consolidated in this registry with explicit `RATIFIED` status.

## 2. Fixed project constraints

The current baseline assumes:

```text
language
    -> Python

public API framework
    -> FastAPI / ASGI

persistence database
    -> PostgreSQL
```

Changing one of these constraints requires an explicit technology decision and any necessary architecture reopen/propagation.

## 3. Decision registry

### STACK-01 — application/infrastructure execution model

**Status:** RATIFIED.

#### Async runtime

```text
native asyncio
```

is the project asynchronous execution baseline.

FastAPI/Starlette remain the ASGI web/runtime boundary. AnyIO may be used where natural at that boundary or in infrastructure integrations, but portability across asyncio/Trio is not a project requirement.

Alternative event-loop implementations such as `uvloop` are runtime optimizations only and are not part of the architectural technology baseline.

#### Application I/O model

Application operations that perform I/O are asynchronous by default.

This includes, in particular:

```text
HTTP/application operations that reach persistence
PostgreSQL Unit of Work and persistence access
future external-service integrations
discovery/configuration/orchestration I/O
streaming or other naturally asynchronous capabilities
```

The project does not require every Python function to be asynchronous.

#### Pure domain model

Pure domain computation remains ordinary synchronous Python.

This includes, when no I/O is performed:

```text
domain entities/value objects
canonicalization
validation semantics
candidate construction
schema/data migration algorithms
invariant evaluation
pure transformation logic
```

Async is therefore an application/infrastructure execution property, not a domain-model property.

#### Explicit I/O boundary

I/O must remain explicit in the call graph.

The project avoids hidden/lazy I/O that makes normal attribute/function access unexpectedly require database or network activity.

Blocking third-party libraries may be used only behind an explicit, bounded thread/process boundary. Accidental blocking I/O inside the event loop is not an accepted implementation style.

#### Unit of Work ownership

One semantic PostgreSQL Unit of Work owns one connection/transaction for its lifetime.

```text
one semantic UoW
    -> one explicitly owned async connection/transaction
    -> one semantic transaction boundary
```

A UoW connection/transaction is not concurrently shared by sibling tasks.

Async concurrency may exist between independent UoWs; it does not create intra-UoW parallel access to the same PostgreSQL transaction.

#### Mixed sync/async application

The project may contain synchronous and asynchronous functions where their workloads justify it.

```text
I/O-bearing application/infrastructure operation
    -> async

pure computation
    -> sync

blocking integration
    -> explicit bounded offload boundary
```

Repeated arbitrary sync/async boundary crossings inside one operation are avoided.

#### Ordinary request/response vs long-running work

Asynchronous server execution does **not** imply asynchronous HTTP semantics for callers.

Ordinary kernel commands remain normal request/response operations. `async def` does not by itself introduce `202 Accepted`, background jobs, polling or event streams.

This preserves the current public API contract, which exposes no asynchronous kernel-command status resource.

#### Future long-running operation principle

A capability whose semantic lifetime exceeds one request must not be represented merely by a detached in-process `asyncio` task.

When such a requirement appears, the owning cycle should introduce an explicit durable resource such as a conceptual `Job`, `Run` or `Execution` with authoritative persisted state.

The worker/queue technology is intentionally not selected yet. Durability, retry, scheduling, priority, distribution and throughput requirements must drive that future choice.

#### Polling and SSE principle

For a future durable long-running resource:

```text
authoritative current state
    -> normal HTTP read endpoint
    -> suitable for polling

SSE
    -> optional server-push projection for progress/events
    -> not the sole authority for state
```

Polling/read semantics are the recovery-safe baseline. SSE may be introduced for low-latency unidirectional progress/event delivery, but must not be the only way to determine current/final state.

WebSocket is not a project baseline and requires a concrete bidirectional persistent-communication requirement.

#### Structured concurrency

Native `asyncio` structured-concurrency primitives are the canonical baseline for in-process concurrent work.

In-process tasks remain process-lifetime work and must not be confused with durable jobs.

### STACK-02 — PostgreSQL driver and kernel persistence toolkit

**Status:** RATIFIED.

#### Driver

```text
Psycopg 3
```

Psycopg is the PostgreSQL driver and direct driver-level escape hatch for PostgreSQL protocol capabilities.

#### Persistence toolkit

```text
SQLAlchemy Core 2.x
```

SQLAlchemy Core is the default kernel persistence/query toolkit.

The kernel does not use SQLAlchemy ORM as persistence authority and does not depend on ORM `Session`, identity map, lazy loading, autoflush or ORM-owned Unit of Work semantics.

#### Unit of Work ownership

The semantic Unit of Work is owned by NETAUTO.

```text
one semantic Unit of Work
    -> one explicitly owned PostgreSQL connection/transaction

application/domain semantics
    -> determine transaction boundaries

persistence toolkit
    -> realizes those boundaries
```

No concurrent sibling operation independently uses the same semantic UoW connection/transaction.

#### Schema representation

The physical PostgreSQL schema is represented with SQLAlchemy Core metadata constructs:

```text
MetaData
Table
Column
PrimaryKey
ForeignKey
UniqueConstraint
CheckConstraint
Index
PostgreSQL-specific types/dialect constructs
```

SQLAlchemy is not a portability abstraction for NETAUTO. PostgreSQL-specific dialect features are permitted and expected where they match the architecture.

#### Runtime query policy

SQLAlchemy Core expressions are the default for ordinary DQL/DML, joins, filters, keyset pagination, schema references and composable predicates.

Textual PostgreSQL SQL is allowed when materially clearer or when a PostgreSQL mechanism is better represented directly, including advisory locks, complex recursive SQL or special PostgreSQL constructs.

Raw SQL remains inside the persistence/infrastructure boundary.

#### Driver escape hatch

Direct Psycopg access is permitted behind an explicit persistence boundary for driver/protocol capabilities where SQLAlchemy Core adds no value, such as future `COPY`, pipeline or measured specialized bulk paths.

Preferred hierarchy:

```text
ordinary persistence/query work
    -> SQLAlchemy Core

PostgreSQL SQL better expressed textually
    -> textual SQL through the persistence boundary

driver/protocol capability
    -> direct Psycopg access
```

#### Layer isolation

SQLAlchemy and Psycopg types do not cross into the domain model.

Application/domain code does not build SQLAlchemy statements or depend on SQLAlchemy `Table`/`Column` objects.

#### Migrations

```text
Alembic
+
the same SQLAlchemy MetaData
```

is the project migration baseline.

Alembic autogeneration is advisory only:

```text
autogenerate
    -> candidate migration
    -> mandatory review
    -> final migration
```

#### Performance policy

Core expressions are not replaced with raw SQL/Psycopg based on speculative performance assumptions. Measured hot paths may use the textual-SQL or driver escape hatch when benchmarks demonstrate material benefit and semantics remain aligned.

### STACK-03 — Pydantic and model boundaries

**Status:** RATIFIED.

#### Transport technology

```text
Pydantic 2.x
```

is the canonical FastAPI request/response model technology.

Public HTTP request and response DTOs use Pydantic at the transport boundary. Pydantic is not the NETAUTO domain-model framework.

#### Request-model strictness

```text
strict validation
unknown fields forbidden
no generic scalar coercion
field omission preserved distinctly from explicit null/value
```

Transport mapping preserves caller intent until conversion into application-command semantics. It may validate carrier shape but may not silently repair or reinterpret explicit invalid input.

#### Validation authority boundary

Pydantic owns transport syntax and shape validation, including JSON object shape, required/forbidden fields, discriminated request variants, strict carrier types, basic public structural bounds and response serialization.

Pydantic does not replace:

```text
PrimitiveType parsing/canonicalization
DataTypeVersion constraint semantics
ObjectTemplate certification/effective-schema validation
Object runtime-state validation
schema-change migration semantics
ownership/Relationship invariants
lifecycle/default/dependency admission
current-state-dependent validation
```

A convenient Pydantic built-in type must not narrow or widen a frozen NETAUTO lexical/domain contract.

#### Application command/result boundary

```text
HTTP JSON
    -> Pydantic request DTO
    -> explicit intent-preserving mapping
    -> application command
    -> domain/application execution
    -> application result/semantic projection
    -> explicit transport mapping
    -> Pydantic response DTO
    -> HTTP JSON
```

Application commands/results use ordinary Python types, dataclasses, enums or project value objects. The application layer has no FastAPI dependency and does not use Pydantic as semantic authority.

#### Domain isolation

The domain model is plain Python and has no Pydantic dependency.

#### Response DTO boundary

Persistence rows, SQLAlchemy rows or driver-specific objects are never exposed directly as public DTOs.

```text
persistence representation
    -> application/domain semantic representation or projection
    -> explicit response mapping
    -> Pydantic response DTO
```

#### Failure taxonomy ownership

Pydantic/FastAPI validation errors do not redefine the NETAUTO error taxonomy. The transport adapter maps transport-model failures into the ratified public failure boundary.

#### Configuration is a separate boundary

Pydantic use for process settings is a distinct decision in `STACK-04`.

### STACK-04 — process configuration and settings

**Status:** RATIFIED.

#### Settings technology

```text
pydantic-settings 2.x
```

is the baseline for typed process/deployment configuration.

It does not make Pydantic the domain-model authority and does not define future NETAUTO-managed application resources.

#### Configuration scope

Process settings contain only values required to compose and operate the current process, for example PostgreSQL connection URL, pool/runtime settings, logging settings, infrastructure timeouts or process secrets when actual consumers exist.

Future domain/application configuration managed by NETAUTO should normally be explicit application resources rather than an unbounded environment-variable surface.

#### Lifecycle and fail-fast behavior

```text
process starts
    -> load settings
    -> validate complete settings
    -> construct infrastructure/application
    -> serve
```

Missing or invalid required configuration fails startup. Settings are not import-time global side effects and are immutable for the process lifetime. Runtime reload is not part of the baseline.

#### Sources and precedence

Production configuration is environment-first with prefix:

```text
NETAUTO_
```

Precedence:

```text
1. explicit constructor/test injection
2. real environment variables
3. mounted secret files
4. explicitly enabled local dotenv input
5. safe code defaults
```

The source order is configured explicitly.

#### Dotenv policy

`.env` is local development/testing convenience only. Production does not depend on dotenv or implicit parent-directory discovery.

#### Secrets

Secrets may be supplied through environment variables or mounted secret files. No project-wide Vault/cloud-secret-manager SDK is selected. Secrets are never emitted in normal logging.

#### No project runtime configuration-file framework

The project does not adopt a canonical TOML/YAML/INI runtime configuration hierarchy or internal `development`/`staging`/`production` profile system.

#### Dependency boundary

`pydantic-settings` belongs to composition/infrastructure. Domain code has no dependency on process settings; application services receive concrete injected dependencies.

#### Testing and database separation

Tests construct/inject configuration explicitly and do not mutate a shared settings singleton. Runtime and test PostgreSQL configuration remain separate.

#### Safe observability

Startup may emit a small safe non-secret configuration summary. Diagnostic source tracing must not become normal production logging.

#### Proportionality

The technology baseline defines the allowed mechanism; it does not require speculative settings or hierarchy.

```text
current requirement
    -> current setting

future possibility without current consumer
    -> no setting yet
```

The current implementation therefore contains only settings consumed by the delivered runtime or tests. Future cycles add settings only when a real consumer requires them.

### STACK-05 — dependency injection and composition root

**Status:** RATIFIED.

#### Composition model

NETAUTO uses explicit Python dependency injection. Constructor/function injection is preferred. No external DI/container framework is part of the current baseline.

#### FastAPI dependency boundary

FastAPI `Depends()` is an HTTP-adapter mechanism, not the authority for constructing the application/domain object graph.

It may serve request/transport concerns or access already-composed capabilities. Domain, application and persistence code do not depend on FastAPI `Depends()`.

#### Composition root

Process/application wiring is explicit at a composition/bootstrap root:

```text
process startup
    -> load validated Settings
    -> create AsyncEngine / PostgreSQL pool
    -> create UoW/application factories and stateless services
    -> create FastAPI application/adapters
    -> serve
```

FastAPI lifespan may own process-lifetime resources but does not redefine transaction semantics.

A project-specific `Container` abstraction is not required while the object graph remains directly readable.

#### Lifecycle/scoping rules

```text
process lifetime
    -> Settings
    -> AsyncEngine / connection pool
    -> factories
    -> stateless application services where appropriate

HTTP request lifetime
    -> transport/request context
    -> future principal/correlation metadata

semantic operation lifetime
    -> Unit of Work
    -> PostgreSQL connection/transaction
    -> operation-specific persistence access

domain lifetime
    -> ordinary Python objects governed by domain semantics
```

These lifetimes are not collapsed into one framework request scope.

#### Unit of Work is not request-scoped infrastructure

```text
HTTP/CLI/worker caller
    -> application operation
    -> UoW factory
    -> semantic UoW / transaction
    -> commit or rollback
```

An HTTP request often invokes one UoW, but this coincidence is not an architecture rule. FastAPI dependency `yield` lifecycle does not own transaction semantics.

#### Process resources and globals

Mutable import-time global singletons and service-locator access are not part of the baseline. Stateless application services may be process-lived; each I/O-bearing operation creates its own UoW.

#### Testing rule

Domain/application tests construct dependencies directly. FastAPI `dependency_overrides` is reserved for API-adapter/integration tests.

#### Future DI/container reconsideration

A DI/container framework may be reconsidered only when concrete composition complexity demonstrates need. It is not introduced speculatively.

### STACK-06 — logging and minimal observability

**Status:** RATIFIED.

#### Logging technology

```text
Python stdlib logging
```

is the baseline. No structured-logging framework is selected. Configuration is centralized at bootstrap; modules do not install their own handlers.

#### Logging ownership

Pure domain code should not normally log. Expected semantic failures are not `ERROR` merely because an HTTP response is unsuccessful.

Unexpected/internal failures are logged once at the outer handling boundary with appropriate exception context. Repeated logging at repository, application and HTTP layers is avoided.

#### Levels and volume

```text
DEBUG   -> diagnostic detail
INFO    -> meaningful process/infrastructure lifecycle
WARNING -> abnormal but handled condition
ERROR   -> unexpected/internal failure requiring attention
```

Routine successful commands are not automatically logged at `INFO`.

#### Request correlation

The HTTP adapter may assign a lightweight request identifier via `contextvars` or equivalent standard-library mechanism. It is transport metadata, not domain/transaction/lifecycle identity.

This is the only request-correlation mechanism required by the current baseline.

#### Log format

The default format is human-readable text. Application code emits standard `LogRecord` events; formatter choice remains bootstrap/deployment concern.

#### SQL and access logging

SQL logging is disabled normally and may be enabled diagnostically at `DEBUG`. Uvicorn access logging is the current HTTP access-log baseline.

#### Sensitive data

Secrets and unrestricted request/persistence/application state are not intentionally logged. Prefer identifiers and bounded context.

#### Deferred observability capabilities

The current baseline does not select:

```text
OpenTelemetry / distributed tracing
Prometheus or another metrics framework
structured-logging framework
application-wide JSON logging contract
custom tracing/span framework
```

These require concrete operational requirements and must not be anticipated through speculative application/domain abstractions.

#### Proportionality

Current realization may remain limited to centralized stdlib logging, startup/shutdown and unexpected-error logging, lightweight request correlation and existing Uvicorn access logging.

### STACK-07 — kernel testing stack and verification strategy

**Status:** RATIFIED.

Testing is part of the kernel correctness/safety model. Complementary layers preserve the current semantic, persistence, concurrency and API contracts; no one layer substitutes for the others.

#### Test layers

```text
T0  pure domain unit tests
T1  application/orchestration tests
T2  real-PostgreSQL persistence integration tests
T3  deterministic real-PostgreSQL concurrency contract tests
T4  API contract/integration tests
T5  migration/schema tests
T6  targeted property-based tests
T7  supplementary stress/randomized concurrency tests
```

T0..T5 are normal kernel layers. T6 applies where meaningful semantic properties exist. T7 is supplementary discovery tooling.

#### Core runner and async testing

```text
pytest
pytest-asyncio
```

are canonical. Async tests follow the asyncio model. Function-scoped event-loop isolation is default unless a fixture lifecycle justifies broader scope.

Markers are explicitly registered and strict-marker behavior is enabled.

#### API testing

API tests use:

```text
HTTPX AsyncClient
+
ASGITransport
```

against the composed FastAPI application. Tests that exercise startup/shutdown run the real ASGI lifespan.

#### Real PostgreSQL requirement

Persistence, migration, integration and concurrency guarantees attributed to PostgreSQL are tested against real PostgreSQL, not SQLite, fake databases or in-process transaction simulation.

Mocks/fakes remain acceptable only for behavior genuinely independent of PostgreSQL.

#### PostgreSQL provisioning boundary

NETAUTO test code does not provision PostgreSQL. Excluded:

```text
Docker-based test provisioning
Testcontainers
auto-started embedded/local PostgreSQL
silent fallback to another backend
```

The environment supplies a dedicated target through `TEST_DATABASE_URL`. Absence/invalidity fails PostgreSQL-required commands clearly.

#### Test-database isolation and parallelism

```text
parallel real-PG worker
    -> isolated PostgreSQL test database

scenario
    -> unique semantic IDs/names
    -> cleanup after participating sessions terminate
```

When only one database exists, interfering PostgreSQL suites run without cross-worker DB parallelism. Pure tests may be parallelized when independent.

#### Parallel test runner

`pytest-xdist` is available but cannot weaken isolation. Deterministic worker orchestration inside one scenario belongs to the concurrency harness, not xdist scheduling.

#### Deterministic concurrency harness

The current kernel includes reusable test infrastructure for the canonical PostgreSQL concurrency contract:

```text
CTL
OBS
optional blocker B
T1 / T2 / optional T3
stable scenario IDs
deterministic barriers/phases
PostgreSQL blocker/wait observation
failure diagnostics
```

Real blockers/gates/constraints are preferred. `sleep()` is never a correctness coordination primitive. Test-only interception is permitted only under the narrow architecture escape hatch and cannot create a different production path.

Normative scenarios are not automatically rerun to hide flakes. Retry/convergence is tested only when part of the operation contract.

#### Timeout safety

```text
pytest-timeout
```

is part of the test safety toolset so a broken concurrency test cannot hang CI indefinitely.

Timeouts prevent hangs; they do not establish race ordering, blocking or non-blocking semantics.

#### Property-based testing

`Hypothesis` is part of the baseline and is used selectively for meaningful properties such as primitive canonicalization, decimal/datetime/IP/byte-size handling, constraint combinations, cursor codecs and pure migration transformations.

#### Coverage

`coverage.py` with branch coverage is diagnostic evidence, not semantic correctness. Critical gaps are addressed through risk and traceability rather than an arbitrary percentage alone.

#### Migration/schema verification

A clean real PostgreSQL database must prove:

```text
empty/clean schema
    -> Alembic upgrade head
    -> expected usable schema
    -> no unexplained drift from authoritative MetaData
```

A migration file existing is not execution evidence.

#### Stress/randomized concurrency

Stress testing is supplementary. A discovered race is reduced, where reasonably possible, to a deterministic reproducer with stable contract coverage.

#### Traceability and regression

Tests implementing explicit architecture contracts retain discoverable traceability. Canonical concurrency scenario IDs remain visible in test organization/metadata.

Preferred defect workflow:

```text
defect / race discovered
    -> deterministic failing regression when reasonably possible
    -> architecture realignment if required
    -> implementation fix
    -> permanent regression coverage
```

### STACK-08 — Python and development quality toolchain

**Status:** RATIFIED.

#### Python runtime

```text
CPython 3.14.x
```

is the single supported minor baseline, represented as:

```text
>=3.14,<3.15
```

Development, CI, deployment, Ruff and Pyright target the same minor baseline. Supporting another minor requires explicit technology review and applicable full verification.

#### Project/dependency management

```text
uv
```

is canonical for runtime selection support, environment synchronization, dependency resolution/groups, lockfile maintenance and command execution.

`uv.lock` is committed and is the canonical exact resolution. Project metadata expresses compatibility intent; CI/deployment use locked synchronization.

#### Build backend and layout

```text
Hatchling
```

remains the build backend and the `src/` layout is retained.

#### Linting, formatting and imports

```text
Ruff
```

is the single formatter/linter/import-ordering tool. Black, isort, Flake8 or overlapping authorities are not added.

Rules are curated; suppressions are narrow and justified. Local and CI use the same configuration.

#### Static type checking

```text
Pyright strict
```

is the single type-checker authority for `src` and `tests`. Mypy is not a second project-wide checker. Exceptions for dynamic/third-party boundaries are local and justified.

#### Configuration location

Tool configuration is centralized in `pyproject.toml` where supported. Extra config files require concrete justification.

#### Canonical execution model

Developer and CI workflows use the project environment through `uv`, conceptually:

```text
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest ...
```

Exact selections derive from the active cycle and project configuration. Local and CI must not maintain hidden divergent policies.

#### Dependency upgrades

Dependency updates are explicit reviewed changes. Lockfile changes pass applicable verification; generic automatic merging is not part of the baseline.

#### Pre-commit policy

Pre-commit hooks are optional convenience, not correctness authority. CI remains authoritative enforcement.

#### Alignment state

The current `pyproject.toml`, `.python-version` and `uv.lock` are the delivered realization of the ratified Python/toolchain baseline. Future changes update these artifacts coherently and are reviewed like code.

### STACK-09 — process entrypoints and ASGI serving

**Status:** RATIFIED.

#### ASGI server

```text
Uvicorn
```

is the ASGI serving baseline.

NETAUTO uses an explicit application factory rather than import-time process composition:

```text
Uvicorn
    -> explicit application factory
    -> load/validate settings
    -> compose application
    -> FastAPI/ASGI lifespan
    -> serve
```

Direct Uvicorn invocation is preferred over an additional discovery/wrapper CLI layer.

#### Process and worker model

Kernel correctness is independent of serving process count. Multiple processes remain correct through PostgreSQL; process-local locks, mutable globals, caches or registries never become cross-process invariant authority.

Worker count is deployment concern.

#### Process manager

No separate project process manager is selected. Gunicorn is not a dependency or serving requirement. Supervision, restart and replica count belong to deployment unless a future requirement says otherwise.

#### ASGI lifespan

Lifespan initializes and cleans process-local resources such as the engine/pool. It does not define semantic transaction boundaries.

#### Database migrations

Migration is explicit administration. Application startup, factory construction and lifespan do not execute Alembic upgrades.

```text
explicit migration/admin step
    -> schema at intended revision
    -> start/replace serving processes
```

#### Development reload

Uvicorn reload is local convenience, not production model or application capability.

#### Server/deployment configuration boundary

Host, port, worker count, reload and proxy/server behavior belong to Uvicorn/deployment configuration unless a concrete application-composition requirement transfers ownership.

TLS termination, reverse proxy and ingress topology remain deployment concerns.

#### Custom NETAUTO CLI

The current baseline has no custom operator CLI merely wrapping existing tools:

```text
serve               -> Uvicorn
schema migrations   -> Alembic
tests               -> pytest
project commands    -> uv
```

`Typer` is not part of the current dependency baseline. A future real operator CLI requires a concrete NETAUTO-specific command surface and remains an adapter over application capabilities.

#### Signals and graceful shutdown

Uvicorn/ASGI owns serving signals and graceful shutdown. Application lifespan cleans only resources NETAUTO owns.

## 4. Evolution rule

Technology choices are reviewed one decision point at a time.

A new choice becomes authoritative only after explicit ratification and consolidation in this file. If it affects current semantic or technical architecture, the appropriate milestone/fix documents and AS-IS must be reopened or evolved through the project governance process before implementation.
