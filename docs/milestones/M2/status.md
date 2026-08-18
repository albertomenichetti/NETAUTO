# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S02 CANDIDATE READY FOR REVIEW

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S02 — CANDIDATE READY FOR REVIEW
current task    reviewer inspection of the corrected M2-S02 candidate
blockers        reviewer decision pending; M2-S03 remains blocked
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | CORRECTED `M2-S02` CANDIDATE PUBLISHED — reviewer decision pending |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | COMPLETED | `M2-S00 COMPLETED` |
| `M2-S02` | CANDIDATE READY FOR REVIEW | `M2-S01 COMPLETED`; reviewer decision pending |
| `M2-S03` | BLOCKED | `M2-S02 COMPLETED` |
| `M2-S04` | BLOCKED | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` and `M2-S01` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Corrected review-fix disposition

No contract, architecture, implementation-planning or technology contradiction is open. The three bounded implementation/evidence defects from the M2-S02 reviewer inspection are corrected by the candidate recorded below. They did not require architecture reopening. Reviewer acceptance remains pending.

### S02-RF-01 — CORRECTED: canonical S02 concurrency evidence

The functional transaction paths are consistent with the frozen lock registry, but the published T3 evidence does not prove every assigned interleaving and assertion that the candidate record reports as complete.

The current `ROW-30` target proves SCHEMA_CHANGE-first against RDV deprecation with a real blocked race, then represents deprecation-first only by pre-deprecating the target and invoking SCHEMA_CHANGE sequentially. The current `REF-10` target similarly proves SCHEMA_CHANGE-first against Definition root delete with a blocked race, then represents delete-first only through a completed sequential delete attempt followed by SCHEMA_CHANGE.

Those sequential pre-states are useful semantic tests, but they are not the required independent-session second winner orders. The missing variants must prove the real waiter/blocker relationship, fresh post-wait outcome and absence of `40P01`.

The assigned scenario targets also need stronger permanent assertions:

```text
ROW-26
    assert exact before/after factual event state for the real transition,
    in addition to UPDATE/event cardinality and the waiter no-op

ROW-27
    assert the complete ordered factual lifecycle sequence for both winner orders

ROW-28
    assert closure preservation and exact lifecycle/source-target facts,
    in addition to the final pin and stale-target failure
```

Required correction:

```text
add a real deprecator-first ROW-30 race using independent sessions
add a real root-delete-first REF-10 race using independent sessions
prove required blocking with pg_blocking_pids()
assert exact fresh semantic outcomes and final state for both orders
strengthen ROW-26, ROW-27 and ROW-28 with their missing event/closure assertions
preserve stable scenario IDs and machine-resolvable parameter variants
```

Corrected by real independent-session schema-first and opposite-order targets for `ROW-30` and `REF-10`, each with authoritative `pg_blocking_pids()` observation before release, plus exact event, state, closure, diagnostic and post-wait assertions. `ROW-26`, both `ROW-27` orders and both `ROW-28` outcomes now assert their complete required histories.

### S02-RF-02 — CORRECTED: S02 lifecycle traceability

The required behavior is present in the test suite, but the machine-checkable bundle registry does not map all mandatory evidence to its owning bundle.

In particular:

```text
M2-VER-12
    maps invalid carrier/transition and corrupt-page tests,
    but does not map a concrete valid end-to-end target proving the exact
    CREATED / DATA_CHANGE / SCHEMA_CHANGE / DELETED factual shapes

M2-VER-14
    maps sole-store and rollback targets,
    but does not map the existing historical-independence target that reads
    history after Relationship, Definition/RDV/DTV and endpoint deletion
```

The existing full-suite execution does not make those mandatory bundle links machine-resolvable. A bundle may reuse one concrete test already owned elsewhere, but every required obligation must be represented explicitly in its own target set.

Required correction:

```text
map real valid four-transition shape evidence into M2-VER-12
map the historical-independence target into M2-VER-14
add any missing narrowly focused target if one existing test is too broad
keep all targets real and collected
preserve 16 outcomes, 32 acceptance criteria, 32 bundles and 83 scenarios
preserve every S00/S01 registry and target
```

Corrected by mapping the collected end-to-end four-transition API target into `M2-VER-12` and `M2-VER-14`, retaining invalid-codec/corruption, sole-store and four atomic rollback targets, and resolving every registry target against actual pytest collection. The frozen census remains 16 outcomes, 32 acceptance criteria, 32 evidence bundles and 83 scenarios; all S00/S01 and PLAN registries remain preserved.

### S02-RF-03 — CORRECTED: bounded S02 read paths

The Object-relative page path correctly avoids one complete aggregate sequence per represented fact, but it still loads the complete certified RelationshipDefinition set rather than only the Definition IDs represented by the page.

The SCHEMA_CHANGE path calls `published_history()`, whose current persistence implementation first loads the version-number set and then calls `get_version()` separately for every version. Since `get_version()` loads header and declarations separately, schema migration cost grows through preventable per-version query repetition.

This violates the S02 execution constraint to avoid preventable N+1 queries and weakens the bounded-page realization expected by the prompt.

Required correction:

```text
add a set-based stable-Definition aggregate loader for represented Definition IDs
use it in Object-relative page validation instead of certified_set()
batch-load published/deprecated RDV history headers and declarations
remove per-version get_version() query repetition from the SCHEMA_CHANGE path
retain one parent-graph load at most per page
add query-shape/count regressions preventing full certified-set and history N+1 reintroduction
preserve all semantic and concurrency behavior
```

Corrected by a represented-ID `RelationshipDefinitionStore.get_many()` loader and a two-statement published/deprecated RDV history load. Real-PostgreSQL regressions prove empty input performs zero queries; a page representing three of five Definitions uses one bounded Definition aggregate statement, zero `certified_set()` calls and one parent-graph load; one-version and four-version histories both use two statements and zero per-item `get_version()` calls; SCHEMA_CHANGE continues to consume the batched history.

All three findings are corrected, every mandatory real-PostgreSQL and complete gate passes, and the corrected candidate is published for reviewer inspection. `M2-S03` remains blocked until reviewer-owned `M2-S02 COMPLETED`.

## Previous M2-S02 candidate review record

Published candidate reviewed:

```text
candidate state                 CANDIDATE READY FOR REVIEW
reviewer result                 REVIEW CHANGES REQUIRED
implementation                  99b6d32d1ab9f3529881eb2e16809e01ea5b2be2
candidate evidence/status       66d9d47dab97c2b42b63ed015261d65ccf1abc16
publication provenance          9400502acc99b7c959cc5070cd97914b2ace7087
prompt baseline                 9f4ed2ef69efdfbb6bc0e79dfc14c979f4f0f66d
branch                          M2
durable revision                0001_m2_kernel (unchanged)
Alembic graph                   one base / one head
authoritative table census      15
metadata drift                  compare_metadata == []
CPython                         3.14.7
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                              0.12.3
```

Candidate verification reported:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS (171 files)
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
Relationship domain/property targets                        PASS (30)
Relationship API/lifecycle targets                           PASS (24)
S02 PostgreSQL + traceability targets                        PASS (37)
shared writer/Object regressions                             PASS (54)
route inventory targets                                      PASS (11)
schema metadata/migrations                                    PASS (5)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (153; 250 deselected)
uv run pytest -q -m "not postgresql" -ra                    PASS (195; 208 deselected)
uv run pytest -q -ra                                        PASS (403, 132.07s)
```

The candidate reported no skip, xfail, rerun or supported-path SQLSTATE `40P01`. The implementation of DATA_CHANGE, SCHEMA_CHANGE, the shared LifecycleStore, coherent reads, fan-out, atomic rollback and exact public surface remains useful and must be preserved. Passing the existing targets does not close the uncovered evidence and bounded-query findings above.

No schema, migration, dependency or lockfile changed. No M1 database bridge, backfill, stamp path or dual decoder was introduced. Health, startup guard, CLI, packaging and M2-S03 capability remain absent. Obsolete GitHub Actions and encoded payload material remain absent.

## Corrected M2-S02 candidate record

Candidate identity:

```text
M2-S02                         CANDIDATE READY FOR REVIEW
reviewer decision              pending
review finding record          4c1ae6905295ed1f7f69f71ecd9af7e76d1ca47f
review-fix prompt               98e8a092b27afeb50cbadd07c6356349958ddf88
corrective implementation      f27d13c6d8366e46c9ad3fb2b07ede735be0ff3e
candidate evidence/status      recorded by the commit containing this record
publication provenance         pending normal push to origin/M2
branch                          M2
durable revision                0001_m2_kernel (unchanged)
Alembic graph                   one base / one head
authoritative table census      15
metadata drift                  compare_metadata == []
business HTTP operations        63 exact
CPython                         3.14.7
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                              0.12.3
```

Corrected exact targets:

```text
ROW-26
  tests/test_m2_s02_semantic_concurrency.py::test_row_26_data_changes_reread_fresh_state_and_waiter_can_be_noop

ROW-27
  tests/test_m2_s02_semantic_concurrency.py::test_row_27_data_and_schema_change_have_serial_factual_history[data-first]
  tests/test_m2_s02_semantic_concurrency.py::test_row_27_data_and_schema_change_have_serial_factual_history[schema-first]

ROW-28
  tests/test_m2_s02_semantic_concurrency.py::test_row_28_schema_changes_recheck_forward_target_after_wait[lower-first]
  tests/test_m2_s02_semantic_concurrency.py::test_row_28_schema_changes_recheck_forward_target_after_wait[higher-first]

ROW-30
  tests/test_m2_s02_semantic_concurrency.py::test_row_30_schema_change_first_blocks_target_deprecation
  tests/test_m2_s02_semantic_concurrency.py::test_row_30_target_deprecation_first_blocks_schema_change
  tests/test_m2_s02_semantic_concurrency.py::test_row_30_definition_default_change_is_independent

REF-10
  tests/test_m2_s02_semantic_concurrency.py::test_ref_10_schema_change_first_blocks_definition_delete
  tests/test_m2_s02_semantic_concurrency.py::test_ref_10_definition_delete_first_rolls_back_then_schema_changes

S02-RF-02
  tests/test_relationship_api.py::test_m2_s02_data_schema_change_lifecycle_and_strict_contract

S02-RF-03
  tests/test_m2_s02_semantic_concurrency.py::test_object_relationship_page_batches_only_represented_definitions
  tests/test_m2_s02_semantic_concurrency.py::test_published_relationship_history_is_set_based_and_schema_change_uses_it
```

Query-bound evidence:

```text
RelationshipDefinitionStore.get_many(())                    0 statements
page represented Definition IDs                             3 exact IDs of 5 total
page RelationshipDefinition aggregate statements            1
page certified_set() calls                                   0
page parent-graph loads                                      1
published history, 1 eligible version                        2 statements
published history, 4 eligible versions + 1 DRAFT             2 statements
published history per-item get_version() calls               0
eligible history order/status/declarations                   exact and complete
SCHEMA_CHANGE batched-history calls                          1
```

Verification executed with the externally supplied `TEST_DATABASE_URL`:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS (172 files)
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
uv run pytest --collect-only -q                             PASS (411, 1.68s)
uv run pytest -q tests/test_m2_s02_relationship_domain.py \
  tests/test_m2_traceability.py -ra                         PASS (27, 5.62s)
uv run pytest -q tests/test_m2_s02_semantic_concurrency.py \
  -ra                                                       PASS (38, 27.12s)
uv run pytest -q tests/test_relationship_api.py \
  tests/test_relationship_semantic_concurrency.py \
  tests/test_object_api.py \
  tests/test_object_semantic_concurrency.py -ra             PASS (70, 47.74s)
uv run pytest -q tests/test_schema_metadata.py \
  tests/test_migrations.py -ra                              PASS (5, 1.67s)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (158; 253 deselected;
                                                                  96.93s)
uv run pytest -q -m "not postgresql" -ra                    PASS (196; 215 deselected;
                                                                  9.64s)
uv run pytest -q -ra                                        PASS (411, 142.41s)
```

Verification and unchanged-boundary census:

```text
skips / xfails / reruns                       0 / 0 / 0
observed worker SQLSTATE values               none
supported-path SQLSTATE 40P01                 none observed
schema / migration changes                    none
dependency / uv.lock changes                  none
0001_m2_kernel                                unchanged
one Alembic base / one head                   verified
compare_metadata                              []
authoritative tables                          15
business HTTP operations                      63
M1 bridge/backfill/stamp/dual decoder          absent
Health/startup/CLI/packaging/M2-S03 surface   absent
obsolete Actions / encoded payload material   absent
S00/S01/PLAN registries                       preserved and passing
unexecuted mandatory requirements              none
architecture/documentation findings            none
known residual risks                           none identified
```

`M2-S02` is not `COMPLETED`; acceptance remains reviewer-owned. `M2-S03` remains `BLOCKED`.

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
CPython                       3.14.7
PostgreSQL                    16.14
full suite                    PASS (349)
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

Review the corrected published candidate for:

```text
M2-S02 — factual Relationship mutations, lifecycle and coherent reads
```

The reviewer decides whether the three recorded review findings are closed. Do not start `M2-S03` unless and until the reviewer records `M2-S02 COMPLETED`.

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
