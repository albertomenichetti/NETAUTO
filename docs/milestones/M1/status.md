# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S07 — Runtime Relationship and relationship lifecycle vertical slice
```

**Step status:** IN PROGRESS — REVIEW CHANGES REQUIRED

M1-S00 through M1-S06 have completed implementation review.

## M1-S06 accepted baseline

Accepted implementation:

```text
1c21ac046505e383b707b3f7e328b82921257673
+
e4fd891a9ef606ea43eaf4aa38029d33619ddbf8
    API error-detail review fix
```

The accepted S06 model-plane remains authoritative.

## S07 PAR-02 architecture correction — re-frozen 2026-08-15

Deterministic `PAR-02 REL.CREATE × RD.RENAME` exposed a physical-schema contradiction. The architecture was explicitly reopened, corrected, propagated and re-frozen without changing Relationship domain/API semantics.

Re-frozen rule:

```text
RelationshipResolution.name
    = mutable non-key metadata

no baseline FK-referenziable UNIQUE/index key
may include relationship_resolutions.name
```

The obsolete constraint is:

```text
uq_relationship_resolutions_semantic_child
UNIQUE(
    relationship_definition_id,
    from_template_id,
    to_template_id,
    name
)
```

Unchanged physical/domain authorities include `relationship_resolutions` PK `(id)`, technical `UNIQUE(id, relationship_definition_id)`, Definition/endpoint FKs, runtime same-Definition composite FK, runtime exact-view PK arbitration and complete Definition validation in domain/UoW.

Normative propagation commits:

```text
d1e8c1bf3007416afe9622df88a85970def5cda8  PERSIST-07 correction
8e96cda02722469e844170c66760118668a5f810  REALIZE-15 / PAR-02 correction
26ce0ec4b0780e2be05e5f219113327d61c06879  freeze-record revalidation
6d06ab507ce4afbd8e886ff010e7149ab68d17a5  architecture-index re-freeze
```

## S07 implementation candidate under review

Delivered implementation:

```text
27150496d460a5eed0ca025b176ec52324e948a4
```

The reviewed candidate includes:

- complete factual Relationship domain/application/persistence/API capability;
- deterministic symmetric/non-symmetric runtime closure;
- exact-view PK arbitration, whole-UoW rollback and fresh-UoW convergence;
- exact-ID idempotent/ABA-safe DELETE;
- factual and Object-relative semantic reads;
- Relationship lifecycle event union and one-statement metadata observation;
- Definition/Object FK lifetime behavior and strengthened RD.DELETE integration;
- architecture-correction migration `0002_resolution_name_nonkey` whose upgrade only drops `uq_relationship_resolutions_semantic_child` and whose downgrade restores that exact constraint;
- SQLAlchemy MetaData and migration drift aligned to the corrected head;
- no new table, column, gate, Object.DELETE or S08 semantic behavior.

Reported verification on PostgreSQL 16.14:

```text
uv lock --check / sync / build          PASS
Ruff format/check                       PASS
Pyright strict                          PASS
non-PostgreSQL                          108 passed
PostgreSQL serial                       128 passed
S07 concurrency selection               16 passed
clean migration / downgrade / drift     PASS
```

Canonical S07 coverage includes `ARB-05A/B/C`, `ARB-06`, `ARB-07A/B`, `REF-04`, `SNAP-01..03`, `ATOMIC-02/03`, `PAR-01/02/05`. `PAR-02` now proves REL.CREATE progresses while RD.RENAME remains open on independent PostgreSQL sessions.

## S07 review outcome

No production-semantic blocker is currently identified. The candidate is **not yet complete** because the mandatory verification contract still lacks explicit regressions for:

```text
1. REALIZE-15 non-serialization:
   REL.CREATE × OBJ.DATA_CHANGE
   REL.CREATE × OBJ.SCHEMA_CHANGE

2. CREATE/event atomicity after complete closure insertion:
   forced RELATIONSHIP_CREATED event insertion failure
   -> no header, no runtime rows, no creation events

3. Lifecycle API evidence against real Relationship events:
   relationship_definition_id filter
   relationship_name filter
   Object-specific timeline involvement via
       object_id = X OR destination_object_id = X

4. Strict Relationship CREATE body closure:
   null UUID operand
   wrong/non-string UUID carrier
   -> 400 invalid_request
```

These are verification-completeness findings, not architecture changes. Production code should change only if the new tests expose an implementation defect.

Current review-fix execution aid:

```text
docs/milestones/M1/wip/M1-S07-review-fixes-codex-prompt.md
```

The previous resume prompt is completed/superseded by the delivered implementation and is removed from WIP.

## S07/S08 boundary

Semantic `REF-03` (`REL.CREATE × OBJ.DELETE`) and Relationship `REF-05` (`REL.DELETE × OBJ.DELETE`) remain intentionally deferred to M1-S08 because final `Object.DELETE` is delivered there. S07 must not add a fake/private Object DELETE.

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
M1-S07  IN PROGRESS — REVIEW CHANGES REQUIRED
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

Only the S07 verification-closure findings above. No architecture contradiction is currently known.

PostgreSQL-dependent verification requires the externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.