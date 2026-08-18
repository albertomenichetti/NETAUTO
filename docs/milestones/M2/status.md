# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S04 READY

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S04 — READY
current task    prepare the M2-S04 Codex implementation prompt and execute the authorized slice
blockers        none
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | AUTHORIZED — `M2-S04` ONLY |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | COMPLETED | `M2-S00 COMPLETED` |
| `M2-S02` | COMPLETED | `M2-S01 COMPLETED` |
| `M2-S03` | COMPLETED | `M2-S02 COMPLETED` |
| `M2-S04` | READY | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00`, `M2-S01`, `M2-S02` and `M2-S03` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning, technology or verification blocker is open for starting `M2-S04`.

`M2-S04` requires the externally supplied real PostgreSQL target and runtime/lifespan evidence prescribed by its frozen authorities. No fallback database, invented credential, automatic migration path or alternate public behavior is authorized.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S03 completion record

Reviewer result:

```text
M2-S03                         COMPLETED
review acceptance              recorded by the commit containing this status
original prompt                29e490087b24f1ff17d1e4be1abc629b0be3a962
initial implementation         f70ec8968ddef3bd106749b14def0e5cde9688e3
partial evidence/status        1c2dd13b6e5e57310db6f12f0a6d8307c35bda67
review changes record          8ddcfdca85e73b64c5e3bc603d8611d0ffb2eb1c
review-fix prompt              96145aa7621bac760b0ce57c21f62e9c9f4df0fd
corrective implementation      2e8edb707c7f9f0c343532cf18426b70ae215ad4
corrected evidence/status      33803f1c50ced716490541099357e2d74eb742a8
corrected provenance           5f28678fd762fb0c3945747cc7c8d9ffbfa4be19
M2-S04                         READY / not started
```

Closed findings:

```text
S03-FINDING-01
    resolved as a non-normative execution-aid defect; no architecture reopen.
    REF-08 delete-starts-first preserves the frozen RESTRICT lifetime result:
    delete_blocked followed by one complete historical clone under KS holds.

S03-RF-01
    the exact 83-entry recipe registry now composes the delivered map,
    explicit M2 additions and the sole ARB-07 M2 recipe delta.
    Every primary and required secondary recipe has permanent exact-equality evidence.

S03-RF-02
    all mapped canonical semantic workers use one structured outcome ledger.
    The ledger retains node/scenario/role, semantic result, failure or exception,
    SQLSTATE, phase, transaction outcome and UoW identities; raw driver states are
    observed before production mapping. Supported 40P01 and unexpected 40001 fail.

S03-RF-03
    all six REF-08 variants compare complete persisted source and clone projections,
    exact version/declaration sets, target survival, delete_blocked and KS/no-S modes.
```

Accepted concurrency closure:

```text
mutation plans                 41 / 41
mutation families              10 DT + 10 OT + 7 OBJ + 10 RD + 4 REL
advisory gates                 3 exact keys; 6 gated mutations; all others ungated
row-lock modes                 KS / S / NKU / U
canonical ordering             exact and regression-protected

scenario registry              83 / 83
family census                  ROW 30; ARB 8; REF 11; GATE 7; SNAP 5;
                               ATOMIC 7; PAR 9; PLAN 6
scenario target ledger         165 selectors; 189 collected/executed/passed
scenario recipe registry       83 / 83 exact primary/secondary entries
predicate registry             21 / 21
predicate target ledger        136 selectors; 140 passed
M2-VER-15 ... M2-VER-19        5 / 5; 62 selectors; 67 passed

structured canonical outcomes 314
transaction outcomes           215 COMMITTED; 93 ROLLED_BACK; 6 no semantic UoW
semantic scenario coverage     80 scenario IDs;
                               PLAN-01, PLAN-02 and PLAN-04 are non-semantic evidence
```

Accepted canonical SQLSTATE census:

```text
23505                           8
23503                           1
supported-path 40P01            0
unexpected 40001                0
```

Separate negative controls produced one `40P01` and two `40001` observations, each with exactly one attempt and no retry. They are not supported-path outcomes.

Accepted verification:

```text
uv lock --check                                      PASS
uv sync --locked                                     PASS
uv build                                             PASS
Ruff format/check                                    PASS
Pyright                                              PASS — 0 errors
pytest collection                                    446 tests
traceability                                         19 passed
complete semantic concurrency modules                189 passed
M2 locking pure/PostgreSQL                            40 passed
schema metadata / migrations                          5 passed
PostgreSQL concurrency marker                        182 passed
non-PostgreSQL                                       205 passed
full repository suite                                446 passed
post-push full rerun on exact remote candidate       446 passed — 172.21 s
skip / xfail / rerun                                   0 / 0 / 0
```

Environment and unchanged boundaries:

```text
CPython                         3.14.7
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                              0.12.3
authoritative tables            15
Alembic graph                   one base / one head
root revision                   0001_m2_kernel
metadata drift                  compare_metadata == []
schema / migration diff         none
dependency / uv.lock diff       none
business HTTP operations        41 mutations + 22 reads = 63 exact
production/public surface       unchanged
Health/startup/CLI/packaging    no S04-or-later surface introduced
GitHub Actions/encoded payloads absent
```

Reviewer inspection verified the published commit chain, real delta, exact recipe map, structured outcome integration, SQLSTATE observation boundary, REF-08 aggregate assertions, traceability and unchanged surfaces. The reviewer did not independently re-execute the 446-test suite in this inspection; the accepted execution results are those produced and recorded by the corrected candidate.

No blocking review finding remains open for `M2-S03`.

The concluded execution aids were retired from the working tree by the same reviewer-owned acceptance commit:

```text
docs/milestones/M2/wip/M2-S03-codex-prompt.md
docs/milestones/M2/wip/M2-S03-review-fixes-codex-prompt.md
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
review-fix prompt              98e8a092b27afeb50cbadd07c6356349958ddf88
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

Prepare the non-normative Codex implementation prompt for:

```text
M2-S04 — Runtime settings, startup revision guard and Core Health
```

Before implementation, execute the mandatory repository-based pre-flight for `M2-S04`, including verification of its runtime, installed Alembic graph, lifespan and real-PostgreSQL evidence prerequisites. Do not start `M2-S05`.

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
