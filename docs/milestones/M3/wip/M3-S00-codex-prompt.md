# Codex implementation prompt — M3-S00

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the ratified technology baseline, and the operational authorization in `status.md`.

If this prompt conflicts with any owning authority, stop the affected work and report the conflict. Do not reinterpret a frozen decision to fit the current code or this execution aid.

## Assignment

Implement exactly:

```text
M3-S00 — Official CLI Location protocol correctness
```

Work directly on branch:

```text
M3
```

The human-authorized implementation baseline is:

```text
bbfdff45061c3411b3fdd535e4a401aada361b6e
Authorize M3-S00 implementation
```

The prompt-publication commit may be a later documentation-only descendant of that authorization commit. Work from the current `origin/M3`; do not reset the branch to the authorization commit. Confirm that the authorization commit remains in ancestry.

Current authorization is exactly:

```text
M3-S00    READY — AUTHORIZED
M3-S01    NOT AUTHORIZED / dependency blocked
M3-S02    NOT AUTHORIZED / dependency blocked
M3-S03    NOT AUTHORIZED / dependency blocked
M3-S04    NOT AUTHORIZED / dependency blocked
M3-S05    NOT AUTHORIZED / dependency blocked
M3-S06    NOT AUTHORIZED / dependency blocked
M3-S07    NOT AUTHORIZED / dependency blocked
```

Deliver the complete bounded S00 correction and permanent evidence for:

```text
M3-VER-01
M3-VER-02
M3-VER-03
```

Do not start `M3-S01`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not use GitHub Actions or another publication path as a substitute for ordinary repository implementation and verification.

---

# 1. Mandatory pre-flight

Before editing software, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
docs/architecture/cli.md
docs/architecture/verification.md

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
docs/milestones/M3/architecture/cli.md
docs/milestones/M3/architecture/verification.md
docs/milestones/M3/steps.md
docs/milestones/M3/status.md

docs/milestones/M3/wip/M3-S00-codex-prompt.md
```

Read the applicable ratified technology decisions, especially the testing/toolchain and official-CLI decisions in `docs/general/technology_baseline.md`.

The following M3 WIP material may be inspected as historical discovery/cross-check evidence only and must never override the frozen owners:

```text
docs/milestones/M3/wip/cli-post-create-decision.md
docs/milestones/M3/wip/cli-post-create-closure.md
```

Confirm from the repository before changing behavior:

```text
checked-out branch                    M3
origin/M3 ancestry                    includes bbfdff45061c3411b3fdd535e4a401aada361b6e
README active cycle                   M3
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
architecture/cli.md                   FINAL / FROZEN — ADP-07 CLOSED
architecture/verification.md          FINAL / FROZEN — ADP-08 CLOSED
steps.md                              FINAL / FROZEN
M3-S00                                READY or IN PROGRESS
M3-S01                                NOT AUTHORIZED
relevant contract/architecture reopen none
project version                       0.2.0
```

Inspect the current implementation and affected delivered regressions before choosing local decomposition. At minimum inspect:

```text
src/netauto/cli/model.py
src/netauto/cli/registry.py
src/netauto/cli/protocol.py
src/netauto/cli/execution.py
src/netauto/cli/main.py
src/netauto/cli/repl.py
src/netauto/cli/transport.py
src/netauto/cli/render.py

relevant neutral response DTOs under src/netauto/transport/http/

tests/test_m2_s05_registry.py
tests/test_m2_s05_http_client.py
tests/test_m2_s05_process.py
tests/test_m2_s05_review_fixes.py
tests/test_m2_s05_residual_review_fixes.py
tests/test_m2_s06_process.py
tests/test_m2_s06_review_fixes.py
and every directly related accepted CLI regression discovered in the repository
```

The current implementation is evidence, not authority. The known implementation shape includes three points that must be corrected according to ADP-07 rather than preserved accidentally:

```text
request_values.get(token)
    -> collapses exact-key absence and present-but-non-materializable values

isinstance(value, str | int)
    -> admits bool through Python's bool/int relationship unless bool is excluded explicitly

template.format_map(...)
    -> assigns Python-format semantics to dotted Location tokens
```

Do not treat those observations as the design. The frozen architecture below owns the required behavior.

Once pre-flight passes and implementation work actually begins, update `docs/milestones/M3/status.md` from `M3-S00 — READY` to `M3-S00 — IN PROGRESS`. Do not mark the slice `COMPLETED`.

If any mandatory pre-flight condition fails, stop before changing the affected behavior and report the mismatch.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
common CLI expected-Location materialization
closed Location-template token syntax
request-key presence precedence
response JSON-object path fallback
str / int(non-bool) token materialization
literal token replacement only
exact one-Location-header comparison
all eight registered 201 create operations
static registry Location DSL evidence
interactive and non-interactive create truthfulness
preservation of command-scoped HTTP exchange trace
permanent M3-VER-01..03 evidence
operational M3-S00 status/evidence updates required for candidate handoff
```

Expected production scope is principally:

```text
src/netauto/cli/protocol.py
src/netauto/cli/registry.py only if a minimal common/static boundary genuinely belongs there
shared CLI execution/trace code only if required to preserve the frozen common pipeline
```

Prefer the smallest implementation that completely realizes ADP-07. Do not add a command-specific fix for only the three nested cases.

## 2.2 Explicitly out of scope

Do not implement or expose any part of `M3-S01` or later slices, including:

```text
ObjectTemplate parent_template_id omitted/UUID/null changes
nullable selector/planner changes
cursor identity changes
GET/read projection rewrites
trusted lifecycle decoding changes
one-statement PostgreSQL read projection work
integrated M3-S06 traceability closure
M3 final acceptance or delivery
```

Also do not introduce:

```text
new business route or resource
new public DTO field or response flattening
new CLI command or grammar
new CLI error code
schema/table/index/constraint change
Alembic revision
runtime dependency
uv.lock change
project-version change
transport-policy redesign
renderer/enrichment redesign
Location normalization or URI repair
alternate Location guessing
hidden identity lookup
hidden post-mutation GET
retry/backoff behavior
cross-release compatibility behavior
```

Do not alter the eight existing `location_template` values to make the current implementation easier. They are frozen public-protocol metadata.

---

# 3. Exact ADP-07 Location DSL

A registered Location template is NETAUTO registry metadata, not Python formatting syntax.

The token grammar is exactly:

```text
{segment}
{segment.segment...}

segment = [a-z][a-z0-9_]*
```

Valid examples include:

```text
{id}
{version}
{datatype_id}
{datatype.id}
{object_template.id}
{relationship_definition.id}
```

Static registry evidence must reject at least these unsupported/malformed forms and the corresponding grammar classes:

```text
{}
{a..b}
{a[0]}
{a!r}
{a:b}
{{a}}
{a.}
{.a}
unbalanced braces
unsupported token characters
empty path segments
Python conversion/spec syntax
```

No arrays, wildcards, attribute lookup, conversion flags, format specifications or any other Python formatter behavior are supported.

Static validation proves syntax. Runtime materializability against canonical request/response carriers is separate evidence.

---

# 4. Token lookup and materialization semantics

For every token `T`, implement this exact precedence:

```text
1. if request_values contains exact key T
       select that exact request value
       do NOT inspect the response for T

2. otherwise
       resolve T as a dot-separated JSON-object path
       in the already validated canonical response body
```

Presence is authoritative. Do not use a lookup that collapses an absent key with a present key whose value is `None` or otherwise non-materializable.

Therefore:

```text
request_values contains T but selected value is non-materializable
    -> token is non-materializable
    -> do not fall back to response path T
```

Response fallback traverses dictionaries/JSON objects only:

```text
a.b.c -> response["a"]["b"]["c"]
```

Every intermediate segment must be an object containing the next segment. A missing segment or traversal through a non-object returns the non-materializable result; it must not escape as an ordinary local exception.

A token value is materializable only when it is:

```text
str
int, explicitly excluding bool
```

After the type check, inserted text is exactly `str(value)`.

These are non-materializable:

```text
None
bool
float
list
dict/object
```

Materialization is literal replacement only. Never call:

```text
str.format(...)
str.format_map(...)
or another formatter that gives dots/braces Python formatting semantics
```

Equivalent scan/replacement mechanics are free implementation choices if the frozen grammar and outcomes remain exact. Repeated occurrences of the same token use the same resolved scalar. Runtime data-driven failure returns a non-materializable result rather than throwing an ordinary exception.

---

# 5. Frozen eight-operation matrix

Preserve and exercise exactly these eight registered `201 Created` operations and templates:

```text
datatype create
    /api/v1/core/datatypes/{datatype.id}
    nested response path

datatype create-next
    /api/v1/core/datatypes/{datatype_id}/versions/{version}
    request datatype_id; version uses exact request key when present, otherwise response

object-template create
    /api/v1/core/object-templates/{object_template.id}
    nested response path

object-template create-next
    /api/v1/core/object-templates/{template_id}/versions/{version}
    request template_id; version uses exact request key when present, otherwise response

object create
    /api/v1/core/objects/{id}
    top-level response path

relationship-definition create
    /api/v1/core/relationship-definitions/{relationship_definition.id}
    nested response path

relationship-definition create-next
    /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
    request relationship_definition_id; version uses exact request key when present, otherwise response

relationship create
    /api/v1/core/relationships/{id}
    top-level response path
```

The census is exactly:

```text
8 registered 201 operations
3 nested response-token cases
5 remaining flat/request-token cases
```

Do not add or remove a registered operation and do not change the 63-operation CLI registry census.

---

# 6. Protocol outcome semantics

Preserve the common response-validation order:

```text
primary response observed
-> exact expected status validation
-> canonical response DTO validation
-> expected Location materialization
-> exact actual Location validation
-> success or structured protocol failure
```

Do not weaken the existing same-release status/body validation to obtain green create outcomes.

For a registered Location template:

```text
actual Location header count == 1
AND expected Location is materializable
AND actual Location == expected Location exactly
    -> success
```

All of these remain:

```text
Location missing                     -> cli_protocol_error
Location repeated                    -> cli_protocol_error
Location mismatches expected         -> cli_protocol_error
expected token absent                -> cli_protocol_error
invalid response-object traversal    -> cli_protocol_error
expected token non-materializable    -> cli_protocol_error
```

A valid canonical `201 Created` response with exact Location must never become `cli_internal_error` solely because of expected-Location processing.

Do not normalize the actual Location and do not add:

```text
case folding
trailing-slash repair
percent-encoding repair
URI canonicalization
alternate-field guessing
hidden post-create GET
```

The primary successful mutation exchange must remain the truthful structured trace. Mutation success continues to perform no presentation-enrichment GET.

---

# 7. Implementation discipline

The correction is common protocol infrastructure.

Required properties:

```text
one common materializer for all eight creates
closed token grammar
exact request-key presence precedence
object-path response fallback
str/int(non-bool) carrier rule
literal replacement
no Python format semantics
non-materializable runtime data -> protocol outcome, not uncaught local exception
exact one-header equality
```

Do not special-case operation names such as `datatype create`, `object-template create` or `relationship-definition create`.

Do not change `_wire_string()` or introduce the M3-S01 nullable-query behavior as part of this slice.

A narrowly scoped helper or internal sentinel is an implementation choice. Avoid speculative abstractions for future template languages.

For static Location metadata validation, establish permanent T10 evidence for the exact current registry and malformed grammar classes. Do not invent a new public runtime error contract or unrelated import-time behavior merely to satisfy a static test.

Preserve:

```text
HTTP-only CLI authority
63 remote commands
8 local commands
same command grammar
selector semantics
transport policy
result/error shape
ExecutionLedger truthfulness
interactive/non-interactive shared execution pipeline
all eight current Location templates
mutation no-enrichment behavior
```

---

# 8. Required M3 evidence

Create permanent implementation evidence for all three primary bundles. A dedicated test module such as:

```text
tests/test_m3_s00_cli_location.py
```

is acceptable, but exact file/helper decomposition is implementation-local.

Do not merely rename old tests. Add evidence that proves the new frozen rules and retain affected delivered regressions.

## M3-VER-01 — Eight-operation create success

Layers: `T8 + T10`.

Prove exactly:

```text
all 8 registered 201 operations have one non-null Location template
all 8 current templates pass the closed DSL syntax check
all 8 canonical response/request carrier combinations materialize expected Location
all 8 canonical exact Location responses produce CLI success
all 3 nested response-token templates are explicit test cases
all 5 flat/request-token cases remain covered
valid nested-token success never raises
valid nested-token success never yields cli_internal_error
```

Maintain a machine-checkable exact `M3_CLI_201_CENSUS` or equivalent permanent exact-set evidence for these eight operations. Do not use `>= 8` or another minimum-count assertion.

## M3-VER-02 — Exact Location protocol failures

Layers: `T8 + T10`.

Prove exactly:

```text
missing actual Location             -> cli_protocol_error
repeated actual Location            -> cli_protocol_error
mismatching actual Location         -> cli_protocol_error
unresolvable expected token         -> cli_protocol_error
non-materializable request token    -> cli_protocol_error and no response fallback
non-materializable response token   -> cli_protocol_error
bool token                           -> non-materializable
float/list/dict/None token           -> non-materializable as applicable
malformed DSL classes               -> rejected by static evidence
request-key precedence              -> independently demonstrated
request-key presence                -> distinguished from request-key absence
no Python format/format_map semantics for dotted tokens
```

Include a regression that would fail if dotted tokens were passed to Python `format`/`format_map`.

## M3-VER-03 — Interactive/non-interactive truthfulness

Layer: `T8`.

Prove at least one canonical nested-identity create through both modes:

```text
non-interactive execution -> success
interactive execution     -> success
```

Also prove:

```text
both paths use the same parser/execution/protocol behavior
primary successful HTTP exchange remains in the structured trace
no hidden post-mutation GET is issued
interactive formatted success does not perform mutation enrichment
```

Use controlled HTTPX transport/test boundaries already established by the CLI rather than application/persistence access.

M3-S00 owns only `M3-VER-01..03`. Do not claim `M3-VER-04..19` PASS. If you introduce or extend an incremental machine-checkable M3 traceability registry, preserve all frozen stable identifiers and make only currently implemented targets truthful; do not fabricate future concrete targets or PASS states.

---

# 9. Regression and non-drift obligations

At minimum preserve and re-execute the directly affected delivered CLI regression families, including the repository's current equivalents of:

```text
tests/test_m2_s05_registry.py
tests/test_m2_s05_http_client.py
tests/test_m2_s05_process.py
tests/test_m2_s05_review_fixes.py
tests/test_m2_s05_residual_review_fixes.py
tests/test_m2_s06_process.py
tests/test_m2_s06_review_fixes.py
```

Discover and include any additional current CLI protocol/registry/interactive tests affected by the actual diff.

Non-drift requirements are exact:

```text
CLI remote registry                 63 unchanged
registered 201 operations            8 unchanged
registered Location templates        8 unchanged
project version                     0.2.0 unchanged
runtime dependency set              unchanged
uv.lock                              unchanged
schema/migrations                    unchanged
business routes/resources            unchanged
public DTO shapes                    unchanged
```

The slice itself is T8/T10. `M3-VER-01..03` do not require PostgreSQL. Absence of `TEST_DATABASE_URL` is therefore not a blocker for the mandatory M3-S00 evidence and must not be used to avoid executing it.

Do not provision PostgreSQL, invent credentials, use SQLite, Docker or Testcontainers as a substitute for any PostgreSQL-required project evidence. If broader optional verification reaches PostgreSQL-required tests without `TEST_DATABASE_URL`, report those separately and do not claim them PASS.

---

# 10. Verification commands and candidate gate

Run focused evidence first, then affected regressions and the repository-wide non-PostgreSQL/static gates.

Use the repository's locked toolchain. At minimum execute and report exact results for:

```text
uv lock --check
uv sync --locked

uv run pytest -q <M3-S00 focused targets>
uv run pytest -q <directly affected delivered CLI regression targets>

uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
uv run pytest -q -m "not postgresql"
```

Also run:

```text
uv build
```

as a non-drift build check unless an actual repository/environment failure prevents it; report any such failure exactly rather than silently dropping the gate.

Requirements:

```text
M3-VER-01..03 normative skip    0
M3-VER-01..03 xfail            0
M3-VER-01..03 rerun            0
new unexplained warning         0
Ruff                            PASS
Pyright strict                  PASS
all affected delivered CLI      PASS
```

Do not weaken, deselect, skip, xfail or retry a failing normative target to finish the task.

Verify no forbidden delta. At minimum inspect the candidate diff against the authorization baseline/current prompt-publication head and prove that the implementation has not changed:

```text
pyproject.toml dependency/version meaning
uv.lock
src/netauto/migrations/
public API route/DTO contracts
```

If an unexpected schema, migration, dependency, lockfile, route or public-contract change appears necessary, STOP. It is outside M3-S00 and requires the applicable architecture/contract process.

---

# 11. Status, evidence, commit and push

When implementation actually starts:

```text
M3-S00 READY -> M3-S00 IN PROGRESS
```

This is an implementer-owned operational progress transition. Keep later slices not authorized.

During implementation:

```text
frozen contract/architecture/steps remain unchanged in meaning
WIP prompt remains non-normative
implementation findings are classified under AGENTS.md
architecture gap/contradiction -> STOP and report
implementation defect -> correct code and add regression evidence
```

When, and only when, all mandatory M3-S00 evidence and affected gates pass, the implementer may update operational status to:

```text
M3-S00 — CANDIDATE READY FOR REVIEW
```

and record concrete evidence under the cycle's evidence owner if needed. Do not assign:

```text
M3-S00 COMPLETED
M3-S01 READY
M3 DELIVERED
ACCEPTED
```

Those are reviewer/human-owned transitions.

Commit and push the complete candidate to branch `M3`. Do not create a PR.

Before handoff verify, rather than assume:

```text
working tree clean
local branch M3
local HEAD commit
origin/M3 commit
remote branch M3 commit
local HEAD == origin/M3 == remote M3
```

Do not report a clean tree, push or remote synchronization that was not actually verified.

If a mandatory S00 gate fails, leave the slice `IN PROGRESS` or accurately blocked as appropriate and report the exact failure. Do not publish a `CANDIDATE READY FOR REVIEW` state merely because the code change is present.

The execution aid remains under `wip/` while the slice is active. After reviewer acceptance, governance may remove the concluded prompt from the working tree; do not remove it merely to make the candidate look cleaner.

---

# 12. Required final handoff

Report verified facts only. Include:

```text
cycle                         M3
slice                         M3-S00
branch                        M3
authorized baseline           bbfdff45061c3411b3fdd535e4a401aada361b6e
candidate commit              <exact SHA>
push/remote sync              <verified state>
working tree                  <verified state>

implemented scope             <concise exact description>
changed files                 <exact list/categories>
schema/migration changes      none expected; report actual fact
dependency/lock changes       none expected; report actual fact
public route/DTO changes      none expected; report actual fact

M3-VER-01                     <targets + result>
M3-VER-02                     <targets + result>
M3-VER-03                     <targets + result>

verification commands         <exact commands actually run>
results                       <exact pass/fail/collection counts>
Python/tool versions          <when material>
warnings/skips/xfails/reruns  <exact census for executed gates>
verification not executed     <what and why>
known limitations/risks       <verified residuals only>
architecture/documentation findings <none or exact finding>
```

Use handoff wording such as:

```text
M3-S00 candidate implemented and ready for reviewer inspection.
```

Do not state that `M3-S00` is `COMPLETED`. Do not start `M3-S01`.