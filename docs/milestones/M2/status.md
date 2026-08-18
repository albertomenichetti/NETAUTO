# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S02 READY

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S02 — READY
current task    prepare the M2-S02 Codex implementation prompt and execute the authorized slice
blockers        none
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation is authorized only for the exact slice marked `READY` or `IN PROGRESS` here. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | AUTHORIZED — `M2-S02` ONLY |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | COMPLETED | `M2-S00 COMPLETED` |
| `M2-S02` | READY | `M2-S01 COMPLETED` |
| `M2-S03` | BLOCKED | `M2-S02 COMPLETED` |
| `M2-S04` | BLOCKED | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` and `M2-S01` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning, technology or verification blocker is open for starting `M2-S02`.

`M2-S02` requires an externally supplied real PostgreSQL target through `TEST_DATABASE_URL` for its mandatory persistence, lifecycle, coherent-read and concurrency evidence. No fallback database, local credentials or alternate environment variable is authorized.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

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
durable revision              0001_m2_kernel
Alembic graph                 one base / one head
authoritative table census    15
metadata drift                compare_metadata == []
CPython                       3.14.7
PostgreSQL                    16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
```

Accepted verification:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS (169 files)
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
RF02 pure/static exact-pin targets                          PASS (30, 1.14s)
RF01 delete diagnostics / FK classification targets         PASS (17, 3.42s)
RF03 + affected Relationship concurrency targets            PASS (38, 23.93s)
affected Relationship / RD HTTP contracts                   PASS (14, 10.06s)
schema metadata / migration assurance                       PASS (5, 1.69s)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (125, 76.18s)
uv run pytest -q -m "not postgresql" -ra                    PASS (174, 5.22s)
uv run pytest -q -ra                                        PASS (349, 105.82s)
```

Reviewer inspection confirmed:

```text
the unique durable root creates the exact final fifteen-table schema
old disposable M1 revisions are absent from the shipped graph
one base, one head, repeatability and compare_metadata == [] remain intact
RDV lifecycle, default policy, property history and differential DML are complete
factual Relationship CREATE/GET/DELETE persist and expose exact RDV pin/properties
duplicate CREATE and absent DELETE use the exact frozen M2 outcomes
capability and stable/default reads are coherent and corruption-safe
S01-RF-01 preserves separate OT-property and RDV-property blocker categories/counts
both known DataType property-reference FKs map to bounded delete_blocked results
S01-RF-02 removes every implicit factual v1 constructor default
factual exact pins are required, positively validated and preserved on non-v1 projections/events
S01-RF-03 classifies missing dependencies from semantic selectors rather than physical key order
explicit delete-first CREATE/REVISE retain id + version details
implicit lineage loss and stale-default restart preserve the frozen outcomes
S01-RF-01 ... 03 and affected M2-VER / ROW-24 / REF-09 targets are machine-resolvable
all ten primary S01 M2-VER bundles and assigned scenarios pass
no supported scenario produced SQLSTATE 40P01
no test was skipped, xfailed or rerun
no schema, migration, dependency or lockfile changed during corrective work
no M1 bridge, backfill, stamp path or dual lifecycle decoder exists
no M2-S02 DATA_CHANGE/SCHEMA_CHANGE capability was introduced
obsolete GitHub Actions and encoded payload material remain absent
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
PostgreSQL                     16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
```

Accepted verification:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
uv run pytest -q tests/test_m2_locking.py \
  tests/test_m2_s00_traceability.py                         PASS (35)
uv run pytest -q tests/test_m2_locking_postgresql.py        PASS (9)
focused A1 ... A4 Relationship targets                      PASS (6)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (110)
uv run pytest -q -m "not postgresql" -ra                    PASS (160)
uv run pytest -q -ra                                        PASS (314)
```

No blocking review finding remains open for `M2-S00`.

## Immediate next action

Prepare the non-normative Codex implementation prompt for:

```text
M2-S02 — Factual Relationship mutations, lifecycle and coherent reads
```

Before implementation, execute the mandatory repository-based pre-flight for `M2-S02`, including verification that `TEST_DATABASE_URL` is available for the required real-PostgreSQL gates. Do not start `M2-S03`.

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
