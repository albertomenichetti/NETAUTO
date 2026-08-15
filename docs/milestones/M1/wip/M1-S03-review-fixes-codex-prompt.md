# Codex review-fix prompt — M1-S03

**Status:** NON-NORMATIVE REVIEW-FIX PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Continue the current implementation step:

```text
M1-S03 — ObjectTemplate and active model graph vertical slice
```

The implementation commit under review is:

```text
f1fa45aa90a507c4bf07903adec9f51eb1b8e7a5
```

Do not start M1-S04. Preserve the existing S03 implementation except where a change is required by the review findings below.

## Mandatory pre-flight

Re-read and obey at minimum:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/objecttemplate.md
docs/milestones/M1/architecture/objecttemplate-lifecycle.md
docs/milestones/M1/architecture/objecttemplate-properties.md
docs/milestones/M1/architecture/objecttemplate-components.md
docs/milestones/M1/architecture/objecttemplate-effective-schema.md
docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-semantic-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
docs/milestones/M1/architecture/api-error-contract.md
```

The review found no architecture contradiction. These are implementation/verification findings only.

## Review finding 1 — component target is pure referential lifetime, not lifecycle admission

The current ObjectTemplate component-candidate resolution calls `ObjectTemplateStore.lock_lineage_share(target_id)`, which takes an explicit PostgreSQL `FOR SHARE` lock on every component target lineage.

That is stronger than the frozen concurrency realization permits.

A component target is a stable ObjectTemplate lineage reference. It is **not** a lifecycle-sensitive exact-version dependency:

```text
component.target_template_id
    -> stable ObjectTemplate lineage
    -> target need only exist
    -> no default/PUBLISHED target version required
```

REALIZE-15 / REALIZE-07 require pure referential lifetime to be protected by the immediate FK / PostgreSQL key-share machinery, with no generic extra RL-only `FOR SHARE` lock.

### Required correction

- Remove the explicit lineage `FOR SHARE` acquisition used solely to validate component target existence.
- A normal semantic precheck may read target-lineage existence without introducing a lifecycle lock.
- Keep the existing `object_template_components.target_template_id -> object_templates.id` immediate `RESTRICT` FK as final race authority.
- If the target disappears after semantic precheck but before component persistence, translate the expected FK race into the frozen semantic failure boundary without exposing SQL/constraint internals.
- Do not add another lock/gate/table to replace the FK authority.
- Preserve component target semantics: target may be abstract and need not have a default or PUBLISHED version.

### REF-01 correction

The current component-reference `REF-01` mechanism test uses/intercepts the explicit lineage `FOR SHARE`. Replace that with a deterministic real-PostgreSQL test of the actual referential mechanism:

```text
reference wins
    -> FK/key-share protects target lifetime
    -> target DELETE cannot commit

target delete wins
    -> candidate reference cannot commit
```

Use independent transactions and `pg_blocking_pids()` where a positive blocking relation is asserted. Do not coordinate by sleep.

Add a regression proving component reference handling does not introduce artificial non-key lineage contention. In particular, an ObjectTemplate REVISE whose component target is a stable lineage (including a self-target where valid) must not contend with unrelated target `SET_DESCRIPTION` merely because the component reference exists. This protects REALIZE-15 and the PAR-07 non-key topology rather than merely functional outcomes.

## Review finding 2 — SQL/query construction leaked into the application layer

`src/netauto/application/objecttemplates.py` currently imports SQLAlchemy `text` and executes:

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY
```

directly for composite reads.

The isolation choice is correct, but STACK-02 requires SQLAlchemy/textual SQL and query construction to remain inside the persistence/infrastructure boundary. Application/domain code must not build SQLAlchemy statements.

### Required correction

Move this mechanism behind a narrow persistence/UoW boundary, for example a concrete UoW/persistence helper whose semantic intent is to begin/use a coherent read-only repeatable-read transaction.

Requirements:

- `application/objecttemplates.py` no longer imports SQLAlchemy or constructs textual SQL;
- exact OTV and effective-schema composite reads remain snapshot-coherent;
- mutation isolation remains `READ COMMITTED`;
- do not introduce a generic transaction-options framework unless the concrete read requirement needs it;
- keep the implementation explicit and small.

Add/retain a test that proves the composite read path uses one coherent candidate snapshot; the test should exercise the public/application behavior, not merely inspect a method name.

## Review finding 3 — persisted effective-schema corruption is INTERNAL_FAILURE, not semantic 422

The effective-schema GET path currently calls the same `_validate_candidate(...)` helper used by command candidates. That helper maps `ObjectTemplateValidationError` to `semantic_validation_failed` / HTTP 422.

That mapping is correct for a caller-supplied CREATE/REVISE/PUBLISH candidate. It is not correct for an ordinary GET reading already-persisted state.

The frozen API error contract classifies persisted state that contradicts M1 invariants — including malformed persisted effective schema — as:

```text
INTERNAL_FAILURE
-> HTTP 500
-> code = internal_error
```

A caller must not receive 422 as if they could repair an invalid persisted schema by changing the GET request.

### Required correction

Separate the candidate-validation failure mapping from persisted-read invariant handling.

For:

```text
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
```

- missing URI exact target remains `404 resource_not_found`;
- a persisted effective-schema/inheritance/declaration invariant violation becomes `500 internal_error`;
- no SQL/constraint/stack details leak publicly.

CREATE/REVISE/PUBLISH candidate validation keeps the frozen semantic/state mappings.

Add a targeted test that deliberately constructs a persistence state which is structurally DB-valid but semantically invalid for effective resolution (for example an inherited effective member collision if representable under the frozen physical schema), then proves the public GET returns `500` + `internal_error`, not `422`.

## Preserve the already-correct S03 work

Do not rewrite working S03 capability unnecessarily. In particular preserve:

- plain-Python ObjectTemplate domain/effective-schema model;
- exact parent pins and defensive cycle detection;
- exact/implicit DTV admission on caller-owned UoW;
- unchanged historical pins not being gratuitously re-admitted during DRAFT revise;
- canonical primitive reuse for `migration_default`;
- historical property/component evolution and remove/re-add continuity;
- SCALAR -> LIST only normal value-mode evolution;
- component widening-only historical evolution;
- multi-row candidate atomic replacement with one revision increment;
- publication certification of direct exact parent/DTV dependencies;
- direct active-consumer deprecation checks;
- semantic PGTEST coverage already implemented for ROW-01..10 applicable variants, ROW-15/16, ARB-01, PAR-06/07, REF-01 and ATOMIC-01, except where REF-01 must be corrected as above;
- no relationship-capabilities placeholder route;
- no S04+ capability, migration, new schema table, JSON Schema or effective-schema cache.

## Verification

Run and report at least:

```text
uv lock
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "not postgresql"
uv run pytest -m postgresql
```

`TEST_DATABASE_URL` is required for the PostgreSQL suite. With one external database URL, keep PostgreSQL tests serial with respect to xdist.

For the review findings, explicitly report:

- how component target lifetime now relies on FK authority rather than explicit `FOR SHARE`;
- the corrected REF-01 component-reference test and the no-artificial-contention regression;
- where the repeatable-read read mechanism moved and confirmation application code no longer imports SQLAlchemy;
- the test proving malformed persisted effective schema maps to `500 internal_error`;
- all final test counts and PostgreSQL version;
- any suppression/retry/test hook introduced (prefer none; deterministic test-only phase interception is allowed where it does not alter production semantics);
- confirmation no architecture contradiction or S04+ behavior was introduced.

Do not mark S03 `COMPLETED`; completion remains a reviewer decision after this delta is pushed and inspected.
