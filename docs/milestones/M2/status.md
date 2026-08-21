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
blockers                    none at the implementer candidate boundary
M2                          NOT DELIVERED
```

The M2 contract, architecture set and implementation decomposition remain
`FINAL / FROZEN`. No architecture reopen is active. Implementation and the
M2-S09 final-acceptance gate are complete.

The only authorized work is the reviewer-scoped documentation consolidation
specified by:

```text
docs/milestones/M2/as-is-consolidation.md
```

This work produces a current-state architecture candidate. It does not authorize
new product semantics, implementation changes, delivery or merge.

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
separate post-implementation gate and is not a new implementation slice.

## Reviewer-owned final acceptance

```text
rejected candidate             b0546b1109c66a57195c50294291cb4a32ad48f2
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
acceptance.md                  reviewer acceptance summary present
S09 execution aid              retired
M2-S09                         COMPLETED
M2                             NOT DELIVERED
```

The rejected candidate and its reviewer decision remain preserved in immutable
Git history. The accepted replacement record is the only candidate JSON in the
working tree.

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
open findings                   0
```

Verified execution environment:

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

The reviewer did not independently rerun the 896-test suite. Runtime results
above are the implementer's exact-candidate and exact-remote evidence; the
reviewer independently inspected the commit chain, record, lifecycle, runner,
regressions and acceptance boundary.

## AS-IS consolidation gate

Verification-transition closure:

```text
starting AS-IS HEAD            422ce3c490c82d7d2f24ac60d777d75bca40374e
reviewer amendment             8e74df8fa6e3da1cf1be7c210ded57a8e2b8b178
verification-transition commit 1abd90c474ebf0abdfc7d1415cee26b6f3cab9c9
AS-IS corpus commit            8315b6c4a1d5f5ef8247ea02e37765ef2a1dc336
```

The reviewer-authorized S08 regression transition now compares the current API
and persistence documents with the exact current 63-operation and fifteen-table
authorities while preserving all historical delta registries. Its stable node
identity is unchanged.

Pre-push consolidation evidence:

```text
target files / internal links       15 / 35; missing or unresolved 0 / 0
temporal-delta / milestone-ID leak   0 / 0
placeholder / open-point findings   0 / 0
API / CLI / Health                  63 business / 63 remote / 8 local / 1 Health
tables / explicit indexes           15 / 29
Settings fields                     7
mutations / family blocks / cells   41 / 15 / 861
scenarios / predicates / recipes    83 / 21 / 11
focused transition                  1 passed
S08 regression                      4 passed
traceability/documentation policy   117 passed
schema / Alembic                    33 passed; compare_metadata []
API / error / CLI                   277 passed
runtime / schema guard / Health     121 passed
PostgreSQL / concurrency            254 passed
non-PostgreSQL                      642 passed
full repository                     896 passed
collection                          896
skip / xfail / rerun                0 / 0 / 0
supported 40P01 / unexpected 40001  0 / 0
negative controls                   40P01 x1 / 40001 x2
warning census                      1 reviewed Starlette deprecation
```

Verified environment and invariant artifact identity:

```text
PostgreSQL          16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
database identity   netautotest
bounded SELECT 1    PASS
wheel size/members  165978 byte / 77
wheel SHA-256       38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size   48238 byte
runtime-lock SHA-256 0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

Production code, API implementation, CLI implementation, schema, migration,
dependencies and locks are unchanged by the consolidation candidate.

The consolidation must produce one autonomous description of the system that
exists at the accepted M2 boundary.

Non-negotiable rules:

```text
current state, not a sequence of changes
present tense, not milestone chronology
one normative owner per decision
no requirement to reconstruct M1 or M2
no M2-OUT / M2-AC / M2-VER / slice / SHA leakage into current semantics
no candidate counts or review evidence in docs/architecture
no copy/paste of the M2 TO-BE corpus
```

Invalid semantic wording includes forms such as:

```text
M1 had X, M2 added Y
previously ... now ...
new in M2
introduced by M2-Snn
preserved from the old baseline
```

The current AS-IS states the resulting entities, invariants, commands, failures,
persistence, concurrency, runtime and verification obligations directly.

Cycle names are allowed only in the concise provenance section of
`docs/architecture/README.md` and in links to historical records.

## Consolidation target

Expected updated or added owners/projections:

```text
docs/architecture/README.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/api.md
docs/architecture/health.md
docs/architecture/cli.md
docs/architecture/runtime-deployment.md
docs/architecture/linux-operating-baseline.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md
```

The existing DataType, ObjectTemplate and Object owners must be audited and may
change only where their current statements or cross-references are no longer
exact.

The target corpus must describe, without historical narration:

```text
versioned RelationshipDefinition semantics and factual Relationship state
fifteen-table PostgreSQL authority and 0001_m2_kernel as the sole root/head
41 mutation primitives, 861 interaction cells and 21 safety predicates
63 business HTTP operations plus GET /health/core
Core Health behavior
63-operation HTTP-only CLI, 8 local commands and REPL/process behavior
Settings, wheel/runtime-lock, startup guard and trusted-boundary deployment
current Linux installation and operation procedure
T0–T10 verification, 83 scenarios and 21 predicates
```

Milestone-only outcomes, acceptance criteria, evidence-bundle IDs, commit hashes
and pass ledgers remain in the historical M2 record.

## Authorized delta

The consolidation candidate may modify only:

```text
docs/architecture/*.md
docs/milestones/M2/status.md
```

Explicitly permitted new files:

```text
docs/architecture/health.md
docs/architecture/cli.md
docs/architecture/runtime-deployment.md
docs/architecture/linux-operating-baseline.md
```

It must not modify:

```text
src/netauto/
tests/
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

A need to change any forbidden area is a `STOP` and a reviewer finding.

## Candidate and review boundary

The coding agent may move the consolidation gate through:

```text
READY -> IN PROGRESS -> CANDIDATE READY FOR REVIEW
```

A failed gate remains `IN PROGRESS`. The agent must not assign:

```text
AS-IS consolidation    COMPLETED
consistency closure    READY / COMPLETED
M2                     DELIVERED
```

Reviewer acceptance of the consolidation opens the separate whole-corpus
consistency-closure gate. Only after both reviewer-owned gates complete may M2
be marked `DELIVERED`.

## Immediate next action

Execute `docs/milestones/M2/as-is-consolidation.md` from the current `M2` branch.
Produce a complete current-state candidate, run the specified preliminary
consistency and repository gates, push only to `M2`, and hand off:

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
```
