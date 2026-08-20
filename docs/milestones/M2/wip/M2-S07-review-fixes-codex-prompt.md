# Codex review-fix implementation prompt — M2-S07

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Close exactly the bounded M2-S07 review findings:

```text
S07-RF-01 — installed Settings contract is incomplete in operator guidance
S07-RF-02 — primary bundle membership is incomplete against frozen obligations
```

Work directly on branch:

```text
M2
```

The exact reviewer-owned starting baseline is:

```text
1558d5cd1a7125e5810d923274e5809852061214
docs(m2): reopen S07 for operating and evidence closure
```

This baseline is intentionally later than:

```text
c8402a222c537ab6d874b0d7bdb2b4ec6d23f7f8
    S07 candidate evidence

a487e7c51c0b6ff0b15e1f3cfcb3702a9618f7ef
    superseded acceptance that opened S08 before the late findings were recorded
```

Do not reset, revert, rebase, force-push or rewrite either commit. Preserve the append-only history and continue from `1558d5cd...`.

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    reviewer-owned COMPLETED
M2-S04    reviewer-owned COMPLETED
M2-S05    reviewer-owned COMPLETED
M2-S06    reviewer-owned COMPLETED
M2-S07    REVIEW CHANGES REQUIRED
M2-S08    BLOCKED / not started
M2-S09    BLOCKED / not started
```

Deliver only:

```text
complete Linux/operator Settings documentation
installed Settings/default/invalid-boundary evidence
installed server independence from CLI evidence
installed no-401/403/no-security-scheme evidence
complete M2-VER-24 / 29 / 30 target membership
permanent S07 review-fix traceability registry
full focused/T9/PostgreSQL/regression re-execution
new exact-remote CANDIDATE READY FOR REVIEW handoff
```

Do not start `M2-S08`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag, publish a GitHub Release or upload an artifact. Do not add or use GitHub Actions, Docker, Testcontainers, systemd, encoded patches, workflow-dispatched implementation or artifact-mediated source publication.

The built wheel remains verification output. Do not commit `dist/`, virtual environments, extracted target environments, generated certificates, database secrets or other test/install by-products.

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
docs/architecture/persistence.md
docs/architecture/verification.md

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

docs/general/technology_baseline.md
    STACK-01
    STACK-02
    STACK-04
    STACK-05
    STACK-06
    STACK-07
    STACK-08
    STACK-09
    STACK-10

docs/milestones/M2/wip/M2-S07-review-fixes-codex-prompt.md
```

Historical S07 implementation authority remains in the frozen owners and repository history. The retired original prompt may be inspected at commit:

```text
bf498153c458f585cd1a6914a9ac4aa904ebd34c
```

only as an execution cross-check. It is not restored as a second current prompt.

Confirm before changing anything:

```text
checked-out branch                    M2
HEAD                                  1558d5cd1a7125e5810d923274e5809852061214
origin/M2                             same commit
working tree                          clean
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S07                                REVIEW CHANGES REQUIRED
M2-S08                                BLOCKED
relevant architecture reopen          none
TEST_DATABASE_URL                     present and valid
```

Inspect the retained S07 realization and evidence before editing:

```text
pyproject.toml
uv.lock
src/netauto/release/runtime.pylock.toml
src/netauto/settings.py
src/netauto/entrypoints/http.py
src/netauto/migrations/env.py
src/netauto/runtime/schema_guard.py

docs/milestones/M2/linux-operating-baseline.md

tests/support/s07_release.py
tests/test_m2_s07_distribution.py
tests/test_m2_s07_alembic.py
tests/test_m2_s07_linux.py
tests/test_m2_s07_trust.py
tests/test_m2_traceability.py

tests/test_settings.py
tests/test_m2_s04_installed.py
tests/test_m2_s05_installed.py
all tests/test_m2_s05_*.py
all tests/test_m2_s06_*.py
```

The candidate wheel/install/T9 implementation is the starting realization, not a disposable prototype. Do not reimplement S07 from scratch.

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` is mandatory for the T9, PostgreSQL/concurrency and full repository gates. Do not provision PostgreSQL, invent credentials, use Docker/Testcontainers, substitute SQLite or silently fall back to localhost.

If repository state or a frozen authority conflicts with this prompt, stop the affected point and report it. Do not modify frozen contract, architecture or steps to fit convenient code.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
docs/milestones/M2/linux-operating-baseline.md
installed Settings inventory/default/validation evidence
installed server import/composition independence from netauto.cli
installed public-contract absence of 401/403/native security schemes
S07_PRIMARY_BUNDLE_TARGETS membership corrections
S07_REVIEW_FIX_TARGETS permanent registry
traceability assertions for exact required cross-membership
status/evidence update for the corrected candidate
focused, T9, PostgreSQL, non-PG and full-suite reruns
```

Narrow test-only helpers may be added where they make installed-wheel evidence explicit and deterministic.

## 2.2 Out of scope

Do not introduce or change:

```text
M2-S08 integrated regression/delta-allowlist work
M2-S09 final acceptance or delivery
project version 0.2.0
third-party dependency versions, sources, markers or hashes
uv.lock third-party records
runtime.pylock.toml dependency graph
wheel public/runtime content except unavoidable metadata consequences of an actual source change
migration revision 0001_m2_kernel
migration DDL
SQLAlchemy metadata
schema, tables, constraints or indexes
business or Health routes
request/response DTOs
HTTP statuses or error taxonomy
CLI grammar, registry, selectors, state machine, output or transport semantics
native authentication or authorization
server TLS or certificate lifecycle
new runtime settings
NETAUTO host/port/workers settings
installer, process manager, migration wrapper or deployment CLI
Docker/Kubernetes/systemd/CI/CD assets
```

No production-code change is expected. If one appears necessary, stop and explain why the documentation/test/traceability-only correction cannot satisfy the frozen requirement.

Preserve exactly:

```text
project version                  0.2.0
authoritative tables             15
Alembic base / head              1 / 1
head                             0001_m2_kernel
compare_metadata                 []
business HTTP operations         41 mutations + 22 reads = 63
Health operations                1
total public HTTP operations     64
CLI remote / local operations    63 / 8
registry examples                65
canonical scenarios              83
safety predicates                21
native auth / server TLS         absent
```

---

# 3. `S07-RF-01` — Complete installed Settings contract in the Linux guide

## 3.1 Operator-facing inventory

Add one explicit, finite Settings inventory to:

```text
docs/milestones/M2/linux-operating-baseline.md
```

For every installed application setting, document:

```text
canonical environment name
whether it is required
its default when optional
its accepted value domain
its invalid boundaries
its operational meaning
its fail-fast consequence
```

The required inventory is:

### `NETAUTO_DATABASE_URL`

```text
required
complete SQLAlchemy URL
exact driver postgresql+psycopg
contains the complete PostgreSQL transport/credential policy
no split host/port/database/user/password/TLS settings
missing or invalid value rejects migration/server startup
```

The recommended production source remains the protected file selected by:

```text
NETAUTO_SECRETS_DIR=/opt/netauto/secrets
/opt/netauto/secrets/NETAUTO_DATABASE_URL
```

Do not put the URL on the Alembic/Uvicorn command line or in `alembic.ini`.

### `NETAUTO_LOG_LEVEL`

```text
default INFO
allowed CRITICAL | ERROR | WARNING | INFO | DEBUG
other values invalid
```

Make log-level behavior explicit in the canonical start procedure. Prefer including:

```bash
NETAUTO_LOG_LEVEL=INFO
```

in the canonical start command so the documented baseline is unambiguous. An equivalent explicit statement tied directly to that command is acceptable only if permanent evidence makes the relationship exact.

### `NETAUTO_POOL_SIZE`

```text
default 10
integer >= 1
0 invalid
```

### `NETAUTO_MAX_OVERFLOW`

```text
default 20
integer >= 0
-1 / unlimited invalid
```

### `NETAUTO_POOL_TIMEOUT`

```text
default 5.0 seconds
finite numeric value > 0
0, negative, NaN and infinity invalid
```

### `NETAUTO_POOL_RECYCLE`

```text
default disabled when omitted
positive whole seconds when supplied
0 and negative invalid
```

### `NETAUTO_POOL_PRE_PING`

```text
default false
boolean source value
canonical examples true | false
```

## 3.2 Responsibility split

Keep the distinction explicit:

```text
NETAUTO Settings
    -> database_url
    -> log_level
    -> pool_size
    -> max_overflow
    -> pool_timeout
    -> pool_recycle
    -> pool_pre_ping

Uvicorn/deployment settings
    -> bind host
    -> bind port
    -> worker count
```

Do not introduce `NETAUTO_HOST`, `NETAUTO_PORT` or `NETAUTO_WORKERS`.

Retain and connect the capacity formula to the documented pool values:

```text
workers * (pool_size + max_overflow)
```

The Alembic administrative connection remains a separate `NullPool` connection and is not counted as a worker pool slot.

## 3.3 Fail-fast behavior

Document that invalid/missing Settings fail before serving. Distinguish:

```text
invalid Settings
    -> process/bootstrap failure before serving

schema mismatch
    -> startup guard failure before serving

post-start PostgreSQL failure
    -> process remains HTTP-capable, Health returns bounded 503
```

Do not imply automatic repair, fallback, migration or profile selection.

## 3.4 Installed Settings evidence

Add one explicit installed-wheel test, preferably:

```text
tests/test_m2_s07_linux.py::
    test_installed_settings_contract_matches_operator_guide_and_rejects_invalid_values
```

An equivalent exact name is acceptable if every registry is updated coherently.

The test must execute through `s07_release.python`, outside the repository import path, and prove at least:

```text
installed distribution version == 0.2.0
Settings field set is exact
installed defaults are exact
operator guide contains every canonical environment name
operator guide defaults equal installed defaults
operator guide contains the exact validation boundaries
canonical start makes log-level behavior explicit
host/port/workers remain external to Settings
```

Exercise representative invalid values from the installed environment/model:

```text
missing database_url
wrong database driver
invalid log level
pool_size = 0
max_overflow = -1
pool_timeout = 0
pool_timeout = infinity
pool_recycle = 0
invalid pool_pre_ping source value
```

The evidence may use several installed subprocess probes, one bounded installed script or a tightly controlled combination. It must not import source-tree `netauto`.

Requirements:

```text
no PostgreSQL connection is required merely to validate Settings
invalid configuration returns a bounded failure
no database URL, password or sentinel reaches normal output
no test rewrites the installed application
```

Retain the existing operator-document negative checks and extend them rather than replacing them with a loose prose assertion.

---

# 4. `S07-RF-02` — Complete primary evidence-bundle membership

The concrete behavior largely exists. Correct ownership and add only the missing explicit evidence.

## 4.1 `M2-VER-24` — One versioned distribution

The complete primary/supporting union must prove:

```text
one wheel contains server, CLI and Alembic
one release version
outside-checkout installation
installed CLI invocation
installed explicit Alembic
installed unique-head discovery
installed server start/lifecycle
installation/CLI/startup do not implicitly execute one another
server does not depend on CLI
```

Add these existing targets to:

```text
S07_PRIMARY_BUNDLE_TARGETS["M2-VER-24"]
```

```text
tests/test_m2_s07_alembic.py::
    test_installed_alembic_explicitly_realizes_exact_schema_without_cli_cross_action

tests/test_m2_s07_linux.py::
    test_installed_server_migration_start_health_cli_stop_restart_and_mismatch
```

Add one new installed target, preferably:

```text
tests/test_m2_s07_distribution.py::
    test_installed_server_import_and_factory_are_independent_from_cli
```

This test must use the installed release only and make `netauto.cli` unavailable before importing the server path. A suitable realization is an installed subprocess that:

```text
installs a meta-path/import guard rejecting netauto.cli and netauto.cli.*
imports netauto.entrypoints.http
imports Settings
builds the FastAPI application from injected Settings without entering lifespan
verifies the expected public route inventory is constructible
verifies no netauto.cli module was loaded
performs no network or database I/O
```

Do not satisfy server independence by merely grepping one source file. The evidence must prove the installed import/composition path.

The server-independence target belongs to `M2-VER-24`, not to a new bundle.

## 4.2 `M2-VER-29` — Linux operating procedure

Add the installed Settings/guide target from `S07-RF-01` to:

```text
S07_PRIMARY_BUNDLE_TARGETS["M2-VER-29"]
```

The complete M2-VER-29 primary target set must then cover:

```text
documented build/install/configure/migrate/start/stop/restart/Health
installed Settings defaults and invalid boundaries
release layout and ownership
protected secret procedure
explicit installed migration
startup before/after migration
Health 200 and 503
representative business read
orderly shutdown and disposal
fresh restart
no Git checkout
capacity formula
```

Do not move M2-VER-29 ownership to S08.

## 4.3 `M2-VER-30` — Trust and transport boundary

Add one explicit installed public-contract target, preferably:

```text
tests/test_m2_s07_trust.py::
    test_installed_public_contract_has_no_401_403_or_security_scheme
```

It must build/inspect the installed application without entering database lifespan and prove a finite absence contract:

```text
OpenAPI has no securitySchemes
no top-level or operation-level security requirement
no Authorization/header credential parameter
no documented 401 response
no documented 403 response
no native login/logout/token/account/role route
no NETAUTO credential setting
```

Use the installed wheel environment outside checkout. Do not infer absence only from current test names.

Add the following existing real installed-process targets to:

```text
S07_PRIMARY_BUNDLE_TARGETS["M2-VER-30"]
```

```text
tests/test_m2_s07_linux.py::
    test_installed_server_migration_start_health_cli_stop_restart_and_mismatch

tests/test_m2_s07_linux.py::
    test_installed_worker_returns_complete_503_when_real_pg_transport_is_cut
```

These targets already prove process/Health behavior using a unique database sentinel. Their M2-VER-30 membership must make the secret/logging/Health non-leakage obligation explicit.

Retain the existing M2-VER-30 targets for:

```text
operator guide trust boundary
HTTPS trusted CA + matching hostname
untrusted CA failure
hostname mismatch failure
no insecure/skip-verify surface
no credentials/userinfo/settings expansion
no secret in artifact/config/argv
```

Tests may belong to several bundles. Do not duplicate behavior merely to keep target sets disjoint.

---

# 5. Permanent S07 review-fix registry

Extend `tests/test_m2_traceability.py` with one permanent registry:

```text
S07_REVIEW_FIX_TARGETS: dict[str, frozenset[str]] = {
    "S07-RF-01": frozenset({...}),
    "S07-RF-02": frozenset({...}),
}
```

The exact contents must include the concrete targets that close each finding.

At minimum, `S07-RF-01` includes:

```text
existing Linux operator-document policy target
new installed Settings/guide/default/validation target
new S07 review-fix traceability target
```

At minimum, `S07-RF-02` includes:

```text
existing explicit installed Alembic target
existing installed server lifecycle target
existing real-PG transport-cut target
new installed server-no-CLI target
new installed no-401/403/no-security-scheme target
new S07 review-fix traceability target
```

Add a dedicated machine check, preferably:

```text
tests/test_m2_traceability.py::
    test_s07_review_fix_registry_and_complete_bundle_membership
```

It must assert:

```text
finding keys are exactly S07-RF-01 and S07-RF-02
every target exists and is collected
every finding target belongs to the appropriate complete bundle union
M2-VER-24 contains explicit Alembic, installed server lifecycle and server-no-CLI
M2-VER-29 contains installed Settings/guide/default/validation
M2-VER-30 contains no-401/403, lifecycle secret output and transport-cut Health
S05 supporting M2-VER-24/30 membership remains present
S07 installed support for M2-VER-22/23/25/26/27/28 remains present
M2-VER-31 and M2-VER-32 remain DESIGNED / S08-owned
every defined S07 test remains mapped to at least one declared S07 role
```

The current global assertion that every `test_m2_s07_*` target appears somewhere may remain, but it is not a substitute for these obligation-specific cross-membership assertions.

Do not create a second traceability authority outside `tests/test_m2_traceability.py`.

---

# 6. Preserve the candidate artifact boundary

No dependency or runtime package change is authorized.

Verify:

```text
pyproject version                 0.2.0
uv.lock project version          0.2.0
third-party uv.lock records       unchanged
runtime.pylock.toml bytes         regenerated equality
runtime package census            29 total / 27 applicable on Linux CPython
wheel member inventory            77 logical members unless a justified package source change occurs
migration checksum                unchanged
```

Do not hard-code that a rebuilt wheel must have the old byte SHA-256. Build archives may differ in non-semantic bytes. Record the actual final candidate:

```text
wheel filename
wheel size
wheel member count
wheel SHA-256
runtime lock size
runtime lock SHA-256
```

Logical wheel content, installed behavior and dependency graph must remain exact.

No wheel is committed, tagged, uploaded or released.

---

# 7. Required focused verification

Run the smallest affected evidence first. Record exact selected/collected/pass counts and durations.

## 7.1 Review-fix focused targets

Run at least:

```text
new installed Settings/guide target
new installed server-no-CLI target
new installed no-401/403/no-security-scheme target
existing Linux operator-document target
existing explicit installed Alembic target
existing installed server lifecycle target
existing real-PG transport-cut target
new S07 review-fix registry target
```

No focused target may be skipped or xfailed.

## 7.2 Complete `M2-VER-24`

Execute the exact complete union from:

```text
S07_PRIMARY_BUNDLE_TARGETS["M2-VER-24"]
S05_SUPPORTING_BUNDLE_TARGETS["M2-VER-24"]
```

Report selected, unique and passed counts. Deduplicate targets before execution.

## 7.3 Complete `M2-VER-29`

Execute the exact complete primary set from:

```text
S07_PRIMARY_BUNDLE_TARGETS["M2-VER-29"]
```

It must include the new installed Settings/guide target.

## 7.4 Complete `M2-VER-30`

Execute the exact complete union from:

```text
S07_PRIMARY_BUNDLE_TARGETS["M2-VER-30"]
S05_SUPPORTING_BUNDLE_TARGETS["M2-VER-30"]
```

It must include the new no-401/403 target and the existing real installed lifecycle/transport-cut targets.

## 7.5 Installed supporting bundles

Re-execute all installed S07 support for:

```text
M2-VER-22
M2-VER-23
M2-VER-25
M2-VER-26
M2-VER-27
M2-VER-28
```

Do not transfer primary ownership.

## 7.6 Traceability

Run:

```text
tests/test_m2_traceability.py
```

Require all targets to exist and collect. `M2-VER-31` and `M2-VER-32` must remain S08-owned and `DESIGNED`.

---

# 8. T9 and cross-boundary verification

Run the complete S07 installed-artifact suite:

```text
tests/test_m2_s07_distribution.py
tests/test_m2_s07_alembic.py
tests/test_m2_s07_linux.py
tests/test_m2_s07_trust.py
```

The T9 sequence must still prove:

```text
wheel-only installation outside checkout
exact runtime-lock sync
wheel install --no-deps
installed package/resource roots
explicit Alembic downgrade/upgrade
startup before migration rejected
startup after migration accepted
Health 200
business read
installed non-interactive CLI
installed interactive PTY
orderly stop and session disposal
fresh restart and new guard
controlled revision mismatch rejection
real-PG transport cut and complete Health 503
HTTPS trusted/untrusted/hostname mismatch
secret absence from artifact/config/argv/logging/Health/CLI
```

Use the external real PostgreSQL target. Restore every destructive test state.

Re-execute affected accepted boundaries:

```text
all M2-S05 tests
all M2-S06 tests
Settings / runtime / schema guard / Health
migration and schema metadata
M1 / S00 / M2 traceability
```

---

# 9. Mandatory quality and repository gates

Run on the final implementation state before publication:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Then run:

```text
focused review-fix targets
complete M2-VER-24
complete M2-VER-29
complete M2-VER-30
installed support M2-VER-22/23/25/26/27/28
complete S07/T9 suite
complete PostgreSQL/concurrency gate
complete non-PostgreSQL gate
complete repository suite
```

Normative requirements:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative-control SQLSTATEs       only the finite expected census
warning changes                  none unexplained
```

Do not use a generic retry mechanism to hide a failed test. A rerun may be used diagnostically only after preserving the original failure and identifying the cause; final candidate evidence must come from a clean required run.

If any required gate fails, keep:

```text
M2-S07    REVIEW CHANGES REQUIRED or IN PROGRESS
M2-S08    BLOCKED
```

and do not publish a candidate-ready handoff.

---

# 10. Status and evidence handoff

Only after every mandatory gate passes, update:

```text
docs/milestones/M2/status.md
```

to:

```text
M2-S07 — CANDIDATE READY FOR REVIEW
```

not `COMPLETED`.

The candidate record must include:

```text
reviewer reopen baseline          1558d5cd1a7125e5810d923274e5809852061214
corrective implementation commit  <actual SHA>
evidence/status commit            <actual SHA or this commit>
closed findings                    S07-RF-01 / S07-RF-02
M2-S08                             BLOCKED / not started
```

Record exact:

```text
quality commands and results
pytest collection count
focused finding counts
M2-VER-24 / 29 / 30 complete counts
installed support count
T9 count and duration
PostgreSQL/concurrency count and duration
non-PostgreSQL count and duration
full-suite count and duration
skip/xfail/rerun census
warning census
SQLSTATE census
CPython / PostgreSQL / uv / Hatchling versions
wheel filename / size / members / SHA-256
runtime lock size / package census / SHA-256
migration checksum
```

Do not claim reviewer acceptance.

---

# 11. Commit, push and exact-remote verification

Use ordinary Git commits on `M2`.

Recommended separation:

```text
implementation/test/docs correction
    -> one coherent commit

evidence/status candidate publication
    -> one later commit after successful pre-push gates
```

Do not amend or rewrite published commits.

Before each commit:

```text
inspect git status
inspect exact staged paths
stage only S07 review-fix files
verify no wheel, dist, venv, cert, secret or temp output is staged
```

Push only to:

```text
origin/M2
```

After push, verify:

```text
HEAD == origin/M2 == remote M2
working tree clean
ahead/behind 0/0
no PR
no GitHub Actions
no tag or Release
no committed artifact
```

Then re-execute on the exact remote HEAD at minimum:

```text
runtime-lock regeneration equality
focused S07 review-fix union
complete M2-VER-24 / 29 / 30 union
complete S07/T9
M2 traceability
PostgreSQL/concurrency
non-PostgreSQL
complete repository suite
```

If an exact-remote post-push gate fails, append a corrective commit, return status to `IN PROGRESS` or `REVIEW CHANGES REQUIRED`, and do not hand off the candidate.

---

# 12. Completion report format

Report only verified facts.

Include:

```text
branch
starting baseline
implementation commit
candidate evidence/status commit
HEAD/origin/remote equality
ahead/behind
working-tree state
files changed
closed S07-RF-01 / S07-RF-02 details
quality results
focused and complete bundle counts
T9/PostgreSQL/non-PG/full-suite results
SQLSTATE and skip/xfail/rerun census
final artifact and runtime-lock facts
unchanged schema/API/CLI/dependency boundaries
M2-S08 blocked confirmation
absence of PR/Actions/tag/Release/artifact publication
```

The only valid successful implementer state is:

```text
M2-S07    CANDIDATE READY FOR REVIEW
M2-S08    BLOCKED
```

Reviewer ownership remains required for `COMPLETED`.
