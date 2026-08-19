# Codex review-fix prompt — M2-S05

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Correct exactly the four reviewer findings recorded for:

```text
M2-S05 — Official CLI HTTP core and non-interactive mode
```

Work directly on branch:

```text
M2
```

The reviewer-owned corrective baseline is:

```text
77b682bac31f6c2e7a8befa2b5a18d98330fb4ea
docs(m2): require S05 review fixes
```

The reviewed candidate commits are:

```text
3d02fce9fe9c456e26100c3dbbbabce75bf90caf
    feat(m2-s05): add HTTP-only noninteractive CLI

c1365c1c951447ed3f22cd54bcb1effcf41043ee
    docs(m2-s05): record candidate evidence
```

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    reviewer-owned COMPLETED
M2-S04    reviewer-owned COMPLETED
M2-S05    REVIEW CHANGES REQUIRED
M2-S06    BLOCKED
```

Correct only:

```text
S05-RF-01 — preserve already-attempted exchanges on unexpected ordinary failure
S05-RF-02 — reject malformed explicit endpoint ports without silent repair
S05-RF-03 — make command/result/error/trace JSON state deeply immutable
S05-RF-04 — replace placeholder help/example metadata with registry-owned usable metadata
```

Do not start `M2-S06`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not add or use GitHub Actions, workflow-dispatched implementation, encoded patches, or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before editing, pull the branch with a normal fast-forward and re-read at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Delivered AS-IS authorities
docs/architecture/README.md
docs/architecture/api.md
docs/architecture/verification.md

# Active M2 authorities
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# S05 execution aids
docs/milestones/M2/wip/M2-S05-codex-prompt.md
docs/milestones/M2/wip/M2-S05-review-fixes-codex-prompt.md
```

Confirm from the repository, not from this prompt alone:

```text
checked-out branch                    M2
origin/M2 ancestry                    includes 77b682ba...
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S04                                reviewer-owned COMPLETED
M2-S05                                REVIEW CHANGES REQUIRED
open findings                         exactly S05-RF-01 ... S05-RF-04
M2-S06                                BLOCKED
relevant architecture reopen          none
STACK-10                              RATIFIED
working tree before edits             clean
```

Inspect the current implementation and evidence at least in:

```text
pyproject.toml
uv.lock

src/netauto/cli/main.py
src/netauto/cli/model.py
src/netauto/cli/parser.py
src/netauto/cli/registry.py
src/netauto/cli/selectors.py
src/netauto/cli/transport.py
src/netauto/cli/protocol.py
src/netauto/cli/execution.py
src/netauto/cli/render.py

src/netauto/transport/http/
src/netauto/entrypoints/api/

tests/test_m2_s05_parser.py
tests/test_m2_s05_registry.py
tests/test_m2_s05_http_client.py
tests/test_m2_s05_process.py
tests/test_m2_s05_installed.py
tests/test_m2_s05_tls.py
tests/test_m2_traceability.py
```

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` remains mandatory for the complete repository gate and for preserving previously accepted PostgreSQL evidence. Do not provision a database, invent credentials, use Docker/Testcontainers, substitute SQLite or fall back to localhost.

If the checked-out branch, `status.md`, frozen authorities or assigned prompt conflict, stop before changing the affected behavior and report the mismatch. Do not edit frozen architecture to fit the current implementation.

---

# 2. Hard scope and preservation boundary

## 2.1 In scope

```text
structured partial-execution state for unexpected ordinary CLI failures
one truthful exchange trace across every non-interactive outcome
strict endpoint authority/port syntax validation
recursive immutable or equivalently isolated JSON snapshots
registry-owned descriptions and valid command examples
review-fix traceability and permanent regression tests
candidate evidence/status update after every mandatory gate passes
```

## 2.2 Out of scope

Do not implement or expose:

```text
M2-S06 interactive REPL
PromptSession or prompt_async()
prompt_toolkit dependency
/connect
/disconnect
/status
/output
/help runtime command
/history
/clear
/exit
Ctrl-R / Ctrl-C / Ctrl-D behavior
FORMATTED runtime rendering or enrichment execution
interactive connection state
interactive history

M2-S07 version/release work
runtime.pylock.toml
release version change
manual Linux operating procedure
full installed server/CLI/Alembic release evidence

M2-S08 integrated final closure
M2-S09 final acceptance or delivery

new server routes, fields, status codes or business behavior
schema, migration, table, constraint or index changes
application-service, Unit-of-Work or database execution from the CLI
new dependencies
new auth, credentials, profiles or header configuration
--insecure / verify=false
custom per-command CA or client certificate
redirect following
cookie persistence
retry/backoff
OpenAPI-generated command authority
plugin command framework
```

## 2.3 Conforming candidate material to preserve

Preserve the already accepted shape of:

```text
neutral transport DTO authority
FastAPI route reuse of neutral DTO identities
HTTPX runtime dependency promotion
netauto console entrypoint
exact -n non-interactive process grammar
63 exact business CommandSpec values
14 / 16 / 13 / 14 / 5 / 1 family census
deterministic top-level and nested selectors
UUID precedence and UUID-only selector families
per-command selector memoization only
verified TLS and hostname verification
no redirects, retries, auth or cookie persistence
exact 200 / 201 / 204 validation
canonical remote business-error preservation
Location validation
normal exchange order and transparency
one JSON stdout line, stderr empty, exit 0/1
absence of REPL and FORMATTED runtime behavior
```

Preserve unchanged:

```text
15 authoritative tables
one Alembic base / one head
0001_m2_kernel
compare_metadata == []
41 mutations + 22 reads = 63 business HTTP operations
1 Health operation; 64 public server HTTP operations total
83 concurrency scenarios
21 predicates
project version 0.1.0
schema, migration and index inventory
```

The only dependency/lock delta from the S04 baseline remains the already-authorized HTTPX promotion and console-entrypoint root-project metadata. Do not introduce package-version churn.

---

# 3. `S05-RF-01` — preserve every already-attempted exchange

## 3.1 Defect to correct

The reviewed implementation accumulates exchanges inside `execute()`, while `main.run()` owns the final unexpected ordinary `Exception` boundary. When a defect escapes after one or more HTTP attempts, `run()` creates `cli_internal_error` with an empty exchange tuple.

That is not a truthful execution trace.

The frozen result contract requires:

```text
all and only actual HTTP exchanges
exactly once
in execution order
for success and every failure family
```

An unexpected ordinary defect does not erase network activity that already happened.

## 3.2 Required semantic outcomes

```text
unexpected ordinary Exception before any attempted request
    status       error
    error.source local
    error.code   cli_internal_error
    exchanges    []
    result       null
    exit         1

unexpected ordinary Exception after selector exchange(s)
    status       error
    error.code   cli_internal_error
    exchanges    every completed selector attempt in order
    result       null
    exit         1

unexpected ordinary Exception after primary response capture
    status       error
    error.code   cli_internal_error
    exchanges    selector exchanges, if any, then primary exchange
    result       null
    exit         1

unexpected ordinary Exception during post-response/client cleanup
    status       error
    error.code   cli_internal_error
    exchanges    every exchange already observed before cleanup failed
    result       null
    exit         1
```

For every structured result above:

```text
stdout      exactly one JSON object plus newline
stderr      empty
message     bounded and deterministic
raw error   absent
```

Do not normalize:

```text
BaseException
asyncio cancellation
KeyboardInterrupt
SystemExit
```

They must retain their normal process/task semantics.

## 3.3 Realization constraints

Local decomposition is free. Acceptable conceptual designs include:

```text
an execution context/ledger shared across phases
an internal structured unexpected-execution exception carrying partial exchanges
an async execution result boundary that owns both ordinary and unexpected outcomes
```

Whatever design is chosen:

```text
one authority owns the mutable in-flight exchange ledger
public CliResult remains immutable
normal local/selector/transport/remote/protocol outcomes remain unchanged
TransportFailure remains a normal bounded transport outcome
ordinary protocol errors remain normal bounded protocol outcomes
no exchange is duplicated when converting an unexpected failure
no exchange is lost when HttpTransport.__aexit__ or another cleanup path fails
```

Do not solve this by:

```text
logging exchanges only
replaying requests
retrying the operation
catching BaseException
storing a process-global mutable last trace
adding a second result schema
```

## 3.4 Mandatory permanent evidence

Add deterministic tests for at least:

```text
RF01-A
    defect before any request
    -> empty exchanges

RF01-B
    one successful selector lookup
    -> injected ordinary defect before primary request construction/dispatch
    -> selector exchange preserved

RF01-C
    selector lookup plus primary response captured
    -> injected ordinary post-response/protocol defect
    -> both exchanges preserved in order

RF01-D
    primary response captured
    -> injected client/context cleanup defect
    -> primary exchange preserved

RF01-E
    original exception message contains sentinel secret/internal text
    -> sentinel absent from stdout/stderr/result

RF01-F
    cancellation/BaseException negative controls
    -> not converted into cli_internal_error
```

Tests must exercise the real production boundary used by `netauto -n`; a helper-only unit test is insufficient by itself.

---

# 4. `S05-RF-02` — reject malformed explicit ports

## 4.1 Defect to correct

`urllib.parse.urlsplit()` can represent an explicitly empty port as `parts.port is None`. The candidate therefore accepts malformed authorities such as:

```text
http://example.test:
http://example.test:/
https://[2001:db8::10]:
```

and silently removes the colon during normalization.

The endpoint-root contract permits either:

```text
no port
or
one explicit numeric port in the valid TCP range
```

It does not permit repair of malformed caller input.

## 4.2 Required endpoint outcomes

Valid:

```text
http://example.test
http://example.test/
http://example.test:1
https://example.test:443
https://example.test:65535/
https://[2001:db8::10]
https://[2001:db8::10]:8443/
```

Invalid with `cli_invalid_invocation`:

```text
http://example.test:
http://example.test:/
https://[2001:db8::10]:

http://example.test:0
http://example.test:65536
http://example.test:+80
http://example.test:-1
http://example.test:abc

https://[2001:db8::10]:0
https://[2001:db8::10]:65536
https://[2001:db8::10]:+443
https://[2001:db8::10]:abc
```

Preserve existing rejection of:

```text
missing scheme
unsupported scheme
missing host
userinfo
non-root path
query
fragment
invalid bracketed IPv6
```

Every malformed endpoint must produce:

```text
command      null when parsing failed before a command key exists
exchanges    []
stdout       one structured JSON result in the real process path
stderr       empty
exit         1
no raw URL/credential leakage beyond the operator-selected command carrier
```

## 4.3 Realization constraints

Validate the authority syntax rather than relying only on `parts.port`.

The implementation must distinguish:

```text
colon belonging to bracketed IPv6
colon introducing an explicit port
absence of a port delimiter
```

Do not use a permissive repair step, regex that rejects valid IPv6, or a second endpoint grammar used only by tests.

## 4.4 Mandatory permanent evidence

Add pure parser and installed/process-level cases covering:

```text
hostname no-port and valid boundary ports
bracketed IPv6 no-port and valid boundary ports
empty explicit port
zero
out-of-range
signed
non-numeric
trailing slash variants
```

The process-level evidence must assert:

```text
cli_invalid_invocation
command is null
exchanges == []
stdout one line
stderr empty
exit 1
```

---

# 5. `S05-RF-03` — deep immutability and detached serialization

## 5.1 Defect to correct

Frozen dataclasses and top-level `MappingProxyType` do not freeze nested JSON dictionaries and arrays. The reviewed candidate can retain caller-owned nested containers in:

```text
ParsedCommand.parameters
CliError.details
HttpRequestTrace.body
HttpResponseTrace.body
CliResult.result
```

A later mutation can therefore change the authority after parse or observation.

The architecture requires immutable CLI command, result, trace and error values.

## 5.2 Required property

At construction time, every JSON-bearing value must take a recursive immutable snapshot or an equivalently isolated canonical snapshot.

After construction:

```text
mutating the original constructor input
    -> cannot change stored state

attempting to mutate a publicly exposed nested value
    -> either impossible
       or mutates only a detached copy
    -> cannot change stored state

mutating the result of as_json()
    -> cannot change stored state

render_json() called repeatedly
    -> byte-equivalent output while stored state is unchanged
```

Apply this consistently to:

```text
ParsedCommand
CliError
HttpRequestTrace
HttpResponseTrace
HttpExchangeTrace through its members
CliResult.result
CliResult through its command/exchanges/error members
```

Also preserve immutable query/header representation and exchange tuple ordering.

## 5.3 Allowed realization choices

Local representation is free. Acceptable patterns include:

```text
recursive frozen JSON carriers plus an explicit thaw serializer
private canonical serialized snapshots plus detached accessors
a project-local immutable JSON value implementation
```

Whichever pattern is chosen must preserve:

```text
JSON scalar distinctions
object key/value content
array order
integer versus boolean distinction
null
UTF-8 strings
canonical public output shape
Pyright strict typing
```

Do not:

```text
expose MappingProxyType or tuples directly in JSON output
use shallow deepcopy as the final authority
silently stringify unsupported values
change the public JSON result schema
make command serialization depend on mutable process-global state
```

Transport and protocol code may work on detached mutable candidates internally, but the stored trace/result authority must remain isolated.

## 5.4 Mandatory permanent evidence

For every listed value type, use nested examples containing both dictionaries and arrays and prove:

```text
RF03-A
    mutate original constructor input after construction
    -> stored state unchanged

RF03-B
    mutate nested value returned through public access, when mutable access is provided
    -> stored state unchanged
    OR mutation is rejected because the view is immutable

RF03-C
    mutate nested value in as_json() output
    -> second as_json() unchanged

RF03-D
    repeated render_json()
    -> identical bytes
```

At minimum cover:

```text
ParsedCommand.parameters
CliError.details
HttpRequestTrace.body
HttpResponseTrace.body
CliResult.result
one complete CliResult with command + exchanges + error/result
```

Add a property-based test if useful, but deterministic examples are still required.

---

# 6. `S05-RF-04` — complete registry-owned help and examples

## 6.1 Defect to correct

The registry is correctly the static authority for 63 commands, but the common builder currently gives every command placeholder metadata equivalent to:

```text
help_text   = "<operation> <resource>"
example     = "<resource> <operation>"
renderer    = "<resource>.<operation>"
```

For commands requiring selectors or parameters, the example does not parse as that command.

S06 may render `/help`, but it must consume S05 registry authority rather than invent a second help catalog.

## 6.2 Required registry metadata

Every `CommandSpec` must expose, directly or through deterministic derivation from the same immutable spec:

```text
meaningful bounded operation description
resource and operation key
selector kind or explicit absence
whether selector is required
ordered parameter metadata
required versus optional
nullable versus omission-only
parameter carrier kind
path/query/body location
nested selector metadata
exact HTTP method and path template
expected success status
response validator
renderer key reserved for S06
at least one concise syntactically valid command example
```

The description must describe the operation, not merely repeat the two tokens.

The example authority must be usable without a second test-only fixture. A valid design may store:

```text
one immutable example argv/token tuple
plus a deterministic display rendering
```

or another single authoritative representation.

## 6.3 Exact example requirements

For each of all 63 specs, the example must:

```text
identify the same resource and operation
include a selector exactly when required
include every required parameter
omit no required path/query/body operand
use a valid local carrier for each included value
satisfy discriminated RelationshipDefinition CREATE/RENAME shape
use syntactically valid inline JSON or file-free example values
perform no network activity during validation
avoid secrets, real credentials and machine-specific paths
remain concise enough for installed help output
```

Examples may use deterministic documentation placeholders such as UUIDs, qualified names and canonical names, but they must pass the production local parser.

If examples are stored without `-n` and endpoint tokens for reuse by S06 help, provide one deterministic adapter that validates them through the same command parser. Do not create a second command grammar.

## 6.4 Description and parameter evidence

Machine-check that:

```text
all 63 descriptions are non-placeholder and bounded
all 63 examples parse to their own CommandKey
all required selectors/parameters are represented
parameter metadata is sufficient to render required/optional/type/location information
method/path in help derives from the same CommandSpec
no duplicate help registry exists
no OpenAPI runtime generation is introduced
```

Do not implement:

```text
/help runtime command
REPL
FORMATTED renderer execution
terminal output
prompt_toolkit
```

## 6.5 Mandatory permanent evidence

Add tests conceptually covering:

```text
RF04-A
    exact 63 examples
    -> all parse locally
    -> each resolves to its own key
    -> zero HTTP

RF04-B
    selector-bearing examples contain a selector
    selector-free examples do not invent one

RF04-C
    required parameters are present
    optional parameter metadata remains distinguishable

RF04-D
    RelationshipDefinition CREATE examples cover both discriminated shapes
    RelationshipDefinition RENAME metadata can express both accepted shapes

RF04-E
    descriptions are meaningful and not generic token reversal

RF04-F
    one immutable registry remains the sole command/help/dispatch authority
```

A test that merely asserts non-empty strings does not satisfy this finding.

---

# 7. Cross-finding implementation rules

## 7.1 One parser and one registry

Do not create review-fix-only parsers, endpoint validators, example registries or output schemas.

All evidence must exercise the same production authorities used by:

```text
netauto -n
future S06 parser/help integration
```

## 7.2 Original operator intent

The top-level `command` object in JSON remains the original parsed operator intent:

```text
human selector values remain human values
parameters remain the original typed caller values
selector rewrite affects only the request candidate
```

Deep immutability must not replace original intent with resolved UUIDs.

## 7.3 Trace truthfulness

The trace remains:

```text
all and only actual attempts
selector lookups in deterministic first-occurrence order
then the primary exchange
response = null only when no response was obtained
```

Review fixes must not introduce hidden Health requests, hidden enrichment, retries or replays.

## 7.4 Failure taxonomy

Preserve exactly:

```text
local
selector
transport
remote
protocol
```

and the finite CLI-local code catalog already accepted.

Do not add a new public code for partial execution or endpoint-port errors. Both remain within the existing bounded categories:

```text
unexpected ordinary defect    cli_internal_error
malformed endpoint            cli_invalid_invocation
```

---

# 8. Traceability and evidence registry

Add a permanent machine-resolvable registry:

```python
S05_REVIEW_FIX_TARGETS = {
    "S05-RF-01": frozenset({...}),
    "S05-RF-02": frozenset({...}),
    "S05-RF-03": frozenset({...}),
    "S05-RF-04": frozenset({...}),
}
```

Requirements:

```text
exactly four keys
non-empty target set for each key
every node ID is collected by pytest
every target asserts the corresponding reviewer finding
targets are not documentation-only or source-string-only when runtime behavior matters
```

Update the existing bundle registries honestly:

```text
M2-VER-27
    include every review-fix target required by the non-interactive process contract

M2-VER-28 supporting S05 path
    include registry/help/authority and deep-boundary targets where applicable

M2-VER-30 supporting S05 path
    include endpoint/TLS/negative-surface targets where applicable
```

Preserve ownership states:

```text
M2-VER-27       S05 primary candidate PASS only after execution
M2-VER-24       bounded supporting evidence; primary S07-owned
M2-VER-28       bounded supporting evidence; primary S06-owned
M2-VER-30       bounded supporting evidence; primary S07-owned
M2-VER-25/26    DESIGNED until S06
M2-VER-29       DESIGNED until S07
M2-VER-31/32    DESIGNED until S08
```

Do not claim future bundle completion merely because a supporting target passes.

Preserve exact registries:

```text
41 mutations
22 business reads
63 business HTTP operations
1 Health operation
64 total public server operations
83 scenarios
21 predicates
```

---

# 9. Required verification

Run focused checks while implementing, then all gates below.

## 9.1 Static and build gates

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

The lockfile must remain unchanged by the review fixes unless the normal tool proves a root metadata correction is unavoidable. No new dependency is authorized.

## 9.2 Exact review-fix targets

Execute the exact union of:

```text
S05_REVIEW_FIX_TARGETS["S05-RF-01"]
S05_REVIEW_FIX_TARGETS["S05-RF-02"]
S05_REVIEW_FIX_TARGETS["S05-RF-03"]
S05_REVIEW_FIX_TARGETS["S05-RF-04"]
```

Report selector count, unique collected node count, pass count and duration.

## 9.3 S05 and cross-boundary gates

Run at minimum:

```text
all tests/test_m2_s05_*.py
M2-VER-27 primary target union
S05 supporting M2-VER-24/28/30 target unions
neutral DTO and OpenAPI regressions
all route-inventory tests
S04 Settings/startup/Health regressions
schema metadata and migration regressions
M1 / S00 / M2 traceability
```

## 9.4 Repository preservation gates

With externally supplied `TEST_DATABASE_URL`, run:

```text
all PostgreSQL concurrency tests
all non-PostgreSQL tests
full repository suite
```

No required test may be skipped, xfailed or hidden behind a generic rerun.

Record:

```text
CPython version
PostgreSQL version
uv version
collection count
focused counts/durations
PostgreSQL count/duration
non-PostgreSQL count/duration
full-suite count/duration
skip / xfail / rerun census
warning census
supported-path 40P01 census
unexpected 40001 census
```

S05 adds no concurrency scenario, but all accepted S03 evidence must remain green.

## 9.5 Installed console evidence

Build and install the candidate wheel outside the repository import path and prove at least:

```text
netauto entrypoint imports from installed environment
no NETAUTO_DATABASE_URL is required
successful -n command
malformed endpoint-port failure
unexpected post-exchange internal failure through a controlled installed boundary when feasible
one stdout JSON line
stderr empty for structured outcomes
exit 0/1
no Health preflight
```

The full S07 installed distribution gate remains out of scope.

---

# 10. Candidate publication discipline

Only after every required gate passes may Codex update:

```text
docs/milestones/M2/status.md
```

to:

```text
M2-S05 — CANDIDATE READY FOR REVIEW
M2-S06 — BLOCKED
review result — pending
```

Do not mark `M2-S05 COMPLETED`.

The status record must include:

```text
reviewer baseline
review-fix prompt commit
corrective implementation commit
candidate evidence/status commit
all four finding outcomes
exact target registry and pass counts
bundle-state honesty
environment and full gate results
unchanged schema/public/concurrency boundaries
```

Keep both execution aids in `wip/` until reviewer acceptance:

```text
docs/milestones/M2/wip/M2-S05-codex-prompt.md
docs/milestones/M2/wip/M2-S05-review-fixes-codex-prompt.md
```

Publish normally to `origin/M2` without PR or GitHub Actions.

After the final push:

```text
verify local HEAD == origin/M2 == remote M2
verify ahead/behind == 0/0
verify working tree clean
rerun the complete mandatory suite on the exact final remote commit
```

If that exact-commit rerun fails, do not hand off a candidate.

---

# 11. Mandatory handoff format

The final handoff must state clearly:

```text
cycle / slice
branch
review baseline
review-fix prompt commit
corrective implementation commit
candidate evidence/status commit
remote HEAD
working-tree and ahead/behind state
```

For each finding:

```text
S05-RF-01
    structured partial-execution design
    selector/primary/cleanup fault evidence
    cancellation/BaseException negative controls

S05-RF-02
    exact port syntax policy
    hostname and IPv6 boundary matrix
    installed/process evidence

S05-RF-03
    recursive immutable snapshot design
    original-input/public-access/as_json mutation evidence

S05-RF-04
    registry metadata design
    63/63 valid examples
    parser/key/required-operand evidence
```

Also report:

```text
S05_REVIEW_FIX_TARGETS exact membership/counts
M2-VER-27 result
bounded supporting M2-VER-24/28/30 results
collection and all gate counts/durations
CPython/PostgreSQL/uv versions
skip/xfail/rerun/warning/40P01/40001 census
schema/migration/dependency/version diff statement
63-operation, 83-scenario and 21-predicate invariants
absence of S06 capability
absence of PR and GitHub Actions
```

If a required infrastructure target is unavailable, a normative test is unexecuted, or an architecture/documentation contradiction is discovered:

```text
do not claim CANDIDATE READY FOR REVIEW
leave M2-S05 IN PROGRESS or STOP for the affected point
record the exact blocker
keep M2-S06 BLOCKED
```

Reviewer acceptance remains pending and reviewer-owned.