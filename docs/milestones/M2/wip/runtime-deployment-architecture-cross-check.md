# M2 Runtime, Packaging and Deployment Architecture Cross-Check

**Status:** PASS — RUNTIME/DEPLOYMENT DESIGN COMPLETE — STACK-10 CONSOLIDATION / FINAL ARCHITECTURE CLOSURE PENDING

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

## Review target

```text
docs/milestones/M2/architecture/runtime-deployment.md
```

The review compares the runtime design with:

```text
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/verification.md

docs/milestones/M2/wip/runtime-configuration-production-deployment.md
docs/milestones/M2/wip/cli-stack-10-proposal.md

docs/architecture/persistence.md
docs/architecture/verification.md
docs/general/technology_baseline.md

current Settings, engine/UoW, HTTP factory, Alembic environment,
pyproject/Hatchling and migration-source layout on branch M2
```

## Closure summary

```text
application settings inventory                 PASS
settings validation and source precedence      PASS
protected secret-file composition              PASS
engine/pool parameter realization              PASS
worker capacity model                          PASS
same-engine business/startup/Health ownership  PASS
one-wheel server/CLI/Alembic content            PASS
exact runtime dependency-lock delivery         PASS
installed migration package layout             PASS
standard explicit Alembic command              PASS
unique shipped-head authority                  PASS
actual revision inspection                     PASS
startup exact-equality guard                    PASS
startup/lifespan/shutdown ordering              PASS
Linux install/start/stop/restart procedure      PASS
first-baseline/offline-forward posture          PASS
trusted-boundary/TLS/database transport         PASS
M2-VER-22/24/29/30 implementation paths         PASS
open runtime-specific architecture point       0
contract reopening                             NOT REQUIRED
technology consolidation                       PENDING — STACK-10 only
executed implementation evidence                PENDING by governance
```

## Material findings

### 1. One wheel alone would not otherwise preserve the reviewed dependency resolution

The application wheel correctly carries compatibility ranges in `Requires-Dist`, while the project technology baseline treats `uv.lock` as the exact reviewed resolution.

A target with only the wheel and no checkout cannot run `uv sync --locked`. Resolving the wheel ranges directly could therefore produce dependencies different from the reviewed release.

The accepted design keeps one canonical NETAUTO artifact while embedding:

```text
netauto/release/runtime.pylock.toml
```

The file is generated from `uv.lock` with runtime dependencies only and no local project entry. The target:

```text
extracts the pylock from the wheel
-> uv pip sync
-> installs the NETAUTO wheel --no-deps
```

This preserves the one-wheel contract and exact dependency reproducibility without vendoring third-party packages or requiring Git.

### 2. The migration graph must be an installed package resource

The delivered source layout uses repository-root:

```text
migrations/
alembic.ini -> %(here)s/migrations
```

That cannot satisfy installation without checkout.

The accepted M2 source/install layout is:

```text
src/netauto/migrations/
```

with package-resource script location:

```text
netauto:migrations
```

The wheel includes `env.py`, template and exactly one durable root revision. The old development chain is not shipped.

### 3. Explicit Alembic administration remains standard Alembic

M2 does not need a new migration command in the official CLI.

The release environment already contains Alembic as a runtime dependency. An operator-owned non-secret `alembic.ini` selects `netauto:migrations`, while installed `env.py` loads the same database setting source.

```text
<venv>/bin/alembic -c <release>/alembic.ini upgrade head
```

remains an explicit administrative action and no startup path invokes upgrade or stamp.

### 4. Expected revision is discovered from the installed graph, never duplicated

The accepted startup path constructs an in-memory Alembic `Config`, loads `ScriptDirectory` from `netauto:migrations`, requires one base and one head, and uses the unique head as expected revision.

Rejected authorities are:

```text
filename parsing
release version
handwritten constant
operator setting
current database
```

This prevents release/schema drift caused by updating a migration without updating a second constant.

### 5. Actual revision uses the same worker engine

The worker uses `AsyncConnection.run_sync()` with Alembic `MigrationContext` to read current database heads.

The startup guard, Health and business UoWs therefore observe one worker's actual runtime connectivity/pool, while retaining different semantic responsibilities:

```text
startup guard
    -> exact compatibility before serving

Health
    -> SELECT 1 runtime readiness after serving

business UoW
    -> semantic transaction
```

No dedicated startup or Health engine can produce a misleading result.

### 6. Startup is bounded and cannot degrade into Health

The complete startup revision check has a fixed ten-second outer deadline.

Every mismatch, invalid graph, unreachable DB or timeout:

```text
disposes the engine
fails ASGI lifespan startup
serves no business or Health route
performs no migration
```

A later runtime database loss remains the bounded Health `503` case.

### 7. Pool bounds must remain finite

SQLAlchemy supports special unbounded values such as `pool_size=0` or `max_overflow=-1`, but those would invalidate the milestone's connection-capacity model.

The accepted validation is:

```text
pool_size >= 1
max_overflow >= 0
pool_timeout > 0
pool_recycle = null or positive
```

The documented deployment maximum is:

```text
workers * (pool_size + max_overflow)
```

plus external/administrative PostgreSQL consumers.

### 8. The production secret file has one explicit source boundary

The accepted composition uses:

```text
NETAUTO_SECRETS_DIR
    -> bootstrap location selector

<dir>/NETAUTO_DATABASE_URL
    -> complete database_url value
```

Direct `NETAUTO_DATABASE_URL` remains supported and has higher precedence. No database field is split into host/user/password settings, and the URL is absent from commands, Alembic config, Health and normal logs.

### 9. The canonical target is a release environment, not a source project

The target uses a versioned virtual environment under `/opt/netauto/releases/<version>` and direct installed executables.

It does not rely on:

```text
uv project discovery
pyproject.toml on the target
editable install
source migration path
Git checkout
```

The operator may use a `current` symlink, but installed distribution metadata and Alembic head remain the authorities.

### 10. CLI-only and server operation remain independent

The same wheel is valid on a CLI workstation without database configuration.

The runtime review confirms that the CLI import/execution path must not load Settings, persistence or driver code. Conversely, the server uses Uvicorn directly and does not invoke `netauto`.

The only remaining project-wide technology action is formal `STACK-10` consolidation.

### 11. The Linux process baseline is deliberately foreground/manual

M2 defines:

```text
foreground Uvicorn start
normal SIGTERM/Ctrl-C stop
fresh-process restart
post-start Health verification
```

It does not create a daemonizer, PID format or supervisor. External process management can wrap the contract in a future capability.

Canonical examples bind loopback, not `0.0.0.0`.

### 12. Production rollback is not inferred from Alembic downgrade verification

`head -> base` is destructive acceptance evidence only.

The operating posture is:

```text
first durable baseline from empty/recreated DB
offline explicit forward change
exact app/schema equality
```

M2 does not support application/schema rollback, rolling mixed versions or stamping an old schema.

## Cross-owner result

### Contract

```text
M2-OUT-10, 13, 14, 15        covered
M2-AC-22, 24, 29, 30         concretely realizable
scope/non-goal/security delta unchanged
```

### Persistence and Alembic

```text
one root / one head            aligned
fifteen-table graph            aligned
no M1 in-place migration       aligned
explicit administration        aligned
zero second expected-head      aligned
```

### Health

```text
same engine/pool                aligned
startup guard before serving    aligned
Health no Alembic query         aligned
engine disposal                 aligned
```

### CLI

```text
one wheel and console entry     aligned
HTTPX/prompt-toolkit deps        accounted for
CLI-only no DB settings          aligned
same-release guarantee           aligned
```

### Verification

```text
M2-VER-22                       complete path
M2-VER-24                       complete path
M2-VER-29                       executable Linux path
M2-VER-30                       positive/negative boundary
M2-VER-20/21/23/25..28/31/32    compatible supporting paths
```

### Technology baseline

```text
STACK-01 ... 09 compatible
STACK-10 proposal required and sufficient
no additional technology decision
```

## Remaining architecture work

Runtime/deployment itself has no open decision.

The architecture set still requires:

```text
formal STACK-10 ratification in technology_baseline.md
final owner-by-owner OUT/AC/VER traceability sweep
contract/AS-IS/cross-authority/normative-hygiene closure
architecture freeze commit
```

Executed wheel, PostgreSQL, process and Linux evidence follows implementation authorization.

## Final result

```text
runtime/deployment architecture  COMPLETE
contract compatibility           PASS
persistence/Alembic compatibility PASS
Health/CLI compatibility         PASS
verification-design coverage     PASS
runtime-specific open point      0
technology ratification          PENDING — STACK-10 only
implementation evidence          PENDING
contract reopening               NOT REQUIRED
```
