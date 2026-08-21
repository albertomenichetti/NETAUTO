# M2 — Milestone Status

**Milestone status:** POST-IMPLEMENTATION — AS-IS CONSOLIDATION REVIEW CHANGES REQUIRED / M2 NOT DELIVERED

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
current gate                AS-IS consolidation — REVIEW CHANGES REQUIRED
next gate                   consistency closure — BLOCKED
blockers                    ASIS-RF-01 residual; ASIS-RF-04 residual
M2                          NOT DELIVERED
merge                       NOT EXECUTED
```

The M2 contract, architecture set and implementation decomposition remain
`FINAL / FROZEN`. No architecture reopen is active. Implementation and the
M2-S09 final-acceptance gate are complete.

The corrected consolidation candidate at
`1a4c4499bcf063b0d7fcd763401a47cde4d2f1d9` is rejected only for two bounded
current-AS-IS documentation/harness residuals. The accepted product, schema,
API, CLI, Health, runtime behavior and final M2-S09 evidence are not reopened.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | COMPLETED |
| Final acceptance | ACCEPTED — `M2-S09 COMPLETED` |
| AS-IS consolidation | REVIEW CHANGES REQUIRED |
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
current reviewer decision        REVIEW CHANGES REQUIRED
```

The S08 regression transition compares current API and persistence documents
with the exact current 63-operation and fifteen-table authorities while retaining
historical M2 delta registries. Its pytest node identity remains unchanged.

## Corrected candidate evidence retained as non-regression evidence

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

## Reviewer finding ledger

### `ASIS-RF-01` — OPEN, bounded residual

The 41-entry registry, global row order, three advisory gates and lock-mode
vocabulary are present. The remaining defect is the exact meaning of target
acquisition for differential replacement.

Required current meaning:

```text
a target whose reference is created or physically reinserted
    -> included in the initial plan

a target required by semantic admission
    -> included in the initial plan

an unchanged reference
    -> no outgoing target lock
```

`OT.R` must distinguish explicitly:

```text
unchanged parent                  no target reacquisition
changed explicit parent           OT.H@KS + OT.V@S
changed implicit parent           OT.H@S  + OT.V@S
changed component target          OT.H@KS
unchanged component target        no outgoing target lock
unchanged property declaration    no outgoing target lock
same-pin physical reinsertion     DT.H@KS + DT.V@KS
explicit new/rebound property     DT.H@KS + DT.V@S
implicit new/rebound property     DT.H@S  + DT.V@S
```

`RD.R` must distinguish explicitly:

```text
unchanged property declaration    no outgoing target lock
same-pin physical reinsertion     DT.H@KS + DT.V@KS
explicit new/rebound property     DT.H@KS + DT.V@S
implicit new/rebound property     DT.H@S  + DT.V@S
```

The phrase `retained/inserted targets` must not imply an outgoing target lock for
an unchanged physical declaration. Use `replaced/new`, `physically inserted or
reinserted`, or an equivalent exact formulation.

The stable regression gate must add a bounded sentinel check for these specific
rules without duplicating the complete 41-plan matrix in Python.

### `ASIS-RF-02` — CLOSED

Relationship property cardinality, active-consumer semantics, public lexical
contract and persistence codec are propagated through `datatype.md`, `api.md` and
`persistence.md` by `e2c44c38c172e912b264b0e95e304daa3fce8163`.

### `ASIS-RF-03` — CLOSED

`runtime-deployment.md` distinguishes packaged Settings/runtime implementation
from external operator-supplied settings, configuration values and secrets by
`e2c44c38c172e912b264b0e95e304daa3fce8163`.

### `ASIS-RF-04` — OPEN, bounded residual

The status lifecycle must contain one unambiguous active finding ledger. Historical
rejections may remain, but they must be labelled as historical and use past-tense
or finite CLOSED records. A future candidate must not claim all findings closed
while retaining live sections that still say `does not yet`, `required closure`
or `must be corrected` for already closed findings.

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

## Reviewer-authorized residual delta

The next review-fix may modify only:

```text
docs/architecture/concurrency.md
tests/test_m2_s08_regression.py
docs/milestones/M2/status.md
```

All other current architecture owners are frozen at the corrected-candidate
boundary. In particular, preserve the accepted closure of `ASIS-RF-02` and
`ASIS-RF-03`.

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

## Required residual review-fix gate

Execute at least:

```text
focused current-AS-IS regression
complete tests/test_m2_s08_regression.py
traceability and documentation-policy tests
15-file/link/temporal/milestone-ID/placeholder audits
PostgreSQL / concurrency
non-PostgreSQL
full repository
quality / build / collection
exact-remote post-push rerun
```

Required outcome:

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

Apply the bounded residual closure of `ASIS-RF-01` and `ASIS-RF-04` from the
current `M2` branch. Preserve all other AS-IS owners and the accepted product.
The implementer handoff is only:

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