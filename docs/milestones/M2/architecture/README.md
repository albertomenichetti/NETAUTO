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

This README controls architecture-set composition, ownership coverage, gate interpretation and set-level status. Detailed semantic and technical decisions belong to the owning documents indexed here and must not be duplicated as competing authorities.

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
| Relationship domain, version lifecycle and factual semantics | `relationship.md` | DRAFT — SEMANTIC DESIGN COMPLETE; API/PERSISTENCE/CONCURRENCY/VERIFICATION-DESIGN CROSS-CHECK PASSED |
| Public HTTP API, projections, failures and pagination | `api.md` | DRAFT — WIRE DESIGN COMPLETE; PERSISTENCE/CONCURRENCY/VERIFICATION-DESIGN CROSS-CHECK PASSED |
| Persistence authority, relational schema, lifecycle codec, indexes and Alembic realization | `persistence.md` | DRAFT — PHYSICAL DESIGN COMPLETE; TRANSACTION/DEADLOCK/SEMANTIC-MATRIX/POSTGRESQL/VERIFICATION-DESIGN CROSS-CHECK PASSED |
| Complete semantic mutation census and pairwise matrix | `concurrency-matrix.md` | DRAFT — SEMANTIC MATRIX COMPLETE; POSTGRESQL/VERIFICATION-REGISTRY CROSS-CHECK PASSED |
| PostgreSQL lock, gate, retry and deadlock realization | `concurrency.md` | DRAFT — POSTGRESQL REALIZATION COMPLETE; DEADLOCK PROOF / VERIFICATION-REGISTRY CROSS-CHECK PASSED |
| Core Health API | `health.md` | NOT STARTED |
| Official NETAUTO CLI | `cli.md` | NOT STARTED |
| Runtime configuration, packaging, startup guard, deployment and trust/TLS boundaries | `runtime-deployment.md` | NOT STARTED |
| Verification, acceptance evidence and traceability | `verification.md` | DRAFT — VERIFICATION DESIGN COMPLETE; DEPENDENT-OWNER REVIEW PENDING |

A document may own only the areas assigned here. Cross-document consequences must be referenced rather than redefined.

## Initial coverage and ownership map

The outcome ownership is:

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
    all deterministic scenario/evidence registries
    architecture-set traceability and consistency closure
```

Shared outcomes require coordinated owners, but each individual invariant, public contract, realization rule and evidence obligation has one explicit normative home.

## Current architecture progress

```text
relationship.md
    -> normative draft created
    -> Relationship semantic design complete
    -> API, persistence, complete concurrency and verification-design
       cross-check passed
    -> dependent-owner final review pending

api.md
    -> normative draft created
    -> final business and Health wire design complete
    -> Relationship, persistence, complete concurrency and
       verification-design cross-check passed
    -> Health and CLI owner review pending

persistence.md
    -> normative draft created
    -> fifteen-table authority, constraints, lifecycle codec,
       index inventory and first durable Alembic baseline complete
    -> transaction validity and architecture deadlock proof passed
    -> semantic matrix, PostgreSQL realization and verification-design
       cross-check passed
    -> runtime packaging/head-discovery review pending

concurrency-matrix.md
    -> normative draft created
    -> canonical census complete: 41 mutations
    -> all 15 family blocks and 861 unordered cells classified
    -> delivered 19 predicates preserved; VH and RS added
    -> PostgreSQL and verification-registry cross-check passed

concurrency.md
    -> normative draft created
    -> complete lock planner and three-gate registry closed
    -> all 41 mutation lock plans closed
    -> all 21 predicates mapped to PostgreSQL authorities
    -> bounded whole-UoW restart and SQLSTATE policy closed
    -> intended blocking/non-blocking contract closed
    -> supported wait-for graph proven acyclic at architecture level
    -> verification-registry cross-check passed

verification.md
    -> normative draft created
    -> T0 ... T10 verification layers closed
    -> M2-VER-01 ... M2-VER-32 evidence bundles closed
    -> canonical 83-scenario registry closed
    -> all 21 predicates mapped to deterministic evidence
    -> AS-IS regression, negative surface and final acceptance
       evidence contract closed
    -> Health, CLI and runtime-deployment implementation-hook review pending
```

The completed semantic/persistence/concurrency/verification review requires the first durable baseline to preserve:

```text
complete pre-DML lock plans
advisory-gate-first acquisition
one model-root delete gate
no normal row-lock upgrades
one canonical row-class/intra-class order
existing-owner direct-FK target-before-owner ordering
child-FK target-before-DML ordering
differential declaration replacement
CREATE_NEXT cloned-reference lifetime holds
deterministic closure/event writes
bounded whole-UoW restart for approved causes
no automatic retry of SQLSTATE 40P01
stable verification/evidence identifiers
exact positive and negative surface inventories
```

These are architecture requirements and do not alter the frozen public contract.

## Verification gate separation

Architecture freeze and delivery evidence are deliberately separate.

```text
architecture freeze
    -> complete normative design
    -> complete M2-OUT / M2-AC / M2-VER traceability
    -> complete deterministic scenario registry
    -> no open architecture decision

implementation-slice completion
    -> affected evidence targets implemented and passing

final delivery
    -> every M2-VER bundle and canonical scenario executed and PASS
    -> no supported SQLSTATE 40P01
    -> installed artifact and operating evidence PASS
```

Implementation evidence cannot be a prerequisite for architecture freeze because implementation is not authorized until the architecture is frozen. This separation does not weaken final acceptance; it places execution at the only governance stage where M2 code may exist.

## Required architecture work

Before the set can freeze it must at least:

1. create and cross-check `health.md` against `api.md`, `verification.md` and the startup/runtime boundary;
2. create and cross-check `cli.md` against the exact 63-operation business inventory and `M2-VER-25 ... 28`;
3. create and cross-check `runtime-deployment.md` against Alembic packaging, startup guard, Linux operation, trust/TLS and `M2-VER-22`, `24`, `29`, `30`;
4. perform final owner-by-owner M2-OUT / M2-AC / M2-VER traceability closure;
5. perform contract, AS-IS, cross-document authority and normative-hygiene sweeps;
6. resolve every architecture finding without altering the frozen contract.

## Open design points

The following architecture work remains open:

```text
Health application/query/timeout realization
CLI grammar, transport, terminal and exact operation mapping
runtime settings, installed migration/head discovery and Linux procedure
dependent-owner verification-hook confirmation
technology ratification required by final CLI design, if any
final architecture consistency closure
```

The following are no longer open architecture decisions:

```text
Relationship semantics
public M2 HTTP contract
persistence schema/lifecycle/index/Alembic model
semantic concurrency matrix
PostgreSQL lock/gate/retry/deadlock design
verification layers, stable bundles and scenario registry
```

Any finding that would change Scope, Non-goals, explicit deltas, Required outcomes or Acceptance criteria requires formal contract reopening.

## Freeze condition

The architecture set may become `FROZEN` only when:

- `../contract.md` remains `FINAL / FROZEN`;
- every contract area and every `M2-OUT-*` outcome has an explicit normative owner;
- all required semantic, persistence, concurrency, API, failure, runtime, CLI, Health and verification **design** decisions are closed;
- every `M2-AC-*` criterion maps to exactly one stable `M2-VER-*` bundle and a traceable implementation path;
- every supported multi-resource mutation has a complete deterministic lock plan;
- every non-trivial semantic matrix rule has a concrete PostgreSQL realization, stable scenario ID, recipe and expected assertion;
- all positive and negative surface inventories are complete;
- cross-document consequences are propagated without duplicated authority;
- no relevant open, contradictory or partially reopened architecture point remains;
- the complete set passes AS-IS, contract-coverage and consistency sweeps;
- `steps.md` can decompose implementation and executed evidence without making a new semantic or architecture decision.

Executed M2 implementation tests and final artifact evidence are not architecture-freeze prerequisites. They are mandatory implementation-slice and final-delivery gates defined by `verification.md` and the future frozen `steps.md`.

Until the architecture set is frozen, `steps.md` must remain not frozen and implementation of M2 behavior is not authorized.
