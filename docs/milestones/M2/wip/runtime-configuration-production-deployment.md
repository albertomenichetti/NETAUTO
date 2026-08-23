# M2 WIP — Runtime Configuration & Production Deployment Discovery

**Status:** DISCOVERY CAPTURE — NON-NORMATIVE

This document captures decisions reached during M2 feature discovery for the candidate capability **Runtime configuration & production deployment**.

It is an execution aid under `wip/`. It does not replace `contract.md`, the M2 architecture set, `steps.md`, or the current delivered AS-IS. Contract-level outcomes will later be distilled into `contract.md`; semantic/technical decisions will later be assigned to the appropriate M2 architecture owners before implementation is authorized.

## 1. Capability boundary

M2 must define how to configure and execute NETAUTO in a production environment, but it does not need to automate the deployment.

The configuration boundary is:

```text
NETAUTO application configuration
    -> parameters consumed by the application/runtime itself

serving / deployment configuration
    -> parameters controlling how the process is executed
```

Examples:

```text
NETAUTO application configuration
    -> PostgreSQL connection
    -> database connection-pool configuration
    -> log level
    -> future settings with an actual application/runtime consumer

serving / deployment configuration
    -> bind host
    -> bind port
    -> Uvicorn worker count
```

Uvicorn worker count is therefore deployment/serving configuration, not an application `Settings` semantic property. It remains parametrizable through the Uvicorn launch command or an external process-management mechanism.

A Uvicorn worker is an independent OS process. Each worker owns its own application instance, event loop, SQLAlchemy engine, and connection pool.

## 2. Initial configuration inventory

### Application/runtime

The minimum M2 inventory is:

- PostgreSQL connection;
- connection-pool sizing/tuning defined below;
- log level, already present in the current baseline.

### Serving/deployment

The minimum M2 inventory is:

- bind host;
- bind port;
- Uvicorn worker count.

M2 does not require a custom process manager or service definition merely to expose these parameters.

## 3. PostgreSQL connection and secret handling

### Canonical connection parameter

NETAUTO keeps one canonical PostgreSQL connection setting:

```text
database_url
```

The URL contains the complete PostgreSQL connection specification, including credentials when required. Individual DB host, port, database name, username and password are not separate NETAUTO configuration authorities.

### Production secret handling

The production-recommended mechanism is a **local protected secret file** containing the complete `database_url` value.

Properties:

- owned/readable only by the dedicated NETAUTO system user;
- restrictive filesystem permissions;
- not committed to the repository;
- not passed on the command line;
- never emitted in logs.

Environment-based `NETAUTO_DATABASE_URL` may remain supported for development/testing and exceptional use, but it is not the recommended production deployment mechanism.

M2 does not introduce:

- Vault or another external secret manager;
- proprietary secret encryption;
- a NETAUTO secret database;
- YAML/TOML runtime files containing credentials;
- a mandatory production profile solely to disable environment configuration.

## 4. PostgreSQL connection pool

M2 exposes the following application/runtime settings.

```text
pool_size
    default = 10
    configurable

max_overflow
    default = 20
    configurable

pool_timeout
    default = 5 seconds
    configurable
    must be > 0

pool_recycle
    default = disabled
    configurable

pool_pre_ping
    default = disabled
    configurable
```

`pool_use_lifo` is not exposed in M2; SQLAlchemy's standard behavior remains authoritative unless a future requirement justifies a change.

Operational sizing relationship:

```text
maximum theoretical DB connections per worker
    = pool_size + max_overflow

maximum theoretical DB connections for one deployment
    = workers * (pool_size + max_overflow)
```

With the selected defaults:

```text
per worker maximum theoretical connections = 30
```

This multiplication must be called out in production documentation so PostgreSQL capacity is sized coherently with worker count.

## 5. Supported production platform

M2 production deployment targets:

```text
Linux
```

Support is distribution-agnostic. A specific distribution may be used in examples without becoming part of the M2 contract.

Docker and Kubernetes are explicitly out of scope for this capability.

## 6. Packaging and target installation

### Canonical artifact

The canonical distributable artifact is a **versioned Python wheel**.

```text
repository/source
    -> build
    -> versioned NETAUTO wheel

production target
    -> install wheel into a dedicated Python environment
```

The production runtime must not require a Git checkout of the repository.

### Runtime/dependency management

`uv` is the canonical tool on the production target, aligned with the project technology baseline.

Target runtime expectations:

- Linux;
- `uv` available;
- Python 3.14.x managed/resolved through the canonical toolchain;
- network/database access required by NETAUTO;
- dedicated system user;
- protected secret location.

### Artifact transfer boundary

M2 defines:

- how the artifact is built;
- how the target is prepared;
- how the artifact is installed;
- how NETAUTO is configured and started once the artifact is present.

M2 does **not** define how the wheel reaches the target. The following are out of scope:

- SCP/SFTP conventions;
- package or artifact registries;
- CI/CD delivery;
- transfer automation.

### Dedicated system user

Production uses a dedicated OS user for NETAUTO. The concrete username is operator-defined; examples use:

```text
netauto
```

### Reference filesystem layout

The recommended example root is:

```text
/opt/netauto/
    app/
    secrets/
```

Properties:

- the root path is an operational default/example, not semantic identity;
- `app/` follows `uv`'s standard internal layout; M2 does not invent a custom virtual-environment structure;
- `secrets/` contains protected secret material;
- the wheel need not be retained after installation;
- NETAUTO does not require a dedicated application-managed `logs/` directory.

### Canonical manual start form

The deployment documentation will define a canonical command conceptually equivalent to:

```bash
uv run uvicorn netauto.entrypoints.http:create_app \
    --factory \
    --host <host> \
    --port <port> \
    --workers <workers>
```

The exact final command may evolve during architecture/implementation as long as it preserves the agreed boundary: application settings belong to NETAUTO; serving settings belong to Uvicorn/deployment.

## 7. Process lifecycle scope

M2 defines ordinary manual process behavior:

```text
start
    -> canonical uv + Uvicorn launch

stop
    -> orderly process termination

restart
    -> stop followed by a fresh start
```

NETAUTO must release resources it owns during orderly shutdown.

M2 does not require implementation of:

- systemd unit files;
- automatic start at boot;
- process supervision;
- automatic restart policies;
- another process-manager integration.

Those may be added later as automation around an already-defined runtime procedure.

## 8. Alembic migrations and schema compatibility

### Migration execution remains explicit

Application startup must not execute schema migrations automatically.

Production installation/upgrade uses an explicit administrative migration step, initially remaining a manual Alembic invocation of the form:

```text
alembic -c ... upgrade head
```

M2 does not require a custom NETAUTO migration CLI wrapper.

### Migration history ships with the application artifact

The NETAUTO wheel must include the Alembic migration environment and revision history needed by that release.

Conceptually:

```text
NETAUTO wheel
    = application code
    + Alembic migration graph/history
```

The production target therefore does not require the Git repository merely to execute the migrations associated with the installed release.

### Expected schema authority

The installed release's **single Alembic head included in the wheel** is the authority for the database revision expected by that release.

There must not be a separately maintained handwritten revision constant duplicating this authority.

M2 verification should reject an artifact/migration graph with zero or multiple heads unless a future explicit architecture decision introduces supported branching.

### Startup schema guard

Before a worker begins serving requests, it must verify database schema compatibility.

The check compares:

```text
expected revision
    -> unique Alembic head shipped in the installed wheel

actual revision
    -> current database revision obtained through Alembic migration APIs
```

Compatibility requires **exact equality**.

```text
DB revision == expected revision
    -> worker may enter serving

DB revision < expected revision
    -> startup rejected

DB revision > expected revision
    -> startup rejected

DB unreachable / revision indeterminate
    -> startup rejected
```

A newer database schema is not implicitly considered backward compatible with an older NETAUTO release.

Every Uvicorn worker performs its own startup/lifespan validation before entering serving.

The guard detects incompatibility only; it never repairs or migrates the schema.

## 9. Upgrade procedure

M2 supports **offline/forward upgrades with explicit downtime**.

Canonical operational order:

```text
1. stop NETAUTO
2. install the new wheel
3. run the explicit Alembic upgrade to the new head
4. start the new NETAUTO release
5. startup schema guard verifies exact revision compatibility
```

M2 does not support or design:

- rolling upgrades;
- zero-downtime upgrades;
- simultaneous serving by different NETAUTO versions;
- application/schema rollback procedure.

Rollback may be designed in a future cycle.

## 10. Operator readiness checklist

M2 should document, but does not need to automate, an operator checklist for declaring a production installation ready.

The checklist will include at least evidence that:

```text
NETAUTO process starts successfully
expected database schema revision matches exactly
PostgreSQL is reachable/usable
/health/core reports a healthy core
```

This is operational documentation, not a new installer/orchestrator/validation command.

## 11. Explicit out-of-scope summary

For this capability M2 does not include:

- Docker;
- Kubernetes;
- systemd/service-manager implementation;
- start-at-boot automation;
- process supervision/automatic restart;
- artifact transfer/distribution mechanism;
- artifact/package registry;
- CI/CD deployment pipeline;
- custom secret-management system;
- automatic migrations at application startup;
- custom NETAUTO migration wrapper as a requirement;
- rolling or zero-downtime deployment;
- rollback procedure;
- automated installation-readiness command;
- direct application logging to a NETAUTO-owned log file.

## 12. Follow-up implications outside this capability

During this discovery a separate M2 candidate capability was identified:

```text
Logging operational review / introduction
```

It must be analyzed independently. This document does not define its contract.

The `/health/core` readiness check referenced by the operator checklist is owned by the separate M2 Health API capability and must likewise be designed independently.
