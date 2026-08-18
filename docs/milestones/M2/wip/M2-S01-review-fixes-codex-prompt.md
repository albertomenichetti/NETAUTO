# Codex review-fix prompt — M2-S01

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It narrows the authorized corrective task but does not override `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract, architecture or steps, the active milestone status, the ratified technology baseline, or the reviewer findings recorded in `docs/milestones/M2/status.md`.

## Assignment

Correct exactly the three reviewer findings recorded for:

```text
M2-S01 — Durable relational baseline and versioned Relationship model plane

S01-RF-01
    DataType delete diagnostics do not distinguish
    RelationshipDefinitionVersion property references

S01-RF-02
    factual exact RelationshipDefinitionVersion pin is still
    synthesized as implicit version 1 in domain/projection constructors

S01-RF-03
    delete-first exact DataTypeVersion loss can omit the requested
    version selector from referenced_resource_not_found details
```

Work directly on branch:

```text
M2
```

The required starting point is the current reviewed branch tip:

```text
e5728486ace14bf525fa3f5df51d7c18e87b957c
docs(m2): require S01 review fixes
```

The candidate under correction is:

```text
implementation
    c019cada4152e9798e25476d35b0cec5127d6135

candidate status
    63c0e772df4c73c439b7b4baed67b3d11fc809b9
```

`M2-S00` is reviewer-owned `COMPLETED`. `M2-S01` is reviewer-owned `REVIEW CHANGES REQUIRED`. This prompt authorizes only bounded correction and permanent evidence for the three findings above. `M2-S02` remains blocked.

The publication action is:

```text
perform the mandatory repository pre-flight
correct all three findings completely
add permanent deterministic evidence
preserve every already accepted S00/S01 behavior
run all focused and complete mandatory gates
commit intentionally
push normally to origin/M2
verify local/remote synchronization and a clean working tree
publish a new M2-S01 candidate for reviewer inspection
```

Do not create a pull request. Do not merge to `master`, force-push, rewrite published history, tag or release.

Do not add or use GitHub Actions, workflow-dispatched implementation, CI-driven commits, encoded patches or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before modifying code, tests, status or execution evidence, read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Current delivered AS-IS
docs/architecture/README.md
docs/architecture/datatype.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/api.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

# Active M2 authority
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/architecture/provenance.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Execution aids
docs/milestones/M2/wip/M2-S01-codex-prompt.md
docs/milestones/M2/wip/M2-S01-review-fixes-codex-prompt.md
```

Read owning sections dependency-first. The frozen documents are authority. The two prompts are non-normative execution aids. Do not derive requirements from any other historical file in `docs/milestones/M2/wip/`; `architecture/provenance.md` explicitly removes WIP discovery material from implementation authority.

Confirm from the repository itself that:

```text
checked-out branch                  = M2
README active cycle                 = M2 / IMPLEMENTATION / branch M2
origin/M2 baseline                  = e5728486... or a direct descendant
M2 contract                         = FINAL / FROZEN
M2 architecture set                 = FINAL / FROZEN
M2 steps                            = FINAL / FROZEN
M2-S00                              = reviewer-owned COMPLETED
M2-S01                              = REVIEW CHANGES REQUIRED or IN PROGRESS
review findings                     = S01-RF-01, S01-RF-02, S01-RF-03
M2-S02                              = BLOCKED
relevant architecture reopen        = none
STACK-01 ... STACK-10               = RATIFIED
```

Inspect at least these implementation and evidence hotspots before editing:

```text
src/netauto/application/datatypes.py
src/netauto/persistence/datatypes.py
src/netauto/domain/relationships.py
src/netauto/application/relationships.py
src/netauto/application/relationshipdefinitions.py
src/netauto/persistence/relationships.py
src/netauto/persistence/locking.py

tests/test_relationship_domain.py
tests/test_relationship_api.py
tests/test_relationshipdefinition_api.py
tests/test_relationship_semantic_concurrency.py
tests/test_m2_s01_semantic_concurrency.py
tests/test_s08_delete_diagnostics.py
tests/test_m2_traceability.py
```

Search the complete repository for all constructors, projections, fixtures and tests affected by the exact-pin change. Do not assume the list above is exhaustive.

Also verify that the obsolete S00 Actions/payload mechanism remains absent:

```text
.github/m2-s00-payload/
.github/workflows/materialize-verify-m2-s00.yml
.github/workflows/export-m2-worktree.yml
```

A valid externally supplied real PostgreSQL target through `TEST_DATABASE_URL` is mandatory for a complete corrective candidate. Verify availability during pre-flight. Do not provision PostgreSQL, use Docker/Testcontainers, invent credentials, fall back to localhost, fall back to `NETAUTO_DATABASE_URL`, or substitute SQLite.

If README, branch, `status.md`, frozen authorities, current candidate ancestry or required infrastructure disagree, stop before modifying the affected work and report the mismatch. If normative authorities conflict or do not determine one required behavior, stop only the affected point and report an architecture/documentation finding. Do not silently choose a convenient interpretation.

Code, tests, Git history, candidate reports and these prompts are evidence or execution aids, not semantic authority.

---

# 2. Corrective scope and hard boundary

This is not a second implementation of S01. Preserve the accepted candidate and modify only what is necessary to close the recorded findings and their evidence gaps.

## 2.1 Explicitly in scope

```text
separate DataType root-delete blocker diagnostics for:
    ObjectTemplate properties
    RelationshipDefinitionVersion properties

finite translation of both known DataType property-reference FK authorities

required factual Relationship exact RDV pin in domain/projection construction
positive non-boolean exact-pin validation
complete production/test constructor migration

semantic missing-dependency classification for RD CREATE and RDV REVISE
explicit exact DataTypeVersion selector preservation under delete-first races
implicit DataType default-selection freshness and outcome preservation

focused pure, application, API, persistence and deterministic PostgreSQL evidence
traceability updates for the new corrective targets
full regression closure
```

## 2.2 Explicitly out of scope

Do not introduce or modify:

```text
Relationship.DATA_CHANGE
Relationship.SCHEMA_CHANGE
S02 public routes or commands
Health
CLI
runtime settings or pool behavior
startup schema-revision guard
packaging/Linux operating capability
native auth, authorization or TLS
new advisory gates
new retry causes or retry middleware
a generic blocker-resource API
a generic dependency-selector abstraction exposed outside the application boundary
M1 -> M2 bridge, backfill, stamp path or dual decoder
```

No schema, migration, dependency or `uv.lock` change is expected or authorized for these findings. The durable revision must remain:

```text
0001_m2_kernel
```

with exactly one base, one head and exactly fifteen authoritative tables. If a schema, migration or dependency change appears necessary, stop and identify the frozen authority that requires it before making the change.

Do not modify frozen contract, architecture or `steps.md` to fit the implementation.

---

# 3. Shared correctness constraints

All corrections must preserve the completed S00 transaction foundation and accepted S01 realization:

```text
one semantic mutation / one UoW / one connection / one transaction
central prepare_lock_plan / LockPlan authority
three frozen transaction advisory gates
four exact PostgreSQL row-lock modes
canonical class and intra-class order
gate before rows
one complete pre-DML acquisition phase
fresh protected reread
no normal lock upgrade
no explicit post-DML lock
finite SQLSTATE + constraint-name classification
four total attempts only for the two frozen restart causes
no retry of 40P01 or 40001
no SQL, constraint, table, column, URL, credential or stack leakage
```

Do not weaken existing tests to accommodate the correction. Existing tests that rely on the removed implicit factual v1 constructor must be migrated to explicit factual state; their underlying topology/closure assertions remain required.

Avoid preventable N+1 queries. Correctness under concurrency must be proved with independent PostgreSQL sessions and deterministic orchestration. Sleep-only scheduling and generic reruns are forbidden.

---

# 4. S01-RF-01 — exact DataType delete blocker diagnostics

## 4.1 Required semantic result

DataType root deletion must preserve separate semantic blocker categories and exact counts.

The bounded public blocker entries for this correction are:

```text
object_template_property
relationship_definition_property
```

Use a deterministic fixed ordering:

```text
object_template_property
relationship_definition_property
```

Omit zero-count categories. Examples:

```json
{
  "blockers": [
    {"type": "relationship_definition_property", "count": 2}
  ]
}
```

```json
{
  "blockers": [
    {"type": "object_template_property", "count": 1},
    {"type": "relationship_definition_property", "count": 3}
  ]
}
```

Do not merge the counts. Do not report an RDV declaration as an ObjectTemplate property. Do not expose an unbounded identity list.

## 4.2 Persistence/application realization

Replace the current scalar combined-count boundary with a bounded structured result, for example a frozen dataclass or equivalent typed value owned by the persistence/application boundary.

It must preserve independently:

```text
object_template_property_count
relationship_definition_property_count
```

The query implementation may use one bounded aggregate statement or two deliberate aggregate statements. It must not issue one query per consumer row or materialize consumer identities.

The final defensive FK translation must recognize both exact known constraint authorities:

```text
fk_object_template_properties_datatype_version
fk_relationship_definition_properties_datatype_version
```

Translate each to a typed internal delete-reference result carrying the semantic blocker category. Unknown or mismatched constraint names remain `internal_error`; do not use a generic `23503 -> delete_blocked` escape hatch.

The application translation after rollback must produce the same bounded public shape as the normal precheck, with count `1` for the exact final-arbitration blocker. No constraint name or PostgreSQL detail crosses the public boundary.

Preserve transactional default clearing, root delete, rollback and `MODEL_ROOT_DELETE_GATE` behavior unchanged.

## 4.3 Mandatory evidence

Add permanent evidence for all of the following:

```text
RF01-A
    RDV-property-only reference
    -> DataType DELETE returns 409 delete_blocked
    -> one relationship_definition_property entry
    -> exact count

RF01-B
    mixed ObjectTemplate-property + RDV-property references
    -> two distinct entries
    -> exact counts
    -> deterministic order

RF01-C
    real PostgreSQL final FK arbitration through
    fk_object_template_properties_datatype_version
    -> typed bounded application result
    -> no internal leakage

RF01-D
    real PostgreSQL final FK arbitration through
    fk_relationship_definition_properties_datatype_version
    -> typed bounded application result
    -> no internal leakage
```

A narrowly scoped test interceptor may bypass the normal precheck only to exercise the real final FK translation. It must not change production semantics, issue sleep-based scheduling, swallow errors, or replace the real PostgreSQL constraint authority with a fake exception.

Retain the existing ObjectTemplate-only delete diagnostic regression and extend rather than replace its assertions.

---

# 5. S01-RF-02 — required factual exact RDV pin

## 5.1 Domain construction rule

A factual Relationship has no implicit schema identity. Remove the default value `1` from:

```text
Relationship.relationship_definition_version
ObjectRelationshipView.relationship_definition_version
```

The exact pin must be a required constructor value. Do not replace `1` with another default, sentinel, optional value, latest/default lookup or post-construction mutation.

`RelationshipProjection.relationship_definition_version` already represents a required exact value and must remain so.

## 5.2 Validation

At the pure/domain validation boundary, reject an exact factual pin that is:

```text
boolean
zero
negative
```

Use the existing bounded domain validation style, with a stable path such as:

```text
relationship_definition_version
```

and the existing positive-value rule vocabulary where applicable.

Persistence still owns the positive database CHECK. Domain/application validation must not rely solely on PostgreSQL to discover an invalid in-memory or decoded fact.

## 5.3 Complete constructor migration

Update every production and evidence construction site to supply the exact observed or selected pin explicitly.

Rules:

```text
production CREATE
    -> selected_version after protected reread

persistence decode
    -> persisted relationships.relationship_definition_version

Object-relative projection
    -> factual Relationship exact pin

historical/current validation tests
    -> the concrete exact version represented by the fixture

pure closure tests with no schema behavior under test
    -> an explicit positive test pin, never an omitted argument
```

Search the repository structurally, not only by the currently failing tests. Update positional calls carefully so `resolutions`, exact pin and properties cannot be accidentally swapped.

When factual properties are empty, `{}` remains a valid canonical factual state. It is not a schema selector and must not compensate for an absent exact pin. Prefer explicit `{}` at authoritative factual construction sites where it improves clarity.

Do not change public CREATE omission semantics: omitted request `relationship_definition_version` still resolves the stable Definition default inside the protected CREATE UoW and persists the selected exact pin.

## 5.4 Mandatory evidence

Add permanent pure/static evidence proving:

```text
RF02-A
    Relationship cannot be constructed without an exact pin

RF02-B
    ObjectRelationshipView cannot be constructed without an exact pin

RF02-C
    bool / zero / negative factual pins are rejected by pure validation

RF02-D
    relationship_views and Object-relative persistence/API projection
    preserve the exact factual pin without substituting v1

RF02-E
    a fact pinned to a non-v1 exact version survives GET/list/event paths
    with that exact version unchanged
```

Use `inspect.signature`, AST inspection or an equivalent stable static check to prevent reintroduction of a constructor default. Do not rely only on a test that happens to pass an argument.

Preserve all existing pure closure, symmetry, self-loop, overlap and incomplete-closure assertions while migrating their constructors.

---

# 6. S01-RF-03 — semantic missing-dependency classification

## 6.1 Governing rule

A public missing-operand result is derived from the semantic command candidate, not from whichever physical lock key appears first in canonical acquisition order.

The current physical order remains correct:

```text
DataType header
-> exact DataTypeVersion
```

Do not change lock ordering to repair error details.

## 6.2 Explicit DataTypeVersion selection

For a property candidate with an explicitly supplied exact version:

```text
datatype_id = D
datatype_version = V
```

if either the planned DataType header or exact DataTypeVersion row is absent after discovery, return:

```text
422 referenced_resource_not_found

details = {
    resource_type: datatype_version,
    id: D,
    version: V
}
```

The known exact version must never be dropped merely because the first missing physical key is the stable header and therefore has `key.version = None`.

When several semantic operands disappear, choose one deterministically from the semantic candidate ordering. Do not choose by physical lock-class order or set iteration. Preserve a bounded single-selector result.

## 6.3 Implicit DataType default selection

For a property candidate with omitted `datatype_version`, preserve the frozen implicit-selector semantics:

```text
DataType lineage disappeared
    -> referenced_resource_not_found for resource_type datatype + id

fresh default is null
    -> default_version_unavailable

fresh default identifies another exact version
    -> LockPlanStale
    -> complete UoW rollback/restart within the existing shared budget

fresh default still identifies the planned version but the exact row is absent,
cross-lineage or otherwise corrupt
    -> internal_error according to the persisted-corruption boundary

fresh exact target is no longer PUBLISHED for a new/rebound admission
    -> dependency_not_admissible
```

Do not add a third restart cause. A default change remains `LOCK_PLAN_STALE`; a normal semantic failure is not retried.

## 6.4 Implementation boundary

Introduce the smallest local semantic descriptor/helper necessary to retain, for each requested declaration:

```text
property identity/order
DataType id
explicit versus implicit selector
requested explicit version, when present
optimistically selected exact version
current exact dependency, when relevant
```

This helper belongs inside the application implementation boundary. It is not a public DTO, domain resource, persistence authority or generic cross-project selector framework.

Use it consistently in both:

```text
RelationshipDefinition CREATE initial properties
RelationshipDefinitionVersion REVISE differential properties
```

Re-run semantic resolution after lock acquisition and compare the complete required plan through the existing `LockPlan.require_same_plan` discipline. Do not append locks or classify from stale optimistic state.

## 6.5 Mandatory deterministic PostgreSQL evidence

Add real-PostgreSQL delete-first evidence with independent sessions and deterministic barriers after semantic discovery but before the candidate acquires its complete lock plan.

Required cases:

```text
RF03-A — explicit RD CREATE
    discovery observes exact DTV (D, V)
    DataType root delete commits first
    CREATE returns referenced_resource_not_found
    details contain resource_type, id and exact version V
    no Definition, Resolution, RDV or declaration row remains

RF03-B — explicit RDV REVISE
    discovery observes exact DTV (D, V)
    target DataType root delete commits first
    REVISE returns referenced_resource_not_found
    details contain resource_type, id and exact version V
    draft revision and complete declarations remain unchanged

RF03-C — implicit lineage disappearance
    discovery resolves a DataType default
    DataType root delete commits first
    result identifies the DataType operand, not a datatype_version with null version
    no internal detail leaks

RF03-D — implicit default change
    discovery resolves default V1
    concurrent committed default change selects V2
    operation performs a complete approved LockPlanStale restart
    final candidate materializes the fresh valid exact pin or returns the
    frozen semantic result if the fresh selector is unavailable/ineligible
    no stale V1 pin is written
```

Cover both API/application bounded details and final database state. Use no sleep-based scheduling. A test-only pre-acquisition cut may observe and pause the production path but must not alter candidate data, issue semantic SQL, change transaction isolation, or translate failures differently from production.

Map the CREATE binding variants to the existing `ROW-24` authority and the differential REVISE variants to `REF-09` where appropriate. Preserve stable scenario IDs; do not invent a new canonical scenario for an uncovered variant of an existing authority.

---

# 7. Preserve the accepted S01 candidate

The corrective delta must not disturb already accepted areas. Reconfirm at least:

```text
exact fifteen-table metadata
one durable root / one base / one head
compare_metadata == []
old M1 revisions absent
final index positive/negative inventory
RDV lifecycle and historical evolution
first-publication default policy
capability membership and projection
uniform DT / OT / RD default-pointer validation
factual CREATE conflict semantics
factual GET and Object-relative projection
exact-ID DELETE 204/404 and ABA safety
CREATED/DELETED factual lifecycle snapshots
all S00 PLAN evidence
no S02 routes or commands
```

Do not change migration files merely to regenerate formatting or reorder equivalent DDL. No schema drift is expected.

---

# 8. Traceability requirements

Extend the machine-checkable S01 registry rather than creating an untracked review-only test collection.

Add an exact finding registry, conceptually:

```text
S01_REVIEW_FIX_TARGETS = {
    "S01-RF-01": {...real collected targets...},
    "S01-RF-02": {...real collected targets...},
    "S01-RF-03": {...real collected targets...},
}
```

Every target must resolve to a real collected test. No empty bundle, placeholder target or source-text-only claim is sufficient.

Update affected S01 bundle mappings, including the appropriate concrete targets for:

```text
M2-VER-01
M2-VER-04
M2-VER-05
M2-VER-06
```

and any other already implemented S01 bundle directly exercised by the correction. Do not mark a future bundle PASS merely because a corrective test exists.

Preserve the exact frozen census:

```text
16 outcomes
32 acceptance criteria
32 evidence bundles
83 canonical scenarios
```

Preserve every S00 `PLAN-01 ... PLAN-06` target.

When one stable scenario requires several mandatory variants, represent all concrete targets machine-readably. Do not hide required variants behind an undocumented primary target.

---

# 9. Verification requirements

Run focused gates first, then all cross-boundary and complete repository gates. Report exact commands, counts and durations where available.

At minimum run the concrete repository equivalents of:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright

# RF02 pure/static exact-pin evidence
uv run pytest -q \
  tests/test_relationship_domain.py \
  tests/test_relationshipdefinition_domain.py \
  tests/test_m2_traceability.py -ra

# RF01 bounded DataType delete diagnostics and FK classification
uv run pytest -q \
  tests/test_s08_delete_diagnostics.py \
  <new/focused RF01 persistence or API targets> -ra

# RF03 and affected S01 concurrency/application evidence
uv run pytest -q \
  tests/test_m2_s01_semantic_concurrency.py \
  tests/test_relationship_semantic_concurrency.py \
  <new/focused RF03 targets> -ra

# affected HTTP contracts
uv run pytest -q \
  tests/test_relationship_api.py \
  tests/test_relationshipdefinition_api.py -ra

# unchanged durable schema assurance
uv run pytest -q \
  tests/test_schema_metadata.py \
  tests/test_migrations.py -ra

# complete PostgreSQL concurrency
uv run pytest -q -m "postgresql and concurrency" -ra

# complete non-PostgreSQL regression
uv run pytest -q -m "not postgresql" -ra

# complete repository suite, including PostgreSQL tests
uv run pytest -q -ra
```

Do not duplicate a test file on one command line merely because it appears in more than one category. Use exact target lists in the handoff.

Report explicitly:

```text
CPython version
PostgreSQL server version
S01-RF-01 result and exact targets
S01-RF-02 result and exact targets
S01-RF-03 result and exact targets
affected M2-VER bundle results
ROW-24 and REF-09 corrective variant results
schema drift result
one-base / one-head result
full-suite count and duration
skips / xfails / reruns census
whether any supported path returned SQLSTATE 40P01
```

No unexplained skip, xfail, flaky rerun or generic retry is permitted for normative corrective evidence.

If `TEST_DATABASE_URL` is unavailable or any mandatory real-PostgreSQL/full gate is blocked or failing:

```text
leave M2-S01 IN PROGRESS or retain the recorded review finding state
record the exact blocker/failure in status.md
do not claim CANDIDATE READY FOR REVIEW
push a partial correction only when useful and explicitly labelled
never fabricate evidence or substitute another backend
```

---

# 10. Documentation and status discipline

Do not modify frozen contract, architecture or `steps.md`.

Keep both active S01 execution aids in `docs/milestones/M2/wip/` until reviewer acceptance:

```text
M2-S01-codex-prompt.md
M2-S01-review-fixes-codex-prompt.md
```

Do not delete them in the corrective candidate.

Update `docs/milestones/M2/status.md` only with verified operational facts.

During active incomplete correction, the state may be:

```text
M2-S01 IN PROGRESS
```

while preserving the reviewer finding record.

Only when all three findings are closed, every mandatory gate passes against real PostgreSQL, and the corrective commits are pushed may Codex set:

```text
M2-S01 CANDIDATE READY FOR REVIEW
reviewer decision pending
```

Never mark:

```text
M2-S01 COMPLETED
M2-S02 READY or IN PROGRESS
M2 DELIVERED
review ACCEPTED
```

Those states are reviewer/human-owned.

The new status record must retain the original candidate commits and add the corrective implementation/status commit identities, exact evidence results and environment versions.

---

# 11. Toolchain and implementation discipline

Use only the ratified baseline:

```text
CPython 3.14.x
native asyncio
uv with committed uv.lock
SQLAlchemy Core 2.x
Psycopg 3
Alembic
FastAPI / Pydantic 2
pytest / pytest-asyncio
HTTPX ASGITransport
real PostgreSQL through TEST_DATABASE_URL
Ruff
Pyright strict
```

Do not use:

```text
SQLAlchemy ORM Session / AsyncSession
SQLite
Docker
Testcontainers
sleep-based concurrency orchestration
SERIALIZABLE as a substitute for explicit locking
new advisory gates
new automatic retry causes
ON CONFLICT DO NOTHING aggregate writes
new dependency for convenience
global Ruff/Pyright relaxation
broad warning/error suppression
GitHub Actions
```

Application/domain modules remain free of FastAPI, Pydantic, SQLAlchemy and Psycopg imports. Persistence rows and constraint identities do not cross the public boundary.

Keep any unavoidable suppression narrow, local and justified in the handoff.

---

# 12. Git and publication discipline

Before publication:

```text
review the complete diff from e5728486...
review staged diff
exclude unrelated changes
verify no secret or database URL is present
verify no schema/migration/dependency/lockfile drift
verify both S01 prompts remain present
verify obsolete Actions/payload material remains absent
run git diff --check
```

Use one or more coherent intentional commits. Suitable titles include:

```text
fix(m2-s01): correct review findings

test(m2-s01): cover exact pins and delete-first references

docs(m2): publish corrected S01 candidate
```

Push normally to:

```text
origin/M2
```

After push verify:

```text
local HEAD SHA
origin/M2 SHA
remote branch SHA
local/remote synchronization
working tree clean
```

Do not create a PR, merge, force-push, tag or release.

---

# Completion report

At the end provide a reviewer-oriented handoff containing only verified facts:

- cycle `M2`, slice `M2-S01`, branch `M2`;
- corrective implementation and status commit SHA(s);
- push, local/remote synchronization and working-tree state;
- concise changed-file/category inventory;
- `S01-RF-01` implementation summary;
- separate OT-property and RDV-property blocker examples and counts;
- final-FK translation result for both known constraints;
- `S01-RF-02` constructor/API/domain summary;
- proof that no factual exact-pin default remains;
- positive non-boolean pin validation result;
- non-v1 GET/list/event projection result;
- `S01-RF-03` semantic missing-classification summary;
- explicit RD CREATE delete-first result with exact `details.version`;
- explicit RDV REVISE delete-first result with exact `details.version`;
- implicit lineage-disappearance and default-change result;
- exact new traceability targets and affected M2-VER/scenario mappings;
- confirmation that all previous S01 evidence remains passing;
- schema/migration result: expected unchanged;
- dependency/lockfile result: expected unchanged;
- complete quality/test commands, counts and durations;
- CPython and PostgreSQL versions;
- full-suite result and explicit supported-path `40P01` result;
- skip/xfail/rerun census;
- confirmation that no S02, Health, CLI or startup capability was introduced;
- confirmation that no M1 bridge/backfill/stamp/dual decoder exists;
- confirmation that Actions/payload material remains absent;
- every unexecuted requirement and exact reason;
- every residual risk or architecture/documentation finding;
- final `status.md` state without claiming reviewer-owned completion.

Use the wording:

```text
M2-S01 corrective candidate implemented and ready for reviewer inspection
```

only when every mandatory corrective and full gate has passed against real PostgreSQL and the candidate has been pushed.