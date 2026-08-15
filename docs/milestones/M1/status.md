# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S08 — Cross-domain integrity, destructive-operation and API/read closure
```

**Step status:** IN PROGRESS — REVIEW CHANGES REQUIRED

M1-S00 through M1-S07 have completed implementation review.

## M1-S07 accepted baseline

Accepted implementation:

```text
27150496d460a5eed0ca025b176ec52324e948a4
+
a625cf08572ad0a448cdc9e3e631c2d48878dea7
    verification-closure review fix
```

The S07 PAR-02 physical correction remains frozen and accepted:

```text
RelationshipResolution.name = mutable non-key metadata

0002_resolution_name_nonkey
    upgrade   -> drops uq_relationship_resolutions_semantic_child
    downgrade -> restores exactly that constraint
```

## M1-S08 implementation candidate under review

Delivered implementation:

```text
678da20904bec7eb16a6baff45f26a80890dbcae
```

The reviewed candidate correctly delivers:

- final race-safe `Object.DELETE` using `objects(O) FOR UPDATE`;
- zero ownership / zero factual-Relationship delete admission with semantic blocker counts;
- immediate Object ownership/Relationship FK `RESTRICT` as final lifetime race authority;
- atomic `DELETED` event with historical lifecycle retention and no implicit cleanup;
- bounded DataType/ObjectTemplate/Object FK race-loser diagnostic translation;
- full normal blocker matrix for DT/OT/RD/Object deletion;
- lifecycle filter/cursor/index closure;
- exact public route inventory: 32 mutations and 20 reads;
- exact finite API-03.11 public code/status catalog: 23 codes;
- no new migration, table, column, advisory gate, or S09 capability.

Reported verification on PostgreSQL 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1):

```text
uv lock --check / sync / build          PASS
Ruff format/check                       PASS
Pyright strict                          PASS
full suite                              264 passed
non-PostgreSQL                          122 passed
real PostgreSQL                         142 passed
canonical REF selection                 13 passed
migration selection                     1 passed
```

## S08 review outcome

No production-semantic defect is currently identified.

`Object.DELETE` is consistent with the frozen contract:

```text
Object FOR UPDATE
-> validate final current intrinsic snapshot
-> count ownership rows
-> count DISTINCT factual Relationship ids
-> fail bounded delete_blocked if current blockers exist
-> attempt physical Object DELETE
-> known concurrent FK loser maps to ownership|relationship blocker count=1
-> append DELETED(before=current, after=null)
-> commit
```

The bounded race-loser `count=1` behavior is explicitly allowed by the S08 execution contract because the exact current total is not safely available inside the failed/aborted statement path.

### Remaining completion blocker — canonical REF-06 verification

The current deterministic tests explicitly trace `REF-01..05` and exercise the relevant FK lifetime mechanisms. Existing `REF-01`/`REF-04` races also provide partial mechanism evidence for aggregate-root delete vs external references.

However, S08 completion still requires an explicit canonical proof for:

```text
REF-06  aggregate CASCADE × external RESTRICT
```

The required mechanism evidence is not merely normal blocker pre-check behavior. For the DataType, ObjectTemplate and RelationshipDefinition aggregate shapes, verification must force the root DELETE path past a pre-check that initially saw no blocker, let an external current reference become committed, then prove the physical root DELETE loses on PostgreSQL `RESTRICT` and that **both the aggregate root and its owned children remain intact**.

Required explicit variants:

```text
REF-06A  DataType root + owned versions
         × external ObjectTemplate property exact-DTV reference

REF-06B  ObjectTemplate root + owned version/declaration state
         × external current Object/other OT reference

REF-06C  RelationshipDefinition root + owned Resolutions
         × factual Relationship reference
```

This is a verification/traceability finding, not an architecture or production-code change. Existing working production behavior must remain unchanged unless a new real-PG test proves a defect.

Current non-normative review-fix execution aid:

```text
docs/milestones/M1/wip/M1-S08-review-fixes-codex-prompt.md
```

The original S08 implementation prompt is completed/superseded and is removed from WIP.

## Authoritative baseline

```text
docs/milestones/M1/contract.md
    FINAL / FROZEN

docs/milestones/M1/architecture/README.md
    FROZEN after PAR-02 correction

docs/milestones/M1/steps.md
    FINAL / FROZEN

docs/general/technology_baseline.md
    STACK-01..STACK-09 RATIFIED

AGENTS.md
    repository-level operating contract
```

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  COMPLETED        Ownership and Object schema-change vertical slice
M1-S06  COMPLETED        RelationshipDefinition model-plane and capability vertical slice
M1-S07  COMPLETED        Runtime Relationship and relationship lifecycle vertical slice
M1-S08  IN PROGRESS — REVIEW CHANGES REQUIRED
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

Only the explicit `REF-06A/B/C` verification/traceability closure described above. No architecture contradiction is currently known.

PostgreSQL-dependent verification requires the externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.