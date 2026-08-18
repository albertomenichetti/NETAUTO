# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S05 CANDIDATE READY FOR REVIEW

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S05 — CANDIDATE READY FOR REVIEW
current task    reviewer inspection of the published M2-S05 candidate
blockers        none
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | `M2-S05` CANDIDATE READY FOR REVIEW |
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
| `M2-S04` | COMPLETED | `M2-S03 COMPLETED` |
| `M2-S05` | CANDIDATE READY FOR REVIEW | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S04` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning, technology or verification blocker is open on the `M2-S05` candidate.

`M2-S05` is limited to the official CLI HTTP core and non-interactive mode. It must preserve the completed runtime/startup/Health capability and must not begin `M2-S06` interactive REPL work before reviewer-owned completion.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S05 candidate record

Candidate state:

```text
M2-S05                         CANDIDATE READY FOR REVIEW
starting baseline              24f65b11afe72f2882a796e1c0daf6aef80bda05
implementation-start status    c8ac18e1dfcd33beb9a20468c393ba0266a20d23
implementation                 3d02fce9fe9c456e26100c3dbbbabce75bf90caf
candidate evidence/status      recorded by the commit containing this status
review result                  reviewer-owned / pending
M2-S06                         BLOCKED / not started
```

Implemented candidate:

```text
neutral wire boundary          shared request/success/page/lifecycle/error/Health DTOs
server adapters                reuse neutral DTO identities; 63 business routes unchanged
runtime dependency             HTTPX >=0.28,<1 promoted from dev to project dependency
console entrypoint             netauto = netauto.cli.main:main
CLI execution                  HTTP-only exact -n non-interactive process
remote registry                immutable 63 CommandSpec values
family census                  14 / 16 / 13 / 14 / 5 / 1
selectors                      DataType, ObjectTemplate, Object and UUID-only families
transport                      verified TLS, no redirect/retry/auth/cookie persistence
protocol                       exact 200/201/204, DTO/error/Location validation
trace                          every actual lookup and primary exchange once and ordered
process result                 one stdout JSON line; stderr empty; exit 0/1
interactive REPL/FORMATTED     not introduced; owned by blocked M2-S06
```

Candidate verification:

```text
uv lock                                               PASS — 44 packages
uv lock --check                                       PASS — 44 packages
uv sync --locked                                      PASS — 42 checked packages
uv build                                              PASS — sdist + wheel 0.1.0
Ruff format/check                                     PASS — 213 files
Ruff lint                                             PASS
Pyright                                               PASS — 0 errors
pytest collection                                     630 tests
M2-VER-27 primary S05 targets                         67 passed — 11.64 s
M2-VER-24 bounded supporting targets                   7 passed — 8.69 s
M2-VER-28 registry/selector supporting targets        19 passed — 1.53 s
M2-VER-30 transport-security supporting targets        9 passed — 3.72 s
DTO/API/S04 affected regressions                     115 passed — 39.54 s
schema metadata / migrations                           5 passed — 2.17 s
M1 / S00 / M2 traceability                            23 passed — 14.13 s
PostgreSQL concurrency marker                        182 passed — 116.69 s
non-PostgreSQL                                       379 passed — 31.68 s
full repository suite                                630 passed — 197.59 s
skip / xfail / rerun                                   0 / 0 / 0
warning census                                         1 locked FastAPI/Starlette deprecation
supported-path 40P01 / unexpected 40001                0 / 0
```

Environment and unchanged boundaries:

```text
CPython                         3.14.7
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                              0.12.3
authoritative tables            15
Alembic graph                   one base / one head
root migration                  0001_m2_kernel unchanged
metadata/schema/index diff      none
project version                 0.1.0 unchanged
dependency / lock delta         HTTPX promotion only; no package version churn
business HTTP operations        41 mutations + 22 reads = 63 exact
operational HTTP operations      1 Health; total public HTTP = 64
CLI remote operations           63 exact; Health excluded
scenario / predicate registries 83 / 21 unchanged
GitHub Actions/PR               not used / not created
```

`M2-VER-27` is candidate `PASS`. The `M2-VER-24`, `M2-VER-28` and
`M2-VER-30` entries are bounded S05 supporting evidence only; their primary
slice ownership remains S07, S06 and S07 respectively. `M2-VER-25/26/29/31/32`
remain `DESIGNED`. No S06 capability was started.

The sole warning is the already known deprecation emitted by the locked
FastAPI/Starlette test-client path. It caused no skip, xfail, rerun or failure.
No blocking implementation, architecture or documentation finding remains open
on the candidate. M2-S05 is not `COMPLETED`; reviewer inspection is pending.

## M2-S04 completion record

Reviewer result:

```text
M2-S04                         COMPLETED
original prompt                43b2c42188af35db650b1e7badecf39038987566
initial implementation         dc18d5dcca586b6c64ae6912921448318db8e27c
initial candidate status       765ef4bb356776555f89fe98e5387ed6b1b7de49
review changes record          5a3cac401141c783e4ef8881bffac2816df856a1
review-fix prompt              4c52427efb994de47677f0d4f6561838a12d38de
corrective implementation      67d375bddb00c71687d4ecc51e83566537c51687
corrected evidence/status      d43824aef23915c6a3fc3d4fff1f7e9cfdbcba55
review acceptance              recorded by the commit containing this status
M2-S05                         READY / not started
```

Closed findings:

```text
S04-RF-01
    Settings validation hides input carriers and production loading maps finite
    expected failures to bounded bootstrap categories. Expected installed-graph,
    database-inspection and owned-timeout failures suppress raw causes/contexts.
    Factory, ASGI lifespan and Uvicorn logging evidence proves that credentials,
    host/port, SQL, SQLSTATE, filesystem and driver sentinels are not disclosed.
    Unexpected programming defects and cancellation remain unnormalized.

S04-RF-02
    Health and startup guards classify TimeoutError as an owned timeout only when
    the corresponding asyncio timeout object reports expiration. An inner timeout
    propagates as unexpected and reaches the canonical safe HTTP 500 boundary;
    owned/probe timeouts retain the exact bounded 503 result.

S04-RF-03
    M2-VER-22 and M2-VER-23 now have exact comprehensive, machine-resolvable target
    membership. S04_REVIEW_FIX_TARGETS owns exactly the three review findings.
    Installed-wheel evidence proves Health 200 -> 503 -> 200 inside one lifespan,
    on one runtime engine, without reconstructing the runtime or startup guard.
```

Accepted S04 capability:

```text
Settings fields                 7 exact immutable runtime values
source precedence               constructor > environment > explicit secret files > defaults
secret selector                 absolute existing NETAUTO_SECRETS_DIR only; no implicit source
runtime engine                  one bounded lazy AsyncEngine per app/worker
engine consumers                mutation/read UoW, startup guard and Health share identity
startup guard                   installed netauto:migrations head == actual singleton head
guard timeout                   fixed 10.0 seconds; no retry, migration, stamp or repair
lifespan order                  guard before state publication and serving
engine cleanup                  normal, failed, post-composition and cancelled paths
Health probe                    exact SELECT 1 on the shared engine
Health timeout                  fixed 2.0 seconds including checkout and cleanup
operational API                 GET /health/core only
HTTP result families            exact 200 / 503 / 400 / canonical 500
route inventory                 63 business + 1 operational = 64
M2-VER-22 / M2-VER-23           IMPLEMENTED and accepted
```

Accepted verification:

```text
uv lock --check                                      PASS
uv sync --locked                                     PASS
uv build                                             PASS
Ruff format/check                                    PASS
Ruff lint                                            PASS
Pyright                                              PASS — 0 errors
pytest collection                                    561 tests
S04-RF-01 exact targets                               12 passed
S04-RF-02 exact targets                                9 passed
S04-RF-03 exact targets                                2 passed
focused S04/cross-boundary bundle                    140 passed
schema metadata / migrations                           5 passed
M1 / S00 / M2 traceability                            21 passed
PostgreSQL concurrency marker                        182 passed
non-PostgreSQL                                       310 passed
full repository suite                                561 passed
post-push full rerun on exact remote candidate       561 passed — 190.57 s
skip / xfail / rerun                                   0 / 0 / 0
supported-path 40P01 / unexpected 40001                0 / 0
installed-wheel 200 -> 503 -> same-engine 200        PASS
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
CLI / packaging / S05 surface   none introduced by S04
GitHub Actions/encoded payloads absent
```

The accepted run emitted one dependency deprecation warning in the locked FastAPI/Starlette test path. It caused no skip, xfail, rerun or failure and is not a slice blocker.

Reviewer inspection verified the published commit chain, production delta, timeout ownership, full bootstrap diagnostic boundary, installed-wheel behavior, traceability and unchanged schema/public boundaries. The reviewer did not independently re-execute the 561-test suite in this inspection; the accepted execution results are those produced and recorded by the corrected candidate.

No blocking review finding remains open for `M2-S04`.

The concluded S04 execution aids were retired from the working tree by the same reviewer-owned acceptance commit:

```text
docs/milestones/M2/wip/M2-S04-codex-prompt.md
docs/milestones/M2/wip/M2-S04-review-fixes-codex-prompt.md
```

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
candidate evidence/status      8168aeb3a8e1dedd97afcd22f9da314d689333
review acceptance              d225faee6faf5fbebd36ce68db6c3b2c537323d0
full suite                     PASS (314)
```

No blocking review finding remains open for `M2-S00`.

## Immediate next action

Prepare the non-normative Codex implementation prompt for:

```text
M2-S05 — Official CLI HTTP core and non-interactive mode
```

Before implementation, execute the mandatory repository-based pre-flight for `M2-S05`, including the completed S04 runtime/Health boundary and the frozen CLI architecture/verification authorities. Do not start `M2-S06`.

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
