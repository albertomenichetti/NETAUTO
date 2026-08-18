# Codex review-fix prompt — M2-S04

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Correct exactly the open review findings for:

```text
M2-S04 — Runtime settings, startup revision guard and Core Health
```

Work directly on branch:

```text
M2
```

The reviewer-owned corrective baseline is:

```text
5a3cac401141c783e4ef8881bffac2816df856a1
docs(m2): require S04 review fixes
```

The reviewed candidate chain is:

```text
original S04 prompt             43b2c42188af35db650b1e7badecf39038987566
implementation/evidence         dc18d5dcca586b6c64ae6912921448318db8e27c
candidate status                765ef4bb356776555f89fe98e5387ed6b1b7de49
review changes record           5a3cac401141c783e4ef8881bffac2816df856a1
```

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    reviewer-owned COMPLETED
M2-S04    REVIEW CHANGES REQUIRED — bounded fixes only
M2-S05    BLOCKED
```

Correct only:

```text
S04-RF-01 — expected bootstrap failures retain sensitive raw causes
S04-RF-02 — an inner TimeoutError is misclassified as database not-ready
S04-RF-03 — M2-VER-22/23 traceability and installed evidence overstate closure
```

Do not start `M2-S05`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release. Do not add or use GitHub Actions, encoded patches, workflow-dispatched implementation, or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before editing, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Delivered AS-IS authorities
docs/architecture/README.md
docs/architecture/persistence.md
docs/architecture/api.md
docs/architecture/verification.md

# Active M2 authorities
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Execution aids
docs/milestones/M2/wip/M2-S04-codex-prompt.md
docs/milestones/M2/wip/M2-S04-review-fixes-codex-prompt.md
```

Confirm from the repository that:

```text
checked-out branch                    M2
origin/M2 ancestry                    includes 5a3cac40...
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S03                                COMPLETED
M2-S04                                REVIEW CHANGES REQUIRED
M2-S05                                BLOCKED
open findings                         exactly S04-RF-01/02/03
relevant architecture reopen          none
TEST_DATABASE_URL                     externally supplied and usable
```

Inspect the reviewed implementation and evidence, including at least:

```text
src/netauto/settings.py
src/netauto/application/health.py
src/netauto/persistence/health.py
src/netauto/persistence/engine.py
src/netauto/runtime/schema_guard.py
src/netauto/entrypoints/http.py
src/netauto/entrypoints/api/health.py
src/netauto/entrypoints/api/errors.py

 tests/test_settings.py
 tests/test_health.py
 tests/test_health_probe.py
 tests/test_health_postgresql.py
 tests/test_health_api.py
 tests/test_http_composition.py
 tests/test_runtime_engine.py
 tests/test_runtime_schema_guard.py
 tests/test_m2_s04_installed.py
 tests/test_m2_s04_scope.py
 tests/test_m2_traceability.py
 tests/test_object_scope.py
```

Also inspect the exact locked Starlette/Uvicorn lifespan behavior used by the candidate environment. The production diagnostic boundary is the complete factory/startup/lifespan traceback or log, not only `str(top_level_exception)`.

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` remains mandatory. Do not provision a database, invent credentials, use Docker/Testcontainers, substitute SQLite, fall back to localhost, or silently use `NETAUTO_DATABASE_URL` as the automated-test authority.

If repository state or a frozen authority conflicts with this task, stop only the affected point and report it. Do not modify frozen architecture to fit the current code.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
production Settings failure sanitization
expected startup-guard failure sanitization
owned timeout discrimination for startup and Health
real factory/lifespan/Uvicorn diagnostic evidence
M2-VER-22 exact target closure
M2-VER-23 exact target closure
installed-wheel runtime 503 then same-engine recovery evidence
S04 review-fix traceability
```

## 2.2 Out of scope

Do not add or change:

```text
M2-S05 or later CLI behavior
console entrypoints
HTTPX or prompt-toolkit dependency promotion
release version or runtime.pylock.toml
full S07 packaging/Linux procedure
new public routes or Health aliases
Health authentication, liveness or metrics
host/port/workers Settings
schema, tables, columns, constraints, indexes or migration graph
durable revision 0001_m2_kernel
business DTOs, commands, failures or semantics
lock planner, gates, retries or concurrency scenario registry
automatic migration, stamp, repair or schema fallback
new dependency or uv.lock content
GitHub Actions or encoded implementation payloads
```

Preserve exactly:

```text
15 authoritative tables
one Alembic base / one head
root revision 0001_m2_kernel
compare_metadata == []
41 mutations + 22 reads = 63 business operations
1 GET /health/core operational operation
64 total public HTTP operations
83 concurrency scenarios
21 safety predicates
three advisory gates
four row-lock modes
```

Both S04 execution aids remain in `wip/` until reviewer acceptance:

```text
M2-S04-codex-prompt.md
M2-S04-review-fixes-codex-prompt.md
```

---

# 3. Conforming material to preserve

Do not rewrite working S04 behavior merely to satisfy a test.

Preserve:

```text
Settings
    seven exact immutable fields
    constructor > environment > explicit secret files > defaults
    absolute existing NETAUTO_SECRETS_DIR selector
    no dotenv or implicit source

RuntimeContext
    one bounded lazy AsyncEngine per worker
    same engine for business/coherent UoW, guard and Health
    exact pool keyword mapping

startup guard
    ScriptDirectory from netauto:migrations
    one installed base and one installed head
    expected revision discovered, never hard-coded
    actual revision via MigrationContext on runtime.engine
    exact singleton equality
    fixed 10.0-second owned deadline
    no migration, stamp, repair or retry

lifespan
    guard before app.state publication and serving
    disposal on normal, failed, post-composition and cancelled paths

Health
    exact SELECT 1 on runtime.engine
    exact integer scalar 1
    fixed 2.0-second whole-probe deadline
    one attempt, no retry/cache/background work
    exact 200/503/400/canonical-500 HTTP behavior
    Cache-Control: no-store on valid 200/503

surface
    GET /health/core only
    63 business + 1 operational operation
```

The review findings do not authorize a second engine, a second settings model, a second expected-revision authority or a second Health service.

---

# 4. S04-RF-01 — sanitize the complete bootstrap diagnostic boundary

The current top-level messages are bounded, but raw input/cause material can still be rendered by Pydantic, Starlette and Uvicorn.

The correction must cover the complete production boundary.

## 4.1 Settings validation and source failures

Direct Pydantic validation currently may render the original `input_value`, including a credential-bearing database URL.

Implement defense in depth:

```text
Settings model rendering
    -> hide input values in validation error string/repr output

production load_settings()
    -> catch only finite expected settings validation/source failures
    -> raise one bounded SettingsBootstrapError or equivalent
    -> suppress the raw cause/context from outward traceback rendering

invalid NETAUTO_SECRETS_DIR selector
    -> retain bounded category message
    -> do not include the selected path

unexpected programming defects
    -> do not catch or normalize
```

Use `hide_input_in_errors=True` in the Pydantic configuration unless an equally strong permanent mechanism is demonstrated. This alone is not sufficient: production `load_settings()` must still convert expected validation/source failures into a bounded bootstrap exception.

For expected Settings failures, require all of:

```text
safe fixed message
__cause__ is None
context is suppressed from traceback rendering
traceback.format_exc() contains no raw input
factory/bootstrap logging contains no raw input
```

A finite expected failure may include:

```text
Pydantic ValidationError
pydantic-settings source/configuration error
expected filesystem/source-read error for the explicitly selected secret source
```

Do not catch `BaseException`. Do not absorb `CancelledError`, `KeyboardInterrupt` or `SystemExit`.

Test with a parseable but disallowed credential-bearing URL such as a non-Psycopg PostgreSQL driver so the sentinel reaches validation:

```text
scheme/driver sentinel
username sentinel
password sentinel
host sentinel
port sentinel
database sentinel
query-option sentinel
```

Every sentinel must be absent from:

```text
str(exception)
repr(exception)
traceback.format_exc()
factory/startup diagnostic output
captured logs
```

## 4.2 Installed graph, database inspection and guard timeout failures

For expected startup-guard failures, keep the existing bounded exception taxonomy:

```text
MigrationGraphInvalid
SchemaGuardUnavailable
SchemaRevisionMismatch
```

Expected underlying failures must not remain outward raw causes.

For expected graph/database/source failures:

```text
catch only the finite expected infrastructure exception set
raise the bounded wrapper from None
retain no raw outward __cause__
suppress raw __context__ rendering
never include raw filesystem, SQLAlchemy or Psycopg text
```

Revision mismatch may continue to expose only bounded expected/actual revision identifiers or counts. It must not expose connection or SQL information.

The fixed startup timeout must also distinguish its owned expiration from an unexpected inner `TimeoutError`:

```text
owned 10-second guard deadline expires
    -> SchemaGuardUnavailable with bounded timeout message

inner/raw TimeoutError while the owned deadline has not expired
    -> propagate as unexpected
```

Use the timeout context's expiration state or another explicit owned-timeout discriminator. Do not classify all `TimeoutError` instances as guard timeouts.

Preserve cancellation propagation and cleanup.

## 4.3 Real diagnostic evidence, not top-level-string evidence

Add permanent evidence that captures the actual production diagnostic path.

For Settings/factory failures, exercise the real `create_app()`/factory loading boundary used by Uvicorn or an equivalent process-level factory harness.

For lifespan failures, exercise the real ASGI lifespan startup protocol and at least one actual Uvicorn lifespan logging path without opening a network listener.

At minimum cover:

```text
credential-bearing invalid Settings
unreadable installed Alembic graph
unreachable or query-failing database
owned startup-guard timeout
```

Inject unique sentinels into raw underlying errors for:

```text
credential/database URL
host/port
filesystem path
SQL statement
SQLSTATE
constraint/table name
driver/protocol message
```

Assert that the full emitted factory/startup/lifespan diagnostic and captured log text contain none of those sentinels.

Also assert the bounded category remains observable, for example:

```text
runtime settings are invalid
installed migration graph is unreadable
database revision state could not be inspected
database revision check timed out
```

Exact wording may retain the current bounded vocabulary, but it must be stable, non-secret and finite.

## 4.4 Negative control for unexpected defects

Prove that an unexpected programming exception from:

```text
Settings bootstrap helper
installed graph discovery
current-head adapter
```

is not silently converted into an expected availability/mismatch result merely to sanitize it.

Sanitization applies to expected bootstrap failures. It is not a blanket `except Exception` around the application.

---

# 5. S04-RF-02 — distinguish the Health-owned deadline

The current `CoreHealthService.check()` catches bare `TimeoutError` around the complete probe and therefore converts an unexpected inner timeout into a false readiness 503.

Implement this exact classification:

```text
PostgreSQLHealthProbe raises DatabaseProbeTimedOut
    -> db_status error
    -> message "database readiness check timed out"
    -> HTTP 503

owned outer two-second deadline expires
    -> db_status error
    -> message "database readiness check timed out"
    -> HTTP 503

DatabaseProbeUnavailable
    -> db_status error
    -> message "database readiness check failed"
    -> HTTP 503

inner/raw TimeoutError while the owned deadline is not expired
    -> propagate unchanged as unexpected
    -> existing HTTP unexpected-failure boundary
    -> canonical safe 500 internal_error
```

Use an explicit timeout object or equivalent owned-deadline state. Conceptually:

```python
deadline = asyncio.timeout(CORE_DATABASE_HEALTH_TIMEOUT_SECONDS)
try:
    async with deadline:
        await probe.check()
except TimeoutError:
    if not deadline.expired():
        raise
    # classify only the owned expiration
```

The exact local structure may differ, but the semantic distinction must be permanent and testable.

Preserve:

```text
one probe call
no retry
cancellation propagation
cleanup completion before final monotonic measurement
negative elapsed floor at zero
integer millisecond floor
real pool-starvation timeout and recovery
unexpected non-timeout defect propagation
```

Add deterministic T1/T4 evidence for:

```text
immediate inner TimeoutError
    -> CoreHealthService raises it
    -> probe called once

same inner TimeoutError through GET /health/core
    -> 500 canonical internal_error
    -> raw message absent from response
    -> not a 503 Health DTO

blocking probe / owned deadline
    -> 503 timeout Health DTO

DatabaseProbeTimedOut
    -> 503 timeout Health DTO
```

Re-run the real PostgreSQL pool-starvation test unchanged or strengthened. It must still prove the two-second Health boundary beats the longer pool timeout and that the same engine later recovers.

---

# 6. S04-RF-03 — honest exact bundle membership and installed recovery

The singular M2 registry remains the only traceability authority.

## 6.1 Exact M2-VER-22 membership

`S04_BUNDLE_TARGETS["M2-VER-22"]` must explicitly include permanent collected targets proving at least:

```text
unique installed base/head discovery
zero/multiple installed bases or heads rejected
unreadable installed graph sanitized
exact real PostgreSQL head accepted
missing/base/old/newer/unknown/multiple database states rejected
unreachable database sanitized
query failure sanitized
malformed/indeterminate current-head result rejected
owned guard timeout rejected safely
inner unexpected TimeoutError not misclassified as owned timeout
guard failure prevents state publication/serving
engine disposed on guard failure
engine disposed on post-engine composition failure
engine disposed on cancelled startup
every separately built worker executes its own guard
no startup upgrade/stamp/repair
installed-wheel graph and fail-closed smoke
complete safe factory/lifespan/Uvicorn diagnostic boundary from S04-RF-01
```

Existing targets may be reused only when they assert the exact property. Merely having a test elsewhere in the suite is not bundle membership.

## 6.2 Exact M2-VER-23 membership

`S04_BUNDLE_TARGETS["M2-VER-23"]` must explicitly include permanent collected targets proving at least:

```text
exact Health vocabulary and one attempt
owned outer timeout and cleanup-before-measurement
DatabaseProbeTimedOut classification
DatabaseProbeUnavailable classification
inner unexpected TimeoutError propagation
inner unexpected TimeoutError -> canonical safe HTTP 500
unexpected non-timeout failure propagation
cancellation propagation
finite probe translation with no raw-message leakage
exact SELECT 1 and exact scalar 1
same runtime engine identity
no commit and clean connection return
real pool-starvation 503 and same-engine recovery
exact 200 / 503 / 400 / 500 HTTP families
Cache-Control no-store
OpenAPI 200/503 common DTO
negative no-Alembic/no-second-engine/no-UoW/no-retry Health surface
installed-wheel healthy response
installed-wheel runtime not-ready 503 after successful startup
installed-wheel recovery to 200 on the same runtime engine
```

## 6.3 Extend installed-wheel evidence

Extend the bounded installed-wheel S04 test; do not replace it with a source-tree test.

The test must still prove:

```text
installed netauto imported outside Git checkout
installed netauto:migrations graph discovered
factory construction performs no network I/O
head-matching installed lifespan enters serving
Health 200
controlled guard failure never serves
```

Add, inside one successful installed lifespan:

```text
record installed app.state.runtime.engine identity
exhaust the installed runtime pool deterministically
call GET /health/core
observe 503 with the exact bounded timeout DTO and no-store
release the held runtime connection
call GET /health/core again
observe 200
assert the engine identity is unchanged
assert no second startup guard or engine construction occurred per request
```

A recommended deterministic shape is:

```text
pool_size = 1
max_overflow = 0
pool_timeout > 2 seconds
hold the sole connection from app.state.runtime.engine
invoke the installed ASGI app while the same lifespan remains active
release
invoke again
```

Do not use sleep as the authority. The held connection is the deterministic boundary.

The installed test may use the locked test environment for dependencies, but the `netauto` import and migration resources must come from the candidate wheel installed into a temporary path. No editable/source import is allowed.

## 6.4 Review-fix registry

Add one machine-checkable registry:

```python
S04_REVIEW_FIX_TARGETS = {
    "S04-RF-01": frozenset(...),
    "S04-RF-02": frozenset(...),
    "S04-RF-03": frozenset(...),
}
```

Require:

```text
exact three keys
non-empty targets for each finding
every target resolves against actual pytest collection
S04-RF-01 includes the real diagnostic-boundary targets
S04-RF-02 includes service and HTTP inner-timeout targets
S04-RF-03 includes exact traceability and installed recovery targets
```

Update the registry equality tests so the bundle sets are exact, not merely non-empty subsets.

Keep honest:

```text
M2-VER-01 ... M2-VER-23 owned through S04
    -> IMPLEMENTED with exact non-empty targets

M2-VER-24 and later
    -> DESIGNED

M2-VER-31 / M2-VER-32
    -> still owned by S08
```

Do not mark static bundle state `PASS`; executed PASS belongs only in candidate evidence/status.

---

# 7. Required implementation discipline

## 7.1 Expected versus unexpected failures

Maintain a finite classification boundary.

Expected sanitized bootstrap failures are only the explicitly owned categories. Do not add a broad wrapper that hides all defects.

At every corrected boundary, prove:

```text
expected failure
    -> bounded semantic/bootstrap category
    -> no secret/raw cause in outward diagnostic

unexpected defect
    -> propagates
    -> no false mismatch, timeout or not-ready result

cancellation
    -> cleanup
    -> propagation
```

## 7.2 No sensitive fixtures in failure output

Tests should use obvious unique sentinels, but failed assertions and normal PASS output must not print real `TEST_DATABASE_URL` values.

When subprocess output is included in an assertion, sanitize the externally supplied real URL before constructing the assertion message.

Do not write credentials into `status.md` or the execution aid.

## 7.3 No architecture-by-test

Do not alter the frozen public behavior to make the tests easier.

In particular, do not:

```text
turn startup failures into HTTP endpoints
return a generic 503 for all Health defects
cache the guard result globally across workers
run the guard on each Health request
add a Health-specific engine
remove exception propagation for unexpected defects
```

---

# 8. Mandatory evidence

Use focused tests first, then every regression gate.

## 8.1 S04-RF-01 focused evidence

Cover at minimum:

```text
Settings.hide_input_in_errors or equivalent
load_settings invalid credential-bearing URL -> bounded bootstrap failure
invalid direct secret selector -> bounded non-path-bearing failure
traceback.format_exc() contains no sensitive input
expected wrappers have no outward raw cause
unreadable graph full diagnostic sanitized
unreachable/query failure full diagnostic sanitized
guard timeout full diagnostic sanitized
real ASGI lifespan.startup.failed message sanitized
real Uvicorn lifespan log sanitized
unexpected graph/current-head defect still propagates
cancelled startup still propagates after disposal
```

## 8.2 S04-RF-02 focused evidence

Cover at minimum:

```text
inner TimeoutError service propagation
inner TimeoutError HTTP canonical 500
owned outer timeout remains exact 503
DatabaseProbeTimedOut remains exact 503
DatabaseProbeUnavailable remains exact 503
one attempt
cleanup-before-measurement
cancellation propagation
real PostgreSQL starvation and recovery
```

## 8.3 S04-RF-03 focused evidence

Cover at minimum:

```text
S04_REVIEW_FIX_TARGETS exact/resolvable
M2-VER-22 exact target membership
M2-VER-23 exact target membership
M2-VER-24+ still DESIGNED
63 business + 1 operational route inventory
installed-wheel 200 -> deterministic 503 -> same-engine 200
installed-wheel controlled guard failure remains fail-closed
```

## 8.4 Preserved S04 evidence

Re-run all existing S04 targets, not only the new tests:

```text
Settings and pool mapping
RuntimeContext identity/laziness
schema guard pure and real PostgreSQL matrix
lifespan order and disposal
Health pure/probe/PostgreSQL/API
installed-wheel smoke
S04 scope negatives
M2 traceability
```

## 8.5 Cross-boundary regressions

Re-run at minimum:

```text
M1 traceability
S00 traceability
complete M2 traceability
schema metadata
migration suite
complete PostgreSQL concurrency marker
all non-PostgreSQL tests
full repository suite
```

No normative test may be skipped, xfailed or hidden by generic rerun. Timeout is a hang guard only.

---

# 9. Mandatory commands and gate

Run and report exact commands, counts and durations.

## 9.1 Build and static quality

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

## 9.2 Focused review-fix gate

Run the exact collected targets for:

```text
S04-RF-01 diagnostic sanitization
S04-RF-02 owned timeout discrimination
S04-RF-03 registry and installed recovery
```

Also run all files affected by the correction, expected to include at least:

```text
tests/test_settings.py
tests/test_health.py
tests/test_health_probe.py
tests/test_health_postgresql.py
tests/test_health_api.py
tests/test_http_composition.py
tests/test_runtime_schema_guard.py
tests/test_m2_s04_installed.py
tests/test_m2_s04_scope.py
tests/test_m2_traceability.py
```

## 9.3 Required regression commands

At minimum run:

```text
uv run pytest -q \
  tests/test_settings.py \
  tests/test_health.py \
  tests/test_health_probe.py \
  tests/test_health_postgresql.py \
  tests/test_health_api.py \
  tests/test_http_composition.py \
  tests/test_runtime_engine.py \
  tests/test_runtime_schema_guard.py \
  tests/test_m2_s04_installed.py \
  tests/test_m2_s04_scope.py \
  tests/test_object_scope.py \
  tests/test_m2_traceability.py -ra

uv run pytest -q \
  tests/test_schema_metadata.py \
  tests/test_migrations.py -ra

uv run pytest -q \
  tests/test_m1_traceability.py \
  tests/test_m2_s00_traceability.py \
  tests/test_m2_traceability.py -ra

uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

Adapt filenames only if new focused tests are placed elsewhere. Do not omit an obligation.

The complete suite must use the externally supplied `TEST_DATABASE_URL` and include every PostgreSQL test.

Report:

```text
CPython version
PostgreSQL server version
uv version
collection count
S04-RF-01 count/duration
S04-RF-02 count/duration
S04-RF-03 count/duration
complete focused S04 count/duration
schema/migration count/duration
traceability count/duration
PostgreSQL concurrency count/duration
non-PostgreSQL count/duration
full-suite count/duration
skip / xfail / rerun census
warnings census
supported-path 40P01 census
unexpected 40001 census
```

S04 adds no new T3 scenario; every accepted S03 target must remain green.

## 9.4 Final exact-remote rerun

After committing and pushing the corrective implementation and candidate status:

```text
confirm local HEAD == origin/M2 == remote M2
confirm ahead/behind 0/0
confirm working tree clean
re-run the complete mandatory suite on that exact final remote commit
```

Do not report `CANDIDATE READY FOR REVIEW` if the final post-push run fails or was not executed.

## 9.5 Unchanged-boundary verification

Explicitly verify and report:

```text
15 authoritative tables
one Alembic base / one head
0001_m2_kernel file and revision unchanged
compare_metadata == []
no schema/migration/index diff
no pyproject dependency diff
no uv.lock diff
41 mutations + 22 business reads unchanged
one Health operation; total HTTP 64
83 scenarios and 21 predicates unchanged
no CLI/packaging/S05 surface
obsolete Actions/payload material absent
```

---

# 10. Status, commits and publication

Work directly on `M2` and publish normally to `origin/M2`.

Recommended commit separation:

```text
1. corrective implementation and permanent tests
2. candidate evidence/status
3. optional final provenance-only commit when project discipline requires it
```

Do not create a PR.

Keep both S04 prompts in `wip/`.

Only when every mandatory gate passes may Codex update:

```text
M2-S04 — CANDIDATE READY FOR REVIEW
reviewer decision pending
M2-S05 — BLOCKED
```

Codex must never declare:

```text
M2-S04 — COMPLETED
M2-S05 — READY
```

Those transitions remain reviewer-owned.

If any mandatory test, real-PostgreSQL claim, installed-wheel target, exact-remote rerun or traceability target is incomplete, leave:

```text
M2-S04 — IN PROGRESS
```

or retain `REVIEW CHANGES REQUIRED`, record the exact blocker, and do not overstate readiness.

---

# 11. Required handoff

The final handoff must include:

## Publication

```text
branch
review baseline
review-fix prompt commit
corrective implementation commit
candidate evidence/status commit
optional provenance commit
local HEAD
origin/M2 HEAD
remote M2 HEAD
ahead/behind
working-tree state
PR/Actions statement
```

## Finding closure

For each finding, report concrete implementation and evidence:

```text
S04-RF-01
    Settings production failure boundary
    expected guard wrapper behavior
    cause/context suppression
    real factory/lifespan/Uvicorn diagnostic tests
    unexpected-defect negative control

S04-RF-02
    owned timeout discriminator
    inner TimeoutError service result
    inner TimeoutError HTTP result
    preserved outer timeout/pool-starvation behavior

S04-RF-03
    exact M2-VER-22 membership
    exact M2-VER-23 membership
    S04_REVIEW_FIX_TARGETS
    installed-wheel 200 -> 503 -> same-engine 200
```

## Verification

Report exact commands, counts, durations, environment versions, skip/xfail/rerun/warning census and SQLSTATE census.

## Unchanged boundaries

Report the schema, migration, dependency, route, scenario and predicate invariants listed above.

Do not state that no findings remain unless every completion condition in this prompt has actually been executed and is green.
