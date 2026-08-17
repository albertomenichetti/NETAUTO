# M2 Architecture

**Architecture set status:** DESIGN COMPLETE — FINAL TRACEABILITY / CONSISTENCY CLOSURE PENDING — NOT FROZEN

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

This README owns architecture-set composition, owner coverage, gate interpretation and set-level status. Detailed semantic and technical decisions belong only to the owning documents indexed below and must not be duplicated as competing authorities.

Discovery material under `../wip/` is non-normative input. Every implemented M2 behavior must be traceable to the frozen contract and, after set freeze, to one normative owner here.

## Current baseline and governance state

```text
contract.md
    FINAL / FROZEN

architecture set
    design owners complete
    final cross-document closure pending
    NOT FROZEN

steps.md
    NOT STARTED / NOT FROZEN

implementation
    NOT AUTHORIZED
```

Architecture freeze requires complete design and traceability, not executed M2 implementation evidence. Executed evidence belongs to future implementation-slice and final-delivery gates defined by `verification.md` and the future frozen `steps.md`.

## Normative document map

| Area | Owning document | Status |
|---|---|---|
| Architecture set control, coverage and freeze | `README.md` | FINAL CLOSURE IN PROGRESS |
| Relationship domain, version lifecycle and factual semantics | `relationship.md` | DRAFT — DESIGN COMPLETE; CROSS-OWNER REVIEW PASSED |
| Public HTTP API, projections, failures and pagination | `api.md` | DRAFT — DESIGN COMPLETE; CROSS-OWNER REVIEW PASSED |
| Persistence authority, relational schema, lifecycle codec, indexes and Alembic realization | `persistence.md` | DRAFT — DESIGN COMPLETE; TRANSACTION/DEADLOCK/CROSS-OWNER REVIEW PASSED |
| Complete semantic mutation census and pairwise matrix | `concurrency-matrix.md` | DRAFT — 41-MUTATION / 861-CELL MATRIX COMPLETE |
| PostgreSQL lock, gate, retry and deadlock realization | `concurrency.md` | DRAFT — REALIZATION COMPLETE; ARCHITECTURE DEADLOCK PROOF PASSED |
| Core Health API | `health.md` | DRAFT — DESIGN COMPLETE; API/CLI/RUNTIME/VERIFICATION REVIEW PASSED |
| Official NETAUTO CLI | `cli.md` | DRAFT — DESIGN COMPLETE; API/HEALTH/RUNTIME/VERIFICATION/STACK-10 REVIEW PASSED; FINAL CLOSURE PENDING |
| Runtime configuration, packaging, startup guard, deployment and trust/TLS boundaries | `runtime-deployment.md` | DRAFT — DESIGN COMPLETE; CROSS-OWNER/STACK-10 REVIEW PASSED; FINAL CLOSURE PENDING |
| Verification, acceptance evidence and traceability | `verification.md` | DRAFT — DESIGN COMPLETE; HEALTH/CLI/RUNTIME HOOK REVIEW PASSED; FINAL TRACEABILITY CLOSURE PENDING |

A document may own only the area assigned above. Cross-document consequences are referenced rather than redefined.

## Outcome ownership map

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
    all M2-VER evidence bundles
    deterministic concurrency and surface registries
    architecture-set traceability and consistency closure
```

Shared outcomes require coordinated owners, but every invariant, public contract, realization rule and evidence obligation has one explicit normative home.

## Completed architecture design

```text
relationship.md
    -> stable topology and factual identity preservation
    -> RDV lifecycle/default/property-history semantics
    -> exact factual pin and canonical properties
    -> CREATE / DATA_CHANGE / SCHEMA_CHANGE / DELETE
    -> lifecycle and corruption boundaries

api.md
    -> exact 63-operation business inventory
    -> strict request/response/failure contracts
    -> Relationship/RDV projections and lifecycle union
    -> /health/core wire contract
    -> CLI coverage authority

persistence.md
    -> authoritative fifteen-table model
    -> final keys, constraints, delete actions and indexes
    -> JSONB current/history authority and lifecycle codec
    -> first durable Alembic root baseline
    -> transaction-valid and deadlock-safe persistence pipelines

concurrency-matrix.md
    -> 41 mutation primitives
    -> 15 family blocks
    -> all 861 unordered cells classified
    -> delivered predicates preserved; VH and RS added

concurrency.md
    -> complete centralized lock planner
    -> three-gate registry
    -> canonical row order and sufficient initial lock modes
    -> all 41 mutation lock plans
    -> bounded whole-UoW restart and SQLSTATE policy
    -> supported wait-for graph acyclic by construction

health.md
    -> same runtime engine/pool as business work
    -> exact SELECT 1 active probe
    -> fixed two-second whole-probe deadline
    -> safe 200/503 result and startup-guard separation

cli.md
    -> interactive and non-interactive process contracts
    -> static exact 63-operation registry
    -> HTTP-only execution and deterministic selector resolution
    -> verified HTTPS, no insecure bypass or credential storage
    -> exact FORMATTED/JSON trace, help and in-memory history

runtime-deployment.md
    -> exact application/pool settings and secret-source composition
    -> one-wheel server/CLI/Alembic distribution
    -> embedded exact runtime dependency lock exported from uv.lock
    -> installed package-resource Alembic graph and unique-head discovery
    -> exact pre-serving startup revision guard
    -> Health composition from the same worker engine
    -> reproducible manual Linux install/start/stop/restart/readiness procedure
    -> trusted-boundary HTTP and external TLS responsibility

STACK-10
    -> HTTPX AsyncClient as the official client transport
    -> prompt_toolkit as the asynchronous REPL terminal foundation
    -> stdlib process/token/JSON/file parsing
    -> no general CLI framework or dynamic OpenAPI command generation

verification.md
    -> T0 ... T10 layers
    -> M2-VER-01 ... M2-VER-32 bundles
    -> canonical 83-scenario concurrency registry
    -> all 21 predicates mapped to deterministic evidence
    -> positive/negative surface, installed artifact and final acceptance contracts
```

## Cross-cutting architecture obligations

The complete first durable baseline must preserve:

```text
one semantic mutation / one PostgreSQL UoW
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
bounded whole-UoW restart only for approved causes
no automatic retry of SQLSTATE 40P01
stable verification/evidence identifiers
exact positive and negative surface inventories
same runtime engine/pool for business, startup inspection and Health
a fixed two-second full Health database-probe deadline
no Health/Alembic responsibility overlap
one static exact 63-operation CLI registry
HTTP-only CLI execution with no application/persistence path
no mandatory Health preflight for non-interactive commands
verified HTTPS with no insecure bypass
no persistent endpoint, credentials or command history
one wheel containing server, CLI, release metadata and Alembic graph
one exact embedded runtime dependency lock derived from committed uv.lock
unique shipped Alembic head as the sole expected-revision authority
exact database revision equality before any HTTP serving
```

These are realization obligations and do not introduce any public behavior beyond the frozen contract.

## Verification gate separation

```text
architecture freeze
    -> complete normative design
    -> complete M2-OUT / M2-AC / M2-VER traceability
    -> complete deterministic concurrency and surface registries
    -> ratified required technologies
    -> no open architecture finding

implementation-slice completion
    -> assigned evidence targets implemented and passing
    -> affected AS-IS regression evidence preserved

final delivery
    -> every M2-VER bundle and canonical scenario executed and PASS
    -> no supported SQLSTATE 40P01
    -> schema drift = []
    -> installed wheel, startup, Health, CLI and Linux operation PASS
```

## Remaining work before architecture freeze

Only set-level closure remains:

1. perform the final owner-by-owner `M2-OUT -> M2-AC -> M2-VER -> implementation-path` traceability sweep;
2. perform the final frozen-contract, AS-IS, cross-document authority, terminology and normative-hygiene consistency sweep;
3. resolve every resulting finding without changing the frozen contract;
4. mark every owner and this complete architecture set `FINAL / FROZEN` in one dedicated freeze transition.

The following are no longer open architecture decisions:

```text
Relationship semantics
public M2 HTTP contract
persistence schema/lifecycle/index/Alembic model
semantic concurrency matrix
PostgreSQL lock/gate/retry/deadlock design
Core Health application/query/timeout design
official CLI grammar/transport/selectors/output design
runtime settings, packaging, Alembic installation, startup and Linux operation
verification layers, evidence bundles and scenario registry
```

A finding that would change Scope, Non-goals, explicit deltas, Required outcomes or Acceptance criteria requires formal contract reopening. A compatible architecture clarification does not.

## Freeze condition

The architecture set may become `FINAL / FROZEN` only when:

- `../contract.md` remains `FINAL / FROZEN`;
- every contract area and every `M2-OUT-*` outcome has an explicit normative owner;
- every required semantic, persistence, concurrency, API, runtime, CLI, Health, security and verification **design** decision is closed;
- every `M2-AC-*` maps to exactly one stable `M2-VER-*` bundle and a traceable implementation path;
- every supported multi-resource mutation has a complete deterministic lock plan;
- every non-trivial semantic-matrix rule has a concrete PostgreSQL realization, stable scenario ID, recipe and expected assertion;
- all positive and negative HTTP/CLI/schema/runtime inventories are complete;
- every project-wide technology required by M2 is ratified in `docs/general/technology_baseline.md`;
- cross-document consequences are propagated without duplicated authority;
- no relevant open, contradictory or partially reopened architecture point remains;
- the complete set passes contract, AS-IS, coverage, authority, terminology and normative-hygiene sweeps;
- `steps.md` can decompose implementation and executed evidence without making a new semantic, technology or architecture decision.

Until then, `steps.md` remains not frozen and M2 implementation remains unauthorized.
