# Codex residual review-fix prompt — M2-S05

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS authorities, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Correct exactly the residual reviewer finding recorded for:

```text
M2-S05 — Official CLI HTTP core and non-interactive mode
```

Work directly on branch:

```text
M2
```

The reviewer-owned residual baseline is:

```text
7bfcdc5059de1742c2c211b4edb34c0879f31234
docs(m2): keep S05 open for residual trace boundary
```

Relevant published provenance is:

```text
initial implementation
    3d02fce9fe9c456e26100c3dbbbabce75bf90caf

initial candidate evidence
    c1365c1c951447ed3f22cd54bcb1effcf41043ee

first review record
    77b682bac31f6c2e7a8befa2b5a18d98330fb4ea

first review-fix prompt
    2f43b21d66d318fcc43c2595bdf893fc6f395d53

corrective implementation
    1015dd5ea86b15e8248c9a5e2fe518fe98e2b637

corrective evidence/status
    eb8ff673ad1ea77179194493b712dcc0497b5835

corrective provenance
    372d2954f206ae99f3935d3ee36d28a50f9fb72e

second reviewer record / this baseline
    7bfcdc5059de1742c2c211b4edb34c0879f31234
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
S05-RF-01 — residual unexpected-failure and attempted-exchange trace boundary
```

The following findings are reviewer-owned CLOSED and must not be reopened or redesigned:

```text
S05-RF-02 — strict explicit-port validation
S05-RF-03 — recursive immutable JSON snapshots
S05-RF-04 — registry-owned help metadata and valid examples
```

Do not start `M2-S06`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not add or use GitHub Actions, encoded patches, workflow-dispatched implementation, or artifact-mediated source publication.

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
docs/milestones/M2/wip/M2-S05-residual-review-fix-codex-prompt.md
```

Confirm from the repository, not from this prompt alone:

```text
checked-out branch                    M2
origin/M2 ancestry                    includes 7bfcdc50...
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S04                                reviewer-owned COMPLETED
M2-S05                                REVIEW CHANGES REQUIRED
open finding                          exactly residual S05-RF-01
S05-RF-02 / 03 / 04                   reviewer-owned CLOSED
M2-S06                                BLOCKED
relevant architecture reopen          none
STACK-10                              RATIFIED
working tree before edits             clean
```

Inspect the current implementation and evidence at least in:

```text
src/netauto/cli/main.py
src/netauto/cli/model.py
src/netauto/cli/parser.py
src/netauto/cli/execution.py
src/netauto/cli/selectors.py
src/netauto/cli/transport.py
src/netauto/cli/protocol.py
src/netauto/cli/render.py
src/netauto/cli/registry.py

src/netauto/transport/http/
src/netauto/entrypoints/api/

pyproject.toml
uv.lock

tests/test_m2_s05_parser.py
tests/test_m2_s05_process.py
tests/test_m2_s05_http_client.py
tests/test_m2_s05_installed.py
tests/test_m2_s05_registry.py
tests/test_m2_s05_model.py if present
tests/test_m2_traceability.py
```

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` remains mandatory for the complete repository gate and preservation of previously accepted PostgreSQL claims. Do not provision a database, invent credentials, use Docker/Testcontainers, substitute SQLite or fall back to localhost.

If the branch, `status.md`, frozen authorities or assigned prompt conflict, stop before changing the affected behavior and report the mismatch. Do not edit frozen architecture to fit convenient code.

---

# 2. Hard scope and preservation boundary

## 2.1 In scope

```text
one ordinary-Exception boundary spanning parsing and execution
safe preservation of a fully materialized partial ParsedCommand when available
command-scoped attempted-exchange ownership beginning when send starts
exactly-once provisional/final exchange accounting
response-preserving trace behavior when capture or cleanup fails
bounded internal-error construction from the execution ledger
residual process, transport and trace regressions
residual traceability membership and candidate evidence
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

new server routes, request/response fields, status codes or business behavior
schema, migration, table, constraint or index changes
application-service, Unit-of-Work or database execution from the CLI
new dependencies or dependency-version churn
new auth, credentials, profiles or header configuration
--insecure / verify=false
custom per-command CA or client certificate
redirect following
cookie persistence
retry/backoff
OpenAPI-generated command authority
plugin command framework
```

## 2.3 Accepted material to preserve

Preserve the already conforming implementation and evidence for:

```text
neutral transport DTO authority
FastAPI route reuse of neutral DTO identities
HTTPX runtime dependency promotion
netauto console entrypoint
exact -n non-interactive grammar
63 exact business CommandSpec values
14 / 16 / 13 / 14 / 5 / 1 family census
65 parser-valid registry examples
strict endpoint authority and explicit-port validation
recursive immutable JSON snapshots
registry-owned help/example metadata
deterministic top-level and nested selectors
UUID precedence and UUID-only selector families
per-command selector memoization only
verified TLS and hostname verification
no redirects, retries, auth or cookie persistence
exact 200 / 201 / 204 validation
canonical remote business-error preservation
Location validation
normal selector/primary exchange order
one JSON stdout line, empty stderr and exit 0/1 on supported paths
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

`pyproject.toml` and `uv.lock` must remain unchanged by this residual correction. HTTPX is already the authorized runtime dependency; no additional dependency work is permitted.

---

# 3. Frozen result and trace contract

The non-interactive process result remains exactly:

```json
{
  "status": "ok | error",
  "command": null,
  "exchanges": [],
  "result": null,
  "error": null
}
```

The exact rules relevant to this fix are:

```text
command
    null only when no safe command value exists
    otherwise the original immutable parsed intent

exchanges
    all and only HTTP exchanges actually attempted
    each exchange exactly once
    exact execution order

result
    null on every failure

error
    bounded and structured
    no raw Python, HTTPX, OS or TLS exception text

stdout
    exactly one JSON object followed by one newline

stderr
    empty for every structured outcome

exit
    0 on success
    1 on structured failure
```

An unexpected ordinary defect does not erase parsing state that was safely materialized and does not erase network activity that already began.

Do not catch `BaseException`. In particular:

```text
asyncio.CancelledError
KeyboardInterrupt
SystemExit
GeneratorExit
```

must not become an ordinary `CliResult`.

---

# 4. Residual defect A — one ordinary-Exception boundary covers parsing and execution

## 4.1 Current defect

The reviewed code currently separates the process into:

```text
try parse_process()
except ParseFailure

then

try asyncio.run(execute())
except Exception -> cli_internal_error
```

An unexpected ordinary exception raised by `parse_process()` is outside the bounded internal-error boundary and may produce an unstructured traceback/stderr path.

## 4.2 Required process boundary

Implement one finite process boundary with these semantics:

```text
expected ParseFailure
    -> preserve existing finite local error
    -> command from ParseFailure when present
    -> exchanges = []
    -> exit 1

unexpected ordinary Exception during parsing
    -> cli_internal_error
    -> command = null when no safe ParsedCommand exists
    -> command = safe immutable partial ParsedCommand when one was already materialized
    -> exchanges = []
    -> exit 1

unexpected ordinary Exception during execution or cleanup
    -> cli_internal_error
    -> preserve safe ParsedCommand
    -> preserve ExecutionLedger snapshot
    -> exit 1

BaseException family
    -> propagate unchanged
```

The ordinary-`Exception` boundary must encompass both parsing and execution without swallowing the expected `ParseFailure` classification.

## 4.3 Safe partial command rule

A partial command may be exposed only when it is already a valid immutable `ParsedCommand` snapshot produced by the production parser boundary.

Do not:

```text
copy raw argv wholesale into command
invent a CommandKey after failure
serialize half-decoded mutable dictionaries
expose filesystem paths, credentials or raw exception material
```

Permitted realizations include, but are not limited to:

```text
a small process context updated by parse_process()
a typed parser progress carrier
a bounded internal exception carrying a safe ParsedCommand
a two-stage parser that publishes immutable intent before later validation
```

Do not add an environment-controlled production test hook.

The existing `parse_process(argv) -> (endpoint, command, spec)` public-internal behavior may be preserved through an optional context/dependency injection parameter if useful, but there must remain one production parser authority.

## 4.4 Required parsing evidence

Add deterministic tests for the real production process boundary covering at least:

```text
unexpected RuntimeError before a command key exists
    command = null
    exchanges = []
    cli_internal_error

unexpected RuntimeError after a safe ParsedCommand exists
    command = exact safe parsed intent
    exchanges = []
    cli_internal_error

expected ParseFailure
    original finite local code preserved
    not remapped to cli_internal_error

KeyboardInterrupt from parsing
SystemExit from parsing
asyncio.CancelledError from parsing
    each propagates; none becomes CliResult
```

Tests must exercise `netauto.cli.main.run()` and the actual `main()` output/exit boundary, not only a helper that bypasses it.

At least one subprocess or installed-wheel test must confirm the structured stdout/stderr/exit contract through the installed console boundary. A temporary test-only import hook or isolated wrapper is acceptable if needed to inject an unexpected defect, but do not add a production CLI option, environment variable or runtime hook for fault injection.

---

# 5. Residual defect B — the ledger owns the attempt when send begins

## 5.1 Current defect

The reviewed transport constructs a request trace, calls `AsyncClient.send()`, and appends a completed exchange only:

```text
after an expected httpx.TransportError
or
after send returned, cookie cleanup completed and response trace construction succeeded
```

An unexpected ordinary exception can therefore occur after the request attempt began but before the ledger owns the exchange.

## 5.2 Required attempt lifecycle

Introduce an exactly-once attempt lifecycle equivalent to:

```text
request built
    -> not yet an HTTP attempt

send about to begin
    -> ledger begins one ordered attempt
    -> request trace is fixed
    -> monotonic start is fixed

send fails before returning a response
    -> same attempt finalizes with response = null

send returns a response
    -> same attempt records an immutable response observation immediately
    -> later protocol/capture/cleanup failure cannot remove it

normal completion
    -> same attempt finalizes once
```

Names and local structure are implementation choices. A token/ticket, mutable ledger slot, provisional record or another bounded design is acceptable.

The following invariant is mandatory:

```text
one call whose AsyncClient.send attempt begins
    -> exactly one exchange in the command ledger
```

Never append a second entry merely because classification later changes from expected transport failure to unexpected internal failure.

## 5.3 Snapshot behavior for in-flight attempts

`ExecutionLedger.snapshot()`—or the equivalent authority used by the process boundary—must include an attempt that has begun even when it has not reached ordinary finalization.

Required outcomes:

```text
unexpected ordinary send exception with no response
    -> one exchange
    -> response = null

expected httpx.TransportError
    -> one exchange
    -> response = null
    -> cli_transport_error

response returned, later capture fails
    -> one exchange
    -> response is non-null and represents the observed response
    -> cli_internal_error

response returned, later cleanup fails
    -> one exchange
    -> response is non-null
    -> cli_internal_error
```

Elapsed time must remain a non-negative integer based on monotonic timing. The ledger must not depend on wall-clock time.

## 5.4 Response observation before fallible processing

Once `AsyncClient.send()` returns, capture enough immutable response information before any later fallible protocol/body transformation or cleanup so that the exchange can remain truthful if those later steps fail.

The response observation must preserve, as available from the returned response:

```text
status code
received headers
body format
body value
```

A robust two-stage implementation is encouraged:

```text
observe raw returned response into a bounded immutable snapshot
-> derive the normal HttpResponseTrace
-> perform later cleanup/protocol processing
```

If the normal response-trace builder itself raises unexpectedly, the ledger must still materialize a non-null response from the already observed response. Do not record a false `response = null` after a response was returned.

Do not expose raw bytes as a new public JSON shape. The public trace remains:

```text
body_format = json | text | none
body        = JSON value, text, or null
```

No raw exception text may enter headers, body, details or message.

## 5.5 Cleanup ordering

Preserve the no-cookie-persistence policy, but cleanup must not erase or delay ownership of an attempted exchange.

Required boundaries:

```text
pre-send cookie cleanup fails
    -> no send began
    -> no exchange
    -> cli_internal_error

send began, then post-send cookie cleanup fails
    -> one exchange
    -> response null/non-null according to whether send returned
    -> cli_internal_error

HttpTransport.__aexit__ fails after completed exchanges
    -> every completed exchange preserved
    -> cli_internal_error
```

Do not remove cookie isolation and do not persist cookies merely to simplify ordering.

## 5.6 Exception classification

Keep the finite distinction:

```text
httpx.TransportError
    expected transport boundary
    cli_transport_error
    one attempt, no retry

other ordinary Exception
    unexpected implementation/runtime defect
    propagates to process boundary
    cli_internal_error
    already-started attempts preserved

BaseException
    propagates unchanged
```

Do not broaden `except httpx.TransportError` into `except Exception` inside transport. The transport must not misclassify programming defects as endpoint unavailability.

---

# 6. Exact residual failure matrix

Permanent tests must cover all rows below.

| Case | HTTP attempt began | Response returned | Public error | Exchange count | Response field |
|---|---:|---:|---|---:|---|
| expected local `ParseFailure` | no | no | original local code | 0 | n/a |
| unexpected parse failure before safe command | no | no | `cli_internal_error` | 0 | n/a |
| unexpected parse failure after safe command | no | no | `cli_internal_error` | 0 | n/a |
| pre-send request/cookie defect | no | no | `cli_internal_error` | 0 | n/a |
| expected `httpx.TransportError` | yes | no | `cli_transport_error` | 1 | `null` |
| unexpected ordinary exception from send | yes | no | `cli_internal_error` | 1 | `null` |
| response capture defect | yes | yes | `cli_internal_error` | 1 | non-null |
| post-send cleanup defect | yes | yes | `cli_internal_error` | 1 | non-null |
| `__aexit__` cleanup defect | yes | yes | `cli_internal_error` | 1 | non-null |
| ordinary protocol error | yes | yes | `cli_protocol_error` | 1 | non-null |
| remote business error | yes | yes | remote server code | 1 | non-null |
| `CancelledError` / `KeyboardInterrupt` / `SystemExit` | any | any | not normalized | no structured assertion | no structured assertion |

Add a selector-plus-primary variant proving exact ordering when the primary send/capture/cleanup fails:

```text
exchange[0]    selector lookup
exchange[1]    primary attempt
no duplicates
```

The original `ParsedCommand` shown in the result must remain human intent, not the resolved request candidate.

---

# 7. Test design requirements

## 7.1 Pure ledger tests

Add focused pure tests for the attempt authority:

```text
begin creates one ordered provisional attempt
snapshot includes a begun attempt
response observation updates the same attempt
finalization does not duplicate
repeated snapshot is stable
second finalization/recording cannot create a duplicate
multiple attempts preserve begin order
elapsed_ms is non-negative
```

A malformed static use should fail loudly in tests rather than silently corrupt the trace.

## 7.2 Transport injection tests

Use deterministic injected transports/mocks; no real network timing assumptions.

At minimum inject:

```text
ordinary RuntimeError raised by the send path
httpx.TransportError raised by the send path
response returned, then response-trace construction raises
response returned, then post-send cookie cleanup raises
client __aexit__ / aclose raises
```

For each ordinary unexpected exception, verify the process-level `cli_internal_error` result rather than stopping at a low-level `pytest.raises` test.

For the expected `httpx.TransportError`, verify:

```text
error.source = transport
error.code   = cli_transport_error
one exchange only
response = null
one send attempt only
```

## 7.3 Process boundary tests

Exercise both:

```text
run(argv)
main() / console-style stdout + SystemExit
```

For every structured failure assert exactly:

```text
status        error
result        null
stdout lines  1
stderr        empty
exit code     1
message       bounded
raw sentinel  absent
```

Use distinctive raw exception sentinels and assert they are absent from:

```text
stdout
CliError.message
CliError.details
exchange request/response fields
```

## 7.4 BaseException negative controls

Add explicit negative controls for:

```text
asyncio.CancelledError
KeyboardInterrupt
SystemExit
```

Cover parsing and execution/transport boundaries as applicable. These controls must prove that the exceptions propagate and are not converted into `cli_internal_error`, `cli_transport_error` or `cli_protocol_error`.

Do not catch a propagated `KeyboardInterrupt` or `SystemExit` in the production implementation merely to make a subprocess test convenient.

## 7.5 Installed boundary

Preserve the existing installed-wheel success and malformed-port evidence.

Add bounded installed evidence for the residual process contract where practical. It must import and invoke the installed candidate, not the source checkout, and must not require `NETAUTO_DATABASE_URL` or `TEST_DATABASE_URL`.

No full S07 packaging claim is authorized.

---

# 8. Traceability

## 8.1 Existing review-fix registry

Preserve the existing exact four-key registry:

```python
S05_REVIEW_FIX_TARGETS = {
    "S05-RF-01": frozenset({...}),
    "S05-RF-02": frozenset({...}),
    "S05-RF-03": frozenset({...}),
    "S05-RF-04": frozenset({...}),
}
```

Do not remove the accepted target membership for closed findings.

Extend `S05-RF-01` so it contains every permanent residual target required by this prompt.

## 8.2 Residual target view

Add one machine-checkable residual view:

```python
S05_RESIDUAL_REVIEW_FIX_TARGETS = {
    "S05-RF-01": frozenset({...}),
}
```

Required invariants:

```text
exactly one key
key is S05-RF-01
non-empty target set
all targets resolve in pytest collection
all targets are included in S05_REVIEW_FIX_TARGETS["S05-RF-01"]
all targets are included in M2-VER-27 evidence
all targets are executed in the residual gate
```

Do not introduce `S05-RF-05` or rename the finding. This is completion of the existing reopened finding.

## 8.3 Bundle state

Maintain honest ownership:

```text
M2-VER-27
    primary S05 bundle
    include all residual RF-01 evidence

M2-VER-24
M2-VER-28
M2-VER-30
    bounded supporting evidence only

M2-VER-25 / 26
    remain DESIGNED until S06

M2-VER-29
    remains DESIGNED until S07

M2-VER-31 / 32
    remain DESIGNED until S08
```

Do not claim primary completion for future-owned bundles.

## 8.4 Preserved inventories

Traceability must continue to prove:

```text
41 mutation operations
22 business read operations
63 business HTTP operations
1 Health operation
64 public server HTTP operations
63 CLI remote CommandSpec values
65 stored parser-valid examples
83 concurrency scenarios
21 safety predicates
```

---

# 9. Static and architectural constraints

Add or preserve permanent static evidence that:

```text
main.py catches ordinary Exception but not BaseException
parse_process remains the single parser authority
ExecutionLedger remains command-scoped
transport does not retry
transport catches only the expected HTTPX transport family as transport failure
no raw exception string is copied into CliError
no second trace list bypasses the ledger
no REPL module or prompt_toolkit import exists
no application, persistence or database import enters the CLI
```

Do not satisfy this solely through AST tests. Runtime behavior is primary; static checks are supplementary.

---

# 10. Mandatory verification gate

A real externally supplied PostgreSQL URL remains required for the complete gate.

Run, at minimum:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Then run and report separately:

```text
S05_RESIDUAL_REVIEW_FIX_TARGETS exact union
updated S05-RF-01 complete target set
all S05 tests
M2-VER-27 exact target set
M2-VER-24 bounded support
M2-VER-28 bounded support
M2-VER-30 bounded support
DTO/API/route-inventory regressions
S04 Settings/startup/Health regressions
schema metadata and migration regressions
M1/S00/M2 traceability
PostgreSQL concurrency marker
non-PostgreSQL suite
full repository suite with TEST_DATABASE_URL
installed-wheel/console boundary evidence
```

The residual target run must report:

```text
selector count
collected node count
unique node count
executed node count
passed node count
duration
```

The final report must also include:

```text
full pytest collection count
full-suite count and duration
skip / xfail / rerun census
warning census
supported-path 40P01 census
unexpected 40001 census
expected negative-control 40P01 / 40001 census
CPython version
PostgreSQL server version
uv version
```

No mandatory gate may be replaced by a narrower green subset.

The candidate is not ready when:

```text
TEST_DATABASE_URL is unavailable
any mandatory target is not executed
any target is skipped or xfailed
reruns conceal instability
an ordinary supported path observes 40P01 or unexpected 40001
schema or metadata drift appears
pyproject.toml or uv.lock changes
M2-S06 capability appears
```

---

# 11. Unchanged-boundary verification

Explicitly verify and report:

```text
schema tables                         15
Alembic bases                         1
Alembic heads                         1
root revision                         0001_m2_kernel
compare_metadata                      []
project version                       0.1.0
pyproject dependency diff             none
uv.lock diff                          none
business operations                  41 mutation + 22 read = 63
Health operations                     1
public server operations              64
CLI remote operations                 63
registry examples                     65
concurrency scenarios                 83
safety predicates                     21
REPL/FORMATTED surface                absent
GitHub Actions changes                absent
```

No schema, migration, dependency, lockfile, route, DTO or public-business change is expected from this residual correction.

---

# 12. Status discipline

Before all mandatory gates pass, keep:

```text
M2-S05 — REVIEW CHANGES REQUIRED
M2-S06 — BLOCKED
```

After all mandatory gates pass on the exact published commit, Codex may record only:

```text
M2-S05 — CANDIDATE READY FOR REVIEW
M2-S06 — BLOCKED
reviewer acceptance pending
```

Codex must not declare `M2-S05 COMPLETED`.

Update `docs/milestones/M2/status.md` with:

```text
residual corrective implementation commit
residual candidate evidence/status commit
final provenance commit when used
exact residual target registry counts
finding outcome for S05-RF-01
preservation of CLOSED S05-RF-02/03/04
full gate commands, counts and durations
environment versions
skip/xfail/rerun/warning/SQLSTATE census
unchanged-boundary census
reviewer decision pending
M2-S06 blocked
```

Keep all three S05 execution aids in `wip/` until reviewer acceptance:

```text
M2-S05-codex-prompt.md
M2-S05-review-fixes-codex-prompt.md
M2-S05-residual-review-fix-codex-prompt.md
```

---

# 13. Commit and publication discipline

Use intentional commits on branch `M2`.

A suitable structure is:

```text
fix(m2-s05): close residual CLI trace boundary

docs(m2-s05): record residual candidate evidence

optional provenance-only follow-up when needed
```

Do not create a PR.

After pushing:

```text
git fetch origin M2
verify local HEAD == origin/M2 == remote M2
verify ahead/behind 0/0
verify working tree clean
```

Then rerun the complete mandatory suite on the exact final remote commit. The candidate handoff must use the remote commit identity actually tested.

---

# 14. Required final handoff

The final Codex handoff must state explicitly:

```text
cycle / slice
branch
reviewer baseline
residual review-fix prompt commit
residual implementation commit
candidate evidence/status commit
final provenance/remote HEAD
local/origin/remote equality
ahead/behind
working-tree state
```

For `S05-RF-01`, report separately:

```text
parse boundary before command key
parse boundary after safe partial command
expected ParseFailure preservation
unexpected send exception trace
expected TransportError trace
response-capture failure trace
post-response cleanup failure trace
__aexit__ failure trace
selector-plus-primary ordering
BaseException/cancellation negative controls
```

Report exact traceability membership:

```text
S05_RESIDUAL_REVIEW_FIX_TARGETS selector/node counts
updated S05-RF-01 selector/node counts
M2-VER-27 selector/node counts
```

Report every mandatory gate and the final full-suite rerun on the exact remote HEAD.

End with exactly the honest state:

```text
M2-S05 — CANDIDATE READY FOR REVIEW
M2-S06 — BLOCKED
reviewer acceptance pending
```

If any mandatory requirement remains unexecuted, do not publish the candidate-ready state. Leave `M2-S05` in `REVIEW CHANGES REQUIRED` or `IN PROGRESS` and identify the blocker precisely.