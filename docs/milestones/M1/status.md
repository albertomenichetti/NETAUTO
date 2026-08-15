# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S05 — Ownership and Object schema-change vertical slice
```

**Step status:** READY TO START

M1-S00 through M1-S04 have completed implementation review.

M1-S04 accepted implementation baseline:

```text
d7fd864f31aa161962f1c9595c3fdf69228547d7
+
6a66ce267195166e61c8e98f52df3b344f2581f7
    review-fix delta
```

The reviewed S04 capability includes the complete intrinsic Object vertical slice: kernel-generated UUID identity, exact published OTV admission, definitive exact effective-schema interpretation on the caller-owned UoW, canonical runtime-property state, CREATE/RENAME/DATA_CHANGE, typed atomic intrinsic lifecycle persistence, Object GET/list, intrinsic lifecycle reads and deterministic real-PostgreSQL concurrency verification.

The S04 review-fix delta closed the public lifecycle DTO finding by:

- replacing the single broad lifecycle response DTO with a true discriminated intrinsic union;
- exposing only `CREATED`, `RENAME`, `DATA_CHANGE`, `SCHEMA_CHANGE` and `DELETED` in the intrinsic response/OpenAPI contract;
- enforcing kind-specific `before`/`after` nullability;
- retaining the full nine-value lifecycle `kind` query-filter vocabulary for forward-compatible filtering;
- adding runtime serialization and OpenAPI regression coverage, including a structural-kind filter returning an empty page in the S04-only dataset.

Final reported S04 gates passed with 84 non-PostgreSQL tests and 66 PostgreSQL tests on PostgreSQL 16.14, plus `uv lock`, `uv sync --locked`, build, Ruff and strict Pyright. No S05+ behavior or normative documentation change was introduced.

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
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  READY TO START   Ownership and Object schema-change vertical slice
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for starting M1-S05.

PostgreSQL-dependent verification continues to require an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation blocker to work around: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after its implementation delta has been reviewed and its applicable quality gates, required PostgreSQL/API/concurrency verification and documentation coherence satisfy the exit criteria in `steps.md`.
