# Verification — Current AS-IS

## Purpose

Verification is part of the architecture when it is required to demonstrate a semantic, persistence or concurrency guarantee.

The current verification model is layered so that each class of guarantee is tested at the level where it is actually owned. Tests are evidence of the architecture; they do not redefine the semantic contract.

General traceability target:

```text
required property / invariant
    -> architecture decision
    -> implementation mechanism
    -> concrete verification
```

For concurrency-sensitive guarantees:

```text
semantic safety predicate
    -> PostgreSQL realization
    -> deterministic real-PostgreSQL scenario
```

## Verification layers

### T0 — Pure domain

Purpose:

- value semantics;
- domain-state validity;
- lifecycle transition rules independent of persistence;
- primitive canonicalization and domain invariants that do not require PostgreSQL.

Mocks/fakes are acceptable here when they are not used to claim PostgreSQL guarantees.

### T1 — Application / orchestration

Purpose:

- application command/query contracts;
- semantic Unit of Work orchestration;
- candidate derivation and domain-service composition;
- transport-neutral failure/result semantics.

T1 verifies application behavior without substituting for persistence/concurrency evidence.

### T2 — Real PostgreSQL persistence

Purpose:

- SQLAlchemy/Alembic schema realization;
- PK/UNIQUE/FK/CHECK/delete semantics;
- canonical persistence representations;
- Unit of Work commit/rollback behavior;
- DB/application integration.

Guarantees attributed to PostgreSQL must be verified against a real PostgreSQL server, not SQLite or an in-memory substitute.

### T3 — Deterministic real-PostgreSQL concurrency

Purpose:

- supported concurrent interleavings;
- row-lock/gate/constraint behavior;
- post-wait fresh-snapshot rules;
- uniqueness/FK race outcomes;
- convergence/retry behavior;
- preservation of the semantic safety predicates defined in `concurrency.md`.

T3 is correctness evidence, not a probabilistic stress test.

A valid deterministic concurrency test uses independent database sessions/transactions and an explicit orchestration mechanism that demonstrates the intended blocker/gate/constraint relationship. Arbitrary `sleep()` timing is not a correctness contract.

### T4 — Public API contract / integration

Purpose:

- exact route surface;
- strict request DTO semantics;
- omission vs explicit null/input behavior;
- PrimitiveType wire forms;
- application-to-HTTP error mapping;
- success status/body/Location behavior;
- read/list projection, filter, ordering and pagination contracts.

The public surface is tested against exact expected inventories where the architecture defines a finite closed set; minimum-count assertions are insufficient for forbidden-surface guarantees.

### T5 — Migration / schema lifecycle

Purpose:

- clean Alembic base-to-head upgrade;
- migration composition;
- expected downgrade/upgrade behavior where supported;
- schema structure matching authoritative metadata;
- no unintended metadata drift;
- removal limited to NETAUTO-owned schema objects;
- application startup does not implicitly apply migrations.

Migration verification must protect both current schema correctness and explicit administration boundaries.

### T6 — Targeted property-based verification

Purpose:

- algebraic/canonicalization properties where example tests alone are weak;
- exact-decimal normalization;
- byte-size exactness;
- primitive parse/canonicalization closure and similar bounded properties.

Property-based tests supplement, rather than replace, deterministic contract examples.

### T7 — Randomized / stress

Randomized/stress testing is supplementary. It may find implementation defects but is not accepted as a substitute for deterministic T3 concurrency evidence or explicit architecture traceability.

## Current concurrency verification contract

The current kernel concurrency architecture has a durable canonical scenario registry of **51** scenario IDs grouped as:

```text
ROW     17
ARB      7
REF      6
GATE     6
SNAP     4
ATOMIC   4
PAR      7
       ----
total   51
```

The canonical IDs are architecture/verification identities. Variants may exist beneath one parent scenario but do not redefine the canonical census.

The same registry covers the exact non-independent safety-predicate set defined in `concurrency.md`:

```text
NU VS DG LS DV BA AM RL AL ML OS PO OF SO OC RC RF RA ES
```

All **19** predicates must map to at least one valid canonical real-PostgreSQL scenario and every referenced scenario must exist.

A future mutation/concurrency rule that introduces a new safety requirement must update both semantic concurrency analysis and durable verification mapping.

## Deterministic concurrency harness requirements

Concurrency tests must provide enough orchestration to prove the intended interleaving rather than merely make it likely.

The harness should, as applicable:

- use independent PostgreSQL connections/sessions;
- expose explicit transaction boundaries;
- observe blockers/gates/constraint waits where the mechanism matters;
- coordinate candidate and winner/loser phases deterministically;
- apply bounded timeouts so a broken lock contract fails diagnostically rather than hangs indefinitely;
- capture useful failure diagnostics without changing the semantic outcome;
- ensure fresh reads occur in separate statements where READ COMMITTED post-wait visibility is part of the contract.

Stress/random scheduling may be layered on top, but the deterministic recipe remains the verification authority.

## Required invariant classes

Verification must remain capable of demonstrating, at minimum:

### Domain/model

- DataType and ObjectTemplate lifecycle monotonicity;
- DRAFT `expected_revision` freshness;
- exact pinning/default admission;
- effective-schema validity;
- canonical primitive/constraint behavior;
- RelationshipDefinition aggregate/equivalence/conflict semantics.

### Cross-domain

- active model graph cannot contain a PUBLISHED consumer pointing to a non-PUBLISHED dependency;
- Object state remains valid under its exact schema;
- schema change preserves or rejects current values/ownership deterministically;
- current ownership edges remain compatible with the parent's current exact schema;
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
- required lifecycle event set is atomic with the real mutation;
- failed concurrent candidate transactions do not leak partial aggregate/header/event state.

### Concurrency

- all 19 current safety predicates remain covered;
- intentional advisory gates actually serialize their protected predicates;
- intended non-serialization remains possible where lock-strength design requires it;
- retry/convergence restarts from fresh state rather than stale partial state;
- exact-ID Relationship delete preserves ABA semantics.

### API

- exactly the supported mutation/read surface exists;
- forbidden generic PATCH/PUT and autonomous owned-child mutation surfaces remain absent;
- finite public error catalog stays aligned with application failures;
- no public SQL/constraint/internal leakage;
- list cursors/order/filter semantics remain route-specific and deterministic.

## Runtime/test database separation

Real-PostgreSQL automated tests use a database target logically separate from the application runtime database.

Current configuration boundary:

```text
NETAUTO_DATABASE_URL
    -> runtime / application / migration target

TEST_DATABASE_URL
    -> automated verification target
```

Test execution assumes externally managed PostgreSQL provisioning. The project/test suite does not claim ownership of the PostgreSQL server lifecycle.

No credential or concrete database URL belongs in architecture or acceptance documentation.

## Migration authority checks

The current migration verification baseline must detect:

- failure to migrate from clean base to current head;
- mismatch between migrated schema and authoritative SQLAlchemy metadata;
- loss or unexpected change of PK/UNIQUE/FK/CHECK/index structures;
- accidental reintroduction of the removed RelationshipResolution name-based key;
- ownership of objects outside the NETAUTO schema boundary during downgrade/cleanup;
- application-lifespan code attempting to run migrations implicitly.

Migration changes therefore require both migration-specific tests and schema metadata/constraint verification.

## API surface closure checks

The current API architecture defines a finite canonical surface:

```text
mutation routes = 32
read/list routes = 20
public error codes = 23
namespace = /api/v1/core
```

Verification should compare generated OpenAPI/public registries to exact expected sets so accidental extra routes or missing routes are detected.

Negative surface checks include rejection/absence of:

- generic PUT/PATCH kernel mutation;
- action DSL bypasses;
- autonomous RelationshipResolution mutation;
- autonomous ObjectComponent mutation;
- JSON Schema endpoints or schema-compilation capability.

## Reproducibility gates

A delivery/closure candidate must pass the project-ratified reproducibility/quality gates applicable at that time, including:

- locked dependency consistency;
- clean environment synchronization from the lock;
- package build;
- formatting/linting;
- static type checking;
- complete automated test suite required by the cycle;
- migration/schema checks when persistence is affected.

Exact tool versions and commands are owned by the project technology baseline and cycle evidence, not hard-coded here unless they define a semantic architecture guarantee.

## Evidence durability

Cycle acceptance records may contain transient counts, command ledgers and commit-specific evidence. Those belong to the cycle historical record.

This AS-IS document preserves only durable verification obligations and canonical verification identities needed to understand and safely evolve the current system.
