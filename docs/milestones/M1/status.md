# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S08 — Cross-domain integrity, destructive-operation and API/read closure
```

**Step status:** READY TO START

M1-S00 through M1-S07 have completed implementation review.

## M1-S07 accepted baseline

Accepted implementation:

```text
27150496d460a5eed0ca025b176ec52324e948a4
+
a625cf08572ad0a448cdc9e3e631c2d48878dea7
    verification-closure review fix
```

The accepted S07 capability includes:

- complete factual Relationship domain/application/persistence/API behavior;
- deterministic non-symmetric and symmetric runtime Resolution closure;
- stable-lineage endpoint admission with no exact-OTV dependency;
- exact-view PostgreSQL PK arbitration, complete-UoW rollback and fresh-semantic-UoW convergence;
- exact-ID idempotent/ABA-safe Relationship DELETE;
- factual Relationship GET and Object-relative semantic navigation with deduplication/keyset pagination;
- typed Relationship lifecycle events integrated into global/Object-specific lifecycle reads;
- exactly one READ COMMITTED metadata-observation statement per real Relationship transition;
- complete semantic-view event dedup and state/event atomicity;
- Definition/Object FK lifetime behavior and strengthened RelationshipDefinition DELETE regression coverage;
- no runtime global Relationship gate, source/target semantics, Relationship properties/versioning, Object.DELETE or other S08 behavior.

## S07 PAR-02 architecture correction

During S07, deterministic `PAR-02 REL.CREATE × RD.RENAME` exposed a real physical-schema contradiction. The architecture was explicitly reopened, corrected, propagated and re-frozen without changing Relationship domain/API semantics.

Re-frozen rule:

```text
RelationshipResolution.name
    = mutable non-key metadata

no baseline FK-referenziable UNIQUE/index key
may include relationship_resolutions.name
```

The obsolete constraint:

```text
uq_relationship_resolutions_semantic_child
UNIQUE(
    relationship_definition_id,
    from_template_id,
    to_template_id,
    name
)
```

is no longer part of the head schema.

Accepted physical correction:

```text
0002_resolution_name_nonkey
    upgrade   -> drops exactly uq_relationship_resolutions_semantic_child
    downgrade -> restores exactly that constraint
```

Committed `0001` was not rewritten. No table, column, PK, FK, unrelated index or advisory gate changed. SQLAlchemy MetaData and migrated-schema drift are aligned to the corrected head.

Normative propagation commits:

```text
d1e8c1bf3007416afe9622df88a85970def5cda8  PERSIST-07 correction
8e96cda02722469e844170c66760118668a5f810  REALIZE-15 / PAR-02 correction
26ce0ec4b0780e2be05e5f219113327d61c06879  freeze-record revalidation
6d06ab507ce4afbd8e886ff010e7149ab68d17a5  architecture-index re-freeze
```

## Final S07 verification

Reported on PostgreSQL 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1):

```text
uv lock --check / sync / build          PASS
Ruff format/check                       PASS
Pyright strict                          PASS
non-PostgreSQL                          108 passed
PostgreSQL serial                       131 passed
S07 deterministic concurrency          19 passed
migration / schema / drift              3 passed
```

Canonical S07 coverage includes:

```text
ARB-05A/B/C
ARB-06
ARB-07A/B
REF-04
SNAP-01/02/03
ATOMIC-02
ATOMIC-03
PAR-01
PAR-02
PAR-05
```

Additional accepted REALIZE-15/atomic/API regressions prove:

- REL.CREATE progresses while OBJ.DATA_CHANGE remains open after its non-key UPDATE;
- REL.CREATE progresses while OBJ.SCHEMA_CHANGE remains open after its non-key UPDATE;
- REL.CREATE progresses while RD.RENAME remains open after Resolution-name UPDATE (PAR-02);
- forced `RELATIONSHIP_CREATED` event failure after complete closure insertion rolls back header + all runtime rows + event set;
- real Relationship lifecycle filtering by relationship id, Definition id and relationship name;
- Object-specific lifecycle involvement through `object_id = X OR destination_object_id = X`;
- strict null/non-string UUID operands map to `400 invalid_request`.

No S07 completion blocker or known architecture contradiction remains.

## S07/S08 boundary

Semantic scenarios requiring final `Object.DELETE` remain intentionally deferred to S08:

```text
REF-03   REL.CREATE × OBJ.DELETE(endpoint)
REF-05B  REL.DELETE × OBJ.DELETE
```

S07 did not introduce a fake/private Object DELETE.

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
M1-S08  READY TO START   Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for starting M1-S08.

PostgreSQL-dependent verification requires the externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation choice: affected work stops and follows the explicit reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
