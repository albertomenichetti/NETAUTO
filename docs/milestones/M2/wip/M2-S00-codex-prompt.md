# Codex implementation prompt — M2-S00

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the current delivered AS-IS, the FINAL/FROZEN M2 contract, architecture or steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M2-S00 — LockPlan and AS-IS transaction-hardening foundation
```

from `docs/milestones/M2/steps.md`.

This is the only authorized implementation slice. Do not start `M2-S01` and do not expose any new M2 business capability.

Work directly on branch:

```text
M2
```

The required publication action is:

```text
implement the candidate
run all mandatory verification
commit the candidate intentionally
push the candidate to origin/M2
leave it ready for reviewer inspection
```

Do not create a pull request. Do not merge to `master`. Do not force-push or rewrite published history.

## Mandatory pre-flight

Before changing implementation files, read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Current delivered AS-IS
docs/architecture/README.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
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
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md
```

Read owning sections dependency-first rather than relying on summaries in this prompt.

Confirm from the repository itself that:

```text
checked-out branch       = M2
README active cycle      = M2 / IMPLEMENTATION / branch M2
M2 contract              = FINAL / FROZEN
M2 architecture set      = FINAL / FROZEN
M2 steps                 = FINAL / FROZEN
current authorized slice = M2-S00 only
M2-S00 dependency        = none
relevant reopen          = none
STACK-01 ... STACK-10    = RATIFIED
```

Also inspect the current working tree and remote relationship before modifying anything.

If README, branch, `status.md` or frozen authorities disagree, stop and report the mismatch. If two normative authorities conflict or fail to determine one behavior, stop the affected work and report an architecture/documentation finding. Do not choose the newest, easiest or currently implemented interpretation.

Code, tests, Git history and this prompt are evidence or execution aids, not semantic authority.

## Repository hygiene and prohibited execution path

The repository must contain no M2-S00 implementation mechanism based on GitHub Actions, encoded patches or workflow artifacts.

Verify that the following obsolete material is absent before implementation begins:

```text
.github/m2-s00-payload/
.github/workflows/materialize-verify-m2-s00.yml
.github/workflows/export-m2-worktree.yml
```

Do not restore, decode, inspect as an implementation template or otherwise use any removed base64 payload, failed-candidate artifact or Actions-generated worktree.

Do not add or use:

```text
GitHub Actions workflows
workflow_dispatch jobs
CI-driven commits
artifact-mediated source publication
encoded patch transport
```

Implementation and verification happen directly in the Codex checkout using the repository toolchain and an externally supplied PostgreSQL test target.

## Objective

Introduce the centralized PostgreSQL transaction lock-planning boundary required by the frozen M2 concurrency design and retrofit every delivered M1 mutation path to that physical discipline while preserving the delivered public behavior.

At S00 exit:

```text
one centralized complete LockPlan boundary exists
+
all delivered 32 mutation paths use it or are explicitly proven compatible
+
gate-first and globally ordered row acquisition are enforced
+
all protected state is freshly re-read after waits
+
all current-state DML occurs only after the complete plan is acquired
+
whole-UoW restart is bounded to the two approved internal causes
+
PLAN-01 ... PLAN-06 and affected AS-IS regressions pass
+
no supported scenario produces SQLSTATE 40P01
```

S00 is an internal transaction/concurrency foundation. It introduces no new domain operation, route, DTO, schema capability or operator surface.

## Hard scope boundary

S00 MUST NOT implement or expose:

```text
RelationshipDefinitionVersion domain/application/API behavior
relationship_definition_versions table
relationship_definition_properties table
Relationship properties or exact RDV pin columns
Relationship DATA_CHANGE
Relationship SCHEMA_CHANGE
new RelationshipDefinition version/default/lifecycle routes
M2 duplicate Relationship CREATE public conflict behavior
M2 missing Relationship DELETE 404 behavior
new M2 schema or Alembic baseline
Core Health API
runtime/startup revision guard changes
NETAUTO CLI
wheel/runtime-deployment work
new authentication, TLS, observability or logging capability
M2-S01 or later traceability targets except support strictly required by S00
```

Preserve the delivered M1 HTTP behavior throughout this slice. In particular, do not prematurely switch factual Relationship duplicate-create or missing-delete public outcomes to their M2 forms; those observable deltas belong to `M2-S01`.

No new table, column, index, constraint, migration or dependency is expected. If implementation appears to require one, stop and verify the frozen scope rather than adding it opportunistically.

Do not broaden the task into a general application/persistence rewrite. Prefer the smallest complete implementation that satisfies the frozen S00 obligations.

---

# 1. Central lock-planner boundary

Create one authoritative persistence boundary, conceptually:

```text
src/netauto/persistence/locking.py
```

It owns the concrete equivalents of:

```text
AdvisoryGate
RowLockMode
RowLockClass
RowLockKey
RowLockIntent
LockPlan
LockPlanStale
acquire_lock_plan
classify_postgresql_failure
MAX_SEMANTIC_UOW_ATTEMPTS
```

The current `src/netauto/persistence/gates.py` may be removed, subsumed or retained only as a thin delegating compatibility seam. Advisory keys and acquisition behavior must have exactly one implementation authority.

Application services describe semantic intents. Persistence stores provide exact one-table row-lock statements and protected reloads. No service or store may maintain a second hand-coded acquisition order.

Local type/module decomposition is implementation freedom, but it must preserve the frozen conceptual boundary and remain directly testable.

## 1.1 Advisory gates

Realize exactly these transaction-scoped PostgreSQL advisory gates and stable signed-BIGINT keys:

```text
OWNERSHIP_GRAPH_WRITE_GATE
    0x4E45544100000001

RELATIONSHIP_DEFINITION_CONFLICT_GATE
    0x4E45544100000002

MODEL_ROOT_DELETE_GATE
    0x4E45544100000003
```

Acquire with the concrete equivalent of:

```sql
SELECT pg_advisory_xact_lock(:stable_key)
```

Mandatory discipline:

```text
at most one gate per semantic UoW
gate before every explicit row lock
gate waiter owns no NETAUTO row lock
fresh protected read after gate acquisition
transaction-level only
no manual unlock
no try-lock / NOWAIT / SKIP behavior
```

Gate ownership is exact:

```text
OWNERSHIP_GRAPH_WRITE_GATE
    -> real OBJ.ATTACH edge-add candidates only

RELATIONSHIP_DEFINITION_CONFLICT_GATE
    -> RD.CREATE
    -> RD.RENAME

MODEL_ROOT_DELETE_GATE
    -> DT.DELETE_LINEAGE
    -> OT.DELETE_LINEAGE
    -> RD.DELETE_DEFINITION
```

`OBJ.DETACH` does not use the ownership gate. An idempotent/convergent `ATTACH` path that is not a real edge-add candidate must not take the ownership gate. Definition delete uses only the model-root gate, never the Definition conflict gate.

The model-root gate may physically serialize unrelated root deletes but must not introduce a new public busy/conflict outcome.

## 1.2 Row-lock modes

Realize all four modes and their exact SQLAlchemy Core compilation:

| Architecture mode | PostgreSQL SQL | SQLAlchemy `with_for_update` |
|---|---|---|
| `KS` | `FOR KEY SHARE` | `read=True, key_share=True` |
| `S` | `FOR SHARE` | `read=True` |
| `NKU` | `FOR NO KEY UPDATE` | `key_share=True` |
| `U` | `FOR UPDATE` | no flags |

The counter-intuitive `key_share=True -> FOR NO KEY UPDATE` mapping must have a static SQL compilation regression.

Each lock statement must:

```text
select from exactly one table
select only primary/exact key columns
use OF <target table> where supported
use explicit ORDER BY matching canonical key order
contain no join that can lock another table
contain no NOWAIT
contain no SKIP LOCKED
return exactly the planned key set
```

A missing planned row is handled before DML with the owning semantic not-found/referenced-not-found rule.

## 1.3 Intent coalescence

Coalesce all intents for one semantic row before acquisition. Acquire one sufficient initial mode using:

```text
U > NKU > S > KS
```

This is the NETAUTO sufficient-mode planning precedence. Do not implement normal row-lock upgrades.

A row required for several reasons appears once in the final plan with the strongest required initial mode.

## 1.4 Canonical row identities and class order

Support these semantic row identities, even where S00 currently exercises only the delivered subset:

```text
ObjectTemplate header
ObjectTemplateVersion exact row
DataType header
DataTypeVersion exact row
RelationshipDefinition header
RelationshipDefinitionVersion exact row
Object row
factual Relationship row
```

Do not treat declaration, Resolution, ownership-edge, runtime-closure or lifecycle rows as independent semantic lock owners.

Global class order is exact:

```text
10  ObjectTemplate headers and exact versions
20  DataType headers and exact versions
30  RelationshipDefinition headers and exact versions
40  Object rows
50  factual Relationship rows
```

No supported path may acquire a lower class after a higher class.

Intra-class ordering:

```text
ObjectTemplate
    validate stable parent graph
    ancestor before descendant
    unrelated lineage UUID ascending
    within lineage: header first, then versions ascending

DataType / RelationshipDefinition
    lineage/Definition UUID ascending
    header first
    exact versions ascending

Object / factual Relationship
    UUID ascending
```

Component-target lineages do not create topological edges; they use deterministic lineage ordering.

## 1.5 Target-before-owner and target-before-DML rules

For a direct FK rebound on an already-existing mutable owner, lock the target before the owner. In S00 this includes at least:

```text
ObjectTemplateVersion parent rebind
Object SCHEMA_CHANGE target OTV -> Object owner
```

Do not add the later Relationship SCHEMA_CHANGE operation in this slice.

For child-table insert/reinsert, every expected FK target must be stabilized before child DML. The semantic owner may precede the target in global class order only where the frozen child-table proof explicitly allows it; all target locks must still be complete before the first child write.

---

# 2. Complete planning and protected re-read

Every delivered mutation must follow the concrete equivalent of:

```text
1. begin a READ COMMITTED UoW
2. perform non-locking discovery only
3. construct the complete gate + row plan
4. coalesce intents
5. acquire the optional gate
6. acquire every row in canonical order
7. verify every planned row was acquired
8. issue fresh protected reads after acquisition
9. rederive and revalidate the complete candidate
10. if a new lock identity is required:
        raise LockPlanStale
        rollback the whole UoW
        restart from a fresh UoW
11. perform deterministic current-state DML
12. append the complete lifecycle event set
13. commit
```

No current-state DML may occur before step 11.

After current-state DML begins:

```text
no new gate
no explicit row lock
no row-lock upgrade
no lock-plan expansion
no change to the planned dependency set
```

Implement an enforceable and testable phase boundary. The exact local mechanism is free, but `PLAN-03` and `PLAN-06` must prove that post-DML lock append/gate acquisition is rejected rather than merely discouraged by convention.

After any wait, reload every mutable protected predicate in a new statement. Do not write a candidate derived only from an optimistic pre-lock snapshot.

A changed dependency set never appends a late lock even when the new row would sort after all previously acquired rows. It restarts the whole UoW.

---

# 3. Exact binding and declaration rules used by S00

Use the frozen common binding rules for delivered ObjectTemplate/Object paths.

## 3.1 Explicit new exact binding

```text
stable target header KS
exact target version S
fresh exact-membership + PUBLISHED recheck
persist exact pin
```

## 3.2 Implicit default binding

```text
stable target header S
fresh default_version read
exact target version S
fresh default identity + PUBLISHED recheck
persist exact pin
```

If the fresh default identifies an unplanned different target, restart the whole UoW. If the default is null, preserve the existing owning semantic outcome.

## 3.3 Historical CREATE_NEXT clone lifetime

When `OT.CREATE_NEXT` copies existing exact references and creates new physical FK rows:

```text
stable target header KS
exact target version KS
```

PUBLISHED status is not required for a historical clone, but lifetime through insertion is required.

## 3.4 Differential declaration targets

For inserted or reinserted ObjectTemplate declarations:

```text
new/rebound exact dependency
    -> target S

same exact dependency reinserted because another field changed
    -> target KS

unchanged physical row
    -> no child DML and no outgoing target lock

removed row
    -> no outgoing target lock
```

---

# 4. Retrofit the delivered 32 mutation paths

Audit every delivered application mutation and make its plan explicit. The checklist below is an execution aid; the frozen concurrency owners remain authoritative.

## 4.1 DataType — 10

| Mutation | Gate | Required explicit plan |
|---|---|---|
| `DT.C` | none | no row plan; qualified-name UNIQUE remains final arbitration |
| `DT.CN` | none | own `DT.H NKU`; exact source `DT.V KS` |
| `DT.R` | none | own `DT.H KS`; exact DRAFT `DT.V NKU` |
| `DT.P` | none | own `DT.H NKU`; exact DRAFT `DT.V NKU` |
| `DT.SD` | none | own `DT.H NKU`; target `DT.V S` |
| `DT.CD` | none | own `DT.H NKU` |
| `DT.D` | none | own `DT.H S`; target `DT.V NKU`; reverse active-consumer scan remains non-locking |
| `DT.DD` | none | own `DT.H NKU`; exact DRAFT `DT.V U` |
| `DT.DL` | `MODEL_ROOT_DELETE_GATE` | root `DT.H U` |
| `DT.DESC` | none | own `DT.H NKU` |

## 4.2 ObjectTemplate — 10

| Mutation | Gate | Required explicit plan |
|---|---|---|
| `OT.C` | none | parent/component target OT headers `KS`; explicit parent exact OTV `S` or implicit parent header `S` + exact `S`; DTV targets per common binding rules |
| `OT.CN` | none | cloned parent/component/DTV targets `KS`; own `OT.H NKU`; exact source OTV `KS` |
| `OT.R` | none | candidate parent/component/DTV targets per differential rules; own `OT.H KS`; exact DRAFT `OT.V NKU` |
| `OT.P` | none | parent/DTV headers `KS` and exact versions `S`; own `OT.H NKU`; exact DRAFT `OT.V NKU` |
| `OT.SD` | none | own `OT.H NKU`; target `OT.V S` |
| `OT.CD` | none | own `OT.H NKU` |
| `OT.D` | none | own `OT.H S`; target `OT.V NKU`; active-child scan remains non-locking |
| `OT.DD` | none | own `OT.H NKU`; exact DRAFT `OT.V U` |
| `OT.DL` | `MODEL_ROOT_DELETE_GATE` | root `OT.H U` |
| `OT.DESC` | none | own `OT.H NKU` |

Additional required behavior:

```text
parent OTV target ancestor-orders before the current owner
component targets are stable-header lifetime locks
OT.REVISE performs differential physical replacement
unchanged direct parent FK requires no target reacquisition
changed parent binding requires exact target S
OT.PUBLISH re-certifies complete member history after header NKU
```

## 4.3 Object and ownership — 7

| Mutation | Gate | Required explicit plan |
|---|---|---|
| `OBJ.C` | none | selected OTV header/exact target using explicit or implicit binding rules |
| `OBJ.RN` | none | Object `NKU` |
| `OBJ.DC` | none | Object `NKU` |
| `OBJ.SC` | none | target OTV header `KS`, target exact OTV `S`, then Object `NKU` |
| `OBJ.A` | `OWNERSHIP_GRAPH_WRITE_GATE` for a real edge-add candidate only | parent Object `NKU`; child Object `KS`; coalesced and UUID ordered |
| `OBJ.DET` | none | parent Object `NKU`; pure reference removal takes no child target lock |
| `OBJ.DEL` | none | Object `U` |

After gate and Object locks, `OBJ.A` performs a fresh current-edge and graph-reachability read before insertion.

## 4.4 Delivered RelationshipDefinition — 3

| Mutation | Gate | Required explicit plan in S00 |
|---|---|---|
| `RD.C` | `RELATIONSHIP_DEFINITION_CONFLICT_GATE` | endpoint ObjectTemplate headers `KS`; no RDV/property target exists yet in S00 |
| `RD.RN` | `RELATIONSHIP_DEFINITION_CONFLICT_GATE` | Definition header `KS` after the gate |
| `RD.DL` | `MODEL_ROOT_DELETE_GATE` | root Definition header `U` |

`RD.RN` must be gate-first. The header `KS` is intentionally compatible with non-key exact-version/default work introduced later; do not strengthen it merely to reproduce the old implementation order.

## 4.5 Delivered factual Relationship — 2

| Mutation | Gate | Required explicit plan in S00 |
|---|---|---|
| `REL.C` | none | stable Definition lifetime `KS` as applicable to the current aggregate; endpoint Objects `KS` in UUID order before runtime-closure writes; no RDV target exists yet |
| `REL.DEL` | none | factual Relationship `U` |

Preserve the current delivered factual topology, Resolution identity, exact-view closure and M1 observable outcomes. Resolution rows are not independent semantic lock owners.

## 4.6 Compatibility proof

Create a machine-checkable or otherwise explicit test-side inventory proving that all 32 delivered mutations are either:

```text
planned through the central boundary
or
intentionally row-plan-free with a documented frozen final authority
```

No delivered write path may silently retain legacy ad hoc row/gate ordering.

---

# 5. Mandatory transaction hardening

Implement all S00 hardening called out by frozen `steps.md` and the M2 concurrency architecture:

```text
stable header participation in every delivered exact-version mutation
target-before-existing-owner direct FK rebind
target-before-child DML for inserted/reinserted references
differential ObjectTemplate declaration replacement
CREATE_NEXT cloned-reference lifetime holds
MODEL_ROOT_DELETE_GATE serialization for DT/OT/RD roots
Relationship endpoint Object lifetime holds before closure insertion
Definition RENAME gate-first + header KS
ownership edge addition gate-first for real candidates only
deterministic declaration / closure / lifecycle-event ordering
non-locking reverse active-consumer scans
fresh protected reread after every wait
one complete UoW commit or rollback
```

Do not add generic locks or serialize unrelated operations beyond the frozen gate/row plan.

Preserve required progress, including at least:

```text
REL.CREATE × endpoint OBJ.RENAME
REL.CREATE × RD.RENAME
RD.RENAME × compatible Definition/version activity
independent exact-version mutations using compatible header modes
unrelated Relationship CREATE operations
```

A test failure showing unexpected prohibited blocking is as material as a missing required blocker.

---

# 6. Differential ObjectTemplate declaration DML

`OT.REVISE` remains a complete semantic replacement but physical child DML is differential.

Classify rows as:

```text
unchanged
removed
replaced
new
```

Mandatory realization:

1. unchanged rows are not updated or deleted;
2. removed/replaced rows are deleted in physical primary-key order;
3. all replacement deletes complete before any replacement insert;
4. replacement/new rows are inserted in physical primary-key order;
5. all exact target locks are already held;
6. owner revision increments only after all child DML succeeds;
7. any failure rolls back the owner revision and complete child generation.

ObjectTemplate physical order is:

```text
properties first
    (template_id, template_version, name)

components second
    (template_id, template_version, name)
```

Blind `DELETE all + INSERT all` is forbidden.

Position swaps must remain valid because all replaced rows are removed before reinsertion.

Preserve or adapt the existing atomicity regression so it injects failure at a real differential child-DML seam and proves complete rollback. Do not remove or weaken the rollback assertion merely because an old bulk-insert hook no longer exists.

---

# 7. Whole-UoW restart policy

Provide one bounded semantic-UoW attempt runner used by affected application operations.

Shared budget:

```text
MAX_SEMANTIC_UOW_ATTEMPTS = 4
```

One initial attempt plus at most three complete restarts.

Automatic restart is permitted only for:

```text
LOCK_PLAN_STALE
    optimistic discovery no longer describes the complete lock set

EXACT_VIEW_COLLISION with disappeared current owner
    the failed Relationship CREATE attempt rolled back completely,
    a fresh classification UoW found no current owner,
    and a new candidate must be derived from current state
```

Rules:

```text
each attempt owns a new connection/transaction/UoW
failed transaction is rolled back before classification
no savepoint retry
no store-fragment retry
no retry after a semantic/public failure
no retry for 40P01
no retry for 40001
no sleep-based scheduling/backoff
```

When the exact-view owner is still current, preserve the delivered M1 convergence/public behavior in S00. The later M2 `relationship_fact_conflict` public mapping belongs to S01. Keep internal collision classification separate from the current public outcome so S01 can apply its frozen delta without reintroducing transaction ambiguity.

After four unsuccessful approved attempts, return the existing bounded internal failure; do not expose attempt counts, SQLSTATE or locking details publicly.

---

# 8. Finite PostgreSQL failure classification

Centralize a finite classifier using SQLSTATE plus explicit known constraint identity where required.

Required policy:

```text
23505 unique_violation
    -> classify only through the finite known constraint registry

23503 foreign_key_violation
    -> classify known target/reference/root-delete authority

23514 check_violation
23502 not_null_violation
    -> internal error when discovered by persistence

40P01 deadlock_detected
    -> no retry
    -> internal error
    -> blocking implementation finding

40001 serialization_failure
    -> no retry
    -> internal error

55P03 lock_not_available
57014 query_canceled
    -> operational/internal failure
    -> no semantic remapping
```

Unknown or mismatched constraint names are internal errors, never a generic conflict escape hatch.

A failed transaction is never queried. Capture only bounded internal classification material, leave/rollback the UoW, then map or open a fresh UoW.

No SQLSTATE, constraint, SQL, table, column, driver object, stack trace or connection detail may reach the public API.

Preserve the delivered public failure catalog except for no change at all in this slice.

---

# 9. Deterministic current-state DML and lifecycle ordering

After plan acquisition and fresh revalidation:

```text
current-state rows are written in deterministic conflict-key order
one coherent metadata statement is used where already required
complete lifecycle event set is derived deterministically
lifecycle rows are inserted last in one batch where the current design requires it
commit is all-or-nothing
```

For delivered Relationship CREATE, write runtime-closure rows in exact key order:

```text
(resolution_id, from_object_id, to_object_id)
```

Retain sequential exact-key inserts for the bounded closure unless the frozen verification proves an equivalent unique-index probe order.

Relationship semantic event views remain deterministically ordered by the current owning architecture.

Do not introduce live FKs from lifecycle history back to current rows.

---

# 10. Required PLAN evidence

Implement stable evidence for every new planner scenario.

## PLAN-01 — lock SQL compilation

Prove on the PostgreSQL dialect:

```text
exact KS/S/NKU/U SQLAlchemy mapping
one-table SELECT
OF target where supported
explicit canonical ORDER BY
no join side locking
no NOWAIT
no SKIP LOCKED
```

## PLAN-02 — coalescence and canonical sorting

Use deterministic and property-based evidence where useful to prove:

```text
strongest-mode coalescence
class ordering
OT ancestor-before-descendant ordering
unrelated UUID tie-breaks
header-before-version ordering
version ascending ordering
Object/Relationship UUID ordering
same logical input set -> same final plan
```

## PLAN-03 — complete restart on stale plan

Prove:

```text
changed dependency set raises LockPlanStale
current attempt rolls back completely
next attempt uses a new UoW/connection transaction
candidate is freshly rederived
no post-DML lock append
no partial child/event write survives
```

## PLAN-04 — finite failure classifier

Prove:

```text
known SQLSTATE + known constraint maps to the intended bounded internal class
classification happens only after rollback when fresh state is needed
unknown constraint becomes internal error
public mapping leaks no persistence internals
```

## PLAN-05 — attempt budget and no forbidden retry

Prove exactly four total attempts and distinct owner-current/owner-disappeared exact-view paths.

Prove no retry after:

```text
semantic failure
40P01
40001
unapproved SQLSTATE
```

## PLAN-06 — gate/row/DML phase discipline

Prove:

```text
at most one gate
gate acquired before rows
gate waiter owns no NETAUTO row lock
no normal row-lock upgrade
no explicit row lock after current-state DML
no gate after row/DML
no supported row -> gate edge
```

Use real PostgreSQL for T2/T3 claims and inspect `pg_blocking_pids()` where blocking is part of the assertion.

---

# 11. AS-IS concurrency and regression closure

Run and preserve every delivered regression affected by the 32-path retrofit, especially:

```text
ownership gate scenarios
RelationshipDefinition conflict-gate scenarios
root/reference lifetime scenarios
Relationship CREATE versus Object/Resolution/Definition rename progress
same-owner exact-version serialization
aggregate rollback scenarios
factual exact-view arbitration and winner-disappearance behavior
same-ID delete behavior under the still-delivered M1 public contract
```

Stable delivered scenario IDs remain stable. Do not invent replacement IDs merely because the implementation mechanism changed.

Existing tests are evidence, not authority. Apply this rule carefully:

```text
existing test matches preserved AS-IS/frozen M2 requirement
    -> fix the implementation; do not weaken the test

existing test asserts an internal M1 realization explicitly changed by frozen M2
    -> update the test to the M2 requirement while preserving semantic evidence

unclear whether a test or implementation is wrong
    -> re-read owning authorities; stop on unresolved contradiction
```

Current repository-specific traps to resolve correctly include:

- the advisory-gate inventory must now contain exactly three frozen gates, including `MODEL_ROOT_DELETE_GATE`; update any M1-only “two gates” assertion;
- Definition RENAME must be **gate before header row**, not header before gate; update obsolete harness wording/order and prove the actual gate-first wait graph;
- idempotent/convergent ATTACH and DETACH paths must continue to skip the ownership graph gate; fix the implementation rather than weakening this semantic-progress regression;
- root-delete/reference race cuts must respect the new lifetime locks and prove both valid winner orders without expecting a reference writer to pass through a held target `U` lock;
- atomic ObjectTemplate revise evidence must move to the real differential DML seam and continue to prove full rollback;
- do not “fix” deterministic timeouts by increasing global timeouts, adding sleeps or deleting blocker assertions.

Timeouts are hang guards only. A deterministic supported-path timeout or SQLSTATE `40P01` is a correctness finding.

No unexplained `SKIP`, `XFAIL`, flaky rerun or generic retry is permitted for normative evidence.

---

# 12. Test and implementation discipline

Use:

```text
CPython 3.14.x
uv and committed uv.lock
SQLAlchemy Core 2.x
Psycopg 3
pytest / pytest-asyncio
Hypothesis where it adds algebraic coverage
real PostgreSQL through TEST_DATABASE_URL
Ruff
Pyright strict
```

Do not use:

```text
SQLite
SQLAlchemy ORM Session / AsyncSession
Docker
Testcontainers
sleep-based concurrency orchestration
SERIALIZABLE as a substitute for the lock plan
generic deadlock/serialization retry middleware
global advisory locks beyond the exact registry
new dependencies for convenience
global Ruff/Pyright relaxation
broad warning/error suppression
```

Application/domain modules remain free of FastAPI, Pydantic, SQLAlchemy and Psycopg imports. Locking/failure realization stays inside the persistence/UoW boundary; application services express semantic intents and map bounded results.

Keep local suppressions narrow and justify each one in the handoff.

---

# 13. Required verification commands

A valid externally supplied real PostgreSQL target is mandatory for an S00 candidate.

Use only:

```text
TEST_DATABASE_URL
```

Do not provision a database, invent credentials, fall back to `NETAUTO_DATABASE_URL`, fall back to localhost or substitute another backend.

Run focused evidence first, then the complete required gate. Report exact commands and results.

At minimum run the repository's concrete equivalents of:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright

# focused planner evidence
uv run pytest -q <PLAN-01..PLAN-06 targets>

# all non-PostgreSQL regressions
uv run pytest -q -m "not postgresql"

# focused real-PostgreSQL planner/concurrency evidence
uv run pytest -q -m "postgresql and concurrency" <affected targets as needed>

# complete repository suite against real PostgreSQL
uv run pytest -q
```

Also report the exact PostgreSQL server version used.

The final full suite must include the PostgreSQL-marked tests; do not present a non-PostgreSQL-only run as the complete gate.

If `TEST_DATABASE_URL` or required infrastructure is unavailable:

```text
implement only what can be verified honestly
leave M2-S00 IN PROGRESS
record the exact blocker in status.md/report
push only if the partial candidate is useful and clearly labelled
never claim CANDIDATE READY FOR REVIEW
```

Do not fabricate evidence.

No dependency or lockfile change is expected. If `uv lock --check` fails because implementation changed dependencies, stop and justify why that change is inside frozen S00 scope before proceeding.

---

# 14. Documentation and status discipline

Do not edit the frozen M2 contract, architecture or `steps.md` to fit the implementation.

Do not rewrite the delivered AS-IS to describe an unreviewed candidate.

Do not create final-delivery evidence or begin AS-IS consolidation.

The active prompt remains in `docs/milestones/M2/wip/` until it is superseded or the reviewer accepts the slice. Do not delete this prompt in the implementation candidate.

`docs/milestones/M2/status.md` may be updated only to reflect verified operational facts:

```text
work incomplete or mandatory verification blocked/failing
    -> M2-S00 IN PROGRESS
    -> record exact blocker/finding

all S00 implementation and mandatory verification pass,
candidate committed and pushed
    -> M2-S00 CANDIDATE READY FOR REVIEW
    -> reviewer decision pending
```

Never mark:

```text
M2-S00 COMPLETED
M2 DELIVERED
review ACCEPTED
```

Those states are reviewer/human-owned.

Do not open `M2-S01`.

---

# 15. Git and publication discipline

Before publication:

```text
review git diff and staged diff
exclude unrelated changes
verify no secret/URL/environment value is present
verify obsolete Actions/payload material remains absent
verify active prompt remains present
run git diff --check
```

Use one or more intentional commits with clear M2-S00 scope. A suitable implementation commit title is:

```text
feat(m2-s00): centralize transaction lock planning
```

If status/evidence cleanup is separated, keep every commit coherent and report all SHAs.

Push normally to:

```text
origin/M2
```

Do not create a PR, merge, force-push, tag or release.

After push, verify:

```text
local HEAD SHA
origin/M2 SHA
local/remote synchronization
working tree clean
```

Do not claim publication or a clean tree without checking it.

---

# Completion report

At the end, provide a reviewer-oriented candidate handoff containing only verified facts:

- cycle `M2`, slice `M2-S00`, branch `M2`;
- candidate commit SHA(s);
- push and local/remote synchronization status;
- working-tree status;
- concise changed-file inventory;
- confirmation that the obsolete Actions workflows and encoded payloads are absent;
- centralized planner types/modules and UoW integration;
- exact three-gate registry and acquisition discipline;
- exact four row-lock modes and SQL compilation evidence;
- canonical order/coalescence implementation summary;
- explicit delivered 32-mutation coverage matrix/result;
- differential ObjectTemplate declaration implementation summary;
- whole-UoW restart budget and exact approved causes;
- finite SQLSTATE/constraint-classification summary;
- exact verification commands, pass/fail counts and durations where available;
- exact PostgreSQL server version;
- explicit result for `PLAN-01 ... PLAN-06`;
- affected AS-IS concurrency scenario results;
- full-suite result and confirmation whether any supported path produced `40P01`;
- schema/migration changes: expected `none`;
- dependency/lockfile changes: expected `none`;
- every unexecuted requirement and exact reason;
- every residual risk or architecture/documentation finding;
- confirmation that no M2-S01 business/API/schema capability was introduced;
- final `status.md` state, without claiming reviewer-owned completion.

The correct handoff wording is:

```text
M2-S00 candidate implemented and ready for reviewer inspection
```

only when every mandatory S00 gate has actually passed and the candidate has been pushed.