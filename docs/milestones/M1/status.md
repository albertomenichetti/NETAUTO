# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S01 — PostgreSQL schema, migration, UoW and deterministic-test foundation
```

**Step status:** IN PROGRESS

M1-S00 has completed implementation review. Its clean-slate bootstrap, quality tooling, process-settings boundary, FastAPI factory/lifespan, Alembic scaffold and PostgreSQL test-configuration boundary satisfy the frozen S00 exit criteria.

M1-S01 now owns realization of the complete frozen PostgreSQL physical authority, initial schema migration, async runtime engine/UoW substrate and deterministic PostgreSQL concurrency-test harness foundation.

The non-normative Codex execution prompt for the current step is:

```text
docs/milestones/M1/wip/M1-S01-codex-prompt.md
```

The prompt is an implementation aid only. `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

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
M1-S01  IN PROGRESS      PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  NOT STARTED      PrimitiveType and DataType vertical slice
M1-S03  NOT STARTED      ObjectTemplate and active model graph vertical slice
M1-S04  NOT STARTED      Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  NOT STARTED      Ownership and Object schema-change vertical slice
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

No architecture/documentation blocker is known for M1-S01.

M1-S01 **cannot be completed** without an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`, because migration/schema, persistence/UoW and deterministic blocker verification are mandatory exit gates for this step.

A newly discovered contradiction in frozen architecture is not an implementation blocker to work around: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after its implementation delta has been reviewed and its applicable quality gates, required PostgreSQL/API/concurrency verification and documentation coherence satisfy the exit criteria in `steps.md`.
