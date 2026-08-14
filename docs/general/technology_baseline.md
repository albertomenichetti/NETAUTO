# NETAUTO — Technology Baseline

**Status:** DRAFT — project-wide technology review in progress. `STACK-02` is ratified; other technology decisions remain open until explicitly ratified.

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

**Status:** OPEN.

The current candidate is:

```text
ASGI / asyncio as the project I/O execution baseline

application operations that perform I/O
    -> async

PostgreSQL Unit of Work / persistence I/O
    -> async candidate

pure domain model, canonicalization, validation,
candidate construction and migration algorithms
    -> normal synchronous Python
```

This point is not ratified by this document yet.

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

The concrete sync/async connection type is determined by `STACK-01`, but the invariant is already fixed:

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