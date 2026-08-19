# Codex review-fix prompt — M2-S06

**Status:** NON-NORMATIVE REVIEW-FIX EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Correct exactly the two reviewer findings recorded for:

```text
M2-S06 — Official CLI interactive REPL and formatted experience
```

Work directly on branch:

```text
M2
```

The reviewer-owned review-fix baseline is:

```text
827c15ccf16f89630f975f1b3faa644f0a709c27
docs(m2): keep S06 open for formatted and enrichment correctness
```

The reviewed candidate was:

```text
implementation    e0c7a55bdbb066437fb0189ebcb781b834c476d6
candidate         8d4074f57b214d158d288a65dccde15156bcd812
```

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    reviewer-owned COMPLETED
M2-S04    reviewer-owned COMPLETED
M2-S05    reviewer-owned COMPLETED
M2-S06    REVIEW CHANGES REQUIRED
M2-S07    BLOCKED
```

Implement only:

```text
S06-RF-01
    FORMATTED output must expose the exact resolved primary target identities
    even when the operator supplied a human selector and the direct response
    omits those identities.

S06-RF-02
    FORMATTED enrichment must reject identity-inconsistent secondary GET
    responses and detect stable-lineage cycles even when repeated lineages use
    different exact versions.
```

Preserve all conforming S06 and accepted S05 behavior. Do not start `M2-S07`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not add GitHub Actions or use artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before editing, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
docs/architecture/objecttemplate.md
docs/architecture/api.md
docs/architecture/verification.md

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

docs/general/technology_baseline.md
    STACK-01
    STACK-03
    STACK-07
    STACK-08
    STACK-09
    STACK-10

docs/milestones/M2/wip/M2-S06-codex-prompt.md
docs/milestones/M2/wip/M2-S06-review-fixes-codex-prompt.md
```

Confirm from the repository that:

```text
checked-out branch                    M2
origin/M2 ancestry                    includes 827c15cc...
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S05                                reviewer-owned COMPLETED
M2-S06                                REVIEW CHANGES REQUIRED or IN PROGRESS
M2-S07                                BLOCKED
open review findings                  exactly S06-RF-01 and S06-RF-02
relevant architecture reopen          none
```

Inspect at minimum:

```text
src/netauto/cli/model.py
src/netauto/cli/registry.py
src/netauto/cli/parser.py
src/netauto/cli/selectors.py
src/netauto/cli/transport.py
src/netauto/cli/protocol.py
src/netauto/cli/execution.py
src/netauto/cli/enrichment.py
src/netauto/cli/render.py
src/netauto/cli/repl.py
src/netauto/cli/main.py

src/netauto/transport/http/datatypes.py
src/netauto/transport/http/objecttemplates.py
src/netauto/transport/http/objects.py
src/netauto/transport/http/relationshipdefinitions.py
src/netauto/transport/http/relationships.py

all tests/test_m2_s05_*.py
all tests/test_m2_s06_*.py
tests/test_m2_traceability.py
docs/milestones/M2/status.md
```

The reviewed implementation is the starting realization. Do not rewrite the REPL or command core. Correct the smallest coherent boundaries that close both findings and add permanent evidence.

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` remains mandatory for the full repository gate and preserved PostgreSQL claims. Do not provision a database, invent credentials, use Docker/Testcontainers, substitute SQLite or fall back to localhost.

If a frozen authority conflicts with the correction, stop the affected point and report it. Do not edit frozen contract, architecture or steps to fit the code.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
FORMATTED presentation metadata for exact resolved primary targets
reuse of already-resolved RequestPlan/request trace identities
human-selector plus exact-ID visibility
bodyless direct success target identity
nullable/direct projection selected-resource identity
secondary enrichment GET identity validation
exact ObjectTemplateVersion identity validation
stable-lineage and exact-version cycle detection
bounded cli_protocol_error outcomes
truthful trace and connection-state regressions
S06 review-fix traceability
status/evidence updates for the corrected candidate
```

## 2.2 Out of scope

Do not introduce:

```text
new remote or local commands
new server routes or DTO fields
new public API behavior
new selector kinds or alternate grammar
hidden post-mutation GET
list/lifecycle per-item enrichment
unbounded presentation traversal
new error codes
changes to JSON result/trace schema
changes to S05 non-interactive behavior
changes to Health semantics
schema, migration, constraint or index changes
new dependency or lockfile change
release-version or runtime-lock work
installed Alembic/Linux baseline work
M2-S07, M2-S08 or M2-S09 work
authentication, profiles, credentials or persistent history
```

Preserve exactly:

```text
project version                  0.1.0
runtime dependency set          current S06 set
63 remote CommandSpec values
65 registry examples
8 local commands
15 authoritative tables
one Alembic base / one head
0001_m2_kernel
compare_metadata == []
41 mutations + 22 reads
1 Health route
83 scenarios / 21 predicates
all accepted S05 review-fix behavior
```

---

# 3. `S06-RF-01` — exact identities in FORMATTED direct output

## 3.1 Reviewed defect

The frozen FORMATTED contract requires:

```text
exact IDs remain visible even when names are resolved
```

The current implementation preserves original operator intent in `ParsedCommand` and resolves human selectors only in the request candidate. `render._resource()` and `render._no_content()` then rely on the original selector and direct response body.

This is insufficient where:

```text
operator selector
    -> human value

resolved primary path target
    -> exact UUID

direct body
    -> absent or does not contain the selected path target
```

A trace may contain the exact path, but normal FORMATTED output does not expose the trace.

## 3.2 Required result

FORMATTED output must deterministically expose the exact resolved identities needed to identify the direct primary target.

At minimum:

```text
human selector
    -> may remain visible as submitted intent

resolved primary selector/path identity
    -> exact UUID visible

selector-bearing path/body parameters needed to identify the operation target
    -> exact resolved values visible when the direct response omits them
```

The correction must use already-owned command execution data:

```text
resolved selector/parameters
RequestPlan
primary HttpRequestTrace
or one equivalent immutable presentation value
```

It must not perform an additional HTTP request.

## 3.3 Ownership constraints

Keep singular ownership:

```text
ParsedCommand
    -> original human intent

selector/request planning
    -> exact resolved request intent

CliResult/exchange trace
    -> actual HTTP evidence

FORMATTED presentation
    -> direct result plus exact target metadata
```

Do not mutate `ParsedCommand` into resolved intent and do not change interactive/non-interactive JSON. The accepted JSON contract must continue to report original command intent and exact actual exchanges.

Local implementation freedom includes a small immutable presentation-target value, renderer context or extraction from the primary request trace. Avoid parsing arbitrary URLs when the request planner already owns the exact values.

## 3.4 Required representative cases

Close at least:

```text
human-selected 204 operation
    example: datatype delete core.string
    -> selector lookup + primary DELETE only
    -> original core.string visible
    -> exact resolved datatype UUID visible

nullable selected-resource read
    example: object get-owner server01 returning null
    -> selected Object exact UUID visible
    -> no enrichment request merely to recover that UUID

projection/direct mutation omitting a path target
    example: object attach/detach with a human parent selector
    -> exact resolved parent identity visible
    -> other direct identifiers remain visible

exact UUID selector
    -> remains visible without duplication ambiguity
```

The implementation must generalize through registry/request metadata rather than hard-code only these examples.

## 3.5 Permanent evidence

Add deterministic tests that assert:

```text
exact UUID is in FORMATTED output
original human selector remains observable where intended
all direct IDs are unambiguous
primary result/body remains direct
no hidden GET occurs
exchange count and order are exact
JSON output is byte/schema compatible with S05
```

Include at least one test where the direct response is `204`, one where it is `200` with `null`, and one where it is a projection that omits the selected path target.

---

# 4. `S06-RF-02` — identity-safe enrichment and complete cycle detection

## 4.1 Reviewed defect

`enrichment._Context.get()` currently accepts a secondary GET result after DTO-shape validation and caches it under the requested identity. It does not prove that the returned identity equals the requested identity.

Current exact parent-version traversal also tracks repeated `(template_id, version)` pairs but can accept a repeated stable lineage at another version.

Both paths can produce a plausible but false human presentation.

## 4.2 Stable GET identity validation

Before caching or using any secondary stable resource, verify exact route identity:

```text
DataType GET
    returned id == requested datatype_id

ObjectTemplate GET
    returned id == requested template_id

Object GET
    returned id == requested object_id
```

A DTO-valid response for another resource is an invalid same-release response for this enrichment request.

## 4.3 Exact ObjectTemplateVersion identity validation

For:

```text
GET /object-templates/{template_id}/versions/{version}
```

require:

```text
returned template_id == requested template_id
returned version     == requested version
```

Reject a mismatch in either field before cache/use.

Do not weaken neutral DTOs or server contracts merely to implement client correlation. The check belongs to CLI protocol/enrichment realization.

## 4.4 Cache discipline

Cache only after all checks pass.

```text
cache key
    -> exact requested semantic identity

cached value
    -> identity-validated canonical response
```

A mismatched response must never seed the cache or influence a later enrichment.

## 4.5 Stable-lineage cycle detection

ObjectTemplate inheritance is stable-lineage acyclic. Exact version traversal must therefore track both:

```text
seen exact pairs
    (template_id, version)

seen stable lineages
    template_id
```

Reject at least:

```text
A:2 -> A:1 -> root
A:2 -> B:1 -> A:1
A:2 -> B:3 -> C:1 -> B:1
```

A repeated stable lineage is a cycle even when its exact version differs.

Continue to reject malformed half-pairs where only parent ID or parent version is present.

## 4.6 Failure result

Every identity mismatch or cycle must produce:

```text
source        protocol
code          cli_protocol_error
presentation  null / absent
trace         every actual primary and enrichment exchange exactly once, ordered
connection    remains CONNECTED
```

Only an actual transport failure disconnects the session.

No partial FORMATTED content may be emitted.

## 4.7 Permanent evidence

Inject deterministic controlled responses for at least:

```text
wrong DataType id
wrong ObjectTemplate id
wrong Object id
wrong ObjectTemplateVersion template_id
wrong ObjectTemplateVersion version
same stable lineage repeated at another version
multi-lineage cycle returning to an earlier lineage at another version
```

For every case assert:

```text
cli_protocol_error
no partial presentation
truthful complete trace
no cache pollution
session remains CONNECTED
no extra request after failure is known
```

Retain positive evidence for per-command memoization and valid root-terminating lineages.

---

# 5. Review-fix traceability

Create one explicit permanent registry, conceptually:

```text
S06_REVIEW_FIX_TARGETS = {
    "S06-RF-01": frozenset({...}),
    "S06-RF-02": frozenset({...}),
}
```

Integrate it into `tests/test_m2_traceability.py` or the existing singular traceability owner.

Require:

```text
exact finding census              2 / 2
both target sets non-empty
all targets exist
review-fix union executes PASS
all targets remain inside M2-VER-25 / 26 / 28 as appropriate
M2-VER-27 accepted S05 membership unchanged
M2-VER-29 / 31 / 32 not overclaimed
```

Do not make every future S06 test automatically part of one bundle merely by filename if that weakens explicit review-fix ownership. Preserve the existing primary bundle census while adding exact finding-to-target traceability.

---

# 6. Required focused verification

Run the smallest evidence first.

## 6.1 `S06-RF-01`

Run exact tests for:

```text
human selector -> exact resolved target in FORMATTED
204 direct success
nullable direct read
projection/direct mutation target identity
zero hidden GET
JSON unchanged
```

## 6.2 `S06-RF-02`

Run exact tests for:

```text
stable GET identity mismatches
exact-version identity mismatches
same-lineage/different-version cycle
multi-lineage/different-version cycle
complete-or-fail presentation
trace preservation
connection preservation
positive memoization/root traversal
```

## 6.3 Review-fix union

Run the exact `S06-RF-01` + `S06-RF-02` target registry and report:

```text
selector count
collected node count
pass count
duration
```

---

# 7. Mandatory regression gates

After focused evidence passes, run and report exact commands, counts and durations.

## 7.1 Dependency/build/static

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

No dependency or lock change is expected. If `uv.lock` changes, stop and explain why before publication.

## 7.2 CLI gates

Run:

```text
all M2-S06 tests
all M2-S05 tests
M2-VER-25 complete target set
M2-VER-26 complete target set
M2-VER-28 complete S05 + S06 target set
M2-VER-27 accepted S05 target set
all CLI import/negative-surface checks
all PTY/process tests on Linux
```

Explicitly verify:

```text
8 local commands
63 remote commands
65 examples
9 enrichment entry points
no hidden mutation/list enrichment
JSON primary-only presentation behavior
no direct kernel/database imports
no profile, credentials, insecure TLS or persistent history surface
```

## 7.3 Cross-boundary regressions

Run at minimum:

```text
Health/S04 affected regressions
API route and DTO inventories
M1/S00/M2 traceability
schema metadata and migrations
uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

The full suite must use the externally supplied real `TEST_DATABASE_URL` and include all PostgreSQL tests.

No normative test may be skipped, xfailed or hidden by generic rerun.

Report:

```text
CPython version
PostgreSQL version
uv version
prompt-toolkit version
collection count
focused finding counts
M2-VER-25 / 26 / 28 counts
S05 / S06 counts
PostgreSQL count
non-PostgreSQL count
full-suite count and duration
skip / xfail / rerun census
warning census
supported-path 40P01 / unexpected 40001 census
```

---

# 8. Unchanged-boundary verification

Explicitly verify and report:

```text
project version 0.1.0
no dependency or lock delta
15 authoritative tables
one Alembic base / one head
0001_m2_kernel unchanged
compare_metadata == []
no schema/migration/index diff
41 mutations + 22 business reads
1 Health route / 64 total public HTTP operations
63 CLI remote specs
14 / 16 / 13 / 14 / 5 / 1 family census
65 examples
83 scenarios / 21 predicates
no S07 runtime lock, release or Linux work
no PR or GitHub Action
```

---

# 9. Implementation and publication discipline

Work directly on `M2`.

Use normal source edits, tests, commits and push. Do not create a PR.

A reasonable publication sequence is:

```text
corrective implementation commit
    -> code + permanent review-fix evidence

corrected evidence/status commit
    -> exact commands/results and candidate state

optional provenance commit
    -> only if required to record the exact final remote-tested commit
```

Do not delete either S06 prompt while the slice remains open:

```text
docs/milestones/M2/wip/M2-S06-codex-prompt.md
docs/milestones/M2/wip/M2-S06-review-fixes-codex-prompt.md
```

Do not edit frozen contract, architecture or steps.

## 9.1 Status transitions

At corrective implementation start, `status.md` may record:

```text
M2-S06 — IN PROGRESS
```

while retaining both finding IDs and their bounded scope.

Only after both findings and every mandatory gate pass may Codex publish:

```text
M2-S06 — CANDIDATE READY FOR REVIEW
```

Codex must never assign:

```text
M2-S06 — COMPLETED
M2-S07 — READY or IN PROGRESS
```

Those remain reviewer-owned.

If the real PostgreSQL target or another mandatory requirement is unavailable:

```text
leave M2-S06 IN PROGRESS or BLOCKED as appropriate
record the exact blocker
publish only explicitly partial work
never claim candidate-ready
```

## 9.2 Final remote verification

After pushing the corrected candidate:

```text
verify local HEAD == origin/M2 == remote M2
verify ahead/behind 0/0
verify working tree clean
rerun the complete mandatory suite on the exact final remote commit
```

If the post-push rerun changes evidence or reveals a failure, publish the corrected state and repeat. Do not hand off an unverified provenance commit.

---

# 10. Required handoff

The final handoff must report:

```text
cycle / slice / branch
review-fix baseline 827c15cc...
corrective implementation commit(s)
corrected evidence/status commit
final remote HEAD
local/origin/remote synchronization
working-tree state
```

Report each finding separately:

```text
S06-RF-01
    implementation mechanism
    representative human-selector/bodyless/nullable/projection cases
    exact target visibility
    no-hidden-GET evidence
    permanent targets and result

S06-RF-02
    stable/exact identity correlation mechanism
    lineage-cycle mechanism
    mismatch/cycle failure behavior
    trace and connection preservation
    permanent targets and result
```

Report all exact quality and suite facts, unchanged boundaries and environment versions.

Explicitly state:

```text
M2-S06 is CANDIDATE READY FOR REVIEW, not COMPLETED
M2-S07 remains BLOCKED and not started
no architecture reopen was required
no PR or GitHub Action was created
```

If either finding remains open, a mandatory gate was not executed or the full real-PostgreSQL suite did not pass, do not use candidate-ready wording.