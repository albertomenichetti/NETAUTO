# NETAUTO — Technology Baseline

**Status:** DRAFT — project-wide technology review in progress. `STACK-01` and `STACK-02` are ratified; other technology decisions remain open until explicitly ratified.

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

## 4. Technology-review rule

Technology choices are reviewed one decision point at a time.

A choice becomes authoritative only after explicit ratification and consolidation in this document.

If a future technology change affects a frozen milestone semantic or technical contract, the affected architecture must be explicitly reopened and realigned before implementation.