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
| Relationship domain, version lifecycle and factual semantics | `relationship.md` | DRAFT — SEMANTIC DESIGN COMPLETE; API CROSS-CHECK PASSED |
| Public HTTP API, projections, failures and pagination | `api.md` | DRAFT — WIRE DESIGN COMPLETE |
| Persistence authority, relational schema, lifecycle codec, indexes and Alembic realization | `persistence.md` | NOT STARTED |
| Complete semantic mutation census and pairwise matrix | `concurrency-matrix.md` | NOT STARTED |
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
    -> API wire cross-check passed
    -> persistence, concurrency and verification review pending

api.md
    -> normative draft created
    -> final business and Health wire design complete
    -> Relationship semantic cross-check passed
    -> persistence, Health, CLI, concurrency and verification review pending
```

No M2 architecture document is frozen yet.

## Required architecture work

Before the set can freeze it must at least:

1. cross-check and freeze the Relationship semantic and API wire owners with every dependent owner;
2. propagate and close the complete persistence metadata, lifecycle codec, index and Alembic realization;
3. build the complete mutation census and pairwise semantic concurrency matrix;
4. define PostgreSQL lock ownership, modes, ordering, advisory gates, retries and constraint arbitration;
5. freeze Health, startup revision guard, CLI and runtime/deployment behavior at architecture level;
6. define complete deterministic verification and traceability registries;
7. perform cross-document consistency, AS-IS and contract-coverage sweeps;
8. resolve every architecture finding without altering the frozen contract.

## Open design points

The following architecture work remains open:

```text
Relationship/API cross-review with persistence and concurrency
normative persistence propagation from WIP discovery
complete concurrency matrix
PostgreSQL realization
final module and persistence-boundary ownership
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
- cross-document consequences are propagated without duplicated authority;
- no relevant open, contradictory or partially reopened point remains;
- the complete set passes AS-IS, contract-coverage and consistency sweeps.

Until then, `steps.md` must remain not frozen and implementation of M2 behavior is not authorized.
