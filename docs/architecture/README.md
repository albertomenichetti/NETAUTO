# NETAUTO — Current Architecture

**Status:** CURRENT AS-IS

## Purpose and authority

This directory is the authoritative description of the system that NETAUTO is.
It owns current semantics, guarantees, boundaries and verification obligations;
code and tests realize and verify this corpus but do not redefine it.

The applicable architecture is composed from this directory and the ratified
technology decisions in [`../general/technology_baseline.md`](../general/technology_baseline.md).
Historical milestone and fix records explain how a state was reached but are not
required to understand or implement the current system.

## Concise provenance

| Consolidated cycle | Historical record | Current-state result |
|---|---|---|
| M1 | [`../milestones/M1/`](../milestones/M1/) | PostgreSQL kernel, versioned model resources, factual objects and relationships, ownership, HTTP and deterministic concurrency foundations. |
| M2 | [`../milestones/M2/`](../milestones/M2/) | Versioned Relationship schemas and factual state, durable migration baseline, centralized lock planning, Health, official CLI and installed Linux runtime. |

Provenance is historical navigation only. The owner map below is the semantic
entry point.

## Owner map

| Area | Owner | Responsibility |
|---|---|---|
| Data types and primitive values | [`datatype.md`](datatype.md) | DataType lineage/version lifecycle, constraints and canonical primitive values. |
| Template model | [`objecttemplate.md`](objecttemplate.md) | ObjectTemplate inheritance, exact versions, properties, components and effective schema. |
| Factual objects and ownership | [`object.md`](object.md) | Object identity/state, schema evolution, ownership and intrinsic lifecycle. |
| Relationship model and facts | [`relationship.md`](relationship.md) | Definition topology, exact versions, property schemas, factual state, closure and relationship history. |
| Persistence and migrations | [`persistence.md`](persistence.md) | Fifteen-table PostgreSQL model, keys, constraints, indexes, codecs and Alembic authority. |
| Semantic concurrency | [`concurrency-matrix.md`](concurrency-matrix.md) | Forty-one mutation primitives, interaction classification and twenty-one safety predicates. |
| PostgreSQL concurrency realization | [`concurrency.md`](concurrency.md) | Unit of Work, centralized lock plans, advisory gates, ordering, arbitration and restart policy. |
| Public HTTP surface | [`api.md`](api.md) | Exact business and Health routes, DTOs, status/failure contracts, reads and pagination. |
| Core readiness | [`health.md`](health.md) | Application readiness semantics and the bounded PostgreSQL probe. |
| Official client | [`cli.md`](cli.md) | Static 63-operation HTTP client, REPL, selectors, output and process behavior. |
| Runtime and deployment | [`runtime-deployment.md`](runtime-deployment.md) | Settings, engines, startup guard, wheel, installed migrations, trust and operating model. |
| Linux operator procedure | [`linux-operating-baseline.md`](linux-operating-baseline.md) | Executable installation, migration, start, readiness, stop and restart projection. |
| Verification policy | [`verification.md`](verification.md) | T0–T10 evidence policy, environments and release gates. |
| Concurrency verification registry | [`verification-concurrency-registry.md`](verification-concurrency-registry.md) | Exact 83-scenario, 21-predicate and recipe registry. |

## System scope

NETAUTO is a PostgreSQL-backed, REST-API-first infrastructure modelling kernel.
It provides:

- stable and exact-versioned model resources;
- factual Objects, ownership and typed factual Relationships;
- coherent current and historical projections;
- one semantic mutation per transactional Unit of Work;
- deterministic concurrency and reference-lifetime guarantees;
- a strict HTTP API and an HTTP-only official CLI;
- an exact startup schema guard and bounded Core readiness operation;
- one versioned wheel with server, CLI, migration graph and exact runtime lock;
- a manual, foreground Linux operating procedure.

The system does not provide native authentication or authorization, server TLS,
containers, orchestration, process supervision, automatic migration, backup,
restore, high availability, observability platforms or deployment automation.
HTTP is supported only inside an administratively trusted reachability boundary;
TLS across an untrusted segment is externally terminated.

## Global principles

### Semantic authority precedes mechanism

Domain and public contracts define valid states and outcomes. PostgreSQL,
SQLAlchemy, FastAPI, HTTPX and terminal tooling realize those decisions without
creating an alternate semantic authority.

### Exact persisted identity

Stable lineages and exact versions are distinct identities. Persisted facts bind
to exact versions; nullable defaults are explicit selection policy, never a
floating persisted reference or a latest/highest fallback.

### Atomic semantic mutation

One semantic mutation owns one write Unit of Work. Protected reads, admission,
state writes, deterministic child/closure writes and required lifecycle events
commit or roll back together.

### Concurrency is correctness

Supported concurrent outcomes must be serially explainable under the semantic
matrix. The PostgreSQL realization stabilizes complete predicates before DML,
preserves referential lifetime and has no supported-path deadlock recovery
contract.

### Coherent reads and safe corruption boundary

A public aggregate or page observes one coherent committed state. Persisted
invariant corruption fails the complete representation safely; it is never
repaired, filtered or partially projected at a read boundary.

### Explicit operation and remediation

Installation, migration, startup and readiness are distinct operations. Server
startup verifies exact migration revision and never upgrades, stamps or repairs
the database. Health observes readiness and never remediates it.

## Shared invariants

- stable identities are opaque UUIDs unless an owner defines a composite key;
- exact version numbers and revisions are positive, non-boolean integers;
- lifecycle state is `DRAFT`, `PUBLISHED` or `DEPRECATED`;
- mutation of a DRAFT uses `expected_revision` generation freshness;
- only PUBLISHED exact versions admit lifecycle-sensitive direct bindings;
- existing exact historical bindings remain interpretable after deprecation;
- cross-aggregate current references use non-cascading lifetime protection;
- canonical JSON values contain no domain null carrier;
- lifecycle history is atomic with real transitions and independent of live
  display metadata;
- public errors use a finite code catalogue with bounded safe details;
- required PostgreSQL claims are proven on real PostgreSQL.

## Update discipline

A cycle changes this corpus only after its contract, architecture,
implementation and acceptance are closed. Consolidation assigns each resulting
decision to one current owner and removes temporal explanation. A later change
must update the owning current document, all dependent owners and permanent
verification registries together.

When current owners conflict, work stops until the contradiction is resolved by
an authorized architecture change. Recency, implementation behavior and test
expectations are evidence, not automatic precedence.
