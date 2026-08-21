# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S09 IN PROGRESS

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S09 — IN PROGRESS
current task    execute the replacement final gate from one new clean candidate SHA
blockers        TEST_DATABASE_URL absent in the current execution environment
M2              NOT DELIVERED
```

The M2 contract, architecture set and implementation decomposition remain
`FINAL / FROZEN`. No architecture reopen is active.

Implementation or review-fix work is authorized only for the exact slice marked
`READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `M2-S09 COMPLETED`,
milestone delivery, AS-IS consolidation and merge remain reviewer/human-owned.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | AUTHORIZED — `M2-S09` replacement final gate only |
| Final acceptance | IN PROGRESS |
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
| `M2-S07` | COMPLETED | `M2-S06 COMPLETED` |
| `M2-S08` | COMPLETED | `M2-S07 COMPLETED` |
| `M2-S09` | IN PROGRESS | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S08` are reviewer-owned `COMPLETED`. M2-S09 remains open
inside the same slice.

## Replacement candidate cycle

The reviewer-owned rejection is preserved in Git history. The replacement
cycle started only after the rejected lifecycle and both corrections passed
their focused tests:

```text
rejected candidate             b0546b1109c66a57195c50294291cb4a32ad48f2
review rejection               2afc3eb1d86bb829185981279d8c6fe9a1667b11
review-fix starting HEAD       49bed9eaf80ea00e515088f53a7125d55e3c7694
review-fix commit              56e3a1766e37893a0f4c91166f130bfffbab425b
replacement-cycle commit       recorded by the commit containing this status
candidate record inventory     empty
acceptance.md                  absent
active execution aid          present
M2-S09                         IN PROGRESS
M2                             NOT DELIVERED
```

The rejected candidate record and rejection summary have been retired from the
working tree. They remain recoverable from the reviewer-owned history and are
not reusable as evidence for the replacement candidate.

## Closed review findings

### S09-RF-01 — Reviewer lifecycle coherence

Closed by one shared lifecycle validator and permanent regressions covering:

```text
READY / IN PROGRESS
    no record or acceptance summary; active aid present

CANDIDATE READY FOR REVIEW
    one implementer-phase record; null decision; candidate summary; aid present

REVIEW CHANGES REQUIRED
    one reviewer-phase rejected record; rejection summary; aid present

COMPLETED
    one reviewer-phase ACCEPTED record; acceptance summary; aid absent
```

The tests reject every incoherent state/decision combination and stale
phase-specific summary marker. The real rejected record passed reviewer-phase
validation before retirement.

### S09-RF-02 — Fail-closed final-gate runner

Closed by a pure effective-status policy and a public runner result derived from
that policy:

```text
raw pytest non-zero                     -> non-zero
target FAIL or BLOCKED                  -> non-zero
SKIP / XFAIL / XPASS / RERUN            -> non-zero
missing JUnit                            -> all targets BLOCKED / non-zero
all targets PASS + clean census          -> zero
reviewed warnings alone                  -> zero
```

The public JSON now reports the effective `exit_status`, the raw
`pytest_exit_status`, every non-PASS target and bounded diagnostics.

## Authorized correction boundary

The correction is test/evidence-only. It may modify, as needed:

```text
tests/support/s09_acceptance.py
tests/test_m2_s09_acceptance.py
tests/test_m2_s08_evidence.py
tests/test_m2_s08_negative_surface.py
docs/milestones/M2/evidence/README.md
docs/milestones/M2/acceptance.md
docs/milestones/M2/evidence/candidate-*.json
docs/milestones/M2/status.md
```

It must not modify:

```text
src/netauto/
public API or DTOs
CLI behavior or grammar
Health
schema, DDL, indexes or Alembic graph
dependencies, uv.lock or runtime.pylock.toml
version 0.2.0 or wheel content
frozen contract, architecture or steps
```

The rejected record and rejection summary may be retired from the working tree
when the implementer starts the new cycle, after their reviewer-owned state is
preserved in Git history.

## Replacement gate progress

```text
S09-RF-01 / S09-RF-02 focused closure       PASS
rejected-state focused + traceability         87 passed / 0 non-PASS
Ruff format / lint                            PASS
Pyright strict                                PASS
review-fix commit published                  PASS
M2-S09 transition to IN PROGRESS             PASS
rejected JSON / acceptance.md retirement     PASS
new clean candidate SHA                      pending this commit publication
complete exact-candidate final gate          BLOCKED — TEST_DATABASE_URL absent
new candidate record / summary               NOT CREATED
exact-remote publication-integrity gate       NOT STARTED
```

No isolated rerun or reuse of the old JSON can substitute for the new full gate.

## Historical evidence from the rejected candidate

```text
evidence bundles              32 / 32 PASS
acceptance criteria           32 / 32 PASS
outcomes                      16 / 16 covered
canonical scenarios           83 / 83 PASS
safety predicates             21 / 21 PASS
bundle union                  369 unique targets / 516 passed
scenario union                166 unique targets / 190 passed
S06 / T8                      73 passed
S07 / T9                      18 passed
S08 / T10                     99 passed
schema / Alembic              33 passed / compare_metadata []
API / error / CLI             277 passed
runtime / schema guard        121 passed
PostgreSQL / concurrency      254 passed
non-PostgreSQL                614 passed
full repository               868 passed
skip / xfail / rerun          0 / 0 / 0
supported 40P01 / 40001       0 / 0
negative controls             40P01 x1 / 40001 x2
```

Artifact identity:

```text
wheel SHA-256
38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60

runtime-lock SHA-256
0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

These counts are historical context only. They are not reused in a replacement
record. The reviewer did not independently rerun the 868-test suite; the
reviewer inspected the old commit chain, record and harness.

## Active execution aid

The active non-normative S09 aid remains:

```text
docs/milestones/M2/wip/M2-S09-codex-prompt.md
```

It is not semantic authority. The bounded review-fix instructions in this
status and the reviewer handoff govern the next continuation; a dedicated
review-fix aid may replace it without adding a second active prompt.

## Immediate next action

Provide `TEST_DATABASE_URL` and execute the complete replacement final gate
from the exact clean replacement-cycle commit. Do not publish a candidate,
start AS-IS consolidation, declare delivery or merge until every prescribed
pre-publication and exact-remote gate passes.

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
```
