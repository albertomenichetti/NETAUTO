# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S02 — PrimitiveType and DataType vertical slice
```

**Step status:** BLOCKED — PRE-FLIGHT ARCHITECTURE GAP

M1-S00 and M1-S01 have completed implementation review.

M1-S01 review accepted commit:

```text
a1b97f663faf27f6485e25ec23886063321f0d91
```

The reviewed S01 foundation includes the complete frozen 13-table SQLAlchemy Core authority, one Alembic head with no unexplained metadata drift, PostgreSQL structural enforcement, async READ COMMITTED runtime engine/UoW composition, centralized transaction advisory gates and the deterministic real-PostgreSQL harness foundation.

Real PostgreSQL verification was executed against PostgreSQL 16.14 and covered migration/schema, representative structural constraints/FKs/CASCADE/RESTRICT, UoW commit/rollback/isolation/independent connections and a deterministic `pg_blocking_pids()` blocker proof without sleep-based orchestration.

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
M1-S02  BLOCKED          PrimitiveType and DataType vertical slice — API CREATE result DTO gap
M1-S03  NOT STARTED      ObjectTemplate and active model graph vertical slice
M1-S04  NOT STARTED      Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  NOT STARTED      Ownership and Object schema-change vertical slice
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

### S02 pre-flight finding — DT/OT CREATE result DTO shape

The frozen API documents require `DT.CREATE` and `OT.CREATE` to return `201 + Location` with a command-specific result containing the created stable lineage plus the created v1 DRAFT exact-version result. The component lineage and exact-version DTOs are individually defined, but the enclosing public JSON object shape / field names for the CREATE command result are not explicitly frozen.

This is a public-contract gap, not an implementation detail to delegate to Codex. S02 implementation remains blocked until the API authority is explicitly completed and propagated consistently. No S02 Codex implementation prompt is considered ready while this gap remains open.

PostgreSQL-dependent verification continues to require an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation blocker to work around: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after its implementation delta has been reviewed and its applicable quality gates, required PostgreSQL/API/concurrency verification and documentation coherence satisfy the exit criteria in `steps.md`.
