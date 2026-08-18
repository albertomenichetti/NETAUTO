# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S04 REVIEW CHANGES REQUIRED

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S04 — REVIEW CHANGES REQUIRED
current task    prepare and execute the bounded M2-S04 review-fix prompt
blockers        S04-RF-01, S04-RF-02 and S04-RF-03
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | `M2-S04` REVIEW CHANGES REQUIRED — bounded fixes only |
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
| `M2-S04` | REVIEW CHANGES REQUIRED | `M2-S03 COMPLETED` |
| `M2-S05` | BLOCKED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00`, `M2-S01`, `M2-S02` and `M2-S03` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and reviewed findings

No contract, architecture, implementation-planning or technology contradiction is open. The published S04 candidate implements the principal runtime and Health capability, but three bounded implementation/evidence defects remain. They are corrected inside `M2-S04`; no architecture reopen is required.

### `S04-RF-01` — expected bootstrap failures retain sensitive raw causes

Reviewed implementation:

```text
Settings
    validation errors are allowed to retain the original input carrier

schema guard
    MigrationGraphInvalid / SchemaGuardUnavailable / timeout wrappers
    are raised with explicit raw causes
```

The top-level messages are bounded, but that is not the complete startup diagnostic boundary. Starlette formats the complete lifespan exception traceback and Uvicorn logs the `lifespan.startup.failed` message. A Pydantic validation failure may therefore include the input database URL, and an expected graph/DB failure may include a chained filesystem, SQLAlchemy or driver exception containing DSN, host, SQL or protocol material.

This violates the frozen requirement that ordinary startup diagnostics do not disclose database URLs, credentials, host/port, raw SQL, driver internals or unbounded exception detail.

Required correction:

```text
production Settings loading
    -> invalid values produce one bounded bootstrap exception
    -> validation rendering/traceback does not include input values
    -> credential-bearing database_url is absent from str/repr/traceback/log output

expected graph / database / timeout failures
    -> bounded bootstrap exceptions only
    -> no outward raw __cause__ / unsuppressed __context__
    -> no leakage through the real ASGI lifespan failure message or Uvicorn logging

unexpected programming defects
    -> remain unexpected and are not silently normalized
```

Permanent evidence must exercise the real production composition boundary, not merely `str(top_level_exception)`. It must capture the actual lifespan/startup diagnostic for credential-bearing invalid Settings, unreadable graph, unreachable/query failure and timeout, and assert that secrets, URL/host, SQL, SQLSTATE and raw driver text are absent.

### `S04-RF-02` — an inner `TimeoutError` is misclassified as database not-ready

`CoreHealthService.check()` currently catches bare `TimeoutError` around the complete probe call. This correctly handles expiration of the owned `asyncio.timeout(2.0)` context, but it also catches a `TimeoutError` raised directly by an unexpected probe/programming path before the owned deadline expires.

The latter is not an ordinary readiness outcome. Under the frozen Health boundary it must propagate to the existing unexpected-failure handler and produce the canonical safe HTTP `500`, not a false `503` with `"database readiness check timed out"`.

Required correction:

```text
owned outer two-second deadline expires
    -> bounded Health 503 timeout result

PostgreSQLHealthProbe raises DatabaseProbeTimedOut
    -> bounded Health 503 timeout result

unexpected inner/raw TimeoutError while the owned deadline did not expire
    -> propagate
    -> canonical safe HTTP 500
```

The implementation may use the timeout context's expiration state or another equally explicit owned-timeout discriminator. It must preserve cancellation propagation, one attempt, cleanup-before-measurement and the real pool-starvation behavior already passing.

### `S04-RF-03` — M2-VER-22/23 traceability and installed evidence overstate closure

The singular registry correctly marks only `M2-VER-22` and `M2-VER-23` as newly implemented, but their current target sets omit mandatory parts of the frozen evidence.

At minimum, the exact bundle membership must include permanent targets for:

```text
M2-VER-22
    unreadable installed graph
    unreachable / query-failing database
    malformed or indeterminate current-head result
    cancelled and post-engine composition-failure disposal
    complete safe lifespan diagnostic boundary from S04-RF-01

M2-VER-23
    unexpected inner TimeoutError -> safe 500 from S04-RF-02
    unexpected failure and cancellation propagation
    finite probe translation / no raw-message leakage
    negative no-Alembic/no-second-engine/no-UoW Health surface
    installed-wheel runtime not-ready 503 after successful startup,
        followed by recovery on the same installed runtime engine
```

Existing tests may be reused when they prove the exact assertion, but they must be explicitly linked in `S04_BUNDLE_TARGETS`; missing assertions require new deterministic targets. Every target must resolve against the actual pytest collection and be executed in the corrected candidate gate.

Bundles `M2-VER-24` and later remain `DESIGNED`. The 63-operation business registry remains separate from the single operational Health route.

## M2-S04 reviewed candidate record

Reviewer result:

```text
M2-S04                         REVIEW CHANGES REQUIRED
review baseline                43b2c42188af35db650b1e7badecf39038987566
implementation/evidence        dc18d5dcca586b6c64ae6912921448318db8e27c
candidate status               765ef4bb356776555f89fe98e5387ed6b1b7de49
open findings                  S04-RF-01, S04-RF-02, S04-RF-03
M2-S05                         BLOCKED / not started
```

Conforming material to preserve:

```text
Settings fields                 7 exact immutable runtime values
source precedence               constructor > environment > explicit secret files > defaults
secret selector                 absolute existing NETAUTO_SECRETS_DIR only; no implicit source
runtime engine                  one bounded lazy AsyncEngine per app/worker
engine consumers                mutation/read UoW, startup guard and Health share identity
startup guard                   installed netauto:migrations head == actual singleton head
guard timeout                   fixed 10.0 seconds; no retry, migration, stamp or repair
lifespan order                  guard before state publication/serving
engine cleanup                  normal, failed, post-composition and cancelled paths
Health probe                    exact SELECT 1 on the shared engine
Health timeout                  fixed 2.0 seconds including checkout and cleanup
operational API                 GET /health/core only
HTTP result families            exact 200 / 503 / 400 / canonical 500
route inventory                 63 business + 1 operational = 64
schema/dependencies             unchanged
```

Candidate-reported verification:

```text
uv lock --check                                      PASS — 0.03 s
uv sync --locked                                     PASS — 0.03 s
uv build                                             PASS — 1.58 s
Ruff format/check                                    PASS
Ruff lint                                            PASS
Pyright                                              PASS — 0 errors
pytest collection                                    543 tests
focused S04/cross-boundary bundle                    122 passed — 25.61 s
schema metadata / migrations                           5 passed — 2.20 s
M1 / S00 / M2 traceability                            20 passed — 12.58 s
PostgreSQL concurrency marker                        182 passed — 117.15 s
non-PostgreSQL                                       292 passed — 19.18 s
full repository suite                                543 passed — 185.19 s
skip / xfail / rerun                                   0 / 0 / 0
supported-path 40P01 / unexpected 40001                0 / 0
installed-wheel smoke                                PASS
```

Environment and unchanged boundaries:

```text
CPython                         3.14.7
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                              0.12.3
authoritative tables            15
Alembic graph                   one base / one head
root migration                  0001_m2_kernel unchanged
metadata drift                  compare_metadata == []
schema / migration / index diff none
dependency / uv.lock diff       none
business HTTP operations        41 mutations + 22 reads = 63 exact
operational HTTP operations      1 Health; total public HTTP = 64
scenario / predicate registries 83 / 21 unchanged
CLI / packaging / S05 surface   none introduced
GitHub Actions/encoded payloads absent
```

The reported runs remain useful candidate evidence. The reviewer did not independently re-execute the 543-test suite during this inspection. The three findings identify paths not exercised or not represented by the current mandatory target set.

The non-normative S04 prompt remains in `wip/` while the slice is open.

## M2-S03 completion record

Reviewer result:

```text
M2-S03                         COMPLETED
original prompt                29e490087b24f1ff17d1e4be1abc629b0be3a962
initial implementation         f70ec8968ddef3bd106749b14def0e5cde9688e3
partial evidence/status        1c2dd13b6e5e57310db6f12f0a6d8307c35bda67
review changes record          8ddcfdca85e73b64c5e3bc603d8611d0ffb2eb1c
review-fix prompt              96145aa7621bac760b0ce57c21f62e9c9f4df0fd
corrective implementation      2e8edb707c7f9f0c343532cf18426b70ae215ad4
corrected evidence/status      33803f1c50ced716490541099357e2d74eb742a8
corrected provenance           5f28678fd762fb0c3945747cc7c8d9ffbfa4be19
review acceptance              2b89f4ce79272554721ff694dd8ae8e32e7fab25
full suite                     PASS (446)
```

No blocking review finding remains open for `M2-S03`.

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
review acceptance              850abd97ece1aadeae65aa090d86c7ec4982751f
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
review acceptance              24e7b788b6b7f54d96614ef2c37bffbeb25ebd8b
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
review acceptance              d225faee6faf5fbebd36ce68db6c3b2c537323d0
full suite                     PASS (314)
```

No blocking review finding remains open for `M2-S00`.

## Immediate next action

Prepare the non-normative corrective execution aid:

```text
docs/milestones/M2/wip/M2-S04-review-fixes-codex-prompt.md
```

The correction remains inside `M2-S04` and is limited to `S04-RF-01`, `S04-RF-02` and `S04-RF-03`. Do not start `M2-S05`.

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
