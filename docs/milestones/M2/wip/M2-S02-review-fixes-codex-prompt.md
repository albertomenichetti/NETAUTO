# Codex review-fix prompt — M2-S02

**Status:** NON-NORMATIVE REVIEW-FIX IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It narrows the authorized corrective task but does not override `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract, architecture or steps, the active milestone status, the ratified technology baseline, or the reviewer findings recorded in `docs/milestones/M2/status.md`.

## Assignment

Correct exactly these reviewer-owned findings inside the existing slice:

```text
M2-S02 — Factual Relationship mutations, lifecycle and coherent reads

S02-RF-01 — canonical S02 concurrency evidence is incomplete
S02-RF-02 — S02 bundle traceability overstates lifecycle evidence closure
S02-RF-03 — new S02 read paths retain preventable unbounded/N+1 work
```

Work directly on branch:

```text
M2
```

The reviewer-owned corrective baseline is:

```text
4c1ae6905295ed1f7f69f71ecd9af7e76d1ca47f
docs(m2): require S02 review fixes
```

The reviewed candidate lineage is:

```text
prompt baseline                 9f4ed2ef69efdfbb6bc0e79dfc14c979f4f0f66d
S02 implementation              99b6d32d1ab9f3529881eb2e16809e01ea5b2be2
candidate evidence/status       66d9d47dab97c2b42b63ed015261d65ccf1abc16
publication provenance          9400502acc99b7c959cc5070cd97914b2ace7087
review changes record           4c1ae6905295ed1f7f69f71ecd9af7e76d1ca47f
```

Start from the current `origin/M2` tip containing this prompt. That tip must be `4c1ae690...` or a direct descendant. Do not reset, rebase, force-push or rewrite the published S00/S01/S02 history.

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    REVIEW CHANGES REQUIRED — bounded correction authorized
M2-S03    BLOCKED
```

The publication action is:

```text
perform the mandatory repository pre-flight
preserve every conforming S02 capability
correct S02-RF-01, S02-RF-02 and S02-RF-03 completely
add permanent deterministic evidence
run every focused and complete mandatory gate
commit intentionally
push normally to origin/M2
verify local/remote synchronization and a clean working tree
publish a corrected M2-S02 candidate for reviewer inspection
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
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/api.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
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

# Active execution aids
docs/milestones/M2/wip/M2-S02-codex-prompt.md
docs/milestones/M2/wip/M2-S02-review-fixes-codex-prompt.md
```

Read owning sections dependency-first. Frozen documents are authority. These prompts are execution aids only. Do not derive implementation requirements from historical discovery or cross-check material under `docs/milestones/M2/wip/`; `architecture/provenance.md` removes those files from implementation authority.

Confirm from the repository itself that:

```text
checked-out branch                  = M2
README active cycle                 = M2 / IMPLEMENTATION / branch M2
origin/M2 ancestry                  includes 4c1ae690...
M2 contract                         = FINAL / FROZEN
M2 architecture set                 = FINAL / FROZEN
M2 steps                            = FINAL / FROZEN
M2-S00                              = reviewer-owned COMPLETED
M2-S01                              = reviewer-owned COMPLETED
M2-S02                              = REVIEW CHANGES REQUIRED or IN PROGRESS
M2-S03                              = BLOCKED
open review findings                = exactly S02-RF-01 ... S02-RF-03
relevant architecture reopen        = none
STACK-01 ... STACK-10               = RATIFIED
```

Inspect at least these current implementation/evidence boundaries before editing:

```text
src/netauto/domain/relationships.py
src/netauto/application/relationships.py
src/netauto/application/relationshipdefinitions.py
src/netauto/persistence/lifecycle.py
src/netauto/persistence/relationships.py
src/netauto/persistence/locking.py
src/netauto/persistence/uow.py

tests/test_m2_s02_relationship_domain.py
tests/test_m2_s02_semantic_concurrency.py
tests/test_m2_traceability.py
tests/test_relationship_api.py
tests/test_relationship_semantic_concurrency.py
tests/support/semantic_concurrency.py
tests/support/pg_harness.py
```

Search the complete repository for current uses of:

```text
certified_set
published_history
get_version
get_versions
RelationshipDefinitionStore
RelationshipDefinitionVersionStore
pg_blocking_pids
ROW-26 ... ROW-30
REF-10
M2-VER-12
M2-VER-14
```

Verify that the conforming S02 candidate is present before changing it:

```text
Relationship.DATA_CHANGE                       implemented
Relationship.SCHEMA_CHANGE                     implemented
LifecycleStore sole lifecycle SQL authority    implemented
coherent Relationship/lifecycle reads           implemented
63 exact business HTTP operations               implemented
schema                                           exactly 15 tables
Alembic graph                                    one base / one head
metadata drift                                   []
```

A valid externally supplied real PostgreSQL target through `TEST_DATABASE_URL` is mandatory for a corrected candidate. Verify availability during pre-flight. Do not provision PostgreSQL, use Docker/Testcontainers, invent credentials, fall back to localhost, fall back to `NETAUTO_DATABASE_URL`, or substitute SQLite.

If README, branch, `status.md`, frozen authorities, ancestry or required infrastructure disagree, stop before modifying the affected work and report the mismatch. If normative authorities conflict or do not determine one material behavior, stop only the affected point and report an architecture/documentation finding. Do not silently select a convenient interpretation.

---

# 2. Scope and hard boundary

This task is a bounded review correction. Preserve every conforming element of the published S02 candidate.

## 2.1 Explicitly in scope

```text
real second-winner-order T3 evidence for ROW-30 and REF-10
missing lifecycle/closure assertions in ROW-26, ROW-27 and ROW-28
machine-resolvable parameter variants under the existing stable scenario IDs
M2-VER-12 valid four-transition lifecycle-shape traceability
M2-VER-14 historical-independence traceability
set-based represented-Definition loading for Object-relative pages
set-based PUBLISHED/DEPRECATED RDV history loading
query-shape/count regression evidence for both bounded loaders
status/evidence update for a corrected S02 candidate
complete regression closure
```

## 2.2 Explicitly out of scope

Do not introduce or implement:

```text
M2-S03 complete 861-cell concurrency closure beyond these S02 corrections
Core Health
startup schema-revision guard
runtime settings or pool changes
CLI or REPL
packaging/Linux operating capability
native authentication, authorization or TLS termination
new advisory gates
new row-lock modes
new retry causes or generic retry middleware
new public business routes
Relationship endpoint mutation/reversal/move
bulk mutation, PATCH or generic action APIs
property-value search or runtime-property indexing
standalone Relationship lifecycle timeline
event-set resource or event_set_id
M1 -> M2 bridge, backfill, stamp path or dual decoder
```

No schema, migration, dependency or `uv.lock` change is expected or authorized. Preserve:

```text
src/netauto/persistence/metadata.py table/constraint/index meaning
src/netauto/migrations/ durable root graph
pyproject.toml dependency set
uv.lock
```

If a schema, migration or dependency change appears necessary, stop and identify the exact frozen authority requiring it. Do not alter the durable baseline for implementation convenience.

Do not modify the frozen contract, architecture or `steps.md` to fit code. Do not weaken, delete, rename away or relax existing passing S00/S01/S02 regressions.

---

# 3. Shared correctness constraints

Every correction must preserve:

```text
one semantic mutation / one UoW / one connection / one transaction
READ COMMITTED mutation baseline
REPEATABLE READ READ ONLY coherent-read boundary
central prepare_lock_plan / LockPlan authority
three frozen transaction advisory gates only
four frozen PostgreSQL row-lock modes only
canonical class and intra-class order
gate before rows
one complete pre-DML acquisition phase
fresh protected reread after waits
no normal lock upgrade
no explicit post-DML lock
finite SQLSTATE + constraint-name classification
four total attempts only for the two frozen restart causes
no retry of 40P01 or 40001
one complete current-state + event-set commit or rollback
no SQL, constraint, table, column, URL, credential or stack leakage
```

Preserve exact S02 semantics:

```text
DATA_CHANGE no-op performs no UPDATE and emits no event
DATA_CHANGE preserves pin and closure
SCHEMA_CHANGE uses Definition KS -> target RDV S -> Relationship NKU
SCHEMA_CHANGE is explicit, same-Definition, forward and PUBLISHED-through-commit
SCHEMA_CHANGE atomically updates pin + properties and preserves closure
all four factual transitions use LifecycleStore
current and historical reads remain corruption-safe
public business operation inventory remains exactly 63
```

Application/domain modules remain free of FastAPI, Pydantic, SQLAlchemy and Psycopg imports. Stores do not commit or open nested semantic transactions.

---

# 4. S02-RF-01 — complete canonical T3 evidence

The production paths are not to be redesigned merely to make tests convenient. Correct the deterministic evidence so it proves the frozen interleavings and exact outcomes.

## 4.1 ROW-30 — real deprecator-first interleaving

Retain the existing SCHEMA_CHANGE-first variant and add a genuine overlapping deprecator-first variant using independent semantic sessions/UoWs.

Required deprecator-first recipe:

```text
T1 RDV.DEPRECATE
    -> acquire the target RDV lifecycle owner lock
    -> pause while the transaction remains open before commit

T2 REL.SCHEMA_CHANGE
    -> acquire every earlier compatible planned row, as applicable
    -> wait on target RDV SHARE before the factual Relationship owner

OBS
    -> prove pg_blocking_pids(T2_pid) contains T1_pid
    -> prove T2 has not acquired the factual Relationship owner lock while waiting

release T1
    -> deprecation commits

T2 wakes
    -> performs fresh protected reread
    -> observes target no longer PUBLISHED
    -> returns dependency_not_admissible
    -> leaves factual pin/properties/closure unchanged
    -> writes no SCHEMA_CHANGE event
```

Use the actual production DEPRECATE and SCHEMA_CHANGE paths. Do not model the second winner order by pre-deprecating sequentially. Do not issue semantic SQL from the controller or interceptor.

For the retained SCHEMA_CHANGE-first variant assert at least:

```text
real required blocking between independent sessions
SCHEMA_CHANGE commits against the PUBLISHED target
RDV deprecation subsequently completes with its frozen semantics
current fact remains valid on the exact now-DEPRECATED target
one exact SCHEMA_CHANGE event set exists
closure is unchanged
no 40P01
```

Preserve the stable scenario ID `ROW-30`. Expose both winner-order variants as machine-resolvable targets, either through explicit test functions or stable parametrized node IDs.

## 4.2 REF-10 — real root-delete-first interleaving

Retain the existing SCHEMA_CHANGE-first variant and replace the sequential pseudo delete-first case with a genuine overlapping root-delete-first variant using independent semantic sessions/UoWs.

Required root-delete-first recipe:

```text
T1 RD.DELETE_DEFINITION
    -> acquire MODEL_ROOT_DELETE_GATE
    -> acquire Definition root UPDATE
    -> pause before the fresh blocker decision completes

T2 REL.SCHEMA_CHANGE
    -> attempt Definition KEY SHARE first
    -> wait before target RDV and factual Relationship owner acquisition

OBS
    -> prove pg_blocking_pids(T2_pid) contains T1_pid
    -> prove the waiter does not hold the factual Relationship owner row

release T1
    -> fresh blocker read observes the current factual Relationship
    -> DELETE returns bounded delete_blocked
    -> the failed semantic UoW rolls back/releases its gate and root lock

T2 wakes
    -> rereads the live Definition/target/fact
    -> completes the valid SCHEMA_CHANGE
    -> preserves closure
    -> emits one exact event set
```

Required final assertions:

```text
DELETE details are the exact bounded public blocker result
Definition and target remain current after the blocked delete
Relationship exact pin/properties equal the admitted target result
runtime closure keys equal the pre-race keys
no partial model/factual/event state
no 40P01
```

For the retained SCHEMA_CHANGE-first variant prove the root DELETE waiter relationship with `pg_blocking_pids()`, then prove the fresh post-wait `delete_blocked` outcome and exact final factual/event state.

Preserve the stable scenario ID `REF-10`. Expose both winner-order variants as machine-resolvable targets.

## 4.3 Strengthen ROW-26

In addition to the existing no-lost-update, update-count and waiter-no-op assertions, permanently assert the exact factual state carried by every real DATA_CHANGE event row.

For each committed transition verify:

```text
kind = RELATIONSHIP_DATA_CHANGE
before.relationship_definition_version == after.relationship_definition_version
before.properties == the fresh state immediately before that transition
after.properties == the complete canonical state immediately after that transition
fan-out rows for one transition carry identical before/after state
pin and closure remain unchanged
```

For the waiter that becomes a semantic no-op verify:

```text
no owner-row UPDATE
no additional DATA_CHANGE event row
returned state equals the fresh committed state
```

Do not rely only on event cardinality.

## 4.4 Strengthen ROW-27

For both winner orders, assert the complete serial factual history rather than only final state and counts.

Expected semantic sequences are:

```text
DATA_CHANGE first
    v1 / old properties
        -> DATA_CHANGE
    v1 / changed properties
        -> SCHEMA_CHANGE
    v2 / migrated changed properties

SCHEMA_CHANGE first
    v1 / old properties
        -> SCHEMA_CHANGE
    v2 / migrated old properties
        -> DATA_CHANGE
    v2 / changed properties
```

Group the fan-out rows into their two semantic transitions using durable transition facts such as transaction timestamp, kind and identical before/after state; there is no `event_set_id` and none may be introduced. Assert deterministic transition ordering, complete identical state across each fan-out, exact final state and unchanged closure.

## 4.5 Strengthen ROW-28

Cover and assert both serial possibilities:

```text
lower forward target wins first
    -> source v1 -> target v2 event
    -> fresh target v2 -> target v3 event
    -> both operations succeed

higher forward target wins first
    -> source v1 -> target v3 event
    -> waiting lower target becomes non-forward
    -> exact semantic_validation_failed result
    -> no second SCHEMA_CHANGE event
```

For both variants assert:

```text
complete runtime closure unchanged
exact event before/after versions and properties
fresh source pin used after wake-up
no stale-source migration
no partial current/event state
no 40P01
```

## 4.6 Harness and registry rules

Use the existing deterministic harness and phase vocabulary. A test-only interceptor may observe or pause a named production phase but may not:

```text
change candidate data
issue semantic SQL
acquire production locks
change isolation
commit or rollback
change failure mapping
select another production path
use sleep as ordering authority
```

Required blocking is proved primarily by:

```text
pg_blocking_pids(waiter_pid) contains known blocker_pid
```

Required progress is proved by a positive production phase reached while the other transaction remains open. Timeouts are hang guards only.

Every worker captures SQLSTATE when present. Any supported-path `40P01` fails the target and blocks candidate readiness; it is never retried.

Update `tests/test_m2_traceability.py` so every new winner-order/strengthened target remains machine-resolvable under the existing stable IDs. Do not create replacement scenario IDs.

---

# 5. S02-RF-02 — repair lifecycle bundle traceability

The implementation behavior may reuse existing concrete tests, but each mandatory bundle obligation must be linked explicitly in its own machine-checkable target set.

## 5.1 M2-VER-12

Ensure `M2-VER-12` maps at least one real collected end-to-end target that proves all valid factual transition shapes:

```text
RELATIONSHIP_CREATED
    before = null
    after  = exact factual state

RELATIONSHIP_DATA_CHANGE
    before/after factual
    same exact version
    different complete properties

RELATIONSHIP_SCHEMA_CHANGE
    before/after factual
    strictly forward exact version
    properties may be equal or different

RELATIONSHIP_DELETED
    before = final exact factual state
    after  = null
```

The existing broad Relationship API lifecycle test may be reused if it asserts all four valid shapes explicitly. If its assertions are insufficient or too indirect, add one narrowly focused valid-transition test instead of inferring PASS from unrelated targets.

Keep the existing invalid-carrier, invalid-transition and corrupt-page targets. Valid and invalid codec evidence are both required.

## 5.2 M2-VER-14

Ensure `M2-VER-14` maps a real collected historical-independence target that proves global Relationship history remains readable after deletion of current resources, including:

```text
factual Relationship and closure
RelationshipDefinition and owned RDVs/declarations
referenced DataType lineage/versions when no current blocker remains
endpoint Objects
```

The target must prove historical decoding performs no live RDV/DTV/Object lookup and preserves historical names and exact factual snapshots. It must also preserve the frozen distinction:

```text
global lifecycle route
    -> history remains readable without current resources

Object-specific lifecycle route
    -> current path Object is still required
```

The existing end-to-end historical test may be reused if these assertions are explicit. Otherwise add a focused target.

Keep the sole-LifecycleStore and all four atomic rollback targets already mapped to `M2-VER-14`.

## 5.3 Machine-checkable closure

Update the registry and its own assertions so that:

```text
M2-VER-12 includes valid four-transition shape evidence
M2-VER-14 includes historical-independence evidence
every mapped node ID resolves to a collected test
no target is a placeholder or source-introspection substitute for runtime behavior
S01 registries and review-fix targets remain unchanged
PLAN-01 ... PLAN-06 remain unchanged
16 outcomes remain exact
32 acceptance criteria remain exact
32 evidence bundles remain exact
83 canonical scenarios remain exact
```

Preserve the existing registry state vocabulary. Runtime execution records PASS; the source registry continues to use its established `IMPLEMENTED`/`DESIGNED` distinction unless a frozen authority says otherwise.

---

# 6. S02-RF-03 — remove unbounded and N+1 query paths

Correct the new S02 query behavior without weakening coherent-read or corruption validation.

## 6.1 Represented-Definition loader for Object-relative pages

Add a set-based stable RelationshipDefinition aggregate loader, for example:

```text
RelationshipDefinitionStore.get_many(definition_ids)
```

or an equivalent bounded method.

Requirements:

```text
input is the finite distinct Definition ID set represented by the current page
empty input returns an empty mapping without querying
one set-based aggregate read loads only those Definition headers and Resolutions
result is keyed by Definition ID
ordering remains deterministic
missing represented Definition is detectable as corruption
unrelated Definitions are not loaded
```

Use this loader in `RelationshipService._validated_many()` instead of `certified_set()`.

Preserve the rest of the page validation:

```text
one coherent REPEATABLE READ READ ONLY UoW
limit + 1 ordered semantic view identities
set-based factual aggregate loading
set-based exact RDV/declaration loading
set-based DTV loading
endpoint and closure validation
one ObjectTemplate parent-graph load at most per page
complete-page internal_error on one corrupt represented fact
cursor identity unchanged
```

Do not replace one full-model scan with one query per Definition.

## 6.2 Batched PUBLISHED/DEPRECATED RDV history

Replace the current per-version `published_history()` implementation with a bounded set-based loader.

Required semantics remain:

```text
same RelationshipDefinition only
statuses PUBLISHED and DEPRECATED
version ascending
complete version headers + complete declarations
no DRAFT member
historical continuity validation unchanged
```

Implementation requirements:

```text
no loop that calls get_version() once per historical version
headers loaded set-wise
declarations loaded set-wise or through one equivalent joined aggregate statement
query count remains constant with respect to history cardinality
missing/incoherent rows remain corruption, not silent omission
```

SCHEMA_CHANGE must use the batched history result while preserving:

```text
same lock plan
same fresh protected reread
same forward/PUBLISHED admission
same preserve-or-fail migration
same LockPlanStale behavior
same current/event atomicity
```

## 6.3 Permanent query-shape/count evidence

Add regressions that fail if either optimization is reversed.

### Page loader evidence

Prove at least:

```text
several unrelated Definitions exist
one page represents a strict subset
certified_set() is not called by the page path
only represented Definition IDs are passed to the bounded loader
one bounded Definition aggregate statement is used, not one per Definition
parent graph is loaded at most once for the page
page result and corruption behavior remain exact
```

Use real PostgreSQL for SQL/query-count claims. A narrow application-level spy may additionally assert method selection, but it cannot replace the persistence evidence.

### RDV history evidence

Prove at least:

```text
one Definition owns multiple PUBLISHED/DEPRECATED versions
published_history() returns the exact ordered complete snapshots
get_version() is not called once per history item
SQL statement count for the history loader is constant as history cardinality grows
SCHEMA_CHANGE still validates and migrates correctly through that loader
```

Count only the owned loader/query boundary rather than freezing unrelated total request statements or PostgreSQL planner details. The test must reject an N+1 reintroduction without becoming brittle to an equivalent one-query versus bounded-multi-query implementation.

Static AST/source assertions may supplement, but not replace, real execution evidence.

---

# 7. Required focused verification

At minimum, implement and run concrete targets for:

```text
S02-RF-01
    ROW-30 schema-first and real deprecator-first variants
    REF-10 schema-first and real root-delete-first variants
    strengthened ROW-26
    strengthened ROW-27, both orders
    strengthened ROW-28, both serial outcomes

S02-RF-02
    M2-VER-12 valid and invalid lifecycle shapes
    M2-VER-14 atomicity and historical independence
    exact traceability registry resolution

S02-RF-03
    represented-Definition bounded loader
    page path does not call certified_set
    one parent graph load at most
    batched ordered RDV history
    no get_version-per-history-item
    history query count independent of version count
```

Re-run all affected S02 evidence, including:

```text
M2-VER-08
M2-VER-09
M2-VER-11
M2-VER-12
M2-VER-13
M2-VER-14

ROW-26
ROW-27
ROW-28
ROW-29
ROW-30
REF-10
SNAP-05
ATOMIC-02
ATOMIC-03
ATOMIC-06
ATOMIC-07
```

Preserve and rerun the relevant S00/S01 planner, lifecycle, Relationship CREATE/DELETE, Object, schema and migration regressions.

Suggested command groups must be adapted to the actual added target locations, but the final executed gate must include at least:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright

uv run pytest -q tests/test_m2_s02_relationship_domain.py \
  tests/test_m2_traceability.py -ra

uv run pytest -q tests/test_m2_s02_semantic_concurrency.py -ra

uv run pytest -q tests/test_relationship_api.py \
  tests/test_relationship_semantic_concurrency.py \
  tests/test_object_api.py \
  tests/test_object_semantic_concurrency.py -ra

uv run pytest -q tests/test_schema_metadata.py \
  tests/test_migrations.py -ra

uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

The complete suite must execute with the externally supplied `TEST_DATABASE_URL` and include every PostgreSQL target.

Record:

```text
exact commands
pass counts and durations
CPython version
PostgreSQL server version
uv version
skip / xfail / rerun census
all observed worker SQLSTATE values or an explicit supported-path 40P01 census
```

No skip, xfail, deselection mistake, flaky rerun or timeout counts as PASS for an assigned requirement. Any supported scenario producing `40P01` blocks candidate readiness.

Verify unchanged boundaries explicitly:

```text
15 authoritative tables
one Alembic base / one head
0001_m2_kernel unchanged
compare_metadata == []
no schema or migration diff
no dependency or uv.lock diff
63 exact business HTTP operations
no Health/startup/CLI/packaging/M2-S03 surface
obsolete Actions/payload material remains absent
```

---

# 8. Status, commits and publication discipline

Keep both S02 execution aids under `docs/milestones/M2/wip/` while the slice remains unaccepted:

```text
M2-S02-codex-prompt.md
M2-S02-review-fixes-codex-prompt.md
```

Do not delete them. Their retirement is reviewer-owned after slice acceptance.

Use intentional commits. A suitable separation is:

```text
implementation/test corrections
candidate evidence/status
optional provenance-only status correction when the status commit SHA must be recorded
```

Do not manufacture extra commits solely to imitate that pattern when one clean implementation commit and one status commit suffice.

Only when every mandatory focused and complete gate passes may `docs/milestones/M2/status.md` be changed to:

```text
M2-S02 — CANDIDATE READY FOR REVIEW
reviewer decision pending
M2-S03 — BLOCKED
```

The corrected candidate record must include:

```text
review-fix prompt commit
corrective implementation commit
candidate evidence/status commit
publication provenance, when applicable
finding-by-finding disposition for S02-RF-01 ... 03
new exact target/node IDs
query-bound assertions and results
environment versions
focused and complete verification commands/counts/durations
skip/xfail/rerun and 40P01 census
unchanged schema/migration/dependency/public-surface statement
```

Codex must not declare `M2-S02 COMPLETED`. Acceptance remains reviewer-owned.

If any mandatory requirement remains unexecuted, any target fails, `TEST_DATABASE_URL` is unavailable, or a new architecture/documentation finding emerges:

```text
do not mark CANDIDATE READY FOR REVIEW
do not start M2-S03
retain REVIEW CHANGES REQUIRED or record an honest IN PROGRESS/STOP state
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

# 9. Required handoff

The final Codex handoff must report, without claiming reviewer acceptance:

```text
cycle / slice / branch
starting reviewer baseline
corrective implementation commit(s)
candidate status/provenance commit(s)
local/remote synchronization and clean tree

S02-RF-01 disposition
    exact real winner-order targets
    pg_blocking_pids evidence
    strengthened ROW-26/27/28 assertions

S02-RF-02 disposition
    exact M2-VER-12 target membership
    exact M2-VER-14 target membership
    registry census and resolution

S02-RF-03 disposition
    bounded Definition loader realization
    bounded RDV history realization
    query-shape/count target results

all focused commands and results
full PostgreSQL concurrency result
non-PostgreSQL result
full-suite result
CPython / PostgreSQL / uv versions
skip / xfail / rerun / 40P01 census
schema / migration / dependency / uv.lock unchanged statement
exact public operation inventory
absence of M2-S03 and later capabilities
status = CANDIDATE READY FOR REVIEW or honest partial state
```

Do not state that no finding remains merely because the full suite passes. Explicitly demonstrate closure of each recorded reviewer finding and allow the reviewer to decide completion.