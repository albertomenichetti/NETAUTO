# Codex review-fix prompt — M3-S07

**Status:** NON-NORMATIVE REVIEW-FIX EXECUTION AID.

This file is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the reviewer-owned decision in `docs/milestones/M3/acceptance.md`, and the operational authority in `docs/milestones/M3/status.md`.

If this prompt conflicts with an owning authority, stop the affected path and report the conflict. Do not weaken final evidence to make the review pass.

---

# Assignment

Fix exactly the two open findings on:

```text
M3-S07 — Full M3 acceptance and delivery-candidate gate

S07-RF-01 — final-acceptance lifecycle is not closed in permanent evidence
S07-RF-02 — mapped-target final-gate command is not recorded exactly
```

Work directly on branch:

```text
M3
```

The original S07 implementation authorization remains:

```text
16b761802369ff85b71aa966bfcfaeaac55b4ccf
Authorize M3-S07 implementation
```

The reviewer decision state before this review-fix prompt is:

```text
first tested candidate      1f018a771227087a5c629e644d77c06879585003
first publication           5af225375a1f27414be5455199f0ae84991b379b
review status commit        4b45ec736c96d04c525c7b133e41d0f2294d3443
review decision commit      f14953174fbc88c4f955d85ed2a763467f727501
review outcome              REVIEW CHANGES REQUIRED
S07-RF-01                   OPEN
S07-RF-02                   OPEN
M3-S07                      NOT COMPLETED
M3                          NOT ACCEPTED / NOT DELIVERED
```

Work from current `origin/M3`; do not reset to the rejected candidate or authorization baseline. Confirm all listed commits remain in ancestry.

Only same-slice review fixes are authorized. Do not start delivery/consolidation. Do not create a PR, merge, rebase, force-push, tag, release or publish artifacts.

---

# 1. Mandatory pre-flight

Re-read at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
docs/milestones/M3/architecture/verification.md
docs/milestones/M3/steps.md
docs/milestones/M3/status.md
docs/milestones/M3/acceptance.md

docs/milestones/M3/evidence/M3-S06-candidate.md
docs/milestones/M3/evidence/M3-S07-candidate.md
docs/milestones/M3/wip/M3-S07-codex-prompt.md
docs/milestones/M3/wip/M3-S07-review-fix-prompt.md

tests/support/m3_evidence.py
tests/test_m3_traceability.py
tests/test_m3_s06_integration.py
```

M2 final-acceptance lifecycle helpers may be inspected only as implementation style precedent. Do not import M2-only requirements into M3.

Pre-flight must confirm:

```text
branch                       M3
M3-S00..S06                  reviewer-owned COMPLETED
M3-S07                       REVIEW CHANGES REQUIRED
software implementation      S07 REVIEW FIX ONLY
open findings                exactly S07-RF-01 / S07-RF-02
contract/architecture reopen none
project version              0.2.0
schema/migration/dependencies unchanged
TEST_DATABASE_URL            available before final rerun
```

---

# 2. Hard scope boundary

Authorized changes are limited to:

```text
permanent test/support changes required to close S07-RF-01
review-fix lifecycle assertions/tests
an optional small committed S07 final-gate helper required to close S07-RF-02
status transitions within S07 review-fix/candidate states
replacement S07 candidate evidence publication
replacement candidate-state acceptance summary
```

Do not change production code merely because this is the last slice.

Production changes are authorized only if the corrected final gate exposes a separate frozen implementation defect. If that occurs, report it before treating the candidate as final; any correction creates another candidate and requires another full final-gate restart.

Explicitly forbidden without a reopen or separate authorization:

```text
new business behavior
new route/resource/DTO/filter/order semantics
cursor codec/version change
schema/table/index/constraint change
Alembic revision
runtime dependency or uv.lock change
project-version change
mutation semantic weakening
cross-request snapshot guarantee
release/tag/merge/delivery/consolidation work
new M3-VER identity
```

---

# 3. S07-RF-01 — close the reviewer-owned lifecycle before candidate selection

## Problem

The rejected candidate's permanent target:

```text
tests/test_m3_traceability.py::test_m3_contract_quality_gates_and_normative_state_are_closed
```

accepts only active S07 states and requires the S07 execution prompt to remain active. Therefore a reviewer transition to `COMPLETED` plus execution-aid retirement would make permanent `M3-VER-18` evidence fail immediately.

## Required result

Before selecting the replacement immutable candidate, implement a lifecycle-aware final-acceptance evidence model that covers both the current review/candidate states and the future reviewer-owned completed state.

At minimum the permanent evidence must distinguish:

```text
REVIEW CHANGES REQUIRED / IN PROGRESS
    -> S07 is the only authorized implementation/review-fix scope
    -> M3 not accepted/delivered
    -> active execution-aid inventory is valid for review work

CANDIDATE READY FOR REVIEW
    -> reviewer decision PENDING
    -> M3-S07 not COMPLETED
    -> M3 not accepted/delivered
    -> candidate evidence exists
    -> S07 execution aid(s) may remain active until reviewer action

COMPLETED reviewer state
    -> acceptance.md reviewer decision ACCEPTED
    -> M3-S07 COMPLETED
    -> software implementation NOT AUTHORIZED
    -> no active M3-S* Codex execution/review-fix prompt
    -> M3 remains NOT DELIVERED
    -> final delivery/consolidation remains a separate transition
```

The candidate does **not** need the live repository to be in `COMPLETED` state during its final gate. It must contain testable lifecycle logic proving that the future reviewer-only documentation transition is already a supported state.

Recommended shape:

```text
small pure parser/validator in tests/support/m3_s07_acceptance.py (or equivalent)
unit tests with synthetic READY/REVIEW/CANDIDATE/COMPLETED document sets
one actual-repository assertion for the current candidate state
```

Equivalent bounded design is allowed.

Do not merely add the literal word `COMPLETED` to one tuple while still hard-wiring active prompt/software-authorization assertions. The state-dependent invariants must be modeled coherently.

The completed-state model must use wording consistent with the M3/M2 governance boundary:

```text
M3-S07 COMPLETED / final acceptance ACCEPTED
M3 NOT DELIVERED
final delivery approval/consolidation still separate
```

No test/evidence semantic change may be required from the reviewer after the replacement candidate has passed.

---

# 4. S07-RF-02 — make the mapped-target gate exactly reproducible

## Problem

The rejected evidence record described the registry-derived final gate using a prose placeholder inside a heredoc instead of the literal executable command/script.

## Required result

The replacement evidence record must contain an exact reproducible command for the gate that:

```text
imports M3_EVIDENCE_TO_TARGETS from tests/support/m3_evidence.py
derives the sorted union of all 19 bundle target sets
requires all 19 bundle keys exact and target sets non-empty
executes the derived targets on the replacement candidate
handles parametrized pytest node IDs correctly
uses JUnit or equivalent deterministic result parsing
fails on missing/failure/error/skip/xfail/rerun
records target count, concrete case count and exit status
```

Preferred options:

1. Add a small committed test-only helper/CLI and record one literal invocation, for example conceptually:

```text
uv run python -m tests.support.m3_s07_acceptance run-mapped-bundles ...
```

2. If retaining an inline Python heredoc, write the complete literal Python body in the evidence record exactly as executed.

Do not duplicate/redefine `M3_EVIDENCE_TO_TARGETS`; derive from it.

---

# 5. Replacement candidate discipline

RF-01 changes permanent test/evidence code. Therefore the rejected candidate cannot be accepted.

Required sequence:

```text
A. implement RF-01 and any committed RF-02 helper
B. update status to an authorized S07 review-fix IN PROGRESS state if needed
C. run focused tests while developing
D. commit every code/test/helper change
E. select the new immutable tested delivery-candidate SHA
F. verify working tree clean at that SHA
G. restart the COMPLETE S07 final gate from its first command
H. do not edit any file during the final gate
I. if any file must change, abandon the SHA and restart A..H with another candidate
J. only after every gate passes, publish corrected evidence/acceptance/status docs in a later docs-only commit
```

The replacement tested candidate must contain all lifecycle/helper semantics used by the gate. The later publication commit must not change test or production semantics.

---

# 6. Complete final gate must be rerun

Re-execute the complete frozen S07 gate against the replacement SHA. Nothing may be inherited as final PASS from `1f018a771227087a5c629e644d77c06879585003`.

Mandatory final disposition remains:

```text
M3-VER-01 .. M3-VER-19             PASS
GET route census                    22 / 22
cursor route census                 12 / 12
CLI 201 Location census              8 / 8
contract quality gates               8 / 8
mapped bundle targets               all present / collected / PASS
22 GET business statements          exactly one each
T3 snapshot                         BEFORE + AFTER PASS
required PostgreSQL                 PASS
schema compare_metadata             []
Alembic root/head/current            0001_m2_kernel
schema/migration/dependency drift   0
Ruff format/check                   PASS
Pyright strict                      PASS
uv lock/sync/build                  PASS
collection                          PASS
non-PostgreSQL suite                PASS
full repository suite               PASS
normative skip/xfail/rerun          0 / 0 / 0
supported-path 40P01                0
unexpected 40001                    0
blocking M3 product findings        0
open incompatible reopen            0
end-to-end traceability             COMPLETE
```

Use the original `M3-S07-codex-prompt.md` sections 5–12 as the complete final-gate authority in addition to this bounded review-fix prompt.

Record wheel and sdist filename/bytes/SHA-256 from the replacement clean candidate. Do not publish them.

---

# 7. Replacement evidence publication

After the complete gate passes, publish a docs-only commit that updates:

```text
docs/milestones/M3/evidence/M3-S07-candidate.md
docs/milestones/M3/acceptance.md
docs/milestones/M3/status.md
```

The replacement candidate record must replace the first candidate's final-gate claims with the new exact SHA/run. Git history and `status.md` retain the rejected first-candidate identity and findings.

`acceptance.md` returns to candidate state only after the replacement gate passes:

```text
# M3 Final Acceptance Candidate
Status: CANDIDATE READY FOR REVIEW
reviewer decision       PENDING / reviewer-owned
replacement candidate  <exact SHA>
S07-RF-01 / S07-RF-02   candidate-fixed / reviewer closure pending
M3-S07                  not COMPLETED
M3                      not ACCEPTED / not DELIVERED
final delivery approval not granted
```

`status.md` may then move to:

```text
M3-S07 CANDIDATE READY FOR REVIEW
review findings 2 / 2 candidate-fixed — reviewer closure pending
```

Do not mark findings reviewer-closed. Do not mark S07 completed. Do not mark M3 accepted/delivered.

The publication commit must contain documentation/evidence state only. If it changes test/production semantics, it is not a docs-only publication and the candidate must be reconsidered.

---

# 8. Required handoff

Report at minimum:

```text
branch
review-fix baseline / prompt-publication SHA
rejected first candidate
replacement tested candidate SHA
replacement candidate parent
replacement evidence-publication HEAD
local/origin/remote equality
clean working tree
PR state

S07-RF-01 closure evidence
S07-RF-02 closure evidence
lifecycle helper/tests and exact node IDs
exact mapped-target command
19-bundle disposition
all exact censuses
22/22 statement result
T3 result
non-drift result
artifact identities
complete command ledger/counts/durations
skip/xfail/rerun/warning census
concurrency SQLSTATE census
production corrections, if any
blockers/findings/reopen state
```

Expected handoff state after a successful rerun:

```text
M3-S07                 CANDIDATE READY FOR REVIEW
S07-RF-01              candidate-fixed / reviewer closure pending
S07-RF-02              candidate-fixed / reviewer closure pending
reviewer decision      PENDING
M3                     NOT ACCEPTED / NOT DELIVERED
final delivery         NOT AUTHORIZED
```

The reviewer alone may close the findings and accept the replacement candidate.