# NETAUTO Architecture — Current AS-IS

**Status:** CURRENT AS-IS — consolidated from the accepted and merged M1 baseline.

## Purpose and authority

`docs/architecture/` is the authoritative description of the system as currently delivered.

It is intentionally history-light and state-heavy:

- it describes what NETAUTO is now;
- it must be sufficient to verify the starting assumptions of a future milestone or fix;
- it does not require reconstruction of earlier cycles;
- historical rationale, acceptance evidence and prompts remain in `docs/milestones/`, `docs/fixes/` and Git history.

When a future cycle declares behavior unchanged, that behavior must be verifiable here. A missing or contradictory starting assumption is a design STOP condition under `docs/general/linee_guida_progetto.md`.

Project-wide technology choices are owned by `docs/general/technology_baseline.md`. They are repeated here only when they directly constitute an architectural guarantee.

## Delivery provenance

| Cycle | Type | Delivered result | Historical record |
|---|---|---|---|
| `M1` | Milestone | PostgreSQL-only kernel; DataType, ObjectTemplate, Object and Relationship semantics; UoW, concurrency, public API and verification baseline. Delivered and merged on 2026-08-15. | `docs/milestones/M1/` |

Future delivered `Mx` and `Fx-y` cycles are appended when their result is consolidated into this AS-IS.

## Architecture map

| Area | Owning document | Responsibility |
|---|---|---|
| DataType | `datatype.md` | Scalar type system, canonicalization, constraints, versioning, lifecycle and dependency rules. |
| ObjectTemplate | `objecttemplate.md` | Versioned entity schemas, inheritance, properties, ownership slots, effective schema and model lifecycle. |
| Object | `object.md` | Runtime admission/state, schema migration, ownership, lifecycle events and deletion. |
| Relationship | `relationship.md` | Definition/Resolution model plane, factual Relationship closure and navigation. |
| Persistence | `persistence.md` | PostgreSQL relational authority, keys/FKs/delete boundaries, canonical storage and denormalizations. |
| Semantic concurrency | `concurrency-matrix.md` | Canonical mutation census, interaction scopes, safety predicates and allowed outcomes. |
| PostgreSQL concurrency realization | `concurrency.md` | UoW, isolation, row locks, constraints, advisory gates and convergence mechanisms. |
| Public API | `api.md` | HTTP/JSON command, selector, DTO, list, error, success and forbidden-surface contracts. |
| Verification policy | `verification.md` | Verification layers, evidence policy and closure obligations. |
| Canonical concurrency verification | `verification-concurrency-registry.md` | Stable scenario IDs, predicate coverage, harness constraints and orchestration recipes. |

A decision belongs in its owning document. Cross-cutting documents may state consequences but must not redefine that decision.

In particular:

```text
concurrency-matrix.md
    -> what must remain true

concurrency.md
    -> how PostgreSQL/UoW realizes it

verification.md
    -> how evidence is classified and required

verification-concurrency-registry.md
    -> which stable deterministic scenarios prove it
```

## System scope

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
       resolved through RelationshipDefinition/Resolution contracts
```

The current architecture excludes, unless introduced by a future delivered cycle:

- authentication/authorization and multi-tenancy;
- discovery, observation and reconciliation;
- automation, scheduling and workflow engines;
- plugin SDK/runtime expansion;
- web UI and telemetry/time-series domains;
- alternate persistence backends;
- JSON Schema as validation language, compile target or public schema projection.

## Global principles

### Correctness first

Semantic correctness and dataset consistency take precedence over premature optimization, legacy compatibility and database portability.

### Domain semantics before mechanism

The domain defines valid states/transitions. Persistence, UoW, concurrency, API and verification preserve those semantics.

### PostgreSQL authority

PostgreSQL is the only supported persistence backend. No portability burden is maintained solely for hypothetical alternatives.

### Exact persisted references

Version-sensitive references are exact. A default may resolve caller omission at admission time, but the persisted binding materializes the selected exact version.

### Atomic semantic mutations

One semantic mutation is one write UoW. State-dependent reads, admission, writes and required lifecycle events commit or roll back together.

### Concurrency is correctness

An invariant is not guaranteed if a supported concurrent interleaving can violate it.

### Cross-domain validity

A mutation must preserve the relevant dependency graph, not merely local aggregate validity.

### No implicit remediation

Commands do not silently expand responsibility to move Objects, detach ownership, delete subtrees, transform incompatible values or rewrite Relationship endpoints.

## Shared current-state invariants

The owning documents elaborate these cross-cutting rules:

- stable lineage identity is distinct from exact version identity;
- version lifecycle is `DRAFT -> PUBLISHED -> DEPRECATED`;
- PUBLISHED/DEPRECATED model snapshots are immutable;
- DRAFT mutation uses `expected_revision` freshness;
- active PUBLISHED consumers have PUBLISHED exact dependencies;
- cross-aggregate current references are non-cascading unless they are true owned child state;
- Object state is canonical and exact-schema pinned;
- ownership is single-owner and acyclic;
- factual Relationship closure is complete and exact;
- lifecycle events are append-only history atomic with their mutation;
- public DTOs are semantic contracts, not persistence-row mirrors;
- public failures are transport-neutral semantics mapped at the HTTP boundary.

## AS-IS update discipline

After a delivered milestone or fix:

1. derive the resulting current semantics from the approved cycle;
2. update each affected owning document;
3. propagate cross-cutting consequences;
4. update delivery provenance;
5. remove cycle-temporal wording;
6. retain the cycle directory as history;
7. keep durable identifier registries explicit in architecture rather than only in code/tests.

Consolidation is never an indiscriminate copy of cycle documents.

Outside a software cycle, an explicitly human-authorized documentation task may repair broken references, stale wording or an ambiguous statement only when the correction is **lossless** with respect to delivered behavior. A change to system meaning requires a milestone or fix.

## Consistency rule

A contradiction inside this AS-IS set is an architecture defect. It must not be resolved by selecting the newer or more convenient file. The affected authority must be reconciled before dependent design or implementation continues.
