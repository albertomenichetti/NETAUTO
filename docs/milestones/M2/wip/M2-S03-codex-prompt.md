# Codex implementation prompt — M2-S03

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It narrows the authorized implementation task but does not override `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract, architecture or steps, the active milestone status, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M2-S03 — Complete kernel concurrency and deadlock-evidence closure
```

Work directly on branch:

```text
M2
```

The reviewer-owned implementation baseline is:

```text
850abd97ece1aadeae65aa090d86c7ec4982751f
docs(m2): accept S02 and open S03
```

Start from the current `origin/M2` tip containing this prompt. That tip must be `850abd97...` or a direct descendant. Do not reset, rebase, force-push or rewrite the published S00/S01/S02 history.

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    READY, authorized
M2-S04    BLOCKED
```

The publication action is:

```text
perform the mandatory repository pre-flight
complete the 41-mutation physical-plan audit and any required corrections
complete the canonical 83-scenario deterministic PostgreSQL registry
complete the exact 21-predicate evidence mapping
implement and pass M2-VER-15 ... M2-VER-19
run every focused and complete mandatory gate
commit intentionally
push normally to origin/M2
verify local/remote synchronization and a clean working tree
publish an M2-S03 candidate for reviewer inspection
```

Do not create a pull request. Do not merge to `master`, force-push, rewrite published history, tag or release.

Do not add or use GitHub Actions, workflow-dispatched implementation, CI-driven commits, encoded patches or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before modifying code, tests, status or evidence, read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Current delivered AS-IS
docs/architecture/README.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/persistence.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

# Active M2 authority
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/architecture/provenance.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Active execution aid
docs/milestones/M2/wip/M2-S03-codex-prompt.md
```

Read owning sections dependency-first. Frozen documents are authority. This prompt is only an execution aid. Historical discovery, proposal and cross-check files under `docs/milestones/M2/wip/` have no implementation authority; `architecture/provenance.md` owns their disposition.

Confirm from the repository itself that:

```text
checked-out branch                  = M2
README active cycle                 = M2 / IMPLEMENTATION / branch M2
origin/M2 ancestry                  includes 850abd97...
M2 contract                         = FINAL / FROZEN
M2 architecture set                 = FINAL / FROZEN
M2 steps                            = FINAL / FROZEN
M2-S00                              = reviewer-owned COMPLETED
M2-S01                              = reviewer-owned COMPLETED
M2-S02                              = reviewer-owned COMPLETED
M2-S03                              = READY or IN PROGRESS
M2-S04                              = BLOCKED
relevant architecture reopen        = none
STACK-01 ... STACK-10               = RATIFIED
```

Inspect at least these implementation and evidence boundaries before editing:

```text
src/netauto/application/datatypes.py
src/netauto/application/objecttemplates.py
src/netauto/application/objects.py
src/netauto/application/relationshipdefinitions.py
src/netauto/application/relationships.py

src/netauto/persistence/locking.py
src/netauto/persistence/uow.py
src/netauto/persistence/datatypes.py
src/netauto/persistence/objecttemplates.py
src/netauto/persistence/objects.py
src/netauto/persistence/relationships.py
src/netauto/persistence/lifecycle.py
src/netauto/persistence/metadata.py

tests/support/pg_harness.py
tests/support/semantic_concurrency.py

tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py

tests/test_datatype_semantic_concurrency.py
tests/test_objecttemplate_semantic_concurrency.py
tests/test_object_semantic_concurrency.py
tests/test_relationshipdefinition_semantic_concurrency.py
tests/test_relationship_semantic_concurrency.py
tests/test_m2_locking.py
tests/test_m2_locking_postgresql.py
tests/test_m2_s01_semantic_concurrency.py
tests/test_m2_s02_semantic_concurrency.py
```

Search the complete repository for every:

```text
prepare_lock_plan
acquire_lock_plan
LockPlan
LockPlanStale
begin_dml
RowLockIntent
AdvisoryGate
pg_blocking_pids
40P01
40001
pytest.mark.concurrency
scenario registry
safety-predicate registry
```

The list above is not exhaustive.

A valid externally supplied real PostgreSQL target through `TEST_DATABASE_URL` is mandatory for a complete S03 candidate. Verify availability during pre-flight. Do not provision PostgreSQL, use Docker/Testcontainers, invent credentials, fall back to localhost, fall back to `NETAUTO_DATABASE_URL`, or substitute SQLite.

If README, branch, `status.md`, frozen authorities, candidate ancestry or required infrastructure disagree, stop before modifying the affected work and report the mismatch. If normative authorities conflict or do not determine one material behavior, stop only the affected point and report an architecture/documentation finding. Do not silently choose a convenient interpretation.

Code, tests, Git history, candidate reports and this prompt are evidence or execution aids, not semantic authority.

---

# 2. Slice scope and hard boundary

M2-S03 is a cross-kernel concurrency and verification-closure slice. It introduces no new business capability and no new public route.

## 2.1 Explicitly in scope

```text
41 / 41 production mutation lock-plan coverage
21 / 21 semantic safety-predicate coverage
83 / 83 canonical deterministic scenario coverage
3 / 3 advisory-gate coverage
4 / 4 row-lock-mode coverage
one canonical global row order
approved whole-UoW restart boundaries
finite PostgreSQL failure classification boundaries
required blocking and required progress evidence
complete supported-path 40P01 census

M2-VER-15
M2-VER-16
M2-VER-17
M2-VER-18
M2-VER-19

ROW-01 ... ROW-30
ARB-01 ... ARB-08
REF-01 ... REF-11
GATE-01 ... GATE-07
SNAP-01 ... SNAP-05
ATOMIC-01 ... ATOMIC-07
PAR-01 ... PAR-09
PLAN-01 ... PLAN-06

machine-checkable mutation/scenario/predicate/evidence registries
deterministic harness completion
implementation corrections exposed by the required evidence
complete regression closure for the affected kernel
```

## 2.2 Explicitly out of scope

Do not introduce or implement:

```text
M2-S04 runtime settings
pool configuration changes
startup revision guard
GET /health/core
CLI or REPL
wheel/Linux operating work beyond normal build regression
native authentication, authorization or TLS termination
new business routes or DTO fields
new domain capability or public failure code
new advisory gate
new row-lock mode
new retry cause or generic retry middleware
global SERIALIZABLE isolation
schema, migration or index changes
new dependency or uv.lock change
M1 -> M2 bridge, backfill, stamp path or dual decoder
```

The accepted baseline must remain:

```text
15 authoritative tables
0001_m2_kernel
one Alembic base / one head
compare_metadata == []
63 business HTTP operations
no Health route yet
no CLI surface yet
```

If a schema, migration, dependency or public-contract change appears necessary, stop and identify the exact frozen authority that requires it. Do not modify the accepted durable baseline or public surface for test convenience.

Do not modify frozen contract, architecture or `steps.md` to fit code.

---

# 3. Existing baseline and required consolidation

S00, S01 and S02 already delivered substantial concurrency implementation and evidence. Preserve it.

The current repository has several intentionally incremental registries:

```text
tests/test_m1_traceability.py
    delivered 51-scenario target map and 19-predicate baseline

tests/test_m2_s00_traceability.py
    delivered 32-mutation planner inventory and PLAN-01 ... PLAN-06

tests/test_m2_traceability.py
    frozen M2 census plus S01/S02 target maps
```

M2-S03 must produce one complete M2 view without creating competing authorities.

A derived/imported composition is acceptable. Blindly copying the same scenario or predicate map into several independently maintained dictionaries is not acceptable.

At the end of S03, one machine-checkable M2 registry must own or unambiguously compose:

```text
M2_MUTATIONS                   exact 41 IDs
M2_MUTATION_TO_CALLABLE        exact production callable ownership
M2_MUTATION_TO_GATE            exact gate or none
M2_MUTATION_TO_EVIDENCE        non-empty evidence for every mutation

M2_CONCURRENCY_SCENARIOS       exact 83 IDs
M2_SCENARIO_TO_TARGETS         non-empty real target set for every ID
M2_SCENARIO_TO_RECIPES         exact primary/secondary recipe ownership
M2_PREDICATE_TO_SCENARIOS      exact 21-predicate map

M2_EVIDENCE_TO_TARGETS
    M2-VER-15 ... M2-VER-19 = IMPLEMENTED with non-empty targets
    accepted S00/S01/S02 bundles preserved
    later primary bundles remain honest DESIGNED states
```

Concrete names may differ if the structure is equivalent and singular.

Every mapped target must:

```text
exist as a file and pytest function
resolve against actual pytest collection
use exact parameterized node IDs where a variant is normative
be uniquely attributable in its declared role
not be a placeholder, minimum-count assertion or uncollected string
```

A broad test may support several scenario IDs only when it explicitly asserts every mapped obligation. Merely executing the same code path is insufficient.

Preserve `tests/test_m1_traceability.py` as delivered-AS-IS regression evidence or refactor it losslessly. The final M2 registry must nevertheless expose all 83 current M2 IDs and the two new predicates `VH` and `RS`.

---

# 4. Exact 41-mutation physical-plan closure

## 4.1 Canonical census

The exact mutation set is:

```text
DataType — 10
    DT.C
    DT.CN
    DT.R
    DT.P
    DT.SD
    DT.CD
    DT.D
    DT.DD
    DT.DL
    DT.DESC

ObjectTemplate — 10
    OT.C
    OT.CN
    OT.R
    OT.P
    OT.SD
    OT.CD
    OT.D
    OT.DD
    OT.DL
    OT.DESC

Object / ownership — 7
    OBJ.C
    OBJ.RN
    OBJ.DC
    OBJ.SC
    OBJ.A
    OBJ.DET
    OBJ.DEL

RelationshipDefinition / RDV — 10
    RD.C
    RD.RN
    RD.CN
    RD.R
    RD.P
    RD.SD
    RD.CD
    RD.D
    RD.DD
    RD.DL

factual Relationship — 4
    REL.C
    REL.DC
    REL.SC
    REL.DEL
```

Do not retain the S00 32-operation registry as the final M2 inventory. Extend or supersede it with an exact 41-operation view while preserving its accepted PLAN evidence.

## 4.2 Exact gate ownership

The only gated mutations are:

```text
OBJ.A
    OWNERSHIP_GRAPH_WRITE_GATE

RD.C
RD.RN
    RELATIONSHIP_DEFINITION_CONFLICT_GATE

DT.DL
OT.DL
RD.DL
    MODEL_ROOT_DELETE_GATE
```

Every other mutation has no advisory gate.

Assert:

```text
three and only three gate keys exist
at most one gate per UoW
gate before every explicit row lock
gate waiter owns no NETAUTO row lock
no row -> gate edge
no public busy outcome from gate contention
```

## 4.3 Exact row discipline

Every mutation must remain compatible with the frozen registry in `architecture/concurrency.md`:

```text
KS    FOR KEY SHARE
S     FOR SHARE
NKU   FOR NO KEY UPDATE
U     FOR UPDATE
```

Global class order:

```text
10  ObjectTemplate headers/versions
20  DataType headers/versions
30  RelationshipDefinition headers/versions
40  Object rows
50  factual Relationship rows
```

Intra-class order remains:

```text
ObjectTemplate
    ancestor before descendant
    unrelated UUID ascending
    header before exact versions
    versions ascending

DataType / RelationshipDefinition
    UUID ascending
    header before exact versions
    versions ascending

Object / Relationship
    UUID ascending
```

Normal lock upgrades and post-DML explicit locks remain forbidden.

## 4.4 Evidence standard for 41 / 41

Do not satisfy the census only by checking that function source contains `prepare_lock_plan`.

For every mutation, provide a traceable combination of:

```text
production callable ownership
expected gate ownership
central-planner usage
begin-DML phase discipline
at least one concrete production execution target
row/gate-plan observation appropriate to its risk
```

Fixed-plan operations may share a parameterized plan-observation target. Candidate-dependent operations require variants sufficient to prove their distinct physical rules.

At minimum include explicit evidence for:

```text
OT.C
    explicit and implicit parent binding
    component target lifetime
    property DTV explicit/default binding

OT.CN
    cloned parent exact-version lifetime
    cloned component stable-root lifetime
    cloned property DTV lifetime

OT.R
    unchanged declaration
    removed declaration
    new/rebound exact target
    same-target reinsertion requiring KS only
    parent direct-FK rebind target-before-owner

OT.P
    target exact dependencies S
    own header/DRAFT owner
    historical recertification after wait

OBJ.C
    explicit and implicit OTV selection

OBJ.SC
    target OTV before Object owner

OBJ.A
    ownership gate first
    parent NKU + child KS coalesced and UUID ordered

RD.C
    Definition gate first
    endpoint ObjectTemplate lifetime
    property DTV explicit/default binding

RD.CN
    cloned property DTV lifetime

RD.R
    differential declaration variants

RD.P
    exact dependency S
    Definition/DRAFT ownership
    historical recertification

REL.C
    explicit and implicit RDV admission
    endpoint Object lifetime
    no global Relationship gate

REL.SC
    Definition KS + target RDV S before factual Relationship NKU
```

Use existing accepted targets where they already prove the obligation. Add or strengthen targets only where the evidence is missing.

Any observed mismatch is an implementation defect inside S03: preserve the frozen design, correct the production path and add permanent regression evidence.

## 4.5 Restart and classifier boundaries

Preserve exactly:

```text
MAX_SEMANTIC_UOW_ATTEMPTS = 4

approved automatic restart causes only:
    LOCK_PLAN_STALE
    exact-view collision whose current owner disappeared

no automatic retry:
    semantic failure
    40P01
    40001
```

Each retry attempt is a new UoW/transaction. No savepoint or store-fragment retry is authorized.

Re-execute `PLAN-01 ... PLAN-06` and keep their accepted static, real-PostgreSQL and concurrency targets resolvable.

---

# 5. Exact 21-predicate closure

The canonical predicate set is exactly:

```text
NU
VS
DG
LS
DV
VH
BA
AM
RL
AL
ML
OS
RS
PO
OF
SO
OC
RC
RF
RA
ES
```

The exact frozen mapping is:

```text
NU  -> ARB-01
VS  -> ROW-01, ROW-02, ROW-18, ROW-19
DG  -> ROW-03, ROW-04, ROW-20, ATOMIC-01, ATOMIC-05
LS  -> ROW-04, ROW-06, ROW-20, ROW-21
DV  -> ROW-05, ROW-06, ROW-08, ROW-21, ROW-23, ROW-24, ROW-30
VH  -> ROW-22, ROW-23
BA  -> ROW-07, ROW-08, ROW-12, ROW-24, ROW-28, ROW-30
AM  -> ROW-09, ROW-10, ROW-25
RL  -> REF-01 ... REF-11
AL  -> ROW-16, ROW-17; RD variants are included in ROW-16
ML  -> ROW-15
OS  -> ROW-11, ROW-12, ATOMIC-04
RS  -> ROW-26 ... ROW-29, ATOMIC-06, ATOMIC-07
PO  -> ROW-13, ROW-14
OF  -> ARB-03, ARB-04, ATOMIC-04
SO  -> ARB-02
OC  -> GATE-01, GATE-02, GATE-03, PAR-04
RC  -> GATE-04, GATE-05, GATE-06, ATOMIC-04
RF  -> ARB-05, ARB-07, ARB-08, ATOMIC-02
RA  -> ARB-06, ARB-07, ATOMIC-03
ES  -> SNAP-01 ... SNAP-05, PAR-01, PAR-02, PAR-08
```

Machine checks must assert:

```text
exact 21-key census
no additional predicate
all mapped scenario IDs belong to the exact 83-ID registry
every predicate has at least one collected target through its scenarios
every PostgreSQL concurrency predicate has real independent-session evidence
```

Do not infer predicate meaning from current lock modes. Semantic predicates remain owned by the matrix.

---

# 6. Canonical 83-scenario registry

## 6.1 Exact census

```text
ROW       30
ARB        8
REF       11
GATE       7
SNAP       5
ATOMIC     7
PAR        9
PLAN       6
          --
total     83
```

The exact IDs are:

```text
ROW-01 ... ROW-30
ARB-01 ... ARB-08
REF-01 ... REF-11
GATE-01 ... GATE-07
SNAP-01 ... SNAP-05
ATOMIC-01 ... ATOMIC-07
PAR-01 ... PAR-09
PLAN-01 ... PLAN-06
```

Every ID must have:

```text
one non-empty target set
one primary recipe
optional explicit secondary recipes
collected pytest node IDs
semantic outcome assertions
mechanism assertions where architecture-owned
SQLSTATE observation where a worker can fail
```

Identifier-only registration is forbidden.

## 6.2 Preserve the 51 delivered scenarios

Preserve every delivered target and obligation unless strengthened by the frozen M2 delta.

The explicit modified obligations are:

```text
ARB-05
    losing CREATE returns relationship_fact_conflict
    no loser mutation/event

ARB-06
    same-ID DELETE outcomes are one 204 and one 404/resource_not_found

ARB-07
    current winner is conflict, never successful convergence
    winner disappearance may trigger bounded fresh-UoW restart

SNAP-01
    Definition/Resolution rename variants include all real Relationship
    CREATE / DATA_CHANGE / SCHEMA_CHANGE / DELETE transitions

SNAP-02
    Object rename variants include all real Relationship
    CREATE / DATA_CHANGE / SCHEMA_CHANGE / DELETE transitions

ATOMIC-02
    closure-collision loser rolls back and maps to M2 conflict

ATOMIC-03
    delete rollback remains exact and same-ID successful path is 204/404
```

No other delivered scenario may be weakened or silently dropped.

## 6.3 Required family broadening

The common versioned-aggregate predicates apply across distinct production implementations.

Audit and add variants as needed so the scenario registry proves the materially distinct paths for:

```text
ROW-03 / ROW-04
    exact DRAFT generation races across DT, OT and RDV paths
    use ROW-20 for the RDV-specific generation family where appropriate

ROW-07 ... ROW-10
    ObjectTemplate/DTV admission and active-model paths remain complete

ROW-16
    root/internal lifetime for DataType, ObjectTemplate and RelationshipDefinition
    both winner orders where the public result differs

ROW-17
    Definition rename/root-delete same-aggregate lifetime

SNAP-01 / SNAP-02
    map the accepted S02 DATA_CHANGE/SCHEMA_CHANGE rename-cut targets in addition
    to delivered CREATE/DELETE targets

PAR-06 / PAR-07
    preserve delivered compatible/incompatible header behavior
```

A shared helper implementation is not evidence that separate services/stores obey the same rule.

## 6.4 `REF-08` — ObjectTemplate CREATE_NEXT cloned references

Implement deterministic real-PostgreSQL variants for all materially distinct cloned reference shapes:

```text
cloned exact parent OTV
cloned stable component target ObjectTemplate
cloned exact property DTV
```

For each shape prove both lifetime orders:

```text
clone/reference first
    -> target delete is blocked
    -> cloned version and declarations are complete

target delete first
    -> CREATE_NEXT fails with the frozen bounded missing-reference outcome
    -> no new partial version/declaration set survives
```

Required mechanism assertions:

```text
cloned target header KS
cloned exact target version KS where exact
all cloned targets acquired before child insertion
no PUBLISHED requirement for historical clone
no 40P01
```

Use stable scenario ID `REF-08`; parameterized variants remain beneath the same ID.

## 6.5 `REF-09` — differential replacement/reinsertion

Complete the accepted S01 evidence so the canonical scenario covers each distinct physical FK shape that can be replaced or reinserted:

```text
ObjectTemplate property -> exact DTV
ObjectTemplate component -> stable ObjectTemplate target
RelationshipDefinition property -> exact DTV
```

Exercise as applicable:

```text
new/rebound target
same exact target reinserted because another field changed
unchanged physical row
removed row
reference-first and delete-first orders
```

Prove:

```text
no transient reference gap visible to a target delete
no blind delete-all/insert-all authority
new/rebound target uses S
same-target reinsertion uses KS
unchanged/removed outgoing target takes no unnecessary admission lock
revision and complete declaration set roll back atomically on failure
no dangling reference
no 40P01
```

Do not weaken the accepted differential DML tests.

## 6.6 `REF-10` — all direct existing-owner rebinds

The accepted S02 candidate already covers factual Relationship schema rebind. Preserve and rerun it.

Add the two remaining direct-owner families, both winner orders:

```text
ObjectTemplate exact parent-version rebind × target ObjectTemplate root delete
Object SCHEMA_CHANGE × target ObjectTemplate root delete
```

Together with the existing Relationship variant, prove:

```text
target exact version/root locks precede mutable owner
waiter does not hold the existing owner while waiting for target
rebind-first leaves a blocker and target delete cannot commit
root-delete-first prevents the new/rebound target use or yields the frozen
fresh serial outcome
stable existing root references are not reinterpreted as a new public conflict
no partial owner state
no 40P01
```

Use `pg_blocking_pids()` for required waits and exact lock-plan order assertions.

## 6.7 `REF-11` — mutually referencing model roots

Implement a deterministic real-PostgreSQL scenario using every materially realizable mutual-root FK shape in the final schema; at minimum cover two ObjectTemplate roots with mutual stable component references.

Prove:

```text
both root DELETE commands acquire MODEL_ROOT_DELETE_GATE before root rows
gate waiter owns no NETAUTO row lock
one root delete enters FK/cascade arbitration at a time
no transaction waits on the other root while holding the inverse root
both committed/failing outcomes have one serial explanation
losing/blocked delete leaves both roots and complete owned children intact
no partial aggregate
no 40P01
no retry of a deadlock victim
```

Do not invent a busy result. Normal bounded `delete_blocked` semantics remain authoritative.

## 6.8 `GATE-07` — model-root gate waiter

Use semantically independent roots so the result proves physical over-serialization rather than a semantic dependency.

Required sequence:

```text
T1 acquires MODEL_ROOT_DELETE_GATE and remains open
T2 starts another model-root delete
OBS proves T2 blocked by T1 through pg_blocking_pids()
T2 owns no NETAUTO row lock while waiting
T1 completes/releases
T2 acquires the gate
T2 performs a subsequent fresh aggregate/blocker read
T2 completes with its ordinary serial semantic result
```

Assert no new public conflict code and no `40P01`.

`PLAN-06` remains necessary but does not replace this root-delete-specific scenario.

## 6.9 `PAR-08` — Definition rename compatibility

Prove positive progress while an RD.RN transaction remains open for every materially distinct compatible family:

```text
RDV REVISE on an exact DRAFT
RD SET_DEFAULT or CLEAR_DEFAULT
RDV DEPRECATE
factual Relationship CREATE
```

Where useful, include CREATE_NEXT/PUBLISH only if they exercise another lock-mode path not already represented.

Required assertions:

```text
RD.RN owns Definition conflict gate + header KS
compatible operation reaches a positive production phase while rename is open
no hidden second Definition gate
no prohibited header-exclusive serialization
final state is serially valid
Relationship event metadata remains one coherent observation
no 40P01
```

Use `PAR-08`; do not hide these variants under delivered `PAR-02` alone.

## 6.10 `PAR-09` — distinct RDV progress

Prove both:

```text
distinct exact RDV DEPRECATE operations
    shared Definition header S
    distinct exact RDV NKU
    both make progress without waiting on each other at the header

distinct exact DRAFT REVISE operations
    shared Definition header KS
    distinct exact RDV NKU
    both make progress
```

Use a positive production phase while the other transaction remains open. Final aggregates and revisions/statuses must be exact. No `40P01`.

## 6.11 Remaining new M2 scenarios

Preserve and rerun the already accepted implementations for:

```text
ROW-18 ... ROW-30
ARB-08
REF-07
REF-09 accepted variants
REF-10 Relationship variant
SNAP-05
ATOMIC-05 ... ATOMIC-07
PLAN-01 ... PLAN-06
```

Strengthen them only when the complete S03 registry exposes a missing normative assertion.

---

# 7. Deterministic harness completion

The harness must support the complete frozen role and phase vocabulary.

## 7.1 Roles

```text
CTL
OBS
B
T1
T2
optional T3
```

Every semantic worker uses an independent PostgreSQL session/UoW with identifiable backend metadata.

## 7.2 Phase vocabulary

Support the exact M2 phase set, either through one enum or a singular equivalent registry:

```text
UOW_STARTED
DISCOVERY_COMPLETE
LOCK_PLAN_BUILT
GATE_WAITING
GATE_ACQUIRED
ROW_LOCK_WAITING
ROW_LOCKS_ACQUIRED
PROTECTED_STATE_REREAD
LOCK_PLAN_STALE
DEPENDENCIES_STABILIZED
CANDIDATE_WRITTEN
CLOSURE_WRITTEN
METADATA_SNAPSHOT_CAPTURED
EVENT_SET_WRITTEN
CONSTRAINT_ARBITRATED
BEFORE_COMMIT
COMMITTED
ROLLED_BACK
UOW_RESTARTED
```

Preserve aliases only when they are a thin compatibility projection and do not create two independent vocabularies.

A test-only interceptor may observe or pause a production phase but may not:

```text
change candidate data
issue semantic SQL
acquire a production lock
change isolation
commit or rollback
change failure mapping
choose another production path
use sleep as ordering authority
```

## 7.3 Required blocking

Required blocking is proved primarily by:

```text
pg_blocking_pids(waiter_pid)
    contains the known blocker PID
```

`pg_stat_activity` and `pg_locks` may supply diagnostics only.

## 7.4 Required progress

Required non-blocking is proved by a positive production phase reached by T2 while T1 remains open.

Do not use task scheduling, a short timeout, absence from `pg_blocking_pids()` or a completed discovery read as the sole progress proof.

## 7.5 Worker outcome and SQLSTATE capture

Provide one shared worker-outcome boundary that records, when present:

```text
returned semantic value
ApplicationFailure
unexpected exception type
PostgreSQL SQLSTATE
last production/test phase
commit or rollback outcome
```

Do not swallow raw database errors before SQLSTATE is recorded. Preserve normal production mapping; the capture belongs only to the test harness.

For every T3 target:

```text
any worker SQLSTATE == 40P01
    -> immediate test failure

40P01 / 40001
    -> never retried by the production path
```

The final S03 evidence record must report all observed worker SQLSTATE values or explicitly state that none were observed.

## 7.6 Recipes

Preserve the delivered recipes:

```text
REC-LOCK
REC-UNIQUE
REC-FK
REC-GATE
REC-CUT
REC-ROLLBACK
REC-PROGRESS
REC-ABA
```

and the M2 recipes:

```text
REC-PLAN
REC-CLASSIFY
REC-RESTART
```

Every scenario must have one primary recipe and only explicit secondary recipes.

Timeouts remain hang guards. Normative scenarios must not be automatically rerun to hide flakiness.

---

# 8. Primary M2-S03 evidence bundles

## 8.1 `M2-VER-15` — DRAFT lost-update prevention

Map and execute exact evidence for:

```text
same-generation REVISE / REVISE
REVISE / PUBLISH
PUBLISH / DELETE_DRAFT
fresh generation and lifecycle loser outcome
no hybrid declaration generation
rollback after physical child work
```

Required scenario ownership:

```text
ROW-03
ROW-04
ROW-20
ATOMIC-01
ATOMIC-05
```

Ensure materially distinct DT, OT and RDV paths are represented.

## 8.2 `M2-VER-16` — model admission stability

Map and execute exact evidence for:

```text
default validity through commit
explicit/implicit exact admission
publisher/deprecator rendezvous
active-consumer removal semantics
VH historical recertification
no PUBLISHED consumer -> non-PUBLISHED direct dependency
no new fact bound to a target that lost PUBLISHED
```

Required scenario ownership:

```text
ROW-07 ... ROW-10
ROW-21 ... ROW-25
ROW-30
```

Do not substitute one family for another where separate service/store implementations exist.

## 8.3 `M2-VER-17` — concurrent factual CREATE

Map and execute:

```text
ARB-05
ARB-07
ARB-08
ATOMIC-02
PLAN-05
```

Prove:

```text
at most one factual identity
one complete closure and creation event set
losing physical work rolls back
winner current -> relationship_fact_conflict
winner disappeared -> bounded fresh-UoW restart
no 40P01
```

## 8.4 `M2-VER-18` — factual mutation/delete serialization

Map and execute:

```text
ROW-26
ROW-27
ROW-28
ROW-29
ARB-06
```

Prove exact serial state/event outcomes for all DATA_CHANGE, SCHEMA_CHANGE and DELETE combinations, including the one-204/one-404 exact DELETE result.

## 8.5 `M2-VER-19` — coherent historical metadata

Map and execute:

```text
SNAP-01 ... SNAP-05
PAR-01
PAR-02
PAR-08
```

Prove all four real factual transition families against Definition/Resolution and Object rename cuts, one authoritative metadata statement, complete event-set observation and required progress.

## 8.6 Honest bundle states

At S03 candidate handoff:

```text
M2-VER-15 ... M2-VER-19
    -> IMPLEMENTED with exact collected targets
    -> PASS only in the candidate evidence/status record after execution

accepted S00/S01/S02 primary bundles
    -> preserved

M2-VER-22 and later primary bundles
    -> remain DESIGNED until their assigned slices

M2-VER-31 / M2-VER-32
    -> remain S08-owned even though S03 supplies supporting registries
```

Do not overstate future bundle implementation merely because the full test suite is green.

---

# 9. Deadlock and wait-graph closure

The supported wait graph remains:

```text
optional one advisory gate
-> globally ordered explicit row locks
-> fresh protected reads
-> deterministic current/child DML
-> append-only lifecycle batch
-> commit
```

Permanent S03 evidence must reject:

```text
row -> gate
more than one gate
normal lock upgrade
post-DML explicit lock
owner-before-direct-target rebind
unsorted overlapping closure insertion
consumer-row locking from dependency deprecator
root-delete/root-delete inverse waits
lifecycle FK/back-edge to current model
```

Required progress must remain:

```text
unrelated REL.C × REL.C
REL.C × OBJ.RN(endpoint)
REL.C × RD.RN
RD.RN × compatible exact-version/default/lifecycle operations
distinct-version DT/OT/RD DEPRECATE
distinct DRAFT REVISE operations
```

Intentional serialization must remain:

```text
real ownership edge additions
RD CREATE/RENAME candidates
all model-root deletes
parent Object rename/data mutation × ATTACH
description × default/header policy mutation
```

A functional final state is not sufficient when the frozen architecture owns a blocking or progress contract.

No correctness result may rely on PostgreSQL deadlock-victim selection. Any supported-path `40P01` is a blocking implementation finding.

---

# 10. Required verification execution

## 10.1 Collection and registry checks

Run and record at least:

```text
uv run pytest --collect-only -q
```

Add focused static checks proving:

```text
41 exact mutation IDs
83 exact scenario IDs
21 exact predicate IDs
3 exact gates
4 exact row modes
all scenario target node IDs collected
all mutation evidence targets collected
all M2-VER-15 ... 19 targets collected
no empty target set
no duplicate competing registry
```

## 10.2 Focused S03 runs

Create the smallest focused module grouping that cleanly owns S03 additions, expected conceptually as one or more of:

```text
tests/test_m2_s03_traceability.py
tests/test_m2_s03_semantic_concurrency.py
```

Equivalent placement is acceptable when it preserves existing module ownership and avoids one oversized undifferentiated file.

Run exact focused targets for:

```text
41-mutation plan registry
21-predicate map
83-scenario target/recipe map
REF-08
REF-09 complete variants
REF-10 OT/Object/Relationship variants
REF-11
GATE-07
PAR-08
PAR-09
ROW-03/04/16 cross-family broadening
SNAP-01/02 M2 transition broadening
M2-VER-15 ... M2-VER-19
```

## 10.3 Exact canonical scenario execution

Build the sorted deduplicated union of every concrete target in `M2_SCENARIO_TO_TARGETS` and execute it.

The handoff must report:

```text
83 / 83 scenario IDs mapped
number of unique concrete pytest node IDs
all mapped targets collected
all mapped targets executed
all mapped targets passed
```

A full-suite pass without an exact scenario-target execution ledger is insufficient for S03 completion.

## 10.4 Complete gates

At minimum run:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright

uv run pytest -q tests/test_m1_traceability.py \
  tests/test_m2_s00_traceability.py \
  tests/test_m2_traceability.py \
  <new S03 traceability targets> -ra

uv run pytest -q \
  tests/test_datatype_semantic_concurrency.py \
  tests/test_objecttemplate_semantic_concurrency.py \
  tests/test_object_semantic_concurrency.py \
  tests/test_relationshipdefinition_semantic_concurrency.py \
  tests/test_relationship_semantic_concurrency.py \
  tests/test_m2_s01_semantic_concurrency.py \
  tests/test_m2_s02_semantic_concurrency.py \
  <new S03 concurrency targets> -ra

uv run pytest -q tests/test_m2_locking.py \
  tests/test_m2_locking_postgresql.py -ra

uv run pytest -q tests/test_schema_metadata.py \
  tests/test_migrations.py -ra

uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

Adapt command paths to the actual implementation, but do not omit an obligation.

The complete suite must run with the externally supplied `TEST_DATABASE_URL` and include every PostgreSQL target.

Record:

```text
exact commands
pass counts and durations
CPython version
PostgreSQL server version
uv version
41 / 41 mutation-plan census
83 / 83 scenario census
21 / 21 predicate census
M2-VER-15 ... 19 target results
skip / xfail / rerun census
all observed worker SQLSTATE values
supported-path 40P01 census
```

No skip, xfail, deselection mistake, flaky rerun or timeout counts as PASS for an assigned requirement.

## 10.5 Unchanged-boundary verification

Explicitly verify:

```text
15 authoritative tables
one Alembic base / one head
0001_m2_kernel unchanged
compare_metadata == []
no schema or migration diff
no dependency or uv.lock diff
63 exact business HTTP operations
no Health/startup/CLI/packaging/M2-S04 surface
obsolete Actions/payload material remains absent
```

---

# 11. Documentation, commits and publication discipline

Keep this execution aid in:

```text
docs/milestones/M2/wip/M2-S03-codex-prompt.md
```

until reviewer acceptance. Do not delete it in the implementation candidate. Its retirement is reviewer-owned after slice acceptance.

Use intentional commits. A suitable separation is:

```text
implementation / harness / deterministic evidence
candidate evidence and status
optional provenance-only status correction when the evidence commit SHA must be recorded
```

Do not manufacture extra commits merely to imitate this pattern.

Only when every mandatory focused, exact-registry and complete gate passes may `docs/milestones/M2/status.md` be changed to:

```text
M2-S03 — CANDIDATE READY FOR REVIEW
reviewer decision pending
M2-S04 — BLOCKED
```

The candidate record must include:

```text
prompt baseline and prompt commit
implementation commit(s)
candidate evidence/status commit
publication provenance, when applicable

41 / 41 mutation plans
exact gate census
exact row-mode/order discipline

83 / 83 scenarios
unique concrete target count
all target node IDs collected/executed/passed

21 / 21 predicates and exact mapping
M2-VER-15 ... M2-VER-19 target membership/results

new/strengthened scenario disposition:
    REF-08
    REF-09
    REF-10
    REF-11
    GATE-07
    PAR-08
    PAR-09
    cross-family ROW/SNAP variants

harness phase and SQLSTATE-capture disposition
environment versions
focused and complete commands/counts/durations
skip/xfail/rerun and 40P01 census
unchanged schema/migration/dependency/public-surface statement
```

Codex must not declare `M2-S03 COMPLETED`. Acceptance remains reviewer-owned.

If any mandatory requirement remains unexecuted, any target fails, `TEST_DATABASE_URL` is unavailable, a supported scenario produces `40P01`, or a new architecture/documentation finding emerges:

```text
do not mark CANDIDATE READY FOR REVIEW
do not start M2-S04
record an honest IN PROGRESS or STOP state
record the exact blocker and completed partial work
publish only an explicitly partial candidate when useful
```

Push normally to `origin/M2`, then verify:

```text
local HEAD == origin/M2 == remote M2
working tree clean
ahead/behind 0/0
no PR created
no GitHub Actions or encoded publication mechanism introduced
```

---

# 12. Required handoff

The final Codex handoff must report, without claiming reviewer acceptance:

```text
cycle / slice / branch
starting reviewer baseline
implementation commit(s)
candidate status/provenance commit(s)
local/remote synchronization and clean tree

41-mutation closure
    exact census
    gate census
    candidate-dependent plan variants
    any production correction made

83-scenario closure
    exact family census
    exact unique target count
    collection/execution/pass result
    disposition of every added or broadened scenario

21-predicate closure
    exact map
    all predicates represented by passing targets

M2-VER-15 ... M2-VER-19
    exact target membership
    focused results

harness closure
    independent sessions
    phase vocabulary
    pg_blocking_pids evidence
    positive progress evidence
    SQLSTATE capture

all focused commands and results
full PostgreSQL concurrency result
non-PostgreSQL result
full-suite result
CPython / PostgreSQL / uv versions
skip / xfail / rerun / 40P01 census
schema / migration / dependency / uv.lock unchanged statement
exact 63-operation business surface
absence of M2-S04 and later capabilities
status = CANDIDATE READY FOR REVIEW or honest partial state
```

Do not state that no finding remains merely because the full suite passes. Explicitly demonstrate every S03 completion condition and allow the reviewer to decide whether the slice is `COMPLETED`.
