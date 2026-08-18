# Codex review-fix prompt — M2-S03

**Status:** NON-NORMATIVE REVIEW-FIX EXECUTION PROMPT.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture, `steps.md`, and the reviewer-owned state in `status.md`.

## Assignment

Correct exactly the three open reviewer findings inside:

```text
M2-S03 — Complete kernel concurrency and deadlock-evidence closure
```

Work directly on branch:

```text
M2
```

The reviewer-owned corrective baseline is:

```text
8ddcfdca85e73b64c5e3bc603d8611d0ffb2eb1c
docs(m2): require S03 review fixes
```

The published implementation material to preserve is:

```text
original S03 prompt              29e490087b24f1ff17d1e4be1abc629b0be3a962
partial implementation           f70ec8968ddef3bd106749b14def0e5cde9688e3
partial evidence/status          1c2dd13b6e5e57310db6f12f0a6d8307c35bda67
review findings                  8ddcfdca85e73b64c5e3bc603d8611d0ffb2eb1c
```

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    REVIEW CHANGES REQUIRED
M2-S04    BLOCKED
```

Implement only:

```text
S03-RF-01 — exact frozen scenario-to-recipe registry
S03-RF-02 — complete structured T3 worker outcome / SQLSTATE capture
S03-RF-03 — complete persisted-state assertions for REF-08
```

Do not start `M2-S04`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not add or use GitHub Actions, encoded patches, workflow-dispatched implementation or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before editing, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Delivered AS-IS authorities
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/persistence.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

# Active M2 authorities
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Active execution aids
docs/milestones/M2/wip/M2-S03-codex-prompt.md
docs/milestones/M2/wip/M2-S03-review-fixes-codex-prompt.md
```

Confirm from the repository that:

```text
branch                              M2
origin/M2 ancestry                  includes 8ddcfdca...
contract                            FINAL / FROZEN
architecture set                    FINAL / FROZEN
steps                               FINAL / FROZEN
M2-S03                              REVIEW CHANGES REQUIRED
M2-S04                              BLOCKED
open architecture reopen            none
TEST_DATABASE_URL                    available and usable
```

Inspect the current implementation and evidence boundaries, including at least:

```text
tests/support/pg_harness.py
tests/support/semantic_concurrency.py
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py
tests/test_m2_s03_semantic_concurrency.py
all modules referenced by M2_SCENARIO_TO_TARGETS

src/netauto/persistence/locking.py
src/netauto/persistence/uow.py
application and persistence services used by REF-08 and PLAN-05
```

Search the complete repository for:

```text
M2_SCENARIO_TO_RECIPES
ScenarioRecipes
REC-LOCK
REC-UNIQUE
REC-FK
REC-GATE
REC-CUT
REC-ROLLBACK
REC-PROGRESS
REC-ABA
REC-PLAN
REC-CLASSIFY
REC-RESTART

capture(
capture_worker_outcome
blocked_race
progress_race
asyncio.create_task
sqlstate
pgcode
40P01
40001
pytest.mark.concurrency
```

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` is mandatory. Do not provision a database, invent credentials, use Docker/Testcontainers, substitute SQLite, fall back to localhost or use `NETAUTO_DATABASE_URL` as the test target.

If repository state or a frozen authority conflicts with this bounded task, stop the affected point and report it. Do not alter frozen architecture to fit the candidate.

---

# 2. Authority resolution for the former `S03-FINDING-01`

The reviewer has resolved the implementer-raised REF-08 finding. No architecture reopen is authorized.

The original S03 execution aid contained an invalid requirement for the `delete-first` REF-08 variant:

```text
target disappears
-> OT.CREATE_NEXT fails with referenced_resource_not_found
```

That sentence is superseded by `status.md` and this review-fix aid.

The authority-conforming result is:

```text
target root DELETE starts first
-> acquires its normal gate/root ownership
-> observes the reference already persisted by the eligible source version
-> returns bounded delete_blocked and rolls back
-> waiting OT.CREATE_NEXT acquires historical-clone KS lifetime holds
-> exactly one complete clone commits
```

Reason:

```text
CREATE_NEXT copies already-owned references
source references are protected by immediate RESTRICT FKs
a delete that observes an existing blocker may fail conservatively
a historical clone is RL lifetime work, not new BA/PUBLISHED admission
```

Therefore:

```text
preserve immediate RESTRICT FKs
preserve delete_blocked
preserve KS for cloned target lifetime
preserve complete clone success after the losing delete
```

Do not weaken schema, delete policy, source eligibility or production semantics to manufacture target disappearance.

---

# 3. Hard scope boundary

## 3.1 In scope

```text
exact scenario recipe ownership for all 83 canonical IDs
structured outcome capture for every T3 semantic worker
complete SQLSTATE census for the exact scenario ledger
immediate failure on supported-path 40P01
no-retry evidence for 40P01 and 40001
complete REF-08 source/clone/target assertions
traceability and focused regression updates required by those corrections
status/evidence handoff after all mandatory gates pass
```

## 3.2 Out of scope

Do not add or change:

```text
business or HTTP semantics
public routes, DTOs or error codes
41-mutation census
83-scenario census or stable IDs
21-predicate census or frozen predicate mapping
three advisory gates
four row-lock modes
canonical row order
restart causes or attempt budget
schema, migration, indexes or 0001_m2_kernel
dependencies or uv.lock
Health, startup guard, runtime settings, CLI, packaging or M2-S04
M1 -> M2 bridge/backfill/stamp/dual decoder
```

Preserve the accepted boundary:

```text
15 authoritative tables
one Alembic base / one head
compare_metadata == []
41 mutations + 22 reads = 63 business HTTP operations
```

---

# 4. `S03-RF-01` — exact frozen scenario-to-recipe registry

The current generic family-derived recipe map is not acceptable. Build one singular exact registry by composing:

```text
delivered canonical recipe ownership
+
explicit M2 scenario additions
+
explicit M2 recipe deltas only
```

Do not infer recipes from the scenario prefix alone.

## 4.1 Exact expected map

Represent one primary recipe and every required secondary recipe.

### ROW

```text
ROW-01 ... ROW-09
    primary     REC-LOCK

ROW-10
    primary     REC-CUT

ROW-11 ... ROW-30
    primary     REC-LOCK
```

### ARB

```text
ARB-01
    primary     REC-UNIQUE

ARB-02
    primary     REC-UNIQUE

ARB-03
    primary     REC-LOCK

ARB-04
    primary     REC-LOCK

ARB-05
    primary     REC-UNIQUE
    secondary   REC-ABA

ARB-06
    primary     REC-LOCK

ARB-07
    primary     REC-ABA
    secondary   REC-UNIQUE
    secondary   REC-RESTART

ARB-08
    primary     REC-UNIQUE
    secondary   REC-ROLLBACK
```

`ARB-05`, `ARB-06` and `ARB-07` retain their delivered orchestration ownership even though M2 changes public loser/delete semantics. `REC-RESTART` on `ARB-07` is the explicit M2 winner-disappearance whole-UoW restart evidence; it supplements rather than replaces the delivered UNIQUE variant.

### REF

```text
REF-01 ... REF-10
    primary     REC-FK

REF-11
    primary     REC-GATE
    secondary   REC-FK
```

### GATE

```text
GATE-01
    primary     REC-GATE

GATE-02
    primary     REC-GATE
    secondary   REC-CUT

GATE-03 ... GATE-05
    primary     REC-GATE

GATE-06
    primary     REC-GATE
    secondary   REC-CUT

GATE-07
    primary     REC-GATE
```

### SNAP

```text
SNAP-01 ... SNAP-05
    primary     REC-CUT
```

### ATOMIC

```text
ATOMIC-01
    primary     REC-ROLLBACK

ATOMIC-02
    primary     REC-UNIQUE
    secondary   REC-ROLLBACK

ATOMIC-03 ... ATOMIC-07
    primary     REC-ROLLBACK
```

### PAR

```text
PAR-01
    primary     REC-PROGRESS

PAR-02
    primary     REC-PROGRESS

PAR-03
    primary     REC-LOCK

PAR-04
    primary     REC-GATE

PAR-05
    primary     REC-PROGRESS

PAR-06
    primary     REC-PROGRESS

PAR-07
    primary     REC-LOCK
    secondary   REC-PROGRESS

PAR-08
    primary     REC-PROGRESS

PAR-09
    primary     REC-PROGRESS
```

`PAR-07` owns both delivered variants: description/default contention (`REC-LOCK`) and description/DRAFT-revise progress (`REC-PROGRESS`). Keep both explicitly represented beneath the stable scenario ID.

### PLAN

```text
PLAN-01
    primary     REC-PLAN

PLAN-02
    primary     REC-PLAN

PLAN-03
    primary     REC-RESTART

PLAN-04
    primary     REC-CLASSIFY

PLAN-05
    primary     REC-RESTART

PLAN-06
    primary     REC-PLAN
```

## 4.2 Registry implementation requirements

Create or correct one canonical test-only registry. Avoid two independently maintained complete maps.

Acceptable structure:

```text
one delivered recipe projection
+
one explicit M2 addition/delta projection
-> one M2_SCENARIO_TO_RECIPES authority
```

Add permanent machine checks that prove:

```text
exactly 83 keys
exact key equality with M2_CONCURRENCY_SCENARIOS
exact primary and secondary equality for every entry
no empty recipe set
one primary per scenario
primary not repeated as secondary
all names in the exact 11-recipe vocabulary
no generic prefix fallback remains
all target mappings and stable scenario IDs remain unchanged
```

The test must fail for every mismatch listed in `status.md`, not merely for an unknown recipe string.

Do not weaken or remove any accepted scenario target to make the map easier to satisfy.

---

# 5. `S03-RF-02` — complete T3 worker outcome and SQLSTATE capture

The existence of `WorkerOutcome` is insufficient while shared orchestration still bypasses it.

Implement one authoritative structured outcome ledger used by every semantic worker in every canonical T3 target.

## 5.1 Required worker record

For each worker, preserve at minimum:

```text
pytest node ID
canonical scenario ID or IDs represented by the target
worker role: B / T1 / T2 / T3 as applicable
returned semantic value, when any
ApplicationFailure, when any
unexpected exception type and safe test diagnostic
PostgreSQL SQLSTATE, when present
last observed production/test phase
transaction outcome: COMMITTED / ROLLED_BACK / no semantic transaction
attempt/UoW identities when the scenario proves restart
```

The test record may hold the actual exception object internally, but no production/public failure behavior may change.

## 5.2 Robust SQLSTATE extraction

The extractor must handle bounded wrapped forms, including as applicable:

```text
error.sqlstate
error.pgcode
error.orig
error.driver_exception
__cause__ chain
__context__ chain
ApplicationFailure chained from a SQLAlchemy/DBAPI failure
```

Traverse safely with cycle detection. Do not inspect arbitrary string messages to guess a SQLSTATE.

If production translation removes the raw error from the visible exception chain, use a test-only SQLAlchemy/engine/UoW error observation boundary to record the DBAPI SQLSTATE before normal production mapping consumes it. Do not modify the public error envelope or expose database internals.

## 5.3 Shared orchestration integration

Introduce structured forms conceptually equivalent to:

```text
run_worker_outcome(...)
blocked_race_outcomes(...)
progress_race_outcomes(...)
```

The existing convenience helpers may continue returning semantic values for legacy assertions, but they must delegate to the structured forms and must register/assert the underlying outcomes before unwrapping them.

At minimum, correct all paths that currently use:

```text
capture()
blocked_race()
progress_race()
direct asyncio.create_task() for semantic workers
custom worker wrappers in canonical scenario targets
```

No canonical T3 worker may bypass the outcome ledger.

A static/AST check may help reject direct legacy bypasses in mapped concurrency targets, but runtime evidence is mandatory.

## 5.4 Forbidden and allowed SQLSTATE behavior

For every supported canonical scenario worker:

```text
40P01
    -> immediate scenario failure
    -> no automatic retry

40001
    -> immediate scenario failure unless the target is the intentional
       negative control proving no retry
    -> no automatic retry

23505 / 23503 or another finite expected arbitration SQLSTATE
    -> may be observed internally
    -> must be recorded
    -> production semantic mapping and rollback remain authoritative
```

Separate:

```text
canonical supported-scenario SQLSTATE census
intentional negative-control SQLSTATE evidence
```

Do not report “no SQLSTATE observed” unless the structured ledger actually contains none. Report exact observed values and counts, grouped at least by scenario/node/worker role.

## 5.5 Required focused evidence

Add tests proving all of the following:

```text
direct sqlstate extraction
pgcode extraction
SQLAlchemy .orig wrapping
nested cause/context extraction
ApplicationFailure chained from DBAPI material
cycle-safe traversal
40P01 causes immediate harness failure
40001 is captured and is not retried
23505/23503 can be captured while public semantic mapping remains unchanged
blocked_race compatibility path records both workers
progress_race compatibility path records both workers
custom direct-worker path records every worker
restart path records distinct UoW/attempt identities
```

Add a machine-checkable coverage assertion tying every canonical T3 target to the SQLSTATE-aware orchestration. An unexplained bypass is a failing target, not a documentation note.

## 5.6 Exact scenario-ledger execution

Execute the sorted deduplicated union of every target in `M2_SCENARIO_TO_TARGETS` under the outcome-aware harness.

Report:

```text
83 / 83 scenario IDs
exact selector count
exact collected node count
exact executed node count
exact passed node count
exact semantic-worker outcome count
exact COMMITTED / ROLLED_BACK / no-UoW counts
exact SQLSTATE census
supported-path 40P01 count = 0
unexpected 40001 count = 0
```

Counts may increase because of the corrective regressions. Do not preserve an old count by omitting new evidence.

Re-run `PLAN-05` and retain exact evidence that neither `40P01` nor `40001` is retried by production.

---

# 6. `S03-RF-03` — complete REF-08 cloned-state evidence

Preserve the six real-PostgreSQL variants:

```text
shapes
    parent
    component
    property

orders
    clone-first
    delete-first
```

Preserve real blocking through independent sessions and `pg_blocking_pids()`.

## 6.1 Common assertions for all six variants

Before the race, capture the complete source version and target state. After both operations finish, prove:

```text
delete result                     delete_blocked
clone result                      exact version 2, DRAFT, revision 1
consumer version set              exactly source v1 + one new v2
source version                    unchanged in every persisted field
target root                       still present
target exact version, when exact  still present
clone declarations                complete, not partial
no extra version/declaration      present
clone plan                        KS lifetime modes only for cloned pins
PUBLISHED-admission SHARE         absent for every historical clone target
supported-path 40P01              absent
```

Compare complete domain/store projections, not only row counts.

## 6.2 Parent shape

Prove source and clone both retain exactly:

```text
parent_template_id = target root
parent_version     = exact source target version
```

Also prove both versions retain their complete property/component sets unchanged, even when those sets are empty.

## 6.3 Component shape

Prove source and clone contain the same complete component declaration, including every persisted field:

```text
name
position
target_template_id
```

The target root must remain present after `delete_blocked`.

## 6.4 Property shape

Prove source and clone contain the same complete property declaration, including every persisted field represented by the domain/persistence model, at minimum:

```text
name
position
datatype_id
datatype_version
value_mode
required
migration_default or equivalent persisted default field
```

Compare the complete property value object when possible so future fields cannot silently escape the assertion.

The DataType root and exact DTV must remain present after `delete_blocked`.

## 6.5 Atomicity and no partial clone

Add or strengthen an assertion showing that a forced late clone failure, if already represented by accepted atomic evidence, still rolls back:

```text
new version header
parent pin
every cloned property/component row
```

Do not invent a new canonical scenario ID. Reuse `REF-08` and the existing atomic scenario that owns clone/child rollback when applicable. The six REF-08 targets themselves must directly prove the successful clone is complete.

---

# 7. Traceability and evidence updates

Preserve exactly:

```text
41 mutation IDs
83 scenario IDs
21 predicate IDs
3 advisory gates
4 row-lock modes
M2-VER-15 ... M2-VER-19 primary ownership
all accepted S00/S01/S02 bundle targets
63 business HTTP operations
```

Add a machine-resolvable review-fix registry:

```text
S03_REVIEW_FIX_TARGETS = {
    "S03-RF-01": ...,
    "S03-RF-02": ...,
    "S03-RF-03": ...,
}
```

Each set must be non-empty, resolve against real pytest collection and contain the exact focused targets that close the finding.

Keep future bundles honest:

```text
M2-VER-15 ... M2-VER-19    IMPLEMENTED with exact targets
M2-VER-22 and later        DESIGNED until their owning slices
M2-VER-31 / 32             still S08-owned
```

Do not mark a bundle `PASS` in the static registry. Executed PASS belongs in candidate evidence/status.

---

# 8. Mandatory verification

Run the smallest focused checks first, then every complete S03 gate.

## 8.1 Build and static quality

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

## 8.2 Focused review-fix targets

Run exact tests for:

```text
S03-RF-01 exact 83-entry recipe equality
S03-RF-02 SQLSTATE extraction and structured helper integration
S03-RF-02 negative controls for 40P01 / 40001 no retry
S03-RF-03 all six REF-08 variants
S03 review-fix traceability registry
PLAN-05
```

## 8.3 Exact registries and bundle ledgers

Run and report the exact deduplicated target sets for:

```text
41-mutation evidence ledger
83-scenario evidence ledger under SQLSTATE-aware capture
21-predicate coverage
M2-VER-15 ... M2-VER-19
```

## 8.4 Complete affected suites

At minimum run:

```text
uv run pytest -q \
  tests/test_m1_traceability.py \
  tests/test_m2_s00_traceability.py \
  tests/test_m2_traceability.py \
  <review-fix traceability targets> -ra

uv run pytest -q \
  tests/test_datatype_semantic_concurrency.py \
  tests/test_objecttemplate_semantic_concurrency.py \
  tests/test_object_semantic_concurrency.py \
  tests/test_relationshipdefinition_semantic_concurrency.py \
  tests/test_relationship_semantic_concurrency.py \
  tests/test_m2_s01_semantic_concurrency.py \
  tests/test_m2_s02_semantic_concurrency.py \
  tests/test_m2_s03_semantic_concurrency.py -ra

uv run pytest -q tests/test_m2_locking.py \
  tests/test_m2_locking_postgresql.py -ra

uv run pytest -q tests/test_schema_metadata.py \
  tests/test_migrations.py -ra

uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

Adapt filenames only when the implementation places new focused tests elsewhere. Do not omit an obligation.

No normative requirement may be skipped, xfailed, deselected accidentally or hidden by rerun. Timeout remains a hang guard only.

## 8.5 Unchanged-boundary verification

Explicitly verify and report:

```text
15 authoritative tables
one Alembic base / one head
0001_m2_kernel unchanged
compare_metadata == []
no schema or migration diff
no dependency or uv.lock diff
63 exact business HTTP operations
no Health/startup/CLI/packaging/M2-S04 surface
obsolete Actions/payload material absent
```

---

# 9. Status, commits and publication

Keep both execution aids in the working tree until reviewer acceptance:

```text
docs/milestones/M2/wip/M2-S03-codex-prompt.md
docs/milestones/M2/wip/M2-S03-review-fixes-codex-prompt.md
```

Use intentional commits, normally separating:

```text
review-fix implementation and focused evidence
candidate evidence/status
optional provenance-only correction when required
```

Only after every focused, exact-ledger and complete gate passes may `status.md` record:

```text
M2-S03 — CANDIDATE READY FOR REVIEW
reviewer decision pending
M2-S04 — BLOCKED
```

The candidate record must include:

```text
corrective baseline and prompt commit
implementation/evidence/provenance commits
resolution of S03-RF-01 / 02 / 03
exact 83-entry recipe registry disposition
exact structured worker-outcome coverage
exact canonical and negative-control SQLSTATE census
complete REF-08 source/clone/target evidence
41 / 83 / 21 censuses
M2-VER-15 ... 19 results
all commands, counts and durations
environment versions
skip / xfail / rerun census
schema/migration/dependency/public-surface unchanged statement
```

Codex must not declare `M2-S03 COMPLETED`; acceptance is reviewer-owned.

If any required target fails, `TEST_DATABASE_URL` is unavailable, a canonical worker bypasses the outcome ledger, a supported scenario observes `40P01`, or another architecture/documentation contradiction appears:

```text
do not mark CANDIDATE READY FOR REVIEW
do not start M2-S04
leave an honest IN PROGRESS or STOP state
record the exact blocker and completed partial work
```

Push normally to `origin/M2` and verify:

```text
local HEAD == origin/M2 == remote M2
working tree clean
ahead/behind 0/0
no PR
no GitHub Actions or encoded publication mechanism
```

---

# 10. Required handoff

Report verified facts only:

```text
cycle / slice / branch
starting corrective baseline
implementation, evidence and provenance commits
remote synchronization and clean tree

S03-RF-01
    exact recipe-map implementation
    exact equality result for all 83 IDs
    explicit disposition of every former mismatch

S03-RF-02
    structured harness architecture
    proof every canonical T3 worker is captured
    worker outcome totals
    commit / rollback totals
    SQLSTATE census by canonical scenarios
    negative-control census
    40P01 / 40001 no-retry result

S03-RF-03
    six REF-08 variants
    source/clone equality by shape
    target survival
    exact version/declaration counts
    KS/no-S plan result

41 / 83 / 21 registries
M2-VER-15 ... M2-VER-19 results
focused and complete command results
CPython / PostgreSQL / uv versions
skip / xfail / rerun census
unchanged schema/migration/dependency/HTTP surface
status = CANDIDATE READY FOR REVIEW or honest partial state
```

Do not claim there are no residual findings merely because the full suite is green. Demonstrate each review finding independently and leave the reviewer to decide completion.