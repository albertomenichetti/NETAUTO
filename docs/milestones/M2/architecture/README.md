# M2 Architecture

**Architecture set status:** DESIGN IN PROGRESS — NOT FROZEN

## Purpose and authority boundary

This directory contains the normative M2 TO-BE architecture required to satisfy the frozen milestone contract in `../contract.md`.

Implementation authority is composed as follows:

```text
current delivered AS-IS in docs/architecture/
+
FINAL / FROZEN M2 contract
+
FROZEN M2 architecture delta
=
implementation authority for M2
```

This README controls architecture-set composition, ownership coverage and set-level status. Detailed semantic and technical decisions belong to the owning documents indexed here and must not be duplicated as competing authorities.

Discovery material under `../wip/` is non-normative input. It must be distilled into the owning architecture documents before the set can freeze.

## Current baseline

The starting architecture is the delivered AS-IS under:

```text
docs/architecture/
```

The milestone obligations and authorized deltas are frozen in:

```text
docs/milestones/M2/contract.md
```

No M2 architecture document is frozen yet. Implementation planning and implementation remain unauthorized.

## Normative document map

| Area | Owning document | Status |
|---|---|---|
| Architecture set control, coverage and freeze | `README.md` | DESIGN IN PROGRESS |
| Relationship domain, version lifecycle and factual semantics | `relationship.md` | DRAFT — SEMANTIC DESIGN COMPLETE; API/PERSISTENCE/CONCURRENCY-MATRIX CROSS-CHECK PASSED |
| Public HTTP API, projections, failures and pagination | `api.md` | DRAFT — WIRE DESIGN COMPLETE; PERSISTENCE/CONCURRENCY-MATRIX CROSS-CHECK PASSED |
| Persistence authority, relational schema, lifecycle codec, indexes and Alembic realization | `persistence.md` | DRAFT — PHYSICAL DESIGN COMPLETE; TRANSACTION/DEADLOCK/SEMANTIC-MATRIX CROSS-CHECK PASSED |
| Complete semantic mutation census and pairwise matrix | `concurrency-matrix.md` | DRAFT — SEMANTIC MATRIX COMPLETE |
| PostgreSQL lock, gate, retry and deadlock realization | `concurrency.md` | NOT STARTED |
| Core Health API | `health.md` | NOT STARTED |
| Official NETAUTO CLI | `cli.md` | NOT STARTED |
| Runtime configuration, packaging, startup guard, deployment and trust/TLS boundaries | `runtime-deployment.md` | NOT STARTED |
| Verification, acceptance evidence and traceability | `verification.md` | NOT STARTED |

A document may own only the areas assigned here. Cross-document consequences must be referenced rather than redefined.

## Initial coverage and ownership map

The initial outcome ownership is:

```text
relationship.md
    M2-OUT-01
    M2-OUT-02
    M2-OUT-03
    M2-OUT-04
    M2-OUT-05

api.md
    M2-OUT-04
    M2-OUT-06
    M2-OUT-07
    M2-OUT-11
    M2-OUT-12

persistence.md
    M2-OUT-03
    M2-OUT-07
    M2-OUT-09

concurrency-matrix.md + concurrency.md
    M2-OUT-02
    M2-OUT-04
    M2-OUT-08

health.md
    M2-OUT-11

cli.md
    M2-OUT-12
    M2-OUT-13
    M2-OUT-15

runtime-deployment.md
    M2-OUT-10
    M2-OUT-13
    M2-OUT-14
    M2-OUT-15

verification.md
    M2-OUT-16
    all M2-AC acceptance criteria
    architecture-set traceability and consistency closure
```

Shared outcomes require coordinated owners, but each individual invariant, public contract and realization rule must still have one explicit normative home.

## Current architecture progress

```text
relationship.md
    -> normative draft created
    -> Relationship semantic design complete
    -> API, persistence and semantic-concurrency cross-check passed
    -> PostgreSQL realization and verification review pending

api.md
    -> normative draft created
    -> final business and Health wire design complete
    -> Relationship, persistence and semantic-concurrency cross-check passed
    -> Health, CLI, PostgreSQL realization and verification review pending

persistence.md
    -> normative draft created
    -> fifteen-table authority, constraints, lifecycle codec,
       index inventory and first durable Alembic baseline complete
    -> transaction validity cross-check passed
    -> architecture-level deadlock wait-graph cross-check passed
    -> semantic concurrency-matrix cross-check passed
    -> exact PostgreSQL realization and deterministic evidence pending

concurrency-matrix.md
    -> normative draft created
    -> canonical census complete: 41 mutations
    -> all 15 family blocks and 861 unordered cells classified
    -> delivered 19 predicates preserved
    -> VH schema-history and RS factual-Relationship-state predicates added
    -> frozen M2 conflict/delete outcomes propagated
    -> PostgreSQL realization and deterministic evidence pending
```

The completed semantic/persistence review requires the first durable baseline to preserve:

```text
complete pre-DML lock plans
advisory-gate-first acquisition
one new model-root delete gate
no normal row-lock upgrades
existing-owner FK target-before-owner ordering
differential declaration replacement
CREATE_NEXT cloned-reference lifetime holds
deterministic closure/event writes
whole-UoW restart for stale optimistic lock plans
```

These are architecture hardening requirements and do not alter the frozen public contract.

No M2 architecture document is frozen yet.

## Required architecture work

Before the set can freeze it must at least:

1. cross-check and freeze the Relationship semantic, API wire, persistence and semantic-concurrency owners with every dependent owner;
2. define the exact PostgreSQL lock helpers, modes, gate registry, acquisition plan, restart/retry boundary and deadlock-proof realization;
3. extend the deterministic real-PostgreSQL scenario registry to prove every predicate, intended progress outcome and absence of supported-path deadlocks;
4. freeze Health, startup revision guard, CLI and runtime/deployment behavior at architecture level;
5. define complete deterministic verification and traceability registries;
6. perform cross-document consistency, AS-IS and contract-coverage sweeps;
7. resolve every architecture finding without altering the frozen contract.

## Open design points

The following architecture work remains open:

```text
exact PostgreSQL implementation of the canonical lock planner
MODEL_ROOT_DELETE_GATE and gate-first realization
whole-UoW restart/retry and SQLSTATE handling
new deterministic VH/RS/FK/rebind/root-delete/no-40P01 scenarios
final persistence-boundary/module review
Health and startup-guard realization
CLI grammar, transport, operation mapping and output realization
runtime/deployment realization
verification registry and evidence map
architecture consistency closure
```

These are architecture decisions about how to satisfy the frozen contract. Any finding that would change Scope, Non-goals, explicit deltas, Required outcomes or Acceptance criteria requires formal contract reopening.

## Freeze condition

The architecture set may become `FROZEN` only when:

- `../contract.md` remains `FINAL / FROZEN`;
- every contract area and every `M2-OUT-*` outcome has an explicit normative owner;
- all required semantic, persistence, concurrency, API, failure, runtime, CLI, Health and verification decisions are closed;
- every `M2-AC-*` criterion has a traceable architecture and verification path;
- every supported multi-resource mutation has a complete deterministic lock plan;
- every non-trivial semantic matrix rule has a concrete PostgreSQL realization and deterministic scenario;
- deterministic real-PostgreSQL evidence covers the required semantic races and contains no supported-path `40P01`;
- cross-document consequences are propagated without duplicated authority;
- no relevant open, contradictory or partially reopened point remains;
- the complete set passes AS-IS, contract-coverage and consistency sweeps.

Until then, `steps.md` must remain not frozen and implementation of M2 behavior is not authorized.
