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
current task    reviewer inspection of the bounded M2-S05 corrective candidate
blockers        reviewer acceptance pending; M2-S06 remains blocked
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | `M2-S05` CANDIDATE READY FOR REVIEW — reviewer acceptance pending |
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

## Current blockers and reviewed findings

No contract, architecture, implementation-planning or technology contradiction is open. The four bounded findings below are corrected in the published S05 corrective candidate. Reviewer acceptance remains pending; no architecture reopen was required.

### `S05-RF-01` — an unexpected ordinary exception loses already-attempted HTTP exchanges

Reviewed implementation:

```text
execute()
    accumulates selector and primary exchanges in a local list

main.run()
    catches an ordinary Exception outside execute()
    creates cli_internal_error with exchanges = ()
```

If an unexpected defect occurs after a selector lookup or primary HTTP response—for example in request/protocol processing or transport cleanup—the process still emits a structured `cli_internal_error`, but the result falsely reports an empty trace. This violates the frozen rule that the JSON result contains every attempted HTTP exchange exactly once and in execution order, including failed commands.

Required correction:

```text
ordinary unexpected exception before any request
    -> bounded cli_internal_error
    -> exchanges = []

ordinary unexpected exception after one or more attempts
    -> bounded cli_internal_error
    -> preserve every completed/attempted exchange in order
    -> result = null
    -> stdout one JSON line
    -> stderr empty
    -> exit 1

BaseException / cancellation / KeyboardInterrupt / SystemExit
    -> not normalized as an ordinary CLI result
```

The structured execution boundary may be moved or may carry partial execution state, but no actual exchange may be discarded merely because the command ended through the unexpected-error boundary. Permanent tests must inject defects after a selector exchange, after a primary response and during post-response/client cleanup.

### `S05-RF-02` — endpoint-root parsing silently repairs an empty explicit port

`normalize_endpoint_root()` validates `parts.port` only when it is non-null. Python URL parsing represents an empty explicit port as `None`, so inputs such as:

```text
http://example.test:
http://example.test:/
https://[2001:db8::10]:
```

are accepted and normalized by dropping the trailing colon. The frozen contract permits either no port or one valid explicit numeric port; it does not permit malformed input to be silently repaired.

Required correction:

```text
port absent
    -> valid

explicit numeric port 1..65535
    -> valid

empty, zero, non-numeric, signed or out-of-range explicit port
    -> cli_invalid_invocation
    -> command = null
    -> exchanges = []
```

Add deterministic parser/process regressions for hostname and bracketed-IPv6 roots, while preserving the accepted canonical examples and bounded non-leaking errors.

### `S05-RF-03` — the CLI command/result/trace values are only shallowly immutable

The model uses frozen dataclasses and top-level `MappingProxyType`, but nested JSON objects and arrays are retained by shallow copy. The same is true for command parameters, error details, request/response bodies and successful result bodies. Mutating an original nested input—or a nested value reached through a public field—can therefore change a supposedly immutable command, trace, error or result after construction.

This contradicts the frozen ownership of `model.py` as the authority for immutable CLI command, result, trace and error values and can make rendered output differ from the state that was actually parsed or observed.

Required correction:

```text
construction
    -> take a recursive immutable snapshot or an equivalently isolated canonical copy

stored command / error / request / response / result values
    -> no externally reachable mutation can alter them

serialization
    -> return detached JSON-compatible carriers
    -> mutating a serialized copy cannot alter the stored authority
```

Permanent pure tests must cover nested dictionaries and arrays for `ParsedCommand`, `CliError`, request/response traces and `CliResult`, including mutation of both the original constructor input and the value returned by `as_json()`.

### `S05-RF-04` — registry help and example metadata are placeholders, not command authority

The static registry correctly owns 63 command specifications, but the common builder currently assigns every specification only:

```text
help_text   = "<operation> <resource>"
example     = "<resource> <operation>"
renderer    = "<resource>.<operation>"
```

For operations requiring a selector or parameters, the recorded example is not a valid command at all. The frozen CLI architecture makes this installed registry the sole help/dispatch authority and requires operation help to expose selector type, required/optional parameter types, the exact HTTP operation and concise examples. S06 may render this metadata, but it must not invent a second command/help authority.

Required correction:

```text
every CommandSpec
    -> meaningful bounded operation description
    -> exact selector metadata
    -> required/optional parameter metadata and types
    -> exact HTTP method/path already owned by the spec
    -> at least one concise syntactically valid command example
```

Add machine-checkable evidence that every example resolves to its own registry key and passes the same local parser/required-parameter validation without performing HTTP. Do not implement `/help`, the REPL or FORMATTED runtime behavior in S05.

## M2-S05 corrective candidate record

Candidate state and provenance:

```text
M2-S05                         CANDIDATE READY FOR REVIEW
initial implementation         3d02fce9fe9c456e26100c3dbbbabce75bf90caf
initial candidate evidence     c1365c1c951447ed3f22cd54bcb1effcf41043ee
reviewer baseline              77b682bac31f6c2e7a8befa2b5a18d98330fb4ea
review-fix prompt              2f43b21d66d318fcc43c2595bdf893fc6f395d53
corrective implementation      1015dd5ea86b15e8248c9a5e2fe518fe98e2b637
candidate evidence/status      eb8ff673ad1ea77179194493b712dcc0497b5835
review result                  pending / reviewer-owned
open findings                  none in the corrective candidate
M2-S06                         BLOCKED / not started
```

Corrective finding outcomes:

```text
S05-RF-01  PASS — one execution ledger preserves selector, primary and cleanup
           exchange history on ordinary unexpected failure; BaseException and
           cancellation controls remain unnormalized
S05-RF-02  PASS — absent ports and numeric 1..65535 ports are accepted; empty,
           zero, signed, nonnumeric and out-of-range hostname/IPv6 ports fail
           locally with command = null and exchanges = []
S05-RF-03  PASS — command, plan, error, request/response trace and result JSON
           use recursive immutable snapshots with detached JSON serialization
S05-RF-04  PASS — all 63 CommandSpec values own meaningful descriptions,
           renderer metadata and parser-valid examples; both RelationshipDefinition
           create/rename discriminated shapes are represented
```

Permanent exact review-fix registry:

```text
S05-RF-01                      6 selectors / 8 collected nodes
S05-RF-02                      3 selectors / 21 collected nodes
S05-RF-03                      3 selectors / 3 collected nodes
S05-RF-04                      5 selectors / 5 collected nodes
exact union                   17 selectors / 37 unique nodes / 37 passed — 11.46 s
registry examples             63/63 specs; 65/65 stored examples parse to own key
```

Bundle state remains bounded and honest:

```text
M2-VER-27  S05 primary candidate PASS — 51 selectors / 106 passed — 15.44 s
M2-VER-24  bounded S05 support PASS — 7 selectors / 7 passed — 9.49 s;
           primary ownership remains M2-S07
M2-VER-28  bounded S05 support PASS — 19 selectors / 27 passed — 4.86 s;
           primary ownership remains M2-S06
M2-VER-30  bounded S05 support PASS — 7 selectors / 30 passed — 9.73 s;
           primary ownership remains M2-S07
M2-VER-25/26 remain DESIGNED until M2-S06
M2-VER-29 remains DESIGNED until M2-S07
M2-VER-31/32 remain DESIGNED until M2-S08
```

Candidate verification on the corrective implementation:

```text
uv lock --check                                       PASS — 44 packages
uv sync --locked                                      PASS — 42 checked packages
uv build                                              PASS — sdist + wheel 0.1.0
Ruff format/check                                     PASS — 215 files
Ruff lint                                             PASS
Pyright                                               PASS — 0 errors
pytest collection                                     670 tests — 1.59 s
all tests/test_m2_s05_*.py                            106 passed — 16.22 s
DTO/API/route-inventory regressions                    57 passed — 27.87 s
S04 Settings/startup/Health regressions               121 passed — 15.57 s
schema metadata / migrations                            5 passed — 2.10 s
M1 / S00 / M2 traceability                             24 passed — 14.27 s
installed wheel/entrypoint boundary                     1 passed; success,
                                                       malformed port and controlled
                                                       post-exchange internal failure
PostgreSQL concurrency marker                         182 passed — 117.83 s
non-PostgreSQL                                        419 passed — 36.77 s
full repository suite                                 670 passed — 204.01 s
skip / xfail / rerun                                    0 / 0 / 0
warning census                                          1 locked FastAPI/Starlette deprecation
supported-path 40P01 / unexpected 40001                 0 / 0
negative-control 40P01 / 40001                          1 / 2, expected and immediate
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

Both non-normative S05 execution aids remain in `wip/` pending reviewer acceptance.

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

Prepare the non-normative corrective execution aid:

```text
docs/milestones/M2/wip/M2-S05-review-fixes-codex-prompt.md
```

The correction remains inside `M2-S05` and is limited to `S05-RF-01`, `S05-RF-02`, `S05-RF-03` and `S05-RF-04`. Do not start `M2-S06`.

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
