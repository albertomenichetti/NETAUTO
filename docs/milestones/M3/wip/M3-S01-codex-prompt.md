# Codex implementation prompt — M3-S01

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the ratified technology baseline, and the operational authorization in `status.md`.

If this prompt conflicts with any owning authority, stop the affected work and report the conflict. Do not reinterpret a frozen decision to fit current code or this execution aid.

## Assignment

Implement exactly:

```text
M3-S01 — ObjectTemplate parent tri-state across HTTP, CLI and cursor identity
```

Work directly on branch:

```text
M3
```

The human-authorized implementation baseline is:

```text
ecbd1b20e33b02f1612f12344b4270cdcd044fa6
Authorize M3-S01 implementation
```

The prompt-publication commit will be a later documentation-only descendant of that authorization commit. Work from the current `origin/M3`; do not reset the branch to the authorization commit. Confirm that the authorization commit remains in ancestry.

Current authorization is exactly:

```text
M3-S00    reviewer-owned COMPLETED
M3-S01    READY — AUTHORIZED
M3-S02    NOT AUTHORIZED / dependency blocked
M3-S03    NOT AUTHORIZED / dependency blocked
M3-S04    NOT AUTHORIZED / dependency blocked
M3-S05    NOT AUTHORIZED / dependency blocked
M3-S06    NOT AUTHORIZED / dependency blocked
M3-S07    NOT AUTHORIZED / dependency blocked
```

Deliver the complete bounded S01 capability and permanent evidence for:

```text
M3-VER-14
M3-VER-15
M3-VER-16
```

Do not start `M3-S02`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not use GitHub Actions or another publication path as a substitute for ordinary repository implementation and verification.

---

# 1. Mandatory pre-flight

Before editing software, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
docs/architecture/api.md
docs/architecture/cli.md
docs/architecture/verification.md

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/cli.md
docs/milestones/M3/architecture/verification.md
docs/milestones/M3/steps.md
docs/milestones/M3/status.md

docs/milestones/M3/wip/M3-S01-codex-prompt.md
```

Read every applicable ratified `STACK-*` decision, especially the FastAPI/Pydantic transport boundary, explicit application composition, testing/toolchain and official-CLI decisions in `docs/general/technology_baseline.md`.

Historical M3 WIP documents may be inspected only as discovery/cross-check evidence. They never override the frozen M3 contract or architecture owners.

Confirm from the repository before changing behavior:

```text
checked-out branch                    M3
origin/M3 ancestry                    includes ecbd1b20e33b02f1612f12344b4270cdcd044fa6
README active cycle                   M3
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
architecture/api.md                   FINAL / FROZEN — ADP-04 / ADP-05 CLOSED
architecture/cli.md                   FINAL / FROZEN — ADP-06 / ADP-07 CLOSED
architecture/verification.md          FINAL / FROZEN — ADP-08 CLOSED
steps.md                              FINAL / FROZEN
M3-S00                                reviewer-owned COMPLETED
M3-S01                                READY or IN PROGRESS
M3-S02                                NOT AUTHORIZED
relevant contract/architecture reopen none
project version                       0.2.0
```

Inspect the current realization before choosing local decomposition. At minimum inspect:

```text
src/netauto/entrypoints/api/common.py
src/netauto/entrypoints/api/objecttemplates.py
src/netauto/application/cursors.py
src/netauto/application/objecttemplates.py
src/netauto/persistence/objecttemplates.py

src/netauto/cli/model.py
src/netauto/cli/registry.py
src/netauto/cli/parser.py
src/netauto/cli/selectors.py
src/netauto/cli/execution.py
src/netauto/cli/protocol.py
src/netauto/cli/main.py
src/netauto/cli/repl.py

relevant ObjectTemplate HTTP DTOs under src/netauto/transport/http/

existing ObjectTemplate API/cursor tests
existing CLI parser/selector/request-planning/interactive tests
tests/test_m3_s00_cli_location.py
and every directly affected accepted regression discovered in the repository
```

The current implementation is evidence, not authority. It already contains important pieces that must be preserved rather than redesigned:

```text
HTTP adapter
    -> already computes parent_filter_set from raw query-key presence
    -> current parent_template_id typing is UUID | None and therefore lacks exact lexical null

application ObjectTemplate list
    -> already accepts parent_template_id + parent_filter_set
    -> already includes both values in object_templates cursor filters

persistence ObjectTemplate list
    -> already applies parent_template_id comparison only when parent_filter_set=True
    -> parent_filter_set=True + parent_template_id=None already realizes SQL IS NULL semantics

cursor codec
    -> already stores v=1 / route / filters / key
    -> exact filter equality already distinguishes presence-bit states

CLI parser
    -> already parses raw "null" to None only when ParameterSpec.nullable=True

CLI registry
    -> object-template list parent_template_id is selector-capable but currently not nullable

CLI selector planner
    -> currently creates a selector target for every present selector-capable direct parameter
    -> therefore explicit None would incorrectly enter selector validation unless generalized

CLI request planner
    -> _wire_string() intentionally does not accept None
    -> QUERY explicit-null handling must therefore be location-aware, not a global scalar broadening
```

Do not treat those observations as new design. ADP-04, ADP-05 and ADP-06 below own the required behavior.

Once pre-flight passes and implementation work actually begins, update `docs/milestones/M3/status.md` from `M3-S01 — READY` to `M3-S01 — IN PROGRESS`. Do not mark the slice `COMPLETED`.

If any mandatory pre-flight condition fails, stop before changing the affected behavior and report the mismatch.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
ObjectTemplate list HTTP parent_template_id lexical tri-state
exact lowercase null HTTP carrier
internal parent_filter_set presence preservation
ObjectTemplate list cursor identity for omitted/root/exact-parent states
CLI object-template list parent_template_id nullability
metadata-driven nullable direct-selector handling
location-aware nullable QUERY request planning
CLI explicit-null zero-selector-discovery behavior
interactive/non-interactive CLI carrier equivalence
permanent M3-VER-14..16 evidence
operational M3-S01 status/evidence updates required for candidate handoff
```

Expected production scope is limited principally to:

```text
src/netauto/entrypoints/api/objecttemplates.py
src/netauto/application/objecttemplates.py only if a minimal correction is actually required
src/netauto/application/cursors.py only if required by existing cursor helper ownership
src/netauto/cli/registry.py
src/netauto/cli/parser.py only if needed while preserving its existing generic null rule
src/netauto/cli/selectors.py
src/netauto/cli/execution.py
relevant HTTP/CLI/cursor tests
```

Persistence already owns the required tri-state. Do not change `src/netauto/persistence/objecttemplates.py` unless repository evidence exposes a contradiction with frozen architecture; such a contradiction is a STOP/review item, not permission to redesign persistence.

## 2.2 Explicitly out of scope

Do not implement or expose any part of `M3-S02` or later slices, including:

```text
DataType trusted one-statement read projection work
ObjectTemplate trusted recursive/aggregate read rewrite
Object read projection rewrite
components/Relationship cursor path-target repairs owned by S04
trusted lifecycle decoding changes
integrated 22-route M3 read closure
final M3 acceptance or delivery
```

Also do not introduce:

```text
new business route or resource
new public DTO field
new public parent_filter_set parameter/field
second parent/root filter parameter
alternate root sentinel
new CLI command or grammar
new CLI error code
cursor codec/version change
schema/table/index/constraint change
Alembic revision
runtime dependency
uv.lock semantic change
project-version change
persistence redesign
new selector endpoint
transport-policy redesign
renderer/enrichment redesign
hidden GET
retry/backoff behavior
cross-release compatibility behavior
```

Preserve the completed M3-S00 Location behavior and `M3-VER-01..03` evidence unchanged.

---

# 3. Exact HTTP parent tri-state — ADP-05

The only public HTTP parent filter remains:

```text
parent_template_id
```

Its exact lexical semantics are:

```text
parameter omitted
    -> parent_template_id = None
    -> parent_filter_set  = False
    -> no parent predicate

parent_template_id=<valid UUID>
    -> parent_template_id = UUID
    -> parent_filter_set  = True
    -> direct children of that stable parent

parent_template_id=null
    -> parent_template_id = None
    -> parent_filter_set  = True
    -> root ObjectTemplates only
```

The root sentinel is exact lowercase ASCII text:

```text
null
```

Reject through the delivered `400 invalid_request` boundary:

```text
parent_template_id=
parent_template_id=NULL
parent_template_id=None
parent_template_id=root
parent_template_id=ROOT
malformed UUID
repeated parent_template_id
```

Do not trim whitespace, case-fold or normalize another sentinel into `null`.

## 3.1 Nullable UUID HTTP adapter

Implement the smallest local typed carrier consistent with the frozen architecture:

```text
raw value == "null"
    -> Python None

otherwise
    -> delegate unchanged to the delivered FastAPI/Pydantic UUID parser
```

A `BeforeValidator`-style helper is explicitly permitted; helper naming is implementation-local.

Do not implement a custom UUID parser. Non-null UUID lexical behavior must remain the delivered behavior.

The route already derives the presence bit from raw query membership. Preserve that distinction:

```text
"parent_template_id" not in request.query_params
    !=
"parent_template_id" present with parsed value None
```

Strict `validate_query()` behavior remains authoritative and must continue rejecting repeated/unknown query keys.

## 3.2 Public-surface prohibition

`parent_filter_set` is internal only. It must not appear in:

```text
public query parameters
OpenAPI public query schema
request body DTOs
response DTOs
CLI parameter inventory
structured CLI command intent
```

Static/public-boundary evidence must make this absence permanent.

---

# 4. Cursor identity — ADP-04 / M3-VER-16

Preserve the existing opaque cursor payload and codec version:

```text
v = 1
route
filters
key
```

No `application/cursors.py` codec redesign or version bump is authorized.

For `GET /api/v1/core/object-templates`, canonical semantic filters are exactly:

```text
namespace
name
abstract
parent_template_id
parent_filter_set
```

The three parent states must materialize in cursor filters as:

```text
omitted
    parent_template_id = None
    parent_filter_set  = False

root-only
    parent_template_id = None
    parent_filter_set  = True

exact parent A
    parent_template_id = str(A)
    parent_filter_set  = True
```

Therefore permanent public behavior must prove:

```text
omitted cursor used under root-only       -> 400 invalid_cursor
root-only cursor used under omitted       -> 400 invalid_cursor
root-only cursor continues root-only      -> success
exact parent A cursor under parent B       -> 400 invalid_cursor
exact parent cursor under root-only        -> 400 invalid_cursor
root-only cursor under exact parent        -> 400 invalid_cursor
```

Preserve canonical keyset position:

```text
(namespace, name)
```

Do not put `limit` into semantic cursor identity. Changing `limit` alone must remain compatible under the delivered cursor contract.

Do not expose cursor internals publicly merely to test them; public behavioral evidence is primary. Lower-layer inspection of filters is allowed as supplementary evidence.

---

# 5. Exact CLI parent tri-state — ADP-06

The canonical remote grammar remains unchanged:

```text
<resource> <operation> [selector] [parameter=value ...]
```

For exactly the existing `object-template list` parameter:

```text
name         parent_template_id
kind         STRING
location     QUERY
selector     OBJECT_TEMPLATE
nullable     true
```

Do not change the kind to UUID: non-null values must continue accepting both UUID and delivered human ObjectTemplate selectors `<namespace>.<name>`.

Do not make unrelated selector-capable parameters nullable.

Required CLI states:

```text
object-template list
    -> parent key absent from ParsedCommand.parameters
    -> zero parent selector lookup
    -> no parent_template_id query pair

object-template list parent_template_id=<UUID>
    -> exact-ID selector precedence
    -> zero discovery GET
    -> canonical UUID query pair

object-template list parent_template_id=<namespace>.<name>
    -> normal bounded ObjectTemplate discovery
    -> one selector GET when not already memoized
    -> exactly one match => UUID query pair
    -> zero/multiple retain delivered selector errors

object-template list parent_template_id=null
    -> ParsedCommand.parameters contains key with value None
    -> zero selector-discovery GETs for that value
    -> primary request query contains exact pair parent_template_id=null
```

Explicit null must remain distinct from omission in parsed intent and in the actual HTTP query trace.

---

# 6. Generic nullable direct-selector rule

Fix the selector planner generically at the metadata boundary. Do not special-case the string `parent_template_id`.

For a direct selector-capable `ParameterSpec`:

```text
parameter absent
    -> no selector target

parameter present + non-null value
    -> existing selector target and lookup behavior

parameter present + value None + nullable=True
    -> terminal explicit-null carrier
    -> no selector target
    -> value remains None

parameter present + value None + nullable=False
    -> invalid parsed/registry state
```

The normal parser should already prevent user-reachable non-nullable explicit null. Preserve that bounded local `cli_invalid_parameter` behavior.

Do not invent nullable semantics for nested selectors. `NestedSelector` metadata has no nullable bit; S01 does not broaden that surface.

Preserve:

```text
UUID exact-ID precedence
human selector zero/one/many behavior
selector memoization
selector error catalogue
selector exchange ordering
resolved identity behavior for non-null selectors
```

---

# 7. Location-aware request planning for None

Do not change the global scalar serializer into:

```text
_wire_string(None) -> "null"
```

That is explicitly forbidden by ADP-06.

Request planning must interpret `None` using both `ParameterSpec.nullable` and `ParameterLocation`:

```text
parameter omitted
    -> omit carrier

QUERY + None + nullable=True
    -> append (parameter.name, "null")

QUERY + None + nullable=False
    -> cli_invalid_parameter / invalid plan

BODY + None + nullable=True
    -> preserve None in body candidate
    -> DTO validation/serialization emits JSON null where allowed

BODY + None + nullable=False
    -> existing DTO/local invalid-parameter boundary

PATH + None
    -> invalid/impossible valid plan
    -> cli_invalid_parameter if caller-reachable
```

This rule should be metadata-driven and generic. Do not special-case ObjectTemplate parameter names.

Permanent regression must prove at least:

```text
nullable QUERY explicit null emits lexical "null"
nullable BODY null remains JSON null, not string "null"
PATH None remains invalid
_wire_string itself has no None branch/global null behavior
```

---

# 8. M3-VER-14 — ObjectTemplate HTTP parent tri-state

Primary layer: `T4`.

Permanent evidence must prove all frozen cases:

```text
omitted parent_template_id
    -> no parent predicate
    -> roots and children can both appear subject to other filters

valid UUID parent_template_id
    -> direct children only

exact lowercase parent_template_id=null
    -> roots only

empty
uppercase/special sentinels
malformed UUID
repeated parent_template_id
    -> 400 invalid_request

parent_filter_set
    -> absent from public query/DTO/OpenAPI surface
```

Use the established public HTTP/ASGI verification boundary. The existing ObjectTemplate API integration harness is real-PostgreSQL-backed; do not replace public behavior evidence with a direct function call, fake persistence substitute or SQLite.

Where test setup needs a root, children and another root/parent, create deterministic isolated semantic identities through public API or established fixtures. Do not rely on ordering accidents from unrelated test data.

---

# 9. M3-VER-15 — ObjectTemplate CLI parent tri-state

Primary layer: `T8`.

Permanent evidence must prove:

```text
omitted
    -> no selector lookup
    -> no parent query pair

UUID
    -> canonical UUID query pair
    -> no discovery GET

human selector
    -> normal bounded discovery
    -> resolved UUID query pair

explicit null
    -> parsed None
    -> zero selector-discovery GET
    -> literal parent_template_id=null query pair

explicit null on a non-nullable parameter
    -> cli_invalid_parameter

nullable BODY null
    -> JSON null regression

PATH None
    -> invalid/impossible

_wire_string(None)
    -> not introduced

interactive/non-interactive
    -> same carrier semantics
```

For interactive mode, account only for the explicit `/connect` Health exchange before clearing/isolating the command-under-test trace. The target `object-template list parent_template_id=null` command itself must perform no selector discovery and exactly one primary ObjectTemplate-list exchange.

The actual structured HTTP trace must show:

```text
query.parent_template_id == ["null"]
```

for explicit null, and no `parent_template_id` entry for omission.

---

# 10. M3-VER-16 — Parent-filter cursor identity

Primary layer: `T4`.

Use true multipage public behavior for the root-only continuation case; do not prove continuation only by hand-calling `encode_cursor()` / `decode_cursor()`.

Required evidence:

```text
root-only request with enough roots for next_cursor
    -> first page succeeds
    -> continuation with same root-only identity succeeds

cursor from omitted request reused under root-only
    -> 400 invalid_cursor

cursor from root-only reused under omitted
    -> 400 invalid_cursor

cursor from parent A reused under parent B
    -> 400 invalid_cursor

root-only and exact-parent cursor reuse in either direction
    -> 400 invalid_cursor
```

Also preserve the delivered rule:

```text
same semantic identity + changed limit only
    -> accepted
```

Do not change position-key shape or public ordering to make tests convenient.

---

# 11. Preservation and regression obligations

Preserve exactly outside the frozen S01 delta:

```text
M3-S00 Location correction and M3-VER-01..03
63-operation business HTTP surface
63-operation CLI remote registry census
8 local CLI commands
existing CLI grammar
non-null selector behavior
strict unknown/repeated HTTP query handling
ObjectTemplate list ordering and limit semantics
ObjectTemplate persistence parent filtering
cursor codec v1
other route cursor identities
public DTO shapes
public error catalogue
HTTP-only CLI import boundary
transport and exchange-ledger semantics
FORMATTED/JSON rendering behavior
schema and Alembic baseline
runtime dependency set
uv.lock
project version 0.2.0
```

At minimum re-execute directly affected accepted regressions in the repository's current equivalents of:

```text
tests/test_objecttemplate_api.py
ObjectTemplate list/application/persistence cursor tests
CLI registry/parser/selector/request-planning tests
CLI interactive/non-interactive tests
tests/test_m3_s00_cli_location.py
```

Discover and include every additional regression actually touched by the diff. Do not assume this list is exhaustive.

Do not weaken, deselect, skip, xfail or retry a failing normative target merely to finish the slice.

---

# 12. PostgreSQL and verification environment

M3-S01 primary evidence contains public HTTP `T4` behavior for `M3-VER-14` and `M3-VER-16` plus CLI `T8` behavior for `M3-VER-15`.

The repository's established ObjectTemplate public API harness is real-PostgreSQL-backed. Therefore the candidate must have the externally supplied real PostgreSQL test target required by the concrete mandatory T4 targets.

```text
TEST_DATABASE_URL available
    -> run required focused public HTTP/cursor evidence against it

TEST_DATABASE_URL unavailable
    -> mandatory T4 evidence is BLOCKED
    -> M3-S01 cannot be reported CANDIDATE READY FOR REVIEW
```

Do not:

```text
invent credentials
fall back to localhost
provision Docker/Testcontainers
substitute SQLite
replace public HTTP evidence with persistence-only tests
claim BLOCKED evidence as PASS
```

Report PostgreSQL server/version metadata when mandatory PostgreSQL-backed tests are executed.

---

# 13. Verification commands and candidate gate

Run focused evidence first, then affected regressions, then repository-wide gates.

Use the repository's locked toolchain. At minimum execute and report exact results for:

```text
uv lock --check
uv sync --locked

uv run pytest -q <M3-S01 M3-VER-14..16 focused targets>
uv run pytest -q <directly affected HTTP/CLI/cursor regression targets>
uv run pytest -q tests/test_m3_s00_cli_location.py

uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
uv run pytest -q -m "not postgresql"

uv build
```

Because S01 requires the real-PostgreSQL-backed public HTTP/cursor evidence, also execute the required focused PostgreSQL targets with `TEST_DATABASE_URL`, and after focused evidence is green run the complete repository suite on the same candidate environment:

```text
uv run pytest -q
```

If the repository test policy or environment requires serial execution for interfering PostgreSQL tests, follow the established repository harness rather than adding unsafe parallelism.

Candidate requirements:

```text
M3-VER-14                         PASS
M3-VER-15                         PASS
M3-VER-16                         PASS
normative skip / xfail / rerun    0 / 0 / 0
S00 regression                    PASS
all affected HTTP/CLI/cursor      PASS
Ruff format                       PASS
Ruff lint                         PASS
Pyright strict                    PASS
locked environment                PASS
build                             PASS
full repository suite             PASS
new unexplained warnings          0
```

A previously reviewed/censused third-party deprecation warning may be reported as such; do not suppress it merely to obtain a cosmetic zero-warning result.

Verify no forbidden delta. Inspect the candidate diff against the prompt-publication head and prove that implementation has not changed:

```text
pyproject.toml dependency/version meaning
uv.lock
src/netauto/migrations/
public route inventory
public DTO field inventory
cursor codec payload version
```

If schema, migration, dependency, lockfile, new route/DTO surface, persistence redesign or cursor-version change appears necessary, STOP. It is outside M3-S01 and requires the applicable frozen-authority process.

---

# 14. Status, evidence, commit and push

When implementation actually starts:

```text
M3-S01 READY -> M3-S01 IN PROGRESS
```

Keep:

```text
M3-S00 COMPLETED
M3-S02 .. M3-S07 NOT AUTHORIZED
```

During implementation:

```text
frozen contract/architecture/steps remain unchanged in meaning
WIP prompt remains non-normative
implementation finding -> correct code + permanent regression evidence
architecture gap/contradiction -> STOP and report; do not choose semantics in code
```

When, and only when, all mandatory M3-S01 evidence and candidate gates pass, the implementer may update operational status to:

```text
M3-S01 — CANDIDATE READY FOR REVIEW
```

and record concrete evidence under the cycle's evidence owner if needed.

Do not assign:

```text
M3-S01 COMPLETED
M3-S02 READY
M3 DELIVERED
ACCEPTED
```

Those are reviewer/human-owned transitions.

Commit and push the complete candidate to branch `M3`. Do not create a PR.

Do not remove this S01 execution aid yourself merely because the candidate is ready. Project governance removes/supersedes the active aid after reviewer acceptance or replacement.

Before handoff verify, rather than assume:

```text
working tree clean
local branch M3
local HEAD commit
origin/M3 commit
remote branch M3 commit
local HEAD == origin/M3 == remote M3
```

Do not report a test, database version, clean tree, push or remote synchronization that was not actually verified.

---

# 15. Required candidate handoff

Report verified facts only. Include:

```text
cycle / slice
branch
authorization baseline
prompt-publication baseline
candidate commit SHA
push / remote synchronization status
working-tree status
PR status

implemented HTTP carrier changes
implemented CLI carrier changes
cursor-identity disposition
changed files
explicitly unchanged application/persistence/cursor-codec areas
schema / migration changes
dependency / lockfile changes
route / DTO changes

M3-VER-14 exact commands/results
M3-VER-15 exact commands/results
M3-VER-16 exact commands/results
focused affected regressions
M3-S00 regression result
Ruff / Pyright / collection
non-PostgreSQL suite
mandatory PostgreSQL targets + PostgreSQL version
full repository suite
build
lock check/sync
warnings

verification not executed and exact reason
known limitations or residual risks
architecture/documentation findings
explicitly deferred/out-of-scope behavior
```

Use the reviewer-safe wording:

```text
M3-S01 candidate implemented and ready for reviewer inspection
```

Never claim `M3-S01 COMPLETED` yourself.

---

# Final implementation checklist

Before publication, confirm all are true:

```text
[ ] branch M3 and current origin/M3 verified
[ ] M3-S00 reviewer-owned COMPLETED
[ ] M3-S01 authorized and no later slice authorized
[ ] contract / architecture / steps still FINAL/FROZEN
[ ] HTTP omission / UUID / exact lowercase null semantics exact
[ ] invalid HTTP lexical carriers -> 400 invalid_request
[ ] repeated parent_template_id -> 400 invalid_request
[ ] parent_filter_set remains internal only
[ ] CLI registry changes only ObjectTemplate list parent parameter nullability
[ ] CLI explicit null parses to None without selector discovery
[ ] nullable direct-selector handling is generic and metadata-driven
[ ] explicit null emits exact QUERY carrier parent_template_id=null
[ ] nullable BODY null remains JSON null
[ ] PATH None remains invalid
[ ] no global _wire_string(None) behavior
[ ] omitted/root/exact-parent cursor identities are distinct
[ ] root-only true multipage continuation succeeds
[ ] parent A cursor rejected under parent B
[ ] limit remains excluded from cursor identity
[ ] cursor codec remains v1 unchanged
[ ] persistence tri-state behavior unchanged
[ ] no new route/resource/DTO/error code
[ ] no schema/migration/dependency/lockfile/version change
[ ] M3-VER-14 PASS
[ ] M3-VER-15 PASS
[ ] M3-VER-16 PASS
[ ] M3-S00 regression PASS
[ ] affected HTTP/CLI/cursor regressions PASS
[ ] Ruff format/check PASS
[ ] Pyright strict PASS
[ ] collection PASS
[ ] non-PostgreSQL suite PASS
[ ] mandatory PostgreSQL evidence PASS
[ ] full repository suite PASS
[ ] build PASS
[ ] skip/xfail/rerun normative census 0/0/0
[ ] status is CANDIDATE READY FOR REVIEW, never COMPLETED
[ ] M3-S02 remains NOT AUTHORIZED
[ ] committed and pushed to M3
[ ] local HEAD == origin/M3 == remote M3
[ ] working tree clean
```
