# Verification Architecture — Current AS-IS

## Purpose and authority

This document owns durable verification layers, environment rules and acceptance
quality gates for the current architecture. It does not redefine semantic,
persistence, API, Health, CLI or runtime behavior.

[`verification-concurrency-registry.md`](verification-concurrency-registry.md)
owns stable concurrency scenario IDs, predicates and deterministic recipes.
Concrete pytest node IDs and run ledgers are implementation/evidence
registries, not semantic authority.

## Evidence policy

A normative guarantee passes only through every required layer. A skipped,
xfailed, missing, blocked, timed-out or automatically rerun normative target is
not a pass. Fakes may prove pure orchestration; they never substitute for a real
PostgreSQL, public HTTP or installed-artifact claim.

Durable architecture describes what must be proven. Exact commands, environment
versions, pass counts, durations, hashes and review decisions belong to cycle
evidence records.

## Verification layers

### T0 — Pure domain

Proves plain-Python entity/value semantics, canonicalization, version/property
evolution, factual state transformations, lifecycle transition shapes, runtime
closure and semantic-view derivation.

### T1 — Application and Unit of Work orchestration

Proves transport-neutral command/query behavior, candidate construction, one
semantic operation/one UoW intent, no-op and bounded-restart decisions, store
coordination and finite failure selection.

Mocks/fakes are permitted only where the asserted property is independent of
PostgreSQL.

### T2 — Real PostgreSQL persistence

Proves live metadata/schema behavior, PK/UNIQUE/FK/CHECK/delete actions, canonical
JSONB codecs, aggregate commit/rollback, lock-plan SQL, constraint classification,
read snapshots and active Health query behavior.

T2 requires the externally supplied `TEST_DATABASE_URL`.

### T3 — Deterministic real-PostgreSQL concurrency

Proves supported interleavings, required blocking/progress, fresh post-wait reads,
advisory-gate visibility, PK/UNIQUE/FK arbitration, bounded whole-UoW restart and
supported-path deadlock absence through independent sessions.

Stress and sleep are not correctness authorities.

### T4 — Public HTTP contract

Proves the exact 63 business plus one Health operation inventory, strict request
carriers, omission/null distinction, DTO/status/Location/failure mapping, bounded
details, projection/filter/order/cursor behavior, OpenAPI closure and forbidden
surfaces. Lifespan-sensitive cases use the real ASGI lifespan.

### T5 — Migration, schema lifecycle and startup compatibility

Proves the installed one-root `0001_m2_kernel` graph, fresh upgrade, owned
downgrade/repeatability, exact fifteen-table schema, metadata drift `[]`, package
resource discovery, startup revision equality and absence of automatic migration.

### T6 — Targeted property-based verification

Applies where algebraic coverage is materially stronger than examples, including
primitive canonicalization, factual property maps, data/schema change
transformations, cursor binding and lock-plan sorting/coalescence. It supplements
deterministic examples.

### T7 — Supplementary randomized/stress verification

Discovers problems but never replaces a stable deterministic scenario. A material
finding is reduced to a deterministic regression where reasonably possible.

### T8 — CLI client, terminal and process

Proves parsing, selector planning, session transitions, HTTP trace truthfulness,
FORMATTED/JSON rendering, PTY-visible editing/history, stdout/stderr/exit behavior,
HTTPS validation and HTTP-only authority.

### T9 — Installed artifact and Linux operation

Runs against a wheel installed outside the repository import path in a clean
release environment. It proves package contents, exact lock sync, console and
Alembic entrypoints, explicit migration, startup guard, server/Health/CLI,
stop/restart/disposal and the material operator procedure.

### T10 — Static traceability and negative surface

Proves exact finite inventories and absences: route/CLI/schema/settings/scenario
censuses, constraints/indexes, import boundaries, no automatic migration, no
native auth/TLS/insecure CLI, no deployment/backup/observability assets, no
unresolved normative placeholder and no historical execution aid as authority.

Static evidence does not replace runtime evidence where behavior is material.

## Toolchain and environment

The ratified toolchain is CPython 3.14.x, `uv` with committed lock, pytest and
pytest-asyncio, HTTPX, real PostgreSQL, Hypothesis where justified, Ruff, Pyright
strict and coverage.py as diagnostic evidence.

Canonical project gates are:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
required focused and integrated pytest selections
full repository pytest suite
```

`NETAUTO_DATABASE_URL` is the runtime/administrative target.
`TEST_DATABASE_URL` is the automated real-PostgreSQL target. Tests do not
provision or silently replace PostgreSQL and never fall back to SQLite, a fake,
Docker or Testcontainers.

Concurrent tests use unique semantic identities and independent connections.
Interfering PostgreSQL suites do not use unsafe database-level parallelism.
Cleanup begins only after participating sessions terminate.

T9 uses a clean directory/venv, wheel-only application install, embedded-lock
dependency sync, no checkout import path and a dedicated test database. HTTPS
uses a controlled CA and covers trusted matching hostname, untrusted CA and
hostname mismatch; no external network is required.

## Exact current inventories

Machine-checkable registries require:

```text
mutation primitives             41
semantic family blocks          15
unordered interaction cells    861
safety predicates               21
canonical concurrency scenarios 83
authoritative tables            15
Alembic base/head                 1 / 1 = 0001_m2_kernel
business HTTP operations         63 = 41 mutation + 22 read
Health operations                 1
CLI remote operations            63
CLI local commands                8
public error codes               23
```

Every finite inventory compares exact sets, never a minimum count. Public
operation, CLI registry and generated OpenAPI sets are equal where applicable.
Every stable concurrency scenario maps to a concrete collected target and one
primary deterministic recipe. Every safety predicate maps to one or more
scenarios.

## Deterministic concurrency harness

Roles are:

```text
CTL  orchestration only
OBS  fresh observation/introspection
B    optional real PostgreSQL blocker
T1/T2/T3 independent semantic workers
```

Stable observable phases include UoW start, discovery complete, lock plan built,
gate/row waiting and acquired, protected reread, stale plan, dependencies
stabilized, DML/closure/metadata/event writes, constraint arbitration, commit,
rollback and UoW restart.

A test-only interceptor may pause or observe a named phase only when it does not
change candidate data, issue semantic SQL, acquire a production lock, alter
isolation, commit/rollback, change failure mapping or choose another production
path.

Required blocking is proved primarily with `pg_blocking_pids(waiter_pid)`
containing the known blocker. Required progress is a positive production phase
reached while another transaction remains open. Timeouts are bounded hang guards.

Every worker records SQLSTATE structurally. Any supported scenario observing
`40P01` fails immediately; it is never retried. Unexpected `40001` is equally
forbidden. Negative controls have their own exact finite expected census and do
not weaken supported-path requirements.

## Domain and persistence obligations

Verification preserves:

- stable/version identities, lifecycle/default/generation rules and exact pins;
- complete property/component/Relationship declaration histories;
- primitive canonicalization and optional/non-null value rules;
- Object DATA_CHANGE/SCHEMA_CHANGE and ownership semantics;
- Relationship topology, capability admission, complete closure and factual
  CREATE/DATA_CHANGE/SCHEMA_CHANGE/DELETE;
- lifecycle transition codecs, semantic-view fan-out and history independent of
  live metadata;
- coherent before-or-after aggregate/page reads and full corruption failure;
- all-or-nothing header/child/closure/event behavior;
- reference lifetime, delete blockers and exact-ID ABA safety.

Real PostgreSQL schema checks assert exact columns/types/nullability/defaults,
named PK/UNIQUE/CHECK/FK/delete actions and exact explicit indexes, sort order,
partial predicates and INCLUDE columns. Forbidden GIN/expression/duplicate
indexes and unowned schema objects are checked negatively.

The migration suite proves empty database to head, head to base ownership,
base/head repeatability, failure rollback, external sentinel survival, one graph
root/head and `compare_metadata == []`.

## HTTP, Health and CLI obligations

HTTP tests assert all strict invalid-input families, exact success and error
envelopes, safe bounded details, keyset cursor binding, complete projections,
route-specific ordering and absence of generic PUT/PATCH/action, auth, migration,
autonomous Resolution/declaration and property-search surfaces.

Health tests separate application classification, exact `SELECT 1`, timeout
cleanup and HTTP mapping. Real PostgreSQL proves shared-engine use, connection
return, deterministic pool starvation and recovery. Responses never expose
database/driver/secret details.

CLI verification derives help/dispatch from one static registry, covers every
parameter and selector family, requires fresh command-local ledger/memo state,
records every actual HTTP exchange once, proves mutation no-enrichment and
GET-only bounded read enrichment, and checks interactive PTY and non-interactive
process contracts. Static imports prove no direct server kernel/database path.

## Runtime, distribution and trust obligations

Build evidence proves the one wheel contains server, CLI, neutral DTOs, installed
migration graph and exact runtime lock, with consistent distribution version and
no source/development/deployment content.

Source-isolated installation proves exact dependency synchronization, wheel
`--no-deps` install, explicit Alembic, unique graph discovery, no automatic
migration, startup failure for every non-exact revision, healthy start, runtime
Health 503 after transport loss, orderly disposal and fresh restart guard.

Settings tests cover the exact seven-field inventory, defaults, strict boundaries,
source precedence and absence of dotenv/global load. Trust evidence proves no
native authentication/authorization/401/403/security scheme, no unsafe universal
bind guidance, verified CLI HTTPS, no insecure bypass, database transport solely
in `database_url`, and no secret in argv/log/Health/CLI/config/artifact.

## Negative-surface policy

The repository contains no implemented product surface for:

```text
Relationship property EAV/search/default remediation
autonomous Resolution or declaration CRUD
event-set resource or event-sourced current state
generic query/sort/PATCH/bulk/action protocol
native auth, credentials, server TLS or insecure CLI
container/orchestrator/process-manager/deployment pipeline
cluster/multi-region/high-availability operation
backup/restore/PITR/replica/disaster-recovery automation
metrics/tracing/dashboard/log-shipping platform
automatic migration/stamp/repair
multiple heads or alternate schema compatibility
```

Normative architecture may state these exclusions without being mistaken for an
implementation asset. Static policy audits tracked code, scripts, dependencies,
entrypoints, config/deployment assets and non-normative operator documents.

## Repository and release gate

Release verification passes only when all applicable
focused and integrated layers are green and:

```text
normative skip / xfail / rerun        0 / 0 / 0
supported-path 40P01                  0
unexpected 40001                      0
negative-control SQLSTATE             exact expected census
schema compare_metadata               []
new unexplained warnings              0
locked environment and build          PASS
artifact reproducibility/invariance   PASS as applicable
blocking findings                     0
```

A reviewed third-party deprecation may be censused without imposing an arbitrary
zero-warning semantic rule.

## Evidence durability and evolution

Permanent registries preserve domain invariant codes, 41 mutation names, 83
scenario IDs, 21 predicate codes, recipes, public error/route identifiers,
settings and schema-object names. Cycle outcome/acceptance/evidence IDs, slice
names, review findings, commit hashes and run counts remain historical
evidence and are not current architecture identifiers.

A semantic change updates its owner, dependent owners, finite registry, focused
regression and required integrated gate together. Coverage percentage and raw
test count never compensate for a missing semantic proof.
