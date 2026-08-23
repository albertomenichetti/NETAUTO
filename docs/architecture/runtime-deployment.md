# Runtime, Distribution and Deployment — Current AS-IS

## Purpose and authority

This document owns process settings, PostgreSQL engine/pool composition, startup
schema compatibility, installed distribution, manual deployment and trust
boundaries. [`persistence.md`](persistence.md) owns schema and migration DDL;
[`health.md`](health.md) owns post-start readiness; [`cli.md`](cli.md) owns
client behavior. [`linux-operating-baseline.md`](linux-operating-baseline.md) is
the operator-facing projection of this owner.

## Operating model

The supported lifecycle is:

```text
build one versioned wheel
install one immutable release environment
synchronize exact runtime dependencies from the embedded lock
supply validated settings and protected database secret
run explicit installed Alembic upgrade
select the release
start foreground Uvicorn workers
require exact revision equality in every worker
verify /health/core
stop orderly and restart through a fresh process
```

NETAUTO does not provide containers, orchestration, systemd units, daemonization,
automatic restart/start-at-boot, artifact transfer/registry, CI/CD, rolling or
zero-downtime deployment, application/schema rollback, backup/restore, native
authentication, server TLS or network-policy automation.

## Settings contract

One immutable `Settings` value is loaded explicitly once per process/factory. Its
exact fields are:

| Setting | Environment name | Required/default | Validation |
|---|---|---|---|
| `database_url` | `NETAUTO_DATABASE_URL` | required | Valid SQLAlchemy URL with exact `postgresql+psycopg` driver. |
| `log_level` | `NETAUTO_LOG_LEVEL` | `INFO` | `CRITICAL`, `ERROR`, `WARNING`, `INFO` or `DEBUG`. |
| `pool_size` | `NETAUTO_POOL_SIZE` | `10` | Strict integer `>= 1`; boolean invalid. |
| `max_overflow` | `NETAUTO_MAX_OVERFLOW` | `20` | Strict integer `>= 0`; unlimited `-1` forbidden. |
| `pool_timeout` | `NETAUTO_POOL_TIMEOUT` | `5.0` | Finite strict number `> 0`. |
| `pool_recycle` | `NETAUTO_POOL_RECYCLE` | null/disabled | Positive whole seconds when supplied. |
| `pool_pre_ping` | `NETAUTO_POOL_PRE_PING` | `false` | Canonical boolean source form. |

Serving host, port, worker count and reload are Uvicorn/deployment inputs and are
not NETAUTO Settings. There is no generic configuration file, profile hierarchy,
dotenv discovery, mutable singleton or runtime reload. Importing the settings
module performs no environment read.

## Secret source

`NETAUTO_SECRETS_DIR` is a bootstrap selector for an explicit absolute existing
directory. Invalid explicit selection fails startup. The canonical file is:

```text
<secrets-dir>/NETAUTO_DATABASE_URL
```

Recommended Linux ownership/modes are dedicated user, directory `0700`, file
`0600`. Source precedence is exact:

```text
constructor/test values
direct NETAUTO_* environment
files in explicit NETAUTO_SECRETS_DIR
safe code defaults
```

The database URL is never written to Alembic configuration, command-line
examples, Health, normal logs, CLI state/output, wheel content or repository
files. Bootstrap diagnostics contain only bounded safe categories and release/
revision identifiers.

## Engine and pool

Each worker creates one process-lifetime SQLAlchemy `AsyncEngine`:

```text
isolation_level = READ COMMITTED
pool_size        = settings.pool_size
max_overflow     = settings.max_overflow
pool_timeout     = settings.pool_timeout
pool_recycle     = -1 when null, otherwise the positive value
pool_pre_ping    = settings.pool_pre_ping
```

The same engine/pool serves business write UoWs, coherent read UoWs, startup
revision inspection and the Health probe. There is no startup, migration or
Health-specific runtime engine. Engine construction is lazy; the startup guard
performs the first required checkout.

The theoretical connection maximum is:

```text
per worker  = pool_size + max_overflow
deployment  = workers * (pool_size + max_overflow)
default     = 30 per worker
```

Capacity planning also accounts for the separate Alembic administrative
connection, other clients and PostgreSQL reserved capacity.

Every constructed engine is explicitly disposed on normal shutdown, guard or
composition failure, and cancelled startup. Health owns no extra resource.

## Distribution artifact

The canonical application artifact is:

```text
netauto-<distribution-version>-py3-none-any.whl
```

One wheel contains:

```text
domain, application, persistence and server modules
official netauto CLI and console-entrypoint metadata
neutral HTTP transport DTOs
installed netauto:migrations environment and one-root graph
netauto/release/runtime.pylock.toml
distribution metadata
```

The wheel contains the Settings implementation and runtime composition code. It
contains no operator-supplied settings or configuration values, secrets,
certificates, source checkout, test/development tooling or deployment assets.
Installed distribution metadata is the sole release-version authority shared by
server, CLI and migration graph.

## Exact runtime dependency lock

`netauto/release/runtime.pylock.toml` is a PEP 751 export derived from committed
`uv.lock` with no dev group and no local project entry. It contains exact runtime
versions, markers and artifact hashes. Regeneration must be byte-identical.

A clean target extracts that resource from the wheel, runs `uv pip sync` against
the target Python, then installs the NETAUTO wheel with `--no-deps`. Installation
fails rather than falling back to range-only resolution. Third-party index/cache,
offline wheelhouse, signing, SBOM and vulnerability management remain
operator/platform responsibilities.

## Installed Alembic

The package resource is:

```text
netauto:migrations
```

It contains `env.py`, `script.py.mako` and the unique revision
`0001_m2_kernel`. Operator configuration is a non-secret file containing only:

```ini
[alembic]
script_location = netauto:migrations
path_separator = os
```

Installed `env.py` loads the same validated database URL source, uses a
synchronous SQLAlchemy engine with `NullPool`, supports an injected verification
connection and executes self-contained revision DDL. It never starts the ASGI
application or constructs the business async engine.

Schema realization is an explicit separate command:

```text
<release>/.venv/bin/alembic -c <release>/alembic.ini upgrade head
```

There is no `netauto migrate` command and no migration through installation,
startup, Health or the CLI.

## Shipped and live revision authority

Runtime creates an in-memory Alembic Config with only
`script_location = netauto:migrations`, loads `ScriptDirectory` and requires
exactly one base and one head. The unique installed head is the expected revision;
it is not parsed from filename, package version, an environment variable,
operator config or a handwritten constant.

Startup reads actual current heads through a connection borrowed from the runtime
AsyncEngine and `MigrationContext`. Compatibility is exact singleton equality:

```text
expected = 0001_m2_kernel
actual_heads = (0001_m2_kernel,)
```

No version table, base, older/different/newer/unknown revision, multiple heads,
unreadable graph/database or unreachable target rejects startup. Table
introspection and metadata comparison are not startup substitutes.

The entire guard has fixed timeout:

```text
CORE_STARTUP_SCHEMA_GUARD_TIMEOUT_SECONDS = 10.0
```

It covers pool checkout, connection, revision query, synchronous inspection and
cleanup. Failure disposes the engine and escapes lifespan before serving. The
guard never upgrades, stamps, writes revision state, creates tables or retries
indefinitely.

## ASGI lifespan and workers

The explicit factory is:

```text
netauto.entrypoints.http:create_app
```

It performs no database connection at module import. Each worker lifespan:

```text
configure logging
build runtime from complete Settings
discover unique shipped head
inspect and require exact live revision
compose Health probe/service on the same engine
publish runtime/services into application state
enter serving
dispose engine after serving
```

Each Uvicorn worker is an independent process with its own Settings, event loop,
engine/pool, guard and Health service. PostgreSQL is the only cross-worker semantic
authority. A failed worker exposes neither business nor Health routes.

## Linux support and release layout

The supported platform is Linux with CPython 3.14.x selected/managed by `uv` and
an unprivileged dedicated operator-defined account. A reference layout is:

```text
/opt/netauto/
    releases/<version>/.venv/
    releases/<version>/runtime.pylock.toml
    releases/<version>/alembic.ini
    current -> releases/<version>
    secrets/NETAUTO_DATABASE_URL
```

The versioned release becomes immutable after verification. `current` is an
operator convenience selected atomically after successful install, verification
and migration; it is never version/schema authority. The operating procedure is
fully specified in [`linux-operating-baseline.md`](linux-operating-baseline.md).

Supported initial realization uses an empty or deliberately recreated PostgreSQL
database. Stamping or upgrading an earlier development schema in place is not a
supported path. Explicit `head -> base` is destructive verification, not an
operating rollback.

Stop uses normal Uvicorn/foreground termination so ASGI shutdown disposes the
engine. Restart is an orderly stop followed by a fresh launch, Settings load,
engine/pool, revision guard and Health verification. There is no cached guard or
readiness result across processes.

## Trust and transport

NETAUTO has no native authentication or authorization. The listener is supported
only inside an administratively trusted reachability boundary. Plain HTTP is the
application protocol there. Traffic crossing an untrusted segment requires an
externally managed TLS terminator; NETAUTO owns no certificates, keys, rotation,
mTLS, proxy product or forwarded identity.

The official CLI validates HTTPS certificate and hostname and has no insecure
bypass. PostgreSQL TLS, credentials and connection options exist solely in
`database_url`; there are no parallel database host/port/TLS settings.

## Durable verification

Verification covers every setting/default/boundary and source precedence; exact
engine keyword mapping and disposal; wheel content and entrypoints; embedded-lock
equality; source-isolated dependency sync/install; installed package-resource
Alembic and explicit migration; graph and live revision matrices; pre-serving
failure; Health and CLI outside a checkout; start/stop/restart and transport cut;
protected secret procedure; connection capacity; HTTPS trusted, untrusted and
hostname-mismatch behavior; and static absence of automatic migration,
orchestration/security/secret surfaces.
