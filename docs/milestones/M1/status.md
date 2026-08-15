# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S07 — Runtime Relationship and relationship lifecycle vertical slice
```

**Step status:** IN PROGRESS

M1-S00 through M1-S06 have completed implementation review.

## M1-S06 accepted baseline

Accepted implementation:

```text
1c21ac046505e383b707b3f7e328b82921257673
+
e4fd891a9ef606ea43eaf4aa38029d33619ddbf8
    API error-detail review fix
```

The reviewed S06 capability includes:

- complete `RelationshipDefinition` + authoritative `RelationshipResolution` aggregate semantics;
- deterministic symmetric/non-symmetric Resolution-set derivation with kernel-generated stable identities;
- semantic equivalence and cross-Definition conflict certification over ObjectTemplate lineage-overlap spaces;
- `RELATIONSHIP_DEFINITION_CONFLICT_GATE` for CREATE/RENAME only, with mandatory separate fresh post-gate certified-set read;
- coherent one-statement certified Definition+Resolution set decoding;
- Definition RENAME `FOR NO KEY UPDATE`, DELETE `FOR UPDATE`, and DELETE without conflict gate;
- stable ObjectTemplate lineage FK `RESTRICT` lifetime semantics without exact-OTV admission or generic lifecycle locking;
- atomic complete Resolution-name RENAME;
- RelationshipDefinition CREATE/RENAME/DELETE/GET/list public API;
- ObjectTemplate `relationship-capabilities` projection/list with inherited applicability, exact name filtering and `resolution_id ASC` keyset pagination;
- no standalone RelationshipResolution API, runtime Relationship capability, Relationship lifecycle event variant, migration or new advisory gate.

The final review-fix aligned API-03.11 error details by:

- returning bounded factual Relationship blocker type/count information for `RD.DELETE -> delete_blocked`;
- preserving the failed ObjectTemplate endpoint UUID through the bounded FK-race persistence error so `referenced_resource_not_found.details.id` remains the semantic missing lineage selector.

### Final S06 deterministic PostgreSQL coverage

The accepted suite includes:

```text
ROW-17      RD.RENAME × RD.DELETE, both serial orders
REF-01      RD.CREATE × ObjectTemplate whole-lineage DELETE, both directions
GATE-04 A/B equivalent and non-equivalent conflicting concurrent CREATE
GATE-05 A/B CREATE × RENAME; RENAME(D1) × RENAME(D2)
GATE-06 A/B fresh post-gate visibility; blocker DELETE concurrent with candidate
ATOMIC-04C  complete Resolution-name mutation rollback/atomicity
```

Additional REALIZE-12 mechanism coverage proves same-Definition rename ownership before the gate, intentional global gate over-serialization, transaction-level gate lifetime/release on rollback, coherent protected certified-set reads and absence of fan-out Definition row locking.

### Final S06 quality gates

Reported on PostgreSQL 16.14:

```text
uv lock --check                         PASS
uv sync --locked                        PASS
uv build                                PASS
Ruff format/check                       PASS
Pyright strict                          PASS
non-PostgreSQL                          101 passed
PostgreSQL                              106 passed
```

No S06 completion blocker remains.

## M1-S07 pre-flight outcome

The mandatory S07 pre-flight re-read the current frozen runtime Relationship, RelationshipResolution, lifecycle, persistence/UoW, REALIZE-13/14/15, PGTEST and API-03 authorities together with the accepted S06 implementation seams.

Confirmed:

```text
M1 contract      FINAL / FROZEN
M1 architecture  FROZEN as a set
M1 steps         FINAL / FROZEN
M1-S00..S06      COMPLETED
STACK-01..09     RATIFIED
```

The initial S07 pre-flight found one verification-decomposition drift, not a domain/architecture semantic gap: `REF-03` (`REL.CREATE × OBJ.DELETE`) and the Relationship `REF-05` variant (`REL.DELETE × OBJ.DELETE`) require final `Object.DELETE`, which is deliberately delivered only in M1-S08. `steps.md` already states globally that spanning scenarios are executed only when both operations exist.

The S07/S08 allocation was therefore realigned without changing any frozen Relationship semantics:

```text
9cda795b523cbf525beb19ed620678db152490a1
    docs: align M1-S07 Object delete race allocation
```

S07 now implements/tests all runtime Relationship behavior and all canonical scenarios whose semantic operations are available in S07, including `ARB-05..07`, `REF-04`, `SNAP-01..03`, `ATOMIC-02`, `ATOMIC-03`, `PAR-01`, `PAR-02` and `PAR-05`. It must still prove current RuntimeRelationshipResolution -> Object FK `RESTRICT` mechanics directly at persistence level. Semantic `REF-03` and Relationship `REF-05` are completed in S08 together with final `Object.DELETE`; no fake/private Object.DELETE is introduced.

The mandatory re-pre-flight against the corrected decomposition is clean. No architecture/documentation contradiction is currently known for S07.

Frozen S07 implementation boundaries include:

- Relationship CREATE from exact `resolution_id + from_object_id + to_object_id`;
- stable-lineage endpoint admission, no exact OTV dependency;
- non-symmetric selected-perspective semantics and symmetric unordered-pair semantics;
- deterministic complete runtime Resolution closure;
- exact-view PK arbitration, whole-UoW rollback and fresh semantic-UoW restart/convergence;
- distinct `relationship_fact_conflict` boundary for a candidate closure colliding with a distinct current fact rather than selected-view convergence;
- exact-ID DELETE with `FOR UPDATE`, idempotent absence and ABA safety;
- one-statement READ COMMITTED lifecycle metadata observation for each real Relationship transition;
- semantic-view event dedup and atomic complete event sets;
- factual Relationship GET and Object-relative semantic reads;
- lifecycle response union extension through Relationship events;
- Definition/Object FK lifetime semantics with no global runtime Relationship gate;
- no migration, S08 Object.DELETE, Relationship versioning/properties or source/target semantics.

The non-normative Codex execution prompt is:

```text
docs/milestones/M1/wip/M1-S07-codex-prompt.md
```

Prompt creation commit:

```text
e9c5b52d3b20ac6ee42570274ef8cd80743f6bf9
```

The prompt is an implementation aid only. `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

## Authoritative baseline

M1 implementation proceeds from the frozen/ratified authorities:

```text
docs/milestones/M1/contract.md
    FINAL / FROZEN

docs/milestones/M1/architecture/README.md
    FROZEN global architecture baseline

docs/milestones/M1/steps.md
    FINAL / FROZEN implementation decomposition

docs/general/technology_baseline.md
    STACK-01..STACK-09 ratified

AGENTS.md
    repository-level operating contract
```

Before each implementation step, the mandatory pre-flight defined by `AGENTS.md`, `docs/general/linee_guida_progetto.md` and the step itself must be executed against the current normative repository documents.

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  COMPLETED        Ownership and Object schema-change vertical slice
M1-S06  COMPLETED        RelationshipDefinition model-plane and capability vertical slice
M1-S07  IN PROGRESS      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for implementing M1-S07.

PostgreSQL-dependent verification requires an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation choice: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
