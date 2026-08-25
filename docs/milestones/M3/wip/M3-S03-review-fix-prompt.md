# Codex review-fix prompt — M3-S03

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This review-fix prompt is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M3 contract and architecture set, FINAL/FROZEN `steps.md`, `docs/milestones/M3/status.md`, and the original `docs/milestones/M3/wip/M3-S03-codex-prompt.md`.

If this prompt conflicts with an owning authority, stop the affected work and report the conflict. Do not reinterpret frozen semantics to preserve the current candidate.

## Assignment

Correct exactly the two reviewer findings recorded for:

```text
M3-S03 — ObjectTemplate trusted recursive and aggregate read projections
```

Branch:

```text
M3
```

Reviewed candidate:

```text
2f287723703d33f2531328d8b85511603f881590
```

Reviewer findings/status record:

```text
1e955f2a9c42f2bd27167635b2774f1f0cd952f9
```

Work from current `origin/M3`; do not reset to either commit. Confirm both remain in ancestry.

Authorization remains exactly:

```text
M3-S00  COMPLETED
M3-S01  COMPLETED
M3-S02  COMPLETED
M3-S03  REVIEW CHANGES REQUIRED — AUTHORIZED FOR SAME-SLICE CORRECTION
M3-S04  NOT AUTHORIZED
M3-S05  NOT AUTHORIZED
M3-S06  NOT AUTHORIZED
M3-S07  NOT AUTHORIZED
```

Do not begin M3-S04. Do not create a PR, merge, rebase, force-push, tag or release.

---

# 1. Mandatory pre-flight

Re-read at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/read-projections.md
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/verification.md
docs/milestones/M3/steps.md
docs/milestones/M3/status.md

docs/milestones/M3/wip/M3-S03-codex-prompt.md
docs/milestones/M3/wip/M3-S03-review-fix-prompt.md
```

Confirm:

```text
branch                         M3
candidate in ancestry          2f287723703d33f2531328d8b85511603f881590
review record in ancestry      1e955f2a9c42f2bd27167635b2774f1f0cd952f9
M3-S03                         REVIEW CHANGES REQUIRED
M3-S04                         NOT AUTHORIZED
contract/architecture/steps    FINAL / FROZEN
reopen                         NONE REQUIRED
project version                0.2.0
```

When correction work begins, `M3-S03` may move operationally to `IN PROGRESS`. Do not mark `COMPLETED`.

---

# 2. S03-RF-01 — do not treat required/default absence as undecodable

## Reviewed defect

The candidate added a GET-side rule equivalent to:

```text
required=True + migration_default=None -> ObjectTemplateProjectionError -> 500
```

This is not a representational decoding requirement.

Frozen M3 read authority says GET must not answer whether persisted state would pass current mutation admission. The delivered public `PropertyDto` has:

```text
migration_default: JsonValue | None
```

and excludes the field when the value is `None`. The delivered database schema also permits a committed row with:

```text
required = true
migration_default = NULL
```

Therefore this state is representable and must remain readable even though new mutation input with the same semantic combination remains rejected.

## Required correction

Remove any GET/read-projector rule that rejects a persisted property solely because:

```text
required is true
and migration_default is None
```

For both:

```text
OT-GET-04 exact ObjectTemplateVersion
OT-GET-05 effective schema
```

the persisted property must be materialized normally. The public DTO may omit `migration_default` according to its existing serialization rule.

Do not weaken the mutation boundary. New create/revise input requiring a migration default must continue to be rejected by the delivered request/domain semantics.

## Required evidence

Replace the current false `M3-VER-07` fixture with positive trusted-read evidence:

```text
committed required=True / migration_default=NULL property
    -> GET exact version succeeds
    -> GET effective schema succeeds
    -> property remains present
    -> required remains true
    -> no fabricated migration_default

new mutation candidate with required=True and missing/null migration_default
    -> remains rejected through the existing bounded mutation/request boundary
```

Reassess the ObjectTemplate `M3-VER-07` target honestly.

If no structurally committable ObjectTemplate carrier exists that cannot be converted into a **mandatory public typed field**, record:

```text
ObjectTemplate M3-VER-07 target = NOT APPLICABLE
```

with permanent schema + DTO evidence. This is acceptable and is analogous to the accepted S02 DataType disposition.

Do not invent semantic-invalidity fixtures and call them materially undecodable.

Do not claim the global M3-VER-07 bundle PASS.

---

# 3. S03-RF-02 — exact recursion must be keyed by exact node identity

## Reviewed defect

The candidate `RP-05` CTE tracks recursion visitation only by stable `template_id` and suppresses a parent when that stable id has appeared earlier.

That can truncate a finite persisted exact-pin chain such as:

```text
A:2 -> B:1 -> A:1 -> root
```

The two A nodes are different exact ObjectTemplateVersion identities. Frozen `RP-05` owns exact persisted `(template_id, version)` pins; stable-lineage acyclicity is mutation-owned and must not be reintroduced into GET traversal.

## Required correction

`OT-GET-05` must follow every distinct exact parent pair:

```text
(template_id, version)
```

If a recursion-safety guard is needed, use exact-node identity, e.g. an equivalent of:

```text
visited exact pairs
```

not stable template identity alone.

A repeated stable template id at another exact version must not cause truncation, rejection or semantic repair.

A truly repeated exact pair may be bounded for recursion safety; do not turn that safety mechanism into mutation-cycle certification or a new public error contract.

Preserve:

```text
one SQL statement
ordinary read UoW
exact-pin source of truth
root-to-leaf deterministic ordering
declaring_template_id
independent property/component projection
404 exact leaf semantics
```

Do not change `OT-GET-06` into exact-version ancestry. `RP-06` remains stable-lineage ancestry by design.

## Required evidence

Add a committed PostgreSQL fixture with a finite exact chain containing the same stable template at two different versions, for example:

```text
A:2 -> B:1 -> A:1 -> root
```

with distinguishable declarations on the exact nodes.

Prove:

```text
GET effective-schema follows all exact pairs
A:1 is not silently dropped because A:2 appeared earlier
root-to-leaf projection is deterministic
no mutation semantic recertification is invoked
one business SQL statement remains true
```

Retain the existing evidence that `OT-GET-05` exact-pin ancestry and `OT-GET-06` stable ancestry are different semantics.

---

# 4. Preserve accepted S03 behavior

Do not regress the portions of the candidate that review did not reject:

```text
OT-GET-01 RP-01 trusted lineage page
OT-GET-02 RP-02 trusted exact lineage
OT-GET-03 RP-03 parent-rooted version page
OT-GET-04 typed independent property/component aggregate structure
OT-GET-05 one-statement exact-pin recursive projection
OT-GET-06 one-statement stable-ancestry capability page
ordinary read UoWs
no coherent_read() on six GET paths
PUBLISHED-RDV EXISTS remains capability membership
no RelationshipDefinition default-version recertification in OT-GET-06
S01 parent tri-state and cursor behavior
S02 DataType trusted reads
public routes/DTOs/cursor codec
```

Do not modify Object/Object-Relationship/lifecycle read paths owned by later slices.

---

# 5. Verification

Run focused review-fix evidence first, then the complete original S03 candidate gate.

At minimum report exact results for:

```text
review-fix RF-01 positive trusted-read + mutation-preservation target
review-fix RF-02 repeated-stable/distinct-exact-chain target
all tests/test_m3_s03_objecttemplate_reads.py
M3-S01 parent tri-state regressions
M3-S02 DataType trusted-read regressions
ObjectTemplate API/domain/concurrency affected suites
RelationshipDefinition capability/domain/scope/concurrency affected suites
```

Real PostgreSQL remains mandatory. Re-measure:

```text
OT-GET-01 = 1 business SQL statement
OT-GET-02 = 1
OT-GET-03 = 1
OT-GET-04 = 1
OT-GET-05 = 1
OT-GET-06 = 1
```

using the actual runtime PostgreSQL engine and deterministic statement observation.

Also run:

```text
uv lock --check
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
uv run pytest -q -m "not postgresql"
uv run pytest -q
uv build
```

Required:

```text
normative skip/xfail/rerun  0 / 0 / 0
Ruff                         PASS
Pyright                      PASS
full repository suite        PASS
new unexplained warning       0
```

Do not weaken, skip, xfail or retry a failing normative target.

Verify no forbidden delta in:

```text
schema/migrations
runtime dependencies
uv.lock
project version
public route inventory
public DTO shapes
cursor codec/version
M3-S04+ implementation
```

---

# 6. Corrected candidate status and handoff

If and only if both review findings are closed and every mandatory gate passes, update operational status to:

```text
M3-S03 — CANDIDATE READY FOR REVIEW
```

Record both findings as corrected, but do not mark them reviewer-closed yourself.

Do not mark:

```text
M3-S03 COMPLETED
M3-S04 READY
M3 DELIVERED
```

Commit and push the corrected candidate to branch `M3`. Do not create a PR.

Final handoff must include:

```text
slice / branch
authorization baseline
original prompt baseline
reviewed candidate SHA
review findings record SHA
review-fix prompt SHA/current head ancestry
corrected candidate SHA
changed files
S03-RF-01 correction and evidence
ObjectTemplate M3-VER-07 disposition
S03-RF-02 correction and exact-pair evidence
6/6 PostgreSQL statement counts
complete verification commands/results
skip/xfail/rerun counts
toolchain/PostgreSQL versions
non-drift facts
working tree / local HEAD / origin/M3 / remote M3 synchronization
M3-S04 remains NOT AUTHORIZED
```

Use the wording:

```text
M3-S03 corrected candidate implemented and ready for reviewer inspection.
```

Do not claim reviewer completion.
