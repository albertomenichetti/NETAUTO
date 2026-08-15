# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S03 — ObjectTemplate and active model graph vertical slice
```

**Step status:** IN PROGRESS

M1-S00, M1-S01 and M1-S02 have completed implementation review.

M1-S02 accepted implementation baseline:

```text
97ab77defc77f6cd51492c6ba209dbfce8dd918f
+
57824ca54cbaffafb24b7f8a3b282d9118fb9c6a
    review-fix delta
```

The reviewed S02 capability includes the closed PrimitiveType catalog and canonicalization/constraint authority, complete DataType/DataTypeVersion application operations, PostgreSQL-backed locking/UoW realization, public DataType HTTP read/write/list/error contracts, keyset pagination and real-PostgreSQL deterministic concurrency coverage.

The review-fix delta closed the S02 completion findings by:

- adding semantic outcome coverage for the S02-realizable canonical PGTEST scenarios `ROW-01`, `ROW-02`, `ROW-03`, `ROW-04A/B`, `ROW-05`, `ROW-06`, `ROW-15`, `ROW-16`, `ARB-01`, `PAR-06`, `PAR-07A/B`;
- preserving DataType-side caller-owned-UoW mechanism coverage for `ROW-07` / `ROW-08A/B`, with committed ObjectTemplate-consumer semantics intentionally deferred to M1-S03;
- removing application-level binding helpers whose private UoW would release dependency locks before a future consumer commit; caller-owned persistence admission remains the strong-consistency seam;
- completing required active-consumer, whole-lineage-delete/FK, cursor/filter, PrimitiveType and property-based verification breadth.

Final reported S02 gates passed with 71 non-PostgreSQL tests and 26 PostgreSQL tests on PostgreSQL 16.14, plus build, Ruff and strict Pyright.

M1-S03 pre-flight has been revalidated against the frozen ObjectTemplate, DataType, persistence/concurrency, PGTEST and API authorities. No architecture/documentation contradiction is currently known.

S03 now owns the complete ObjectTemplate model-plane vertical slice: stable lineage/versioning, exact parent pins, local property/component declarations, historical evolution, derived effective schema, caller-owned-UoW DataType/parent admission, active-model-graph publication/deprecation consistency, public ObjectTemplate API and the S03-realizable deterministic PGTEST closure.

In particular, S03 must complete the actual ObjectTemplate-consumer semantics for `ROW-07` / `ROW-08A/B` and active graph scenarios `ROW-09` / `ROW-10`; short-lived application-owned dependency-admission transactions remain forbidden.

The non-normative Codex execution prompt for the current step is:

```text
docs/milestones/M1/wip/M1-S03-codex-prompt.md
```

The prompt is an implementation aid only. `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

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
M1-S03  IN PROGRESS      ObjectTemplate and active model graph vertical slice
M1-S04  NOT STARTED      Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  NOT STARTED      Ownership and Object schema-change vertical slice
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for implementing M1-S03.

PostgreSQL-dependent verification requires an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation blocker to work around: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after its implementation delta has been reviewed and its applicable quality gates, required PostgreSQL/API/concurrency verification and documentation coherence satisfy the exit criteria in `steps.md`.
