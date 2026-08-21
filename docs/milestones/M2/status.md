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

The consolidation candidate at
`b8a7d60b111288cd5b9931723d99adb477b3cc22` is rejected only for bounded
current-AS-IS completeness and lifecycle findings. The accepted product,
schema, API, CLI, Health, runtime behavior and final M2-S09 evidence are not
reopened.

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

## AS-IS consolidation candidate record

```text
starting AS-IS HEAD             422ce3c490c82d7d2f24ac60d777d75bca40374e
reviewer verification amendment 8e74df8fa6e3da1cf1be7c210ded57a8e2b8b178
verification-transition commit  1abd90c474ebf0abdfc7d1415cee26b6f3cab9c9
AS-IS corpus commit             8315b6c4a1d5f5ef8247ea02e37765ef2a1dc336
rejected candidate evidence     b8a7d60b111288cd5b9931723d99adb477b3cc22
reviewer decision               REVIEW CHANGES REQUIRED
reviewer rejection              1e3bba0e91e561945c64f13b8f640864c0f318d0
review-fix starting HEAD        1e3bba0e91e561945c64f13b8f640864c0f318d0
lock-plan test commit           4d5898196cb92add9c65b04a5e9b03d09158325e
AS-IS owner-fix commit          e2c44c38c172e912b264b0e95e304daa3fce8163
candidate evidence/status       this commit
review-fix state                CANDIDATE READY FOR REVIEW
```

The S08 regression transition correctly compares current API and persistence
documents with the exact current 63-operation and fifteen-table authorities,
while retaining historical M2 delta registries. Its pytest node identity remains
unchanged.

Candidate evidence accepted as non-regression evidence:

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

Production code, API/CLI implementation, Health implementation, schema,
migration, dependencies, locks and artifact identity are unchanged by the
consolidation candidate.

## Corrected AS-IS candidate evidence

The bounded review-fix closes all four reviewer findings in the candidate:

```text
ASIS-RF-01  exact 41-entry current lock-plan registry, row-class order,
            three advisory gates, initial KS/S/NKU/U intent and bounded parser
ASIS-RF-02  Relationship property cardinality, active-consumer, lexical and
            persistence-codec propagation across the owning documents
ASIS-RF-03  wheel contains Settings/runtime implementation but no
            operator-supplied configuration values or secrets
ASIS-RF-04  current corrective lifecycle, authorized delta and gate evidence
```

Pre-push documentation and finite-inventory evidence:

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

Pre-push repository evidence:

```text
focused current-AS-IS regression    1 passed / 0.79s
complete S08 regression             4 passed / 4.93s
traceability/documentation policy   117 passed / 38.45s
schema / Alembic                    33 passed / 19.00s; compare_metadata []
API / error / CLI                   277 passed / 68.77s
runtime / schema guard / Health     121 passed / 15.22s
PostgreSQL / concurrency            254 passed / 189.89s
non-PostgreSQL                      642 passed / 88.45s
full repository                     896 passed / 269.36s
collection                          896 / 1.80s
uv lock / locked sync / build       PASS / PASS / PASS
Ruff format / lint                  PASS / PASS
Pyright                             0 errors / 0 warnings
skip / xfail / rerun                0 / 0 / 0
supported 40P01 / unexpected 40001  0 / 0
negative controls                   40P01 x1 / 40001 x2
warning census                      1 reviewed Starlette deprecation
```

Verified external database and artifact identity:

```text
PostgreSQL          16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
database identity   netautotest
bounded SELECT 1    PASS
wheel               netauto-0.2.0-py3-none-any.whl
wheel size          165978 byte
wheel members       77
wheel SHA-256       38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size   48238 byte
runtime-lock SHA-256 0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

Production, public API/CLI behavior, Health, schema, migration, dependencies,
`uv.lock`, runtime lock content and distributed artifact content remain
unchanged. No PR, workflow, tag, Release, acceptance record or artifact
publication is part of this candidate.

## Reviewer findings

### ASIS-RF-01 — complete current lock-plan authority

`docs/architecture/concurrency.md` does not yet preserve the complete current
pre-DML plan for every one of the 41 mutation primitives and expresses the global
row-class order ambiguously.

Required closure:

```text
exact global order
    10 ObjectTemplate headers and exact versions
    20 DataType headers and exact versions
    30 RelationshipDefinition headers and exact versions
    40 Object rows
    50 factual Relationship rows

exact three-gate registry
complete 41-mutation registry
one initial gate/row plan for every mutation
initial KS / S / NKU / U intent where applicable
normal-path no-upgrade rule
direct-FK target-before-owner rule
child/reference target-before-DML rule
```

The owner must state the current architecture directly. It must not describe the
registry as an M2 delta or require a future reader to recover plans from code,
tests or milestone documents.

The existing stable regression test may be extended to assert the exact 41
mutation identifiers, global order, three gates and non-empty documented plan for
every mutation without creating a second semantic matrix.

### ASIS-RF-02 — Relationship property propagation

Current Relationship property semantics must be propagated losslessly to all
cross-cutting owners.

Required corrections:

```text
docs/architecture/datatype.md
    SCALAR/LIST belongs to both ObjectTemplateVersion and
    RelationshipDefinitionVersion property declarations

    direct active PUBLISHED consumers include both ObjectTemplateVersion
    properties and RelationshipDefinitionVersion properties

docs/architecture/api.md
    the shared PrimitiveType lexical/canonical contract also applies to
    Relationship current property values

docs/architecture/persistence.md
    the canonical PrimitiveType persistence codec also applies to
    Relationship current properties and Relationship factual lifecycle
    before_state / after_state snapshots
```

This is propagation of accepted current meaning, not new product semantics.

### ASIS-RF-03 — wheel content wording

`docs/architecture/runtime-deployment.md` must distinguish the packaged Settings
implementation from external operator values.

Required meaning:

```text
the wheel contains the Settings model and runtime code

the wheel contains no operator-supplied settings/configuration values,
secrets, certificates, source checkout, test/dev tooling or deployment assets
```

The phrase `contains no settings` is not acceptable because it is literally
ambiguous and conflicts with the packaged Settings implementation.

### ASIS-RF-04 — operational status coherence

This status record must remain aligned with the actual review phase and
authorized delta. The obsolete instruction to begin consolidation is retired.
The immediate action is now the bounded correction of ASIS-RF-01 ... ASIS-RF-04.

## Non-negotiable consolidation rules

The consolidation produces one autonomous description of the system that exists
at the accepted M2 boundary.

```text
current state, not a sequence of changes
present tense, not milestone chronology
one normative owner per decision
no requirement to reconstruct M1 or M2
no M2-OUT / M2-AC / M2-VER / slice / SHA leakage into current semantics
no candidate counts or review evidence in docs/architecture
no copy/paste of the M2 TO-BE corpus
```

Invalid semantic wording includes:

```text
M1 had X, M2 added Y
previously ... now ...
new in M2
introduced by M2-Snn
preserved from the old baseline
```

Cycle names are allowed only in the concise provenance section of
`docs/architecture/README.md` and in links to historical records.

## Reviewer-authorized review-fix delta

The review-fix may modify only:

```text
docs/architecture/concurrency.md
docs/architecture/datatype.md
docs/architecture/api.md
docs/architecture/persistence.md
docs/architecture/runtime-deployment.md
docs/milestones/M2/status.md
tests/test_m2_s08_regression.py
```

The remaining current architecture documents must be preserved unless a direct,
precise dependency of one listed correction demonstrates a contradiction. Such a
case is a new STOP and reviewer finding, not implicit scope expansion.

Do not modify:

```text
src/netauto/
all other tests
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

## Required review-fix gate

Execute at least:

```text
focused current-AS-IS regression
exact 41-mutation lock-plan documentation audit
temporal/delta wording audit
milestone-ID leakage audit
Markdown link audit
placeholder/open-point audit
traceability and documentation-policy tests
schema / Alembic
API / CLI / Health / runtime
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

Review the bounded closure of `ASIS-RF-01 ... ASIS-RF-04` on the exact published
`M2` candidate. The consistency-closure gate remains blocked pending reviewer
acceptance. The implementer handoff is only:

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
