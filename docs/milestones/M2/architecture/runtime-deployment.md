# M2 Runtime, Packaging and Deployment Architecture

**Status:** DRAFT — RUNTIME/DEPLOYMENT DESIGN COMPLETE — CROSS-OWNER REVIEW PASSED — TECHNOLOGY-BASELINE/FINAL-CLOSURE PENDING

**Authority:** NORMATIVE M2 ARCHITECTURE DRAFT

## Authority and scope

This document owns the M2 runtime, packaging and deployment realization for:

```text
validated process settings and secret-source composition
PostgreSQL AsyncEngine and connection-pool realization
one-wheel server / CLI / Alembic distribution
exact runtime dependency-lock delivery
installed Alembic environment and explicit administration
unique shipped-head discovery
exact startup database-revision guard
ASGI lifespan, worker and shutdown composition
manual Linux installation and ordinary process operation
offline first-baseline realization and future forward-operation posture
trusted-boundary, external-TLS and database-transport responsibilities
runtime/deployment verification hooks
```

Its implementation authority, once the complete M2 architecture set is frozen, is:

```text
docs/milestones/M2/contract.md
    FINAL / FROZEN operating, packaging and security outcomes
+
docs/general/technology_baseline.md
    ratified Python, settings, persistence, testing, packaging,
    serving and official-CLI technology
+
persistence.md
    first durable schema and Alembic graph content
+
health.md
    same-engine Core readiness probe and post-start behavior
+
cli.md
    console client, runtime dependencies and HTTP-only boundary
+
verification.md
    M2-VER-20 ... M2-VER-30 and final evidence obligations
+
this document
    installed runtime and operating realization
```

This document does not redefine:

```text
business or Health wire behavior
    -> api.md

Relationship/domain semantics
    -> relationship.md

relational tables, constraints, indexes or revision DDL
    -> persistence.md

semantic races, locks, gates or retries
    -> concurrency-matrix.md and concurrency.md

CLI command grammar, selectors, output or transport semantics
    -> cli.md

executed evidence and delivery records
    -> verification.md and future steps.md
```

Discovery under `../wip/runtime-configuration-production-deployment.md` is superseded by this document for the areas owned here.

---

## 1. Governing operating model

M2 delivers the first complete **manual Linux operating baseline**.

```text
build one versioned application wheel
-> transfer by an operator-owned mechanism
-> install into one dedicated release environment
-> supply validated runtime configuration
-> realize the schema explicitly with Alembic
-> start Uvicorn workers
-> require every worker to pass the exact revision guard
-> verify GET /health/core
-> stop/restart through ordinary process signals and a fresh launch
```

The baseline is intentionally not an orchestrator.

M2 does not provide:

```text
Docker or Kubernetes assets
systemd units or another process manager
start-at-boot or restart automation
artifact registry or transfer automation
CI/CD deployment
rolling, blue/green, canary or zero-downtime upgrade
application/schema rollback procedure
backup, restore or disaster-recovery automation
native authentication, server TLS or network-policy automation
```

The absence of these facilities does not weaken the defined installation, startup, readiness or shutdown contract.

---

## 2. Configuration ownership

Configuration is divided into two non-overlapping authorities.

### 2.1 NETAUTO application/runtime settings

The immutable process `Settings` model owns exactly the values consumed by application/runtime composition:

```text
database_url
log_level
pool_size
max_overflow
pool_timeout
pool_recycle
pool_pre_ping
```

### 2.2 Serving/deployment settings

The Uvicorn command or an external process-management layer owns:

```text
bind host
bind port
worker count
reload and other serving-only behavior
```

These values do not become fields of the NETAUTO `Settings` model.

### 2.3 No profile or generic configuration hierarchy

M2 introduces no:

```text
YAML/TOML/INI application configuration framework
production/development/staging profile model
runtime settings reload
mutable settings singleton
server-discovery profile
```

An operator may use ordinary shell/process environment management around the process, but that mechanism does not become an application configuration format.

---

## 3. Exact Settings contract

Conceptual fields and validation are:

```text
database_url: str
    required
    canonical SQLAlchemy URL
    driver must be postgresql+psycopg

log_level: CRITICAL | ERROR | WARNING | INFO | DEBUG
    default INFO

pool_size: int
    default 10
    must be >= 1

max_overflow: int
    default 20
    must be >= 0
    -1 / unlimited overflow is forbidden

pool_timeout: float
    default 5.0 seconds
    must be > 0

pool_recycle: int | null
    default null = disabled
    when present, positive whole seconds
    zero or negative input is invalid

pool_pre_ping: bool
    default false
```

The engine maps:

```text
pool_recycle = null
    -> SQLAlchemy pool_recycle = -1

pool_recycle = N
    -> SQLAlchemy pool_recycle = N
```

`pool_size = 0` is forbidden even though SQLAlchemy can interpret it as an unbounded pool. A bounded M2 deployment must retain a meaningful capacity calculation.

### 3.1 Canonical environment names

```text
NETAUTO_DATABASE_URL
NETAUTO_LOG_LEVEL
NETAUTO_POOL_SIZE
NETAUTO_MAX_OVERFLOW
NETAUTO_POOL_TIMEOUT
NETAUTO_POOL_RECYCLE
NETAUTO_POOL_PRE_PING
```

No separate host, port, database, username, password or database-TLS setting is introduced. The complete PostgreSQL connection and transport policy remain in `database_url`.

### 3.2 Settings lifecycle

```text
process/factory startup
-> load sources once
-> validate complete immutable Settings
-> compose runtime
-> no reload during process lifetime
```

Missing or invalid settings fail process startup before serving.

Importing `netauto.settings` performs no environment read and creates no global settings object.

---

## 4. Secret-file composition

### 4.1 Bootstrap source selector

M2 adds one bootstrap-only environment selector:

```text
NETAUTO_SECRETS_DIR
```

It identifies the directory passed to `Settings(_secrets_dir=...)` by the composition root. It is not a domain/application setting and is not a second database connection authority.

If supplied, the path must be absolute, exist and identify a directory. Invalid explicit selection fails startup instead of silently falling back.

### 4.2 Canonical database secret file

The production-recommended layout contains:

```text
<secrets-dir>/NETAUTO_DATABASE_URL
```

The file contains exactly the complete `database_url` value and a final newline may be ignored by the settings source.

Reference Linux permissions are:

```text
secrets directory
    owner = dedicated NETAUTO user
    mode  = 0700

NETAUTO_DATABASE_URL
    owner = dedicated NETAUTO user
    mode  = 0600
```

The operator owns permission enforcement. Final operating verification checks the documented procedure; NETAUTO does not introduce a privileged secret-management daemon.

### 4.3 Source precedence

The M2 production source order is:

```text
1. explicit constructor/test values
2. direct NETAUTO_* environment variables
3. files in explicit NETAUTO_SECRETS_DIR
4. safe code defaults
```

Direct `NETAUTO_DATABASE_URL` therefore overrides the file source when both are deliberately supplied.

The production composition root does not enable dotenv or implicit parent-directory discovery.

### 4.4 Safety boundary

The database URL is never:

```text
placed in the canonical Uvicorn command line
written to Alembic configuration
included in Health
included in normal logs or startup summaries
copied into CLI state or output
packaged in the wheel
committed to the repository
```

Startup may log safe non-secret pool and release metadata only.

---

## 5. Runtime engine and pool

### 5.1 Process resource

One worker constructs one process-lifetime `AsyncEngine`:

```text
create_async_engine(
    settings.database_url,
    isolation_level="READ COMMITTED",
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    pool_recycle=(-1 if settings.pool_recycle is None
                  else settings.pool_recycle),
    pool_pre_ping=settings.pool_pre_ping,
)
```

The async-compatible SQLAlchemy pool selected by `create_async_engine()` remains the runtime pool authority.

The engine is lazy: construction does not pre-create connections. Startup schema validation performs the first required active checkout.

### 5.2 Shared worker runtime

The same engine and pool serve:

```text
business UnitOfWorkFactory
coherent read UnitOfWorkFactory
startup revision inspection
PostgreSQLHealthProbe
```

The startup guard and Health probe are operational connection contexts, not semantic write UoWs. They do not commit business state.

M2 introduces no:

```text
startup engine
Health engine
migration engine inside the serving process
reserved Health connection
process-global connection outside SQLAlchemy ownership
```

Explicit Alembic administration is a separate process and uses its own `NullPool` connection.

### 5.3 Worker capacity

For one worker:

```text
maximum theoretical pooled application connections
    = pool_size + max_overflow
```

For `W` Uvicorn workers:

```text
maximum theoretical pooled deployment connections
    = W * (pool_size + max_overflow)
```

With M2 defaults:

```text
one worker = 10 + 20 = 30
```

This calculation excludes:

```text
explicit Alembic administrative connection
other applications/operators
PostgreSQL reserved/superuser connections
```

Deployment documentation must require capacity planning against PostgreSQL's total connection budget before increasing worker or pool counts.

### 5.4 Shutdown

Every constructed engine is explicitly disposed with `await engine.dispose()`:

```text
normal lifespan shutdown
startup-guard failure after engine creation
composition failure after engine creation
cancelled startup path
```

The Health service owns no second resource and requires no separate disposal.

---

## 6. One coherent wheel

### 6.1 Canonical artifact

The canonical NETAUTO application artifact is:

```text
netauto-<release-version>-py3-none-any.whl
```

The wheel contains:

```text
server/application/domain/persistence modules
official CLI modules
netauto console entrypoint metadata
transport-only shared DTOs
complete installed Alembic environment and revision graph
release dependency lock resource
installed release metadata
```

The wheel does not contain:

```text
operator configuration or secrets
TLS certificates or private keys
Git repository
pytest suite or development tooling
Docker/Kubernetes/systemd assets
reverse-proxy configuration
```

### 6.2 One release version

The installed distribution metadata is the release-version authority:

```text
importlib.metadata.version("netauto")
```

Server, CLI and migration graph ship from this one distribution. No independent CLI, server or schema package version exists.

The exact M2 release number is release metadata, not a domain identity, but it must differ intentionally from the delivered M1 distribution and be used consistently in:

```text
wheel filename
installed metadata
release directory
verification evidence
```

No handwritten parallel `__version__` authority is required. A convenience `netauto.__version__` may derive from installed metadata only.

### 6.3 Runtime dependencies

Authorized M2 implementation moves/adds:

```text
httpx>=0.28,<1
    -> runtime dependency for official CLI

prompt-toolkit>=3.0,<4
    -> runtime dependency for official CLI
```

and exposes:

```toml
[project.scripts]
netauto = "netauto.cli.main:main"
```

The dependency and console-entrypoint change remains conditional on formal `STACK-10` ratification in `docs/general/technology_baseline.md` before architecture freeze.

No Typer, Click, cmd2, Rich or second HTTP client is added.

### 6.4 Server and CLI import independence

A CLI-only workstation installs the same wheel but:

```text
netauto invocation
    -> imports CLI and neutral transport modules only
    -> does not load Settings
    -> does not import application services or persistence
    -> creates no engine
    -> requires no database_url
```

Server factory import and application startup do not require invoking the CLI.

Presence in one wheel is a release boundary, not a runtime dependency cycle.

---

## 7. Reproducible dependency installation from one wheel

### 7.1 Problem closed by M2

Wheel `Requires-Dist` metadata intentionally expresses compatible version ranges. Installing only those ranges on a target would permit a dependency resolution different from the reviewed `uv.lock`.

M2 therefore ships one generated runtime lock resource **inside the same application wheel**:

```text
netauto/release/runtime.pylock.toml
```

It is an exported PEP 751 lock containing:

```text
all transitive runtime dependencies
exact versions and artifact hashes/markers
no development dependency group
no local NETAUTO project entry
```

The wheel remains the only required NETAUTO release artifact. Third-party distributions are obtained from the operator's configured index/cache and are not vendored into the NETAUTO wheel.

### 7.2 Build-source authority

The resource is generated from the committed `uv.lock`, conceptually:

```text
uv export
    --frozen
    --no-dev
    --no-emit-project
    --format pylock.toml
    --output-file src/netauto/release/runtime.pylock.toml
```

Release verification fails when regeneration changes the committed/package candidate. The file is generated evidence, not a second manually edited dependency authority.

### 7.3 Target synchronization

A clean target release environment performs:

```text
1. extract netauto/release/runtime.pylock.toml from the wheel
   using the standard-library zipfile module

2. uv pip sync --python <release-python> runtime.pylock.toml

3. uv pip install --python <release-python> --no-deps <netauto-wheel>
```

`--no-deps` is required on the final wheel install because dependencies were already synchronized from the embedded exact lock.

The procedure fails rather than silently falling back to an unconstrained range resolution.

### 7.4 Scope boundary

M2 does not define:

```text
which public/private package index supplies third-party wheels
offline wheelhouse construction
artifact signing infrastructure
SBOM publication
vulnerability-management policy
```

Those may wrap the exact release lock later without changing application semantics.

---

## 8. Installed Alembic package

### 8.1 Canonical package layout

The first durable migration environment moves under the installed Python package:

```text
src/netauto/migrations/
    __init__.py
    env.py
    script.py.mako
    versions/
        __init__.py
        <single durable root revision>.py
```

The old repository-root development migration chain is not shipped by the M2 wheel.

The package contains exactly the graph owned by `persistence.md`:

```text
one base/root
one head
fifteen-table final schema
no predecessor revision
```

Hatchling includes the Python and non-Python migration resources because they live beneath the selected `src/netauto` package. Wheel-content verification remains mandatory.

### 8.2 Package-resource script location

The canonical Alembic script location is:

```text
netauto:migrations
```

No absolute source-tree path and no `%(here)s/migrations` assumption is used by installed administration or startup inspection.

### 8.3 Operator-owned minimal Alembic config

The canonical Linux procedure creates one non-secret operator file in the release directory:

```ini
[alembic]
script_location = netauto:migrations
path_separator = os
```

The file contains no database URL, credentials, expected revision constant or source checkout path.

### 8.4 Migration environment

Installed `env.py`:

```text
loads the same validated database_url source as server startup
uses a synchronous SQLAlchemy Engine with NullPool
supports an injected synchronous test connection
runs revision scripts explicitly
never starts the ASGI application
never constructs the business AsyncEngine
```

Revision scripts are self-contained physical DDL and do not import mutable application metadata as migration authority.

Development `compare_metadata` may receive authoritative metadata through an explicit verification/autogenerate path, but production `upgrade` does not derive DDL from current application models.

### 8.5 Explicit command

The canonical administrative operation is the ordinary Alembic executable installed in the release environment:

```text
<release>/.venv/bin/alembic
    -c <release>/alembic.ini
    upgrade head
```

The command receives `NETAUTO_SECRETS_DIR` or direct settings through the process environment.

M2 adds no:

```text
netauto migrate command
second migration console entrypoint
startup migration
schema repair endpoint
```

---

## 9. Shipped migration-graph authority

### 9.1 Programmatic Config

Runtime inspection builds an in-memory Alembic `Config` and sets only:

```text
script_location = netauto:migrations
```

It does not read an operator `alembic.ini`, because expected schema identity is a property of the installed release, not of a mutable deployment file.

### 9.2 Unique graph validation

The installed graph is loaded through `ScriptDirectory.from_config()`.

Before use it must satisfy:

```text
len(script_directory.get_bases()) == 1
len(script_directory.get_heads()) == 1
```

The unique element of `get_heads()` is the expected revision.

The expected revision is never obtained from:

```text
migration filename parsing
package version
handwritten constant
environment variable
operator configuration
database state
```

Zero/multiple base or head revisions are invalid release composition and reject startup.

### 9.3 Package-resource lifetime

Alembic's installed package-resource script-location support is the normal realization. If an implementation path requires a concrete filesystem directory, it must use `importlib.resources.files()` plus `as_file()` for the complete operation lifetime; it must not copy migration scripts into an untracked persistent directory.

---

## 10. Actual database revision

### 10.1 Same runtime engine

Startup revision inspection uses a borrowed connection from the worker's already-created `AsyncEngine`.

Conceptually:

```text
async with runtime.engine.connect() as connection:
    actual_heads = await connection.run_sync(
        lambda sync_connection:
            MigrationContext.configure(sync_connection).get_current_heads()
    )
```

The operation performs no commit and no application-table access.

### 10.2 Exact state

The database is startup-compatible only when:

```text
actual_heads == (expected_head,)
```

after normalizing the returned sequence as an unordered singleton.

The following all reject startup:

```text
alembic_version absent / no current revision
database at base
older revision
newer or unknown revision
multiple current heads
revision state unreadable
migration graph with zero/multiple heads
database unreachable or query failure
```

A newer revision is not inferred to be backward compatible.

### 10.3 No schema introspection substitute

The startup guard does not compare tables/columns/indexes or run `compare_metadata`. Exact Alembic revision equality is the runtime compatibility gate.

Metadata/schema drift is a verification and release-quality failure, not a startup repair mechanism.

---

## 11. Startup schema guard

### 11.1 Conceptual owner

```text
src/netauto/runtime/schema_guard.py
```

owns:

```text
MigrationGraphInvalid
SchemaGuardUnavailable
SchemaRevisionMismatch
discover_unique_shipped_head
load_current_database_heads
require_exact_schema_revision
```

These are bootstrap/infrastructure values and do not cross into business application failures or HTTP error codes.

### 11.2 Bounded operation

The complete guard is bounded by:

```text
CORE_STARTUP_SCHEMA_GUARD_TIMEOUT_SECONDS = 10.0
```

The outer native-asyncio deadline covers:

```text
pool checkout
initial PostgreSQL connection
revision-table query
synchronous Alembic inspection adapter
connection cleanup
```

This constant is a bootstrap safety boundary, not a readiness or availability SLA and not a deployment setting.

The operator may additionally configure PostgreSQL driver transport timeouts in `database_url`; NETAUTO does not add parallel host/TLS/connect settings.

### 11.3 Behavior

```text
exact singleton equality
    -> startup may continue

any mismatch/unavailability/timeout/invalid graph
    -> safe bootstrap diagnostic
    -> engine disposal
    -> lifespan startup failure
    -> worker never serves
```

The guard:

```text
never invokes alembic.command.upgrade
never writes alembic_version
never stamps
never creates tables
never retries indefinitely
never maps failure to /health/core
```

### 11.4 Diagnostics

Safe startup diagnostics may include:

```text
installed release version
expected revision ID
actual revision ID/count when readable
bounded failure category
```

They must not include:

```text
database URL or credentials
username/host/port extracted from the URL
raw SQL or stack in normal operator output
unbounded driver internals
```

Unexpected defects remain logged through the project outer error boundary.

---

## 12. ASGI composition and lifespan

### 12.1 Explicit factory

The serving entry remains:

```text
netauto.entrypoints.http:create_app
```

with Uvicorn `--factory`.

The factory loads validated settings and constructs the FastAPI application without opening a database connection at module import time.

### 12.2 Lifespan order

Each worker lifespan follows exactly:

```text
1. configure logging
2. build RuntimeContext from complete Settings
3. discover and validate unique shipped Alembic head
4. inspect current database revision through runtime.engine
5. require exact equality
6. compose PostgreSQLHealthProbe(runtime.engine)
7. compose CoreHealthService
8. publish runtime/services in application state
9. enter serving
10. on shutdown, dispose runtime.engine
```

If any step after engine construction fails, disposal occurs before the exception escapes lifespan startup.

Routers may be registered when the application object is constructed, but ASGI serving is not considered entered until the successful lifespan startup boundary.

### 12.3 Worker model

Every Uvicorn worker is an independent OS process with its own:

```text
Settings value
application instance
event loop
AsyncEngine and pool
startup guard
Health service
```

PostgreSQL is the only cross-worker semantic authority.

No process-local lock, cache, migration result or “first worker” flag can satisfy another worker's guard.

### 12.4 Failed worker

A worker whose guard fails exposes neither:

```text
/api/v1/core
/health/core
```

Deterministic schema mismatch causes every worker against that database/release pair to fail the same equality check.

Deployment readiness is declared only after the requested serving process set is running and Health succeeds.

---

## 13. Health composition

`health.md` is realized without duplication:

```text
startup guard
    -> exact schema compatibility before serving

/health/core after startup
    -> same runtime engine/pool
    -> SELECT 1
    -> fixed two-second readiness deadline
```

Health never calls the schema guard or Alembic graph APIs.

After successful startup:

```text
later DB outage or pool saturation
    -> worker remains an HTTP process
    -> /health/core returns the bounded 503 result
```

Startup mismatch remains an out-of-serving process failure, not a Health component state.

---

## 14. Official CLI packaging handoff

The one wheel exposes:

```text
netauto
```

and contains all 63-command registry/client modules owned by `cli.md`.

Runtime packaging confirms:

```text
server does not invoke CLI
CLI does not load server Settings or persistence
Health is consumed only by interactive /connect and /status
non-interactive CLI performs no mandatory Health preflight
same wheel/release is the guaranteed compatibility pair
```

A CLI-only target may install the same release environment procedure without supplying `NETAUTO_SECRETS_DIR` or `database_url`.

Cross-release CLI/server combinations remain unsupported and no server-version negotiation endpoint is introduced.

---

## 15. Supported Linux baseline

### 15.1 Platform

M2 supports:

```text
Linux
CPython 3.14.x
uv-managed or uv-selected compatible Python
```

Support is distribution-agnostic. One distribution may be used for acceptance evidence without becoming product identity.

### 15.2 Dedicated user

A production installation uses a dedicated unprivileged OS account. Examples use:

```text
netauto
```

The concrete username is operator-defined.

The serving process does not require root privileges or permission to modify its installed release.

### 15.3 Reference layout

```text
/opt/netauto/
    releases/
        <release-version>/
            .venv/
            runtime.pylock.toml
            alembic.ini
    current -> releases/<release-version>
    secrets/
        NETAUTO_DATABASE_URL
```

Properties:

```text
release directory
    -> immutable after successful installation

current symlink
    -> operator-managed convenience
    -> never schema compatibility authority

secrets
    -> shared operator-owned secret source
    -> outside every release directory
```

The wheel may be removed after verified installation. M2 creates no application-owned log directory.

A simpler direct versioned path may be used instead of `current`; the symlink is a reference operating layout, not domain identity.

---

## 16. Canonical build procedure

On a clean source/build environment:

```text
1. select CPython 3.14.x
2. uv sync --locked
3. regenerate runtime.pylock.toml from uv.lock with --frozen
4. require no generated-lock diff
5. uv build --wheel
6. inspect the built wheel
```

Wheel inspection must prove at least:

```text
one netauto distribution version
netauto console entrypoint
server and CLI packages
netauto/migrations/env.py
netauto/migrations/script.py.mako
exactly one durable revision script
netauto/release/runtime.pylock.toml
no source-root migration dependency
```

The source environment and tests are not packaged as production runtime content.

Artifact transfer to the target remains outside M2.

---

## 17. Canonical clean installation

Given one transferred M2 wheel, the operator performs conceptually:

```text
1. create /opt/netauto/releases/<version>
2. create a CPython 3.14 virtual environment with uv
3. extract runtime.pylock.toml from the wheel using that Python stdlib
4. uv pip sync the release environment from the extracted pylock
5. uv pip install the NETAUTO wheel with --no-deps
6. create the minimal non-secret alembic.ini
7. verify installed version, netauto entrypoint and unique graph head
8. configure the protected secret source
9. apply Alembic upgrade head explicitly
10. select the release path/current symlink
11. start the server
12. verify /health/core
```

No step requires:

```text
Git checkout
source-tree migrations
editable install
project pyproject.toml on the target
dev dependency group
```

### 17.1 First durable database realization

Supported M2 installation targets are:

```text
empty PostgreSQL database
or
pre-baseline development database that is dropped/recreated first
```

An old M1 development schema is not stamped or upgraded in place.

### 17.2 Failure handling

Installation is not considered selected/current until dependency sync, wheel install and package/head verification succeed.

A failed Alembic operation leaves no serving worker started. Schema-level rollback behavior is owned and verified by `persistence.md`/`verification.md`.

---

## 18. Serving command

The canonical foreground form is:

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

`NETAUTO_POOL_RECYCLE` is omitted to retain the disabled default.

The command deliberately does not contain the database URL.

### 18.1 Bind policy

Canonical examples use:

```text
127.0.0.1
or
one explicit trusted-management interface address
```

`0.0.0.0` is never presented as an implicit safe default. It may be selected explicitly only when external reachability controls make the resulting listener consistent with the trusted-boundary contract.

### 18.2 Serving values

```text
host
port
workers
```

remain Uvicorn arguments. M2 introduces no duplicate `NETAUTO_HOST`, `NETAUTO_PORT` or `NETAUTO_WORKERS` application settings.

### 18.3 Foreground baseline

The canonical process runs in the foreground. An external shell/session or future process manager may supervise it, but supervision is not part of M2.

M2 does not define a PID-file format, daemonization layer or background launcher.

---

## 19. Stop and restart

### 19.1 Stop

Ordinary stop sends the Uvicorn process a normal termination signal or uses the foreground terminal interrupt.

```text
stop accepting new work
-> complete/cancel in-flight work according to ASGI/Uvicorn lifecycle
-> execute application lifespan shutdown
-> await engine.dispose()
-> exit
```

M2 does not redefine Uvicorn's signal ownership.

### 19.2 Restart

Restart is:

```text
successful orderly stop
-> fresh execution of the canonical start command
-> fresh Settings load
-> fresh engine/pool
-> fresh exact revision guard in every worker
-> post-start Health verification
```

No mutable process state or cached Health/schema result survives a restart.

### 19.3 Abrupt termination

Process kill or host failure may prevent graceful cleanup. PostgreSQL connection/session cleanup then follows OS/driver/database behavior and is not a substitute for the normal orderly stop contract.

---

## 20. Offline forward operating posture

M2 supports explicit downtime for schema/application changes.

Conceptual order for a future forward release is:

```text
prepare and verify the new release environment
-> stop the serving release
-> apply the new release's explicit Alembic upgrade
-> select/start the new release
-> require startup revision equality
-> verify Health
```

For the M2 first durable baseline, the database is empty/recreated before the root upgrade.

M2 does not support:

```text
simultaneous different release workers against one database
rolling schema/application compatibility
automatic downgrade
switching application release backward after schema change
production use of head -> base as rollback
```

`head -> base` exists only as destructive schema verification required by the contract, not as an operating recovery procedure.

---

## 21. Trust and transport realization

### 21.1 HTTP trust boundary

NETAUTO has no native authentication or authorization in M2.

The server listener is supported only inside an administratively trusted reachability boundary.

Direct exposure to an untrusted network or Internet is unsupported.

### 21.2 TLS

NETAUTO/Uvicorn owns plain HTTP inside that boundary.

Traffic crossing an untrusted segment must use an externally managed TLS terminator such as a reverse proxy, gateway or load balancer.

M2 does not own:

```text
certificate/private-key settings
certificate issuance/rotation/reload
mTLS
proxy product selection
forwarded-identity headers
```

Health and business routes share the same listener and boundary.

### 21.3 CLI HTTPS

The installed CLI follows `cli.md`:

```text
standard certificate and hostname verification
no --insecure or verify=false
no credential/profile storage
```

### 21.4 PostgreSQL transport

Database TLS, certificates and connection options are expressed entirely through `database_url` and the Psycopg/SQLAlchemy connection contract.

NETAUTO does not add parallel database TLS settings or log transport details.

---

## 22. Verification realization

Primary evidence bundles are:

```text
M2-VER-22 — exact startup revision gate
M2-VER-24 — one coherent versioned distribution
M2-VER-29 — Linux operating procedure
M2-VER-30 — trust and transport boundary
```

Supporting evidence includes:

```text
M2-VER-20 / 21
    durable root schema, graph and repeatability

M2-VER-23
    same-engine post-start Health

M2-VER-25 ... 28
    installed console client and HTTP-only boundary

M2-VER-31 / 32
    AS-IS regression and complete traceability
```

### 22.1 Settings and engine evidence

T1/T2 verification covers:

```text
all defaults and invalid boundaries
direct environment versus explicit secrets-dir precedence
no dotenv production discovery
database URL driver validation
exact create_async_engine keyword mapping
pool_recycle null -> -1
max_overflow -1 and pool_size 0 rejected
one engine shared by UoW, guard and Health
engine disposal on startup failure and shutdown
worker capacity formula documentation
```

### 22.2 Wheel evidence

T5/T8/T9/T10 verification covers:

```text
built wheel content inventory
installed distribution version
netauto console entrypoint
HTTPX/prompt-toolkit runtime dependencies after STACK-10 ratification
embedded runtime.pylock.toml equals frozen uv.lock export
clean dependency sync + --no-deps application install
server/CLI/Alembic execution outside Git checkout
CLI import path loads no Settings/persistence/driver
```

### 22.3 Alembic/head evidence

T5/T9 verification covers:

```text
netauto:migrations resolves from installed wheel
one base and one head
expected head derived through ScriptDirectory
actual heads derived through MigrationContext on real PostgreSQL
exact head -> serving
missing/base/old/newer/unknown/multiple/indeterminate -> startup failure
no endpoint served on failure
no alembic.command.upgrade/stamp in startup call graph
no handwritten expected revision constant
```

### 22.4 Linux process evidence

T9 executes the documented procedure in a clean Linux environment:

```text
create release environment
install from wheel only
load protected secret source
upgrade empty DB to head
start
Health 200
stop with orderly engine disposal
restart and pass fresh guard/Health
simulate runtime DB loss -> Health 503
```

The test may use temporary paths equivalent to `/opt/netauto`; path spelling is not semantic.

### 22.5 Negative evidence

Static and process verification proves absence of:

```text
automatic migration or stamp on startup
source-tree migration path requirement
second expected-revision authority
second runtime/Health engine
unbounded pool configuration
database URL in command/log/Health
default universal bind
native auth/TLS/cert management
Docker/Kubernetes/systemd/process-manager requirement
CLI dependency on database configuration
```

Executed evidence is required after implementation authorization, not before architecture freeze.

---

## 23. AS-IS and cross-owner consistency

### 23.1 Delivered runtime compatibility

M2 preserves:

```text
explicit Uvicorn factory
native asyncio
one process engine/pool
application-owned semantic UoW
explicit Alembic administration
stdlib logging ownership
no server wrapper CLI
```

It extends the runtime with consumed settings, packaged resources and a pre-serving revision guard without changing business transaction boundaries.

### 23.2 Persistence compatibility

```text
first durable root graph
    -> packaged unchanged as revision authority

installed graph
    -> unique expected head

live database
    -> exact current head
```

No migration is synthesized from metadata at runtime and no old development revision is retained as an upgrade source.

### 23.3 Health compatibility

The final lifespan confirms:

```text
same runtime engine/pool
revision guard before serving
Health composition after guard
engine disposal after serving
```

Health's `SELECT 1` and two-second runtime timeout remain unchanged.

### 23.4 CLI compatibility

The final wheel confirms:

```text
same-release server/CLI packaging
one netauto console entrypoint
HTTP-only execution
no Settings/database requirement on CLI-only target
```

CLI grammar, timeout, TLS and output behavior remain owned by `cli.md`.

### 23.5 Verification compatibility

Every runtime outcome has a stable evidence path already owned by `verification.md`. The embedded exact runtime lock is implementation evidence beneath `M2-VER-24`/`29`; it does not create a new contract criterion.

### 23.6 Technology-baseline handoff

`STACK-10` must be ratified before architecture freeze. That consolidation authorizes the HTTPX/prompt-toolkit runtime dependencies already accounted for by the wheel and lock design.

No other technology decision is required by this owner.

No contract reopening is required.

---

## 24. Traceability and closure

Primary ownership:

```text
M2-OUT-10
    exact startup schema compatibility

M2-OUT-13
    one coherent versioned distribution

M2-OUT-14
    reproducible Linux operating baseline

M2-OUT-15
    explicit trust and transport boundary
```

Direct acceptance ownership:

```text
M2-AC-22
M2-AC-24
M2-AC-29
M2-AC-30
```

Shared support:

```text
M2-AC-20 / 21
    installed durable Alembic graph

M2-AC-23
    post-start same-engine Health

M2-AC-25 ... 28
    installed CLI and same-release compatibility

M2-AC-31 / 32
    regression and traceability closure
```

Architecture-draft closure:

```text
application settings inventory and validation        CLOSED
secret-source and precedence model                    CLOSED
engine/pool mapping and worker capacity                CLOSED
one-wheel package content                              CLOSED
exact embedded runtime dependency lock                 CLOSED
installed Alembic package and explicit command         CLOSED
unique shipped-head discovery                          CLOSED
actual revision inspection                             CLOSED
startup timeout/equality/failure behavior              CLOSED
ASGI lifespan and shutdown ordering                    CLOSED
Health same-engine post-start composition              CLOSED
CLI packaging/import independence                      CLOSED
Linux layout/install/start/stop/restart procedure      CLOSED
offline first-baseline/forward posture                 CLOSED
trusted-boundary and external-TLS realization          CLOSED
verification hooks and negative surface                CLOSED
AS-IS/persistence/Health/CLI/verification cross-check  PASS
```

No runtime/deployment design point remains open in this owner.

This document remains `NOT FROZEN` until:

- `STACK-10` is formally ratified and consolidated in the technology baseline;
- final owner-by-owner traceability confirms every M2-OUT/M2-AC/M2-VER path;
- the complete M2 architecture set passes contract, AS-IS, authority and normative-hygiene consistency closure.

Executed installation, startup and operating evidence belongs to implementation slices and final delivery, not architecture freeze.
