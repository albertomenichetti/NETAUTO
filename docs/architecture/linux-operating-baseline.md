# Linux operating baseline — NETAUTO 0.2.0

## Purpose and authority

This is the executable operator projection of
[`runtime-deployment.md`](runtime-deployment.md) for the current release. The
runtime document owns semantics; this guide supplies the concrete Linux commands.
It does not define a deployment product or an alternate configuration authority.

## Prerequisites and responsibilities

The supported target is Linux with CPython 3.14.x and `uv`. The artifact is
`netauto-0.2.0-py3-none-any.whl`. A dedicated unprivileged, operator-defined
account runs the release. PostgreSQL is externally managed and the target database
is empty or deliberately recreated for this root schema.

Artifact transfer, package index/cache, account creation, PostgreSQL lifecycle,
network reachability and external TLS termination are operator responsibilities.

## Settings inventory

| Environment name | Required/default | Accepted value |
|---|---|---|
| `NETAUTO_DATABASE_URL` | required | Complete SQLAlchemy URL with exact `postgresql+psycopg` driver. |
| `NETAUTO_LOG_LEVEL` | `INFO` | `CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`. |
| `NETAUTO_POOL_SIZE` | `10` | Integer `>= 1`; boolean/fractional invalid. |
| `NETAUTO_MAX_OVERFLOW` | `20` | Integer `>= 0`; `-1`/unlimited invalid. |
| `NETAUTO_POOL_TIMEOUT` | `5.0` | Finite number `> 0`. |
| `NETAUTO_POOL_RECYCLE` | omitted/disabled | Positive whole seconds when set. |
| `NETAUTO_POOL_PRE_PING` | `false` | Canonical `true` or `false`. |

Host, port and worker count are Uvicorn arguments, not NETAUTO settings. Invalid
settings fail bootstrap before serving. A revision mismatch fails the separate
startup guard. PostgreSQL loss after successful startup leaves an HTTP process
whose Health result is 503.

## Reference layout

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

The release directory is immutable after verification. `current` is an
operator-owned convenience, not release or schema authority. Secrets stay outside
release directories. NETAUTO creates no application log directory; foreground
stdout/stderr belong to the invoking environment.

## Build

From the selected clean source revision:

```bash
uv lock --check
uv sync --locked
uv export --frozen --no-dev --no-emit-project \
  --format pylock.toml \
  --output-file src/netauto/release/pylock.runtime.toml
cmp src/netauto/release/pylock.runtime.toml \
  src/netauto/release/runtime.pylock.toml
rm src/netauto/release/pylock.runtime.toml
uv build --wheel
unzip -l dist/netauto-0.2.0-py3-none-any.whl
```

The regeneration uses the same relative output path used by permanent evidence,
so the generated uv command header is byte-identical. A difference is a build
failure; the embedded lock is never edited to match output.

Transfer only the wheel to a target staging path.

## Filesystem ownership

A privileged administrator performs only the root-directory ownership handoff.
Substitute administered account/group names:

```bash
NETAUTO_USER=netauto
NETAUTO_GROUP=netauto
sudo install -d -o "$NETAUTO_USER" -g "$NETAUTO_GROUP" -m 0755 /opt/netauto
sudo -u "$NETAUTO_USER" install -d -m 0755 /opt/netauto/releases
sudo -u "$NETAUTO_USER" install -d -m 0700 /opt/netauto/secrets
```

Every later command runs as the dedicated account.

## Wheel-only installation

```bash
install -d /opt/netauto/releases/0.2.0
uv venv --python 3.14 /opt/netauto/releases/0.2.0/.venv
/opt/netauto/releases/0.2.0/.venv/bin/python - \
  /staging/netauto-0.2.0-py3-none-any.whl \
  /opt/netauto/releases/0.2.0/runtime.pylock.toml <<'PY'
from pathlib import Path
from zipfile import ZipFile
import sys

with ZipFile(sys.argv[1]) as wheel:
    data = wheel.read("netauto/release/runtime.pylock.toml")
Path(sys.argv[2]).write_bytes(data)
PY
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

The release venv Python performs lock extraction; no global `python3.14`
executable is assumed after venv creation. The target needs no Git checkout,
editable install, project `pyproject.toml` or development group.

Create `/opt/netauto/releases/0.2.0/alembic.ini`:

```ini
[alembic]
script_location = netauto:migrations
path_separator = os
```

It contains no `sqlalchemy.url`, credentials, expected-revision constant or
checkout path.

Verify installed metadata, entrypoint and graph:

```bash
/opt/netauto/releases/0.2.0/.venv/bin/python - <<'PY'
from importlib.metadata import entry_points, version
from alembic.config import Config
from alembic.script import ScriptDirectory
from netauto.runtime.schema_guard import discover_unique_shipped_head

assert version("netauto") == "0.2.0"
assert any(
    ep.name == "netauto" and ep.value == "netauto.cli.main:main"
    for ep in entry_points(group="console_scripts")
)
cfg = Config("/opt/netauto/releases/0.2.0/alembic.ini")
script = ScriptDirectory.from_config(cfg)
assert script.get_bases() == ["0001_m2_kernel"]
assert script.get_heads() == ["0001_m2_kernel"]
assert discover_unique_shipped_head() == "0001_m2_kernel"
PY
```

## Secret procedure

```bash
chmod 0700 /opt/netauto/secrets
install -m 0600 /dev/null /opt/netauto/secrets/NETAUTO_DATABASE_URL
```

The dedicated account owns directory and file. Write the complete operator
PostgreSQL URL to the file, optionally ending in newline. This guide intentionally
contains no usable URL or credential.

Settings source precedence is constructor/test injection, direct `NETAUTO_*`
environment, explicit secrets directory, then safe defaults. A direct environment
value overrides the file only when deliberately supplied.

## Explicit schema realization

```bash
env NETAUTO_SECRETS_DIR=/opt/netauto/secrets \
  /opt/netauto/releases/0.2.0/.venv/bin/alembic \
  -c /opt/netauto/releases/0.2.0/alembic.ini upgrade head
```

Installation, CLI and server startup do not migrate. Startup only requires exact
installed-head equality. An earlier development database is recreated, not stamped
or upgraded in place. `head -> base` is destructive isolated verification, not an
operating rollback.

If migration fails, do not start or stamp around it. Correct the external
configuration/target, recreate the empty target when appropriate and rerun the
explicit command.

## Atomic release selection

Only after dependency synchronization, wheel verification and successful
migration:

```bash
ln -s releases/0.2.0 /opt/netauto/.current-0.2.0
mv -T /opt/netauto/.current-0.2.0 /opt/netauto/current
test "$(readlink /opt/netauto/current)" = "releases/0.2.0"
```

The temporary symlink and `mv -T` provide same-filesystem atomic selection.

## Foreground start

```bash
env \
  NETAUTO_SECRETS_DIR=/opt/netauto/secrets \
  NETAUTO_LOG_LEVEL=INFO \
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
absent from argv. Loopback is the safe reference bind. Any broader explicit bind
requires external reachability controls; `0.0.0.0` is not presented as an
implicit safe default.

Missing/invalid settings, an unreachable database or an uninitialized/mismatched
revision prevents serving. Startup never remediates these conditions.

## Readiness, stop and restart

After startup, require `GET /health/core` to return 200 with the complete valid
Health DTO before business traffic. A 503 means the process is HTTP-capable but
PostgreSQL is not ready.

Stop through the foreground interrupt or normal `SIGTERM` and allow lifespan
shutdown to dispose the engine. Restart is an orderly stop followed by the same
fresh command. The process reloads settings, creates a fresh pool, reruns the exact
revision guard and must pass Health again. NETAUTO defines no daemon, PID file,
supervisor, automatic restart or start-at-boot behavior.

## PostgreSQL capacity

```text
per-worker maximum = pool_size + max_overflow
deployment maximum = workers * (pool_size + max_overflow)
default one worker  = 10 + 20 = 30
```

This excludes the separate Alembic `NullPool` connection, other clients and
PostgreSQL reserved/superuser capacity.

## Trust and transport

NETAUTO has no native authentication or authorization. HTTP is supported only
inside an administratively trusted reachability boundary. Traffic across an
untrusted segment requires external TLS termination. Firewall, VPN, gateway or
reverse proxy remains external infrastructure, not a NETAUTO identity authority
or bundled configuration.

The server owns no certificate/private-key lifecycle. The CLI verifies HTTPS
certificate and hostname through administered trust and exposes no insecure
bypass. PostgreSQL TLS and connection options exist solely in `database_url`.

## Failure boundary

Invalid settings and revision mismatch fail before serving. Explicit migration
failure is corrected administratively and never bypassed. Runtime Health 503 does
not trigger migration, engine rebuild or automatic process restart. Abrupt
termination may skip orderly cleanup and has no application recovery promise.

No container, process manager, deployment pipeline, high-availability mechanism,
backup/restore process or observability platform is hidden behind this procedure.

