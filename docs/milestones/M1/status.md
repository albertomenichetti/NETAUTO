# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S04 — Object intrinsic state and intrinsic lifecycle vertical slice
```

**Step status:** IN PROGRESS — REVIEW CHANGES REQUIRED

M1-S00, M1-S01, M1-S02 and M1-S03 have completed implementation review.

M1-S03 accepted implementation baseline:

```text
f1fa45aa90a507c4bf07903adec9f51eb1b8e7a5
+
5519fc9395de6e30e66d228f14fabed5385b41fa
    review-fix delta
```

The reviewed S03 capability includes the complete ObjectTemplate model-plane vertical slice: stable lineage/version lifecycle, exact parent pins, local property/component declarations, historical evolution, derived effective schema, caller-owned-UoW DataType/parent admission, active-model-graph publication/deprecation consistency, strict public ObjectTemplate API, keyset pagination and deterministic real-PostgreSQL concurrency coverage.

The S03 review-fix delta closed the completion findings by:

- removing the explicit `FOR SHARE` lock from stable-lineage component-target admission and restoring immediate PostgreSQL FK/key-share authority for pure referential lifetime;
- translating component-target FK race losses to bounded `referenced_resource_not_found` semantics without SQL/constraint leakage;
- replacing the component `REF-01` mechanism with deterministic reference-first/delete-first FK arbitration coverage and adding a no-artificial-contention regression against target `SET_DESCRIPTION`;
- moving `REPEATABLE READ READ ONLY` transaction setup behind the persistence/UoW boundary through `CoherentReadUnitOfWork`, leaving application code free of SQLAlchemy query construction;
- proving composite exact-version reads cannot mix header and declaration generations across a concurrent revise;
- mapping DB-valid but semantically corrupt persisted effective-schema state to `500 internal_error` rather than caller `422 semantic_validation_failed`.

Final reported S03 gates passed with 74 non-PostgreSQL tests and 55 PostgreSQL tests on PostgreSQL 16.14, plus `uv lock`, `uv sync --locked`, build, Ruff and strict Pyright.

M1-S04 pre-flight was revalidated against the frozen Object, runtime-state, lifecycle, ObjectTemplate effective-schema, persistence/UoW, concurrency/PGTEST and API authorities. No architecture/documentation contradiction is known.

The initial S04 implementation under review is:

```text
d7fd864f31aa161962f1c9595c3fdf69228547d7
```

The implementation establishes the intended intrinsic Object vertical capability: plain-Python runtime-property semantics, exact published OTV admission, definitive exact effective-schema interpretation on the caller-owned UoW, CREATE/RENAME/DATA_CHANGE, atomic typed intrinsic lifecycle persistence, Object GET/list and lifecycle reads, with deterministic real-PostgreSQL coverage for `ROW-11`, Object target admission/default races, the Object `REF-01` variant and `ATOMIC-04A`.

The completion review found one targeted public API/OpenAPI finding: the S04 intrinsic lifecycle response DTO currently uses the full nine-value persistence `EventKind`, which incorrectly advertises ownership/Relationship event kinds with the intrinsic `{before,after}` response shape. API-03.9 requires a discriminated event-family representation; S04 must expose only the frozen intrinsic family in its response DTO while retaining the full lifecycle `kind` query-filter vocabulary.

The non-normative Codex review-fix prompt is:

```text
docs/milestones/M1/wip/M1-S04-review-fixes-codex-prompt.md
```

The original S04 implementation prompt and review-fix prompt are execution aids only. `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

`SCHEMA_CHANGE`, ownership ATTACH/DETACH, Object DELETE, ownership projections and Relationship behavior remain explicitly deferred to later steps.

With a single externally supplied `TEST_DATABASE_URL`, PostgreSQL-required suites remain serial with respect to pytest-xdist. Cross-worker PostgreSQL parallelism is permitted only when the external environment supplies isolated database targets per worker or equivalent isolation consistent with STACK-07/PGTEST.

## Authoritative baseline

M1 implementation proceeds from the following frozen/ratified authorities:

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
    repository-level operating contract for coding agents
```

Before each implementation step, the mandatory pre-flight defined by `AGENTS.md`, `docs/general/linee_guida_progetto.md` and the step itself must be executed against the current normative repository documents.

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  IN PROGRESS      Object intrinsic state and intrinsic lifecycle vertical slice — review changes required
M1-S05  NOT STARTED      Ownership and Object schema-change vertical slice
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

### S04 review finding — intrinsic lifecycle public DTO discrimination

The persistence/internal event vocabulary correctly contains all nine M1 event kinds, and API-03.10 global lifecycle query filtering also owns the full kind vocabulary. The current S04 transport response model nevertheless uses that full enum inside the intrinsic `{before,after}` DTO, making the public/OpenAPI schema claim that ownership and Relationship kinds share intrinsic event fields.

The response boundary must be narrowed to a real discriminated intrinsic family (`CREATED`, `RENAME`, `DATA_CHANGE`, `SCHEMA_CHANGE`, `DELETED`) with kind-appropriate before/after nullability. Structural/Relationship response variants remain deferred to their owning slices. This is an implementation/verification finding only; no frozen architecture contradiction was found.

PostgreSQL-dependent verification requires an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation blocker to work around: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after its implementation delta has been reviewed and its applicable quality gates, required PostgreSQL/API/concurrency verification and documentation coherence satisfy the exit criteria in `steps.md`.
