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
current task    reviewer inspection of the published M2-S02 candidate
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
| `M2-S02` | CANDIDATE READY FOR REVIEW | `M2-S01 COMPLETED`; reviewer decision pending |
| `M2-S03` | BLOCKED | `M2-S02 COMPLETED` |
| `M2-S04` | BLOCKED | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` and `M2-S01` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning, technology or verification blocker is open for reviewing `M2-S02`.

`M2-S02` requires an externally supplied real PostgreSQL target through `TEST_DATABASE_URL` for its mandatory persistence, lifecycle, coherent-read and concurrency evidence. No fallback database, local credentials or alternate environment variable is authorized.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S02 candidate record

Candidate state:

```text
M2-S02                         CANDIDATE READY FOR REVIEW
reviewer decision              pending
implementation                 99b6d32d1ab9f3529881eb2e16809e01ea5b2be2
candidate evidence/status      recorded by the commit containing this record
prompt baseline                9f4ed2ef69efdfbb6bc0e79dfc14c979f4f0f66d
durable revision               0001_m2_kernel (unchanged)
Alembic graph                  one base / one head
authoritative table census     15
metadata drift                 compare_metadata == []
CPython                        3.14.7
PostgreSQL                     16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                             0.12.3
```

Implemented candidate:

```text
Relationship DATA_CHANGE validates one non-empty unique operation set, serializes on
the factual owner, reloads fresh complete state, applies canonical whole-state SET /
REMOVE semantics and writes one whole JSONB replacement plus one exact event set only
for a real transition. A semantic no-op writes neither UPDATE nor lifecycle event.

Relationship SCHEMA_CHANGE protects Definition KS and exact target RDV S before the
factual Relationship NKU, restarts only on LockPlanStale within the shared four-attempt
budget, requires an exact forward PUBLISHED target through commit, applies direct
source-to-target preserve-or-fail migration, updates pin + properties atomically in one
row statement and leaves closure unchanged.

LifecycleStore is the single lifecycle SQL, codec, metadata-projection and writer
boundary for intrinsic Object, ownership and all four factual Relationship transitions.
ObjectStore and RuntimeRelationshipStore retain current-state persistence only.

Relationship GET, Object-relative pages and lifecycle pages use coherent read
boundaries; page aggregate/schema/DataType validation is batched and corruption fails
the complete response. Historical factual snapshots use the shared closed carrier
codec and remain independent of deleted current Relationship, Definition/RDV/DTV and
endpoint resources.

The public surface adds exactly DATA_CHANGE and SCHEMA_CHANGE: 41 mutation operations,
22 read operations and 63 business operations total. No Health, startup, CLI,
packaging or M2-S03 capability is introduced.
```

Implemented evidence registries:

```text
M2-VER-08   PASS — DATA_CHANGE domain/application/persistence/API, no-op, ROW-26,
                    ATOMIC-06
M2-VER-09   PASS — SCHEMA_CHANGE preserve-or-fail/API, ROW-27/28/30, REF-10,
                    ATOMIC-07
M2-VER-11   PASS — six concrete GET/page read cuts and complete-page corruption
M2-VER-12   PASS — shared historical carriers, exact factual states and transitions
M2-VER-13   PASS — all four fact shapes and every factual transition family
M2-VER-14   PASS — sole LifecycleStore ownership and CREATE/DATA/SCHEMA/DELETE rollback

ROW-26      PASS — no lost update; waiter no-op; exactly one UPDATE and one event set
ROW-27      PASS — both winner orders; serial pin/properties/events; closure unchanged
ROW-28      PASS — valid forward serialization and stale target rejection after wait
ROW-29      PASS — DATA/SCHEMA x DELETE, both winner orders, exact final DELETE state
ROW-30      PASS — target deprecation orders, protected admission and default independence
REF-10      PASS — target-before-owner rebind/root-delete orders; bounded result
SNAP-05     PASS — DATA/SCHEMA x source/to/both/Definition rename cuts; one observation
ATOMIC-06   PASS — post-DATA DML writer failure restores old fact and leaves no event
ATOMIC-07   PASS — post-SCHEMA DML writer failure restores old fact and leaves no event
```

Fan-out and read/historical evidence:

```text
non-symmetric                         2 semantic views/events per transition
symmetric distinct endpoints         2 semantic views/events per transition
symmetric self-loop                   1 semantic view/event per transition
inheritance overlap                   4 raw closure rows, 2 semantic views/events
GET/page x DATA/SCHEMA/DELETE         committed before-or-after only
historical independence              PASS after Relationship, Definition/RDV/DTV and
                                     endpoint Object deletion
Object-specific historical route     still requires the current path Object
```

Candidate verification:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS (171 files)
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
uv run pytest -q tests/test_relationship_domain.py \
  tests/test_m2_s02_relationship_domain.py -ra              PASS (30, 0.75s)
uv run pytest -q tests/test_relationship_api.py \
  tests/test_relationshipdefinition_api.py \
  tests/test_object_api.py -ra                              PASS (24, 17.60s)
uv run pytest -q tests/test_m2_s02_semantic_concurrency.py \
  tests/test_m2_traceability.py -ra                         PASS (37, 24.80s)
uv run pytest -q tests/test_relationship_semantic_concurrency.py \
  tests/test_object_semantic_concurrency.py -ra             PASS (54, 34.89s)
uv run pytest -q tests/test_m2_traceability.py \
  tests/test_object_scope.py -ra                            PASS (11, 2.88s)
uv run pytest -q tests/test_schema_metadata.py \
  tests/test_migrations.py -ra                              PASS (5, 1.68s)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (153; 250 deselected;
                                                                  95.27s)
uv run pytest -q -m "not postgresql" -ra                    PASS (195; 208 deselected;
                                                                  6.34s)
uv run pytest -q -ra                                        PASS (403, 132.07s)
```

Verification census and unchanged boundaries:

```text
skips / xfails / reruns                       0 / 0 / 0
supported-path SQLSTATE 40P01                 none observed
schema / migration changes                    none
dependency / uv.lock changes                  none
M1 bridge/backfill/stamp/dual decoder          absent
obsolete Actions / encoded payload material   absent
S00/S01 evidence and completion records       preserved and passing
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

Review the published candidate for:

```text
M2-S02 — Factual Relationship mutations, lifecycle and coherent reads
```

Do not start `M2-S03` unless and until the reviewer records `M2-S02 COMPLETED`.

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
