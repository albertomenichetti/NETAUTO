# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S09 REVIEW CHANGES REQUIRED

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S09 — REVIEW CHANGES REQUIRED
current task    close S09-RF-01 and S09-RF-02 in the test-only final-gate harness
blockers        two bounded S09 harness findings; M2 remains NOT DELIVERED
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
| Implementation | AUTHORIZED — bounded `M2-S09` review fixes only |
| Final acceptance | REVIEW CHANGES REQUIRED |
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
| `M2-S09` | REVIEW CHANGES REQUIRED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S08` are reviewer-owned `COMPLETED`. M2-S09 remains open
inside the same slice.

## Reviewer-owned decision

Rejected candidate chain:

```text
starting reviewer-owned HEAD   98405300ffd009a96ba187c8e5fe6f93d489303e
harness / candidate commit     b0546b1109c66a57195c50294291cb4a32ad48f2
evidence/status publication    0b1de73487061f68ed96ef78f48ad67866f11867
remote-integrity record        c8e4fc04874da6ef28d80115bd6c4d7aaeb4441f
review decision                REVIEW CHANGES REQUIRED
review decision commit         recorded by the commit containing this status
M2                             NOT DELIVERED
```

The candidate evidence remains at:

```text
docs/milestones/M2/evidence/candidate-b0546b1109c66a57195c50294291cb4a32ad48f2.json
docs/milestones/M2/acceptance.md
```

The candidate record now carries the finite reviewer decision and the two open
review findings. The green runtime evidence remains supporting evidence; it
does not permit reuse of `b0546b1...` after the harness changes.

## Open findings

### S09-RF-01 — Reviewer lifecycle coherence

The S09 lifecycle parser and permanent tests do not represent
`REVIEW CHANGES REQUIRED`. The current checks can also accept an incoherent
`COMPLETED` state with `REVIEW CHANGES REQUIRED`, and they require
candidate/pending wording from `acceptance.md` even after a future completion.

Required exact matrix:

```text
READY / IN PROGRESS
    record absent
    acceptance.md absent
    active S09 aid present

CANDIDATE READY FOR REVIEW
    exactly one record
    reviewer_decision null
    candidate/pending summary
    active S09 aid present

REVIEW CHANGES REQUIRED
    exactly one rejected record
    reviewer_decision REVIEW CHANGES REQUIRED
    rejection summary
    active S09 aid present

COMPLETED
    exactly one accepted record
    reviewer_decision ACCEPTED
    acceptance summary
    active S09 aid absent
```

Permanent regressions must reject every incoherent state/decision combination.

### S09-RF-02 — Fail-closed final-gate runner

`tests.support.s09_acceptance._run_group()` currently returns only the raw
pytest exit status. It must fail when any requested target is not `PASS`, or
when skip, xfail, xpass or rerun evidence is observed, even if pytest exits
zero.

Permanent regressions must cover:

```text
all targets PASS                 -> exit 0
pytest non-zero                  -> non-zero
missing/BLOCKED target           -> non-zero
SKIP                             -> non-zero
XFAIL                            -> non-zero
XPASS summary                    -> non-zero
RERUN                            -> non-zero
```

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

## Required new candidate cycle

```text
1. move M2-S09 to IN PROGRESS;
2. fix S09-RF-01 and S09-RF-02 only;
3. retire the rejected candidate JSON and rejection acceptance.md;
4. freeze and push a new harness/candidate SHA;
5. rerun the complete exact-candidate final gate from zero;
6. publish exactly one candidate-<NEW_SHA>.json and acceptance.md;
7. rerun the complete exact-remote publication-integrity gate;
8. hand off only M2-S09 CANDIDATE READY FOR REVIEW / M2 NOT DELIVERED.
```

No isolated rerun or reuse of the old JSON can substitute for the new full gate.

## Evidence retained from the rejected candidate

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

The reviewer did not independently rerun the 868-test suite. Runtime results
above are the implementer's exact-candidate and exact-remote evidence; the
reviewer independently inspected the commit chain, evidence record and harness.

## Active execution aid

The active non-normative S09 aid remains:

```text
docs/milestones/M2/wip/M2-S09-codex-prompt.md
```

It is not semantic authority. The bounded review-fix instructions in this
status and the reviewer handoff govern the next continuation; a dedicated
review-fix aid may replace it without adding a second active prompt.

## Immediate next action

Continue M2-S09 with the bounded test-only correction of `S09-RF-01` and
`S09-RF-02`. Do not start AS-IS consolidation, delivery or merge.

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
