# Codex implementation prompt — M2-S06

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Implement exactly:

```text
M2-S06 — Official CLI interactive REPL and formatted experience
```

Work directly on branch:

```text
M2
```

The reviewer-owned starting baseline is:

```text
e1f11b8bf655079ed7c8aff99b56c2b2e4d17c03
docs(m2): accept S05 and open S06
```

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    reviewer-owned COMPLETED
M2-S04    reviewer-owned COMPLETED
M2-S05    reviewer-owned COMPLETED
M2-S06    READY
M2-S07    BLOCKED
```

Deliver the complete vertically coherent S06 capability:

```text
prompt_toolkit runtime dependency and asynchronous terminal integration
exact no-argument `netauto` interactive mode
initial DISCONNECTED / FORMATTED / empty process-local history
one explicit interactive session state machine
one endpoint-scoped reusable HTTPX client
command-scoped selector cache and truthful exchange ledger
exact eight-command local inventory
Health-backed /connect and /status behavior
remote commands through the completed S05 registry/parser/HTTP core
registry-driven local help
process-local chronological history and Ctrl-R reverse search
Ctrl-C, Ctrl-D, /clear and /exit terminal behavior
interactive JSON using the accepted S05 result/trace schema
deterministic FORMATTED rendering
bounded registered GET-only enrichment for the exact frozen read set
complete-or-fail formatted reads
pure, controlled-HTTP and Linux PTY/subprocess evidence
M2-VER-25 / M2-VER-26 / M2-VER-28 primary evidence
preservation of M2-VER-27 and every accepted S05 review-fix boundary
```

Do not start `M2-S07`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not add or use GitHub Actions, encoded patches, workflow-dispatched implementation, or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before editing, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
docs/architecture/api.md
docs/architecture/verification.md

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/runtime-deployment.md
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
```

The following WIP documents may be inspected only as historical discovery/cross-check material and never as authority:

```text
docs/milestones/M2/wip/netauto-cli.md
docs/milestones/M2/wip/cli-architecture-cross-check.md
docs/milestones/M2/wip/cli-stack-10-proposal.md
```

`architecture/cli.md`, the ratified `STACK-10`, `steps.md` and `status.md` supersede them wherever wording differs.

Confirm from the repository that:

```text
checked-out branch                    M2
origin/M2 ancestry                    includes e1f11b8b...
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S05                                reviewer-owned COMPLETED
M2-S06                                READY or IN PROGRESS
M2-S07                                BLOCKED
relevant architecture reopen          none
STACK-10                              RATIFIED
```

Inspect the completed S05 implementation and evidence before choosing any decomposition. At minimum inspect:

```text
pyproject.toml
uv.lock
src/netauto/cli/__init__.py
src/netauto/cli/main.py
src/netauto/cli/model.py
src/netauto/cli/registry.py
src/netauto/cli/parser.py
src/netauto/cli/selectors.py
src/netauto/cli/transport.py
src/netauto/cli/protocol.py
src/netauto/cli/execution.py
src/netauto/cli/render.py
src/netauto/transport/http/health.py
all neutral transport DTO modules

tests/test_m2_s05_model.py
tests/test_m2_s05_parser.py
tests/test_m2_s05_registry.py
tests/test_m2_s05_http_client.py
tests/test_m2_s05_process.py
tests/test_m2_s05_tls.py
tests/test_m2_s05_installed.py
tests/test_m2_s05_review_fixes.py
tests/test_m2_s05_residual_review_fixes.py
tests/test_m2_traceability.py

tests/test_health.py
tests/test_health_probe.py
tests/test_health_api.py
tests/test_health_postgresql.py
tests/test_http_composition.py
```

The accepted S05 implementation is the starting realization, not a disposable prototype. Reuse its immutable command/result model, exact 63-operation registry, parser codecs, selector traversal, HTTPX policy, protocol validation and truthful `ExecutionLedger`. Do not create a parallel interactive command model.

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` remains mandatory for the full repository gate and preserved PostgreSQL claims. Do not provision a database, invent credentials, use Docker/Testcontainers, substitute SQLite or fall back to localhost.

S06 CLI correctness itself is public-HTTP client and terminal correctness. Do not use application services, persistence or PostgreSQL as a substitute for HTTP evidence.

If repository state or a frozen authority conflicts with this task, stop the affected point and report it. Do not modify frozen architecture to fit convenient code. Local decomposition and deterministic wording remain implementation choices only where they do not alter semantics, public guarantees, trace shape or verification authority.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
prompt-toolkit>=3.0,<4 as a runtime dependency
one asynchronous no-argument REPL
process routing between `netauto` and accepted `netauto -n ...`
PromptSession.prompt_async()
POSIX shlex tokenization of submitted REPL lines
explicit testable session state
DISCONNECTED / CONNECTED(normalized endpoint root)
FORMATTED / JSON
one endpoint-scoped reusable HTTPX client
one fresh execution ledger and selector cache per command
/connect
/disconnect
/status
/output
/help
/history
/clear
/exit
remote execution through the completed S05 core
exact Health decoding for connection transitions
registry-driven help
process-local in-memory history
Ctrl-R reverse search
Ctrl-C edit cancellation
Ctrl-D empty-prompt exit
deterministic formatted success/error output
registered bounded single-resource enrichment
Linux PTY/process tests
traceability for M2-VER-25, M2-VER-26 and M2-VER-28
```

## 2.2 Out of scope

Do not implement or expose:

```text
M2-S07 release-version change
runtime.pylock.toml
installed Alembic changes
full installed Linux operating procedure
release-directory layout
server start/stop/restart procedure
full installed-artifact acceptance

M2-S08 integrated final traceability closure
M2-S09 final acceptance or delivery

new server route, DTO field or business behavior
new Health semantics or business-style Health command
schema, migration, table, constraint or index change
application-service, UnitOfWork or persistence execution from CLI
database_url or PostgreSQL access from CLI
native authentication, credential, generic-header or profile model
persistent endpoint/output/history configuration
cross-release negotiation
--insecure / verify=false / skip-verify
custom per-command CA or client certificate
generic --header or Authorization parameter
redirect following
cookie persistence
HTTP or semantic retry/backoff
OpenAPI-generated command registry
plugin command framework
Typer, Click, cmd2 or Rich authority
terminal styling as semantic output
new remote command, alias or alternate grammar
unbounded list/lifecycle enrichment
hidden post-mutation GET
```

Preserve exactly:

```text
project version 0.1.0
15 authoritative tables
one Alembic base / one head
root revision 0001_m2_kernel
compare_metadata == []
41 mutations + 22 reads = 63 business HTTP operations
1 GET /health/core operational operation
64 total public server HTTP operations
63 exact remote CLI CommandSpec values
family census 14 / 16 / 13 / 14 / 5 / 1
65 parser-valid registry examples
83 concurrency scenarios
21 safety predicates
three advisory gates
four row-lock modes
completed S04 Settings/startup/Health behavior
completed S05 non-interactive stdout/stderr/exit and trace behavior
```

S06 supersedes only the temporary S05 expectation that no-argument invocation was invalid. Every accepted `-n` behavior and every S05 review-fix regression remains mandatory.

---

# 3. Dependency and process routing

Add exactly:

```text
prompt-toolkit>=3.0,<4
```

to `[project].dependencies` and update `uv.lock` through the normal locked workflow.

Requirements:

```text
no duplicate dev declaration
no unrelated dependency upgrade
HTTPX remains runtime
project version remains 0.1.0
entrypoint remains netauto = netauto.cli.main:main
```

The installed process grammar is exactly:

```text
netauto
    -> interactive REPL

netauto -n <endpoint-root> <resource> <operation>
    [selector] [parameter=value ...]
    -> accepted S05 non-interactive mode

all other argv shapes
    -> bounded local invocation failure
    -> no prompt and no HTTP exchange
```

Do not run nested event loops. The synchronous entrypoint owns one native-asyncio bootstrap; interactive and non-interactive paths must fit coherently beneath it while preserving the accepted callable/test boundaries where practical.

The non-interactive process contract remains:

```text
one JSON stdout line
empty stderr for structured outcomes
exit 0 on success / 1 on command failure
no prompt, confirmation or Health preflight
```

---

# 4. Singular CLI ownership

Implement the interactive realization conceptually under:

```text
src/netauto/cli/repl.py
```

Local decomposition may add narrowly owned helpers, but preserve singular authorities:

```text
registry.py
    -> all 63 remote commands, help metadata and renderer keys

parser.py
    -> shared remote token validation and value decoding

model.py
    -> immutable command/result/error/trace values

transport.py
    -> HTTPX policy, client lifecycle and truthful attempts

protocol.py
    -> business/Health wire validation

execution.py
    -> selectors, primary request and optional formatted enrichment

render.py
    -> canonical JSON and deterministic formatted output

repl.py
    -> PromptSession, mutable session state, local commands and terminal loop
```

Do not copy the S05 parser into the REPL. Factor a shared remote-token parser used by both already-shell-tokenized `-n` argv and POSIX-`shlex` interactive tokens.

Do not copy the command registry into local help or rendering tables. Local commands may have one separate immutable local registry, but remote metadata must remain the same `CommandSpec` values.

---

# 5. Session, client and command lifetime

Initial state is exactly:

```text
connection = DISCONNECTED
output     = FORMATTED
history    = empty process-local list
prompt     = netauto>
```

No environment variable, localhost default, prior endpoint or profile establishes a connection.

Interactive mode owns at most one endpoint-scoped `httpx.AsyncClient`/transport at a time. Reuse it for selector, primary and enrichment exchanges across commands while CONNECTED.

Separate lifetimes explicitly:

```text
session client / pool
    -> persists while CONNECTED

command ExecutionLedger
    -> new for every submitted command

selector/enrichment memoization
    -> new for every submitted command

command result trace
    -> contains only that command's exchanges
```

Do not let exchanges, selector resolutions or formatted enrichment cache values leak across commands.

Closing must be exact and idempotent for:

```text
/disconnect
successful replacement /connect
failed replacement /connect
/status failure
business-command transport failure
/exit
Ctrl-D exit
ordinary loop shutdown
unexpected ordinary failure when continuation is unsafe
```

Cancellation, `KeyboardInterrupt`, `SystemExit` and other `BaseException` families must not be normalized into ordinary CLI results.

---

# 6. Exact local command inventory and parsing

The only local commands are:

```text
/connect <endpoint-root>
/disconnect
/status
/output <JSON|FORMATTED>
/help [resource] [operation]
/history
/clear
/exit
```

A leading `/` identifies local intent. No local command token is sent to the business API.

Interactive tokenization uses POSIX `shlex`. Empty/whitespace-only submissions perform no command, produce no result and are not added to history.

Validate exact arity and spellings locally. Unknown local commands, malformed quoting, missing/extra arguments and invalid output-mode casing produce bounded existing CLI-local errors and return to the prompt.

Do not add aliases, abbreviations or interactive missing-value questions.

For JSON local results, use the accepted top-level `CliResult` schema. Represent local command intent as:

```text
resource  = local
operation = command name without '/'
selector / parameters = submitted local arguments in deterministic form
exchanges = [] unless the local command owns Health HTTP
```

Keep result payloads deterministic, bounded and limited to the local command's observable state. Do not create a second error taxonomy.

---

# 7. Connection state machine

## 7.1 Remote command while disconnected

Return:

```text
source    = local
code      = cli_not_connected
exchanges = []
```

Do not infer or contact an endpoint.

## 7.2 `/connect <endpoint-root>`

Implement this order exactly:

```text
1. validate local arity
2. close and discard any current client/endpoint
3. normalize and validate the new endpoint root with the accepted S05 authority
4. create one candidate client
5. execute exactly GET <root>/health/core
6. require HTTP 200, exact CoreHealthDTO and both component statuses = ok
7. success -> adopt candidate and become CONNECTED(root)
8. any failure -> close candidate and remain DISCONNECTED
```

A failed replacement never restores the previous endpoint, even when failure occurs during endpoint normalization, client creation, send, response validation or cleanup.

`503`, redirect, malformed JSON, wrong content type, invalid Health DTO, non-ready component status and transport failure all fail connection.

The Health exchange is included exactly once in the local JSON result trace.

## 7.3 `/disconnect`

```text
close current client if present
clear endpoint
state = DISCONNECTED
no HTTP exchange
idempotent while already disconnected
```

## 7.4 `/status`

```text
DISCONNECTED
    -> render local state
    -> no request

CONNECTED
    -> exactly GET /health/core using the current client
    -> valid ready 200 preserves CONNECTED
    -> every other outcome closes client and becomes DISCONNECTED
```

## 7.5 State after ordinary remote commands

```text
local parse/selector error
    -> preserve current state

valid HTTP business success or canonical business error
    -> preserve CONNECTED

business-response protocol error
    -> preserve CONNECTED

HTTPX transport failure during selector, primary or enrichment
    -> close client and become DISCONNECTED
```

No remote command performs an implicit Health preflight.

---

# 8. Local command semantics

## `/output`

Accepted forms are exact and case-sensitive:

```text
/output JSON
/output FORMATTED
```

Apply the new mode before rendering the acknowledgment:

```text
/output JSON       -> acknowledgment in JSON
/output FORMATTED  -> acknowledgment in formatted text
```

Output mode changes do not affect connection or history.

## `/help`

Generate help only from the installed local-command inventory and the exact remote `COMMAND_REGISTRY`:

```text
/help
    -> grammar, exact local commands and resources

/help <resource>
    -> exact operation list

/help <resource> <operation>
    -> selector kind
    -> ordered required/optional parameters and types
    -> exact method/path
    -> concise registry-owned examples
```

No endpoint or OpenAPI request is permitted. Unknown resource/operation is a bounded local error.

## `/history`

Maintain a separate chronological list of non-empty submitted lines.

```text
/history
    -> render all lines completed before the current invocation
    -> include local and remote commands
    -> number from 1
```

Append the current `/history` line only after its result has been rendered. Never persist history across processes.

Use prompt_toolkit `InMemoryHistory` for terminal reverse search while keeping NETAUTO's separate chronological list as the `/history` output authority.

## `/clear`

Clear the terminal through prompt_toolkit-supported terminal mechanics and preserve:

```text
connection
output mode
history
registry
```

It performs no HTTP request.

## `/exit`, Ctrl-D and Ctrl-C

```text
/exit
    -> close client
    -> normal exit 0

Ctrl-D on an empty prompt
    -> same as /exit

Ctrl-C while editing
    -> cancel current input buffer
    -> preserve session state
    -> return to prompt

Ctrl-R
    -> reverse search current-process history
```

One ordinary command error never terminates the REPL.

---

# 9. Remote commands inside the REPL

Interactive remote grammar remains exactly:

```text
<resource> <operation> [selector] [parameter=value ...]
```

Use POSIX `shlex` once, then the same shared parser/value codecs as `-n`. Preserve:

```text
strict omission versus explicit null
inline JSON and @file.json
complete local validation before HTTP
same CommandSpec identity
same deterministic selector order and de-duplication
same exact method/path/query/body construction
same 200/201/204 and Location validation
same canonical remote business errors
same protocol/transport classification
same truthful ordered trace
```

The persistent session client must not weaken S05 attempt ownership. Every actual selector, primary or enrichment send is represented once, including unexpected ordinary send/capture/cleanup failures. Do not catch `BaseException`.

---

# 10. Interactive JSON contract

Interactive JSON uses the accepted S05 top-level shape exactly:

```text
status
command
exchanges
result
error
```

Local commands have the canonical local command identity. Remote JSON mode executes only:

```text
selector lookups
+
primary operation
```

It performs no presentation enrichment.

Each line result must preserve all and only its actual exchanges in order. No exchange from `/connect`, `/status` or an earlier command may leak into a later result.

Do not change non-interactive JSON serialization, field names, immutability, byte stability or stdout semantics.

---

# 11. FORMATTED output

FORMATTED exists only in the interactive REPL.

Global rules:

```text
plain deterministic UTF-8 text
no color/style carries meaning
exact IDs remain visible
no silent value truncation
pages expose next_cursor or explicit end-of-page
errors show source/code/message/http status/bounded details
no traceback or raw ordinary exception text
```

Use `CommandSpec.renderer_key` as the singular remote renderer selector. Every one of the 63 specs must resolve to a renderer strategy; equivalent shapes may share implementations.

## 11.1 Mutations

Render only the direct requested result:

```text
HTTP status
Location when present
returned identifiers/projection
or explicit bodyless success target
```

Never issue a hidden post-mutation GET.

## 11.2 Lists/pages/lifecycle

Render the primary page only. Do not enrich one item at a time. Preserve item IDs and `next_cursor`.

## 11.3 Exact bounded single-resource enrichment set

Required FORMATTED enrichment exists only for:

```text
datatype get-version
    -> stable DataType GET for qualified name

object-template get
    -> stable parent lineage chain

object-template get-version
    -> exact parent-version chain
    -> owning/parent/declaring templates as qualified names
    -> property DataTypes as qualified names
    -> component target templates as qualified names

object-template get-effective-schema
    -> owning/declaring templates
    -> property DataTypes
    -> component target templates

object get
    -> stable ObjectTemplate qualified name

object get-owner
    -> parent Object canonical name when non-null
    -> slot declaring ObjectTemplate qualified name

relationship-definition get
    -> Resolution endpoint templates as qualified names

relationship-definition get-version
    -> property DataTypes as qualified names

relationship get
    -> distinct endpoint Object canonical names
```

Rules:

```text
public GET routes only
no mutation and no Health request
one command-scoped ID memoization map
preserve first-discovery order
lineage traversal stops at root
cycle, missing resource or invalid response -> protocol/corruption failure
required enrichment failure -> whole command failure
no partial formatted representation emitted
all enrichment exchanges appear once in the command trace
```

No list command, lifecycle page or mutation may execute these enrichments.

Build the complete enriched representation before emitting it. Do not stream a partial formatted result.

---

# 12. Failure and outer-loop discipline

Preserve the finite catalog:

```text
local
    cli_invalid_invocation
    cli_invalid_command
    cli_missing_selector
    cli_unexpected_selector
    cli_missing_parameter
    cli_unexpected_parameter
    cli_duplicate_parameter
    cli_invalid_parameter
    cli_json_error
    cli_file_error
    cli_not_connected
    cli_internal_error

selector
    cli_selector_invalid
    cli_selector_not_found
    cli_selector_ambiguous

transport/protocol
    cli_transport_error
    cli_protocol_error
```

Remote server codes remain exact and unprefixed.

An unexpected ordinary exception is bounded at the outer command-loop boundary as `cli_internal_error` only when safe continuation is possible. Preserve the exact command progress and truthful ledger snapshot. Never expose raw exception text.

If session/client state may be corrupted, close it and move to DISCONNECTED before either continuing safely or terminating. Do not silently retain an uncertain CONNECTED state.

---

# 13. Permanent verification

Implement primary evidence for:

```text
M2-VER-25 — interactive state machine
M2-VER-26 — interactive connection behavior
M2-VER-28 — coverage and authority boundary
```

Use pure state-machine tests, controlled HTTP transports and Linux PTY/subprocess tests. Do not use sleep as correctness orchestration; use prompt/output sentinels, PTY reads, process polling and finite hang guards.

## 13.1 M2-VER-25

Cover at minimum:

```text
initial DISCONNECTED / FORMATTED / empty history
exact eight local commands and arity
remote while disconnected -> cli_not_connected / zero exchanges
/output switch-before-acknowledgment
/help without endpoint and from singular registry
chronological /history and append-after-render rule
blank lines excluded
/clear preserves state/history
Ctrl-R current-session reverse search
Ctrl-C edit cancellation without exit
Ctrl-D empty-prompt exit
/exit cleanup and exit 0
REPL continuation after local and remote errors
no implicit endpoint/profile/history persistence
```

## 13.2 M2-VER-26

Cover at minimum:

```text
/connect exact GET /health/core
ready 200 exact DTO -> CONNECTED
valid 503 -> DISCONNECTED
200 with non-ready component -> DISCONNECTED
malformed/wrong-content/invalid DTO -> DISCONNECTED
redirect not followed -> DISCONNECTED
transport failure -> DISCONNECTED
old client closed before replacement validation
failed replacement never restores old endpoint
/disconnect local/idempotent
/status disconnected -> zero requests
/status connected -> exactly one Health request
/status failure closes/disconnects
business remote error preserves CONNECTED
business protocol error preserves CONNECTED
selector/primary/enrichment transport failure disconnects
no business-command Health preflight
```

Assert exact request order and traces.

## 13.3 M2-VER-28

Cover at minimum:

```text
63 API operations == 63 CommandSpec mappings
all renderer keys resolve
help/spec/example consistency
all nine exact enrichment read shapes
lineage and ID memoization
cycle/missing/invalid enrichment complete failure
no partial formatted output
no hidden mutation GET
no list/page/lifecycle enrichment
JSON mode no presentation enrichment
all actual exchanges once and ordered
exact IDs and next_cursor visible
bodyless mutation formatting
error formatting without traceback
CLI HTTP-only import boundary
```

Preserve the accepted S05 support already assigned to M2-VER-28; S06 adds its primary interactive/formatted targets rather than replacing the foundation.

## 13.4 Traceability registry

Update the singular machine-checkable traceability registry so that:

```text
M2-VER-25 and M2-VER-26 move from DESIGNED to IMPLEMENTED
M2-VER-28 remains IMPLEMENTED and gains complete S06 primary targets
all three have non-empty resolvable targets
primary ownership of 25/26/28 remains M2-S06
accepted S05 supporting targets for M2-VER-28 remain represented
M2-VER-27 remains implemented and S05-owned
M2-VER-29 / M2-VER-31 / M2-VER-32 remain DESIGNED
no S07 bundle is overclaimed
```

## 13.5 Accepted S05 regressions

Re-run every `tests/test_m2_s05_*.py` module and preserve:

```text
non-interactive process channels and exit
endpoint/port normalization
63/65 registry census
selectors and nested selectors
TLS trust/hostname matrix
redirect/cookie/retry absence
truthful in-flight ledger behavior
bounded parse/send/capture/cleanup defects
recursive immutability and byte-stable JSON
installed candidate-wheel non-interactive support
```

Adjust only temporary S05 tests explicitly superseded by the no-argument REPL. Replace the old no-argument-error assertion with exact S06 process-mode evidence; preserve malformed unsupported argv evidence. Replace the old assertion that `repl.py`/prompt_toolkit are absent with positive S06 dependency/REPL evidence while retaining all insecure/forbidden-surface assertions.

---

# 14. Mandatory commands and final gate

Run and report exact commands, counts and durations.

## 14.1 Dependency/build/static quality

```text
uv lock
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Use `uv lock` only for the authorized prompt-toolkit dependency change.

## 14.2 Focused S06 evidence

Run exact collected targets for:

```text
state/local commands/history/help
connection/Health transitions
persistent-client versus command-ledger isolation
formatted renderers and all registered enrichments
complete-or-fail behavior
JSON no-enrichment behavior
terminal/PTTY controls
process-mode routing
M2-VER-25
M2-VER-26
M2-VER-28
CLI negative surface
```

## 14.3 Cross-boundary regressions

At minimum run:

```text
all tests/test_m2_s05_*.py
all tests/test_m2_s06_*.py or exact equivalent S06 modules
all Health/S04 tests affected by /connect validation
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py
tests/test_schema_metadata.py
tests/test_migrations.py
uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

The full repository suite must use externally supplied `TEST_DATABASE_URL` and include all PostgreSQL tests. No normative test may be skipped, xfailed or hidden by generic rerun.

Report:

```text
CPython version
PostgreSQL server version
uv version
prompt-toolkit resolved version
collection count
focused state/connection/render/PTY counts
M2-VER-25 target count
M2-VER-26 target count
M2-VER-28 primary and preserved-support counts
all S05 regression count
PostgreSQL count
non-PostgreSQL count
full-suite count and duration
skip / xfail / rerun census
warning census
supported-path 40P01 / unexpected 40001 census
```

S06 adds no concurrency scenario, but every accepted S03 scenario remains mandatory.

## 14.4 Unchanged boundaries

Explicitly verify and report:

```text
15 authoritative tables
one Alembic base / one head
0001_m2_kernel unchanged
compare_metadata == []
no schema/migration/index diff
only authorized pyproject/uv.lock dependency change
project version unchanged
41 mutations + 22 business reads unchanged
1 Health route / 64 total server operations unchanged
63 remote CLI specs exact
family census 14 / 16 / 13 / 14 / 5 / 1
65 registry examples exact
83 scenarios and 21 predicates unchanged
no S07 runtime-lock/release/Linux surface
no PR or GitHub Action
```

---

# 15. Implementation and publication discipline

Work directly on `M2`. Use normal source edits, tests, commits and push. Do not create a PR.

A reasonable sequence is:

```text
implementation commit(s)
    -> dependency, REPL/session, rendering/enrichment and permanent tests

evidence/status commit
    -> candidate evidence and state only after all mandatory gates pass

optional provenance commit
    -> only when needed to identify the exact final remote-tested commit
```

Do not delete this prompt while the slice remains open. Do not edit frozen contract, architecture or steps to fit implementation.

At implementation start, `status.md` may become:

```text
M2-S06 — IN PROGRESS
```

Only after every mandatory gate passes may Codex publish:

```text
M2-S06 — CANDIDATE READY FOR REVIEW
```

Codex must never assign:

```text
M2-S06 — COMPLETED
M2-S07 — READY or IN PROGRESS
```

Those remain reviewer-owned.

If mandatory infrastructure or verification is unavailable, keep S06 explicitly partial/IN PROGRESS or blocked as appropriate, record the exact reason, and never use candidate-ready wording.

After pushing a candidate:

```text
verify local HEAD == origin/M2 == remote M2
verify ahead/behind 0/0
verify working tree clean
rerun the complete mandatory suite on the exact final remote commit
```

Do not hand off an unverified provenance commit.

---

# 16. Required handoff

Report:

```text
cycle / slice / branch
starting baseline
implementation commit(s)
evidence/status commit
final remote HEAD
local/origin/remote synchronization
working-tree state
```

Summarize by boundary:

```text
prompt-toolkit dependency and process routing
session/client lifecycle
shared parser and local command authority
Health state machine
history/help/terminal mechanics
JSON preservation
formatted renderer registry
bounded enrichment
failure/cleanup boundaries
traceability
```

Report exact facts:

```text
8 / 8 local commands
63 / 63 remote operations
65 parser-valid examples
initial/terminal state variants
/connect and /status matrices
persistent-client / command-ledger isolation
all nine enrichment read shapes
zero hidden mutation/list enrichment
M2-VER-25 status and target count
M2-VER-26 status and target count
M2-VER-28 primary count and preserved S05 support
M2-VER-27 regression status
Ctrl-R / Ctrl-C / Ctrl-D / /clear / /exit PTY results
all dependency/lock changes
all commands, counts and durations
environment versions
skip/xfail/rerun/warnings
40P01/40001 census
```

Explicitly state:

```text
M2-S06 is CANDIDATE READY FOR REVIEW, not COMPLETED
M2-S07 remains BLOCKED
no release/runtime-lock/installed-Linux scope was started
no schema, migration, server API or business behavior changed
no PR or GitHub Action was created
```

If a requirement was not executed, a finding remains, or the full externally supplied PostgreSQL suite did not pass, do not use candidate-ready wording.
