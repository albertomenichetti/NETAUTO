# NETAUTO — Technology Baseline

**Status:** DRAFT — project-wide technology review in progress. `STACK-01`, `STACK-02`, `STACK-03`, `STACK-04`, `STACK-05`, `STACK-06`, `STACK-07` and `STACK-08` are ratified; other technology decisions remain open until explicitly ratified.

## 1. Scope and authority

This document defines project-wide implementation technology choices that are not milestone-specific domain architecture.

It is subordinate to frozen milestone contracts and architecture for semantic behavior: a technology choice may implement a frozen contract but may not reinterpret it.

`docs/wip/` remains non-normative working space. Technology decisions become authoritative only when consolidated here.

## 2. Already fixed project constraints

The current project baseline assumes:

```text
language
    -> Python

public API framework
    -> FastAPI / ASGI

persistence database
    -> PostgreSQL
```

These are not reopened by the current technology review.

The remaining application/infrastructure libraries, middleware and tooling are reviewed independently.

## 3. Decision registry

### STACK-01 — application/infrastructure execution model

**Status:** RATIFIED.

#### Async runtime

```text
native asyncio
```

is the project asynchronous execution baseline.

FastAPI/Starlette remain the ASGI web/runtime boundary. AnyIO may be used where it is natural or useful at that boundary or in infrastructure integrations, but portability across asyncio/Trio is not a project requirement.

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

The project avoids hidden/lazy I/O that makes a normal attribute/function access unexpectedly require database or network activity.

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

This preserves the frozen mutation/locking semantics while allowing the event loop to schedule unrelated work during database/network waits.

#### Mixed sync/async application

The project may contain both synchronous and asynchronous APIs/functions where their workloads justify it.

This is intentional and supported by the FastAPI/ASGI runtime.

The rule is semantic rather than endpoint-by-endpoint convenience:

```text
I/O-bearing application/infrastructure operation
    -> async

pure computation
    -> sync

blocking integration
    -> explicit bounded offload boundary
```

The project avoids repeated arbitrary sync/async boundary crossings inside one operation.

#### Ordinary request/response vs long-running work

Asynchronous server execution does **not** imply asynchronous HTTP semantics for callers.

Ordinary kernel commands remain normal request/response operations: the client sends a request and waits for the resulting HTTP response.

`async def` is an implementation execution model and does not by itself introduce `202 Accepted`, background jobs, polling or event streams.

This preserves the frozen M1 public API contract, which does not expose asynchronous kernel command status.

#### Future long-running operation principle

Future capabilities such as discovery, reconciliation, configuration campaigns or automation may introduce semantic operations whose lifetime exceeds one request.

Those operations must not be represented merely by detached in-process `asyncio` tasks.

When such a requirement appears, the project should introduce an explicit durable resource such as a conceptual `Job`, `Run` or `Execution` with authoritative persisted state.

The concrete worker/queue technology is intentionally **not selected yet**. Requirements such as durability, retries, scheduling, priority, distribution and throughput must drive that future decision.

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

Polling/read semantics are the robust baseline because they allow any HTTP client to recover authoritative current state after disconnects or missed notifications.

Server-Sent Events may be introduced when low-latency unidirectional progress/event delivery is useful, especially for UI or operator experience.

SSE must not be the only way to determine the final/current job state.

WebSocket is not a project baseline. It should be introduced only when a real bidirectional persistent-communication requirement exists.

#### Structured concurrency

Native `asyncio` structured-concurrency primitives are the canonical baseline for in-process concurrent work.

In-process tasks remain process-lifetime work and must not be confused with durable jobs.

### STACK-02 — PostgreSQL driver and kernel persistence toolkit

**Status:** RATIFIED.

#### Driver

```text
Psycopg 3
```

Psycopg is the PostgreSQL driver and remains the direct driver-level escape hatch for PostgreSQL protocol/driver capabilities.

#### Persistence toolkit

```text
SQLAlchemy Core 2.x
```

SQLAlchemy Core is the default kernel persistence/query toolkit.

The kernel does **not** use SQLAlchemy ORM as its persistence authority.

In particular, the kernel does not depend on ORM `Session`, identity-map, lazy-loading, autoflush or ORM-owned Unit of Work semantics.

#### Unit of Work ownership

The semantic Unit of Work is owned by NETAUTO, not by SQLAlchemy ORM.

Under `STACK-01`, the kernel persistence path is asynchronous and uses an explicitly owned async connection/transaction.

The invariant is:

```text
one semantic Unit of Work
    -> one explicitly owned PostgreSQL connection/transaction

application/domain semantics
    -> determine transaction boundaries

persistence toolkit
    -> realizes those boundaries
```

No concurrent sibling operation may independently use the same semantic UoW connection/transaction.

#### Schema representation

The physical PostgreSQL schema is represented programmatically with SQLAlchemy Core metadata constructs:

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

SQLAlchemy is **not** a database-portability abstraction for NETAUTO.

PostgreSQL remains the only persistence target and PostgreSQL-specific SQLAlchemy dialect features are explicitly permitted and expected where they match the frozen architecture.

#### Runtime query policy

Default:

```text
SQLAlchemy Core expressions
```

for ordinary DQL/DML, joins, filters, keyset pagination, schema references and composable predicates.

Core is the default, not an absolute rule.

Textual PostgreSQL SQL is explicitly allowed when it is materially clearer or when a PostgreSQL mechanism is better represented directly.

Examples include, where appropriate:

```text
advisory-lock statements
complex recursive SQL
special PostgreSQL constructs
queries whose Core expression would obscure rather than clarify semantics
```

Raw SQL should remain inside the persistence/infrastructure boundary.

#### Driver escape hatch

Direct Psycopg access is permitted behind an explicit persistence boundary for driver/protocol capabilities where SQLAlchemy Core adds no value, including possible future paths such as:

```text
COPY
pipeline/protocol-specific operations
measured specialized bulk paths
```

This is an escape hatch, not a parallel general-purpose persistence style.

The preferred hierarchy is:

```text
ordinary persistence/query work
    -> SQLAlchemy Core

PostgreSQL SQL better expressed textually
    -> textual SQL through the same persistence boundary

driver/protocol capability
    -> direct Psycopg access
```

#### Layer isolation

SQLAlchemy and Psycopg types do not cross into the domain model.

Application/domain code does not build SQLAlchemy statements or depend on SQLAlchemy `Table`/`Column` objects.

Query construction belongs to the persistence/infrastructure layer.

#### Migrations

```text
Alembic
+
the same SQLAlchemy MetaData
```

is the project migration baseline for the PostgreSQL schema.

Alembic autogeneration is advisory only:

```text
autogenerate
    -> candidate migration
    -> mandatory review
    -> final migration
```

No generated migration is authoritative merely because Alembic produced it.

#### Performance policy

The project does not replace Core expressions with raw SQL/Psycopg based on speculative performance assumptions.

Measured hot paths may use the textual-SQL or driver escape hatch when benchmarks demonstrate material benefit and the resulting implementation remains consistent with the frozen semantic/persistence architecture.

### STACK-03 — Pydantic and model boundaries

**Status:** RATIFIED.

#### Transport technology

```text
Pydantic 2.x
```

is the canonical FastAPI request/response model technology.

Public HTTP request DTOs and public HTTP response DTOs use Pydantic models at the transport boundary.

Pydantic is selected because it integrates naturally with FastAPI request parsing, response serialization/filtering and OpenAPI generation. It is not selected as the NETAUTO domain-model framework.

#### Request-model strictness

Public request models preserve the frozen API wire semantics.

The baseline is:

```text
strict validation
unknown fields forbidden
no generic scalar coercion
field omission preserved distinctly from explicit null/value
```

Transport mapping must preserve caller intent until it has been converted into the corresponding application command semantics.

A request model may validate public carrier shape and structural wire constraints, but it may not silently repair or reinterpret explicit invalid intent.

#### Validation authority boundary

Pydantic is responsible for transport syntax and shape validation, including, where applicable:

```text
JSON/request object shape
required/forbidden transport fields
discriminated request variants
strict carrier types
basic public structural bounds
response serialization/public shape
```

Pydantic is **not** authoritative for NETAUTO semantic validation.

In particular, Pydantic must not replace:

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

A convenient Pydantic built-in type must not narrow, widen or otherwise redefine a frozen NETAUTO lexical/domain contract.

When the NETAUTO public wire contract defines a carrier such as a string whose semantic parsing is owned by the domain/application layer, the transport model should preserve that carrier rather than delegating semantic interpretation to Pydantic.

#### Application command/result boundary

Transport DTOs are not application commands merely because their fields look similar.

The canonical flow is:

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

Application commands/results use ordinary Python types, dataclasses, enums and/or project value objects as appropriate.

The application layer has no FastAPI dependency and does not use Pydantic as its semantic model authority.

Pydantic dependency in the application layer is not part of the project baseline and should not be introduced merely to avoid an explicit transport/application mapping.

#### Domain isolation

The domain model is plain Python and has no Pydantic dependency.

Domain entities, value objects, candidate state, invariant evaluation and canonicalization do not inherit from `BaseModel` and do not use Pydantic serialization/validation as their semantic representation.

The domain therefore remains reusable independently of HTTP, FastAPI and Pydantic.

#### Response DTO boundary

Pydantic response models are an explicit public-boundary projection and provide a defensive serialization/filtering boundary.

Persistence rows, SQLAlchemy rows or driver-specific objects are never exposed directly through Pydantic response serialization as an architectural shortcut.

The expected flow is:

```text
persistence representation
    -> application/domain semantic representation or projection
    -> explicit response mapping
    -> Pydantic response DTO
```

This keeps the public API independent of physical persistence shape.

#### Failure taxonomy ownership

Pydantic/FastAPI validation errors do not redefine the frozen NETAUTO error taxonomy.

Transport/shape failures, semantic validation failures, state conflicts and internal failures remain classified according to the application/API contracts.

In particular, the existence of a Pydantic `ValidationError` does not by itself determine that the public failure is `semantic_validation_failed` or any other semantic code.

The transport adapter owns the mapping from transport-model failures into the ratified public failure boundary.

#### Configuration is a separate boundary

Use of Pydantic for application configuration/settings is a distinct technology decision and is not implied by STACK-03.

Configuration parsing/validation will be reviewed separately because external configuration is a different boundary from public HTTP DTOs.

### STACK-04 — process configuration and settings

**Status:** RATIFIED.

#### Settings technology

```text
pydantic-settings 2.x
```

is the project baseline for typed process/deployment configuration.

This choice applies to configuration of the running NETAUTO process. It does not make Pydantic the domain-model authority and does not define how future NETAUTO-managed application resources such as discovery definitions, connector configuration or automation policy are modeled.

#### Configuration scope

Process settings include only values required to compose and operate the process, for example as requirements emerge:

```text
PostgreSQL connection URL
connection-pool/runtime infrastructure settings
logging settings
HTTP/server process settings
infrastructure timeouts
process-level secrets
```

Future domain/application configuration managed by NETAUTO itself should normally be represented as explicit application resources rather than accumulated indefinitely as environment variables.

#### Lifecycle and fail-fast behavior

Settings are constructed and validated explicitly during process bootstrap/composition.

The canonical lifecycle is:

```text
process starts
    -> load settings
    -> validate complete settings
    -> construct infrastructure/application
    -> serve
```

Missing required configuration or invalid values fail process startup before the application is declared operational.

Settings are not instantiated as import-time global side effects.

After successful composition, process settings are treated as immutable for the lifetime of that process. Runtime mutation/reload is not part of the baseline; configuration changes require explicit recomposition/restart unless a future requirement introduces a separate dynamic-configuration design.

#### Sources and precedence

Production deployment configuration is environment-first, using the project prefix:

```text
NETAUTO_
```

The intended precedence is:

```text
1. explicit constructor/test injection
2. real environment variables
3. mounted secret files
4. explicitly enabled local dotenv input
5. safe code defaults
```

The source order should be configured explicitly rather than depending accidentally on library defaults.

Environment parsing may perform controlled conversion from string carriers into typed process settings. This is intentionally different from the strict no-coercion public HTTP boundary defined by STACK-03.

#### Dotenv policy

A `.env` file is a local development/testing convenience only.

Production operation must not depend on a dotenv file, and NETAUTO does not rely on implicit parent-directory discovery of dotenv configuration.

If dotenv support is enabled for a local entry point, that behavior is explicit at the composition/bootstrap boundary.

#### Secrets

Process secrets may be supplied through environment variables or mounted secret files.

NETAUTO does not select a project-wide Vault/cloud-secret-manager SDK as part of this baseline. The deployment environment remains responsible for making required secrets available to the process through a supported source.

Secrets must never be emitted in normal startup/configuration logging.

#### No project runtime configuration-file framework

The project does not adopt TOML, YAML, INI or another project runtime configuration-file hierarchy as a canonical process-configuration source.

Likewise, NETAUTO does not implement an internal layered `development` / `staging` / `production` configuration system. The deployment environment already determines the concrete settings supplied to the process.

A future configuration-document requirement may be evaluated on its own merits rather than pre-building one now.

#### Dependency boundary

`pydantic-settings` belongs to composition/infrastructure.

Domain code has no dependency on process settings or `pydantic-settings`. Application services receive the concrete infrastructure/contracts they require rather than reading process-global settings directly.

#### Testing and database separation

Tests construct/inject configuration explicitly and do not mutate a shared settings singleton.

Runtime and test PostgreSQL configuration remain separate. Test composition must use the dedicated test database configuration rather than silently inheriting the runtime database target.

#### Safe observability

Startup may emit a small safe summary of operationally useful non-secret configuration.

Diagnostic source tracing, if used during troubleshooting, must not become normal production logging because configuration-source diagnostics may expose sensitive values.

#### Proportionality / M1 implementation rule

The technology baseline defines the allowed configuration mechanism; it does **not** require speculative settings or configuration structure.

M1 should introduce only settings that are actually consumed by M1 runtime/test composition.

In particular, M1 must not create nested settings groups, secret backends, reload machinery, deployment profiles, generic configuration registries or placeholder settings merely to anticipate later milestones.

The rule is:

```text
current requirement
    -> current setting

future possibility without current consumer
    -> no setting yet
```

This keeps the M1 configuration surface intentionally minimal while preserving a project-wide mechanism that can grow when real requirements appear.

### STACK-05 — dependency injection and composition root

**Status:** RATIFIED.

#### Composition model

NETAUTO uses explicit Python dependency injection as the project composition baseline.

Constructor/function injection is preferred. Dependency injection is treated as a design principle; a DI container is only one possible mechanism and is not required for the project baseline.

The project does **not** adopt an external DI/container framework at this stage.

#### FastAPI dependency boundary

FastAPI `Depends()` is an HTTP-adapter mechanism, not the authority for constructing the NETAUTO application/domain object graph.

It may be used for transport/request concerns such as:

```text
request context
future authentication/authorization context
HTTP-derived parameters or metadata
access to already-composed application capabilities
```

Domain, application and persistence code do not import or depend on FastAPI `Depends()`.

The project avoids recursive `Depends()` wiring for domain services, repositories, Unit of Work ownership or other core application composition merely because the framework can provide it.

#### Composition root

Process/application wiring is explicit at a composition/bootstrap root.

Conceptually:

```text
process startup
    -> load validated Settings
    -> create AsyncEngine / PostgreSQL pool
    -> create UoW/application factories and stateless services
    -> create FastAPI application/adapters
    -> serve
```

FastAPI lifespan may own initialization and cleanup of process-lifetime resources such as the database engine/pool, but framework lifecycle does not redefine application transaction semantics.

NETAUTO does not require a project-specific `Container` abstraction merely to wrap this wiring. M1 keeps composition directly readable while the object graph remains small.

#### Lifecycle/scoping rules

The project distinguishes lifetimes explicitly:

```text
process lifetime
    -> Settings
    -> AsyncEngine / connection pool
    -> factories
    -> stateless application services where appropriate

HTTP request lifetime
    -> transport/request-specific context
    -> future authentication principal / correlation metadata

semantic operation lifetime
    -> Unit of Work
    -> PostgreSQL connection/transaction
    -> operation-specific persistence access

domain lifetime
    -> ordinary Python objects governed by domain semantics
```

These lifetimes must not be collapsed merely because a framework offers one convenient request scope.

#### Unit of Work is not request-scoped infrastructure

A semantic NETAUTO Unit of Work is created and owned by the application operation that defines the transaction boundary.

The baseline is:

```text
HTTP/CLI/worker caller
    -> application operation
    -> UoW factory
    -> semantic UoW / transaction
    -> commit or rollback
```

An HTTP request may commonly invoke one application operation and therefore one UoW, but this coincidence is not an architectural rule.

FastAPI dependency `yield` lifecycle does not own or define transaction semantics for the kernel.

This keeps the same application operation callable from future CLI, worker, discovery, reconciliation or automation entry points without requiring FastAPI request lifecycle emulation.

#### Process resources and globals

Process-wide resources are composed explicitly and may be exposed to the HTTP adapter through an application/runtime context owned by the FastAPI application lifecycle.

Mutable import-time global singletons and service-locator access are not part of the baseline.

Application services that are stateless apart from injected factories/dependencies may be process-lived; each I/O-bearing semantic operation still creates its own operation-scoped UoW as required by STACK-01 and STACK-02.

#### Testing rule

Domain and application tests construct their dependencies directly and do not require a FastAPI application or FastAPI dependency overrides.

FastAPI `dependency_overrides` is reserved for API-adapter/integration tests where replacing an HTTP dependency is genuinely the boundary under test.

A useful architectural test is:

```text
if an application-service unit test requires FastAPI dependency_overrides
    -> the framework boundary is probably leaking inward
```

#### Future DI/container reconsideration

A DI/container framework may be reconsidered only if future composition complexity demonstrates a concrete need, for example a substantially larger dynamic/plugin-driven object graph that explicit Python wiring no longer represents clearly.

It is not introduced speculatively for M1 or merely to reduce a small amount of explicit bootstrap code.

### STACK-06 — logging and minimal observability

**Status:** RATIFIED.

#### Logging technology

```text
Python stdlib logging
```

is the project logging baseline.

NETAUTO does not adopt a structured-logging framework such as `structlog` as part of the baseline. Logging configuration is centralized at process/bootstrap composition; individual modules obtain normal hierarchical loggers and do not install their own handlers or configure the logging system independently.

#### Logging ownership

Pure domain code should not normally produce logging side effects.

Domain/application semantics are expressed through returned values and project/domain failures. Application, transport and infrastructure boundaries decide which operationally meaningful events require logging.

Expected application outcomes such as normal not-found, semantic-validation or state-conflict responses are not `ERROR` merely because they are unsuccessful HTTP responses.

Unexpected/internal failures are logged once, at the outer boundary where they are finally handled or leave the process, with exception context when appropriate. The project avoids repeated logging of the same exception at repository, application and HTTP layers.

#### Log levels and volume

The baseline uses the standard logging levels according to operational significance:

```text
DEBUG
    -> diagnostic detail

INFO
    -> meaningful process/infrastructure lifecycle events

WARNING
    -> abnormal but handled operational conditions

ERROR
    -> unexpected/internal failures requiring operator attention
```

Ordinary successful kernel commands are not automatically logged at `INFO`; the project avoids turning routine application traffic into high-volume application logs without an operational requirement.

#### Request correlation

The HTTP adapter may assign a lightweight request identifier and make it available to logging context through Python `contextvars` or an equivalently small standard-library mechanism.

The request identifier is transport/infrastructure observability metadata only. It does not become a domain/application identifier, does not define transaction identity and does not modify lifecycle-event semantics.

This lightweight correlation is the only request-tracing mechanism required by the M1 baseline.

#### Log format

The default M1 log format is ordinary human-readable text.

Application code emits standard `logging.LogRecord` events and does not depend on a project-specific structured-event API. Formatters remain a bootstrap/deployment concern, so a future deployment may adopt JSON or another formatter without rewriting domain/application code.

#### SQL and access logging

SQLAlchemy/driver SQL logging is disabled during normal operation and may be enabled diagnostically at `DEBUG` when required. Normal application logging must not duplicate every SQL statement.

HTTP access logging uses the Uvicorn/runtime baseline unless a concrete operational requirement demonstrates that NETAUTO needs a different access-log implementation.

#### Sensitive data

Secrets and other values designated sensitive by an integration must never be intentionally emitted to normal logs.

Logging/exception code should prefer identifiers and bounded diagnostic context over unrestricted serialization of request bodies, persistence rows or application state.

#### Deferred observability capabilities

The project does not select the following as part of M1 or the current technology baseline:

```text
OpenTelemetry / distributed tracing
Prometheus or another metrics framework
structured-logging framework
application-wide JSON logging contract
custom tracing/span framework
```

These capabilities may be introduced later from concrete operational requirements and measured need. Their absence from M1 must not be compensated by speculative abstractions in application/domain code.

#### Proportionality / M1 implementation rule

M1 implements only the logging/observability support it actually consumes.

A sufficient M1 realization may consist of:

```text
centralized stdlib logging configuration
small startup/shutdown and unexpected-error logging
lightweight request_id middleware/context
existing Uvicorn access logging
```

No observability framework, metrics registry, tracing abstraction or structured-event layer is created merely to anticipate future deployment needs.

### STACK-07 — kernel testing stack and verification strategy

**Status:** RATIFIED.

Testing is part of the kernel correctness/safety model, not merely developer tooling. The M1 implementation must preserve the frozen semantic, persistence, concurrency and API contracts through complementary test layers; no single class of test substitutes for the others.

#### Test layers

The baseline distinguishes:

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

T0..T5 are normal kernel verification layers. T6 is part of the M1 baseline where meaningful semantic properties exist. T7 is supplementary discovery tooling and does not replace deterministic contract tests.

#### Core runner and async testing

```text
pytest
pytest-asyncio
```

are the canonical test runner and asyncio test integration.

NETAUTO is asyncio-only at the project execution baseline, therefore async tests use the asyncio test model rather than maintaining test portability across Trio/other async backends.

Function-scoped event-loop isolation is the default unless a specific fixture lifecycle requires a broader scope. Asyncio debug mode may be enabled in CI/test profiles as an additional diagnostic guard rail.

Pytest markers used by the suite are explicitly registered and strict-marker behavior is enabled so misspelled/unregistered markers do not silently alter suite selection.

#### API testing

API tests use:

```text
HTTPX AsyncClient
+
ASGITransport
```

against the composed FastAPI ASGI application.

Tests that exercise application startup/shutdown must execute the real ASGI lifespan rather than assuming that transport construction implicitly runs it.

API contract tests verify the frozen public contract, including status codes, response DTOs, `Location` where required, strict request shape, omitted-vs-null behavior, failure taxonomy, cursor/list behavior, idempotent/convergent outcomes and committed database/lifecycle state where applicable.

#### Real PostgreSQL requirement

Persistence, migration, kernel integration and concurrency correctness are demonstrated against **real PostgreSQL**.

The suite does not use SQLite, fake databases, mock PostgreSQL behavior or in-process transaction simulation as substitutes for PostgreSQL semantics.

Mocks/fakes may be used for pure unit/application-boundary tests when the behavior being tested is genuinely independent of PostgreSQL. They are never evidence for row-lock, FK/PK/UNIQUE arbitration, MVCC, advisory-lock, transaction or rollback correctness.

#### PostgreSQL provisioning boundary

NETAUTO test code does **not** provision PostgreSQL.

Specifically, the project baseline excludes:

```text
Docker-based test provisioning
Testcontainers
auto-started embedded/local PostgreSQL
silent fallback to another database backend
```

The test environment/operator provides an already available dedicated PostgreSQL test target through:

```text
TEST_DATABASE_URL
```

The URL must identify test infrastructure distinct from runtime production/development persistence as required by the project configuration baseline.

Absence or invalidity of the required PostgreSQL test configuration must never cause fallback to SQLite or another backend. Commands intended to run the PostgreSQL-required suite must fail clearly when their required test database is unavailable; suite-selection commands may explicitly exclude PostgreSQL-marked tests.

#### Test-database isolation and parallelism

Concurrency scenarios use genuinely independent PostgreSQL connections/transactions and may commit real state; an outer rollback transaction is therefore not a sufficient isolation strategy.

The frozen PGTEST database-isolation contract remains authoritative:

```text
parallel real-PG worker
    -> isolated PostgreSQL test database

scenario
    -> unique semantic IDs/names
    -> cleanup only after participating sessions terminate
```

NETAUTO does not secretly create Docker containers or hidden PostgreSQL instances to satisfy this rule.

When the external test environment provides only one test database URL, PostgreSQL-required suites that could interfere through shared authority/gates run without cross-worker database parallelism. Parallel real-PG execution is enabled only when the environment explicitly provides/provisions isolated database targets per test worker (or equivalent externally managed isolation consistent with PGTEST).

Pure/unit tests remain freely parallelizable where they do not share mutable external state.

#### Parallel test runner

```text
pytest-xdist
```

is part of the testing toolset for scalable suite execution, but it is not allowed to weaken test isolation.

It may parallelize pure tests and real-PG tests only where the database-isolation contract is satisfied. Deterministic T1/T2/T3 transaction orchestration inside a concurrency scenario remains owned by the concurrency harness, never by xdist scheduling.

A test that depends accidentally on global shared state is defective; intentionally serial execution must be explicit and justified by the relevant authority/gate contract.

#### Deterministic concurrency harness

M1 implements reusable project-owned test infrastructure for the frozen PostgreSQL concurrency test architecture.

It realizes the canonical PGTEST roles and concepts, including:

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

Real PostgreSQL blockers/gates/constraints are the preferred orchestration mechanism. `sleep()` is never a correctness coordination primitive. Test-only persistence interception is permitted only under the narrow escape-hatch rules already frozen in PGTEST and must never create a different production semantic path.

The normative deterministic concurrency suite does not automatically rerun failed scenarios to make flakes disappear. Retry/convergence is tested only when it is part of the semantic operation contract itself.

#### Timeout safety

A pytest-level timeout/deadline guard (for example `pytest-timeout`) is part of the test safety tooling so broken concurrency tests cannot hang CI indefinitely.

Timeouts are safety nets only. They do not establish race ordering, blocking or non-blocking semantics; deterministic database/harness coordination does that.

#### Property-based testing

```text
Hypothesis
```

is part of the M1 testing baseline.

It is used selectively where a meaningful semantic property exists, especially for areas such as:

```text
PrimitiveType parsing/canonicalization
exact decimal lexical/canonical rules
datetime lexical/canonical rules
IP/prefix handling
byte-size parsing
constraint combinations
qualified-name/cursor codecs
pure schema/migration transformations
```

Property tests complement, rather than replace, explicit examples for frozen edge cases and contract cases.

#### Coverage

```text
coverage.py
```

with branch coverage is part of the test review toolset.

Coverage is diagnostic evidence, not the semantic definition of correctness. The project does not initially freeze an arbitrary percentage as a substitute for contract coverage. Critical untested branches in domain/application/persistence/error behavior are addressed based on risk and traceability rather than merely maximizing a scalar percentage.

#### Migration/schema verification

Migration tests use a clean real PostgreSQL test database and verify at minimum:

```text
empty/clean schema
    -> Alembic upgrade head
    -> expected usable schema
    -> no unexplained drift from authoritative SQLAlchemy MetaData
```

A migration file existing in the repository is not evidence that the migration executes correctly.

Future upgrade-path tests are added as persisted production schema history develops.

#### Stress/randomized concurrency

Stress/randomized concurrency testing is supplementary and may be selected separately from the deterministic CI contract suite.

A race discovered by stress testing is reduced, where reasonably possible, to a deterministic reproducer with stable contract coverage before/with the implementation fix. Stress success never substitutes for the canonical deterministic PGTEST scenarios.

Generic automatic reruns are not accepted as flakiness treatment for normative kernel tests.

#### Traceability

Tests that implement explicit frozen architecture contracts retain stable traceability to those contracts.

In particular, the canonical PGTEST scenario IDs remain visible in test organization/naming/metadata, and API/persistence contract tests should make the authority they exercise discoverable without requiring reconstruction from implementation details.

#### Regression rule

When a correctness defect is discovered in production, integration testing, stress testing or review, the preferred fix workflow is:

```text
defect / race discovered
    -> deterministic failing regression test when reasonably possible
    -> architecture realignment if the finding changes a frozen assumption
    -> implementation fix
    -> permanent regression coverage
```

The kernel does not rely on a code-only fix for a reproducible correctness defect.

### STACK-08 — Python and development quality toolchain

**Status:** RATIFIED.

#### Python implementation and supported runtime

NETAUTO targets:

```text
CPython 3.14.x
```

as the single supported Python minor-version baseline.

The project metadata expresses the supported range as:

```text
>=3.14,<3.15
```

The local development/runtime pin should identify Python 3.14 consistently with the project metadata.

NETAUTO is an application/kernel rather than a general-purpose compatibility library. Supporting additional Python minor versions is therefore not implicit. A move to a later minor version is an explicit project technology-baseline decision followed by the normal static-analysis and full test verification before the supported range is changed.

The intended invariant is:

```text
local development
CI
deployment/runtime
Ruff target
Pyright target
    -> the same supported CPython minor baseline
```

#### Project/dependency management

```text
uv
```

is the canonical project environment and dependency-management tool.

It owns the normal project workflow for:

```text
Python/runtime selection support
virtual environment synchronization
dependency resolution
dependency groups
lockfile maintenance
project command execution
```

The project commits `uv.lock` to Git. The lockfile is the canonical exact dependency resolution used to obtain reproducible development, CI and deployment environments.

Project metadata expresses dependency intent/compatibility bounds; exact resolved versions belong in `uv.lock` rather than being duplicated as exact pins throughout `pyproject.toml` without a specific need.

CI/deployment synchronization must use the committed lockfile in locked/frozen mode so a stale or missing lock update is detected rather than silently re-resolved.

#### Build backend and layout

```text
Hatchling
```

remains the build backend.

The existing `src/` package layout is retained.

`uv` project/dependency management and Hatchling build-backend responsibilities remain distinct; adopting `uv` is not a reason to change an otherwise adequate build backend.

#### Linting, formatting and import ordering

```text
Ruff
```

is the canonical tool for:

```text
linting
formatting
import ordering
```

The project does not add Black, isort, Flake8 or another overlapping formatter/linter merely to duplicate Ruff responsibilities.

The lint configuration uses a curated correctness/maintainability rule set appropriate to the codebase. It does not blindly enable Ruff `ALL`.

The baseline includes ordinary Python/error/import checks plus additional rule families with concrete value for a kernel codebase, including modern-Python, common-bug and asyncio-specific diagnostics where applicable.

Suppressions are narrow and justified. A noisy rule is evaluated explicitly rather than disabling an entire useful rule family solely for convenience.

Formatting and linting are CI correctness gates using the same configuration used locally.

#### Static type checking

```text
Pyright
```

is the single canonical static type checker.

The default project mode is:

```text
strict
```

for both `src` and `tests`.

The current kernel is developed under strict typing from the beginning rather than accumulating a broad `basic`-mode debt to be repaired later.

Type-checking exceptions for third-party typing limitations or genuinely dynamic boundaries must be local and justified. The project does not relax the whole codebase to accommodate one problematic integration.

Mypy is not a second CI type checker. Maintaining two independent project-wide type-checker authorities is not part of the baseline.

Tests are included in strict static analysis because test infrastructure, fixtures and especially the PostgreSQL concurrency harness are part of the kernel safety model.

#### Configuration location

Tool configuration is centralized primarily in `pyproject.toml` where the tool supports it.

The project avoids introducing additional `ruff.toml`, `pyrightconfig.json`, `pytest.ini`, `setup.cfg` or equivalent files unless a concrete limitation or clarity need justifies separating a configuration later.

#### Canonical developer and CI execution model

Developer and CI workflows use the project environment through `uv`, conceptually:

```text
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest ...
```

The exact command decomposition may evolve with the CI/test suites, but local and CI invocations must execute the same tools against the same project configuration rather than maintaining separate hidden quality policies.

Activation of a virtual environment is not a prerequisite for the canonical commands; `uv run` is the normal execution boundary.

#### Dependency upgrades

Dependency updates are explicit reviewed changes.

A dependency-update automation may propose changes, but a new version is not accepted merely because it is available. The lockfile update is reviewed like code and must pass the applicable quality/test matrix, including real-PostgreSQL and deterministic concurrency verification where the changed dependency can affect those paths.

Generic automatic merging of dependency updates is not part of the baseline.

#### Pre-commit policy

Git pre-commit hooks are optional developer convenience only.

They are not the authority for project correctness and are not required to reproduce the canonical quality gates. CI remains the authoritative enforcement boundary.

#### Alignment rule

The existing pre-review `pyproject.toml` is not made normative merely by containing historical dependencies/tool settings.

After the technology review is complete, project metadata/tool configuration is aligned in one deliberate sweep. That alignment includes removing obsolete/excluded dependencies, eliminating duplicate packages, adding ratified testing/tooling dependencies, updating the Python target and moving Pyright from `basic` to `strict` without piecemeal drift during the review itself.

## 4. Technology-review rule

Technology choices are reviewed one decision point at a time.

A choice becomes authoritative only after explicit ratification and consolidation in this document.

If a future technology change affects a frozen milestone semantic or technical contract, the affected architecture must be explicitly reopened and realigned before implementation.