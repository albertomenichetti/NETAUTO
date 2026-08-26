# M3-S07 Candidate Evidence

This record contains implementer-owned execution evidence for the exact M3-S07 delivery candidate. It does not complete M3-S07, accept or deliver M3, or grant final delivery approval.

## Candidate identity and publication state

```text
cycle / slice                 M3 / M3-S07
branch                        M3
authorization baseline        16b761802369ff85b71aa966bfcfaeaac55b4ccf
prompt-publication baseline   3c3471a36939f2ee8dbe5bdf55c692204abca506
tested delivery candidate     1f018a771227087a5c629e644d77c06879585003
candidate parent              e040f1ec327986423c402a1189c9a07245cc9ac0
evidence-publication HEAD     containing docs-only publication commit;
                              exact SHA resolved and verified in handoff
publication model             direct commit and push to M3; no PR
project version               0.2.0
reviewer decision             PENDING / reviewer-owned
```

Candidate preparation changed only `docs/milestones/M3/status.md` and the S07 lifecycle assertions in `tests/test_m3_traceability.py`. The precursor `e040f1ec327986423c402a1189c9a07245cc9ac0` was abandoned when the first Ruff format check found a wrapping-only issue. The formatter correction was committed as the replacement candidate above, and the entire final gate was restarted from its first command. No result from the abandoned run is used as final evidence.

At final-gate capture, the working tree was clean at the tested candidate. Local `M3` was at the candidate while `origin/M3` and the remote `M3` ref remained at the prompt-publication baseline, so evidence publication was pending. The containing publication commit is necessarily later than the evidence it records; exact local/origin/remote equality and the clean final tree are verified after push and reported in the handoff.

## Runtime and toolchain

```text
PostgreSQL  16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
Python      3.14.7
uv          0.12.3
pytest      8.4.2
Ruff        0.16.3
Pyright     1.1.411
```

`TEST_DATABASE_URL` was available throughout the final gate. Alembic's runtime CLI intentionally reads `NETAUTO_DATABASE_URL`, so the disposable test URL was mapped to that setting for direct Alembic commands without printing or recording the URL.

## Exact final censuses

The machine-checkable registries in `tests/support/m3_evidence.py` and their live-equality assertions passed exactly:

```text
M3 outcomes                         8 / 8
M3 acceptance criteria             19 / 19
M3 evidence bundles                19 / 19
non-empty architecture owner sets  19 / 19
non-empty collected target sets    19 / 19
contract quality gates              8 / 8
canonical business GET routes      22 / 22
cursor-bearing routes              12 / 12
CLI 201 + Location operations       8 / 8
```

The registry-derived target union contained 43 concrete pytest targets. Pytest expanded them to 65 cases. The JUnit verifier found all 43 requested targets, with zero missing and zero failed, errored, skipped, xfailed or rerun targets.

## M3-VER-01..19 disposition

Every row below was re-executed on the tested delivery candidate by the registry-derived mapped-target gate. The complete accepted M3 module gate and full repository gate independently re-executed the same permanent evidence.

| Bundle | Disposition | Concrete re-executed evidence |
|---|---|---|
| `M3-VER-01` | PASS | Exact eight-operation CLI `201 + Location` census, materialization and canonical success cases |
| `M3-VER-02` | PASS | Closed Location DSL, request/response carrier precedence and protocol-failure cases |
| `M3-VER-03` | PASS | Interactive and non-interactive nested create truthfulness with one primary exchange |
| `M3-VER-04` | PASS | Integrated 22-route success matrix plus family trusted-read projections |
| `M3-VER-05` | PASS | Integrated request/path-target failures and existing-target empty-page behavior |
| `M3-VER-06` | PASS | Static 22-service no-certification census plus trusted-read/write-boundary regressions |
| `M3-VER-07` | PASS | Object and lifecycle representable-surprise read boundaries |
| `M3-VER-08` | PASS | Historical lifecycle trusted-decoder boundary |
| `M3-VER-09` | PASS | Complete 12-route cursor matrix plus family cursor identity targets |
| `M3-VER-10` | PASS | Object components cross-parent cursor rejection and projection context |
| `M3-VER-11` | PASS | Object-relative Relationship cross-object cursor rejection and deduplication |
| `M3-VER-12` | PASS | True multipage traversal for all 12 cursor routes with changed limit |
| `M3-VER-13` | PASS | Global/Object lifecycle route-scope cursor distinction |
| `M3-VER-14` | PASS | HTTP omitted / UUID / exact lowercase `null` parent tri-state |
| `M3-VER-15` | PASS | CLI omission / selector / explicit-null tri-state and bounded discovery |
| `M3-VER-16` | PASS | Parent-filter cursor identity and limit compatibility |
| `M3-VER-17` | PASS | Schema, migration, dependency, lockfile and version non-drift |
| `M3-VER-18` | PASS | Exact identifier/owner/target registries, live censuses, CQGs and active governance state |
| `M3-VER-19` | PASS | 22/22 one-business-statement census and deterministic T3 BEFORE/AFTER cuts |

Disposition: `19 / 19 PASS`. This is implementer candidate evidence, not reviewer acceptance.

## Integrated read, cursor and snapshot evidence

The accepted M3 evidence-module command passed `99 / 99`. It revalidated canonical success and frozen failure behavior for all 22 GET routes, true multipage continuation for all 12 cursor routes, the complete eight-operation CLI Location matrix, the read-versus-mutation authority boundary, the lifecycle trusted-decoder boundary and the ObjectTemplate HTTP/CLI parent tri-state.

The real-PostgreSQL observer was cleared immediately before each canonical successful GET. Every route executed exactly one production `SELECT`/`WITH` business statement:

```text
DT-GET-01..04     1 / 1 / 1 / 1
OT-GET-01..06     1 / 1 / 1 / 1 / 1 / 1
OBJ-GET-01..06    1 / 1 / 1 / 1 / 1 / 1
RD-GET-01..04     1 / 1 / 1 / 1
REL-GET-01        1
LC-GET-01         1
total             22 / 22 PASS
```

The deterministic T3 RelationshipDefinition aggregate target passed both parametrized cuts with independent reader/writer sessions and bounded test-only events:

```text
AFTER   writer committed root plus both resolution fragments before the
        authoritative read; the response was the complete AFTER generation
BEFORE  authoritative statement completed before the writer commit; the
        response remained the complete BEFORE generation
result  2 / 2 PASS; no mixed generation
```

No repeatable membership or shared snapshot across separate page requests is claimed.

## Schema, migration, dependency and artifact evidence

```text
Alembic files                 0001_m2_durable_kernel.py plus __init__.py only
revision / down_revision      0001_m2_kernel / None
Alembic roots / heads         1 / 1
live current revision         0001_m2_kernel
live compare_metadata         []
metadata tables               15
project version               0.2.0
requires-python               >=3.14,<3.15
runtime dependency delta      0
schema/migration delta        0
uv.lock delta                 0
```

Authorized Git blob identities remained exact:

```text
pyproject.toml                d20bbb94739a74ebfb0bd27291b6e4f130d24c5f
uv.lock                       0aa980926fda5f42ee3a7d3cedc64f9fcf8c2d23
0001_m2_durable_kernel.py     27fc85e0b4411332fce87c406b6216b35db6eb20
```

Artifacts produced from the clean tested candidate:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `dist/netauto-0.2.0-py3-none-any.whl` | 170185 | `428a2fe05a9905f3794dd15de65667d5506fa5bef2f0568d1ca1dd2b59fb0ba2` |
| `dist/netauto-0.2.0.tar.gz` | 1048412 | `308c0a8bf643faf01ee5fc3376df3565946208f37a3826a4f6756e5bee152a04` |

No artifact was published and no release or tag was created.

## Concurrency evidence

The material real-PostgreSQL concurrency command passed `190 / 190` in `119.23s` and reported:

```text
canonical semantic-worker outcomes       312
canonical scenario IDs represented        78
transaction outcomes                     COMMITTED 214 / NO_UOW 5 / ROLLED_BACK 93
supported-path 40P01                       0
unexpected 40001                           0
negative-control outcomes                  3
negative-control SQLSTATEs                 40001 twice / 40P01 once
```

The negative-control observations are intentionally separate and prove that forbidden SQLSTATEs fail immediately and are not normalized. The independent permanent M2/current-AS-IS registry checks passed the exact authoritative `83` scenario IDs; the worker-outcome count above is not that registry census.

The complete repository run independently reported 314 canonical outcomes, 80 represented worker scenario IDs, `COMMITTED 215 / NO_UOW 6 / ROLLED_BACK 93`, supported-path `40P01 = 0`, unexpected `40001 = 0`, and the same three separate negative-control outcomes.

## Verification ledger

```text
uv lock --check
    PASS — 46 packages resolved; 0.02s

uv sync --locked
    PASS — 44 packages checked; 0.04s

uv build
    PASS — wheel and sdist built; 1.72s

uv run ruff format --check .
    PASS — 294 files already formatted; 0.06s

uv run ruff check .
    PASS; 0.05s

uv run pyright
    PASS — 0 errors, 0 warnings, 0 informations; 25.16s

uv run pytest --collect-only -q
    PASS — 990 tests collected in 1.95s; 1 reviewed warning

uv run python - <<'PY'
    [assert clean candidate; derive the sorted union from
     M3_EVIDENCE_TO_TARGETS; execute pytest with JUnit; require every mapped
     exact/parametrized case to have no failure/error/skip/xfail/rerun]
PY
    PASS — 19 bundles; 43 mapped targets; 65 passed in 22.88s;
    JUnit missing/non-pass = 0 / 0

uv run pytest -q tests/test_m3_s00_cli_location.py tests/test_m3_s01_parent_tristate.py tests/test_m3_s02_datatype_reads.py tests/test_m3_s03_objecttemplate_reads.py tests/test_m3_s04_object_reads.py tests/test_m3_s05_relationship_reads.py tests/test_m3_traceability.py tests/test_m3_s06_integration.py
    PASS — 99 passed in 27.60s

uv run pytest -q tests/test_migrations.py tests/test_schema_metadata.py
    PASS — 5 passed in 2.11s; compare_metadata == []

NETAUTO_DATABASE_URL="$TEST_DATABASE_URL" uv run alembic upgrade head
NETAUTO_DATABASE_URL="$TEST_DATABASE_URL" uv run alembic current
NETAUTO_DATABASE_URL="$TEST_DATABASE_URL" uv run alembic check
    PASS — current 0001_m2_kernel (head); no new upgrade operations

uv run pytest -q tests/test_datatype_concurrency.py tests/test_datatype_semantic_concurrency.py tests/test_objecttemplate_semantic_concurrency.py tests/test_object_semantic_concurrency.py tests/test_relationshipdefinition_semantic_concurrency.py tests/test_relationship_semantic_concurrency.py tests/test_m2_s01_semantic_concurrency.py tests/test_m2_s02_semantic_concurrency.py tests/test_m2_s03_semantic_concurrency.py
    PASS — 190 passed in 119.23s

uv run pytest -q tests/test_m2_traceability.py::test_s03_scenario_registry_targets_and_recipes_are_exact tests/test_m2_s09_acceptance.py::test_s09_final_gate_registries_are_exact_derived_and_collected
    PASS — 2 passed in 6.91s; authoritative registry = 83 IDs

uv run pytest -q -m "not postgresql"
    PASS — 706 passed, 284 deselected, 1 warning in 92.88s

uv run pytest -q
    PASS — 990 passed, 1 warning in 300.36s
```

The disposable test database was empty after fixture cleanup when an informational direct Alembic probe first ran; `current` was therefore blank and `check` reported that the target was not up to date. No repository file changed. The designated test database was explicitly upgraded to the one frozen head and the recorded `current`/`check` commands then passed. The mandatory migration/schema pytest gate had already passed and the final full suite subsequently passed.

Final normative pytest disposition:

```text
passed                 990
skipped                  0
xfail / xpass             0 / 0
automatic reruns          0
warnings                  1 — previously reviewed StarletteDeprecationWarning
```

The warning comes from FastAPI's `TestClient` import and recommends `httpx2`; no warning was hidden or normalized.

## Final diff and scope review

The final review used delivered M2 merge baseline `748d02a2c54d432617f8f46b639379188f560bc4`, prompt-publication baseline `3c3471a36939f2ee8dbe5bdf55c692204abca506`, and the tested candidate.

The M3 production diff remains limited to the five frozen observable deltas:

```text
GET/read semantic-certification responsibility correction
components cursor binds parent_object_id
Object-relative Relationship cursor binds object_id
parent_template_id adds lowercase null root-only state in HTTP/CLI
CLI Location materializer supports nested response JSON paths
```

The live OpenAPI GET set, application business GET set and frozen registry are exactly equal at 22. No route decorator was added from the M2 baseline. The cursor codec module and version did not change. Schema, migration, metadata, dependency, lockfile and project version did not change. Mutation regressions and the full suite passed, and the CLI evidence observed no hidden post-mutation enrichment GET.

The S07-only semantic diff from the prompt baseline is empty: no `src/`, schema, migration, dependency or lock file changed. S07 added no production correction. Its pre-candidate changes are limited to operational status and lifecycle-aware traceability assertions.

```text
new public route/resource               none
new response field                      none
new filter/order behavior               none beyond frozen parent null delta
offset/total-count/query DSL             none
schema/migration/dependency drift        none
new cursor format                        none
mutation semantic weakening             none
cross-request snapshot guarantee         none
hidden CLI enrichment GET                none
unrelated runtime/deployment capability  none
blocking M3 findings                     0
open incompatible reopen                 0
open blockers                            0
```

## Ownership boundary

```text
reviewer decision             PENDING / reviewer-owned
M3-S07                        not COMPLETED
M3                            not ACCEPTED or DELIVERED
final delivery approval       not granted
PR                            not created
merge / rebase / tag / release not performed
```

The candidate is ready for reviewer inspection only.
