# Codex review-fix prompt — M2-S00

**Status:** NON-NORMATIVE REVIEW-FIX PROMPT.

This execution aid narrows the next implementation pass for the still-open `M2-S00` slice. It does not override `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract, architecture or steps, the active status, or the ratified technology baseline.

## Assignment

Correct and complete the current partial implementation of:

```text
M2-S00 — LockPlan and AS-IS transaction-hardening foundation
```

Implementation under review:

```text
328fe179dade3a30168cb2e14dbbb5042a82e463
feat(m2-s00): centralize transaction lock planning
```

Work directly on branch:

```text
M2
```

This is a **review-fix inside the same slice**. Do not create another slice, do not start `M2-S01`, and do not introduce any M2 business/API/schema capability.

The required publication action is:

```text
correct the implementation
add or strengthen permanent evidence
run every available focused gate
run the mandatory real-PostgreSQL and full gates when TEST_DATABASE_URL is available
commit intentionally
push normally to origin/M2
leave the branch synchronized and clean
```

Do not create a pull request. Do not merge, tag, release, force-push or rewrite history.

---

# 1. Mandatory pre-flight

Before changing implementation or tests, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Delivered AS-IS
docs/architecture/README.md
docs/architecture/concurrency.md
docs/architecture/concurrency-matrix.md
docs/architecture/persistence.md
docs/architecture/relationship.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

# Active M2 authority
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Active execution aids
docs/milestones/M2/wip/M2-S00-codex-prompt.md
docs/milestones/M2/wip/M2-S00-review-fixes-codex-prompt.md
```

Inspect the actual branch delta from:

```text
b10e10a9d4cb2a71c8f1dcaf336bc379dceceb18
..
328fe179dade3a30168cb2e14dbbb5042a82e463
```

Confirm from the repository itself:

```text
checked-out branch       = M2
origin/M2                 = expected current published baseline or a direct descendant
M2 contract              = FINAL / FROZEN
M2 architecture set      = FINAL / FROZEN
M2 steps                 = FINAL / FROZEN
current authorized slice = M2-S00 only
current slice state      = IN PROGRESS
relevant reopen          = none
STACK-01 ... STACK-10    = RATIFIED
```

Also verify that the removed GitHub Actions/payload mechanism remains absent:

```text
.github/m2-s00-payload/
.github/workflows/materialize-verify-m2-s00.yml
.github/workflows/export-m2-worktree.yml
```

Do not restore, inspect or use encoded payloads or workflow artifacts as an implementation source.

The review findings below are currently classified as implementation/evidence defects, not architecture defects. If repository authority fails to determine one correction unambiguously, stop only the affected behavior and report the exact contradiction instead of choosing an interpretation.

---

# 2. Scope and expected outcome

Close all of the following before presenting `M2-S00` as a review candidate:

```text
A. race-safe post-collision classification for delivered REL.CREATE
B. complete removal of planner-induced global ObjectTemplate ancestry scans
C. explicit PLAN-01 ... PLAN-06 target mapping and mandatory PostgreSQL evidence
D. full S00 regression closure, including no supported 40P01
```

The review-fix must preserve all otherwise-correct work already present in commit `328fe179...`, including:

```text
central locking.py authority
three frozen advisory gates
four frozen row-lock modes
canonical class/row ordering
one explicit acquisition phase before DML
fresh protected reread
LockPlanStale whole-UoW restart
four-attempt shared budget
differential ObjectTemplate declaration DML
finite SQLSTATE + constraint registry
32 delivered mutation-path retrofit
current delivered public behavior
```

No schema, migration, dependency or `uv.lock` change is expected.

---

# 3. Finding A — make REL.CREATE collision classification lifetime-safe

## 3.1 Current defect

After an `ExactRelationshipViewCollision`, the failed candidate transaction rolls back and a fresh classification UoW reads current exact-view owner IDs.

The current implementation can perform this sequence:

```text
read current_id = R
R is deleted and committed by another transaction
load/validate R
R is now absent
-> internal_error
```

The existing winner-disappearance evidence pauses before the effective owner-ID read completes. It does not prove the narrower ABA window after an ID has been observed but before the current aggregate is lifetime-stabilized.

This violates the frozen distinction:

```text
owner still current
    -> validate current aggregate
    -> preserve the delivered S00 result

owner absent
    -> consume one whole-operation restart
    -> rederive the candidate from current state
```

Do not fix this by merely passing `restart_if_missing=True` to one later read. Several statements participate in aggregate validation, so a bare pre-read remains racy.

## 3.2 Required classification pipeline

After a candidate loses exact-view PK arbitration:

```text
1. leave the failed UoW
2. ensure complete rollback
3. open a fresh classification UoW
4. non-lockingly discover every current factual Relationship owner relevant
   to the collided exact-view keys
5. deduplicate owner UUIDs
6. build one complete LockPlan for those factual Relationship rows
7. acquire lifetime-stabilizing row locks in canonical UUID order
8. re-read the same exact-view owner set after lock acquisition
9. if the required owner set changed, disappeared or expanded:
       abort this classification attempt
       consume one approved whole-UoW restart
10. validate every still-current aggregate while its lifetime lock is held
11. classify the current result
12. perform no DML and write no event in the classification UoW
```

Use the central planner. Do not call a store `lock_*` helper directly and do not issue hand-written `SELECT ... FOR UPDATE` from the application service.

The expected sufficient mode for an immutable delivered factual Relationship lifetime observation is:

```text
Relationship header KS
```

It must block physical DELETE through the complete validation while remaining compatible with non-key activity where the frozen model permits it. Do not use a global Relationship gate or indiscriminate `U` locking as a shortcut.

When several current owner IDs are observed, lock all of them in the planner's canonical Relationship UUID order before classifying any one aggregate. Do not lock/read one owner, then discover and append another lock.

The failed transaction is never queried. Fresh classification is performed only after rollback.

## 3.3 Preserve the delivered S00 public result

This review-fix is still S00. Preserve the delivered M1 behavior that the original S00 prompt explicitly retained:

```text
same current semantic fact still exists
    -> convergent RelationshipCreateResult
    -> created = false
    -> no loser current-state mutation
    -> no loser lifecycle event

distinct current factual owner still conflicts
    -> preserve the existing bounded conflict outcome

owner disappeared before protected classification
    -> whole operation restarts
    -> a newly valid candidate may be created
```

Do not introduce the later `M2-S01` public loser delta in this review-fix.

## 3.4 Required permanent regressions

Add deterministic real-PostgreSQL coverage for at least:

### A1 — ID observed, winner disappears before owner lock

```text
T1 commits the winning fact
T2 loses exact-view arbitration and rolls back
T2 classification reads owner ID R
phase cut occurs after the ID observation but before the Relationship KS lock
T1/T3 deletes R and commits
T2 resumes
T2 fresh protected owner read sees the changed/absent owner set
T2 restarts the whole semantic operation
T2 may create a new fact under current state
```

Assert:

```text
new UoW / new backend transaction for the retry
no internal_error
no partial loser row/event survives
created relationship ID differs from the deleted winner
attempt budget remains bounded
```

### A2 — delete starts after classification owner lock

```text
classification holds Relationship KS on R
concurrent REL.DELETE(R) attempts U and blocks
classification validates and returns the delivered current-owner result
after classification transaction ends, DELETE progresses
```

Use `pg_blocking_pids()` to prove the actual blocker relation.

### A3 — owner set changes or expands

For a candidate with several collided exact-view keys, prove that a changed current owner set never causes fragmented lock acquisition or classification from a mixed snapshot. The operation must restart or return the current bounded conflict only after one complete protected owner set is established.

### A4 — exact current owner remains current

Retain and strengthen existing `ARB-05`/`ARB-07` behavior:

```text
one winner aggregate
one complete event set
loser converges without mutation/event
no 40P01
```

No `sleep()` ordering, generic flaky rerun, savepoint retry or failed-transaction query is allowed.

---

# 4. Finding B — remove all planner-induced global ObjectTemplate scans

## 4.1 Current defect

Generic application `_acquire()` helpers currently call a method equivalent to:

```python
await ObjectTemplateStore(...).lineage_parents()
```

which materializes:

```sql
SELECT id, parent_template_id
FROM object_templates
```

for every plan routed through those helpers, including plans containing no ObjectTemplate row at all.

This makes local mutations perform work proportional to the total number of ObjectTemplate lineages and adds avoidable database traffic to paths such as Object rename/data/delete/ownership and RelationshipDefinition delete.

The correction must be complete. Do not patch only one call site.

## 4.2 Central ancestry-preparation boundary

Audit every construction/acquisition path for `LockPlan` and every use of the complete ObjectTemplate parent map.

Create one reusable planner-preparation boundary, located in the persistence/locking area or an equivalently central seam, that:

```text
1. coalesces/inspects the requested intents
2. extracts the distinct planned ObjectTemplate lineage IDs
3. if that set is empty:
       executes zero ObjectTemplate ancestry query
4. if that set is non-empty:
       loads only those lineages and the stable ancestor closure needed
       for canonical ordering and validation
5. deduplicates shared ancestors
6. constructs the canonical plan
7. never materializes unrelated ObjectTemplate lineages
```

Application services may describe intents. They must not independently decide how to fetch the planner's ancestry metadata.

Remove planner-only calls that unconditionally inject the complete `lineage_parents()` map into `LockPlan`.

## 4.3 Query-shape and complexity requirements

For lock-plan preparation:

```text
no OT intents
    -> O(1) planner metadata work
    -> zero query against object_templates for ordering metadata

OT intents present
    -> work proportional to:
       planned OT lineages + their distinct stable ancestor closure
    -> independent of unrelated ObjectTemplate row count
```

Use either:

```text
one bounded recursive CTE rooted at the planned lineage IDs
```

or:

```text
batched-by-depth indexed lookups
```

Do not introduce a per-node N+1 query pattern.

Do not add a process-global ancestry cache, background cache, cross-transaction mutable singleton or stale in-memory graph authority. Per-plan/per-UoW materialization is sufficient.

## 4.4 Missing and corrupt ancestry semantics

Preserve the frozen distinction:

```text
planned lineage itself absent
    -> keep a deterministic acquisition position
    -> report the planned row as missing
    -> application maps path/body absence correctly

existing lineage points to missing parent
existing ancestry contains a cycle
persisted stable graph is otherwise corrupt
    -> abort before DML as an internal/invariant failure
```

Do not reinterpret a missing planned body operand as database corruption. Do not silently treat a corrupt existing parent chain as a root.

The ordering rules remain exactly:

```text
ancestor before descendant
unrelated-lineage UUID ascending
header before versions
versions ascending
```

## 4.5 Required call-site closure

At minimum audit and correct planner metadata behavior for:

```text
DataTypeService
ObjectTemplateService
ObjectService
RelationshipDefinitionService
RelationshipService
whole-UoW collision classification helpers
any test-only planner wrapper that mirrors production behavior
```

Expected examples:

```text
DT.*
OBJ.RN
OBJ.DC
OBJ.A
OBJ.DET
OBJ.DEL
RD.DL
REL.C / REL.DEL
post-collision factual-owner classification
    -> no ObjectTemplate planner ancestry query

OBJ.C
OBJ.SC
OT operations with planned OT rows
RD.C endpoint lifetime plan
    -> targeted ancestry closure only
```

RelationshipDefinition certification and Relationship semantic validation may legitimately require a complete current ancestry graph for their domain predicates. Preserve those owning semantic reads. The review finding concerns the **additional planner-ordering full scan**.

For example, an RD.RENAME certification path may still perform its required semantic certified-set/ancestry read, but it must not perform a second full-table scan merely to order a plan containing only an RD header.

## 4.6 Required regression evidence

Add stable evidence proving all of the following.

### B1 — no ancestry loader invocation without OT intents

Use a spy/failing planner ancestry provider and prove that plans containing only:

```text
DT
RD
Object
Relationship
```

never invoke it.

### B2 — targeted closure excludes unrelated lineages

On real PostgreSQL, create:

```text
planned descendant
its ancestor chain
many unrelated ObjectTemplate lineages
```

Build/acquire the planned OT lock plan and assert that the planner ancestry material contains exactly the planned lineages plus required ancestors, never unrelated rows.

Do not use timing thresholds as the proof.

### B3 — shared ancestors are deduplicated

Plan two descendants sharing one ancestor and prove the ancestor is loaded/represented once and ordering remains deterministic across input permutations.

### B4 — no N+1

Instrument statement execution or the ancestry loader and prove the number of ancestry queries is bounded by the chosen query strategy, not by the number of nodes.

### B5 — missing target and corrupt ancestry

Cover:

```text
missing planned OT header -> returned in missing planned keys
existing child with missing parent -> internal/invariant failure
cycle -> internal/invariant failure
```

### B6 — representative mutation query closure

Instrument the dedicated planner ancestry seam, rather than merely counting every semantic query in the service, and prove representative paths:

```text
OBJ.RN / OBJ.DC / OBJ.DEL / OBJ.A / OBJ.DET
RD.DL
REL.C / REL.DEL
```

perform no planner ancestry load.

For a path such as RD.RN that has a legitimate semantic full-graph certification read, prove there is no additional planner read.

### B7 — static anti-regression

Add a bounded static/source-structure check that prevents generic application `_acquire()` helpers from restoring unconditional complete `lineage_parents()` injection.

Do not make this static check the only evidence; retain unit and real-PostgreSQL behavior tests.

---

# 5. Finding C — complete PLAN-01 ... PLAN-06 evidence ownership

## 5.1 Explicit target registry

Extend the machine-checkable S00 traceability so each stable planner scenario owns concrete targets:

```text
PLAN-01
PLAN-02
PLAN-03
PLAN-04
PLAN-05
PLAN-06
```

The registry must identify:

```text
pure/static target(s)
real-PostgreSQL target(s), where required
concurrency target(s), where required
```

Every target name must resolve to a real collected test. Do not satisfy traceability only by searching service source for `_acquire(` or `begin_dml()`.

The existing 32-mutation inventory remains useful, but it is not a substitute for exact PLAN evidence.

## 5.2 PLAN-01 — SQL compilation and execution

Retain static PostgreSQL-dialect compilation for exact:

```text
KS  -> FOR KEY SHARE
S   -> FOR SHARE
NKU -> FOR NO KEY UPDATE
U   -> FOR UPDATE
```

Also execute representative statements against real PostgreSQL and preserve:

```text
one table only
OF target
explicit ORDER BY
no accidental join lock
no NOWAIT
no SKIP LOCKED
missing-key reporting
```

## 5.3 PLAN-02 — coalescence and canonical sorting

Strengthen pure/property evidence so arbitrary input permutations produce one identical plan and prove:

```text
strongest sufficient mode wins
class order
OT ancestor order
UUID tie-breaks
header before version
version ascending
shared-ancestor handling
```

Targeted ancestry loading from Finding B becomes part of PLAN-02 evidence.

## 5.4 PLAN-03 — real whole-UoW stale-plan restart

Provide at least one real application-level PostgreSQL scenario in which optimistic discovery becomes stale before the protected reread, causing:

```text
LockPlanStale
complete rollback of the attempt
new UoW
new PostgreSQL transaction/backend identity
fresh candidate derivation
no partial current-state or lifecycle write
```

A fake UoW-only test remains useful but does not satisfy the T2/T3 part.

## 5.5 PLAN-04 — finite failure classification

Retain the finite synthetic SQLSTATE/constraint census and add real PostgreSQL evidence for representative known:

```text
23505 UNIQUE authority
23503 FK authority
```

Prove:

```text
known constraint -> bounded internal class
unknown/mismatched constraint -> internal error
failed transaction is exited/rolled back before fresh-state classification
no SQLSTATE/constraint/table/SQL leaks publicly
```

The corrected `REL.CREATE` collision pipeline is part of the after-rollback classification evidence.

## 5.6 PLAN-05 — budget and forbidden retries

Retain exact four-attempt pure evidence and prove through real scenarios:

```text
owner-current and owner-disappeared paths are distinct
approved restart consumes the shared budget
new attempt uses a fresh UoW
semantic failure is not retried
40P01 is never automatically retried
40001 is never automatically retried
```

Do not manufacture a supported-path deadlock and then hide it. A supported deterministic scenario returning `40P01` is a blocking defect.

Policy-level injected error evidence may prove the no-retry branch; the complete PostgreSQL concurrency suite must prove supported paths do not produce `40P01`.

## 5.7 PLAN-06 — real gate/row/DML discipline

Add or identify real PostgreSQL evidence proving:

```text
at most one gate
gate acquired before every row lock
gate waiter owns no NETAUTO row lock
waiter acquires gate after release
fresh protected read occurs after gate acquisition
no normal lock upgrade
no explicit lock after DML begins
no row -> gate edge
```

Use independent sessions, `pg_blocking_pids()` and, where needed, bounded `pg_locks` diagnostics. PostgreSQL relation/table locks incidental to statements are not the semantic row-lock ownership being prohibited; assert the intended NETAUTO row/gate property precisely.

---

# 6. Preserve all other S00 behavior

Do not change or weaken:

```text
READ COMMITTED mutation baseline
REPEATABLE READ READ ONLY coherent reads
one mutation / one UoW
no nested semantic transaction
no store commit
three-gate registry and stable keys
gate-first discipline
canonical row-class ordering
exact lock-mode mapping
root-delete serialization
ownership real-edge-only gate rule
Definition CREATE/RENAME gate rule
fresh protected reread
differential ObjectTemplate replacement
current delivered public route/error catalog
bounded failure details and non-leakage
lifecycle atomicity
M1 exact-fact convergence semantics retained for S00
```

Do not remove or weaken existing deterministic AS-IS scenarios merely because a new lock causes them to block at a different phase. Re-anchor phase cuts to the frozen mechanism and continue to prove both required blocking and required progress.

Do not increase global timeouts, add sleeps, add generic retries, mark normative tests xfail/skip, or deselect failing PostgreSQL tests.

---

# 7. Layer and scope discipline

Do not introduce:

```text
M2-S01 RelationshipDefinitionVersion capability
Relationship properties
Relationship DATA_CHANGE / SCHEMA_CHANGE
new API routes or wire changes
new schema/table/column/index/constraint
new Alembic revision
new dependency
new advisory gate
global Relationship gate
global ObjectTemplate graph cache
SERIALIZABLE baseline
SQLAlchemy ORM Session / AsyncSession
Docker or Testcontainers
GitHub Actions
background jobs
```

Domain modules remain plain Python and free of SQLAlchemy/Psycopg/FastAPI/Pydantic imports.

Application services describe semantic intents and map bounded results. Persistence owns SQL, planner preparation, lock acquisition and PostgreSQL classification.

Any local suppression must be narrow and justified in the handoff. No global Ruff/Pyright relaxation.

---

# 8. Verification gate

A valid externally supplied real PostgreSQL target is mandatory before this review-fix may become `CANDIDATE READY FOR REVIEW`.

Use only:

```text
TEST_DATABASE_URL
```

Do not provision a database, use Docker/Testcontainers, invent credentials, use SQLite, fall back to `NETAUTO_DATABASE_URL` or fall back to localhost.

Run focused checks first, then the complete gate. Report exact commands, counts and failures.

At minimum run the repository's concrete equivalents of:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright

# focused pure/static review-fix evidence
uv run pytest -q tests/test_m2_locking.py tests/test_m2_s00_traceability.py

# focused real-PG PLAN and REL.CREATE collision evidence
uv run pytest -q <all PLAN-01..PLAN-06 PostgreSQL targets>
uv run pytest -q <all A1..A4 collision-classification targets>
uv run pytest -q <all targeted-ancestry PostgreSQL targets>

# affected deterministic concurrency regressions
uv run pytest -q -m "postgresql and concurrency" <affected modules/targets>

# all non-PG regressions
uv run pytest -q -m "not postgresql"

# full repository suite, including PostgreSQL-marked tests
uv run pytest -q
```

Report:

```text
CPython version
PostgreSQL server version
exact selected/full pass counts
durations where available
all PLAN-01 ... PLAN-06 states
whether any supported path returned SQLSTATE 40P01
whether any test was skipped, xfailed or rerun
```

No normative requirement is `PASS` merely because the test collected.

If `TEST_DATABASE_URL` is still unavailable:

```text
implement and run only what can be verified honestly
keep M2-S00 IN PROGRESS
record the exact remaining blocker
push only an explicitly partial corrective candidate
never claim ready for review
```

---

# 9. Documentation and status discipline

Do not modify the frozen M2 contract, architecture or `steps.md` to fit the code.

Do not rewrite delivered AS-IS documentation for an unreviewed candidate.

Keep both active S00 execution aids in `wip/` until the reviewer accepts or explicitly supersedes them. Do not delete this review-fix prompt in the corrective candidate.

Update `docs/milestones/M2/status.md` only with verified operational facts:

```text
corrections or mandatory PG verification incomplete
    -> M2-S00 IN PROGRESS
    -> record exact open implementation/evidence finding or infrastructure blocker

all review-fix implementation and mandatory verification pass
and candidate is committed/pushed
    -> M2-S00 CANDIDATE READY FOR REVIEW
    -> reviewer decision pending
```

Never mark:

```text
M2-S00 COMPLETED
M2 DELIVERED
review ACCEPTED
```

Do not open `M2-S01`.

---

# 10. Git and publication discipline

Before committing:

```text
review the complete diff from 328fe179...
exclude unrelated changes
verify no secret or database URL is present
verify no Actions/payload material was restored
verify both active prompts remain present
run git diff --check
```

Use one or more intentional commits with clear review-fix scope. A suitable primary title is:

```text
fix(m2-s00): make collision classification race-safe
```

A separate coherent performance/evidence commit is acceptable, for example:

```text
perf(m2-s00): bound ObjectTemplate ancestry planning

test(m2-s00): complete real PostgreSQL PLAN evidence
```

Push normally to:

```text
origin/M2
```

After push verify:

```text
local HEAD SHA
origin/M2 SHA
local/remote synchronization
working tree clean
```

Do not create a PR, merge, force-push, tag or release.

---

# Completion report

At the end provide a reviewer-oriented handoff containing only verified facts:

- cycle `M2`, slice `M2-S00`, branch `M2`;
- corrective commit SHA(s);
- local/remote synchronization and working-tree state;
- concise changed-file inventory;
- exact race-safe `REL.CREATE` classification pipeline implemented;
- exact A1 ... A4 results;
- exact planner ancestry preparation mechanism;
- proof that no-OT plans perform zero planner ancestry query;
- proof that OT plans load only planned lineages plus ancestor closure;
- query-count/query-shape evidence showing no full scan and no N+1;
- missing/corrupt ancestry behavior evidence;
- explicit `PLAN-01 ... PLAN-06` target registry and result for each ID;
- exact static/build/test commands and counts;
- PostgreSQL server version;
- full-suite result;
- explicit statement whether any supported path returned `40P01`;
- skipped/xfail/rerun census;
- schema/migration changes: expected `none`;
- dependency/lockfile changes: expected `none`;
- confirmation that Actions/payload material remains absent;
- every unexecuted mandatory requirement and exact reason;
- every residual risk or architecture/documentation finding;
- confirmation that no `M2-S01` capability was introduced;
- final `status.md` state without claiming reviewer-owned completion.

Use:

```text
M2-S00 corrective candidate implemented and ready for reviewer inspection
```

only if every mandatory S00 and review-fix gate has actually passed against real PostgreSQL and the candidate has been pushed.