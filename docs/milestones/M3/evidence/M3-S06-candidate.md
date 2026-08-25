# M3-S06 Candidate Evidence

This record contains non-semantic execution evidence for the M3-S06 implementation candidate. It does not accept the slice, authorize M3-S07, or record final M3 acceptance.

## Candidate identity

```text
cycle / slice             M3 / M3-S06
branch                    M3
authorization baseline    28f2a1ad1f612cb19f8064e34ae9294c5a60499b
prompt baseline           e0f44bd2560aa354cc780c9e668cfacc9cb3842f
implementation candidate  c13bf884b8196e256fe4e7cefd73d083660fa54e
candidate parent          e0f44bd2560aa354cc780c9e668cfacc9cb3842f
publication model         direct commit and push to M3; no PR
```

At evidence capture, local `M3` was at the implementation candidate and `origin/M3` remained at the prompt baseline, so publication was pending. This record is necessarily committed after the tested implementation SHA; final local/origin/remote synchronization is verified and reported in the candidate handoff.

## Runtime and toolchain

```text
PostgreSQL  16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
Python      3.14.7
uv          0.12.3
pytest      8.4.2
Ruff        0.16.3
Pyright     1.1.411
```

## Finite registry and public-surface censuses

The machine-checkable owner is `tests/support/m3_evidence.py`; its exact-equality tests are in `tests/test_m3_traceability.py`.

```text
M3 outcomes                         8 / 8
M3 acceptance criteria             19 / 19
M3 evidence bundles                19 / 19
non-empty architecture owner sets  19 / 19
non-empty collected target sets    19 / 19
M3 contract quality gates           8 / 8
canonical business GET routes      22 / 22
cursor-bearing routes              12 / 12
CLI 201 + Location operations       8 / 8
```

The live OpenAPI GET set, application business-operation set, and frozen 22-route registry are equal. The live CLI registry-derived `201` set and frozen eight-operation registry are equal. Every concrete evidence target exists and is collected.

## Integrated HTTP and cursor evidence

The public HTTP matrix executed canonical successful requests for all 22 GET routes and verified exact top-level DTO shapes. It also exercised the frozen failure categories across resource families: unknown query, repeated query, malformed carrier, missing path target, missing nested parent, missing nested child/version, successful empty page, missing owner target, and existing detached target returning `null`.

All 12 cursor routes performed real multi-page traversal with a changed continuation limit. Traversed keys equaled unpaged baselines in canonical order with no omission or duplication. Every route rejected an incompatible scope cursor, a malformed token, and a malformed key. Every route with a semantic membership filter rejected a changed filter; every route with a required path target rejected a changed target. Compound Object Relationship and descending lifecycle keys were exercised directly.

## One-business-statement census

The S06 PostgreSQL observer was cleared immediately before each canonical successful GET. Every application `SELECT`/`WITH` on the production connection path counted; setup and cleanup remained outside each observation window.

| Route | Statements | Route | Statements |
|---|---:|---|---:|
| DT-GET-01 | 1 | DT-GET-02 | 1 |
| DT-GET-03 | 1 | DT-GET-04 | 1 |
| OT-GET-01 | 1 | OT-GET-02 | 1 |
| OT-GET-03 | 1 | OT-GET-04 | 1 |
| OT-GET-05 | 1 | OT-GET-06 | 1 |
| OBJ-GET-01 | 1 | OBJ-GET-02 | 1 |
| OBJ-GET-03 | 1 | OBJ-GET-04 | 1 |
| OBJ-GET-05 | 1 | OBJ-GET-06 | 1 |
| RD-GET-01 | 1 | RD-GET-02 | 1 |
| RD-GET-03 | 1 | RD-GET-04 | 1 |
| REL-GET-01 | 1 | LC-GET-01 | 1 |

Disposition: `22 / 22 PASS`, with exactly one business statement per route. Static inspection also proved that the exact 22 application GET targets have no `coherent_read()` or mutation-certification prerequisite.

## Deterministic T3 snapshot evidence

The representative family was an exact RelationshipDefinition aggregate containing one root and two persisted resolution fragments. Reader and writer used independent PostgreSQL sessions. Test-only events provided deterministic cuts with bounded timeouts and no sleeps, production SQL/isolation/locks/path changes, or hook-side transaction control.

```text
AFTER cut   reader paused immediately before its authoritative statement;
            writer atomically committed root + both resolution changes;
            response contained the complete AFTER generation.

BEFORE cut  authoritative statement completed before the pause;
            writer atomically committed root + both resolution changes;
            response retained the complete BEFORE generation.

result      2 / 2 PASS; no mixed generation observed
```

M3 continues not to promise repeatable membership or one shared snapshot across separate page requests.

## Non-drift evidence

```text
Alembic revision inventory       0001_m2_durable_kernel.py plus __init__.py only
revision / down_revision         0001_m2_kernel / None
migration roots / heads          1 / 1
live compare_metadata            []
metadata tables                  15
project version                  0.2.0
requires-python                  >=3.14,<3.15
runtime dependency delta         0
new migration/schema delta       0
uv.lock delta                    0
```

Authorized Git blob identities remained exact:

```text
pyproject.toml                   d20bbb94739a74ebfb0bd27291b6e4f130d24c5f
uv.lock                          0aa980926fda5f42ee3a7d3cedc64f9fcf8c2d23
0001_m2_durable_kernel.py        27fc85e0b4411332fce87c406b6216b35db6eb20
```

No production module, public route, DTO, cursor codec/version, schema, migration, dependency, lockfile, or project version changed in S06.

## M3-VER disposition and concrete commands

| Bundle | Disposition | Re-executed concrete evidence |
|---|---|---|
| M3-VER-01..03 | PASS | `uv run pytest -q tests/test_m3_s00_cli_location.py ...` through the 99-test accepted-M3 command |
| M3-VER-04..06 | PASS | S06 integrated matrix/traceability plus accepted S02-S05 read/write regressions in the 99-test command |
| M3-VER-07..08 | PASS | accepted S04/S05 lifecycle targets in the 99-test command |
| M3-VER-09 | PASS | S06 12-route cursor matrix plus accepted family cursor targets |
| M3-VER-10..11 | PASS | accepted S04 components/relationship cross-target targets |
| M3-VER-12 | PASS | S06 12-route true multi-page cursor matrix |
| M3-VER-13 | PASS | accepted S05 global/Object lifecycle scope target |
| M3-VER-14..16 | PASS | accepted S01 HTTP/CLI/cursor parent tri-state targets |
| M3-VER-17 | PASS | S06 static non-drift plus migration/schema tests |
| M3-VER-18 | PASS | exact registries, owner/target resolution, live censuses, CQG and normative-state tests |
| M3-VER-19 | PASS | 22/22 SQL observer plus two deterministic snapshot interleavings |

All 19 bundles have non-empty concrete collected target sets and passing evidence on the tested implementation candidate. This is S06 candidate evidence, not reviewer acceptance.

## Verification ledger

```text
uv run pytest -q tests/test_m3_traceability.py tests/test_m3_s06_integration.py
    PASS — 11 passed

uv run pytest -q tests/test_m3_s00_cli_location.py tests/test_m3_s01_parent_tristate.py tests/test_m3_s02_datatype_reads.py tests/test_m3_s03_objecttemplate_reads.py tests/test_m3_s04_object_reads.py tests/test_m3_s05_relationship_reads.py tests/test_m3_traceability.py tests/test_m3_s06_integration.py
    PASS — 99 passed

uv run pytest -q tests/test_migrations.py tests/test_schema_metadata.py
    PASS — 5 passed; live compare_metadata == []

uv run pytest -q tests/test_datatype_concurrency.py tests/test_datatype_semantic_concurrency.py tests/test_objecttemplate_semantic_concurrency.py tests/test_object_semantic_concurrency.py tests/test_relationshipdefinition_semantic_concurrency.py tests/test_relationship_semantic_concurrency.py tests/test_m2_s01_semantic_concurrency.py tests/test_m2_s02_semantic_concurrency.py tests/test_m2_s03_semantic_concurrency.py
    PASS — 190 passed; 312 canonical outcomes; 78 scenario IDs;
    supported-path 40P01 = 0; unexpected 40001 = 0

uv lock --check
    PASS — 46 packages resolved

uv sync --locked
    PASS — 44 packages checked

uv build
    PASS — sdist and wheel built for netauto 0.2.0

uv run ruff format --check .
    PASS — 293 files already formatted

uv run ruff check .
    PASS

uv run pyright
    PASS — 0 errors, 0 warnings, 0 informations

uv run pytest --collect-only -q
    PASS — 990 tests collected

uv run pytest -q -m "not postgresql"
    PASS — 706 passed, 284 deselected, 1 warning

uv run pytest -q
    PASS — 990 passed, 1 warning in 298.79s
    canonical outcomes = 314; scenario IDs = 80
    transaction outcomes = COMMITTED 215 / NO_UOW 6 / ROLLED_BACK 93
    supported-path 40P01 = 0; unexpected 40001 = 0
```

Normative test disposition for the complete run:

```text
passed             990
skipped              0
xfail / xpass         0 / 0
automatic reruns      0
warnings              1 — previously reviewed third-party deprecation
```

The warning is `StarletteDeprecationWarning` from FastAPI's `TestClient` import recommending `httpx2`; S06 neither hid nor normalized it.

## Findings and residual limits

- No frozen implementation defect or architecture/documentation contradiction was found.
- No production correction was required.
- The deterministic concurrency negative-control target emitted its intentional three forbidden SQLSTATE observations (`40001` twice and `40P01` once); canonical supported paths emitted neither.
- Separate keyset page requests retain the frozen non-goal: they do not share one repeatable snapshot.
- M3-S06 remains reviewer-owned for completion. M3-S07 and final M3 acceptance remain not authorized.
