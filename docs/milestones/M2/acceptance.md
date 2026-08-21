# M2 Final Acceptance Review

Status: REVIEW CHANGES REQUIRED

This is the reviewer-owned decision for the final-acceptance candidate. It is
durable evidence, not semantic authority.

## Candidate identity

```text
candidate commit       b0546b1109c66a57195c50294291cb4a32ad48f2
evidence publication   0b1de73487061f68ed96ef78f48ad67866f11867
integrity record       c8e4fc04874da6ef28d80115bd6c4d7aaeb4441f
evidence record        docs/milestones/M2/evidence/candidate-b0546b1109c66a57195c50294291cb4a32ad48f2.json
branch                 M2
reviewer decision      REVIEW CHANGES REQUIRED
```

The executed candidate evidence remains materially green:

```text
evidence bundles             32 / 32 PASS
acceptance criteria          32 / 32 PASS
outcomes                     16 / 16 covered
canonical scenarios          83 / 83 PASS
safety predicates            21 / 21 PASS
installed T9                 PASS
full repository              868 passed
skip / xfail / rerun         0 / 0 / 0
supported 40P01              0
unexpected 40001             0
compare_metadata             []
open runtime findings        0
```

Artifact identity remains:

```text
wheel SHA-256
38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60

runtime-lock SHA-256
0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

## Reviewer findings

### S09-RF-01 — Reviewer lifecycle coherence

The permanent S09 lifecycle does not currently model
`REVIEW CHANGES REQUIRED`. It can also admit incoherent combinations such as
`COMPLETED` with a non-accepted reviewer decision and requires candidate-state
wording even after completion.

The lifecycle must become an exact state/decision matrix:

```text
READY / IN PROGRESS
    no candidate record
    no acceptance.md

CANDIDATE READY FOR REVIEW
    one record
    reviewer_decision = null
    candidate/pending acceptance summary

REVIEW CHANGES REQUIRED
    one rejected record
    reviewer_decision = REVIEW CHANGES REQUIRED
    reviewer rejection summary
    active S09 aid retained

COMPLETED
    one accepted record
    reviewer_decision = ACCEPTED
    reviewer acceptance summary
    active S09 aid retired
```

### S09-RF-02 — Fail-closed final-gate runner

The bundle/scenario runner currently returns only the raw pytest exit status.
It must return non-zero whenever any requested target is `FAIL` or `BLOCKED`,
or when the collected census contains a skip, xfail, xpass or rerun, even when
pytest itself exits zero.

## Decision boundary

The findings are confined to the test-only S09 acceptance harness and lifecycle
documentation. They do not demonstrate a production, API, CLI, Health, schema,
migration, dependency, lock or artifact defect.

The current candidate is rejected as the final S09 candidate because correcting
the harness changes the candidate commit. The next candidate must use a new SHA
and must repeat the entire exact-candidate and exact-remote final gate.

```text
M2-S09                 REVIEW CHANGES REQUIRED
M2                     NOT DELIVERED
AS-IS consolidation    not started
merge                  not executed
```
