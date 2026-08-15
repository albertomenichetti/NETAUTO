# NETAUTO Architecture — Current AS-IS

**Status:** CURRENT AS-IS — consolidated on 2026-08-15 from the accepted M1 delivery baseline and subsequently reviewed for lossless authority coverage.

## Purpose and authority

`docs/architecture/` is the authoritative description of the architecture of the system as currently delivered.

This directory is intentionally history-light and state-heavy:

- it describes what NETAUTO is now;
- it must be sufficient to verify the starting assumptions of a future milestone or fix;
- it does not require the reader to reconstruct M1, M2, ... history to understand current behavior;
- historical rationale, acceptance evidence, implementation prompts and cycle-specific wording remain in `docs/milestones/`, `docs/fixes/` and Git history.

When a future cycle declares a behavior unchanged, that behavior must be verifiable here. A missing or contradictory starting assumption is a design STOP condition under `docs/general/linee_guida_progetto_v2.md`.

Technology choices that are project-wide rather than semantic architecture are owned by `docs/general/technology_baseline.md` and are not duplicated here unless they directly define an architectural guarantee.

## Delivery provenance

The following delivered cycles have contributed to the current AS-IS. This table records provenance only; cycle documents are historical records and are not the current architecture authority.

| Cycle | Type | Delivered result relevant to current AS-IS | Historical record |
|---|---|---|---|
| `M1` | Milestone | Established the PostgreSQL-only kernel; ratified DataType, ObjectTemplate, Object and Relationship semantics; consolidated UoW, concurrency, public API and verification contracts; final reviewer acceptance completed on 2026-08-15. | `docs/milestones/M1/` |

No fix cycle has been delivered after M1 at this snapshot. Future delivered `Mx` and `Fx-y` cycles must be appended here when their changes are consolidated into the AS-IS.

## Architecture map

| Area | Owning document | Responsibility |
|---|---|---|
| DataType | `datatype.md` | Primitive scalar type system, versioning, lifecycle, canonicalization, constraints, default/pinning and active dependency rules. |
| ObjectTemplate | `objecttemplate.md` | Versioned entity schemas, inheritance, properties, ownership slots, effective schema and model lifecycle. |
| Object | `object.md` | Runtime entity admission/state, schema migration, ownership, lifecycle events and deletion semantics. |
| Relationship | `relationship.md` | RelationshipDefinition/Resolution model-plane semantics, factual Relationship runtime closure and graph navigation. |
| Persistence | `persistence.md` | PostgreSQL authority, relational model, FK/delete boundary, canonical persistence representations and denormalizations. |
| Semantic concurrency matrix | `concurrency-matrix.md` | Canonical mutation census, sparse pairwise rules, 19 safety predicates, allowed outcomes and future-mutation analysis discipline. |
| Concurrency / Unit of Work | `concurrency.md` | Transaction boundaries, isolation, locks/gates, convergence and PostgreSQL realization of the semantic predicates. |
| Public API | `api.md` | HTTP/JSON adapter boundary, exact route/DTO/selector/list/error/success contracts and forbidden surface. |
| Verification | `verification.md` | Required verification layers, real-PostgreSQL evidence model, migration/API/reproducibility obligations and traceability baseline. |
| Canonical concurrency verification | `verification-concurrency-registry.md` | Stable 51-scenario registry, 19-predicate coverage, deterministic harness constraints and eight orchestration recipes. |

A semantic decision belongs in its owning document. Cross-cutting documents may state realization consequences but must not redefine the owning domain semantics.

The two concurrency companion documents are intentionally distinct:

```text
concurrency-matrix.md
    -> what must remain true under each scoped mutation interaction

concurrency.md
    -> how the current PostgreSQL/UoW architecture realizes those guarantees
```

Likewise:

```text
verification.md
    -> durable verification policy and layers

verification-concurrency-registry.md
    -> exact stable concurrency scenario and recipe identities
```

## System scope

The current kernel centers on four concepts:

```text
DataType
    -> versioned atomic scalar domains

ObjectTemplate
    -> versioned entity schemas with inheritance,
       typed properties and ownership/component slots

Object
    -> runtime entity with stable identity,
       exact ObjectTemplateVersion pin and canonical mutable state

Relationship
    -> typed factual association between Objects,
       resolved through model-plane RelationshipDefinition/Resolution contracts
```

The current architecture deliberately excludes, unless introduced by a future delivered cycle:

- authentication and authorization;
- multi-tenancy;
- Observation/discovery/reconciliation capabilities;
- automation/execution/scheduling/workflow engines;
- plugin SDK/runtime capability expansion;
- web UI;
- time-series/telemetry domain;
- persistence backends alternative to PostgreSQL;
- JSON Schema as validation language, compile target or public schema projection.

## Global architectural principles

### Correctness first

Semantic correctness and dataset consistency have priority over premature throughput optimization, legacy compatibility and database portability.

### Domain semantics before mechanism

The domain model defines valid states and transitions. Persistence, Unit of Work, concurrency controls, API and verification must preserve the same semantics.

### PostgreSQL is the persistence authority

PostgreSQL is the only supported persistence backend for the current kernel. The domain remains separated from persistence concerns, but no architecture burden is maintained solely to support alternate backends.

### Exact references over floating state

Version-sensitive persisted references are exact. Current defaults may be used to resolve caller omission at admission time, but a persisted binding materializes the selected exact version.

### Atomic semantic mutations

One semantic kernel mutation is one write Unit of Work. State-dependent reads, admission checks, required writes and lifecycle-event production commit or roll back together.

### Concurrency is part of correctness

An invariant is not considered guaranteed if a supported concurrent interleaving can violate it. Concurrency contracts therefore belong to the architecture rather than to a later performance phase.

### Cross-domain validity

Local aggregate validity is insufficient when a mutation can invalidate a dependent model, ownership edge, relationship or runtime object. The committed dataset must remain globally coherent for the affected dependency graph.

### No implicit remediation

A semantic command does not silently broaden its responsibility to repair unrelated state. Examples include no implicit Object move, ownership detach, subtree delete, schema value transformation or relationship endpoint rewrite unless a future explicit workflow defines it.

## Current-state invariants shared across areas

The following principles are cross-cutting and are elaborated in the owning documents:

- stable lineage identity is distinct from exact version identity;
- lifecycle of versioned model snapshots is monotonic `DRAFT -> PUBLISHED -> DEPRECATED`;
- PUBLISHED/DEPRECATED model snapshots are immutable;
- exact-DRAFT semantic mutation uses `expected_revision` freshness;
- active PUBLISHED model dependencies point to PUBLISHED exact dependencies;
- current cross-aggregate references use non-cascading lifetime semantics unless they are owned child state of the same aggregate;
- Object runtime state uses canonical values and an exact schema pin;
- ownership is single-owner and acyclic;
- factual Relationship identity is stable and its runtime resolved closure is complete and exact;
- lifecycle events are append-only application/kernel history and commit atomically with the mutation that produces them;
- public API DTOs are semantic command/projection contracts, not persistence-row mirrors;
- public errors are transport-neutral semantic failures mapped at the HTTP adapter boundary.

## Current persistence and transaction baseline

```text
PostgreSQL only
READ COMMITTED mutation baseline
explicit row locks / FK / uniqueness / advisory gates as required
full semantic-UoW rollback on failure
fresh re-validation after stabilization or lock wait
real PostgreSQL required to verify DB/concurrency guarantees
```

Runtime and automated-test database configuration are externally supplied and logically separated. The application does not own PostgreSQL instance provisioning.

## Current public API baseline

The public kernel API is HTTP/JSON under:

```text
/api/v1/core
```

The application command/query contract is authoritative; FastAPI/Pydantic/OpenAPI are transport/composition concerns.

The API exposes explicit semantic commands rather than generic PATCH/PUT mutation. Read surfaces expose canonical semantic projections. Paginated collections use opaque keyset cursors and fixed route-specific ordering.

See `api.md` for the canonical route, DTO, filter, error and success contract.

## AS-IS update discipline

After a delivered milestone or fix:

1. derive only the resulting current-system semantics from the approved cycle documents;
2. update the affected owning documents in this directory;
3. harmonize cross-cutting consequences in persistence/concurrency/API/verification documents as applicable;
4. update the delivery-provenance table above;
5. remove cycle-temporal language such as `target`, `candidate`, `during Mx`, `to be implemented` when it no longer describes the delivered system;
6. preserve the cycle documents separately as historical records;
7. verify that any durable identifier registry needed to evolve the system safely remains explicitly enumerated here rather than only in code/tests.

Consolidation into `docs/architecture/` is never an indiscriminate copy of milestone/fix documentation.

## Consistency rule

A contradiction inside this AS-IS set is an architecture defect. It must not be resolved by choosing whichever file is newer or more convenient. The affected authority must be explicitly reconciled before a dependent design or implementation continues.