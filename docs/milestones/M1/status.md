# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S02 — PrimitiveType and DataType vertical slice
```

**Step status:** IN PROGRESS — REVIEW CHANGES REQUIRED

M1-S00 and M1-S01 have completed implementation review.

M1-S01 review accepted commit:

```text
a1b97f663faf27f6485e25ec23886063321f0d91
```

The reviewed S01 foundation includes the complete frozen 13-table SQLAlchemy Core authority, one Alembic head with no unexplained metadata drift, PostgreSQL structural enforcement, async READ COMMITTED runtime engine/UoW composition, centralized transaction advisory gates and the deterministic real-PostgreSQL harness foundation.

Real PostgreSQL verification was executed against PostgreSQL 16.14 and covered migration/schema, representative structural constraints/FKs/CASCADE/RESTRICT, UoW commit/rollback/isolation/independent connections and a deterministic `pg_blocking_pids()` blocker proof without sleep-based orchestration.

With a single externally supplied `TEST_DATABASE_URL`, PostgreSQL-required suites remain serial with respect to pytest-xdist. Cross-worker PostgreSQL parallelism is permitted only when the external environment supplies isolated database targets per worker or equivalent isolation consistent with STACK-07/PGTEST.

The S02 pre-flight public-contract gap was closed before implementation. `api-error-contract.md` freezes the DT/OT CREATE command-result composition:

```text
DT.CREATE -> {datatype:<lineage DTO>, version:<exact v1 DTV DTO>}
OT.CREATE -> {object_template:<lineage DTO>, version:<exact v1 OTV DTO>}
```

with literal public field names and canonical API-03.9 nested DTOs. The clarification does not establish a generic response envelope.

The initial S02 implementation under review is:

```text
97ab77defc77f6cd51492c6ba209dbfce8dd918f
```

The functional/domain/application/persistence/API structure is broadly aligned with the frozen S02 architecture, but the completion gate found implementation/verification findings that must be corrected before S02 can be marked complete.

The non-normative Codex review-fix prompt is:

```text
docs/milestones/M1/wip/M1-S02-review-fixes-codex-prompt.md
```

The original S02 implementation prompt remains an implementation aid only. `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

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
M1-S02  IN PROGRESS      PrimitiveType and DataType vertical slice — review changes required
M1-S03  NOT STARTED      ObjectTemplate and active model graph vertical slice
M1-S04  NOT STARTED      Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  NOT STARTED      Ownership and Object schema-change vertical slice
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

### S02 review finding — canonical PGTEST semantic coverage

The current `tests/test_datatype_concurrency.py` demonstrates useful PostgreSQL lock/arbitration mechanisms, but most canonical scenario IDs are not yet complete PGTEST coverage because they do not also assert the semantic operation outcomes/failures/final states required by PGTEST-01.

`PAR-07A` additionally exercises description-vs-description rather than the canonical `SET_DESCRIPTION × SET_DEFAULT` pair.

Canonical S02-realizable scenarios must be completed with actual DataType semantic operations and allowed/forbidden outcome assertions while retaining deterministic real-PostgreSQL mechanism evidence.

### S02 review finding — binding-admission lifetime boundary

`DataTypeService.admit_exact_binding()` and `admit_default_binding()` open and close their own UoW, so their `FOR SHARE` protection ends before a future consumer could persist and commit its exact binding. They must not be used as the strong-consistency admission capability.

The reusable admission primitive must execute on the caller-owned semantic UoW connection, as the persistence-level `DataTypeStore.admit_exact()` / `admit_default()` already allow.

### S02 review finding — required verification breadth

The current suite does not yet demonstrate all S02-required primitive edge cases and DataType persistence/application/API failure families, including active PUBLISHED consumer blocking vs DRAFT/DEPRECATED non-blocking, max-DRAFT version reuse, external-FK whole-lineage delete blocking, cursor/filter mismatch and several explicit PrimitiveType/Hypothesis cases.

The review-fix prompt enumerates the required closure set.

These findings are implementation/verification findings only. No frozen architecture contradiction was found and architecture remains FROZEN.

PostgreSQL-dependent verification continues to require an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation blocker to work around: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after its implementation delta has been reviewed and its applicable quality gates, required PostgreSQL/API/concurrency verification and documentation coherence satisfy the exit criteria in `steps.md`.
