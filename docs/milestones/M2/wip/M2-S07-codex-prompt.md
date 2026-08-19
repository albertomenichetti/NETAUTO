# Codex implementation prompt — M2-S07

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, and the reviewer-owned operational state in `status.md`.

## Assignment

Implement exactly:

```text
M2-S07 — Versioned wheel, installed Alembic and Linux operating baseline
```

Work directly on branch:

```text
M2
```

The reviewer-owned starting baseline is:

```text
b105e774765e7d8a2c68ab14501cfd6043eadf13
docs(m2): accept S06 and open S07
```

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    reviewer-owned COMPLETED
M2-S03    reviewer-owned COMPLETED
M2-S04    reviewer-owned COMPLETED
M2-S05    reviewer-owned COMPLETED
M2-S06    reviewer-owned COMPLETED
M2-S07    READY
M2-S08    BLOCKED
M2-S09    BLOCKED
```

Deliver the complete vertically coherent S07 capability:

```text
one intentional M2 release version: 0.2.0
one canonical netauto-0.2.0-py3-none-any.whl
server, official CLI, neutral DTOs and complete Alembic graph in that wheel
one embedded PEP 751 runtime lock generated from the committed uv.lock
clean dependency synchronization from the extracted embedded lock
final wheel installation with --no-deps
installed unique-base / unique-head Alembic discovery
explicit installed Alembic upgrade head outside the repository checkout
no automatic migration during install, CLI invocation or server startup
one durable manual Linux operating document
one executed Linux install/configure/migrate/start/Health/stop/restart procedure
installed startup mismatch and post-start DB-unready evidence
installed interactive and non-interactive CLI evidence
installed HTTPS trusted/untrusted/hostname-mismatch evidence
secret, trust-boundary, bind-policy and connection-capacity evidence
M2-VER-24 / M2-VER-29 / M2-VER-30 primary evidence
installed-artifact support for M2-VER-22 / 23 / 25 / 26 / 27 / 28
preservation of every accepted S00-S06 behavior and boundary
```

Do not start `M2-S08`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag, publish a GitHub Release or upload a release artifact. Do not add or use GitHub Actions, Docker, Testcontainers, systemd, encoded patches, workflow-dispatched implementation or artifact-mediated source publication.

The built candidate wheel is verification output. Do not commit `dist/`, virtual environments, extracted target environments, generated test secrets or other installation by-products.

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

docs/milestones/M2/wip/M2-S07-codex-prompt.md
```

Historical discovery material may be inspected only as a cross-check and never as authority, including:

```text
docs/milestones/M2/wip/runtime-configuration-production-deployment.md
```

The FINAL/FROZEN contract, architecture set, `steps.md`, `status.md` and ratified technology baseline supersede WIP wording wherever they differ.

Confirm from the repository that:

```text
checked-out branch                    M2
origin/M2 ancestry                    includes b105e774...
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
M2-S06                                reviewer-owned COMPLETED
M2-S07                                READY or IN PROGRESS
M2-S08                                BLOCKED
relevant architecture reopen          none
STACK-08 / STACK-09 / STACK-10         RATIFIED
```

Inspect the completed implementation before choosing any decomposition. At minimum inspect:

```text
pyproject.toml
uv.lock
.python-version
.gitignore
alembic.ini

src/netauto/__init__.py
src/netauto/settings.py
src/netauto/runtime/engine.py
src/netauto/runtime/context.py
src/netauto/runtime/schema_guard.py
src/netauto/entrypoints/http.py
src/netauto/health.py
src/netauto/cli/
src/netauto/transport/http/
src/netauto/migrations/__init__.py
src/netauto/migrations/env.py
src/netauto/migrations/script.py.mako
src/netauto/migrations/versions/__init__.py
src/netauto/migrations/versions/0001_m2_durable_kernel.py

tests/test_settings.py
tests/test_runtime_engine.py
tests/test_runtime_schema_guard.py
tests/test_http_composition.py
tests/test_bootstrap_diagnostics.py
tests/test_health.py
tests/test_health_probe.py
tests/test_health_api.py
tests/test_health_postgresql.py
tests/test_m2_s04_installed.py

tests/test_m2_s05_installed.py
all tests/test_m2_s05_*.py
all tests/test_m2_s06_*.py

tests/test_migrations.py
tests/test_schema_metadata.py
tests/test_m2_traceability.py
```

The existing installed migration package, exact startup guard, Health implementation, CLI and migration DDL are accepted starting realizations. S07 packages and operates them; it does not redesign them.

A real externally supplied PostgreSQL target through `TEST_DATABASE_URL` is mandatory for the installed migration, startup, Health and complete repository gates. Do not provision PostgreSQL, invent credentials, use Docker/Testcontainers, substitute SQLite or silently fall back to localhost.

The T9 harness may use disposable paths equivalent to `/opt/netauto` and may reset an explicitly isolated test database through existing repository fixtures or permissions supplied by the external target. It must not stop or reconfigure a shared PostgreSQL server. Every destructive database step must be isolated, restored or cleaned before the test ends.

If repository state or a frozen authority conflicts with this task, stop the affected point and report it. Do not modify frozen contract, architecture or steps to fit convenient code.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
project release version 0.2.0
coherent pyproject.toml / uv.lock local-project version update
src/netauto/release/__init__.py
src/netauto/release/runtime.pylock.toml
normal Hatchling package-data realization where required
one versioned application wheel
wheel content, metadata and entrypoint inspection
runtime-lock regeneration/equality verification
clean wheel-only release environment synchronization and installation
installed netauto:migrations package-resource operation
operator-owned minimal non-secret alembic.ini
explicit installed Alembic migration on real PostgreSQL
installed unique shipped-head discovery
installed Uvicorn startup guard / Health / shutdown / restart
installed official CLI interactive and non-interactive operation
controlled installed CLI HTTPS verification matrix
manual Linux operating documentation
T9 subprocess / PTY / real-PostgreSQL evidence
M2-VER-24 / 29 / 30 traceability and evidence
installed-artifact support for M2-VER-22 / 23 / 25 / 26 / 27 / 28
```

## 2.2 Out of scope

Do not introduce or expose:

```text
M2-S08 integrated final traceability/negative-surface closure
M2-S09 final acceptance, final wheel gate or milestone delivery
Git tag, GitHub Release, package-index publication or artifact upload
artifact transfer automation or registry policy
wheel signing, SBOM or vulnerability-management policy
vendored third-party wheels or an offline wheelhouse
Docker, Compose, Kubernetes or container manifests
systemd units, daemonization, PID files or process supervision
start-at-boot or automatic restart policy
CI/CD or GitHub Actions
rolling, blue/green, canary or zero-downtime upgrade
application/schema rollback procedure
backup/restore/disaster-recovery automation
native authentication, authorization, accounts, roles, 401 or 403 semantics
native server TLS, certificate/private-key settings or certificate lifecycle
NETAUTO process-manager, server wrapper or migration wrapper command
`netauto migrate` or a second migration entrypoint
startup migration, stamp, repair or schema endpoint
new application settings for host, port or worker count
new database host/port/user/password/TLS settings outside database_url
new CLI command, option, credential/profile or insecure verification bypass
new API route, DTO field, business behavior or error code
schema, migration DDL, table, constraint or index change
new Alembic revision or revision-ID change
cross-release CLI/server compatibility negotiation
persistent CLI history/profile/configuration
```

Preserve exactly unless this slice explicitly authorizes release packaging metadata:

```text
15 authoritative tables
one Alembic base / one Alembic head
root revision ID 0001_m2_kernel
root revision filename 0001_m2_durable_kernel.py
root revision DDL content
compare_metadata == []
41 mutations + 22 reads = 63 business HTTP operations
1 GET /health/core operational operation
64 total public server HTTP operations
63 exact remote CLI CommandSpec values
8 exact local CLI commands
CLI family census 14 / 16 / 13 / 14 / 5 / 1
65 parser-valid registry examples
9 FORMATTED enrichment entry points
83 concurrency scenarios
21 safety predicates
three advisory gates
four row-lock modes
completed Settings/startup/Health behavior
completed non-interactive and interactive CLI behavior
```

The only dependency-authority changes authorized by S07 are:

```text
project version 0.1.0 -> 0.2.0
uv.lock local NETAUTO project metadata aligned to 0.2.0
committed generated runtime.pylock.toml exported from that locked runtime graph
```

Do not upgrade or add third-party dependencies.

---

# 3. Release version and metadata

Set the M2 release version exactly to:

```text
0.2.0
```

This is the intentional S07-owned successor to the delivered/current `0.1.0` distribution.

Update coherently:

```text
pyproject.toml [project].version
uv.lock local netauto project record
wheel filename
wheel METADATA Version
installed importlib.metadata.version("netauto")
reference release directory in operator documentation
evidence records
```

The canonical wheel filename is:

```text
netauto-0.2.0-py3-none-any.whl
```

Requirements:

```text
one distribution version authority = installed package metadata
no handwritten independent __version__ constant
no server, CLI or migration sub-version
no public version endpoint
no version environment variable
no release tag or GitHub Release
```

A convenience `netauto.__version__` is unnecessary. If retained or introduced for a concrete installed use, it must derive from `importlib.metadata` and never become a second authority.

Use normal lock maintenance for the local version change:

```text
uv lock
uv lock --check
```

Inspect the lock diff. No third-party package version, source, marker or hash change is authorized. If `uv lock` proposes unrelated resolution changes, diagnose and stop rather than accepting them silently.

Permanent evidence must correlate at least:

```text
wheel basename
METADATA Version
installed distribution version
netauto console User-Agent release component
installed server/CLI/migrations package roots
release-directory version
```

Do not add a business/API version negotiation surface merely to prove common packaging.

---

# 4. Exact embedded runtime dependency lock

## 4.1 Canonical resource

Create the installed package resource:

```text
src/netauto/release/__init__.py
src/netauto/release/runtime.pylock.toml
```

`runtime.pylock.toml` is generated evidence beneath `uv.lock`, not a hand-edited dependency authority.

Generate it from the committed candidate lock with the architecture-owned semantics:

```text
uv export \
    --frozen \
    --no-dev \
    --no-emit-project \
    --format pylock.toml \
    --output-file src/netauto/release/runtime.pylock.toml
```

If the installed `uv` version requires a syntax-equivalent spelling, record the exact command and prove equivalent output semantics. Do not weaken any option.

The file must contain:

```text
all transitive runtime dependencies
exact package versions
applicable environment markers
artifact URLs/source descriptors as emitted by uv
artifact hashes required by the PEP 751 export
```

It must contain no:

```text
dev dependency group
pytest / Ruff / Pyright / Hypothesis / coverage / xdist / pytest-timeout
local NETAUTO project entry
editable or source-checkout reference
repository absolute path
credential or private index token
operator secret
manual compatibility range in place of exact resolution
```

## 4.2 Regeneration equality

Permanent verification must regenerate into a separate temporary file with `--frozen` and require byte-for-byte equality with the committed package resource.

At candidate handoff report:

```text
runtime lock path
runtime lock byte size
runtime lock SHA-256
exact uv export command
runtime package count
absence of project/dev entries
```

Do not claim that `runtime.pylock.toml` replaces `uv.lock`. Repository development continues to use committed `uv.lock`; the embedded pylock owns exact installed-runtime synchronization only.

## 4.3 Wheel inclusion

Prove the built wheel contains exactly one:

```text
netauto/release/runtime.pylock.toml
```

and that its bytes equal the committed source resource.

Use standard package-resource or `zipfile` access for inspection. Do not copy the lock into a second source authority.

---

# 5. Canonical wheel content and exclusions

Build one coherent application artifact with Hatchling and the existing `src/` layout.

The wheel must contain:

```text
netauto application modules
netauto domain modules
netauto persistence modules
netauto runtime and Health modules
netauto entrypoints and HTTP adapters
netauto CLI modules
neutral transport DTO modules
netauto/migrations/__init__.py
netauto/migrations/env.py
netauto/migrations/script.py.mako
netauto/migrations/versions/__init__.py
netauto/migrations/versions/0001_m2_durable_kernel.py
netauto/release/__init__.py
netauto/release/runtime.pylock.toml
netauto-0.2.0.dist-info/METADATA
netauto-0.2.0.dist-info/entry_points.txt
netauto-0.2.0.dist-info/RECORD
```

It must expose exactly the existing application console entrypoint:

```text
netauto = netauto.cli.main:main
```

Alembic and Uvicorn remain dependency-provided executables. Do not add wrapper scripts for them.

The wheel must not contain:

```text
tests/
docs/
.git or repository metadata
pyproject.toml or uv.lock
root operator alembic.ini
real or example database secrets
TLS certificates/private keys
virtual environments
build caches
Docker/Kubernetes/systemd/process-manager assets
GitHub workflow files as release runtime content
source-root migration path dependencies
multiple migration revisions or a second graph
```

Hatchling may already include non-Python files beneath `src/netauto`. Add explicit build configuration only when required to make package content deterministic; do not broaden inclusion to tests, docs or repository files.

Wheel verification must inspect logical content and metadata. Record the exact candidate wheel SHA-256 and size. Do not claim byte-identical independent wheel builds unless that property is separately and actually demonstrated; the mandatory reproducibility claim is the exact installed dependency graph and deterministic required content.

Installation of the wheel itself must not contact PostgreSQL, migrate, import the ASGI factory, start the CLI or create operator files.

---

# 6. Clean target dependency synchronization and wheel installation

## 6.1 Target isolation

T9 uses a clean target directory outside the repository checkout. The target must have:

```text
Linux
CPython 3.14.x
uv
one transferred candidate wheel
no source checkout requirement
no editable install
no project pyproject.toml
no development dependency group
```

For subprocesses:

```text
remove PYTHONPATH
use a working directory outside the repository
ensure imported netauto paths are inside the release .venv
avoid accidental repository-root sys.path imports
```

Do not copy source modules, migration scripts or `uv.lock` into the target.

## 6.2 Exact installation sequence

Exercise the exact conceptual sequence:

```text
1. create release directory releases/0.2.0
2. create releases/0.2.0/.venv with CPython 3.14.x
3. extract netauto/release/runtime.pylock.toml from the wheel with stdlib zipfile
4. write it as releases/0.2.0/runtime.pylock.toml
5. uv pip sync --python <release-python> runtime.pylock.toml
6. uv pip install --python <release-python> --no-deps <candidate-wheel>
7. verify installed distribution and executables
```

The final NETAUTO install must use `--no-deps`. Dependency resolution must not fall back to the wheel's compatible `Requires-Dist` ranges.

The operator's configured index/cache supplies third-party artifacts. S07 does not define a package index or offline wheelhouse. Tests may use the configured environment/cache, but must not silently skip when exact synchronization cannot be performed.

After synchronization and installation, machine-check:

```text
installed third-party name/version set == applicable runtime.pylock set
installed netauto version == 0.2.0
no dev-only package introduced by the procedure
netauto executable exists
uvicorn executable exists
alembic executable exists
all first-party imports resolve under the release .venv
```

Incidental environment bootstrap packages must be understood and bounded; do not hide an unexplained extra dependency set.

## 6.3 CLI-only target independence

Prove that invoking the installed CLI in a clean environment with no:

```text
NETAUTO_DATABASE_URL
NETAUTO_SECRETS_DIR
TEST_DATABASE_URL
```

can open the REPL and execute local help/exit, and can execute non-interactive public-HTTP commands against a controlled endpoint.

The CLI-only path must not import Settings, application services, persistence, SQLAlchemy, Psycopg or Alembic execution modules merely because they share one wheel.

---

# 7. Installed Alembic package and explicit schema realization

## 7.1 Preserve the accepted graph

The accepted package already owns:

```text
src/netauto/migrations/
    __init__.py
    env.py
    script.py.mako
    versions/
        __init__.py
        0001_m2_durable_kernel.py
```

Preserve:

```text
revision ID         0001_m2_kernel
down_revision       None
one base            1
one head            1
fifteen-table DDL   unchanged
migration checksum  unchanged from the S07 baseline unless a pure packaging newline issue is proven
```

Do not edit migration DDL, metadata, table names, constraints or indexes in S07.

## 7.2 Package-resource discovery

Prove from the installed release, outside the checkout:

```text
script_location = netauto:migrations
ScriptDirectory.from_config() succeeds
get_bases() == ("0001_m2_kernel",)
get_heads() == ("0001_m2_kernel",)
discover_unique_shipped_head() == "0001_m2_kernel"
script.py.mako is accessible
exactly one durable revision module is present
```

No assertion may derive the head from filename parsing, project version, a handwritten constant, environment configuration or database state.

## 7.3 Operator-owned configuration

The target release directory contains an operator-created non-secret file:

```ini
[alembic]
script_location = netauto:migrations
path_separator = os
```

It must contain no:

```text
sqlalchemy.url
database URL or credentials
expected revision constant
absolute checkout/migration path
```

The canonical installed command is:

```text
<release>/.venv/bin/alembic \
    -c <release>/alembic.ini \
    upgrade head
```

Supply database configuration only through direct validated `NETAUTO_DATABASE_URL` or the protected `NETAUTO_SECRETS_DIR` source.

## 7.4 Explicit migration evidence

Against the externally supplied real PostgreSQL target, exercise an isolated empty/base database state:

```text
wheel installation
    -> leaves database revision unchanged

installed CLI invocation
    -> leaves database revision unchanged

server startup before explicit migration
    -> fails the revision guard
    -> opens no serving endpoint
    -> does not create/stamp/migrate schema

explicit installed Alembic upgrade head
    -> creates exact durable schema
    -> writes exact singleton alembic_version

server startup after explicit migration
    -> succeeds
```

Use the installed `alembic` executable and installed migration package. Do not import source-tree migrations into the target command.

The installed migration environment must continue to use synchronous SQLAlchemy administration with `NullPool`, the same validated database URL source, and no ASGI/business AsyncEngine startup.

If test isolation requires destructive head/base transitions, serialize the affected PostgreSQL test and restore the externally supplied target to the expected state before completion.

---

# 8. Durable Linux operating document

Create one operator-facing implementation document at:

```text
docs/milestones/M2/linux-operating-baseline.md
```

This document is operating guidance beneath the frozen runtime/deployment architecture. It must not redefine application semantics or promise facilities outside M2.

Use release version `0.2.0` consistently and cover at minimum:

## 8.1 Prerequisites and responsibility split

```text
supported platform       Linux
supported Python         CPython 3.14.x
canonical tool           uv
runtime artifact         netauto-0.2.0-py3-none-any.whl
dedicated account        unprivileged operator-defined user
PostgreSQL target        empty/recreated first-baseline database
artifact transfer        operator-owned / out of scope
```

Distinguish:

```text
NETAUTO application settings
    database_url
    log_level
    pool_size
    max_overflow
    pool_timeout
    pool_recycle
    pool_pre_ping

Uvicorn/deployment settings
    host
    port
    workers

operator secret ownership
    NETAUTO_SECRETS_DIR
    NETAUTO_DATABASE_URL file permissions
```

## 8.2 Reference filesystem layout

Document:

```text
/opt/netauto/
    releases/
        0.2.0/
            .venv/
            runtime.pylock.toml
            alembic.ini
    current -> releases/0.2.0
    secrets/
        NETAUTO_DATABASE_URL
```

Clarify:

```text
release directory immutable after successful installation
current symlink operator convenience only
current is not release/schema authority
secrets stay outside release directories
wheel may be removed after verified installation
NETAUTO creates no application-owned log directory
```

## 8.3 Build and installation

Document the exact build-source sequence:

```text
uv sync --locked
uv export --frozen --no-dev --no-emit-project --format pylock.toml ...
require no generated-lock diff
uv build --wheel
inspect wheel
```

Document the exact target sequence from the transferred wheel:

```text
create release directory
create .venv
extract runtime.pylock.toml with stdlib zipfile
uv pip sync exact runtime lock
uv pip install --no-deps wheel
create minimal alembic.ini
verify metadata, entrypoints and unique head
```

Do not require a Git checkout, editable install, target `pyproject.toml` or dev dependencies.

## 8.4 Secret procedure

Document:

```text
secrets directory mode       0700
NETAUTO_DATABASE_URL mode    0600
owner                         dedicated NETAUTO user
file content                  complete database_url with optional final newline
```

Do not include a real URL or plausible credential in documentation. Use an unmistakable placeholder.

Explain source precedence:

```text
constructor/test injection
> direct NETAUTO_* environment
> explicit NETAUTO_SECRETS_DIR files
> safe defaults
```

Explain that direct environment input overrides the secret file only when deliberately supplied.

## 8.5 Explicit schema realization

Document the installed Alembic command and make clear:

```text
migration is explicit administration
installation does not migrate
CLI does not migrate
startup does not migrate or stamp
pre-baseline databases are recreated, not stamped/upgraded in place
head -> base is destructive verification, not operating rollback
```

## 8.6 Foreground start

Use a canonical command equivalent to:

```bash
env \
  NETAUTO_SECRETS_DIR=/opt/netauto/secrets \
  NETAUTO_POOL_SIZE=10 \
  NETAUTO_MAX_OVERFLOW=20 \
  NETAUTO_POOL_TIMEOUT=5 \
  NETAUTO_POOL_PRE_PING=false \
  /opt/netauto/current/.venv/bin/uvicorn \
    netauto.entrypoints.http:create_app \
    --factory \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1
```

Do not place `database_url` on the command line.

Do not present `0.0.0.0` as an implicit safe default. Explain that any explicitly broader bind requires external reachability controls consistent with the trusted-boundary contract.

`NETAUTO_POOL_RECYCLE` remains omitted for the disabled default.

## 8.7 Readiness, stop and restart

Document:

```text
verify GET /health/core == 200 complete body
stop with foreground interrupt or normal SIGTERM
allow ASGI lifespan shutdown and engine.dispose()
restart as orderly stop + fresh canonical start
fresh process reloads Settings, creates new engine/pool and reruns exact guard
verify Health again after restart
```

Do not introduce daemonization, PID-file or supervision semantics.

## 8.8 Capacity planning

State prominently:

```text
per worker maximum theoretical application connections
    = pool_size + max_overflow

deployment maximum theoretical application connections
    = workers * (pool_size + max_overflow)
```

With defaults:

```text
1 worker = 10 + 20 = 30
```

Explain exclusions:

```text
explicit Alembic NullPool administrative connection
other applications/operators
PostgreSQL reserved/superuser connections
```

Require capacity planning against the complete PostgreSQL connection budget before increasing workers or pools.

## 8.9 Trust and transport

Document exactly:

```text
no native NETAUTO authentication or authorization in M2
HTTP supported only inside an administratively trusted reachability boundary
untrusted-segment traffic requires externally managed TLS termination
NETAUTO owns no server certificate/private-key lifecycle
CLI HTTPS always verifies certificate and hostname
no CLI insecure/skip-verify mode
PostgreSQL transport/TLS/options live solely in database_url
```

Do not imply that firewall, VPN, gateway or reverse proxy becomes a NETAUTO identity authority.

## 8.10 Failure handling and non-goals

Document bounded operator consequences for:

```text
invalid/missing settings
unreachable database
uninitialized or mismatched Alembic revision
failed explicit migration
Health 503 after successful startup
orderly versus abrupt termination
```

List the M2 non-goals without implying hidden support:

```text
Docker/Kubernetes
systemd/process manager
automatic restart/start-at-boot
CI/CD/artifact transfer
rolling/zero-downtime
rollback
backup/restore
native auth/server TLS
```

Permanent T10 evidence must machine-check the critical wording and forbidden examples. Documentation-only checks do not replace the executed T9 procedure.

---

# 9. T9 installed-artifact harness

Create focused permanent installed-artifact evidence, conceptually decomposed as:

```text
tests/test_m2_s07_distribution.py
    version, runtime lock, wheel inventory and clean install

tests/test_m2_s07_alembic.py
    installed graph and explicit migration

tests/test_m2_s07_linux.py
    release layout, server lifecycle, Health and CLI

tests/test_m2_s07_trust.py
    secret/bind/documentation/HTTPS boundaries
```

Equivalent bounded decomposition is allowed. Avoid one opaque test that hides which acceptance obligation failed.

Use reusable test-only helpers for:

```text
candidate wheel build
wheel member inspection
clean release environment creation
runtime-lock extraction and sync
installed executable invocation
free local port selection
foreground Uvicorn process lifecycle
readiness polling with a finite deadline
safe stdout/stderr sanitization
Linux PTY interaction
controlled local HTTPS endpoint and CA
isolated PostgreSQL revision state
```

The helpers are test infrastructure only. Do not add a production installer, supervisor or deployment CLI.

## 9.1 Wheel build reuse

Build the exact candidate wheel once per suitable test scope and reuse it across T9 targets where isolation permits. Every assertion must still run from the candidate wheel, not source imports.

Record and assert:

```text
one wheel only
exact expected filename/version
wheel SHA-256
required member inventory
forbidden member inventory
entrypoint metadata
runtime lock equality
one migration revision
```

## 9.2 Source-path isolation

Every installed process claim must prove:

```text
cwd outside repository
PYTHONPATH absent
netauto.__file__ inside release .venv
migration resources inside installed distribution
no source-tree file required
```

Do not use an installed target plus repository `tests/` or `src/` on its import path and call it wheel-only evidence.

## 9.3 Installation has no side effects

Before and after:

```text
runtime dependency sync
wheel install
installed netauto local invocation
installed netauto non-interactive invocation against controlled HTTP
```

prove there is no implicit:

```text
PostgreSQL connection
alembic_version change
schema creation
server startup
migration execution
```

Use process/network interception where suitable for non-PostgreSQL paths and real revision-state inspection for database claims.

## 9.4 Installed server lifecycle

Run the installed release with the installed Uvicorn executable as an actual Linux subprocess:

```text
configured protected secret source
explicit pool settings
127.0.0.1 dynamic test port
--workers 1
factory entrypoint
```

Required sequence:

```text
empty/base DB before migration
    -> startup fails
    -> no listener enters serving

explicit installed Alembic upgrade head
    -> exact revision

first start
    -> startup guard passes
    -> Health 200
    -> one representative business HTTP read succeeds

orderly SIGTERM/foreground stop
    -> process exits normally
    -> owned runtime resources are released

fresh restart
    -> new process
    -> fresh guard
    -> Health 200
```

Prove disposal through objective evidence. Acceptable complementary evidence includes:

```text
installed lifespan instrumentation already owned by tests
PostgreSQL session disappearance for the dedicated test target
pool/engine closure observed from an installed-process test boundary
```

A process disappearing without any evidence that the NETAUTO lifespan cleanup ran is insufficient by itself.

Use finite deadlines and always terminate/kill as cleanup only after recording a failed orderly-stop assertion.

## 9.5 Startup mismatch

After a successful explicit migration, place only the isolated test database into a controlled non-matching Alembic state and start the installed server.

Require:

```text
nonzero startup/process outcome
no serving listener
safe bounded diagnostic
no DB URL/credential leakage
no migration/stamp/repair
```

Restore exact head before subsequent tests.

Do not modify the installed migration graph to manufacture mismatch evidence.

## 9.6 Post-start DB-unready behavior

After a successful start, create a controlled real-PostgreSQL communication failure for the dedicated test path without stopping or reconfiguring a shared PostgreSQL service.

Permitted test-side strategies include:

```text
controlled local forwarding transport that can be cut
isolated-database connectivity denial with explicit restoration
another deterministic real-PG mechanism that breaks the worker's next checkout
```

The strategy must not mock `PostgreSQLHealthProbe` or replace the installed application.

Require:

```text
worker remains an HTTP process
GET /health/core returns 503 complete bounded body
Cache-Control: no-store
no Alembic query/remediation
no credential/internal leakage
```

Restore connectivity and either prove recovery on the same process or perform an orderly stop; report which contract path was executed.

If the external database target does not provide the permissions or transport control needed for a deterministic safe failure, record the exact blocker and do not claim `M2-VER-29` PASS.

## 9.7 Installed CLI

Against installed code only, prove:

```text
no-argument REPL opens netauto>
initial DISCONNECTED / FORMATTED
local /help and /status while disconnected
Ctrl-D empty-prompt exit or /exit normal exit
/connect to the installed healthy server
/status revalidation
one FORMATTED remote read
/output JSON and one JSON remote command
non-interactive one-command contract
no mandatory Health preflight in -n mode
one stdout JSON result and exact exit semantics
```

Reuse the accepted T8 behavior; S07 owns installed-artifact execution, not new CLI semantics.

The installed CLI process environment must not require database settings.

## 9.8 Installed HTTPS verification

Use a controlled local HTTPS endpoint and test CA. Exercise the installed CLI executable for:

```text
trusted CA + matching hostname
    -> success

untrusted CA
    -> cli_transport_error / process failure

trusted CA + hostname mismatch
    -> cli_transport_error / process failure
```

Use administered standard trust environment mechanisms supported by HTTPX. Do not add a NETAUTO CA/profile option.

Also prove:

```text
--insecure absent
verify=false absent
skip-verify absent
generic credential/header options absent
URL userinfo rejected
```

Do not add server-side TLS to NETAUTO/Uvicorn merely to run this matrix; a controlled external test TLS endpoint/terminator owns it.

## 9.9 Secret and command-line non-leakage

Use a unique sentinel in the disposable database URL and require it absent from:

```text
canonical documentation command line
Uvicorn argv / Linux process command line
normal startup stdout/stderr
Health response
CLI output/state
Alembic configuration file
wheel members and metadata
recorded evidence text
```

Sanitize assertion diagnostics before embedding subprocess output in pytest failure messages.

The secret file may contain the sentinel only in its protected disposable location.

---

# 10. M2-VER bundle ownership and traceability

Extend the singular machine-checkable M2 registry in `tests/test_m2_traceability.py`.

Create explicit S07 primary target ownership, conceptually:

```text
S07_PRIMARY_BUNDLE_TARGETS = {
    "M2-VER-24": frozenset({...}),
    "M2-VER-29": frozenset({...}),
    "M2-VER-30": frozenset({...}),
}
```

Requirements:

```text
exact primary bundle census        M2-VER-24 / 29 / 30
all target sets non-empty
all target names exist
all targets use the actual candidate wheel where required
S05 support for M2-VER-24/30 remains present
S06 and S05 support for CLI bundles remains present
complete bundle targets are the honest union of primary and supporting evidence
M2-VER-29 moves from DESIGNED to IMPLEMENTED only with concrete targets
M2-VER-31 / 32 remain S08-owned and are not overclaimed
```

Add an explicit S07 installed-support registry for the installed-artifact portions of:

```text
M2-VER-22
M2-VER-23
M2-VER-25
M2-VER-26
M2-VER-27
M2-VER-28
```

Do not transfer primary ownership of those accepted bundles. The S07 targets supplement them with wheel-installed T9 evidence.

Machine-check at least:

```text
M2-VER-24 proves one versioned distribution
M2-VER-29 proves the executed Linux procedure
M2-VER-30 proves trust/transport boundaries
all three primary bundles include runtime and static evidence where required
installed support is mapped without duplicate or orphan targets
63 remote operations and 8 local commands remain exact
no new public/server/CLI operation was introduced
```

Avoid silently making every future `test_m2_s07_*` function part of every bundle by filename. Use explicit ownership where evidence roles differ.

---

# 11. Required focused verification

Run the smallest evidence first and report exact selected/collected/pass counts and durations.

## 11.1 Release metadata and lock

Run exact targets proving:

```text
0.2.0 metadata coherence
uv.lock local-version-only delta
runtime pylock regeneration equality
runtime-only package graph
no project/dev entries
wheel lock bytes equal committed source
```

## 11.2 M2-VER-24

Run the complete concrete target set for:

```text
wheel content and exclusions
one release version
entrypoints
clean lock sync
--no-deps wheel install
installed server/CLI/Alembic imports
unique installed head
no installation/CLI/server implicit cross-action
```

## 11.3 M2-VER-29

Run the complete concrete target set for:

```text
operator document policy
release layout
secret permissions
explicit migration
startup-before-migration failure
start / Health / business read
orderly stop / disposal
restart / fresh guard / Health
post-start DB-unready Health 503
no Git checkout
capacity formula
```

## 11.4 M2-VER-30

Run the complete concrete target set for:

```text
trusted-boundary documentation
safe bind examples
no native auth/401/403/credential surface
no database URL leakage
installed HTTPS trust success
untrusted CA failure
hostname mismatch failure
no insecure bypass
DB transport only through database_url
no server certificate lifecycle settings
```

## 11.5 Installed support for accepted bundles

Re-execute the installed-artifact portions required by:

```text
M2-VER-22 — exact startup revision guard
M2-VER-23 — same-engine Health
M2-VER-25 — installed REPL/terminal state
M2-VER-26 — installed connect/status transitions
M2-VER-27 — installed non-interactive process
M2-VER-28 — installed coverage/HTTP-only boundary
```

Do not infer PASS from the source-environment tests alone.

---

# 12. Mandatory commands and final gate

Run and report exact commands, counts and durations.

## 12.1 Version, lock, build and static quality

Use normal source edits and the authorized version update, then run:

```text
uv lock
uv lock --check
uv sync --locked
uv export --frozen --no-dev --no-emit-project \
    --format pylock.toml \
    --output-file <temporary-regenerated-runtime.pylock.toml>
compare temporary export byte-for-byte with src/netauto/release/runtime.pylock.toml
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Also inspect and report:

```text
pyproject version diff
uv.lock diff
third-party dependency/version/hash diff census
runtime lock package census
wheel member census
wheel SHA-256 / size
runtime lock SHA-256 / size
```

No unrelated dependency upgrade is permitted.

## 12.2 Focused S07 evidence

Run exact collected targets for:

```text
M2-VER-24 primary and supporting union
M2-VER-29 primary
M2-VER-30 primary and supporting union
installed M2-VER-22 / 23 / 25 / 26 / 27 / 28 support
S07 traceability registries
wheel negative content surface
secret/non-leakage surface
```

## 12.3 Schema and runtime regressions

At minimum run:

```text
tests/test_migrations.py
tests/test_schema_metadata.py
tests/test_runtime_schema_guard.py
tests/test_runtime_engine.py
tests/test_settings.py
tests/test_http_composition.py
tests/test_bootstrap_diagnostics.py
tests/test_health.py
tests/test_health_probe.py
tests/test_health_api.py
tests/test_health_postgresql.py
tests/test_m2_s04_installed.py
```

## 12.4 CLI regressions

At minimum run:

```text
all tests/test_m2_s05_*.py
all tests/test_m2_s06_*.py
```

Preserve the exact S05/S06 review-fix boundaries and installed CLI evidence.

## 12.5 Cross-boundary and full repository gates

Run:

```text
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py
uv run pytest -q -m "postgresql and concurrency" -ra
uv run pytest -q -m "not postgresql" -ra
uv run pytest -q -ra
```

The complete suite must use the externally supplied `TEST_DATABASE_URL` and include all PostgreSQL tests.

No normative test may be skipped, xfailed or hidden by generic rerun. Do not add a rerun plugin or automatic rerun wrapper.

The Linux-only T9 and PTY targets must run on Linux. Platform skip decorators may remain for genuinely non-Linux development collection, but a candidate cannot be declared ready unless the actual acceptance environment executes them and the final skip census is zero.

Report:

```text
CPython version
Linux kernel and evidence distribution
PostgreSQL server version
uv version
Hatchling/build backend version when observable
release version
wheel filename/hash/size
runtime lock hash/size/package count
collection count
focused bundle counts and durations
installed support counts
PostgreSQL count/duration
non-PostgreSQL count/duration
full-suite count/duration
skip / xfail / rerun census
warning census
supported-path 40P01 / unexpected 40001 census
negative-control 40P01 / 40001 census
```

---

# 13. Unchanged-boundary verification

Explicitly verify and report:

```text
15 authoritative tables
one Alembic base / one head
revision ID 0001_m2_kernel unchanged
0001_m2_durable_kernel.py DDL unchanged
compare_metadata == []
no schema/migration/constraint/index diff
41 mutations + 22 reads unchanged
1 Health route unchanged
64 total public HTTP operations unchanged
63 CLI remote specs unchanged
8 local CLI commands unchanged
65 registry examples unchanged
9 enrichment entry points unchanged
83 scenarios and 21 predicates unchanged
three advisory gates and four row-lock modes unchanged
Settings inventory/defaults unchanged
startup and Health timeout constants unchanged
CLI JSON schema/trace unchanged
no new native auth/TLS/credential surface
no S08/S09 implementation
```

Verify version/dependency scope exactly:

```text
project version                 0.2.0
third-party compatibility ranges unchanged
third-party uv.lock resolution unchanged
runtime.pylock generated only from runtime resolution
no build artifact committed
```

Verify forbidden runtime/deployment mechanisms remain absent:

```text
Docker/Kubernetes/systemd assets
server wrapper CLI
migration wrapper CLI
automatic upgrade/stamp/repair
source-checkout requirement
second revision/version authority
second runtime/Health engine
unbounded pool setting
unsafe default universal bind
native server TLS/cert settings
native authentication/authorization
CLI insecure verification bypass
persistent CLI credential/profile/history
```

---

# 14. Implementation and publication discipline

Work directly on `M2`.

Use normal source edits, generated lock workflow, tests, commits and push. Do not create a PR.

A reasonable publication sequence is:

```text
implementation commit(s)
    -> release version, runtime lock/package data, operator document,
       T9 harness and traceability

evidence/status commit
    -> exact candidate wheel/lock hashes, commands, counts, environment
       and candidate state only after every mandatory gate passes

optional provenance commit
    -> only when needed to record the exact final remote-tested commit
```

Do not commit:

```text
dist/
*.whl
.venv/
temporary releases/
extracted runtime locks outside src/netauto/release/
secret files
TLS private keys/test CA artifacts
subprocess logs
pytest caches
```

Do not delete this prompt while S07 remains open.

Do not edit frozen contract, architecture or steps to fit implementation. The durable Linux operator document is implementation/operating guidance and must remain subordinate to them.

## 14.1 Status transitions

At implementation start, `status.md` may become:

```text
M2-S07 — IN PROGRESS
```

Only after every mandatory gate passes on the exact candidate may Codex publish:

```text
M2-S07 — CANDIDATE READY FOR REVIEW
```

Codex must never assign:

```text
M2-S07 — COMPLETED
M2-S08 — READY or IN PROGRESS
```

Those remain reviewer-owned.

If any mandatory environment, PostgreSQL permission, dependency synchronization, Linux/PTy/TLS target or requirement is unavailable:

```text
leave M2-S07 IN PROGRESS or BLOCKED as appropriate
record the exact blocker
publish only explicitly partial work
never claim candidate-ready
```

A documentation-only procedure, source-tree installed smoke or mocked Health probe is not a substitute for T9.

## 14.2 Final remote verification

After pushing the candidate:

```text
verify local HEAD == origin/M2 == remote M2
verify ahead/behind 0/0
verify working tree clean
rebuild the wheel from the exact final remote commit
rerun runtime-lock equality
rerun every mandatory S07 bundle and the complete suite
rerun the documented T9 procedure against that exact rebuilt wheel
```

The final evidence must identify the SHA-256 of the wheel built from the exact final remote commit.

If the post-push rebuild or rerun changes evidence or reveals a failure, publish the corrected state and repeat. Do not hand off an unverified evidence/provenance commit.

Do not tag or publish the candidate wheel as a release during S07.

---

# 15. Required handoff

The final handoff must report:

```text
cycle / slice / branch
reviewer-owned starting baseline
implementation commit(s)
evidence/status commit
optional provenance commit
final remote HEAD
local/origin/remote synchronization
working-tree state
PR / Actions / tag / release state
```

Summarize implementation by boundary:

```text
release metadata
runtime PEP 751 lock
wheel content/package data
clean target synchronization/install
installed Alembic graph and explicit migration
Linux operating document
installed server lifecycle and Health
installed interactive/non-interactive CLI
trust/TLS/secret boundary
traceability
```

Report exact release facts:

```text
release version
wheel filename
wheel SHA-256
wheel byte size
wheel member count
runtime lock SHA-256
runtime lock byte size
runtime package count
installed distribution version
installed unique base/head
migration revision applied
release-layout path used for T9
```

Report exact operating evidence:

```text
installation outside checkout
runtime sync + --no-deps install commands
pre-migration startup failure
explicit migration result
first startup / Health / business read
orderly stop and disposal evidence
restart / fresh guard / Health
post-start DB-unready result and restoration
installed REPL/CLI results
HTTPS trusted/untrusted/mismatch results
secret permission and leakage results
capacity formula/document checks
```

Report all commands, counts, durations, environment versions, skips/xfails/reruns/warnings and SQLSTATE census.

Explicitly state:

```text
M2-S07 is CANDIDATE READY FOR REVIEW, not COMPLETED
M2-S08 remains BLOCKED
no schema, migration DDL, API or CLI semantic change was introduced
no built wheel was committed or published
no tag, PR, GitHub Release or GitHub Action was created
```

If one mandatory procedure or the complete externally supplied PostgreSQL suite did not pass, do not use candidate-ready wording.