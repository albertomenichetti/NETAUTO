# M2 — Milestone Status

**Milestone status:** POST-IMPLEMENTATION — AS-IS CONSOLIDATION CANDIDATE READY FOR REVIEW / M2 NOT DELIVERED

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase                       POST-IMPLEMENTATION
last implementation slice   M2-S09 — COMPLETED
current gate                AS-IS consolidation — CANDIDATE READY FOR REVIEW
next gate                   consistency closure — BLOCKED
blockers                    none in candidate; reviewer inspection pending
M2                          NOT DELIVERED
merge                       NOT EXECUTED
```

The M2 contract, architecture set and implementation decomposition remain
`FINAL / FROZEN`. No architecture reopen is active. Implementation and the
M2-S09 final-acceptance gate are complete.

The residual consolidation candidate at
`3121597e39b9a038d574b9f68f4370deffa1e50f` is rejected only for one bounded
current-AS-IS documentation/harness inconsistency. The final residual candidate
closes that inconsistency without reopening the accepted product, schema, API,
CLI, Health, runtime behavior or final M2-S09 evidence.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | COMPLETED |
| Final acceptance | ACCEPTED — `M2-S09 COMPLETED` |
| AS-IS consolidation | CANDIDATE READY FOR REVIEW |
| Consistency closure | BLOCKED — requires accepted AS-IS consolidation |
| Delivery | NOT DELIVERED |
| Merge | NOT EXECUTED |

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
| `M2-S07` | COMPLETED | `M2-S06 COMPLETED` |
| `M2-S08` | COMPLETED | `M2-S07 COMPLETED` |
| `M2-S09` | COMPLETED | `M2-S00 ... M2-S08 COMPLETED` |

All implementation slices are reviewer-owned `COMPLETED`. Consolidation is a
separate post-implementation gate and is not an implementation slice.

## Reviewer-owned final acceptance

```text
rejected S09 candidate          b0546b1109c66a57195c50294291cb4a32ad48f2
review rejection               2afc3eb1d86bb829185981279d8c6fe9a1667b11
replacement candidate          87de783462b24f17b5da5aa31ce002c19734e0eb
evidence/status publication    e794093bd6b2dae7ffe27a028ddebead8c14941e
S09 acceptance commit          1e9c40161fb7b9d26a6491295c6e393d0eacf60d
reviewer decision              ACCEPTED
evidence record                candidate-87de783462b24f17b5da5aa31ce002c19734e0eb.json
M2-S09                         COMPLETED
M2                             NOT DELIVERED
```

The accepted replacement record is the only S09 candidate JSON in the working
tree. The rejected candidate and its decision remain preserved in Git history.

Accepted exact-candidate and exact-remote evidence remains:

```text
M2-VER                          32 / 32 PASS
M2-AC                           32 / 32 PASS
M2-OUT                          16 / 16 covered
canonical scenarios             83 / 83 PASS
safety predicates               21 / 21 PASS
full repository                 896 passed
collection                      896
skip / xfail / rerun            0 / 0 / 0
supported 40P01                 0
unexpected 40001                0
negative controls               40P01 x1 / 40001 x2
compare_metadata                []
open product findings           0
```

Artifact identity remains:

```text
wheel                 netauto-0.2.0-py3-none-any.whl
wheel size            165978 byte
wheel members         77
wheel SHA-256         38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size     48238 byte
runtime packages      29
runtime-lock SHA-256  0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

## AS-IS consolidation history

```text
starting AS-IS HEAD               422ce3c490c82d7d2f24ac60d777d75bca40374e
verification amendment            8e74df8fa6e3da1cf1be7c210ded57a8e2b8b178
verification-transition commit    1abd90c474ebf0abdfc7d1415cee26b6f3cab9c9
AS-IS corpus commit               8315b6c4a1d5f5ef8247ea02e37765ef2a1dc336
first candidate                   b8a7d60b111288cd5b9931723d99adb477b3cc22
first reviewer rejection          1e3bba0e91e561945c64f13b8f640864c0f318d0
lock-plan completeness test       4d5898196cb92add9c65b04a5e9b03d09158325e
AS-IS owner-fix commit            e2c44c38c172e912b264b0e95e304daa3fce8163
corrected candidate               1a4c4499bcf063b0d7fcd763401a47cde4d2f1d9
second reviewer rejection         7df7030ddb83e70a0005072dc007448e0370a789
differential-plan test commit     f929edbec2fd81415e34c171c83d5913b88e29b0
residual AS-IS owner commit       c92d8ca6b8114d4334792dbb60cc0ad7d235f23e
residual candidate                3121597e39b9a038d574b9f68f4370deffa1e50f
third reviewer rejection          4914d885163a726c3e8f180d50a258b3e318e387
final residual starting HEAD      4914d885163a726c3e8f180d50a258b3e318e387
component sentinel commit         49c6f0d1bf753602b4ddee8a07c9ca0c67b411c9
component owner commit            08076564d7393d588adce8cd1942b40b3536a926
candidate evidence/status         this commit
current implementer state         CANDIDATE READY FOR REVIEW
```

The exact-remote evidence reported for `3121597e...` is retained as
non-regression evidence:

```text
focused current-AS-IS regression    1 passed
complete S08 regression             4 passed
traceability/documentation policy   117 passed
schema / Alembic                    33 passed; compare_metadata []
API / error / CLI                   277 passed
runtime / schema guard / Health     121 passed
PostgreSQL / concurrency            254 passed
non-PostgreSQL                      642 passed
full repository                     896 passed
collection                          896
uv lock / locked sync / build       PASS / PASS / PASS
Ruff format / lint                  PASS / PASS
Pyright                             0 errors / 0 warnings
skip / xfail / rerun                0 / 0 / 0
supported 40P01 / unexpected 40001  0 / 0
negative controls                   40P01 x1 / 40001 x2
warning census                      1 reviewed Starlette deprecation
```

Production, public API/CLI behavior, Health, schema, migration, dependencies,
`uv.lock`, runtime-lock content and distributed artifact content remain
unchanged.

## Finite reviewer finding ledger

### `ASIS-RF-01` — CLOSED in candidate

The 41-entry registry, global row order, three advisory gates and reusable exact
binding rules remain intact. The `OT.R` plan classifies component locking by
whether the complete physical declaration is inserted or reinserted, rather than
only by a change of target identity.

Required current meaning:

```text
changed or physically reinserted component declaration
    -> target OT.H@KS

unchanged physical component declaration
    -> no outgoing target lock

removed component declaration
    -> no outgoing target lock
```

The first case includes a changed `target_template_id`, a changed `position` with
the same target, or any future change to a persisted component field that causes
physical reinsertion. The permanent sentinel rejects the narrower
`changed component target` / `unchanged component target` classification.

### `ASIS-RF-02` — CLOSED, unchanged

Relationship property cardinality, active-consumer semantics, public lexical
contract and persistence codec remain propagated through the current owners.

### `ASIS-RF-03` — CLOSED, unchanged

The runtime/deployment owner distinguishes packaged Settings/runtime
implementation from external operator-supplied settings, configuration values
and secrets.

### `ASIS-RF-04` — CLOSED, unchanged

The status record has one finite active ledger, labels prior rejections as
history and keeps its operational state, evidence and immediate action aligned.

## Non-negotiable consolidation rules

The consolidation is one autonomous representation of the system at the accepted
M2 boundary:

```text
current state, not a sequence of changes
present tense, not milestone chronology
one normative owner per decision
no requirement to reconstruct M1 or M2
no M2-OUT / M2-AC / M2-VER / slice / SHA leakage into current semantics
no candidate counts or review evidence in docs/architecture
no copy/paste of the M2 TO-BE corpus
```

Cycle names remain allowed only in the concise provenance section of
`docs/architecture/README.md` and in links to historical records.

## Final residual delta

The bounded review-fix modified only:

```text
docs/architecture/concurrency.md
tests/test_m2_s08_regression.py
docs/milestones/M2/status.md
```

All other current architecture owners remain frozen at the residual-candidate
boundary. The accepted closure of `ASIS-RF-02`, `ASIS-RF-03` and `ASIS-RF-04`
is unchanged.

Do not modify:

```text
src/netauto/
all other tests
all other docs/architecture files
schema or migrations
pyproject.toml
uv.lock
src/netauto/release/runtime.pylock.toml
README.md root
AGENTS.md
docs/general/
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/
docs/milestones/M2/steps.md
docs/milestones/M2/acceptance.md
docs/milestones/M2/evidence/
docs/milestones/M2/wip/  (non-normative execution aids)
```

No contract, architecture-set or implementation reopen is authorized.

## Final residual candidate evidence

Pre-push evidence on the complete owner/test correction tree:

```text
focused current-AS-IS regression    1 passed / 0.77s
complete S08 regression             4 passed / 4.59s
traceability/documentation policy   117 passed / 38.56s
target files / links                15 / 35; unresolved 0
temporal / milestone / placeholder  0 / 0 / 0
schema / Alembic                    33 passed / 18.91s; compare_metadata []
API / error / CLI                   277 passed / 67.22s
runtime / schema guard / Health     121 passed / 15.25s
PostgreSQL / concurrency            254 passed / 187.49s
non-PostgreSQL                      642 passed / 86.80s
full repository                     896 passed / 274.00s
collection                          896 / 1.82s
uv lock / locked sync / build       PASS / PASS / PASS
Ruff format / lint                  PASS / PASS
Pyright                             0 errors / 0 warnings
```

Outcome census:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative-control SQLSTATE        exact expected census
compare_metadata                 []
new unexplained warnings         0
artifact identity                unchanged
open consolidation findings      0
```

Verified environment and immutable artifact evidence:

```text
PostgreSQL                       16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
database identity                netautotest
bounded SELECT 1                 PASS
wheel size / members             165978 byte / 77
wheel SHA-256                    38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size                48238 byte
runtime-lock SHA-256             0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

## Candidate and review boundary

The coding agent may move the gate only through:

```text
REVIEW CHANGES REQUIRED
    -> IN PROGRESS
    -> CANDIDATE READY FOR REVIEW
```

A failed gate remains `IN PROGRESS`. The coding agent must not assign:

```text
AS-IS consolidation    COMPLETED
consistency closure    READY / COMPLETED
M2                     DELIVERED
merge                   EXECUTED
```

Reviewer acceptance of the consolidation opens the separate whole-corpus
consistency-closure gate. Only after both reviewer-owned gates are `COMPLETED`
may M2 become `DELIVERED`.

## Immediate next action

Reviewer inspection of the final residual candidate is the only immediate next
action. The implementer handoff is:

```text
AS-IS consolidation    CANDIDATE READY FOR REVIEW
consistency closure    BLOCKED
M2                     NOT DELIVERED
```

## Current status vocabulary

```text
READY
IN PROGRESS
CANDIDATE READY FOR REVIEW
REVIEW CHANGES REQUIRED
COMPLETED
BLOCKED
FINAL / FROZEN
NOT STARTED
NOT AUTHORIZED
NOT DELIVERED
DELIVERED
NOT EXECUTED
```
