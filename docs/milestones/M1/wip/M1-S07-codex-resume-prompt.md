# Codex resume prompt — M1-S07 after PAR-02 architecture correction

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for resuming the already-started M1-S07 implementation after the deterministic PAR-02 test exposed and triggered correction of a frozen physical-schema contradiction. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Resume and complete exactly:

```text
M1-S07 — Runtime Relationship and relationship lifecycle vertical slice
```

The existing local S07 implementation is intentionally uncommitted because the affected work stopped at the architecture contradiction. **Do not discard, reset, or rewrite working S07 code merely because the architecture was reopened.** Preserve the current working tree, bring in the updated normative documents safely, inspect the resulting diff, apply the narrow schema correction below, and continue verification.

Do not implement M1-S08 `Object.DELETE` or broaden the Relationship model.

## Mandatory re-pre-flight

Before resuming affected implementation, re-read at minimum:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/architecture/m1-final-consistency-review.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/relationship.md
docs/milestones/M1/architecture/relationship-definition.md
docs/milestones/M1/architecture/relationship-resolution.md
docs/milestones/M1/architecture/relationship-runtime.md
docs/milestones/M1/architecture/relationship-concurrency.md
docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-relationship.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
```

Confirm:

```text
M1 contract      = FINAL / FROZEN
M1 architecture  = FROZEN after the 2026-08-15 PAR-02 correction
M1 steps         = FINAL / FROZEN
M1-S00..S06      = COMPLETED
current step     = M1-S07 IN PROGRESS
STACK-01..09     = RATIFIED
```

If another normative contradiction appears, stop the affected behavior again rather than choosing a new implementation interpretation.

## Architecture correction that unblocks PAR-02

The frozen semantics are unchanged:

```text
RelationshipResolution.name
    = mutable non-key metadata

RD.RENAME
    = non-key Definition mutation
    = Definition header FOR NO KEY UPDATE

REL.CREATE × RD.RENAME
    = must not serialize solely because runtime FK protection references
      Definition/Resolution identity

Relationship lifecycle names
    = coherent old OR new committed metadata snapshot per REALIZE-14
```

The previous physical schema contained:

```text
uq_relationship_resolutions_semantic_child
UNIQUE (
    relationship_definition_id,
    from_template_id,
    to_template_id,
    name
)
```

That defensive constraint is no longer part of PERSIST-07. Because `name` participated in a PostgreSQL FK-eligible unique key, updating `name` became key-changing and acquired a stronger row lock, which blocked the runtime composite-FK insertion path and violated REALIZE-15 / PAR-02.

The re-frozen physical rule is:

```text
NO baseline FK-referenziable UNIQUE/index key may include
relationship_resolutions.name
```

Complete Definition shape and duplicate semantic-child rejection remain domain/UoW invariants. Do not weaken those validations.

The following remain unchanged and MUST stay present:

```text
relationship_resolutions PRIMARY KEY (id)
UNIQUE (id, relationship_definition_id)
Definition owned-child FK
from_template_id / to_template_id ObjectTemplate FK RESTRICT
runtime same-Definition composite FK
runtime exact-view PK arbitration
```

## Exact persistence change authorized in S07

Apply only the schema correction required by the re-frozen architecture:

1. remove `uq_relationship_resolutions_semantic_child` from SQLAlchemy `MetaData`;
2. add one forward Alembic revision after current `0001` that drops exactly that existing constraint;
3. provide a correct downgrade that restores exactly that constraint;
4. do **not** rewrite the already-committed `0001` migration history;
5. do not add/remove any table or column;
6. do not alter PKs, FK definitions, delete actions, technical `(id, relationship_definition_id)` UNIQUEs, indexes unrelated to this correction, or any advisory gate;
7. update schema/migration tests so clean DB -> Alembic head and metadata drift checks prove the new frozen schema.

This is an explicitly authorized architecture-correction migration, not scope expansion.

## Preserve the existing S07 implementation boundary

Resume the factual Relationship slice already implemented locally. Preserve the frozen behavior already required by S07, including:

- CREATE from exact `resolution_id + from_object_id + to_object_id`;
- stable-lineage endpoint admission without exact OTV dependency;
- non-symmetric selected-perspective semantics;
- symmetric unordered-pair semantics;
- deterministic complete RuntimeRelationshipResolution closure;
- exact-view PK arbitration and whole-UoW rollback;
- fresh semantic-UoW convergence after a collision;
- `relationship_fact_conflict` only for a distinct current factual conflict, not persisted corruption;
- exact-ID idempotent/ABA-safe Relationship DELETE;
- one-statement READ COMMITTED lifecycle metadata observation;
- complete semantic-view event dedup and atomic event sets;
- factual Relationship GET and Object-relative semantic reads;
- lifecycle API union extension with Relationship events;
- Definition/Object FK lifetime semantics;
- no runtime global Relationship gate.

Do not add source/target, forward/reverse, Relationship versioning/properties, caller-supplied Relationship IDs, standalone runtime-row CRUD, or new public routes beyond frozen S07.

## Deterministic PAR-02 closure

Re-run the existing deterministic PAR-02 regression against the corrected migrated schema.

It must prove the mechanism property, not merely final functional success:

```text
REL.CREATE × RD.RENAME
    does not block solely because of runtime FK key protection
```

The test should continue to use independent PostgreSQL transactions/connections and deterministic coordination. Do not weaken it, add sleep-based orchestration, or change the expected non-serialization contract to fit the old schema.

Also preserve SNAP-01 semantics:

```text
real Relationship transition event set
    = complete old Resolution-name generation
      OR complete new Resolution-name generation
    != half-old / half-new
```

Removing the defensive UNIQUE must not introduce any metadata locking workaround or change the one-statement snapshot boundary.

## Required S07 verification after the correction

Finish all still-open S07 verification and rerun the full relevant gate, including:

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

`REF-03` and Relationship `REF-05` remain deferred to S08 with final `Object.DELETE`. Do not create a fake/private Object.DELETE.

Retain direct persistence-level proof of RuntimeRelationshipResolution -> Object FK `RESTRICT` mechanics in S07.

Run at minimum:

```text
uv lock --check
uv sync --locked
uv build
Ruff format/check
Pyright strict
non-PostgreSQL suite
real-PostgreSQL suite using TEST_DATABASE_URL
clean-DB Alembic upgrade head
metadata/migrated-schema drift verification
```

Report the exact PostgreSQL server version.

With one shared `TEST_DATABASE_URL`, do not run PostgreSQL tests across xdist workers unless isolated DB targets are explicitly provided.

## Working-tree / integration discipline

The pre-correction S07 implementation is valuable work, not a failed branch.

Integrate the remote documentation changes without losing it. After synchronization:

- inspect `git status` and the complete diff;
- confirm only the expected architecture docs changed remotely;
- keep local S07 implementation changes;
- make the exact metadata + `0002` migration correction;
- resolve tests from the corrected authority;
- do not modify normative architecture documents yourself;
- do not mark `docs/milestones/M1/status.md` complete; reviewer owns completion status.

## Completion report

When S07 is fully green, commit and push the complete S07 implementation to `core_review` and report:

- implementation commit SHA;
- changed-file summary;
- exact quality/test results;
- PostgreSQL version;
- migration revision added and explicit confirmation that it only drops `uq_relationship_resolutions_semantic_child` on upgrade;
- PAR-02 blocker/non-blocker evidence after schema correction;
- canonical S07 PGTEST IDs/variants covered;
- confirmation that `REF-03` and Relationship `REF-05` remain deferred to S08;
- confirmation of no new table/column/gate/S08 behavior;
- any remaining unverified requirement or newly discovered contradiction.
