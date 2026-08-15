# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S07 — Runtime Relationship and relationship lifecycle vertical slice
```

**Step status:** IN PROGRESS — ARCHITECTURE REALIGNED / RESUME READY

M1-S00 through M1-S06 have completed implementation review.

## M1-S06 accepted baseline

Accepted implementation:

```text
1c21ac046505e383b707b3f7e328b82921257673
+
e4fd891a9ef606ea43eaf4aa38029d33619ddbf8
    API error-detail review fix
```

The accepted S06 model-plane remains authoritative: complete RelationshipDefinition/RelationshipResolution aggregates, global certification/conflict gate, coherent capability reads and stable lineage FK lifetime semantics. The S07 architecture correction below does not change S06 domain semantics or public API behavior.

## M1-S07 pre-flight and decomposition

The mandatory S07 pre-flight confirmed:

```text
M1 contract      FINAL / FROZEN
M1 architecture  FROZEN as a set
M1 steps         FINAL / FROZEN
M1-S00..S06      COMPLETED
STACK-01..09     RATIFIED
```

The earlier verification-decomposition drift remains resolved: semantic `REF-03` (`REL.CREATE × OBJ.DELETE`) and Relationship `REF-05` (`REL.DELETE × OBJ.DELETE`) require final `Object.DELETE`, which is delivered in M1-S08. S07 must not introduce a fake/private Object DELETE; it still proves RuntimeRelationshipResolution -> Object FK `RESTRICT` mechanics directly at persistence level.

## S07 PAR-02 architecture correction — 2026-08-15

During implementation, deterministic `PAR-02 REL.CREATE × RD.RENAME` exposed a real frozen architecture/schema contradiction. The affected work correctly stopped without commit/push.

The contradiction was:

```text
RelationshipResolution.name
    = mutable non-key metadata

REALIZE-15 / PAR-02
    = REL.CREATE must not serialize solely on RD.RENAME

former PERSIST-07 physical schema
    = UNIQUE(
        relationship_definition_id,
        from_template_id,
        to_template_id,
        name
      )
```

Because `name` participated in the defensive FK-eligible UNIQUE, PostgreSQL treated Resolution-name RENAME as key-changing and the resulting stronger row lock blocked the runtime composite-FK insertion path. This violated the already-ratified PAR-02/REALIZE-15 non-serialization contract.

The architecture was explicitly reopened, re-read, corrected, propagated and re-frozen. PAR-02 was preserved; the defensive UNIQUE was removed from the frozen PERSIST-07 authority.

Re-frozen rule:

```text
RelationshipResolution.name
    = mutable non-key metadata

no baseline FK-referenziable UNIQUE/index key
may include relationship_resolutions.name
```

Unchanged physical/domain authorities:

```text
relationship_resolutions PRIMARY KEY (id)
UNIQUE (id, relationship_definition_id)
Definition -> Resolution owned-child FK
from_template_id / to_template_id FK RESTRICT
runtime same-Definition composite FK
runtime exact-view PK arbitration
complete Definition shape / duplicate semantic-child rejection in domain/UoW
```

### Authorized physical correction

S07 is explicitly authorized to add one forward Alembic revision after current `0001` that drops only:

```text
uq_relationship_resolutions_semantic_child
```

The downgrade restores exactly that constraint. Do not rewrite committed `0001`. No table, column, PK, FK, unrelated index or advisory gate changes are authorized.

SQLAlchemy MetaData and migration/schema drift tests must be aligned to the corrected head.

Normative propagation commits:

```text
d1e8c1bf3007416afe9622df88a85970def5cda8  PERSIST-07 correction
8e96cda02722469e844170c66760118668a5f810  REALIZE-15 / PAR-02 correction
26ce0ec4b0780e2be05e5f219113327d61c06879  freeze-record revalidation
6d06ab507ce4afbd8e886ff010e7149ab68d17a5  architecture-index re-freeze
```

No Relationship domain, API, lifecycle, factual identity, convergence or conflict semantics changed.

## S07 resume boundary

The already-implemented local S07 working tree must be preserved rather than discarded. After integrating the remote architecture correction, implementation resumes with:

- removal of `uq_relationship_resolutions_semantic_child` from SQLAlchemy MetaData;
- exactly one `0002` Alembic correction migration;
- schema/migration drift verification;
- deterministic PAR-02 rerun without weakening the test;
- completion of the remaining S07 verification and quality gates.

The current non-normative execution aid is:

```text
docs/milestones/M1/wip/M1-S07-codex-resume-prompt.md
```

The original S07 prompt was superseded and removed so only one operative WIP prompt remains.

Prompt commits:

```text
59c8e41cfe72c79e47220798a0d0be6cb68180fc  add resume prompt
1c92e6076ad656cfc8d9027234d17d76bab58af8  remove superseded prompt
```

## S07 verification still required

S07 must finish and pass the applicable runtime Relationship gate, including:

```text
ARB-05..07
REF-04
SNAP-01..03
ATOMIC-02
ATOMIC-03
PAR-01
PAR-02
PAR-05
```

`REF-03` and Relationship `REF-05` remain deferred to S08 with final Object.DELETE.

Required quality/migration verification includes:

```text
uv lock --check
uv sync --locked
uv build
Ruff format/check
Pyright strict
non-PostgreSQL suite
real-PostgreSQL suite via TEST_DATABASE_URL
clean DB -> alembic upgrade head
metadata/migrated-schema drift verification
```

## Authoritative baseline

M1 implementation proceeds from:

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
M1-S07  IN PROGRESS      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known after the PAR-02 architecture correction. S07 is authorized to resume from the preserved local implementation using `M1-S07-codex-resume-prompt.md`.

PostgreSQL-dependent verification requires the externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation choice: affected work stops and follows the explicit reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
