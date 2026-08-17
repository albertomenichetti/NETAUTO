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
| Relationship domain, version lifecycle and factual semantics | `relationship.md` | DRAFT — SEMANTIC DESIGN COMPLETE; API/PERSISTENCE/CONCURRENCY CROSS-CHECK PASSED |
| Public HTTP API, projections, failures and pagination | `api.md` | DRAFT — WIRE DESIGN COMPLETE; PERSISTENCE/CONCURRENCY CROSS-CHECK PASSED |
| Persistence authority, relational schema, lifecycle codec, indexes and Alembic realization | `persistence.md` | DRAFT — PHYSICAL DESIGN COMPLETE; TRANSACTION/DEADLOCK/SEMANTIC-MATRIX/POSTGRESQL-REALIZATION CROSS-CHECK PASSED |
| Complete semantic mutation census and pairwise matrix | `concurrency-matrix.md` | DRAFT — SEMANTIC MATRIX COMPLETE; POSTGRESQL CROSS-CHECK PASSED |
| PostgreSQL lock, gate, retry and deadlock realization | `concurrency.md` | DRAFT — POSTGRESQL REALIZATION COMPLETE; DEADLOCK PROOF PASSED |
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
    -> API, persistence and complete concurrency cross-check passed
    -> verification review pending

api.md
    -> normative draft created
    -> final business and Health wire design complete
    -> Relationship, persistence and complete concurrency cross-check passed
    -> Health, CLI and verification review pending

persistence.md
    -> normative draft created
    -> fifteen-table authority, constraints, lifecycle codec,
       index inventory and first durable Alembic baseline complete
    -> transaction validity and architecture deadlock proof passed
    -> semantic matrix and PostgreSQL realization cross-check passed
    -> deterministic evidence pending

concurrency-matrix.md
    -> normative draft created
    -> canonical census complete: 41 mutations
    -> all 15 family blocks and 861 unordered cells classified
    -> delivered 19 predicates preserved
    -> VH schema-history and RS factual-Relationship-state predicates added
    -> PostgreSQL realization cross-check passed
    -> deterministic evidence pending

concurrency.md
    -> normative draft created
    -> complete lock planner and three-gate registry closed
    -> all 41 mutation lock plans closed
    -> all 21 predicates mapped to PostgreSQL authorities
    -> bounded whole-UoW restart and SQLSTATE policy closed
    -> intended blocking/non-blocking contract closed
    -> supported wait-for graph proven acyclic at architecture level
    -> deterministic real-PostgreSQL evidence pending
```

The completed semantic/persistence/concurrency review requires the first durable baseline to preserve:

```text
complete pre-DML lock plans
advisory-gate-first acquisition
one new model-root delete gate
no normal row-lock upgrades
one canonical row-class/intra-class order
existing-owner direct-FK target-before-owner ordering
child-FK target-before-DML ordering
differential declaration replacement
CREATE_NEXT cloned-reference lifetime holds
deterministic closure/event writes
bounded whole-UoW restart for approved causes
no automatic retry of SQLSTATE 40P01
```

These are architecture hardening requirements and do not alter the frozen public contract.

No M2 architecture document is frozen yet.

## Required architecture work

Before the set can freeze it must at least:

1. cross-check and freeze the Relationship semantic, API wire, persistence, semantic-matrix and PostgreSQL realization owners with every remaining dependent owner;
2. extend the deterministic real-PostgreSQL scenario registry to prove every predicate, intended progress outcome, retry boundary and absence of supported-path deadlocks;
3. freeze Health, startup revision guard, CLI and runtime/deployment behavior at architecture level;
4. define complete deterministic verification and contract/architecture traceability;
5. perform cross-document consistency, AS-IS and contract-coverage sweeps;
6. resolve every architecture finding without altering the frozen contract.

## Open design points

The following architecture work remains open:

```text
deterministic VH/RS/FK/rebind/root-delete/no-40P01 scenarios
real-PostgreSQL lock-planner and SQLSTATE evidence
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
