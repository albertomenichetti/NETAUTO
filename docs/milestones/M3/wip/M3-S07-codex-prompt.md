# Codex implementation prompt — M3-S07

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the ratified technology baseline, and the operational authorization in `status.md`.

If this prompt conflicts with an owning authority, stop the affected work and report the conflict. Do not reinterpret frozen semantics to make a final gate pass.

---

# Assignment

Execute exactly:

```text
M3-S07 — Full M3 acceptance and delivery-candidate gate
```

Work directly on branch:

```text
M3
```

The human-authorized implementation baseline is:

```text
16b761802369ff85b71aa966bfcfaeaac55b4ccf
Authorize M3-S07 implementation
```

The prompt-publication commit is a later documentation-only descendant of that authorization commit. Work from the current `origin/M3`; do not reset the branch to the authorization commit. Confirm the authorization commit remains in ancestry.

Current governance is exactly:

```text
M3-S00    reviewer-owned COMPLETED
M3-S01    reviewer-owned COMPLETED
M3-S02    reviewer-owned COMPLETED
M3-S03    reviewer-owned COMPLETED
M3-S04    reviewer-owned COMPLETED
M3-S05    reviewer-owned COMPLETED
M3-S06    reviewer-owned COMPLETED
M3-S07    READY — AUTHORIZED
```

S07 creates **no new M3-VER identity** and has **no planned business behavior**. It must select one delivery-candidate commit, execute the complete frozen final gate against that exact candidate, and publish truthful candidate evidence for reviewer inspection.

Do **not** mark `M3-S07` `COMPLETED`. Do **not** mark M3 `ACCEPTED`, `DELIVERED`, merged, released or tagged. Reviewer acceptance and final milestone delivery approval remain separate governance decisions.

Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release.

---

# 1. Mandatory repository pre-flight

Before changing any file, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
docs/milestones/M3/architecture/read-projections.md
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/cli.md
docs/milestones/M3/architecture/verification.md
docs/milestones/M3/steps.md
docs/milestones/M3/status.md

docs/milestones/M3/evidence/M3-S06-candidate.md
docs/milestones/M3/wip/M3-S07-codex-prompt.md

tests/support/m3_evidence.py
tests/test_m3_traceability.py
tests/test_m3_s06_integration.py
all accepted M3-S00..S05 evidence modules
```

Inspect the final-gate patterns already delivered by the project only as implementation/evidence precedent, not as M3 semantic authority. In particular, M2 final-acceptance helpers may be reused as a style reference where useful, but **do not import M2-only acceptance requirements into M3**.

Pre-flight must confirm:

```text
checked-out branch                    M3
origin/M3 ancestry                    includes 16b761802369ff85b71aa966bfcfaeaac55b4ccf
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M3-S00..S06                           reviewer-owned COMPLETED
M3-S07                                READY or IN PROGRESS
open contract findings                0
open architecture findings            0
incompatible reopen                   none
project version                       0.2.0
GET registry                          22 exact
cursor registry                       12 exact
CLI 201 registry                       8 exact
M3 evidence registry                  19 exact
migration graph                       one root/head = 0001_m2_kernel
TEST_DATABASE_URL                     available
```

Authorized non-drift baselines remain:

```text
pyproject.toml blob SHA               d20bbb94739a74ebfb0bd27291b6e4f130d24c5f
uv.lock blob SHA                      0aa980926fda5f42ee3a7d3cedc64f9fcf8c2d23
migration file                        src/netauto/migrations/versions/0001_m2_durable_kernel.py
migration blob SHA                    27fc85e0b4411332fce87c406b6216b35db6eb20
migration revision                    0001_m2_kernel
```

These SHAs are evidence baselines, not permission to reset files.

When S07 work actually begins, `status.md` may move from `READY` to `IN PROGRESS`. Do not mark it completed.

---

# 2. Hard scope boundary

S07 is a final validation/evidence slice.

## In scope

```text
small permanent S07 acceptance/evidence helpers if needed
final evidence-lifecycle tests if needed
execution of every M3-VER-01..19 target on one candidate
22/22 GET, 12/12 cursor and 8/8 CLI census revalidation
real-PostgreSQL final evidence
schema/Alembic/dependency/lock/version non-drift proof
locked build/static/full-suite final gate
artifact metadata for the build produced from the candidate
final change review against frozen M3 authorities
one durable S07 candidate evidence record
one candidate-ready acceptance summary
operational status update to CANDIDATE READY FOR REVIEW
```

Permanent S07 helpers must **derive** from the S06 `tests/support/m3_evidence.py` registries rather than duplicate or redefine the 8 OUT / 19 AC / 19 VER / 22 GET / 12 cursor / 8 CLI semantics.

## Out of scope

Do not introduce:

```text
new business behavior
new resource or public route
new DTO field
new filter/order/pagination behavior
new cursor identity or codec version
new Location or parent-tri-state semantics
schema/table/index/constraint changes
new Alembic revision
runtime dependency or uv.lock change
project-version change
mutation-lock/retry redesign
cross-request snapshot guarantee
unrelated cleanup/refactor
release/tag/merge action
```

If the final gate exposes a bounded implementation defect against already-frozen authority, do not hide it by weakening tests or evidence. A correction may be made only if it preserves the frozen semantics and stays within the authorized S07 final-gate purpose; any correction creates a **new candidate SHA** and requires the **entire final gate to be rerun**. If the failure is an authority contradiction, report the required reopen instead of patching around it.

---

# 3. One immutable delivery-candidate SHA

The final gate must be tied to one exact commit.

Recommended publication discipline:

```text
A. implementation/final-gate candidate commit
    - contains any S07 test/support/status-IN-PROGRESS changes required before testing
    - contains no claimed final PASS results that have not yet been executed
    - becomes the immutable candidate SHA

B. execute the complete final gate with working tree clean at exactly candidate SHA

C. evidence-publication commit
    - adds only final evidence / acceptance candidate summary / status candidate-ready metadata
    - references the tested candidate SHA exactly
    - does not change production/test semantics used by the gate
```

The tested delivery candidate is the SHA from step A, not the later evidence-publication commit.

Before starting final commands:

```text
git status --short       -> empty
HEAD                     -> candidate SHA
no uncommitted files
candidate contains every test/helper needed by the final gate
```

During the final gate, do not edit files. If anything must change, the current candidate is abandoned: make the correction, commit a new candidate and restart the complete gate from the beginning.

The evidence record must identify both:

```text
tested delivery candidate SHA
later evidence-publication HEAD
```

---

# 4. Final evidence lifecycle

Create one S07 candidate record under:

```text
docs/milestones/M3/evidence/M3-S07-candidate.md
```

The accepted S06 record remains historical evidence and is not replaced.

Create:

```text
docs/milestones/M3/acceptance.md
```

in **candidate** state only. Before reviewer action it must clearly contain wording equivalent to:

```text
# M3 Final Acceptance Candidate
Status: CANDIDATE READY FOR REVIEW
reviewer decision: PENDING / reviewer-owned
M3-S07 is not COMPLETED
M3 is not ACCEPTED or DELIVERED
final delivery approval has not been granted
```

It must not contain reviewer-owned `ACCEPTED`, `COMPLETED`, `DELIVERED`, release/tag/merge claims or equivalent wording.

`status.md` may move to:

```text
M3-S07 — CANDIDATE READY FOR REVIEW
```

only after every mandatory final gate passes on the identified candidate.

If a mandatory gate fails or is blocked, keep S07 `IN PROGRESS` / blocked and publish the exact blocker; do not create a false candidate-ready acceptance summary.

---

# 5. Re-execute all nineteen M3 evidence bundles

Final acceptance owns no new bundle ID. Re-execute:

```text
M3-VER-01 .. M3-VER-19
```

against the same candidate.

Use the machine-checkable mappings in:

```text
tests/support/m3_evidence.py
    M3_EVIDENCE_TO_TARGETS
```

as the target source of truth.

Requirements:

```text
all 19 bundle keys exact
all target sets non-empty
all mapped targets collected on the candidate
all mapped targets execute and PASS on the candidate
no PASS is inherited merely from an earlier slice run
no skipped/xfail/rerun target counts as PASS
```

A small S07 helper may derive the union of mapped targets and/or parse pytest JUnit output to demonstrate that every mapped concrete target passed. Prefer derived evidence over a manually duplicated list. Do not change `M3_EVIDENCE_TO_TARGETS` merely to make the gate easier; a mapping change requires truthful traceability justification and must remain consistent with frozen ADP-08.

The final evidence record must contain a disposition table for every `M3-VER-01..19` and point to the actual command/report that re-executed its target set.

---

# 6. Exact final censuses

Revalidate exact equality, not minimum counts:

```text
M3 outcomes                       8 / 8
M3 acceptance criteria           19 / 19
M3 evidence bundles              19 / 19
GET routes                       22 / 22
cursor-bearing routes            12 / 12
CLI 201 + Location operations     8 / 8
contract quality gates            8 / 8
```

Re-run the S06 machine-checkable traceability and integrated route/cursor/statement evidence. The final candidate must still prove:

```text
22 / 22 canonical GET success/failure compatibility
12 / 12 cursor binding and true multipage keyset completeness
8 / 8 CLI 201 Location matrix
22 / 22 GETs exactly one authoritative PostgreSQL business statement
T3 deterministic BEFORE and AFTER projection evidence
read-vs-mutation authority boundary
lifecycle trusted decoder boundary
ObjectTemplate HTTP/CLI parent tri-state
```

---

# 7. Mandatory real-PostgreSQL final gate

`TEST_DATABASE_URL` is mandatory. Missing PostgreSQL makes final acceptance `BLOCKED`, never PASS.

Record:

```text
PostgreSQL server version
Python version
uv version
pytest version
Ruff version
Pyright version
```

At minimum re-run:

```text
focused M3 S00..S07/traceability acceptance evidence
all mapped M3-VER target sets
migration/schema metadata evidence
material mutation/concurrency regressions
S06 22-route statement census
S06 T3 BEFORE/AFTER snapshot evidence
```

Canonical concurrency output must preserve:

```text
supported-path 40P01 = 0
unexpected 40001 = 0
negative-control SQLSTATE census remains intentionally separate
```

Do not confuse the structured worker-outcome scenario count printed by pytest with the separate authoritative 83-scenario registry; the permanent M2/current-AS-IS registry must still pass its exact 83-ID checks in the full repository suite.

---

# 8. Schema / Alembic / dependency / lock non-drift

Re-prove `M3-VER-17` on the final candidate.

Mandatory checks include:

```text
no new migration file
one Alembic base/head = 0001_m2_kernel
live PostgreSQL compare_metadata == []
metadata table census remains 15
no new M3 table/index/constraint
pyproject project version == 0.2.0
requires-python unchanged
runtime dependency list unchanged
pyproject.toml authorized blob unchanged
uv.lock authorized blob unchanged
0001 migration authorized blob unchanged
uv lock --check PASS
uv sync --locked PASS
```

Any unexplained delta is a blocking finding, not an incidental final-gate change.

---

# 9. Build/static gate and candidate artifact evidence

Run from the clean tested candidate:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Record the exact build outputs produced from the candidate. At minimum record for the wheel and sdist:

```text
filename
byte size
SHA-256
```

Do not change project version. Do not publish artifacts or create a release/tag.

The full repository suite remains the preserved project verification authority, including delivered installed-artifact/runtime evidence already present in that suite. S07 does not invent a new M3-only deployment capability.

---

# 10. Complete repository verification

Run:

```text
uv run pytest -q -m "not postgresql"
```

Then run the complete repository suite with required PostgreSQL:

```text
uv run pytest -q
```

Final normative disposition must be:

```text
skip / xfail / automatic rerun = 0 / 0 / 0
```

A previously reviewed third-party warning may be reported separately. Any new unexplained project warning/failure is a finding.

Record exact collection/pass/deselect/warning counts and duration for the final candidate.

Do not claim PASS for an unexecuted command.

---

# 11. Final change review

Before publishing candidate evidence, perform a final repository diff/review from the pre-M3 delivered baseline and from the S07 authorization/prompt baseline as appropriate.

Confirm the only intentional M3 observable deltas remain exactly the frozen set:

```text
GET/read semantic-certification responsibility correction
components cursor binds parent_object_id
Object-relative Relationship cursor binds object_id
parent_template_id adds lowercase null root-only state in HTTP/CLI
CLI registered Location materializer supports nested response JSON paths
```

Confirm no accidental escape into:

```text
new public route/resource
new response field
new filter/order semantics
offset/total-count/query DSL
schema/migration/dependency change
new cursor format
mutation semantic weakening
cross-request snapshot token/guarantee
hidden CLI enrichment GET
unrelated runtime/deployment capability
```

Reviewer-facing evidence must report:

```text
blocking M3 findings = 0
open incompatible reopen = 0
```

only if that is actually true.

---

# 12. Candidate evidence record contents

`docs/milestones/M3/evidence/M3-S07-candidate.md` must contain at minimum:

```text
cycle / slice
branch
authorization baseline
prompt-publication baseline
tested delivery candidate SHA
candidate parent
later evidence-publication HEAD (filled by publication discipline/handoff as applicable)
working-tree state
local/origin/remote synchronization
PR state
project version

Python/PostgreSQL/uv/pytest/Ruff/Pyright versions

8 OUT / 19 AC / 19 VER / 22 GET / 12 cursor / 8 CLI censuses
M3-VER-01..19 disposition table with concrete executed evidence
22/22 one-statement result
T3 BEFORE/AFTER result
schema compare_metadata result
migration graph result
dependency/lock/version non-drift result
canonical concurrency SQLSTATE result

exact verification commands
exit status / test counts / durations
skip/xfail/rerun census
warnings
wheel + sdist filename/size/SHA-256

final diff/scope review
production corrections made in S07, if any
open findings/blockers/reopen state
reviewer decision = PENDING
M3-S07 = not completed
M3 = not accepted/delivered
```

Do not edit the S06 candidate record to retroactively turn it into S07 evidence.

---

# 13. Candidate publication discipline

Only after every mandatory final gate passes may the implementer publish:

```text
M3-S07 — CANDIDATE READY FOR REVIEW
```

The publication commit may contain only candidate evidence/governance metadata that does not alter the tested implementation semantics. At minimum:

```text
docs/milestones/M3/evidence/M3-S07-candidate.md
docs/milestones/M3/acceptance.md
docs/milestones/M3/status.md
```

Keep `docs/milestones/M3/wip/M3-S07-codex-prompt.md` active while the slice awaits reviewer decision. Reviewer removes it only after accepted completion.

After publication verify:

```text
local HEAD == origin/M3 == remote M3
working tree clean
PR not created
publication HEAD identified
tested delivery candidate SHA remains explicitly identified
no semantic file changed after the tested candidate
M3-S07 is CANDIDATE READY FOR REVIEW, not COMPLETED
M3 is not ACCEPTED/DELIVERED
```

If a post-candidate semantic/test helper change becomes necessary, the prior evidence is invalid for final acceptance: create a new candidate and rerun the entire final gate.

---

# 14. Required final handoff from Codex

Report at minimum:

```text
M3-S07 candidate ready for reviewer inspection
branch
authorization baseline
prompt baseline
tested delivery candidate SHA
evidence-publication HEAD
push/sync state
working-tree state
PR state
S07 operational state
M3 acceptance/delivery state

changed files before candidate
files added only by evidence publication
all final censuses
M3-VER-01..19 PASS table
PostgreSQL one-statement census
T3 BEFORE/AFTER result
schema/migration/dependency non-drift
build artifact hashes
full commands/results/counts/durations
tool/runtime versions
skip/xfail/rerun/warning census
canonical 40P01 / unexpected 40001 result
final scope review
open findings/blockers/reopens
```

If every mandatory gate passes, use wording equivalent to:

```text
M3-S07 delivery candidate prepared and ready for reviewer inspection.
```

Do not say that M3-S07 is completed or that M3 is accepted, delivered, released, merged or tagged.