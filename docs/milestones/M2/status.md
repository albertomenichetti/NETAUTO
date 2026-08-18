# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S01 REVIEW CHANGES REQUIRED

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S01 — REVIEW CHANGES REQUIRED
current task    prepare and execute the bounded M2-S01 Codex review-fix prompt
blockers        S01-RF-01, S01-RF-02, S01-RF-03
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded reviewer findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | AUTHORIZED — `M2-S01` REVIEW FIX ONLY |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | REVIEW CHANGES REQUIRED | `M2-S00 COMPLETED` |
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

No contract, architecture, implementation-planning or technology contradiction is open. The M2-S01 reviewer inspection identified three implementation/evidence defects. They do not require architecture reopening and must be corrected inside `M2-S01`.

### S01-RF-01 — DataType delete diagnostics do not distinguish RDV property references

The new `relationship_definition_properties` rows correctly retain exact DataTypeVersion lifetime and are included in the DataType root-delete precheck count. The current application result nevertheless reports the combined ObjectTemplate-property and RelationshipDefinition-property count entirely as:

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

### S01-RF-02 — factual exact version is still synthesized as implicit v1 in domain/projection constructors

`Relationship` and `ObjectRelationshipView` currently default `relationship_definition_version` to `1`. Pure/domain call sites therefore remain valid without supplying the new exact pin, even though M2 factual state has no implicit v1/latest/default representation and version `1` may be DRAFT, DEPRECATED or unrelated to the selected fact.

Required correction:

```text
make the factual exact RDV pin an explicit required value
validate its positive exact identity at the appropriate pure/application boundary
update every production and evidence construction site to supply the observed/selected pin
remove compatibility-style constructor behavior that can manufacture v1 state
retain {} only as an explicit canonical factual property state, not as schema selection
add pure/static regression evidence preventing reintroduction of an implicit pin
```

### S01-RF-03 — delete-first exact DataTypeVersion loss can omit the requested version selector

RD CREATE/REVISE plans contain both a DataType header and an exact DataTypeVersion row. Canonical acquisition reports the header before the version. Current missing-row handling maps the first non-RD/OT missing key to `resource_type = datatype_version` and forwards `key.version`; when the complete DataType lineage disappeared, the first key has `version = None`, so an explicitly requested exact DataTypeVersion can produce `referenced_resource_not_found` without the known `details.version` selector.

Required correction:

```text
classify missing rows from the semantic command operand/candidate, not only the first physical missing key
preserve id + version for an explicitly selected exact DataTypeVersion
preserve the owning implicit-selector outcome when default-based discovery becomes stale
add deterministic delete-first RD CREATE and RD REVISE reference-lifetime evidence
assert the exact bounded public details and absence of internal leakage
```

`M2-S02` remains blocked until all three findings are corrected, the mandatory real-PostgreSQL and full gates pass, and a new candidate is published for reviewer inspection.

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

The candidate reported no skip, xfail, rerun or supported-path SQLSTATE `40P01`. Its migration, schema, RDV, factual CREATE/GET/DELETE and assigned concurrency evidence remains useful and must be preserved unless a reviewer finding requires a focused correction. Passing existing targets does not close the three uncovered findings above; permanent regression targets must be added.

No dependency or lockfile changed. No M1 database bridge, backfill, stamp path or dual lifecycle decoder was added. M2-S02 factual DATA_CHANGE/SCHEMA_CHANGE routes and commands, Health, CLI and startup-revision capability remain absent. The obsolete S00 Actions/payload material remains absent.

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

Prepare and execute one non-normative Codex review-fix prompt for:

```text
M2-S01 — S01-RF-01, S01-RF-02 and S01-RF-03
```

The correction remains in the same slice. Preserve the accepted candidate scope, add focused permanent evidence, rerun every affected PostgreSQL/API/domain target and the complete repository gate, then publish a new `CANDIDATE READY FOR REVIEW`. Do not start `M2-S02`.

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
