# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S01 CANDIDATE READY FOR REVIEW

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S01 — CANDIDATE READY FOR REVIEW
current task    reviewer inspection of the corrected M2-S01 candidate
blockers        none
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. No implementation work is currently active while the corrected candidate awaits reviewer inspection. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | `M2-S01` CORRECTED CANDIDATE — reviewer decision pending |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | CANDIDATE READY FOR REVIEW | `M2-S00 COMPLETED` |
| `M2-S02` | BLOCKED | `M2-S01 COMPLETED` |
| `M2-S03` | BLOCKED | `M2-S02 COMPLETED` |
| `M2-S04` | BLOCKED | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` is reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Reviewer findings and corrective disposition

No contract, architecture, implementation-planning, technology or verification blocker is open for reviewer inspection of the corrected `M2-S01` candidate. The prior reviewer inspection identified the following three implementation/evidence defects. They did not require architecture reopening and their bounded candidate corrections remain inside `M2-S01`.

### S01-RF-01 — DataType delete diagnostics do not distinguish RDV property references

At review time, the new `relationship_definition_properties` rows correctly retained exact DataTypeVersion lifetime and were included in the DataType root-delete precheck count. The application result nevertheless reported the combined ObjectTemplate-property and RelationshipDefinition-property count entirely as:

```text
object_template_property
```

This makes RDV-only and mixed blocker diagnostics semantically false. The defensive final-FK translation also recognizes only `fk_object_template_properties_datatype_version`; the new `fk_relationship_definition_properties_datatype_version` authority is not translated into bounded `delete_blocked` diagnostics.

Required correction:

```text
preserve separate bounded semantic blocker categories and exact counts
handle RDV-only and mixed blocker sets deterministically
translate every known DataType property-reference FK through the bounded delete result
never expose SQLSTATE, constraint, table or driver details
add normal-precheck and deterministic final-arbitration regression evidence
```

Corrected candidate disposition: separate bounded counts are emitted in fixed ObjectTemplate-property / RelationshipDefinition-property order, both exact final FK authorities map to their semantic category, and unknown constraints remain internal. Normal RDV-only/mixed and real final-FK paths have permanent PostgreSQL evidence.

### S01-RF-02 — factual exact version is still synthesized as implicit v1 in domain/projection constructors

At review time, `Relationship` and `ObjectRelationshipView` defaulted `relationship_definition_version` to `1`. Pure/domain call sites therefore remained valid without supplying the new exact pin, even though M2 factual state has no implicit v1/latest/default representation and version `1` may be DRAFT, DEPRECATED or unrelated to the selected fact.

Required correction:

```text
make the factual exact RDV pin an explicit required value
validate its positive exact identity at the appropriate pure/application boundary
update every production and evidence construction site to supply the observed/selected pin
remove compatibility-style constructor behavior that can manufacture v1 state
retain {} only as an explicit canonical factual property state, not as schema selection
add pure/static regression evidence preventing reintroduction of an implicit pin
```

Corrected candidate disposition: both factual constructors require an explicit exact pin, pure validation rejects boolean and non-positive pins, every constructor site supplies the observed pin, and non-v1 GET, Object-relative list and lifecycle paths preserve it.

### S01-RF-03 — delete-first exact DataTypeVersion loss can omit the requested version selector

RD CREATE/REVISE plans contain both a DataType header and an exact DataTypeVersion row, and canonical acquisition reports the header before the version. At review time, missing-row handling mapped the first non-RD/OT missing key to `resource_type = datatype_version` and forwarded `key.version`; when the complete DataType lineage disappeared, the first key had `version = None`, so an explicitly requested exact DataTypeVersion could produce `referenced_resource_not_found` without the known `details.version` selector.

Required correction:

```text
classify missing rows from the semantic command operand/candidate, not only the first physical missing key
preserve id + version for an explicitly selected exact DataTypeVersion
preserve the owning implicit-selector outcome when default-based discovery becomes stale
add deterministic delete-first RD CREATE and RD REVISE reference-lifetime evidence
assert the exact bounded public details and absence of internal leakage
```

Corrected candidate disposition: local semantic dependency descriptors now drive deterministic missing-operand classification for CREATE and REVISE without changing physical lock order. Explicit delete-first paths retain the requested exact version, implicit lineage loss identifies the DataType, and the existing complete-UoW stale-default restart is preserved and proven.

`M2-S02` remains blocked until reviewer-owned acceptance marks `M2-S01 COMPLETED`.

## M2-S01 candidate record

Published candidate reviewed:

```text
candidate state                 CANDIDATE READY FOR REVIEW
reviewer result                 REVIEW CHANGES REQUIRED
implementation commit           c019cada4152e9798e25476d35b0cec5127d6135
candidate status commit         63c0e772df4c73c439b7b4baed67b3d11fc809b9
branch                          M2
durable revision                0001_m2_kernel
Alembic graph                   one base / one head
authoritative table census      15
metadata drift                  compare_metadata == []
CPython                         3.14.7
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
```

Candidate verification reported:

```text
uv lock --check                                             PASS
uv sync --locked                                            PASS
uv build                                                    PASS
uv run ruff format --check .                                PASS (168 files)
uv run ruff check .                                         PASS
uv run pyright                                              PASS (0 errors)
focused RDV / Relationship API and domain targets           PASS (41)
uv run pytest -q tests/test_migrations.py -ra               PASS (2)
uv run pytest -q tests/test_m2_s01_semantic_concurrency.py  PASS (12)
uv run pytest -q -m "postgresql and concurrency" -ra        PASS (122)
uv run pytest -q -m "not postgresql" -ra                    PASS (168)
uv run pytest -q -ra                                        PASS (337)
```

The reviewed candidate reported no skip, xfail, rerun or supported-path SQLSTATE `40P01`. Its migration, schema, RDV, factual CREATE/GET/DELETE and assigned concurrency evidence remained useful and was preserved. At review time, passing those existing targets did not close the three uncovered findings above and permanent regression targets were required.

No dependency or lockfile changed. No M1 database bridge, backfill, stamp path or dual lifecycle decoder was added. M2-S02 factual DATA_CHANGE/SCHEMA_CHANGE routes and commands, Health, CLI and startup-revision capability remain absent. The obsolete S00 Actions/payload material remains absent.

Corrected candidate published:

```text
candidate state                 CANDIDATE READY FOR REVIEW
reviewer result                 pending
original implementation         c019cada4152e9798e25476d35b0cec5127d6135
original candidate status       63c0e772df4c73c439b7b4baed67b3d11fc809b9
corrective implementation       46afa3341d292fb1790612456b28689eafb5b694
corrective evidence/status       6d8a0838530f2b449c598dc545a0a2ad3577c5d3
branch                          M2
remote                          origin/M2
durable revision                0001_m2_kernel
Alembic graph                   one base / one head
authoritative table census      15
metadata drift                  compare_metadata == []
CPython                         3.14.7
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
```

Corrected candidate verification:

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

The `S01-RF-01 ... 03` registry and affected `M2-VER-01`, `M2-VER-04`, `M2-VER-05` and `M2-VER-06` bundle targets are machine-resolvable and passed. The `ROW-24` explicit CREATE, implicit CREATE and stale-default restart variants and the `REF-09` explicit REVISE variant passed with exact final-state assertions. The full suite reported no skip, xfail or rerun, and no supported path returned SQLSTATE `40P01`.

No schema, migration, dependency or lockfile changed. Both active S01 execution aids remain present and obsolete Actions/payload material remains absent.

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

Review the corrected candidate for:

```text
M2-S01 — S01-RF-01, S01-RF-02 and S01-RF-03 corrective evidence
```

The reviewer decision is pending. Do not mark `M2-S01 COMPLETED` and do not start `M2-S02` before reviewer-owned acceptance.

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
