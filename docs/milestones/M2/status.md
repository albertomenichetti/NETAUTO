# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S05 REVIEW CHANGES REQUIRED

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S05 — REVIEW CHANGES REQUIRED
current task    prepare and execute one bounded residual M2-S05 review-fix prompt
blockers        S05-RF-01 remains open; M2-S06 remains blocked
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | `M2-S05` REVIEW CHANGES REQUIRED — residual `S05-RF-01` only |
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
| `M2-S05` | REVIEW CHANGES REQUIRED | `M2-S04 COMPLETED` |
| `M2-S06` | BLOCKED | `M2-S05 COMPLETED` |
| `M2-S07` | BLOCKED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S04` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and reviewed findings

No contract, architecture, implementation-planning or technology contradiction is open. The corrective candidate closes `S05-RF-02`, `S05-RF-03` and `S05-RF-04`. `S05-RF-01` is materially improved but not yet complete; the remaining work is bounded to the same non-interactive CLI execution/trace boundary.

### `S05-RF-01` — REOPENED: the unexpected-failure boundary is not complete

Accepted corrective material:

```text
one command-scoped ExecutionLedger exists
normal selector and primary exchanges are recorded once and in order
an unexpected failure after normal response capture preserves recorded exchanges
HttpTransport.__aexit__ failure preserves the already-recorded primary exchange
expected TransportFailure remains a bounded transport result
BaseException, cancellation, KeyboardInterrupt and SystemExit remain unnormalized
raw unexpected exception text is absent from the structured result
```

Two residual gaps remain.

#### A. Unexpected parsing defects bypass the structured process boundary

The production `run()` function catches only `ParseFailure` around `parse_process()`. The general ordinary-`Exception` boundary begins after parsing, around `asyncio.run(execute(...))`.

Therefore an unexpected ordinary defect in endpoint parsing, registry lookup, local decoding or another `parse_process()` path escapes the non-interactive result boundary entirely. Instead of the frozen outcome:

```text
status       error
error.code   cli_internal_error
command      null or the safely parsed partial command
exchanges    []
stdout       one JSON object plus newline
stderr       empty
exit         1
```

the process may terminate with an unstructured traceback.

#### B. The ledger records a request too late for some attempted-exchange failures

`HttpTransport.exchange()` builds the request and calls `AsyncClient.send()`, but records the exchange only:

```text
when an expected httpx.TransportError is caught
or
after send returned, cookie cleanup completed and response capture succeeded
```

Consequently an ordinary unexpected exception raised:

```text
inside AsyncClient.send after the request attempt began
during response-trace construction
during the post-response cookie cleanup in exchange()
```

can still reach the outer `cli_internal_error` boundary with the attempted request absent from the ledger. This contradicts the frozen requirement that every actual attempted HTTP exchange appears exactly once and in execution order on every structured outcome.

Required correction:

```text
one ordinary-Exception boundary covers parsing and execution
    -> expected ParseFailure remains its finite local outcome
    -> unexpected parse defect becomes bounded cli_internal_error
    -> BaseException families remain untouched

once an HTTP send attempt begins
    -> the request attempt is owned by the command ledger
    -> an unexpected ordinary send failure preserves one exchange with response = null
    -> a returned response remains represented if response capture or later cleanup fails
    -> expected TransportFailure is not duplicated
    -> selector and primary ordering remains exact

all structured failures
    -> result = null
    -> one JSON stdout line
    -> empty stderr
    -> exit 1
    -> no raw exception text
```

Permanent evidence must exercise the real `netauto -n` boundary for at least:

```text
unexpected RuntimeError from parse_process before a command key exists
unexpected RuntimeError from parsing after a safe partial command exists
unexpected ordinary exception raised by the HTTP send path
unexpected failure during response-trace construction or equivalent post-response capture
unexpected failure during exchange-level post-response cleanup
existing __aexit__ cleanup failure
expected httpx.TransportError without duplicate exchange
BaseException/cancellation negative controls
```

### `S05-RF-02` — CLOSED

The endpoint authority now distinguishes absence of a port from one explicit ASCII-decimal port. Hostname and bracketed-IPv6 forms accept only `1..65535`; empty, zero, signed, nonnumeric and out-of-range ports produce bounded `cli_invalid_invocation`, `command = null` and no exchange. Parser, process and installed-wheel evidence cover the required matrix.

### `S05-RF-03` — CLOSED

`ParsedCommand`, `RequestPlan`, `CliError`, request/response traces and `CliResult` now take recursive immutable JSON snapshots. Public nested values cannot mutate the stored authority, `as_json()` returns detached ordinary carriers and repeated rendering is byte-stable. Query/header maps and exchange ordering remain immutable.

### `S05-RF-04` — CLOSED

All 63 `CommandSpec` values now own meaningful descriptions, selector and parameter metadata through the same registry fields, renderer metadata and at least one parser-valid example. The registry contains 65 stored examples because both RelationshipDefinition CREATE and RENAME expose their two discriminated shapes. All examples parse through the production parser to their own command without HTTP.

## M2-S05 second review record

Reviewer result:

```text
M2-S05                         REVIEW CHANGES REQUIRED
initial implementation         3d02fce9fe9c456e26100c3dbbbabce75bf90caf
initial candidate evidence     c1365c1c951447ed3f22cd54bcb1effcf41043ee
first review record            77b682bac31f6c2e7a8befa2b5a18d98330fb4ea
first review-fix prompt        2f43b21d66d318fcc43c2595bdf893fc6f395d53
corrective implementation      1015dd5ea86b15e8248c9a5e2fe518fe98e2b637
corrective evidence/status     eb8ff673ad1ea77179194493b712dcc0497b5835
corrective provenance          372d2954f206ae99f3935d3ee36d28a50f9fb72e
closed findings                S05-RF-02, S05-RF-03, S05-RF-04
open finding                   S05-RF-01 residual boundary cases
M2-S06                         BLOCKED / not started
```

Conforming material to preserve:

```text
neutral wire boundary          shared request/success/page/lifecycle/error/Health DTOs
server adapters                reuse neutral DTO identities; 63 business routes unchanged
runtime dependency             HTTPX >=0.28,<1 promoted from dev to project dependency
console entrypoint             netauto = netauto.cli.main:main
CLI execution                  HTTP-only exact -n non-interactive process
remote registry                63 exact CommandSpec values; 65 valid examples
selectors                      deterministic top-level/nested lookup and per-command memoization
transport                      verified TLS, no redirect/retry/auth/cookie persistence
protocol                       exact 200/201/204, DTO/error/Location validation
normal trace paths             selector and primary exchanges recorded once and ordered
process result                 one stdout JSON line; stderr empty; exit 0/1 on covered paths
interactive REPL/FORMATTED     not introduced; owned by blocked M2-S06
```

Candidate-reported verification remains useful but does not close the residual paths:

```text
uv lock --check                                       PASS — 44 packages
uv sync --locked                                      PASS — 42 checked packages
uv build                                              PASS — sdist + wheel 0.1.0
Ruff format/check                                     PASS — 215 files
Ruff lint                                             PASS
Pyright                                               PASS — 0 errors
pytest collection                                     670 tests
review-fix union                                       37 passed
all S05 tests                                         106 passed
M2-VER-27                                             106 passed
M2-VER-24 bounded support                               7 passed
M2-VER-28 bounded support                              27 passed
M2-VER-30 bounded support                              30 passed
DTO/API/route inventory                               57 passed
S04 Settings/startup/Health                          121 passed
schema metadata / migrations                           5 passed
M1 / S00 / M2 traceability                            24 passed
PostgreSQL concurrency marker                        182 passed
non-PostgreSQL                                       419 passed
full repository suite                                670 passed — 206.58 s
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
Alembic graph                   one base / one head
root migration                  0001_m2_kernel unchanged
metadata/schema/index diff      none
project version                 0.1.0 unchanged
dependency / lock delta         none in the review fixes
business HTTP operations        41 mutations + 22 reads = 63 exact
operational HTTP operations      1 Health; total public HTTP = 64
CLI remote operations           63 exact; Health excluded
scenario / predicate registries 83 / 21 unchanged
interactive REPL/FORMATTED      not introduced; owned by blocked M2-S06
GitHub Actions/PR               not used / not created
```

The reviewer inspected the published commit chain, production delta, tests and traceability. The reviewer did not independently execute the 670-test suite during this inspection; the execution results above are those produced and recorded by the candidate.

Both existing S05 execution aids remain in `wip/`. No prompt is retired while the slice is open.

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
corrective evidence/status      6d8a0838530f2b449c598dc545a0a2ad3577c5d3
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

Prepare the bounded residual execution aid:

```text
docs/milestones/M2/wip/M2-S05-review-fixes-2-codex-prompt.md
```

The correction remains inside `M2-S05` and is limited to the residual `S05-RF-01` boundary cases above. Do not start `M2-S06`.

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
