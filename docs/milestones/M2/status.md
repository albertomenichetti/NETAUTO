# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S07 IN PROGRESS

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S07 — IN PROGRESS
current task    implement the authorized M2-S07 release and installed-runtime baseline
blockers        externally supplied TEST_DATABASE_URL is unavailable for mandatory T9/PostgreSQL gates
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | IN PROGRESS — `M2-S07` ONLY |
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
| `M2-S05` | COMPLETED | `M2-S04 COMPLETED` |
| `M2-S06` | COMPLETED | `M2-S05 COMPLETED` |
| `M2-S07` | IN PROGRESS | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S06` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning or technology blocker is open for `M2-S07`. The externally supplied `TEST_DATABASE_URL` is currently unavailable, so PostgreSQL-backed T9 and complete repository gates remain blocked while bounded implementation continues.

`M2-S07` is limited to the versioned wheel, installed Alembic graph and documented/executed Linux operating baseline. It must consume the completed server, runtime, Health and CLI capabilities without changing their frozen public or semantic contracts. It must not begin `M2-S08` integrated traceability/negative-surface closure before reviewer-owned completion.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S07 in-progress implementation record

The bounded release implementation is present but is not a candidate-ready handoff.
The required external PostgreSQL target was not present in the execution
environment, so the installed migration/server T9 targets, PostgreSQL regressions,
concurrency gate, complete suite, and exact-remote post-push rerun have not passed.

Implemented boundaries:

```text
release version                  0.2.0
canonical wheel                  netauto-0.2.0-py3-none-any.whl
embedded runtime lock            netauto/release/runtime.pylock.toml
runtime package census           29 total / 27 applicable on Linux CPython
installed target                 wheel-only / outside checkout / --no-deps app install
installed Alembic                package-resource graph and explicit real-PG harness
Linux operation                  versioned layout, protected secret, foreground lifecycle
CLI operation                    installed PTY and HTTP/HTTPS subprocess harness
traceability                     M2-VER-24 / 29 / 30 plus installed support 22/23/25-28
schema / migration DDL           unchanged
API / CLI semantics              unchanged
M2-S08 / M2-S09                  not started
```

Verified before partial publication:

```text
uv lock --check                  PASS — 46 packages resolved
uv sync --locked                 PASS
uv build                         PASS — 0.2.0 sdist + canonical wheel
Ruff format / lint               PASS — 230 files / no findings
Pyright strict                   PASS — 0 errors / warnings
pytest collection                780 tests / 1 locked deprecation warning
focused S07 non-PostgreSQL       11 passed / 3 real-PG targets deselected
M2 traceability                  21 passed
all non-PostgreSQL               526 passed / 254 deselected / 1 warning
skip / xfail / rerun             0 / 0 / 0 in executed gates
```

Pre-publication release facts:

```text
wheel size / members             166001 bytes / 77
wheel SHA-256                    16618ff26686fb6a44b994593f28c252bf2a0409790d7d59a68d5e324f02e503
runtime lock size                48238 bytes
runtime lock SHA-256             0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
migration checksum               379165a1eda83c226a6c1e5dc4f493c7fa0d0c8dba39449a1d004751aaa39c57
CPython / uv / target OS         3.14.7 / 0.12.3 / Ubuntu 24.04.4 LTS x86_64
```

`uv 0.12.3` accepts only `pylock.toml` or `pylock.<name>.toml` as a
PEP 751 input/output basename. Generation and synchronization therefore use the
byte-identical temporary carrier `pylock.runtime.toml`, while the committed and
installed canonical package resource remains `runtime.pylock.toml`. Permanent
verification regenerates the same relative carrier in a disposable project copy
and requires byte-for-byte equality.

Blocked verification:

```text
TEST_DATABASE_URL                missing
S07 installed explicit migration not executed
S07 pre-start/start/Health/stop/restart/mismatch not executed
S07 real-PG transport-cut 503    not executed
PostgreSQL concurrency gate      not executed
complete repository suite        not executed
post-push exact-remote T9/suite  not eligible while the mandatory target is absent
candidate-ready transition       forbidden
```

## M2-S06 completion record

Reviewer result:

```text
M2-S06                         COMPLETED
original prompt                e0ad43277fb214ed3f97e275416304f0130ff471
initial implementation         e0c7a55bdbb066437fb0189ebcb781b834c476d6
initial candidate evidence     8d4074f57b214d158d288a65dccde15156bcd812
first review record            827c15ccf16f89630f975f1b3faa644f0a709c27
review-fix prompt              a0a97e60074004e44be6a54e19378de6f2e24681
corrective implementation      f9c463fc30856b56ffb0ef0d49d5ca11d558c1ce
corrected evidence/status      ea25b47ee4a78496180ea1c00e13b482ac1ed85b
review acceptance              recorded by the commit containing this status
M2-S07                         READY / not started
```

Closed findings:

```text
S06-RF-01
    Selector planning now records immutable exact identities in registry-owned
    discovery order. Execution derives one FORMATTED-only PresentationTarget from
    the already-resolved command/request plan. Human intent remains visible when
    distinct, while exact UUIDs and identifying path versions remain visible even
    for bodyless or nullable direct results. No recovery or post-mutation GET is
    introduced. CliResult, interactive JSON and the accepted S05 trace schema are
    unchanged.

S06-RF-02
    Every secondary DataType, ObjectTemplate and Object GET validates returned
    identity before cache insertion. Exact ObjectTemplateVersion GETs validate
    both template_id and version. Parent traversal retains exact-pair protection
    and adds a repeated-public-template-ID termination guard. The guard is client
    request/response correlation and finite traversal protection over public DTO
    identities; it imports no domain or persistence authority and does not
    reimplement mutation admission or model certification. Mismatch/repetition
    yields cli_protocol_error, no partial presentation, truthful ordered trace and
    preserves CONNECTED unless the failure is transport-level.
```

Accepted S06 capability:

```text
runtime dependency             prompt-toolkit >=3.0,<4; resolved 3.0.53
process routing                no argv -> async REPL; exact -n unchanged; other argv invalid
initial session                DISCONNECTED / FORMATTED / empty in-memory history
local commands                 8 / 8 exact
remote commands                63 / 63 exact; shared accepted registry/parser
session transport              at most one endpoint-scoped persistent HTTPX client
command isolation              fresh ledger and selector/enrichment memo per command
Health state                   exact /connect and /status ready-200 validation
terminal behavior              Ctrl-R / Ctrl-C editing / Ctrl-D / clear / exit
help/history                    registry-derived help; process-local chronological history
formatted rendering            every installed renderer key resolves deterministically
bounded enrichment             9 exact single-read shapes; GET-only / complete-or-fail
formatted target identity      human intent + exact resolved IDs without extra HTTP
JSON mode                      accepted S05 result/trace shape; no presentation enrichment
mutation/list behavior         direct primary result only; no hidden item/post-mutation GET
HTTP-only boundary             no application, persistence, DB-driver or Alembic execution path
```

Accepted verification:

```text
uv lock --check                PASS — 46 packages resolved
uv sync --locked               PASS — 44 packages checked
uv build                       PASS — sdist + wheel 0.1.0
Ruff format/lint               PASS — 224 files
Pyright strict                 PASS — 0 errors
pytest collection              765 tests
S06-RF-01                      6 selectors / 6 passed
S06-RF-02                      6 selectors / 9 passed
review-fix union               11 unique selectors / 14 passed
M2-VER-25 complete             26 passed
M2-VER-26 complete             18 passed
M2-VER-28 S05 + S06 complete   56 passed
M2-VER-27 accepted S05         126 passed
all M2-S06                     72 passed
all M2-S05                     126 passed
Health / S04 affected          77 passed
API route / DTO inventory      67 passed
traceability / schema/migrate  32 passed
PostgreSQL concurrency         182 passed
non-PostgreSQL                 514 passed
full repository suite          765 passed
post-push exact remote run     765 passed — 211.12 s
skip / xfail / rerun           0 / 0 / 0
warning census                 1 locked FastAPI/Starlette deprecation
supported 40P01 / 40001        0 / 0
negative-control 40P01 / 40001 1 / 2, expected and immediate
```

Environment and unchanged boundaries:

```text
CPython                        3.14.7
PostgreSQL                     16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                             0.12.3
prompt-toolkit                 3.0.53
project version                0.1.0
corrective dependency/lock diff none
authoritative tables           15
Alembic bases / heads          1 / 1
root revision                  0001_m2_kernel
compare_metadata               []
schema / migration / index diff none
business HTTP operations       41 mutations + 22 reads = 63 exact
operational HTTP operations    1 Health; total public HTTP = 64
CLI local / remote operations  8 / 63 exact
CLI family census              14 / 16 / 13 / 14 / 5 / 1
registry examples              65 parser-valid
enrichment entry points        9 exact
scenario / predicate registries 83 / 21
S07 runtime-lock/release/Linux absent / not started at reviewed candidate
GitHub Actions / PR            absent / not created
```

`M2-VER-25`, `M2-VER-26` and the S06-owned complete `M2-VER-28` evidence are accepted. `M2-VER-27` and every S05 review-fix boundary remain preserved. `M2-VER-24`, `M2-VER-29` and `M2-VER-30` retain their S07 primary ownership; `M2-VER-31` and `M2-VER-32` remain S08-owned.

Reviewer inspection verified the published commit chain, exact corrected production delta, immutable target presentation, response-identity correlation, finite traversal guard, truthful traces, connection consequences, permanent finding registry and unchanged API/schema/dependency boundaries. The reviewer did not independently re-execute the 765-test suite; the accepted execution results are the candidate's exact-remote evidence.

The implementer reported one pre-publication aggregate PTY run that did not observe the Ctrl-R sentinel. The isolated target, complete S06 group and exact-remote full suite then passed without terminal-code changes or a generic retry mechanism. This was not reproducible and is recorded as a non-blocking execution-environment observation; T8 is re-executed by the S09 final gate.

No blocking review finding remains open for `M2-S06`.

The concluded S06 execution aids were retired from the working tree by the same reviewer-owned acceptance commit:

```text
docs/milestones/M2/wip/M2-S06-codex-prompt.md
docs/milestones/M2/wip/M2-S06-review-fixes-codex-prompt.md
```

## M2-S05 completion record

Reviewer result:

```text
M2-S05                         COMPLETED
original prompt                24f65b11afe72f2882a796e1c0daf6aef80bda05
initial implementation         3d02fce9fe9c456e26100c3dbbbabce75bf90caf
initial candidate evidence     c1365c1c951447ed3f22cd54bcb1effcf41043ee
first review record            77b682bac31f6c2e7a8befa2b5a18d98330fb4ea
first review-fix prompt        2f43b21d66d318fcc43c2595bdf893fc6f395d53
first corrective implementation 1015dd5ea86b15e8248c9a5e2fe518fe98e2b637
first corrective evidence      eb8ff673ad1ea77179194493b712dcc0497b5835
first corrective provenance    372d2954f206ae99f3935d3ee36d28a50f9fb72e
second review record           7bfcdc5059de1742c2c211b4edb34c0879f31234
residual review-fix prompt     01d12f821ccd1a5d09ea15f4830e9a844ee5ced1
residual implementation        4e23af5dd4fd1f3ac3c7c343637fcad9a4906660
residual evidence/status       2bd40d4ce358e6bd20d86973544441e9830ed563
residual provenance            00f81aafbabdcd5e6bbf66b8271e3aab33cadea8
review acceptance              recorded by the commit containing this status
M2-S06                         READY / not started
```

Closed findings:

```text
S05-RF-01
    The ordinary-Exception boundary spans parsing and execution while expected
    ParseFailure values retain their finite local classification. ParseProgress
    preserves only a safely materialized immutable partial command. The command-
    scoped ExecutionLedger owns an HTTP attempt immediately before send, exposes
    in-flight attempts in snapshots, observes a returned response before later
    fallible processing and finalizes each attempt exactly once. Unexpected send,
    response-capture, exchange-cleanup and context-cleanup failures therefore
    preserve a truthful ordered trace. BaseException families remain unnormalized.

S05-RF-02
    Endpoint roots distinguish an absent port from an explicit ASCII-decimal port.
    Empty, zero, signed, nonnumeric and out-of-range hostname or bracketed-IPv6
    ports fail locally without a command or HTTP exchange.

S05-RF-03
    Command, plan, error, request/response trace and result values use recursive
    immutable JSON snapshots. Public serialization returns detached ordinary JSON
    carriers and repeated rendering is byte-stable.

S05-RF-04
    All 63 CommandSpec values own meaningful help/selector/parameter metadata,
    renderer metadata and parser-valid examples. The 65 examples include both
    discriminated RelationshipDefinition CREATE and RENAME forms and resolve to
    their own installed registry key without HTTP execution.
```

Accepted S05 capability:

```text
neutral HTTP wire authority       shared request/success/page/lifecycle/error/Health DTOs
server adapter reuse              neutral DTO identities; server contract unchanged
runtime dependency                HTTPX >=0.28,<1 promoted from dev to project runtime
console entrypoint                netauto = netauto.cli.main:main
non-interactive grammar           exact netauto -n endpoint resource operation form
remote registry                   63 immutable business CommandSpec values
registry examples                 65 parser-valid examples
family census                     14 / 16 / 13 / 14 / 5 / 1
selectors                         deterministic top-level/nested resolution and one-command cache
transport                         verified TLS; no redirect/retry/auth/cookie persistence
protocol                          exact 200/201/204, business-error and Location validation
trace                             every attempted exchange once, ordered and immutable
unexpected failures               bounded ordinary failures with truthful partial intent/trace
process contract                  one JSON stdout line; empty stderr; exit 0/1
interactive REPL/FORMATTED        absent; owned by M2-S06
```

Accepted verification:

```text
uv lock --check                                       PASS — 44 packages
uv sync --locked                                      PASS — 42 checked packages
uv build                                              PASS — sdist + wheel 0.1.0
Ruff format/check                                     PASS — 218 files
Ruff lint                                             PASS
Pyright                                               PASS — 0 errors
pytest collection                                     691 tests
residual S05-RF-01 registry                           23 selectors / 35 passed
complete S05-RF-01 target set                         35 passed
all S05 tests                                         126 passed
M2-VER-27 primary S05                                 126 passed
M2-VER-24 bounded support                               7 passed
M2-VER-28 bounded support                              27 passed
M2-VER-30 bounded support                              30 passed
DTO/API/route inventory                               57 passed
S04 Settings/startup/Health                          121 passed
schema metadata / migrations                           5 passed
M1 / S00 / M2 traceability                            25 passed
PostgreSQL concurrency marker                        182 passed
non-PostgreSQL                                       440 passed
full repository suite                                691 passed
post-push full rerun on exact remote candidate       691 passed — 205.18 s
skip / xfail / rerun                                   0 / 0 / 0
warning census                                         1 locked FastAPI/Starlette deprecation
supported-path 40P01 / unexpected 40001                0 / 0
negative-control 40P01 / 40001                         1 / 2, expected and immediate
```

Environment and unchanged boundaries:

```text
CPython                         3.14.7
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                              0.12.3
authoritative tables            15
Alembic bases / heads           1 / 1
root revision                   0001_m2_kernel
compare_metadata                []
project version                 0.1.0
schema / migration / index diff none
residual dependency / lock diff none
business HTTP operations        41 mutations + 22 reads = 63 exact
operational HTTP operations      1 Health; total public HTTP = 64
CLI remote operations           63 exact
scenario / predicate registries 83 / 21
GitHub Actions / PR             absent / not created
```

`M2-VER-27` is accepted as the primary S05 bundle. The S05 work for `M2-VER-24`, `M2-VER-28` and `M2-VER-30` remains bounded supporting evidence; their primary ownership remains `M2-S07`, `M2-S06` and `M2-S07` respectively. `M2-VER-25`, `M2-VER-26`, `M2-VER-29`, `M2-VER-31` and `M2-VER-32` remain owned by later slices.

Reviewer inspection verified the published commit chain, production delta, parser progress boundary, attempt lifecycle, response preservation, process regressions, installed-wheel evidence, traceability and unchanged public/schema boundaries. The reviewer did not independently re-execute the 691-test suite during this inspection; the accepted execution results are those produced and recorded by the residual candidate.

No blocking review finding remains open for `M2-S05`.

The concluded S05 execution aids were retired from the working tree by the same reviewer-owned acceptance commit:

```text
docs/milestones/M2/wip/M2-S05-codex-prompt.md
docs/milestones/M2/wip/M2-S05-review-fixes-codex-prompt.md
docs/milestones/M2/wip/M2-S05-residual-review-fix-codex-prompt.md
```

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
review acceptance              bd342146679e405365ab93e4a60ca85b60834161
full suite                     PASS (561)
```

No blocking review finding remains open for `M2-S04`.

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
original implementation        c019cada4152e9798e25476d35b0cec5127d6135
original candidate status      63c0e772df4c73c439b7b4baed67b3d11fc809b9
review changes record          e5728486ace14bf525fa3f5df51d7c18e87b957c
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

Prepare the implementation execution aid and execute:

```text
M2-S07 — Versioned wheel, installed Alembic and Linux operating baseline
```

Do not start `M2-S08` before reviewer-owned completion of `M2-S07`.

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
