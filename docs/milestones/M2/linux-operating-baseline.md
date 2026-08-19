# M2 Linux operating baseline — NETAUTO 0.2.0

This document is operator guidance beneath the frozen M2 runtime/deployment
architecture. It describes the first-baseline installation of the single NETAUTO
0.2.0 application wheel; it does not redefine application semantics or add a
deployment product.

## Prerequisites and responsibilities

The supported target is Linux with CPython 3.14.x and `uv`. The runtime artifact
is `netauto-0.2.0-py3-none-any.whl`. Run it as a dedicated, unprivileged,
operator-defined account. The PostgreSQL target must be an empty or recreated
first-baseline database. Artifact transfer and the configured package index/cache
are operator-owned and outside NETAUTO.

NETAUTO application settings are `database_url`, `log_level`, `pool_size`,
`max_overflow`, `pool_timeout`, `pool_recycle`, and `pool_pre_ping`. Host, port,
and worker count are Uvicorn/deployment settings, not NETAUTO settings. The
operator owns `NETAUTO_SECRETS_DIR`, the database URL secret, its directory and
file permissions, and the PostgreSQL connection policy.

## Reference filesystem layout

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

After verification, keep the release directory immutable. `current` is only an
operator convenience symlink; neither it nor its target name is release or schema
authority. Keep secrets outside releases. The transferred wheel may be removed
after successful verification. NETAUTO creates no application-owned log
directory: foreground stdout/stderr remain under the invoking environment.

## Build and installation

Build from the selected, clean source revision:

```bash
uv sync --locked
uv export --frozen --no-dev --no-emit-project \
  --format pylock.toml --output-file pylock.runtime.toml
cmp pylock.runtime.toml src/netauto/release/runtime.pylock.toml
uv build --wheel
unzip -l dist/netauto-0.2.0-py3-none-any.whl
```

`uv` versions that enforce PEP 751 output basenames require a temporary name such
as `pylock.runtime.toml`; equality is checked against the canonical embedded
`runtime.pylock.toml`. A generated-lock difference is a build failure, not an
operator-editing step.

Transfer only the wheel to a staging location on the target. Then, as the
dedicated account, create the versioned target and install without a Git checkout,
editable install, target `pyproject.toml`, or development dependencies:

```bash
install -d /opt/netauto/releases/0.2.0
uv venv --python 3.14 /opt/netauto/releases/0.2.0/.venv
python3.14 - /staging/netauto-0.2.0-py3-none-any.whl \
  /opt/netauto/releases/0.2.0/runtime.pylock.toml <<'PY'
from pathlib import Path
from zipfile import ZipFile
import sys
with ZipFile(sys.argv[1]) as wheel:
    data = wheel.read("netauto/release/runtime.pylock.toml")
Path(sys.argv[2]).write_bytes(data)
PY
# uv 0.12.3 validates the PEP 751 basename; this is a byte-identical
# syntax-compatible carrier for the canonical extracted resource.
cp /opt/netauto/releases/0.2.0/runtime.pylock.toml \
  /opt/netauto/releases/0.2.0/pylock.runtime.toml
uv pip sync --python /opt/netauto/releases/0.2.0/.venv/bin/python \
  /opt/netauto/releases/0.2.0/pylock.runtime.toml
cmp /opt/netauto/releases/0.2.0/pylock.runtime.toml \
  /opt/netauto/releases/0.2.0/runtime.pylock.toml
rm /opt/netauto/releases/0.2.0/pylock.runtime.toml
uv pip install --python /opt/netauto/releases/0.2.0/.venv/bin/python \
  --no-deps /staging/netauto-0.2.0-py3-none-any.whl
```

Create the operator-owned non-secret file
`/opt/netauto/releases/0.2.0/alembic.ini`:

```ini
[alembic]
script_location = netauto:migrations
path_separator = os
```

It must contain no `sqlalchemy.url`, credential, expected-revision constant, or
checkout path. Verify metadata, entry points, imports, and the installed graph:

```bash
/opt/netauto/releases/0.2.0/.venv/bin/python - <<'PY'
from importlib.metadata import entry_points, version
from alembic.config import Config
from alembic.script import ScriptDirectory
from netauto.runtime.schema_guard import discover_unique_shipped_head
assert version("netauto") == "0.2.0"
assert any(ep.name == "netauto" and ep.value == "netauto.cli.main:main"
           for ep in entry_points(group="console_scripts"))
cfg = Config("/opt/netauto/releases/0.2.0/alembic.ini")
script = ScriptDirectory.from_config(cfg)
assert script.get_bases() == ["0001_m2_kernel"]
assert script.get_heads() == ["0001_m2_kernel"]
assert discover_unique_shipped_head() == "0001_m2_kernel"
PY
```

## Secret procedure

The dedicated NETAUTO user must own the secret directory and file. Apply mode
`0700` to the directory and `0600` to `NETAUTO_DATABASE_URL`:

```bash
install -d -m 0700 /opt/netauto/secrets
install -m 0600 /dev/null /opt/netauto/secrets/NETAUTO_DATABASE_URL
```

Write the complete `database_url`, with an optional final newline, into the file.
Use an unmistakable placeholder during preparation, for example
`<COMPLETE-OPERATOR-SUPPLIED-POSTGRESQL-PSYCOPG-URL>`; this document intentionally
contains no usable database URL or credential.

Configuration precedence is constructor/test injection, then a deliberately
supplied direct `NETAUTO_*` environment value, then files selected by the explicit
`NETAUTO_SECRETS_DIR`, then safe defaults. A direct environment value overrides
the corresponding secret file only when deliberately supplied.

## Explicit schema realization

Migration is a separate administrative action:

```bash
env NETAUTO_SECRETS_DIR=/opt/netauto/secrets \
  /opt/netauto/releases/0.2.0/.venv/bin/alembic \
  -c /opt/netauto/releases/0.2.0/alembic.ini upgrade head
```

Installation does not migrate. The CLI does not migrate. Server startup checks
the exact installed head and does not migrate, stamp, or repair. A pre-baseline
database is recreated rather than stamped or upgraded in place. `head -> base` is
destructive verification used by isolated tests; it is not an operating rollback
procedure.

If explicit migration fails, do not start the server or stamp around the failure.
Inspect the bounded Alembic diagnostic, correct the target/configuration, recreate
the first-baseline database when needed, and rerun the explicit command.

## Foreground start

Start one foreground worker on loopback:

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

`NETAUTO_POOL_RECYCLE` is omitted for its disabled default. The database URL is
never placed on the command line. `127.0.0.1` is the safe reference bind;
`0.0.0.0` is not an implicit safe default. Any explicitly broader bind requires
external reachability controls consistent with the trusted-boundary contract.

Missing or invalid settings, an unreachable database, or an uninitialized or
mismatched Alembic revision prevents startup before the serving listener becomes
ready. Correct the external condition; startup never remediates it.

## Readiness, stop, and restart

After startup, require `GET /health/core` to return HTTP 200 with the complete
Health body before sending business traffic. A 503 after successful startup means
the process is responding but PostgreSQL is not ready for work; investigate the
database/transport and do not treat the worker as ready.

Stop with the foreground interrupt or normal `SIGTERM`, and allow ASGI lifespan
shutdown to complete `engine.dispose()`. Restart means an orderly stop followed by
the same fresh canonical start. The fresh process reloads Settings, creates a new
engine/pool, reruns the exact revision guard, and must pass Health again. Abrupt
termination may skip cleanup; the external process owner must account for it.
NETAUTO defines no daemon, PID-file, supervision, automatic restart, or
start-at-boot behavior.

## PostgreSQL connection capacity

Plan the complete PostgreSQL connection budget before increasing workers or pool
limits:

```text
per worker maximum theoretical application connections
    = pool_size + max_overflow

deployment maximum theoretical application connections
    = workers * (pool_size + max_overflow)

defaults: 1 worker = 10 + 20 = 30
```

This excludes the explicit Alembic `NullPool` administrative connection, other
applications/operators, and PostgreSQL reserved/superuser connections.

## Trust and transport boundary

M2 has no native NETAUTO authentication or authorization. HTTP is supported only
inside an administratively trusted reachability boundary. Traffic across an
untrusted segment requires externally managed TLS termination. A firewall, VPN,
gateway, or reverse proxy remains an external reachability/transport control and
does not become a NETAUTO identity authority.

NETAUTO owns no server certificate/private-key lifecycle. The CLI always verifies
an HTTPS certificate and hostname through the administered system trust
environment; there is no CLI insecure or skip-verify mode. PostgreSQL transport,
TLS, and connection options live solely in `database_url`, not parallel NETAUTO
host, port, certificate, or credential settings.

## Failure handling and M2 non-goals

For invalid/missing settings, unreachable PostgreSQL, or an uninitialized or
mismatched revision, startup fails without serving. A failed explicit migration
is corrected administratively and never bypassed. After successful startup,
Health 503 keeps the worker non-ready while preserving its bounded response.
Prefer orderly termination so lifespan cleanup runs; abrupt termination has no
NETAUTO recovery promise.

The following are M2 non-goals and are not hidden facilities:

- Docker or Kubernetes;
- systemd or another process manager;
- automatic restart or start-at-boot;
- CI/CD or artifact transfer;
- rolling or zero-downtime deployment;
- application/schema rollback;
- backup or restore;
- native authentication, authorization, or server TLS.
