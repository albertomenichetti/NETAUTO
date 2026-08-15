# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S06 — RelationshipDefinition model-plane and capability vertical slice
```

**Step status:** IN PROGRESS — REVIEW CHANGES REQUIRED

M1-S00 through M1-S05 have completed implementation review.

## M1-S05 accepted baseline

```text
62857cc0c32b332a0e916ea83bdb2653f69596ab
+
622a46dde54c8f74cb8bc4ae6b7e70ebf140ee6f
    deterministic verification closure
```

Final S05 gates passed with 86 non-PostgreSQL and 86 PostgreSQL tests on PostgreSQL 16.14 plus lock/sync/build, Ruff and strict Pyright.

## M1-S06 pre-flight

The mandatory S06 pre-flight revalidated the frozen RelationshipDefinition/RelationshipResolution, ObjectTemplate lineage/capability, persistence/UoW, REALIZE-12/15, PGTEST and API-03 authorities.

Confirmed:

```text
M1 contract      FINAL / FROZEN
M1 architecture  FROZEN as a set
M1 steps         FINAL / FROZEN
M1-S00..S05      COMPLETED
STACK-01..09     RATIFIED
```

No architecture/documentation contradiction is known for S06.

## S06 implementation review

Implementation under review:

```text
1c21ac046505e383b707b3f7e328b82921257673
```

The reviewed production delta is broadly architecture-compatible and establishes:

- complete RelationshipDefinition + RelationshipResolution aggregate semantics;
- deterministic symmetric/non-symmetric Resolution derivation;
- semantic signature/equivalence and lineage-overlap conflict certification;
- `RELATIONSHIP_DEFINITION_CONFLICT_GATE` for CREATE/RENAME with separate fresh post-gate certified-set read;
- coherent one-statement certified Definition+Resolution set decoding;
- RENAME `FOR NO KEY UPDATE`, DELETE `FOR UPDATE`, DELETE without conflict gate;
- endpoint ObjectTemplate stable-lineage FK lifetime semantics;
- atomic complete Resolution-name RENAME;
- RelationshipDefinition CREATE/RENAME/DELETE/GET/list API;
- ObjectTemplate relationship-capability projection/list with inheritance applicability;
- no standalone RelationshipResolution API, S07 runtime Relationship behavior, Relationship lifecycle event variants, migration or new gate.

Reported gates on PostgreSQL 16.14:

```text
uv lock --check / uv sync --locked / uv build   PASS
Ruff format/check                                PASS
Pyright strict                                   PASS
non-PostgreSQL                                   101 passed
PostgreSQL                                       106 passed
```

Accepted deterministic coverage includes ROW-17, RD/OT-lineage REF-01, GATE-04A/B, GATE-05A/B, GATE-06A/B, ATOMIC-04C, global-gate over-serialization, rollback/gate release, same-Definition owner ordering and no-fan-out certified-set locking.

### Review findings

No model-plane semantic or concurrency blocker was found. Two bounded API-03.11 error-detail conformance findings remain:

1. `RD.DELETE` `delete_blocked` currently exposes only `{resource_type,id}`. API-03.11 requires bounded blocker type/count information. For current factual Relationship blockers it must include `blockers:[{"type":"relationship","count":N}]` (or equivalent canonical bounded shape).
2. In the concurrent ObjectTemplate-lineage-delete vs RD.CREATE FK-loss path, `RelationshipEndpointReferenceError` currently discards the failed semantic endpoint UUID, so `referenced_resource_not_found.details` loses `id`. The bounded persistence translation must retain the failed endpoint `template_id` without exposing the SQL constraint name.

These are narrow public error-boundary corrections. They do not require architecture reopening and must not change RelationshipDefinition semantics, gate ordering, lock strength, schema or route surface.

The non-normative review-fix prompt is:

```text
docs/milestones/M1/wip/M1-S06-review-fixes-codex-prompt.md
```

Prompt commit:

```text
3513f7a5cecf1fe0d77da79b3afe03bda2262461
```

## Authoritative baseline

```text
docs/milestones/M1/contract.md                FINAL / FROZEN
docs/milestones/M1/architecture/README.md     FROZEN
docs/milestones/M1/steps.md                   FINAL / FROZEN
docs/general/technology_baseline.md            STACK-01..STACK-09 ratified
AGENTS.md                                      repository operating contract
```

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  COMPLETED        Ownership and Object schema-change vertical slice
M1-S06  IN PROGRESS      RelationshipDefinition model-plane and capability vertical slice — review error-detail fixes required
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

Close the two targeted API error-detail findings in the S06 review-fix prompt. No architecture reopening is currently required.

PostgreSQL-dependent verification requires an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

## Operational rule

This file records operational progress only. A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
