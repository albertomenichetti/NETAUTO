# Codex review-fix implementation prompt — M2-S07

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This prompt is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned state in `status.md`.

## Assignment

Close exactly:

```text
S07-RF-01 — installed Settings contract is incomplete in operator guidance
S07-RF-02 — primary bundle membership is incomplete against frozen obligations
```

Work directly on:

```text
branch M2
```

The reviewer-owned reopen baseline is:

```text
1558d5cd1a7125e5810d923274e5809852061214
docs(m2): reopen S07 for operating and evidence closure
```

That SHA is the required ancestry baseline, not the expected current HEAD: publication of this prompt necessarily creates a later commit. Start from the current clean `origin/M2` only when its ancestry contains `1558d5cd...`, this prompt exists, and `status.md` still marks S07 `REVIEW CHANGES REQUIRED` and S08 `BLOCKED`.

Relevant earlier history is preserved append-only:

```text
c8402a222c537ab6d874b0d7bdb2b4ec6d23f7f8
    S07 candidate evidence

a487e7c51c0b6ff0b15e1f3cfcb3702a9618f7ef
    superseded acceptance that opened S08 before the late findings were recorded
```

Do not reset, revert, rebase, amend, force-push or rewrite those commits.

Current authorization:

```text
M2-S00 ... M2-S06    reviewer-owned COMPLETED
M2-S07                REVIEW CHANGES REQUIRED
M2-S08                BLOCKED / not started
M2-S09                BLOCKED / not started
```

Deliver only:

```text
complete Linux/operator Settings documentation
installed Settings/default/invalid-boundary evidence
installed server independence from CLI evidence
installed no-401/403/no-security-scheme evidence
complete M2-VER-24 / 29 / 30 membership
permanent S07 review-fix traceability registry
full focused/T9/PostgreSQL/regression reruns
new exact-remote CANDIDATE READY FOR REVIEW handoff
```

Do not start S08. Do not create a PR, GitHub Action, tag, Release or published artifact. Do not commit wheels, `dist/`, virtual environments, generated certificates, secrets or temporary installation output.

---

# 1. Mandatory pre-flight

Re-read at minimum:

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

docs/milestones/M2/wip/M2-S07-review-fixes-codex-prompt.md
```

Inspect the retained candidate realization:

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
all tests/test_m2_s05_*.py
all tests/test_m2_s06_*.py
```

Confirm:

```text
checked-out branch                    M2
current HEAD                          current origin/M2 prompt-publication commit or later authorized S07 descendant
origin/M2 ancestry                    contains 1558d5cd1a7125e5810d923274e5809852061214
working tree                          clean
contract / architecture / steps      FINAL / FROZEN
M2-S07                                REVIEW CHANGES REQUIRED
M2-S08                                BLOCKED
relevant architecture reopen          none
TEST_DATABASE_URL                     present and valid
```

The wheel/install/T9 implementation is the starting realization, not a disposable prototype. Do not reimplement S07 from scratch.

Use only the externally supplied real PostgreSQL target. Do not provision PostgreSQL, invent credentials, use Docker/Testcontainers, substitute SQLite or silently fall back to localhost.

If frozen authority conflicts with this task, stop the affected point and report it. Do not alter frozen contract, architecture or steps to fit code.

---

# 2. Scope boundary

## In scope

```text
docs/milestones/M2/linux-operating-baseline.md
installed Settings inventory/default/validation evidence
installed server import/composition independence from netauto.cli
installed public-contract absence of 401/403/native security schemes
S07_PRIMARY_BUNDLE_TARGETS corrections
S07_REVIEW_FIX_TARGETS registry
obligation-specific traceability assertions
status/evidence for the corrected candidate
focused, T9, PostgreSQL, non-PG and full-suite reruns
```

## Out of scope

Do not change:

```text
M2-S08 or M2-S09 implementation
project version 0.2.0
third-party dependencies or lock records
runtime.pylock.toml dependency graph
migration 0001_m2_kernel or DDL
SQLAlchemy metadata, tables, constraints or indexes
business/Health routes, DTOs, statuses or errors
CLI grammar, commands, selectors, rendering or transport semantics
native auth/authorization
server TLS
runtime Settings inventory
host/port/workers ownership
installer/process-manager/migration-wrapper surface
Docker/Kubernetes/systemd/CI/CD assets
```

No production-code change is expected. If one becomes necessary, stop and explain why a documentation/test/traceability correction cannot satisfy the frozen requirement.

Preserve:

```text
version                          0.2.0
tables                           15
Alembic bases / heads            1 / 1
head                             0001_m2_kernel
compare_metadata                 []
business HTTP operations         63
Health operations                1
total public HTTP operations     64
CLI remote / local operations    63 / 8
registry examples                65
scenarios / predicates           83 / 21
```

---

# 3. `S07-RF-01` — Complete the installed Settings contract

Update:

```text
docs/milestones/M2/linux-operating-baseline.md
```

with one finite operator-facing inventory containing canonical environment name, required/default state, accepted domain, invalid boundaries, meaning and fail-fast consequence.

Required entries:

```text
NETAUTO_DATABASE_URL
    required
    complete SQLAlchemy URL
    exact driver postgresql+psycopg
    sole database transport/credential authority

NETAUTO_LOG_LEVEL
    default INFO
    CRITICAL | ERROR | WARNING | INFO | DEBUG

NETAUTO_POOL_SIZE
    default 10
    integer >= 1

NETAUTO_MAX_OVERFLOW
    default 20
    integer >= 0
    -1 / unlimited forbidden

NETAUTO_POOL_TIMEOUT
    default 5.0 seconds
    finite and > 0

NETAUTO_POOL_RECYCLE
    default disabled when omitted
    positive whole seconds when supplied

NETAUTO_POOL_PRE_PING
    default false
    boolean source value; canonical examples true | false
```

Make log-level behavior explicit in the canonical start procedure, preferably with:

```bash
NETAUTO_LOG_LEVEL=INFO
```

Keep the responsibility split exact:

```text
NETAUTO Settings
    database_url, log_level and pool fields

Uvicorn/deployment
    host, port and worker count
```

Do not add `NETAUTO_HOST`, `NETAUTO_PORT` or `NETAUTO_WORKERS`.

Document fail-fast distinctions:

```text
invalid Settings
    -> bootstrap failure before serving

schema mismatch
    -> startup-guard failure before serving

post-start DB failure
    -> process remains HTTP-capable; Health returns bounded 503
```

Retain protected secret handling, no URL on command line, explicit Alembic, and the capacity formula:

```text
workers * (pool_size + max_overflow)
```

## Installed evidence

Add an installed-wheel test, preferably:

```text
tests/test_m2_s07_linux.py::
    test_installed_settings_contract_matches_operator_guide_and_rejects_invalid_values
```

Use `s07_release.python` outside the checkout and prove:

```text
installed version == 0.2.0
Settings field set is exact
installed defaults are exact
guide contains every canonical environment name
guide defaults equal installed defaults
guide contains each validation boundary
canonical start makes log-level behavior explicit
host/port/workers are absent from Settings
```

Exercise representative installed invalid cases:

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

Requirements:

```text
no DB connection needed for Settings validation
bounded failure
no URL/password/sentinel leakage
no source-tree netauto import
```

Extend the existing guide-policy test; do not replace it with loose string checks.

---

# 4. `S07-RF-02` — Complete bundle membership

## `M2-VER-24`

Add these existing targets to `S07_PRIMARY_BUNDLE_TARGETS["M2-VER-24"]`:

```text
tests/test_m2_s07_alembic.py::
    test_installed_alembic_explicitly_realizes_exact_schema_without_cli_cross_action

tests/test_m2_s07_linux.py::
    test_installed_server_migration_start_health_cli_stop_restart_and_mismatch
```

Add one installed target, preferably:

```text
tests/test_m2_s07_distribution.py::
    test_installed_server_import_and_factory_are_independent_from_cli
```

It must run in the installed environment and:

```text
install an import guard rejecting netauto.cli and netauto.cli.*
import netauto.entrypoints.http
import Settings
build the FastAPI app from injected Settings without entering lifespan
verify expected public routes are constructible
verify no netauto.cli module loaded
perform no network/DB I/O
```

This proves the installed server does not depend on CLI; source grep alone is insufficient.

The complete M2-VER-24 union must prove wheel/version, outside-checkout install, installed CLI, explicit Alembic, unique graph, server start, no implicit cross-action and server/CLI independence.

## `M2-VER-29`

Add the new installed Settings/guide/default/validation target to:

```text
S07_PRIMARY_BUNDLE_TARGETS["M2-VER-29"]
```

The bundle must cover documented and executed build/install/configure/migrate/start/Health/stop/restart, Settings defaults/validation, release ownership/layout, protected secret, explicit migration, disposal, restart, capacity warning and no Git checkout.

## `M2-VER-30`

Add an installed target, preferably:

```text
tests/test_m2_s07_trust.py::
    test_installed_public_contract_has_no_401_403_or_security_scheme
```

Build/inspect the installed app without DB lifespan and prove:

```text
OpenAPI has no securitySchemes
no top-level or operation security requirement
no Authorization/header credential parameter
no documented 401 response
no documented 403 response
no login/logout/token/account/role route
no NETAUTO credential setting
```

Add these existing targets to `S07_PRIMARY_BUNDLE_TARGETS["M2-VER-30"]`:

```text
tests/test_m2_s07_linux.py::
    test_installed_server_migration_start_health_cli_stop_restart_and_mismatch

tests/test_m2_s07_linux.py::
    test_installed_worker_returns_complete_503_when_real_pg_transport_is_cut
```

They provide real process/Health secret non-leakage evidence. Retain the existing HTTPS, no-bypass, trust-boundary and artifact/config/argv targets.

Tests may belong to several bundles. Do not duplicate behavior merely to keep sets disjoint.

---

# 5. Permanent review-fix traceability

Add to `tests/test_m2_traceability.py`:

```text
S07_REVIEW_FIX_TARGETS = {
    "S07-RF-01": frozenset({...}),
    "S07-RF-02": frozenset({...}),
}
```

`S07-RF-01` must include at least:

```text
existing guide-policy target
new installed Settings/guide target
new review-fix traceability target
```

`S07-RF-02` must include at least:

```text
existing explicit Alembic target
existing installed server lifecycle target
existing real-PG transport-cut target
new server-no-CLI target
new no-401/403 target
new review-fix traceability target
```

Add a dedicated check, preferably:

```text
test_s07_review_fix_registry_and_complete_bundle_membership
```

It must assert:

```text
exact finding keys
every target exists and collects
finding targets belong to required bundle unions
M2-VER-24 contains explicit Alembic, lifecycle and server-no-CLI
M2-VER-29 contains installed Settings/guide validation
M2-VER-30 contains no-401/403, lifecycle secret output and transport-cut Health
S05 supporting M2-VER-24/30 remains present
installed support 22/23/25/26/27/28 remains present
M2-VER-31 and M2-VER-32 remain DESIGNED / S08-owned
every defined S07 test remains mapped to at least one S07 role
```

The existing “every S07 test appears somewhere” check may remain, but it does not replace obligation-specific membership assertions.

Do not create another traceability authority.

---

# 6. Artifact and dependency preservation

Verify without changing:

```text
pyproject / installed version      0.2.0
third-party uv.lock records        unchanged
runtime.pylock regeneration        byte-equal
runtime packages                   29 total / 27 applicable on Linux CPython
migration checksum                 unchanged
wheel logical member inventory     77 unless an explicitly justified package-source change occurs
```

Do not require the old wheel byte hash. Record the final actual filename, size, member count and SHA-256. Logical content and dependency graph must remain exact.

No artifact is committed or published.

---

# 7. Required verification

Run smallest affected evidence first and record exact counts/durations.

## Focused review-fix union

Run:

```text
new installed Settings/guide target
new server-no-CLI target
new no-401/403 target
existing guide-policy target
existing explicit Alembic target
existing server lifecycle target
existing real-PG transport-cut target
new review-fix traceability target
```

No skip or xfail.

## Complete bundles

Execute exact deduplicated unions:

```text
M2-VER-24
    S07 primary + S05 supporting

M2-VER-29
    S07 primary

M2-VER-30
    S07 primary + S05 supporting
```

Report selected, unique and passed counts.

Re-execute installed support for:

```text
M2-VER-22
M2-VER-23
M2-VER-25
M2-VER-26
M2-VER-27
M2-VER-28
```

Run complete:

```text
tests/test_m2_traceability.py
tests/test_m2_s07_distribution.py
tests/test_m2_s07_alembic.py
tests/test_m2_s07_linux.py
tests/test_m2_s07_trust.py
```

T9 must still prove wheel-only install, exact lock sync, `--no-deps`, installed Alembic, pre/post-migration startup, Health 200/503, business read, installed CLI/PTY, orderly disposal, restart, mismatch, real-PG transport cut, HTTPS matrix and secret absence.

Re-execute affected accepted boundaries:

```text
all S05
all S06
Settings/runtime/schema guard/Health
migration/schema metadata
M1/S00/M2 traceability
```

---

# 8. Quality and full gates

Run before publication:

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
focused review-fix union
complete M2-VER-24 / 29 / 30
installed support 22/23/25/26/27/28
complete S07/T9
complete PostgreSQL/concurrency gate
complete non-PostgreSQL gate
complete repository suite
```

Require:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative controls                only expected finite census
warning changes                  none unexplained
```

No generic flaky retry.

If any mandatory gate fails, keep S07 `REVIEW CHANGES REQUIRED` or `IN PROGRESS`, keep S08 blocked, and do not hand off a candidate.

---

# 9. Candidate publication

Only after all gates pass, update `status.md` to:

```text
M2-S07    CANDIDATE READY FOR REVIEW
M2-S08    BLOCKED
```

never `COMPLETED`.

Record:

```text
reopen baseline                  1558d5cd1a7125e5810d923274e5809852061214
implementation commit            actual SHA
evidence/status commit           actual SHA
closed findings                  S07-RF-01 / S07-RF-02
quality and test counts/durations
skip/xfail/rerun and SQLSTATE census
CPython/PostgreSQL/uv/Hatchling versions
wheel filename/size/members/SHA-256
runtime-lock size/packages/SHA-256
migration checksum
unchanged schema/API/CLI/dependency boundaries
```

Do not claim reviewer acceptance.

---

# 10. Commit, push and exact-remote rerun

Use ordinary commits on M2. Recommended separation:

```text
implementation/tests/docs correction
candidate evidence/status publication
```

Before committing, inspect status/diff and stage only S07 review-fix files. Never stage wheels, `dist/`, venvs, certificates, secrets or temporary output.

Push only to `origin/M2`, then verify:

```text
HEAD == origin/M2 == remote M2
working tree clean
ahead/behind 0/0
no PR / Action / tag / Release / artifact publication
```

On the exact remote HEAD rerun at least:

```text
runtime-lock equality
focused review-fix union
complete M2-VER-24 / 29 / 30
complete S07/T9
M2 traceability
PostgreSQL/concurrency
non-PostgreSQL
complete repository suite
```

If post-push evidence fails, append a corrective commit and return S07 to `IN PROGRESS` or `REVIEW CHANGES REQUIRED`; do not hand off.

---

# 11. Completion report

Report verified facts only:

```text
branch and starting ancestry
implementation/evidence commits
HEAD/origin/remote equality
ahead/behind and clean worktree
files changed
closure of both findings
focused/bundle/T9/full results
skip/xfail/rerun and SQLSTATE census
final wheel/runtime-lock facts
unchanged boundaries
S08 blocked
absence of PR/Actions/tag/Release/artifact publication
```

The only successful implementer state is:

```text
M2-S07    CANDIDATE READY FOR REVIEW
M2-S08    BLOCKED
```

`COMPLETED` remains reviewer-owned.
