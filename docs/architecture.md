# Architecture

NETAUTO is a REST-API-first dynamic infrastructure modeling framework. The
backend does not hard-code network-domain concepts such as Device, Interface,
Site, or VLAN. Those concepts are modeled dynamically through versioned
schemas and runtime data.

## Layers

The implemented dependency direction is:

```text
CLI
  -> REST API
     -> Application services
        -> Domain/core
           -> Repository contracts
              -> Persistence
                   -> in-memory reference backend
                   -> SQLAlchemy / SQLite implementation (current transitional code)
                   -> SQLAlchemy / PostgreSQL implementation
```

Key rules:

- the CLI is a REST client only and must not bypass the API by importing
  application, domain, or persistence services as an alternate execution path
- FastAPI routers are thin transport adapters
- application services orchestrate workflows and transaction boundaries
- domain/core packages define semantics and must not depend on FastAPI, Typer,
  or SQLAlchemy
- repository contracts are persistence-neutral

Pydantic is used for static API DTOs. Dynamic user-defined schemas are modeled
as DataTypes and compiled to JSON Schema Draft 2020-12. NETAUTO does not
dynamically generate Pydantic models for them. Validation is strict and does
not perform implicit coercion.

## Model Plane

The model plane contains:

- `DataType` / `DataTypeVersion`
- `ObjectTemplate` / `ObjectTemplateVersion`
- `RelationshipDefinition`

All supported model-plane mutations execute under `MODEL_PLANE_GUARD`.

On SQLite, that logical guard is currently realized by
`SqliteModelWriteUnitOfWork`, which acquires `BEGIN IMMEDIATE` before the first
decision read. That SQLite writer reservation is a backend-specific
implementation detail of the current backend, not the cross-backend
architecture.

Accepted direction:

- PostgreSQL is now the authoritative target backend for the project
- SQLite remains only as transitional implementation code until M2.5.12
- PostgreSQL realizes `MODEL_PLANE_GUARD` with a transaction-scoped advisory
  lock without redefining the architecture around one global database writer
  lock
- PostgreSQL `OWNERSHIP_GRAPH_GUARD` remains pending

Current implemented PostgreSQL persistence state:

- PostgreSQL connectivity, engine construction, and real integration-test
  harnesses are implemented
- Alembic is the authoritative PostgreSQL schema creation mechanism and a
  baseline migration exists for the current schema
- shared SQLAlchemy repository parity is established on PostgreSQL for
  `DataType`, `ObjectTemplate`, `Object`, `ObjectChange`,
  `ComponentMembership`, `RelationshipDefinition`, and `Relationship`
- `PostgresqlModelWriteUnitOfWork` implements `MODEL_PLANE_GUARD` with
  `pg_try_advisory_xact_lock(...)` and bounded acquisition that maps
  exhaustion to `ModelWriteUnavailable`
- ordinary PostgreSQL data-plane writes do not participate in this guard
- application/runtime composition still remains on SQLite
- PostgreSQL `OWNERSHIP_GRAPH_GUARD` remains pending
- no supported migration path exists from historical SQLite development
  databases into PostgreSQL

## Runtime Data Plane

The runtime data plane contains:

- `Object`
- `ComponentMembership`
- `Relationship`
- `ObjectChange`

Current concurrency control is intentionally split by invariant domain:

```text
model plane
    -> MODEL_PLANE_GUARD

ownership topology
    -> OWNERSHIP_GRAPH_GUARD

Object content/state
    -> optimistic conditional replacement / CAS

ordinary runtime data
    -> normal relational concurrency + constraints
```

There is deliberately no global logical database writer lock.

`OWNERSHIP_GRAPH_GUARD` currently protects:

- `attach_component`
- `detach_component`
- `delete_object` / subtree delete

Ordinary Object content mutation does not acquire either logical guard.
`update_object` and `migrate_objects` rely on optimistic conditional
replacement against the exact previously-read Object snapshot.

Current unresolved concern identified for M2.5:

- some data-plane workflows create or modify bindings that depend on mutable
  model-plane admission state
- current SQLite behavior must not be treated as proof that those
  cross-plane races are architecturally solved
- the exact cross-plane binding protocol is intentionally deferred to later
  M2.5 inventory/characterization/ADR slices

## Built-In Primitive Types

NETAUTO currently ships eight built-in primitive types:

- `core.string`
- `core.integer`
- `core.number`
- `core.boolean`
- `core.date`
- `core.datetime`
- `core.ip`
- `core.ip_prefix`

Important runtime validation semantics:

- `core.date`
  accepts strict ISO `YYYY-MM-DD` date strings validated by the current format
  checker
- `core.datetime`
  accepts timezone-aware datetimes only; the current implementation accepts
  `Z` or numeric `±HH:MM` offsets and validates offset shape explicitly
- `core.ip`
  accepts IPv4 or IPv6 addresses only; CIDR notation is invalid; IPv6 zone
  identifiers such as `%eth0` are rejected
- `core.ip_prefix`
  accepts IPv4 or IPv6 CIDR network prefixes only through
  `ipaddress.ip_network(..., strict=True)`; host bits are not accepted as a
  network prefix; scope IDs are rejected

Values are validated, not canonicalized or rewritten into a different textual
representation.

Constraint applicability is currently:

```text
core.string:
    min_length, max_length, pattern, enum

core.integer:
    minimum, maximum, enum

core.number:
    minimum, maximum, enum

core.boolean:
    enum

core.date:
    none

core.datetime:
    none

core.ip:
    none

core.ip_prefix:
    none
```

`core.integer` is strict: integral floats such as `1.0` are rejected.
`core.number` accepts only finite JSON-native `int` and `float` values.
`bool` is never accepted as integer or number.

## DataType

`DataType` is a stable UUID identity plus logical `(namespace, name)` and
optional description.

`DataTypeVersion` exact identity is `(datatype_id, version)` and carries:

- lifecycle status
- base primitive type
- constraint snapshot

Current lifecycle:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

`DEPRECATED` is terminal.

Supported workflows:

- create `v1` as `DRAFT`
- revise a `DRAFT`
- publish `DRAFT -> PUBLISHED`
- deprecate `PUBLISHED -> DEPRECATED`
- create next version from a `PUBLISHED` or `DEPRECATED` source

Version numbers are monotonic and use `max(existing)+1`. The base primitive
type is immutable for the entire DataType lineage.

Lifecycle semantics are owned by the application/domain workflow, and
repositories now add defensive persistence-level enforcement:

- new persisted versions must enter as `DRAFT`
- `DRAFT -> DRAFT` may revise constraints only
- `DRAFT -> PUBLISHED` is status-only
- `PUBLISHED -> DEPRECATED` is status-only
- `DEPRECATED` is terminal
- `base_type` is stable across the lineage

DataType deletion is rejected while any `ObjectTemplate` property still
references it.

Custom-on-custom datatype derivation is not implemented. User-defined
DataTypes are based directly on built-in primitives.

## ObjectTemplate

`ObjectTemplate` is a stable UUID identity with:

- `(namespace, name)` logical name
- optional description
- stable `abstract` flag on the identity

`ObjectTemplateVersion` is the exact versioned schema snapshot containing:

- exact pinned parent `ObjectTemplateVersionRef(template_id, version)` or root
- property declarations
- component slot declarations
- lifecycle status

Important implemented semantics:

- single inheritance
- new `v1` defaults to root (`parent=None`) when no parent is supplied
- same-template inheritance is forbidden
- inheritance cycles are forbidden
- published versions are immutable
- `DEPRECATED` is terminal
- stable parent identity after the lineage has entered `PUBLISHED` or
  `DEPRECATED`
- exact parent version may advance but cannot move backwards
- draft revise uses full snapshot replacement for properties/components, but
  `parent` has special intent semantics:
  omitted `parent` preserves the current draft parent;
  explicit `parent: null` requests root;
  explicit `parent: {...}` requests that exact parent version
- inherited properties and inherited components cannot be shadowed or
  redeclared locally by name
- abstract templates cannot be instantiated as runtime Objects

Property declarations pin exact `DataTypeVersion` identities. API/CLI input
may omit `datatype_version`; the application resolves the highest `PUBLISHED`
DataTypeVersion and persists the resulting exact version pin.

Component declarations reference the stable target `ObjectTemplate` identity,
not an exact `ObjectTemplateVersion`. The target template must already have at
least one `PUBLISHED` version when the declaration is accepted or published in
the supported workflow.

Publication requires:

- the exact parent version to be `PUBLISHED`
- all effective DataType references to be `PUBLISHED`
- effective component targets to have a `PUBLISHED` version
- relationship-definition semantic conflict analysis over the resulting
  published/deprecated ancestry space

Create-next may use a `PUBLISHED` or `DEPRECATED` source version.
Publish does not assign, clear, or rewrite a parent; it publishes the current
draft snapshot exactly.

ObjectTemplate deletion is rejected while referenced by:

- current runtime Objects
- another template's parent ancestry
- component declarations
- RelationshipDefinitions

## Runtime Object

`Object` persists:

- `id`
- `template_id`
- `template_version`
- `properties`

Every Object stores an exact `ObjectTemplateVersion` pin.

Create semantics:

- explicit template version must exist and be `PUBLISHED`
- if omitted, the application resolves the highest `PUBLISHED` template
  version
- the persisted Object still stores the resolved exact version
- abstract templates cannot be instantiated
- properties are validated against effective template properties and their
  exact DataTypeVersion pins

Update semantics:

- Object identity is stable
- exact template pin remains unchanged
- patch semantics are `set/remove`
- the resulting whole property mapping is revalidated
- successful mutation uses optimistic conditional replacement
- no-op update does not create a false history entry

## Object History

`ObjectChange` is append-only runtime history with kinds:

- `CREATED`
- `UPDATED`
- `MIGRATED`
- `DELETED`

Snapshots use `before` / `after` semantics:

- `CREATED`: `before=None`, `after=set`
- `UPDATED`: `before=set`, `after=set`
- `MIGRATED`: `before=set`, `after=set`
- `DELETED`: `before=set`, `after=None`

History deliberately survives deletion of the runtime Object. The SQL
`object_changes.object_id` column is not a destructive foreign key to
`objects`.

## Object Migration

NETAUTO currently implements additive Object migration within the same
ObjectTemplate identity.

Current workflow:

- source and target versions must belong to the same template identity
- target version must be newer than source
- target version must be `PUBLISHED`
- migration analysis compares effective source and target schema
- blocking changes are:
  - property removed
  - property changed
  - component removed
  - component changed
- additive properties/components are reported separately
- newly required properties must be supplied by the caller
- candidate migrated Objects are built and validated before commit
- each replacement uses optimistic CAS against the original Object snapshot
- history entries use `MIGRATED`
- the batch runs in one transaction and commits once
- any CAS conflict aborts and rolls back the whole batch; no partial migration
  and no partial migration history commit

Arbitrary destructive schema migration is not implemented.

## Runtime Composition

`ComponentMembership` is the current structural ownership edge:

- parent Object
- named slot
- child Object

Current semantics:

- a child has at most one direct owner
- same-template recursive composition is valid
- direct same-Object self edge is invalid
- multi-node ownership cycles are prevented by supported workflows, not by
  declarative SQL alone
- child template compatibility is inheritance-aware using stable template
  identity plus exact pinned ancestry
- `attach_component`, `detach_component`, and `delete_object` use
  `OWNERSHIP_GRAPH_GUARD`

Detach removes only the incoming ownership edge. It does not delete the child.

Subtree deletion is application semantics, not SQL cascade semantics:

- the subtree is fully discovered before the first Object delete
- incident runtime Relationships to the deletion set are removed explicitly
- ObjectChange delete history is recorded explicitly
- deletion order is descendants-before-parent
- deleting an owned component directly deletes that Object and its own
  descendants, not its owner
- a detached subtree survives later deletion of its former owner
- corrupt ownership cycles fail before Object deletion proceeds

## RelationshipDefinition And Relationship

`RelationshipDefinition` persists:

- `id`
- `source_template_id`
- `target_template_id`
- `forward_name`
- `reverse_name`

Current semantics:

- endpoints reference stable ObjectTemplate identities, not exact versions
- creating a definition requires each endpoint identity to have at least one
  `PUBLISHED` version
- definitions are version-independent
- applicability is inheritance-aware through exact pinned ancestry
- `PUBLISHED` and `DEPRECATED` versions participate in semantic conflict
  analysis
- inverse-equivalent declarations are normalized for semantic conflict
  detection
- overlapping effective endpoint spaces with the same semantic pair are
  rejected
- ObjectTemplate publication is also checked because new ancestry may create a
  semantic conflict
- same-template definitions are allowed
- deletion is rejected while runtime Relationships still use the definition

`Relationship` persists:

- `id`
- `relationship_definition_id`
- `source_object_id`
- `target_object_id`

Runtime creation uses the definition's canonical `source -> target`
orientation. The application does not accept an inverse-oriented create command
and normalize it automatically.

Forward and reverse names are navigation semantics over the same stored edge.
Therefore:

```text
A -> B
```

is not automatically the same persisted runtime edge as:

```text
B -> A
```

Physical uniqueness is the ordered tuple:

```text
UNIQUE(
    relationship_definition_id,
    source_object_id,
    target_object_id
)
```

A self-link is allowed when endpoint compatibility permits it.

Navigation supports:

- effective definitions
- outgoing
- incoming
- neighbors

A self-link appears in both applicable oriented views from the same stored
edge.

Object subtree deletion explicitly removes runtime Relationships incident to
Objects that are actually being deleted. Unrelated endpoint Objects survive.

## Persistence

The current persistence model intentionally mixes relational structure and JSON
payloads.

Current authoritative structural references use relational columns and foreign
keys where representable:

- `DataTypeVersion -> DataType` stable FK `RESTRICT`
- exact `ObjectTemplateVersion` parent composite FK `RESTRICT`
- `ObjectTemplateProperty ->` exact owner version + exact DataTypeVersion FK
- `ObjectTemplateComponent ->` exact owner version + stable target
  ObjectTemplate FK
- `Object ->` exact ObjectTemplateVersion FK
- `ComponentMembership ->` Object endpoint FKs, one-owner shape via child PK,
  plus non-self / non-empty checks
- `RelationshipDefinition ->` stable ObjectTemplate endpoint FKs
- `Relationship ->` definition/Object endpoint FKs plus ordered uniqueness
- `ObjectChange` intentionally has no destructive FK to runtime Objects

JSON remains in use for:

- dynamic runtime Object properties
- historical ObjectChange snapshots
- DataTypeVersion constraint snapshots

SQLite foreign keys are enabled in the engine factory.

Current SQL backend status:

- SQLite remains the current application/runtime SQL backend
- PostgreSQL connectivity, `psycopg` driver support, `DATABASE_URL`
  configuration, and generic SQLAlchemy engine construction are implemented
- real PostgreSQL integration-test connectivity and isolated schema harnesses
  are implemented
- Alembic baseline migration infrastructure is implemented for PostgreSQL
- DataType and ObjectTemplate SQLAlchemy repository parity is established on
  PostgreSQL
- Object, ObjectChange, and ComponentMembership SQLAlchemy repository parity
  is established on PostgreSQL
- RelationshipDefinition/Relationship repository parity remains pending M2.5.7
- PostgreSQL model-plane concurrency guard work remains pending M2.5.8
- current development recreates the database after structural schema changes
- application startup still remains deliberately on SQLite in this phase
- no supported migration path from existing SQLite development databases to
  PostgreSQL exists

Current startup behavior is explicit in the production composition module:
`src/netauto/main.py` creates the SQLite engine and calls `create_schema(engine)`.

Accepted persistence direction:

- PostgreSQL is the authoritative and only intended supported SQL backend
- SQLite is deprecated transitional code and scheduled for removal in M2.5.12
- NETAUTO does not commit to long-term SQLite/PostgreSQL feature parity
- Alembic moves before dogfooding and will become the authoritative schema
  evolution mechanism in M2.5.4
- M3 dogfooding is blocked until the PostgreSQL transactional foundation closes

## In-Memory Persistence

The in-memory repositories are reference implementations of persistence-neutral
repository behavior.

They are not SQL/SQLite emulators. They enforce shared repository semantics
such as lifecycle rules, duplicate/not-found behavior, deterministic ordering,
and immutability rules, but they do not attempt to emulate:

- foreign-key enforcement details
- SQLite locking
- transaction isolation
- SQL statement ordering
- backend-specific corruption behavior

## REST API And CLI

The current REST API lives under `/api/v1` and includes:

- DataTypes
- ObjectTemplates
- Objects
- Object history
- component attach/detach/navigation
- Object migration analysis and execution
- RelationshipDefinitions
- runtime Relationships
- effective relationship definitions
- outgoing/incoming/neighbors navigation

Architecturally relevant error contracts include:

- `422 request_validation_failed`
- `422 object_validation_failed`
- `404 object_not_found`
- `409 object_concurrent_modification`
- `503 model_write_busy`
- `503 ownership_graph_busy`
- `500 persistence_error`

Both coordination `503` responses include `Retry-After: 1`.

The CLI remains a REST client and currently has top-level groups:

- `datatype`
- `object-template`
- `object`
- `relationship-definition`
- `relationship`

## Current Limitations

Current limitations that are intentionally not hidden:

- SQLite remains the current application/runtime SQL backend
- PostgreSQL is implemented only as persistence infrastructure in this phase;
  application/FastAPI/CLI runtime composition has not switched yet
- Alembic baseline exists, but Relationship repository parity and PostgreSQL
  concurrency guards are still pending
- a comprehensive integrity verifier is not implemented
- raw SQL can bypass some semantic invariants
- multi-node ownership cycles are not declaratively impossible in SQL
- `delete_object` vs concurrent Object update remains explicitly
  uncharacterized as a portable future PostgreSQL behavior
- `delete_object` vs concurrent Object migration remains explicitly
  uncharacterized as a portable future PostgreSQL behavior
- additional cross-plane binding races between data-plane admissions and
  concurrent model-plane lifecycle/delete activity have now been identified as
  distinct M2.5 work
- SQLite's single writer can mask some cross-domain behavior and is not the
  authoritative long-term persistence architecture

## Transition Note

M2.5 changes the accepted direction of the project without changing the
current implementation yet:

- code today still runs on SQLite
- architecture now treats PostgreSQL as the authoritative destination
- SQLite compatibility is no longer a long-term design constraint
- later M2.5 slices will characterize and formalize cross-plane transactional
  admission rules using real PostgreSQL transactions
