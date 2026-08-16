# Verification — Current AS-IS

## Purpose and authority

Verification is part of the architecture when it is required to demonstrate a semantic, persistence or concurrency guarantee.

Tests are evidence of the architecture; they do not redefine the semantic contract.

General traceability target:

```text
required property / invariant
    -> architecture decision
    -> implementation mechanism
    -> concrete verification
```

For concurrency-sensitive guarantees:

```text
semantic rule and safety predicate
    -> PostgreSQL realization
    -> deterministic real-PostgreSQL scenario
```

Authority is divided as follows:

```text
concurrency-matrix.md
    -> semantic mutation interactions and safety predicates

concurrency.md
    -> PostgreSQL / Unit of Work realization

verification-concurrency-registry.md
    -> canonical deterministic scenario IDs,
       coverage mapping and orchestration recipes

this document
    -> verification layers, evidence policy and closure obligations
```

## Verification layers

### T0 — Pure domain

Purpose:

- value semantics;
- domain-state validity;
- lifecycle transition rules independent of persistence;
- primitive canonicalization and domain invariants that do not require PostgreSQL.

Mocks/fakes are acceptable only when they are not used to claim PostgreSQL guarantees.

### T1 — Application / orchestration

Purpose:

- application command/query contracts;
- semantic Unit of Work orchestration;
- candidate derivation and domain-service composition;
- transport-neutral failure/result semantics.

T1 does not substitute for persistence/concurrency evidence.

### T2 — Real PostgreSQL persistence

Purpose:

- SQLAlchemy/Alembic schema realization;
- PK/UNIQUE/FK/CHECK/delete semantics;
- canonical persistence representations;
- Unit of Work commit/rollback behavior;
- DB/application integration.

Guarantees attributed to PostgreSQL require a real PostgreSQL server.

### T3 — Deterministic real-PostgreSQL concurrency

Purpose:

- supported concurrent interleavings;
- row-lock/gate/constraint behavior;
- post-wait fresh-snapshot rules;
- uniqueness/FK race outcomes;
- convergence/retry behavior;
- preservation of the safety predicates owned by `concurrency-matrix.md`.

T3 is correctness evidence, not probabilistic stress testing.

A valid scenario uses independent database sessions/transactions and deterministic orchestration that demonstrates the intended blocker, gate, constraint or progress relationship. Arbitrary `sleep()` timing is not a correctness contract.

### T4 — Public API contract / integration

Purpose:

- exact route surface;
- strict request DTO semantics;
- omission vs explicit null/input;
- PrimitiveType wire forms;
- application-to-HTTP failure mapping;
- success status/body/Location;
- read/list projection, filter, ordering and pagination.

Where the architecture defines a finite closed surface, verification compares exact expected inventories; minimum-count assertions are insufficient.

### T5 — Migration / schema lifecycle

Purpose:

- clean Alembic base-to-head upgrade;
- migration composition;
- expected downgrade/upgrade behavior where supported;
- schema structure matching authoritative metadata;
- no unintended metadata drift;
- cleanup limited to NETAUTO-owned schema objects;
- application startup does not apply migrations implicitly.

### T6 — Targeted property-based verification

Purpose:

- algebraic/canonicalization properties where examples alone are weak;
- exact-decimal normalization;
- byte-size exactness;
- primitive parse/canonicalization closure and similar bounded properties.

Property-based tests supplement deterministic contract examples.

### T7 — Randomized / stress

Randomized/stress testing is supplementary discovery tooling. It does not replace deterministic T3 evidence or architecture traceability.

## Canonical concurrency verification

The exact current scenario census, scenario semantics, safety-predicate coverage and orchestration recipes are owned exclusively by:

```text
docs/architecture/verification-concurrency-registry.md
```

This document intentionally does not duplicate that registry.

Every non-`I` semantic rule in `concurrency-matrix.md` must map to at least one concrete or explicitly equivalent deterministic scenario. A future mutation or new concurrency guarantee must update:

1. the semantic matrix;
2. the PostgreSQL realization;
3. the canonical verification registry;
4. the machine-checkable implementation traceability.

## Deterministic concurrency harness requirements

The harness must, as applicable:

- use independent PostgreSQL connections/sessions;
- expose explicit transaction boundaries;
- observe blockers/gates/constraint waits when the mechanism matters;
- coordinate candidate and winner/loser phases deterministically;
- apply bounded timeouts as safety nets;
- capture useful failure diagnostics without changing semantics;
- execute fresh statements where READ COMMITTED post-wait visibility is required;
- prove important non-blocking through positive progress while the other transaction remains open.

Stress/random scheduling may be layered on top, but the deterministic recipe remains the normative evidence.

## Required invariant classes

Verification must remain capable of demonstrating at least the following.

### Domain/model

- DataType and ObjectTemplate lifecycle monotonicity;
- DRAFT `expected_revision` freshness;
- exact pinning/default admission;
- effective-schema validity;
- canonical primitive/constraint behavior;
- RelationshipDefinition aggregate/equivalence/conflict semantics.

### Cross-domain

- active PUBLISHED model consumers never point to non-PUBLISHED exact dependencies;
- Object state remains valid under its exact schema;
- schema change preserves or rejects values/ownership deterministically;
- ownership edges remain compatible with the parent's current exact schema;
- factual Relationship endpoints remain compatible with stable template lineages.

### Persistence

- authoritative 13-table schema and intended keys/FKs/checks/indices;
- ownership single-owner PK authority;
- exact Relationship resolved-view PK authority;
- same-Definition runtime composite FK coherence;
- current cross-aggregate reference lifetime through `RESTRICT`;
- canonical JSON/primitive representations.

### Atomicity

- every semantic mutation is all-or-nothing;
- required lifecycle events are atomic with the real mutation;
- failed concurrent candidates leak no partial aggregate/header/event state.

### Concurrency

- all current non-independent safety predicates remain covered;
- advisory gates serialize their protected predicates;
- intended non-serialization remains possible where required;
- retry/convergence restarts from fresh state;
- exact-ID Relationship delete preserves ABA semantics.

### API

- exactly the supported mutation/read surface exists;
- forbidden generic and autonomous owned-child surfaces remain absent;
- public error catalog stays aligned with application failures;
- no SQL/constraint/internal detail leaks publicly;
- list cursor/order/filter semantics remain route-specific and deterministic.

## Runtime/test database separation

Real-PostgreSQL automated tests use a target logically separate from the application runtime database.

```text
NETAUTO_DATABASE_URL
    -> runtime / application / migration target

TEST_DATABASE_URL
    -> automated verification target
```

Provisioning is externally managed. No credential or concrete database URL belongs in architecture or acceptance documentation.

## Migration authority checks

Migration verification must detect:

- failure to migrate from clean base to current head;
- mismatch between migrated schema and authoritative SQLAlchemy metadata;
- loss or unexpected change of PK/UNIQUE/FK/CHECK/index structures;
- accidental reintroduction of the removed RelationshipResolution name-based key;
- modification of objects outside the NETAUTO schema boundary during downgrade/cleanup;
- application-lifespan code attempting to run migrations implicitly.

Migration changes require both migration execution evidence and schema metadata/constraint verification.

## API surface closure checks

The current API architecture defines a finite surface owned by `api.md`.

Verification compares generated OpenAPI/public registries to exact expected sets so accidental extra or missing routes/codes are detected.

Negative surface checks include absence of:

- generic PUT/PATCH kernel mutation;
- action DSL bypasses;
- autonomous RelationshipResolution mutation;
- autonomous ObjectComponent mutation;
- JSON Schema endpoints or schema-compilation capability.

## Reproducibility gates

A delivery/closure candidate passes the project-ratified gates applicable at that time, including:

- locked dependency consistency;
- clean environment synchronization from the lock;
- package build;
- formatting/linting;
- static type checking;
- the automated suites required by the cycle;
- migration/schema checks when persistence is affected.

Exact tools and command selections are owned by the technology baseline, project configuration and active cycle evidence rather than duplicated here.

## Evidence durability

Cycle acceptance records may contain command ledgers, transient counts and commit-specific evidence. Those remain in the historical cycle record.

This AS-IS document preserves durable verification obligations. Stable scenario identities needed to evolve concurrency safely are preserved in `verification-concurrency-registry.md`.
