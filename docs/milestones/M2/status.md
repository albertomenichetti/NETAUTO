# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S06 CANDIDATE READY FOR REVIEW

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S06 — CANDIDATE READY FOR REVIEW
current task    reviewer inspection of the published M2-S06 candidate
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
| Implementation | AUTHORIZED — `M2-S06` ONLY |
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
| `M2-S06` | CANDIDATE READY FOR REVIEW | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S05` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning, technology or verification blocker is open for starting `M2-S06`.

`M2-S06` is limited to the official interactive CLI REPL and formatted experience. It must consume the completed S05 HTTP core, registry, selector, protocol, trace and non-interactive authorities without creating a second command model. It must not begin `M2-S07` versioned-wheel, installed-Alembic or Linux operating-baseline work before reviewer-owned completion.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S06 candidate record

Candidate state:

```text
M2-S06                         CANDIDATE READY FOR REVIEW / not COMPLETED
starting baseline              e0ad43277fb214ed3f97e275416304f0130ff471
implementation                 e0c7a55bdbb066437fb0189ebcb781b834c476d6
candidate evidence/status      commit containing this record
M2-S07                         BLOCKED / not started
```

Implemented scope:

```text
runtime dependency             prompt-toolkit >=3.0,<4; resolved 3.0.53
process routing                no argv -> async REPL; exact -n unchanged; other argv invalid
initial session                DISCONNECTED / FORMATTED / empty in-memory history
local commands                 8 / 8 exact
remote commands                63 / 63 exact; same accepted registry and shared parser
session transport              at most one endpoint-scoped persistent HTTPX client
command isolation              fresh ledger and selector/enrichment memo per command
Health state                   exact /connect and /status ready-200 validation
terminal behavior              Ctrl-R / Ctrl-C / Ctrl-D / clear / exit verified on Linux PTY
formatted rendering            every installed renderer key resolves
bounded enrichment             all 9 frozen single-read shapes; GET-only / complete-or-fail
JSON mode                      accepted S05 shape; no presentation enrichment
mutation/list behavior         direct primary result only; zero hidden item/post-mutation GET
```

Traceability:

```text
M2-VER-25                      IMPLEMENTED — 17 permanent targets
M2-VER-26                      IMPLEMENTED — 12 permanent targets
M2-VER-28                      IMPLEMENTED — 7 S06 primary targets
M2-VER-28 S05 support          preserved — 19 targets
M2-VER-27                      IMPLEMENTED / accepted S05 ownership preserved
M2-VER-29 / 31 / 32            DESIGNED; not overclaimed
```

Executed pre-publication verification:

```text
uv lock                        PASS — prompt-toolkit + wcwidth only
uv lock --check                PASS — 46 packages resolved
uv sync --locked               PASS — 44 packages checked
uv build                       PASS — sdist + wheel 0.1.0
Ruff format/check              PASS — 222 files
Ruff lint                      PASS
Pyright strict                 PASS — 0 errors
pytest collection              751 tests
M2-VER-25 runtime group         26 passed
M2-VER-26 runtime group         18 passed
M2-VER-28 S06 runtime group     15 passed
S06 + traceability              78 passed
S05 + S06                      185 passed
all S05 regressions            126 passed
Health / S04 affected          111 passed — 1 locked warning
traceability / schema / migrate 31 passed
PostgreSQL concurrency         182 passed, 569 deselected — 117.75 s
non-PostgreSQL                 500 passed, 251 deselected — 43.47 s
full repository suite          751 passed — 210.35 s
skip / xfail / rerun             0 / 0 / 0
warning census                   1 locked FastAPI/Starlette deprecation
supported 40P01 / 40001          0 / 0
negative-control 40P01 / 40001   1 / 2, expected and immediate
```

Environment and unchanged boundaries:

```text
CPython                        3.14.7
PostgreSQL                     16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
uv                             0.12.3
prompt-toolkit                 3.0.53
authoritative tables           15
Alembic bases / heads          1 / 1
root revision                  0001_m2_kernel
compare_metadata               []
project version                0.1.0
schema / migration / index diff none
dependency / lock delta        prompt-toolkit + transitive wcwidth only
business HTTP operations       41 mutations + 22 reads = 63 exact
operational HTTP operations    1 Health; total public HTTP = 64
CLI remote operations          63 exact
CLI family census              14 / 16 / 13 / 14 / 5 / 1
registry examples              65 parser-valid
scenario / predicate registries 83 / 21
S07 runtime-lock/release/Linux absent / not started
GitHub Actions / PR            absent / not created
```

No architecture or documentation finding remains open from implementation. This record does not assign reviewer-owned completion.

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

Review the published implementation and evidence candidate for:

```text
M2-S06 — Official CLI interactive REPL and formatted experience
```

Do not start `M2-S07` before reviewer-owned completion of `M2-S06`.

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
