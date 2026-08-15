# M1 — Implementation Status

**Milestone status:** DELIVERED

## Final step

```text
M1-S09 — Full M1 acceptance, regression and delivery gate
```

**Step status:** COMPLETED

All M1 implementation and acceptance steps have completed review.

## Accepted S09 evidence baseline

```text
b7c3722ba7964841d28fb8eb63e1bf828f078ff8  Complete M1 acceptance evidence
40e5c5946ebf38a93de4e4c683ca567694acfd58  Correct final Ruff evidence count
```

S09 introduced no production capability. Its accepted repository delta is limited to:

```text
README.md
    reproducible setup / migration / Uvicorn / verification commands

docs/milestones/M1/acceptance.md
    final AC-01..AC-10 and verification evidence record

tests/test_m1_traceability.py
    machine-checkable canonical PGTEST / safety-predicate registry
```

Final reviewer-only closure then aligned README/acceptance wording with the delivered state and corrected one editorial T1 suite-count description. No production code, migration or normative architecture semantics changed during closure.

## Final acceptance outcome

Accepted verification on CPython 3.14.7 and PostgreSQL 16.14:

```text
AC-01..AC-10                           PASS
STACK-07 T0..T6                        PASS
canonical PGTEST                       51 / 51
non-I safety predicates                19 / 19
unique registry target nodes           79 passed
API census                             32 mutation / 20 read / 23 error codes
full suite                             268 passed
non-PostgreSQL                         125 passed
real PostgreSQL                        143 passed
deterministic concurrency              106 passed
API                                    30 passed
migration                              1 passed
Hypothesis properties                  4 passed
Ruff format/check                      PASS
Pyright strict                         PASS — 0 errors / 0 warnings
uv lock / locked sync / build          PASS
base -> head / 0001+0002 / drift       PASS
branch-aware coverage                  87% over 3,749 statements
```

Coverage remains diagnostic evidence; no arbitrary percentage threshold is part of the M1 contract.

The durable final acceptance record is:

```text
docs/milestones/M1/acceptance.md
```

## Delivered M1 capability

The delivered M1 kernel provides the frozen PostgreSQL-backed baseline for:

- `DataType` / `PrimitiveType`;
- `ObjectTemplate` model graph and effective schema;
- `Object` intrinsic state, ownership, schema change and lifecycle;
- `RelationshipDefinition` / `RelationshipResolution` model plane;
- factual runtime `Relationship` and semantic lifecycle/navigation;
- cross-domain deletion/reference integrity;
- strict `/api/v1/core` HTTP/JSON contract;
- deterministic PostgreSQL concurrency verification.

The accepted physical baseline includes the explicitly re-frozen S07 correction:

```text
RelationshipResolution.name = mutable non-key metadata

0002_relationship_resolution_name_nonkey.py
    upgrade   -> drops uq_relationship_resolutions_semantic_child
    downgrade -> restores exactly that constraint
```

Committed `0001` remains unchanged.

## Authoritative baseline

```text
docs/milestones/M1/contract.md
    FINAL / FROZEN

docs/milestones/M1/architecture/README.md
    FROZEN as a set, including the 2026-08-15 ownership and PAR-02 corrections

docs/milestones/M1/steps.md
    FINAL / FROZEN

docs/general/technology_baseline.md
    STACK-01..STACK-09 RATIFIED

AGENTS.md
    repository-level operating contract
```

Individual architecture documents may retain older authoring labels such as `DRAFT`; the set-level FREEZE-01 authority remains controlling.

## Step registry

```text
M1-S00  COMPLETED  Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED  PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED  PrimitiveType and DataType vertical slice
M1-S03  COMPLETED  ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED  Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  COMPLETED  Ownership and Object schema-change vertical slice
M1-S06  COMPLETED  RelationshipDefinition model-plane and capability vertical slice
M1-S07  COMPLETED  Runtime Relationship and relationship lifecycle vertical slice
M1-S08  COMPLETED  Cross-domain integrity, destructive-operation and API/read closure
M1-S09  COMPLETED  Full M1 acceptance, regression and delivery gate
```

## Current blockers

None. No architecture contradiction remains known at M1 delivery.

Any future change to frozen M1 semantics follows the explicit reopen/revalidate/propagate/re-freeze process. New capability belongs to a subsequent milestone unless a formally reopened M1 contract says otherwise.
