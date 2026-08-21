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

The reviewer rejected the corrected consolidation candidate at
`1a4c4499bcf063b0d7fcd763401a47cde4d2f1d9` through
`7df7030ddb83e70a0005072dc007448e0370a789` for two bounded current-AS-IS
documentation/harness residuals. The residual candidate closes those two
findings without reopening the accepted product, schema, API, CLI, Health,
runtime behavior or final M2-S09 evidence.

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
review-fix starting HEAD       49bed9eaf80ea00e515088f53a7125d55e3c7694
review-fix commit              56e3a1766e37893a0f4c91166f130bfffbab425b
replacement-cycle commit       5db3ad31a4b51b14a2bd0e5e77d9dbcb1a7dd6dd
final lifecycle test commit    88533bbcb319c24eb57d47c960620418eeb56085
accepted candidate SHA         87de783462b24f17b5da5aa31ce002c19734e0eb
evidence/status publication    e794093bd6b2dae7ffe27a028ddebead8c14941e
S09 acceptance commit          1e9c40161fb7b9d26a6491295c6e393d0eacf60d
reviewer decision              ACCEPTED
evidence record                candidate-87de783462b24f17b5da5aa31ce002c19734e0eb.json
M2-S09                         COMPLETED
M2                             NOT DELIVERED
```

The accepted replacement record is the only S09 candidate JSON in the working
tree. The rejected candidate and its decision remain preserved in Git history.

## Accepted exact-candidate and exact-remote evidence

```text
M2-VER                          32 / 32 PASS
M2-AC                           32 / 32 PASS
M2-OUT                          16 / 16 covered
canonical scenarios             83 / 83 PASS
safety predicates               21 / 21 PASS
bundle union                    369 unique targets / 516 passed
scenario union                  166 unique targets / 190 passed
S06 / T8                        73 passed
S07 / T9                        18 passed
S08 / T10                       99 passed
schema / Alembic                33 passed / compare_metadata []
API / error / CLI               277 passed
runtime / schema guard / Health 121 passed
PostgreSQL / concurrency        254 passed
non-PostgreSQL                  642 passed
full repository                 896 passed
collection                      896
skip / xfail / rerun            0 / 0 / 0
supported 40P01                 0
unexpected 40001                0
negative controls               40P01 x1 / 40001 x2
warning census                  1 reviewed Starlette deprecation
open product findings           0
```

Verified environment:

```text
CPython             3.14.7
uv                  0.12.3
Hatchling           1.32.0
pytest              8.4.2
Ruff                0.16.3
Pyright             1.1.411
Linux               Ubuntu 24.04.4 LTS / 6.8.0-134-generic / x86_64
PostgreSQL          16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
database identity   netautotest
bounded SELECT 1    PASS
```

Artifact identity:

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
starting AS-IS HEAD              422ce3c490c82d7d2f24ac60d777d75bca40374e
reviewer verification amendment  8e74df8fa6e3da1cf1be7c210ded57a8e2b8b178
verification-transition commit   1abd90c474ebf0abdfc7d1415cee26b6f3cab9c9
AS-IS corpus commit              8315b6c4a1d5f5ef8247ea02e37765ef2a1dc336
first candidate evidence         b8a7d60b111288cd5b9931723d99adb477b3cc22
first reviewer rejection         1e3bba0e91e561945c64f13b8f640864c0f318d0
lock-plan test commit            4d5898196cb92add9c65b04a5e9b03d09158325e
AS-IS owner-fix commit           e2c44c38c172e912b264b0e95e304daa3fce8163
corrected candidate evidence     1a4c4499bcf063b0d7fcd763401a47cde4d2f1d9
second reviewer rejection        7df7030ddb83e70a0005072dc007448e0370a789
residual review-fix starting HEAD 7df7030ddb83e70a0005072dc007448e0370a789
differential-plan test commit     f929edbec2fd81415e34c171c83d5913b88e29b0
residual AS-IS owner commit       c92d8ca6b8114d4334792dbb60cc0ad7d235f23e
candidate evidence/status         this commit
current implementer state         CANDIDATE READY FOR REVIEW
```

The reviewer outcome for the residual candidate is not assigned by the
implementer.

The S08 regression transition compares current API and persistence documents
with the exact current 63-operation and fifteen-table authorities while retaining
historical M2 delta registries. Its pytest node identity remains unchanged.

## Historical corrected-candidate evidence retained as non-regression evidence

Documentation and finite inventories:

```text
target files / internal links       15 / 35; missing or unresolved 0 / 0
temporal-delta / milestone-ID leak   0 / 0
placeholder / open-point findings   0 / 0
API / CLI / Health                  63 business / 63 remote / 8 local / 1 Health
tables / explicit indexes           15 / 29
Settings fields                     7
mutations / family blocks / cells   41 / 15 / 861
advisory gates / row classes        3 / 10,20,30,40,50
scenarios / predicates / recipes    83 / 21 / 11
Relationship property propagation   PASS
wheel Settings/value wording        PASS
```

Exact-remote repository evidence:

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

The residual candidate has no open consolidation finding. The two reviewer
rejections and all four finding identities remain recorded as history.

### `ASIS-RF-01` — CLOSED in candidate

The 41-entry registry retains the exact global row order, three advisory gates
and lock-mode vocabulary. The reusable target rules and the `OT.R` / `RD.R`
plans now distinguish all finite differential cases:

```text
created/rebound exact dependency  H@KS + V@S
implicit created/rebound target   H@S  + V@S
same-pin physical reinsertion     H@KS + V@KS
unchanged reference               no outgoing target lock
removed reference                 no outgoing target lock
```

The stable S08 regression node preserves the exact 41-plan structural census and
adds bounded sentinels for these differential clauses. It does not duplicate the
complete lock-plan matrix in Python.

### `ASIS-RF-02` — CLOSED, unchanged

Relationship property cardinality, active-consumer semantics, public lexical
contract and persistence codec are propagated through `datatype.md`, `api.md` and
`persistence.md` by `e2c44c38c172e912b264b0e95e304daa3fce8163`.

### `ASIS-RF-03` — CLOSED, unchanged

`runtime-deployment.md` distinguishes packaged Settings/runtime implementation
from external operator-supplied settings, configuration values and secrets by
`e2c44c38c172e912b264b0e95e304daa3fce8163`.

### `ASIS-RF-04` — CLOSED in candidate

This finite ledger is the only current finding ledger. Rejections are labelled as
history, every finding has one closed record and the current operational state,
authorized delta, evidence and immediate action agree on reviewer inspection of
the residual candidate.

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

## Historical reviewer-authorized residual delta

The residual review-fix was limited to:

```text
docs/architecture/concurrency.md
tests/test_m2_s08_regression.py
docs/milestones/M2/status.md
```

All other current architecture owners remained frozen at the corrected-candidate
boundary. The closed `ASIS-RF-02` and `ASIS-RF-03` owners were unchanged.

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
```

No contract, architecture-set or implementation reopen is authorized.

## Residual review-fix gate evidence

Pre-push evidence on the complete candidate tree:

```text
focused current-AS-IS regression    1 passed / 0.75s
complete S08 regression             4 passed / 4.46s
traceability/documentation policy   117 passed / 36.80s
target files / links                15 / 35; unresolved 0
temporal / milestone / placeholder  0 / 0 / 0
schema / Alembic                    33 passed / 17.97s; compare_metadata []
API / error / CLI                   277 passed / 65.54s
runtime / schema guard / Health     121 passed / 15.01s
PostgreSQL / concurrency            254 passed / 185.06s
non-PostgreSQL                      642 passed / 85.61s
full repository                     896 passed / 277.46s
collection                          896 / 1.74s
uv lock / locked sync / build       PASS / PASS / PASS
Ruff format / lint                  PASS / PASS
Pyright                             0 errors / 0 warnings
```

Outcome census:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative-control SQLSTATE        40P01 x1 / 40001 x2
compare_metadata                 []
new unexplained warnings         0
artifact identity                unchanged
open consolidation findings      0
```

Verified external database and artifact identity:

```text
PostgreSQL            16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
database identity     netautotest
bounded SELECT 1      PASS
wheel size            165978 byte
wheel members         77
wheel SHA-256         38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size     48238 byte
runtime-lock SHA-256  0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
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

Reviewer acceptance of the corrected consolidation opens the separate
whole-corpus consistency-closure gate. Only after both reviewer-owned gates are
`COMPLETED` may M2 become `DELIVERED`.

## Immediate next action

Review the bounded residual candidate on the exact published `M2` HEAD. The
consistency-closure gate remains blocked pending reviewer acceptance. The
implementer handoff is only:

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
