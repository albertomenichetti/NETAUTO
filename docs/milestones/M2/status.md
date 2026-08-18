# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S03 IN PROGRESS

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S03 — IN PROGRESS
current task    resolve S03-FINDING-01, then complete the M2-S03 candidate gate
blockers        S03-FINDING-01 — REF-08 execution-aid outcome contradicts frozen lifetime authority
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation is authorized only for the exact slice marked `READY` or `IN PROGRESS` here. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | AUTHORIZED — `M2-S03` ONLY |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | COMPLETED | `M2-S00 COMPLETED` |
| `M2-S02` | COMPLETED | `M2-S01 COMPLETED` |
| `M2-S03` | IN PROGRESS | `M2-S02 COMPLETED` |
| `M2-S04` | BLOCKED | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00`, `M2-S01` and `M2-S02` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

`M2-S03` implementation and all executable gates are complete, but the slice is
not a candidate because the following documentation finding affects one mandatory
execution-aid outcome:

```text
S03-FINDING-01 — REF-08 target-delete-first outcome

frozen authority
    docs/milestones/M2/architecture/concurrency.md §6.3 defines OT.CN as
    cloning already-owned physical references under KS lifetime locks;
    the accepted schema keeps immediate RESTRICT FKs for the exact parent OTV,
    stable component target and exact property DTV.

execution aid
    docs/milestones/M2/wip/M2-S03-codex-prompt.md:748 requires a
    target-delete-first order in which the target disappears and OT.CN returns
    the bounded missing-reference outcome.

conflict
    while the eligible PUBLISHED/DEPRECATED source version remains, its existing
    FK already prevents that target root delete from committing. The serial
    authority-conforming outcome is delete_blocked followed by a complete clone;
    making the target disappear would require weakening the frozen FK/lifetime
    contract or deleting the eligible source.

implemented evidence
    REF-08 covers parent OTV, component root and property DTV in both physical
    orders with real PostgreSQL blocking and exact KS plan observation. All six
    variants pass with delete_blocked plus one complete cloned version.

required resolution
    correct/waive the contradictory execution-aid outcome, or formally reopen
    and propagate the normative lifetime/schema design if a semantic change is
    intended. No implementation change is authorized from the WIP prompt alone.
```

`M2-S03` requires an externally supplied real PostgreSQL target through `TEST_DATABASE_URL` for its mandatory 41-mutation, concurrency, lock-plan and deadlock-evidence closure. No fallback database, local credentials or alternate environment variable is authorized.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S03 in-progress implementation record

Implementer result:

```text
M2-S03                         IN PROGRESS — not a review candidate
starting reviewer baseline     850abd97ece1aadeae65aa090d86c7ec4982751f
prompt commit                  29e4900 (docs(m2-s03): add Codex implementation prompt)
implementation                 f70ec89
open finding                   S03-FINDING-01
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

Implemented and verified closure:

```text
mutation plans                 41 / 41; 10 DT + 10 OT + 7 OBJ + 10 RD + 4 REL
advisory gates                 3 exact keys; 6 gated mutations; all others ungated
row-lock modes                 KS / S / NKU / U; canonical class/order assertions
mutation evidence              72 unique selectors; 74 passed

scenario registry              83 / 83
family census                  ROW 30; ARB 8; REF 11; GATE 7; SNAP 5;
                               ATOMIC 7; PAR 9; PLAN 6
scenario target ledger         165 unique selectors; 189 collected/executed/passed
predicate registry             21 / 21 with the exact frozen mapping
M2-VER-15 ... M2-VER-19        IMPLEMENTED; 62 selectors; 67 passed

new/strengthened evidence      REF-08, REF-09, REF-10, REF-11, GATE-07,
                               PAR-08, PAR-09, ROW-03/04/16 and SNAP-01/02
harness                        CTL/OBS/B/T1/T2/T3; exact 19-phase vocabulary;
                               pg_blocking_pids(); positive production progress;
                               outcome/ApplicationFailure/exception/SQLSTATE/
                               phase/commit-or-rollback capture
observed worker SQLSTATE       none
supported-path 40P01           0
skip / xfail / rerun           0 / 0 / 0
```

Executed verification:

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

Unchanged-boundary verification:

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
review acceptance              recorded by the commit containing this status
original prompt                9f4ed2ef69efdfbb6bc0e79dfc14c979f4f0f66d
original implementation        99b6d32d1ab9f3529881eb2e16809e01ea5b2be2
original candidate evidence    66d9d47dab97c2b42b63ed015261d65ccf1abc16
original provenance            9400502acc99b7c959cc5070cd97914b2ace7087
review changes record          4c1ae6905295ed1f7f69f71ecd9af7e76d1ca47f
review-fix prompt               98e8a092b27afeb50cbadd07c6356349958ddf88
corrective implementation      f27d13c6d8366e46c9ad3fb2b07ede735be0ff3e
corrected candidate evidence   6eb21c0fbc58728f075ff3674f039b68bb626ef0
corrected provenance           39d4b6b0a6fb0fae86525ec8bd56cad6df0ccbeb
durable revision               0001_m2_kernel (unchanged)
Alembic graph                  one base / one head
authoritative table census     15
metadata drift                 compare_metadata == []
business HTTP operations       63 exact
CPython                        3.14.7
PostgreSQL                     16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                             0.12.3
```

Closed review findings:

```text
S02-RF-01
    ROW-30 and REF-10 now prove both real concurrent winner orders through
    independent sessions and pg_blocking_pids(); ROW-26, ROW-27 and ROW-28
    assert exact state, event history, fan-out, pin and closure outcomes.

S02-RF-02
    M2-VER-12 and M2-VER-14 now map collected end-to-end valid lifecycle
    shape and historical-independence evidence; every registry target resolves
    against actual pytest collection while preserving the frozen census.

S02-RF-03
    Object-relative pages load only represented RelationshipDefinitions in
    one set-based statement; published/deprecated RDV history uses two bounded
    statements with no per-version get_version() query repetition.
```

Accepted verification:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS (172 files)
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
uv run pytest --collect-only -q                             PASS (411, 1.68s)
S02 domain / traceability targets                           PASS (27, 5.62s)
S02 deterministic PostgreSQL targets                        PASS (38, 27.12s)
Relationship / Object affected regressions                  PASS (70, 47.74s)
schema metadata / migration assurance                       PASS (5, 1.67s)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (158; 253 deselected;
                                                                  96.93s)
uv run pytest -q -m "not postgresql" -ra                    PASS (196; 215 deselected;
                                                                  9.64s)
uv run pytest -q -ra                                        PASS (411, 142.41s)
```

Reviewer inspection confirmed:

```text
Relationship DATA_CHANGE and SCHEMA_CHANGE implement the exact frozen public semantics
DATA_CHANGE no-op writes neither the factual row nor lifecycle history
SCHEMA_CHANGE uses Definition KS, target RDV S and factual Relationship NKU
pin + properties change atomically while runtime closure remains unchanged
LifecycleStore is the sole lifecycle SQL, codec, projection and writer authority
all four factual transition families have exact self-contained historical shapes
semantic-view fan-out covers ordinary, symmetric, self-loop and inheritance overlap
Relationship GET, Object-relative pages and lifecycle pages use coherent read boundaries
one corrupt represented aggregate or event fails the complete response
historical Relationship state remains readable without live model/current rows
ROW-26 ... ROW-30, REF-10, SNAP-05 and ATOMIC-06/07 are implemented and passing
both ROW-30 and REF-10 winner orders use real PostgreSQL blocking evidence
represented Definition loading and RDV history are bounded and regression-protected
M2-VER-08, 09 and 11 ... 14 are machine-resolvable and passing
the public business surface is exactly 41 mutations + 22 reads = 63 operations
no supported scenario produced SQLSTATE 40P01
no test was skipped, xfailed or rerun
the fifteen-table schema, durable root, dependencies and uv.lock are unchanged
no M1 bridge, backfill, stamp path or dual lifecycle decoder exists
no Health, startup guard, CLI, packaging or M2-S03 capability was introduced
obsolete GitHub Actions and encoded payload material remain absent
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
CPython                        3.14.7
PostgreSQL                     16.14
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
CPython                        3.14.7
PostgreSQL                     16.14
full suite                     PASS (314)
```

No blocking review finding remains open for `M2-S00`.

## Immediate next action

Resolve `S03-FINDING-01` through the authority-preserving documentation process.
After resolution, rerun the affected REF-08 evidence and the mandatory candidate
gates before considering:

```text
M2-S03 — CANDIDATE READY FOR REVIEW
```

Do not start `M2-S04` and do not mark `M2-S03` `COMPLETED`.

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
