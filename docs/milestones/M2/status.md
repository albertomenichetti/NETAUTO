# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S03 CANDIDATE READY FOR REVIEW

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S03 — CANDIDATE READY FOR REVIEW
current task    reviewer inspection of the published corrected candidate
blockers        reviewer decision pending; M2-S04 remains blocked
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | `M2-S03` CANDIDATE READY FOR REVIEW |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | COMPLETED | `M2-S00 COMPLETED` |
| `M2-S02` | COMPLETED | `M2-S01 COMPLETED` |
| `M2-S03` | CANDIDATE READY FOR REVIEW | `M2-S02 COMPLETED` |
| `M2-S04` | BLOCKED | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00`, `M2-S01` and `M2-S02` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Reviewed findings and corrected-candidate disposition

No contract, architecture, implementation-planning, technology or infrastructure contradiction is open. The reviewer inspection resolved the implementer-raised execution-aid finding and identified three bounded implementation/evidence defects. Corrective commit `2e8edb707c7f9f0c343532cf18426b70ae215ad4` implements all three inside `M2-S03`; reviewer acceptance remains pending.

The detailed findings below remain preserved as reviewer-owned history. Their candidate dispositions do not self-assign `COMPLETED` or reviewer acceptance.

### Resolution of `S03-FINDING-01` — REF-08 target-delete-first outcome

Reviewer determination:

```text
finding class
    non-normative execution-aid defect; no architecture reopen

frozen semantic authority
    cross-aggregate reference lifetime follows one serial order;
    a delete that observes an already-persisted blocker may return the
    conservative delete_blocked outcome

frozen persistence authority
    the eligible source ObjectTemplateVersion already owns immediate RESTRICT
    references to the cloned parent OTV, component root or property DTV

valid delete-starts-first interleaving
    target root DELETE obtains its gate/root owner and reads blockers
    -> source reference prevents target deletion
    -> DELETE returns delete_blocked and rolls back
    -> waiting OT.CREATE_NEXT obtains cloned-target KS lifetime holds
    -> one complete clone may commit
```

The sentence in `M2-S03-codex-prompt.md` requiring the target to disappear and the clone to fail is superseded for `REF-08`. It cannot override the frozen matrix, persistence model or verification registry. The implemented `delete_blocked` outcome is authority-compatible. The review-fix execution aid must preserve that outcome rather than reopening schema or weakening FK lifetime.

### `S03-RF-01` — exact scenario-to-recipe registry

Candidate disposition: one delivered projection, one explicit M2 addition projection and the sole `ARB-07` M2 delta now compose an exact 83-entry registry. Permanent equality evidence covers every primary and secondary recipe; every former mismatch listed below is corrected.

Prior reviewed state: the original candidate provided all 83 scenario IDs and non-empty collected target sets, but `M2_SCENARIO_TO_RECIPES` was derived primarily from one generic recipe per family and only a small override set. This silently changed the delivered canonical orchestration ownership instead of composing the current AS-IS registry with the explicit M2 additions.

Observed mismatches include, at minimum:

```text
ROW-10
    candidate generic mapping  REC-LOCK
    frozen mapping             REC-CUT

ARB-03 / ARB-04
    candidate generic mapping  REC-UNIQUE
    frozen mapping             REC-LOCK

ARB-05
    frozen REC-UNIQUE + REC-ABA is not preserved

ARB-06
    candidate primary REC-ABA replaces frozen REC-LOCK

ARB-07
    winner-disappearance restart is represented, but the delivered UNIQUE
    arbitration variant is no longer represented in the recipe set

GATE-02 / GATE-06
    the required REC-CUT secondary variants are omitted

ATOMIC-02
    the composite UNIQUE + ROLLBACK realization is reduced to the generic
    ATOMIC family recipe

PAR-03 / PAR-04 / PAR-07
    required lock/gate/mixed lock-progress recipes are replaced by the generic
    PAR progress recipe
```

Required correction:

```text
compose one exact 83-scenario recipe registry from:
    delivered canonical recipe ownership
    + explicit M2 scenario additions
    + explicit M2 recipe deltas only

represent exactly one primary recipe and every required secondary recipe
preserve delivered recipes when M2 changes only the semantic result
add a machine-checkable exact-equality regression for all 83 entries
retain stable scenario IDs and all currently passing concrete targets
```

A registry that merely checks that recipe names belong to the allowed vocabulary is insufficient.

### `S03-RF-02` — complete T3 SQLSTATE/outcome capture

Candidate disposition: the shared blocking/progress helpers and all custom canonical semantic-worker paths now use one structured, SQLSTATE-aware outcome ledger. Runtime collection fails mapped targets on a bypass, incomplete scenario representation, invalid worker role, missing transaction outcome, `40P01` or unexpected `40001`. Structural extraction, raw driver observation, no-retry controls and restart identities have permanent focused evidence.

Prior reviewed state: the original candidate introduced `WorkerOutcome` and `capture_worker_outcome`, but the shared `blocked_race()` and `progress_race()` helpers still executed workers through the legacy `capture()` boundary. Almost all canonical T3 targets therefore did not pass through the new structured capture path; the boundary was exercised only by a narrow subset of S03 evidence.

The frozen verification contract requires every T3 worker result to retain PostgreSQL SQLSTATE when present. A full-suite pass does not by itself prove the reported all-scenario SQLSTATE census, especially when a database failure can be translated into an `ApplicationFailure` before the outer harness observes it.

Required correction:

```text
integrate one structured outcome boundary into the shared deterministic T3
orchestration used by the complete scenario ledger

capture for every semantic worker:
    returned value
    ApplicationFailure
    unexpected exception
    PostgreSQL SQLSTATE when present, including wrapped DBAPI material
    last production/test phase
    commit or rollback outcome

preserve normal production failure mapping
fail every supported target immediately on 40P01
prove 40P01 and 40001 are not retried
execute the complete deduplicated 83-scenario target ledger through the
SQLSTATE-aware boundary and report every observed SQLSTATE value
```

Compatibility helpers may preserve existing convenient return shapes, but they must not bypass the authoritative outcome ledger.

### `S03-RF-03` — complete REF-08 cloned-state evidence

Candidate disposition: all six variants compare the complete persisted source and clone domain projections, exact two-version set, complete declarations, target root/exact target survival, KS lifetime modes and absence of PUBLISHED-admission SHARE.

Prior reviewed state: the six real-PostgreSQL `REF-08` variants correctly proved both physical operation orders, `delete_blocked`, version allocation and KS rather than SHARE lifetime modes. They did not, however, assert the cloned parent/component/property content.

As written, a defect that creates version 2 but omits one or all cloned declarations could still satisfy the target. This leaves the scenario's complete-clone and no-partial-aggregate obligation unproved.

Required correction for both `clone-first` and `delete-first` and for all three shapes:

```text
parent
    source and clone retain the exact parent template/version pin

component
    source and clone retain the complete component declaration and target root

property
    source and clone retain the complete property declaration, exact DTV pin,
    value mode and all persisted declaration fields

all variants
    source generation remains unchanged
    target root/exact version remains present after delete_blocked
    exactly one complete new version exists
    no partial declaration set survives
    clone plan uses KS and never PUBLISHED-admission SHARE for historical pins
```

The correct delete-starts-first result remains `delete_blocked` followed by a complete clone; no schema or production-semantic change is authorized.

`M2-S04` remains blocked pending reviewer acceptance of this corrected `M2-S03 CANDIDATE READY FOR REVIEW`.

## M2-S03 corrected candidate record

Candidate state:

```text
M2-S03                         CANDIDATE READY FOR REVIEW
reviewer decision              pending
corrective baseline            8ddcfdca85e73b64c5e3bc603d8611d0ffb2eb1c
review-fix prompt              96145aa7621bac760b0ce57c21f62e9c9f4df0fd
corrective implementation      2e8edb707c7f9f0c343532cf18426b70ae215ad4
candidate evidence/status      recorded by the following status commit
M2-S04                         BLOCKED / not started
```

Corrective dispositions:

```text
S03-RF-01
    83 / 83 exact recipe entries
    delivered projection + explicit M2 additions + one ARB-07 delta
    former mismatches corrected exactly:
        ROW-10 CUT
        ARB-03/04 LOCK
        ARB-05 UNIQUE + ABA
        ARB-06 LOCK
        ARB-07 ABA + UNIQUE + RESTART
        GATE-02/06 GATE + CUT
        ATOMIC-02 UNIQUE + ROLLBACK
        PAR-03 LOCK; PAR-04 GATE; PAR-07 LOCK + PROGRESS

S03-RF-02
    shared blocked/progress compatibility helpers delegate to structured forms
    all mapped semantic-worker paths are runtime-checked for ledger coverage
    structural SQLSTATE traversal covers sqlstate, pgcode, orig,
        driver_exception, cause/context and cycles
    raw SQLAlchemy/DBAPI SQLSTATE is observed before production mapping
    every canonical outcome retains node, scenario IDs, role, semantic result,
        failure/exception material, phase, transaction result and UoW identities
    PLAN-03 outcome records two distinct UoWs and ROLLED_BACK -> COMMITTED
    40P01 / 40001 no-retry controls execute exactly one attempt

S03-RF-03
    six REF-08 variants pass: parent/component/property x clone/delete first
    source is unchanged; clone is complete v2 DRAFT revision 1
    exact version set is source v1 + clone v2; no extra declaration survives
    parent/component/property values compare as complete domain projections
    referenced root and exact version, where applicable, remain present
    delete result is delete_blocked; clone targets use KS and never SHARE
```

Exact registry execution:

```text
S03 review-fix registry        19 selectors; 22 passed; 13.57s
41-mutation ledger             41 / 41; 72 selectors; 74 passed; 47.92s
83-scenario ledger             83 / 83; 165 selectors; 189 passed; 102.69s
semantic-worker outcomes       314 exact
transaction outcomes           215 COMMITTED; 93 ROLLED_BACK; 6 no-UoW
semantic scenario IDs          80 with semantic workers;
                               PLAN-01/02/04 are non-semantic planner evidence
21-predicate ledger            21 / 21; 136 selectors; 140 passed; 90.74s
M2-VER-15 ... M2-VER-19        5 / 5; 62 selectors; 67 passed; 41.38s
```

Canonical supported-path SQLSTATE census from the exact 83-scenario ledger:

```text
23505                           8
23503                           1
40P01                           0
unexpected 40001                0

ARB-01 / datatype semantic create / T1                         23505 x1
ARB-05 / reciprocal create / T2                                23505 x1
ARB-05 / symmetric inverse-overlap [False] / T2                23505 x1
ARB-05 / symmetric inverse-overlap [True] / T2                 23505 x1
ARB-07 + PLAN-05 / winner disappears / T2                      23505 x1
ARB-07 + PLAN-05 / collision-owner delete block / T2           23505 x1
ARB-08 + ROW-30 / factual partial-owner conflict / T2           23505 x1
ATOMIC-02 / later closure collision / T1                       23505 x1
REF-06 / definition cascade versus relationship RESTRICT / T1  23503 x1
```

The focused negative-control census is separate from supported paths:

```text
negative-control outcomes      3
40P01                           1; immediate harness failure; one attempt
40001                           2; immediate/no-retry and intentional capture;
                                one attempt each
```

Mandatory verification:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS (173 files)
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
uv run pytest --collect-only -q                             PASS (446; 1.60s)
focused S03 review-fix registry                             PASS (22; 13.57s)
M1/S00/M2 traceability                                      PASS (19; 13.08s)
complete semantic concurrency modules                       PASS (189; 120.07s)
M2 locking pure/PostgreSQL                                  PASS (40; 5.25s)
schema metadata / migrations                                PASS (5; 1.98s)
exact 63-operation object-scope boundary                    PASS (5; 2.83s)
PLAN-03 structured restart identities                       PASS (1; 1.86s)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (182; 264 deselected;
                                                                  114.04s)
uv run pytest -q -m "not postgresql" -ra                    PASS (205; 241 deselected;
                                                                  16.85s)
uv run pytest -q -ra                                        PASS (446; 182.83s)
```

All reported runs have zero skips, xfails and reruns. Runtime versions were CPython `3.14.7`, PostgreSQL `16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)` and uv `0.12.3`.

Unchanged boundaries:

```text
authoritative tables         15
Alembic graph                one base / one head: 0001_m2_kernel
metadata drift               compare_metadata == []
schema / migration diff      none
dependency / uv.lock diff    none
business HTTP operations     41 mutations + 22 reads = 63 exact
production/public surface    unchanged
Health/startup/CLI/packaging no new surface
M2-S04                       not started
Actions/encoded payloads     absent
```

## M2-S03 reviewed implementation record

Reviewer result:

```text
M2-S03                         REVIEW CHANGES REQUIRED
starting reviewer baseline     850abd97ece1aadeae65aa090d86c7ec4982751f
implementation prompt          29e490087b24f1ff17d1e4be1abc629b0be3a962
published implementation       f70ec8968ddef3bd106749b14def0e5cde9688e3
partial evidence/status        1c2dd13b6e5e57310db6f12f0a6d8307c35bda67
resolved implementer finding   S03-FINDING-01 — execution-aid defect
open reviewer findings         S03-RF-01, S03-RF-02, S03-RF-03
M2-S04                         BLOCKED / not started
durable revision               0001_m2_kernel (unchanged)
Alembic graph                  one base / one head
authoritative table census     15
metadata drift                 compare_metadata == []
business HTTP operations       63 exact
CPython                        3.14.7
PostgreSQL                     16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                             0.12.3
```

Implemented material to preserve:

```text
mutation plans                 41 / 41; 10 DT + 10 OT + 7 OBJ + 10 RD + 4 REL
advisory gates                 3 exact keys; 6 gated mutations; all others ungated
row-lock modes                 KS / S / NKU / U; canonical class/order assertions
mutation evidence              72 unique selectors; 74 passed

scenario IDs                   83 / 83
family census                  ROW 30; ARB 8; REF 11; GATE 7; SNAP 5;
                               ATOMIC 7; PAR 9; PLAN 6
scenario target ledger         165 unique selectors; 189 nodes passed
predicate registry             21 / 21 with the frozen scenario mapping
M2-VER-15 ... M2-VER-19        IMPLEMENTED; 62 selectors; 67 passed

new/strengthened targets       REF-08, REF-09, REF-10, REF-11, GATE-07,
                               PAR-08, PAR-09, ROW-03/04/16 and SNAP-01/02
phase vocabulary               exact 19 canonical phases plus one thin delivered alias
```

Implementer-reported verification:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS (172 files)
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
uv run pytest --collect-only -q                             PASS (442, 1.37s)
M2 mutation target ledger                                   PASS (74, 50.57s)
M2 exact scenario target ledger                             PASS (189, 107.85s)
M2-VER-15 ... M2-VER-19 target ledger                       PASS (67, 42.93s)
M1/S00/M2 traceability                                      PASS (18, 12.72s)
complete semantic concurrency modules                       PASS (186, 116.47s)
M2 locking pure/PostgreSQL                                  PASS (40, 5.00s)
schema metadata / migrations                                PASS (5, 1.75s)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (182; 260 deselected;
                                                                  113.91s)
uv run pytest -q -m "not postgresql" -ra                    PASS (201; 241 deselected;
                                                                  15.36s)
uv run pytest -q -ra                                        PASS (442, 166.67s)
```

The reported run has zero skips, xfails and reruns, and no raw `40P01` was reported. The reviewer did not re-execute the 442-test suite in this inspection. The results remain useful candidate evidence but do not close the three gaps above.

Unchanged boundaries reported and confirmed by the published delta:

```text
15 authoritative tables; one Alembic base/head; 0001_m2_kernel unchanged
schema metadata and migration files unchanged; compare_metadata == []
pyproject.toml and uv.lock unchanged
41 mutations + 22 reads = 63 exact business HTTP operations
no Health/startup/CLI/packaging/M2-S04 capability introduced
obsolete GitHub Actions and encoded publication payload material remain absent
```

## M2-S02 completion record

Reviewer result:

```text
M2-S02                         COMPLETED
original prompt                9f4ed2ef69efdfbb6bc0e79dfc14c979f4f0f66d
original implementation        99b6d32d1ab9f3529881eb2e16809e01ea5b2be2
original candidate evidence    66d9d47dab97c2b42b63ed015261d65ccf1abc16
original provenance            9400502acc99b7c959cc5070cd97914b2ace7087
review changes record          4c1ae6905295ed1f7f69f71ecd9af7e76d1ca47f
review-fix prompt               98e8a092b27afeb50cbadd07c6356349958ddf88
corrective implementation      f27d13c6d8366e46c9ad3fb2b07ede735be0ff3e
corrected candidate evidence   6eb21c0fbc58728f075ff3674f039b68bb626ef0
corrected provenance           39d4b6b0a6fb0fae86525ec8bd56cad6df0ccbeb
full suite                     PASS (411)
```

No blocking review finding remains open for `M2-S02`.

## M2-S01 completion record

Reviewer result:

```text
M2-S01                         COMPLETED
original implementation       c019cada4152e9798e25476d35b0cec5127d6135
original candidate status     63c0e772df4c73c439b7b4baed67b3d11fc809b9
review changes record         e5728486ace14bf525fa3f5df51d7c18e87b957c
corrective prompt              4a35581769feb0791a9eca1aa795c1fd0f95aa5c
corrective implementation      46afa3341d292fb1790612456b28689eafb5b694
corrective evidence/status     6d8a0838530f2b449c598dc545a0a2ad3577c5d3
publication provenance         63e7be04d8880ec5ea79289fd6b0462babe5ab40
full suite                     PASS (349)
```

No blocking review finding remains open for `M2-S01`.

## M2-S00 completion record

Reviewer result:

```text
M2-S00                         COMPLETED
initial implementation         328fe179dade3a30168cb2e14dbbb5042a82e463
corrective implementation      7950fc041fb8fdb62bfaf72bdcfe40fff2af8dab
candidate evidence/status      8168aeb3a8a3e1dedd97afcd22f9da314d689333
full suite                     PASS (314)
```

No blocking review finding remains open for `M2-S00`.

## Immediate next action

Reviewer inspection of the published corrected candidate for:

```text
M2-S03 — S03-RF-01, S03-RF-02 and S03-RF-03
```

The correction remains inside the same slice. The reviewer decides whether the candidate closes `S03-RF-01`, `S03-RF-02` and `S03-RF-03`. Do not start `M2-S04` unless `M2-S03 COMPLETED` is authoritatively recorded by the reviewer.

## Current status vocabulary

```text
READY
    -> authorized to start after mandatory pre-flight

IN PROGRESS
    -> implementer work is active inside the exact slice scope

CANDIDATE READY FOR REVIEW
    -> implementation/evidence candidate published; reviewer decision pending

REVIEW CHANGES REQUIRED
    -> reviewer-owned result; bounded corrections remain in the same slice

COMPLETED
    -> reviewer-owned acceptance of the slice

BLOCKED
    -> dependency, infrastructure or authority condition prevents start/progress

FINAL / FROZEN
    -> normative authority; change requires formal reopening

NOT STARTED
    -> gate or activity has not begun

NOT AUTHORIZED
    -> activity must not begin

NOT DELIVERED
    -> final gate and closure have not completed
```

`M2-S09`, milestone delivery and merge remain reviewer/human-owned according to project governance.
