# Codex implementation prompt — M1-S01

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S01 — PostgreSQL schema, migration, UoW and deterministic-test foundation
```

from `docs/milestones/M1/steps.md`.

M1-S00 is complete. Do not implement M1-S02 or any domain/application/API capability.

## Mandatory pre-flight

Before changing files, read and obey:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-semantic-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-object-ownership.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-relationship.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
```

For physical column/check details whose semantic shape is owned by a domain companion, also consult the relevant frozen architecture document rather than guessing. In particular, lifecycle event kinds/row families are defined by `object-lifecycle-changelog.md`, and ObjectTemplate declaration column semantics are defined by the ObjectTemplate companion documents.

Confirm from the repository itself that:

```text
M1 contract      = FINAL / FROZEN
M1 architecture  = globally FROZEN as a set
M1 steps         = FINAL / FROZEN
M1-S00           = COMPLETED
current step     = M1-S01
STACK-01..09     = RATIFIED
```

Individual architecture files may still carry old authoring labels such as `DRAFT`; the global architecture index is the set-level freeze authority. Do not reinterpret those headers as open design.

If normative authorities conflict, stop the affected work and report the contradiction instead of choosing one.

Do not use historical Git code as an implementation template.

## Objective

Realize the complete frozen PostgreSQL physical authority and the minimal runtime transaction/test substrate required by all subsequent M1 vertical slices.

S01 is a foundation step. It intentionally creates physical tables that later domain capabilities will use, but it does **not** implement those capabilities.

The output of S01 must provide:

```text
complete 13-table PostgreSQL schema authority
+ one reviewed Alembic head
+ async SQLAlchemy Core/Psycopg runtime engine composition
+ minimal explicit semantic-UoW transaction substrate
+ deterministic real-PostgreSQL concurrency-test harness foundation
```

## Hard scope boundary

S01 MUST NOT implement:

```text
PrimitiveType parsing/canonicalization/constraints
DataType commands or reads
ObjectTemplate commands/effective-schema resolution
Object commands/runtime validation
ownership ATTACH/DETACH/cycle semantics
RelationshipDefinition certification/conflict semantics
runtime Relationship closure/convergence
lifecycle event production by semantic operations
/api/v1/core routes or DTOs
public failure/error mapping
cursor/list implementation
JSON Schema
ORM Session / AsyncSession
repository framework / generic DAO framework
generic command bus / service container
Docker / Testcontainers / DB provisioning
```

Raw persistence tests may insert structurally valid rows directly in order to prove DB constraints/transactions. Such tests are persistence-level evidence only and must not be presented as domain-operation implementation.

## 1. Complete SQLAlchemy Core metadata

Populate the authoritative `MetaData` seam created in S00 with exactly the frozen 13-table authority map:

```text
# model plane
datatypes
datatype_versions
object_templates
object_template_versions
object_template_properties
object_template_components
relationship_definitions
relationship_resolutions

# data plane
objects
object_components
relationships
runtime_relationship_resolutions

# history
object_lifecycle_events
```

Do not create additional authority tables, including:

```text
primitive_types
effective-schema cache
runtime property EAV
ancestry closure
reverse dependency table
generic member table
surrogate DTV/OTV/runtime-resolution identity
```

Use SQLAlchemy Core only. PostgreSQL-specific types/constructs are expected where the architecture requires them.

### Physical type baseline

Use the frozen PostgreSQL representation, including:

```text
UUID          native PostgreSQL UUID
JSON state    JSONB
version/revision/position  INTEGER with positive checks where normative
status/value_mode/base_type/lifecycle kind  TEXT + CHECK
abstract/symmetric/required BOOLEAN
timestamps    TIMESTAMPTZ
model/member identifiers TEXT + CHECK
```

Do not use PostgreSQL ENUM, CITEXT, portability shims, or ORM mapped classes.

### Identity/default rules

Preserve exact semantic identities.

```text
DataTypeVersion       PK(datatype_id, version)
ObjectTemplateVersion PK(template_id, version)
ObjectTemplateProperty PK(template_id, template_version, name)
ObjectTemplateComponent PK(template_id, template_version, name)
object_components     PK(child_object_id)
runtime_relationship_resolutions
    PK(resolution_id, from_object_id, to_object_id)
```

No surrogate version/runtime-resolution IDs.

Current domain UUID identities (`DataType.id`, `ObjectTemplate.id`, `Object.id`, `RelationshipDefinition.id`, `RelationshipResolution.id`, `Relationship.id`) are kernel/application-generated later and therefore receive **no PostgreSQL UUID default merely for convenience**.

`object_lifecycle_events.id` is different: it is a persistence row identity with no domain semantics and must be generated by PostgreSQL. Use a PostgreSQL-side random UUID default such as `gen_random_uuid()`; do not use `uuidv7()` because the event ID has no temporal semantics.

`object_lifecycle_events.occurred_at` must use PostgreSQL `transaction_timestamp()` (or the documented equivalent `CURRENT_TIMESTAMP`) as the server default.

Do not add server defaults for canonical semantic state such as `{}` merely to make raw inserts convenient unless a frozen persistence contract explicitly assigns that default to PostgreSQL.

## 2. Exact constraint/FK realization

Implement every normative PERSIST-01..15 PK/UNIQUE/FK/CHECK/NOT NULL/delete/index rule.

### FK delete policy

`CASCADE` is allowed only for owned child state of the same aggregate:

```text
DataType -> DataTypeVersion
ObjectTemplate -> ObjectTemplateVersion
ObjectTemplateVersion -> local Property/Component
RelationshipDefinition -> RelationshipResolution
Relationship -> RuntimeRelationshipResolution
```

Current cross-aggregate/domain references use immediate `RESTRICT` according to PERSIST-14.

Historical identities in `object_lifecycle_events` must **not** have live FKs.

Do not introduce `SET NULL` current-domain references.

Foreign keys that are the final referential race authority must remain immediate / non-deferred; do not introduce deferred constraints.

### Exact composite references and intentional denormalization

Preserve both intentional M1 denormalizations exactly:

1. `object_template_versions.parent_template_id` alongside `parent_version`, while `object_templates.parent_template_id` remains stable-lineage authority.
2. `runtime_relationship_resolutions.relationship_definition_id`, with the composite FKs that force Relationship header and Resolution to belong to the same Definition.

Keep the technical UNIQUE support structures required for composite FKs:

```text
relationships(id, relationship_definition_id)
relationship_resolutions(id, relationship_definition_id)
```

These are support structures, not additional business identities.

Do not normalize either denormalization away.

### CHECK discipline

Implement DB checks that are actually assigned to the persistence layer. Do **not** strengthen the DB schema with semantic checks merely because they appear easy to express if the frozen architecture assigns that predicate to UoW/domain enforcement.

Examples of valid structural DB checks include, as specified by PERSIST:

```text
positive version/revision/position
closed TEXT vocabularies
model/member identifier grammar and bounds
namespace grammar/bounds
JSONB top-level object shape where required
Object canonical_name length 1..255
ownership parent != child
root/non-root exact-parent null-pair structure
required=false -> migration_default IS NULL
lifecycle event-family column-shape checks where directly structural
```

Do not attempt DB enforcement of effective schema, active model graph, lifecycle transitions, canonical primitive values inside JSON, ownership acyclicity, Relationship aggregate completeness, or other UoW-owned predicates.

`core` / `core.*` reservation remains application admission, not a DB CHECK.

## 3. PERSIST-15 indexes

Implement the complete normative index set from `persistence-model.md`, including model dependency, Object/ownership, Relationship runtime and lifecycle read-path indexes.

Pay particular attention to the API-driven indexes already frozen into PERSIST-15:

```text
objects(canonical_name, id)
object_lifecycle_events(kind, occurred_at, id)
object_lifecycle_events(relationship_name, occurred_at, id)
    WHERE relationship_name IS NOT NULL
```

Do not add speculative GIN/property/snapshot/closure indexes.

## 4. Alembic initial M1 schema revision

Create one coherent initial Alembic revision that builds the complete frozen M1 physical schema from an empty/clean PostgreSQL test target and can downgrade it back to the pre-M1/base state.

The revision may originate from Alembic autogenerate as a candidate, but the committed revision must be manually reviewed against PERSIST-01..15. Autogenerate output is not authority.

The migration and SQLAlchemy metadata must remain aligned.

Do not split the initial revision merely by domain if one coherent revision is simpler. Conversely, do not optimize for migration aesthetics at the expense of exact FK/constraint ordering.

Handle cyclic/composite FK creation explicitly and transparently (for example via named constraints / ALTER ordering / SQLAlchemy `use_alter` where genuinely needed). Never weaken/remove a frozen FK to simplify DDL ordering.

### Alembic runtime path

Alembic remains an explicit administrative/deployment operation. It does not run from FastAPI startup/lifespan.

It is acceptable and preferable to keep the Alembic CLI path synchronous even though NETAUTO runtime persistence is async; migration execution is a separate admin boundary and Psycopg 3 supports the same `postgresql+psycopg://` dialect for sync engine creation.

For migration tests, do not copy `TEST_DATABASE_URL` into the runtime `NETAUTO_DATABASE_URL` environment variable as an implicit fallback. Refactor `migrations/env.py` if needed to support an explicitly injected Alembic connection/config attribute for tests while preserving `Settings`-based runtime CLI configuration as the default administrative path.

Use the official Alembic connection-sharing pattern rather than introducing a `TESTING` branch in migration semantics.

## 5. Async runtime engine composition

Implement the process-lifetime PostgreSQL engine/pool composition required by STACK-01/02/05.

Use:

```text
SQLAlchemy AsyncEngine
SQLAlchemy Core
Psycopg 3 async dialect
postgresql+psycopg://...
READ COMMITTED
```

Use `create_async_engine()`; the `postgresql+psycopg` dialect automatically selects the async Psycopg implementation in this path.

Because the project admits SQLAlchemy 2.x, declare/use the SQLAlchemy asyncio extra if needed for a reproducible async runtime (`sqlalchemy[asyncio]`) rather than relying on an incidental transitive `greenlet` installation.

Do not add `psycopg_pool`; SQLAlchemy owns the normal runtime pool.

Do not invent pool-size/tuning settings in S01 unless a concrete S01 test/runtime requirement consumes them. Defaults are sufficient at this stage.

FastAPI lifespan should own creation/exposure/disposal of process-lifetime engine resources in a small explicit runtime context or equivalently clear composition structure.

Do not create a DB connection at module import. Do not run schema migrations from lifespan.

Do not add a health endpoint just to exercise the engine.

## 6. Minimal semantic Unit of Work substrate

Create only the transaction substrate needed by later application operations.

Expected properties:

```text
one UoW instance
    -> obtains exactly one AsyncConnection
    -> begins exactly one PostgreSQL transaction
    -> READ COMMITTED
    -> exclusive ownership for its lifetime

application operation
    -> explicitly decides commit

failure / exit without successful commit
    -> rollback

repository/helper
    -> never commits independently
```

A small `UnitOfWork` / `UnitOfWorkFactory` naming is acceptable; names are implementation detail.

Prefer a safe explicit lifecycle such as:

```text
async with uow_factory() as uow:
    ... use uow.connection ...
    await uow.commit()
```

with rollback-on-exit when still active. Do not auto-commit merely because a context exited without exception unless that behavior is explicitly controlled by the application operation.

Expose the owned `AsyncConnection` only through the persistence/application boundary needed by subsequent steps. Do not wrap SQLAlchemy in a home-grown query builder or create repository interfaces before an actual vertical slice needs them.

No `Session` / `AsyncSession`.

S01 does not implement operation-specific row locks, active-model checks, cycle checks or Relationship convergence. It only establishes the connection/transaction ownership substrate that later UoWs will use.

## 7. Logical gate seam

PERSIST-20 defines two transaction-level advisory gate resources:

```text
OWNERSHIP_GRAPH_WRITE_GATE
RELATIONSHIP_DEFINITION_CONFLICT_GATE
```

S01 may establish the minimal centralized persistence seam/key registry needed so later slices do not scatter magic advisory-lock SQL/key values.

Requirements:

- transaction-level `pg_advisory_xact_lock`, never session-level locks;
- named/centralized keys;
- no manual unlock API;
- acquisition helper must not combine the protected-state read into the same SQL statement;
- no domain cycle/conflict logic yet.

Do not build a generic distributed-lock framework.

## 8. Deterministic PostgreSQL test harness foundation

Implement reusable **test-only** infrastructure matching PGTEST-03/04 without implementing the 51 semantic scenarios yet.

The harness must support the canonical conceptual roles:

```text
CTL
OBS
optional B
T1
T2
optional T3
```

The foundation should provide only reusable building blocks justified now, such as:

- independent PostgreSQL sessions/connections;
- explicit READ COMMITTED worker transactions;
- stable `scenario_id` + role metadata;
- `application_name` like `netauto-pgtest:<scenario>:<role>`;
- `pg_backend_pid()` capture;
- deterministic test-level phase/barrier coordination;
- `pg_blocking_pids(worker_pid)` observation;
- supporting `pg_stat_activity` / `pg_locks` diagnostic snapshots;
- bounded timeout/deadline safety;
- structured failure diagnostics sufficient to report scenario/role/PID/phase/blockers/wait information.

A harness phase vocabulary may follow the frozen PGTEST names:

```text
UOW_STARTED
OWNER_STABILIZED
DEPENDENCIES_STABILIZED
GATE_WAITING
GATE_ACQUIRED
PROTECTED_STATE_REREAD
CANDIDATE_WRITTEN
CLOSURE_WRITTEN
METADATA_SNAPSHOT_CAPTURED
EVENT_SET_WRITTEN
BEFORE_COMMIT
COMMITTED
ROLLED_BACK
```

Do not force every worker through every phase.

Do not add production `if TESTING` hooks or pause branches.

Do not implement the test-only persistence phase interceptor unless the S01 harness smoke test truly cannot be built with real PostgreSQL blockers; PGTEST explicitly makes the interceptor a last-resort escape hatch.

### No sleep orchestration

`sleep()` must not establish ordering or blocking/non-blocking correctness.

Use a real PostgreSQL lock/advisory-lock boundary to establish the wait. Observation may be bounded by a deadline/timeout, but time is not the mechanism that creates the race.

## 9. Required real-PostgreSQL S01 tests

S01 cannot be completed without an externally supplied real PostgreSQL target through:

```text
TEST_DATABASE_URL
```

Do not provision one. Do not use Docker/Testcontainers. Do not substitute SQLite.

All tests that mutate the shared test database must use scenario/test-owned unique identifiers and clean up after all participating connections terminate.

Do not use pytest-xdist cross-worker parallelism for PostgreSQL tests when only the single externally supplied `TEST_DATABASE_URL` exists. Do not invent per-worker URLs or hidden databases.

### Migration/schema tests

Against the real test target, prove at minimum:

1. the authoritative metadata contains exactly the 13 frozen table names;
2. the M1 Alembic revision can reach base/clean state and `upgrade head` successfully;
3. the resulting DB contains the expected tables/columns/PK/UNIQUE/FK/CHECK/index structures;
4. Alembic/SQLAlchemy metadata comparison shows no unexplained drift;
5. downgrade returns the NETAUTO-owned schema to base without touching unrelated external objects.

### Representative raw structural enforcement

Use raw Core/persistence-level operations to prove representative examples of each DB-enforcement family, without claiming domain semantics. Include enough coverage to catch migration/metadata mistakes, including representative:

```text
PK / composite-PK
UNIQUE(namespace, name)
positive/CHECK and JSONB-shape CHECK
exact composite FK
stable-lineage FK
owned-child CASCADE
external/current-reference RESTRICT
ownership PK(child_object_id)
runtime same-Definition composite-FK protection
lifecycle historical row with no live FK dependency
PostgreSQL-generated lifecycle event id + transaction timestamp
```

Do not attempt to test every semantic invariant in S01; later slices own UoW/domain predicates.

### UoW tests

Using real PostgreSQL, prove:

- UoW opens a real independent connection/transaction;
- transaction isolation is READ COMMITTED;
- explicit commit persists a raw structurally valid change;
- exception/exit-before-commit rolls the complete transaction back;
- two independent UoWs do not share the same backend transaction/connection identity;
- repository/helper code has no independent commit path.

### Harness blocking smoke test

Create one persistence-level harness smoke test that deterministically proves a real PostgreSQL blocker relation.

Preferred shape:

```text
B/T1 holds a real PostgreSQL lock on known authority
T2 attempts a conflicting lock/statement and blocks
OBS queries pg_blocking_pids(T2_pid)
    -> expected blocker PID is present
release blocker by COMMIT/ROLLBACK
T2 progresses
```

The database lock itself establishes the ordering. Do not use `sleep()` to decide that T2 is blocked.

This is a harness-foundation test, **not** one of the 51 canonical semantic scenario IDs unless it actually implements the full canonical scenario contract. Do not falsely claim PGTEST scenario coverage in S01.

## 10. Tests that remain outside S01

Do not implement semantic tests for:

```text
version allocation / expected_revision
publish/default/deprecate
active dependency graph
effective schema
Object canonical property validation
Object schema change
ownership cycle semantics
RelationshipDefinition equivalence/conflict
Relationship exact-view convergence
lifecycle event-set cardinality for real domain operations
API status/error/wire behavior
```

Those start with M1-S02 and later slices.

## 11. Static/build regression gate

Keep the S00 quality baseline green after S01 changes:

```text
uv lock
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "not postgresql"
```

Update `uv.lock` if the SQLAlchemy asyncio extra changes the resolved environment.

No global Pyright/Ruff relaxation is allowed. Any local suppression must be narrow, justified in the completion report, and reviewed.

## 12. Required PostgreSQL verification commands

With a valid externally supplied `TEST_DATABASE_URL`, run the PostgreSQL-required S01 suite explicitly and report the server version used.

At minimum report the results of the repository's concrete equivalents of:

```text
uv run pytest -m postgresql
```

and any narrower migration/concurrency selections used while debugging.

The final S01 review must have real-PostgreSQL evidence for migration, structural enforcement, UoW rollback and blocker observation. Unlike S00, absence of `TEST_DATABASE_URL` is a **completion blocker** for S01.

If the environment lacks the URL, implement what can be implemented, keep `M1-S01` IN PROGRESS, and report exactly which required PostgreSQL gates remain unexecuted. Do not fabricate success and do not mark S01 complete.

## 13. Documentation/status discipline

Do not modify frozen M1 semantic architecture to match implementation choices.

If implementation reveals a true contradiction/gap, stop the affected work and report it for architecture reopening.

Do not mark `M1-S01` `COMPLETED`; completion is a review decision after the GitHub delta and all mandatory PostgreSQL evidence are inspected.

Do not start M1-S02.

## Completion report

At the end, provide:

- concise file/change inventory;
- exact 13-table metadata/migration status;
- any implementation detail chosen for cyclic FK DDL ordering;
- async engine/runtime-context/UoW shape;
- whether any advisory-gate seam was added and its exact scope;
- deterministic harness components created;
- migration/schema drift verification result;
- representative constraint/FK/CASCADE/RESTRICT test results;
- UoW commit/rollback/isolation/independent-connection test results;
- blocking smoke-test result including `pg_blocking_pids` evidence;
- exact PostgreSQL server version used;
- all static/build/test commands and results;
- any Pyright/Ruff suppression or dependency change and rationale;
- any authority contradiction found;
- explicit confirmation that no S02/domain/API capability was implemented;
- confirmation that `status.md` was not marked completed by Codex.
