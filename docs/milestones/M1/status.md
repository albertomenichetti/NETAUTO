# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S03 — ObjectTemplate and active model graph vertical slice
```

**Step status:** IN PROGRESS — REVIEW CHANGES REQUIRED

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

M1-S03 pre-flight was revalidated against the frozen ObjectTemplate, DataType, persistence/concurrency, PGTEST and API authorities. No architecture/documentation contradiction is known.

The initial S03 implementation under review is:

```text
f1fa45aa90a507c4bf07903adec9f51eb1b8e7a5
```

The implementation establishes the intended ObjectTemplate vertical structure: plain-Python domain/effective-schema semantics, aggregate persistence, exact parent and DataType binding, historical evolution, active-model certification/deprecation, strict public ObjectTemplate API, coherent composite reads and deterministic real-PostgreSQL concurrency coverage. The completion review found three targeted implementation/verification findings that must be corrected before S03 is marked complete.

The non-normative Codex review-fix prompt is:

```text
docs/milestones/M1/wip/M1-S03-review-fixes-codex-prompt.md
```

The original S03 implementation prompt and the review-fix prompt are execution aids only. `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

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
M1-S03  IN PROGRESS      ObjectTemplate and active model graph vertical slice — review changes required
M1-S04  NOT STARTED      Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  NOT STARTED      Ownership and Object schema-change vertical slice
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

### S03 review finding — component target lifetime mechanism

Component `target_template_id` is a stable-lineage, pure referential-lifetime dependency. The current implementation acquires an explicit `FOR SHARE` on the target ObjectTemplate lineage while resolving component candidates. This is stronger than REALIZE-15/REALIZE-07: pure referential lifetime must rely on the immediate FK/key-share machinery, with semantic existence precheck allowed but no generic RL-only lifecycle lock.

The component `REF-01` test currently follows the same explicit-share mechanism and must instead prove the real FK lifetime arbitration. A no-artificial-contention regression is also required so component references do not serialize unrelated target non-key metadata mutation.

### S03 review finding — persistence SQL leaked into application

Composite exact/effective-schema reads correctly choose `REPEATABLE READ READ ONLY`, but `src/netauto/application/objecttemplates.py` currently imports SQLAlchemy `text` and constructs the `SET TRANSACTION ...` statement itself. STACK-02 requires SQL/query construction to stay inside persistence/infrastructure. The read-isolation mechanism must move behind a narrow persistence/UoW boundary while preserving snapshot coherence and READ COMMITTED mutation isolation.

### S03 review finding — persisted effective-schema corruption failure class

The public effective-schema GET currently reuses command-candidate validation mapping. A semantically invalid persisted effective schema can therefore be surfaced as `422 semantic_validation_failed`. The frozen API contract requires persisted invariant corruption to map to `500 internal_error`; 422 remains for caller-supplied semantic candidates. The read path and a targeted corruption test must be corrected accordingly.

These findings are implementation/verification findings only. No frozen architecture contradiction was found and the M1 architecture remains FROZEN.

PostgreSQL-dependent verification requires an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation blocker to work around: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after its implementation delta has been reviewed and its applicable quality gates, required PostgreSQL/API/concurrency verification and documentation coherence satisfy the exit criteria in `steps.md`.
