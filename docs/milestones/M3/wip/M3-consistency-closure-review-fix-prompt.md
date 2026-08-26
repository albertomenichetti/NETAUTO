# Codex review-fix prompt — M3 consistency closure

**Status:** NON-NORMATIVE POST-CONSOLIDATION REVIEW-FIX EXECUTION AID.

This execution aid is subordinate to `AGENTS.md`, `docs/general/linee_guida_progetto.md`, the accepted current AS-IS under `docs/architecture/`, the FINAL M3 consistency-closure specification, and the reviewer-owned finding recorded in `docs/milestones/M3/status.md`.

Do not reinterpret current semantics or rerun unrelated work merely to make the review pass.

---

# Assignment

Fix exactly:

```text
M3-CC-RF-01 — post-publication remote-HEAD integrity/lifecycle evidence missing
```

Work directly on branch:

```text
M3
```

Relevant immutable identities:

```text
consistency specification     994414747ef3577e5a6f83bdb62bd2fc9146beff
operational authorization     55cccf0a19786a904d4fad48fd614b211ead48af
AUDITED_ASIS_SHA              2f091f4ca021153280ed37fad7b4b2cc730195f9
candidate publication         68943e222a612577dd66a36af4a6b7e82b3f1b35
review finding status commit  3c804d2fb8477b61bd2345ff442585750c5e0a4d
```

The semantic closure result is not rejected:

```text
CC-01 .. CC-15            PASS
current-owner findings    0
owner corrections         0
AUDITED_ASIS_SHA          unchanged
M3                        NOT DELIVERED
```

Only evidence completion for the later publication state is authorized.

Do not create a PR. Do not merge, rebase, force-push, tag, release or publish artifacts.

---

# 1. Pre-flight

Re-read:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/milestones/M3/consistency-closure.md
docs/milestones/M3/consistency-closure-report.md
docs/milestones/M3/status.md
docs/milestones/M3/acceptance.md
tests/test_m3_traceability.py
tests/test_m3_s07_acceptance.py
```

Confirm:

```text
branch M3
AUDITED_ASIS_SHA remains 2f091f4ca021153280ed37fad7b4b2cc730195f9
publication 68943e222a612577dd66a36af4a6b7e82b3f1b35 remains in ancestry
review finding M3-CC-RF-01 is the only open consistency finding
software implementation NOT AUTHORIZED
M3 NOT DELIVERED
```

Work from current `origin/M3`; do not reset published history.

---

# 2. Scope

Authorized repository modification:

```text
docs/milestones/M3/status.md
```

only to record exact post-publication evidence and return the consistency-closure gate to `CANDIDATE READY FOR REVIEW` if all bounded checks pass.

Do not modify:

```text
docs/architecture/
docs/milestones/M3/consistency-closure-report.md
src/
tests/
pyproject.toml
uv.lock
migrations
frozen M3 contract/architecture/steps
acceptance evidence
technology baseline
```

If a bounded check exposes a substantive defect, STOP and report it. Do not repair it under this prompt.

---

# 3. Exact post-publication target

The original publication target that lacked recorded post-publication evidence is:

```text
68943e222a612577dd66a36af4a6b7e82b3f1b35
```

The current branch now also contains reviewer finding/status documentation. Therefore the evidence fix must prove two things separately:

```text
A. publication integrity of 68943e222a612577dd66a36af4a6b7e82b3f1b35
B. current repository lifecycle integrity after the reviewer finding/status commit
```

Do not alter or replace `AUDITED_ASIS_SHA`.

---

# 4. Bounded publication-integrity checks

Record literal commands and exact results for at least:

```bash
git diff --name-only 2f091f4ca021153280ed37fad7b4b2cc730195f9 68943e222a612577dd66a36af4a6b7e82b3f1b35
```

Required exact file set:

```text
docs/milestones/M3/consistency-closure-report.md
docs/milestones/M3/status.md
```

Then prove no semantic/executable input changed in the publication commit:

```bash
git diff --exit-code 2f091f4ca021153280ed37fad7b4b2cc730195f9 68943e222a612577dd66a36af4a6b7e82b3f1b35 -- docs/architecture src tests pyproject.toml uv.lock src/netauto/migrations
```

Required result: exit 0 / empty diff.

Verify the publication report/status markers directly at that commit, for example with a temporary Python or shell check, requiring at minimum:

```text
report Status = CANDIDATE READY FOR REVIEW
report AUDITED_ASIS_SHA = 2f091f4ca021153280ed37fad7b4b2cc730195f9
report CC-01..CC-15 all PASS
report open findings = 0
status consistency closure = CANDIDATE READY FOR REVIEW
status M3 = NOT DELIVERED
status software implementation = NOT AUTHORIZED
```

Use an executable literal command and record it exactly.

---

# 5. Bounded current lifecycle/integrity checks

From the current clean branch HEAD after syncing with `origin/M3`, run a bounded permanent regression selection that proves final-acceptance lifecycle and current governance remain valid. At minimum run:

```bash
uv run pytest -q tests/test_m3_traceability.py tests/test_m3_s07_acceptance.py
```

This must PASS with no skip/xfail/rerun.

Also verify:

```bash
git status --short
git rev-parse HEAD
git rev-parse origin/M3
```

and obtain/record the remote `refs/heads/M3` SHA using the normal repository workflow. Before any status evidence publication, local HEAD/origin/remote must be equal and working tree clean.

If the current reviewer-status state itself causes the permanent lifecycle tests to fail, report the failure instead of weakening the tests.

---

# 6. Evidence publication

If every bounded check passes, update only:

```text
docs/milestones/M3/status.md
```

Record:

```text
M3-CC-RF-01             CANDIDATE-FIXED — REVIEWER CLOSURE PENDING
original publication    68943e222a612577dd66a36af4a6b7e82b3f1b35
publication file-set audit PASS
semantic/executable diff audit PASS
publication report/status marker audit PASS
current lifecycle regression PASS
literal commands and exact exit/pass counts
current local/origin/remote equality
working tree clean before status publication
```

Return consistency closure to:

```text
CANDIDATE READY FOR REVIEW
```

Do not mark it `COMPLETED` and do not mark M3 delivered.

Because the status evidence commit itself comes after the checks, after pushing it verify local/origin/remote equality and clean working tree again. Report that final equality in the handoff; do not recursively rewrite status solely to embed its own SHA.

---

# 7. Handoff

Report:

```text
branch
M3-CC-RF-01 disposition
AUDITED_ASIS_SHA unchanged
original publication SHA
review-fix evidence/status publication SHA
exact bounded commands
publication file-set result
semantic/executable diff result
publication marker result
lifecycle regression command/count/result
skip/xfail/rerun census
local/origin/remote equality
working tree state
changed files
PR state
M3 NOT DELIVERED
```

Maximum claim:

```text
M3 CONSISTENCY CLOSURE — CANDIDATE READY FOR REVIEW
M3-CC-RF-01 — CANDIDATE-FIXED / REVIEWER CLOSURE PENDING
```

Do not claim closure `COMPLETED`, delivery, merge, release or tag.