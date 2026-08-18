# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S01 IN PROGRESS

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S01 — IN PROGRESS
current task    prepare the M2-S01 Codex implementation prompt and execute the authorized slice
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
| Implementation | AUTHORIZED — `M2-S01` ONLY |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | IN PROGRESS | `M2-S00 COMPLETED` |
| `M2-S02` | BLOCKED | `M2-S01 COMPLETED` |
| `M2-S03` | BLOCKED | `M2-S02 COMPLETED` |
| `M2-S04` | BLOCKED | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` is reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning, technology or verification blocker is open for starting `M2-S01`.

`M2-S01` requires an externally supplied real PostgreSQL target through `TEST_DATABASE_URL` for its mandatory migration, schema, persistence and concurrency evidence. No fallback database, local credentials or alternate environment variable is authorized.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

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

Reviewer inspection confirmed:

```text
all 32 delivered mutation paths use or are proven compatible with the central planner
PLAN-01 ... PLAN-06 have machine-resolvable pure/static and PostgreSQL targets
post-collision REL.CREATE classification is rollback-first and lifetime-safe
factual collision owners are locked canonically with Relationship KS
owner disappearance or set expansion causes a bounded whole-UoW restart
planner ancestry loading is skipped for non-ObjectTemplate plans
targeted ObjectTemplate ancestry uses one recursive CTE and excludes unrelated lineages
differential ObjectTemplate declaration DML and rollback evidence remain intact
three advisory gates and four row-lock modes match the frozen registry
no supported scenario produced SQLSTATE 40P01
no test was skipped, xfailed or rerun
no public M1 behavior changed outside the frozen M2 delta
no schema, migration, dependency or lockfile changed
no M2-S01 business capability was introduced
obsolete GitHub Actions and encoded payload material remain absent
```

No blocking review finding remains open for `M2-S00`.

## Immediate next action

Prepare the non-normative Codex implementation prompt for:

```text
M2-S01 — Durable relational baseline and versioned Relationship model plane
```

Before implementation, execute the mandatory repository-based pre-flight for `M2-S01`, including verification that `TEST_DATABASE_URL` is available for the required real-PostgreSQL gates. Do not start `M2-S02`.

## Current status vocabulary

```text
READY
    -> authorized to start after mandatory pre-flight

IN PROGRESS
    -> implementer work is active inside the exact slice scope

CANDIDATE READY FOR REVIEW
    -> implementation/evidence candidate published; reviewer decision pending

REVIEW CHANGES REQUIRED
    -> reviewer-owned result; corrections remain in the same slice

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
