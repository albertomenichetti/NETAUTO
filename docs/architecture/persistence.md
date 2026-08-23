# Persistence — Current AS-IS

## Authority and backend

PostgreSQL is the only supported persistence backend for the current kernel.

The domain model remains persistence-independent, but the application/persistence architecture deliberately relies on PostgreSQL guarantees. No alternate-backend abstraction is maintained solely for portability.

General enforcement rule:

> PK, UNIQUE, FK, CHECK, NOT NULL and delete actions express states that PostgreSQL can protect clearly and directly; lifecycle, graph-wide, cross-row and cross-aggregate semantics that require interpretation belong to the Unit of Work and concurrency contract.

No constraint-trigger domain layer is part of the current baseline.

## Authoritative table map

### Model plane

```text
datatypes
datatype_versions
object_templates
object_template_versions
object_template_properties
object_template_components
relationship_definitions
relationship_definition_versions
relationship_definition_properties
relationship_resolutions
```

### Data plane

```text
objects
object_components
relationships
runtime_relationship_resolutions
```

### History

```text
object_lifecycle_events
```

Total authoritative tables: **15**.

## Exact column inventory

```text
datatypes
    id, namespace, name, description, default_version
datatype_versions
    datatype_id, version, revision, status, base_type, constraints
object_templates
    id, namespace, name, description, abstract, default_version,
    parent_template_id
object_template_versions
    template_id, version, revision, status, parent_template_id,
    parent_version
object_template_properties
    template_id, template_version, name, position, datatype_id,
    datatype_version, value_mode, required, migration_default
object_template_components
    template_id, template_version, name, position, target_template_id
relationship_definitions
    id, symmetric, default_version
relationship_definition_versions
    relationship_definition_id, version, revision, status
relationship_definition_properties
    relationship_definition_id, relationship_definition_version, name,
    position, datatype_id, datatype_version, value_mode
relationship_resolutions
    id, relationship_definition_id, from_template_id, to_template_id, name
objects
    id, canonical_name, template_id, template_version, properties
object_components
    child_object_id, parent_object_id, slot_name
relationships
    id, relationship_definition_id, relationship_definition_version,
    properties
runtime_relationship_resolutions
    relationship_id, relationship_definition_id, resolution_id,
    from_object_id, to_object_id
object_lifecycle_events
    id, occurred_at, kind, object_id, canonical_name,
    destination_object_id, destination_canonical_name,
    slot_declaring_template_id, slot_name, relationship_id,
    relationship_definition_id, relationship_name, before_state, after_state
```

The current architecture has no authoritative table for:

- PrimitiveType catalog;
- effective-schema cache;
- runtime property EAV;
- template ancestry closure;
- reverse dependency materialization;
- generic property/component member rows;
- surrogate exact-version identity;
- surrogate runtime Relationship-resolution identity.

## Exact version identities

DataTypeVersion:

```text
PRIMARY KEY (datatype_id, version)
```

ObjectTemplateVersion:

```text
PRIMARY KEY (template_id, version)
```

RelationshipDefinitionVersion:

```text
PRIMARY KEY (relationship_definition_id, version)
```

Version numbers are positive integers and are lineage-local. No API-only or persistence-only surrogate version identity exists.

Lineage default pointers are nullable and use same-lineage exact-version composite references.

## ObjectTemplate inheritance persistence

`object_templates.parent_template_id` is the authority for stable parent lineage.

Each non-root ObjectTemplateVersion also persists exact parent dependency:

```text
parent_template_id
parent_version
```

The pair identifies the exact parent version. Root versions have both fields NULL.

The duplicated `parent_template_id` on the exact version is intentional because `version` is not globally unique and the domain exact parent identity is a tuple. Equality between the version-level parent lineage and the lineage header parent is a UoW invariant.

## ObjectTemplate declarations

Local properties and components are separate child tables owned by exact ObjectTemplateVersion snapshots.

Physical local declaration identity:

```text
(template_id, template_version, name)
```

No `property_id` or `slot_id` surrogate exists.

Properties persist:

```text
datatype_id
datatype_version
value_mode
required
migration_default
position
```

The exact DataTypeVersion reference uses a composite FK with `RESTRICT` lifetime semantics.

Components persist stable `target_template_id`; runtime slot compatibility is semantic/UoW logic.

Local `position` values are positive and unique within the respective property/component set.

Owned declaration rows are removed with their exact ObjectTemplateVersion after semantic root-delete admission.

## Object persistence

`objects` contains at least:

```text
id
canonical_name
template_id
template_version
properties
```

`id` is PostgreSQL UUID primary key.

`(template_id, template_version)` is a composite FK `RESTRICT` to the exact current ObjectTemplateVersion.

`canonical_name` is non-null TEXT with semantic length `1..255`, non-unique.

`properties` is non-null JSONB with top-level object shape. `{}` is the zero-property representation.

No runtime EAV model exists.

The persisted Object state contains only canonical JSON-compatible values. Optional LIST zero-cardinality is represented by key absence; JSON null is not a valid runtime domain value.

No global Object state revision is persisted.

## Ownership persistence

```text
object_components(
    child_object_id,
    parent_object_id,
    slot_name
)
```

Single-owner authority:

```text
PRIMARY KEY (child_object_id)
```

Parent and child Object references use `RESTRICT`. A local check prevents `parent_object_id = child_object_id`.

Navigation index:

```text
(parent_object_id, slot_name, child_object_id)
```

No ownership-edge surrogate identity exists.

The runtime row persists `slot_name` but does **not** version-pin an exact component declaration and does not duplicate `slot_declaring_template_id`.

The authoritative current slot semantic key is derived from the parent Object's current exact effective schema:

```text
SlotSemanticKey = (declaring_template_id, slot_name)
```

A current persisted edge that does not resolve exactly one current effective slot is unsupported invariant corruption.

## Relationship persistence

### Model plane

```text
relationship_definitions(
    id,
    symmetric,
    default_version
)
```

```text
relationship_definition_versions(
    relationship_definition_id,
    version,
    revision,
    status
)
```

```text
relationship_definition_properties(
    relationship_definition_id,
    relationship_definition_version,
    name,
    position,
    datatype_id,
    datatype_version,
    value_mode
)
```

```text
relationship_resolutions(
    id,
    relationship_definition_id,
    from_template_id,
    to_template_id,
    name
)
```

Both IDs are UUID primary keys.

Definition owns Resolution child rows and may cascade-delete them only after semantic Definition-delete admission.

Definition also owns its exact versions and their declaration rows. Version
identity is composite; declarations have no surrogate identity. Declaration
name and position are each unique within one exact version. Exact DataTypeVersion
references use `RESTRICT`. The semantic-history index on
`(relationship_definition_id, name, relationship_definition_version DESC)`
supports history recertification without creating a second identity authority.

`relationship_definitions.default_version` is a nullable same-lineage composite
FK to the exact version with `RESTRICT` behavior.

Endpoint template-lineage references use `RESTRICT`.

`RelationshipResolution.name` is mutable non-key metadata. There is no business/exact-child UNIQUE on:

```text
(relationship_definition_id, from_template_id, to_template_id, name)
```

A technical UNIQUE on `(id, relationship_definition_id)` exists only to support same-Definition composite FKs from runtime rows.

### Runtime factual aggregate

```text
relationships(
    id,
    relationship_definition_id,
    relationship_definition_version,
    properties
)
```

```text
runtime_relationship_resolutions(
    relationship_id,
    relationship_definition_id,
    resolution_id,
    from_object_id,
    to_object_id
)
```

Exact resolved-view authority:

```text
PRIMARY KEY (resolution_id, from_object_id, to_object_id)
```

No surrogate runtime-row identity exists.

Relationship owns its runtime-resolution child rows; those child rows cascade only with the owning factual Relationship after semantic deletion admission.

The factual header's
`(relationship_definition_id, relationship_definition_version)` is a composite
`RESTRICT` FK to the exact version. `properties` is non-null JSONB constrained to
a top-level object. The exact pin and complete property map change atomically in
the same row during SCHEMA_CHANGE; DATA_CHANGE replaces only the complete map.

Resolution and Object references use `RESTRICT`.

`relationship_definition_id` is intentionally duplicated on runtime rows to permit declarative same-Definition composite FKs:

```text
(relationship_id, relationship_definition_id)
    -> relationships(id, relationship_definition_id)

(resolution_id, relationship_definition_id)
    -> relationship_resolutions(id, relationship_definition_id)
```

The technical UNIQUE structures required to support these FKs are constraint-support structures, not new business identity.

## Lifecycle-event persistence

A single table `object_lifecycle_events` stores typed event-family state with columns including:

```text
id
occurred_at
kind
object_id
canonical_name
destination_object_id
destination_canonical_name
slot_declaring_template_id
slot_name
relationship_id
relationship_definition_id
relationship_name
before_state
after_state
```

Intrinsic and factual before/after state uses canonical JSONB. Relationship
factual snapshots contain exactly `relationship_definition_version` and
`properties`. Structural event metadata uses typed columns rather than a generic
event payload object.

Historical identity/name columns deliberately have no live FK to current tables.

`id` is PostgreSQL-generated UUID row identity and deterministic ordering tie-breaker, not a domain entity identity.

`occurred_at` is `TIMESTAMPTZ` with transaction timestamp semantics. All events in one semantic UoW therefore share the same transaction-start timestamp.

Canonical event ordering uses `(occurred_at, id)`; this is deterministic but not a global strict commit sequence.

Append-only lifecycle behavior is an application/kernel contract, not a compliance-grade trigger-enforced immutable ledger.

## PostgreSQL scalar/storage choices

- UUID columns use native PostgreSQL `UUID`;
- version, revision and position use positive `INTEGER`;
- lifecycle/status/value-mode/PrimitiveType closed vocabularies use `TEXT + CHECK`, not PostgreSQL ENUM;
- booleans use native BOOLEAN;
- identifiers use TEXT plus semantic CHECK/validation rather than CITEXT/VARCHAR as authority;
- DataType constraints use canonical non-null JSONB object;
- Object/Relationship properties and lifecycle snapshots use canonical JSONB.

## Primitive persistence codec

One canonical primitive persistence mapping is reused across:

- DataType constraints and enum members;
- ObjectTemplate migration defaults;
- Object current properties;
- Relationship current properties;
- Object lifecycle intrinsic snapshots;
- Relationship lifecycle factual `before_state` / `after_state` snapshots.

Relationship state uses this same codec; there is no second Relationship
primitive representation.

Mapping:

```text
core.string    -> JSON string
core.integer   -> JSON integer number
core.number    -> canonical exact-decimal JSON string
core.boolean   -> JSON boolean
core.date      -> ISO YYYY-MM-DD string
core.datetime  -> canonical UTC string ending Z
core.ip        -> canonical IP string
core.ip_prefix -> canonical CIDR string
core.byte_size -> JSON integer number, exact bytes
```

`core.number` exact-decimal string has no exponent, no leading `+`, no unnecessary leading/trailing zero and canonicalizes negative zero to `"0"`.

`core.datetime` uses UTC `Z` with at most microsecond precision and no arbitrary rounding.

Non-canonical IP prefixes with host bits set are rejected rather than normalized silently.

## Delete/FK policy

`CASCADE` is used only for true owned child state of the same aggregate:

```text
DataType               -> DataTypeVersion
ObjectTemplate         -> ObjectTemplateVersion
ObjectTemplateVersion  -> local Property/Component
RelationshipDefinition -> RelationshipResolution
RelationshipDefinition -> RelationshipDefinitionVersion
RelationshipDefinitionVersion -> RelationshipDefinitionProperty
Relationship           -> RuntimeRelationshipResolution
```

Current cross-aggregate/domain references use `RESTRICT`, including exact parent/version dependencies, DataType property pins, Object and Relationship exact schema pins, ownership references, Relationship/Resolution/Object references and current model dependencies.

No `SET NULL` baseline exists for current semantic references.

Cascade is physical cleanup **after** semantic root-delete admission; it is not the delete-admission mechanism itself.

## Explicit index inventory

Constraint-owned PK/UNIQUE indexes are not duplicated. The exact explicit index inventory is:

```text
ix_datatype_versions_status_datatype_version
    datatype_versions(status, datatype_id, version)
ix_object_template_properties_datatype_version
    object_template_properties(datatype_id, datatype_version)
ix_object_template_properties_semantic_history
    object_template_properties(template_id, name, template_version DESC)
ix_object_template_components_semantic_history
    object_template_components(template_id, name, template_version DESC)
ix_object_template_versions_parent_version
    object_template_versions(parent_template_id, parent_version)
ix_object_template_versions_status_template_version
    object_template_versions(status, template_id, version)
ix_object_templates_parent
    object_templates(parent_template_id)
ix_object_template_components_target
    object_template_components(target_template_id)
ix_relationship_resolutions_from_template
    relationship_resolutions(from_template_id)
ix_relationship_resolutions_to_template
    relationship_resolutions(to_template_id)
ix_relationship_definition_versions_status_definition_version
    relationship_definition_versions(status, relationship_definition_id, version)
ix_relationship_definition_properties_datatype_version
    relationship_definition_properties(datatype_id, datatype_version)
ix_relationship_definition_properties_semantic_history
    relationship_definition_properties(
        relationship_definition_id,
        name,
        relationship_definition_version DESC
    )
ix_relationship_resolutions_definition_id
    relationship_resolutions(relationship_definition_id, id)
ix_relationship_resolutions_name_id
    relationship_resolutions(name, id)
ix_objects_template_version
    objects(template_id, template_version)
ix_objects_canonical_name_id
    objects(canonical_name, id)
ix_object_components_parent_slot_child
    object_components(parent_object_id, slot_name, child_object_id)
ix_relationships_definition_version
    relationships(relationship_definition_id, relationship_definition_version)
ix_runtime_resolutions_from_object_page
    runtime_relationship_resolutions(
        from_object_id, relationship_id, to_object_id, resolution_id
    ) INCLUDE (relationship_definition_id)
ix_runtime_resolutions_to_object_relationship
    runtime_relationship_resolutions(to_object_id, relationship_id)
ix_runtime_resolutions_relationship
    runtime_relationship_resolutions(relationship_id)
ix_lifecycle_events_occurred
    object_lifecycle_events(occurred_at, id)
ix_lifecycle_events_object
    object_lifecycle_events(object_id, occurred_at, id)
ix_lifecycle_events_destination
    object_lifecycle_events(destination_object_id, occurred_at, id)
    WHERE destination_object_id IS NOT NULL
ix_lifecycle_events_relationship
    object_lifecycle_events(relationship_id, occurred_at, id)
    WHERE relationship_id IS NOT NULL
ix_lifecycle_events_definition
    object_lifecycle_events(relationship_definition_id, occurred_at, id)
    WHERE relationship_definition_id IS NOT NULL
ix_lifecycle_events_kind
    object_lifecycle_events(kind, occurred_at, id)
ix_lifecycle_events_relationship_name
    object_lifecycle_events(relationship_name, occurred_at, id)
    WHERE relationship_name IS NOT NULL
```

No GIN/expression index exists on Object/Relationship properties or historical
snapshots. There is no standalone default-version index, duplicate
PUBLISHED-only index, second factual-identity index or event-set grouping index.
No ancestry closure or reverse-dependency materialization is authoritative.

## Intentional denormalizations

### Exact ObjectTemplate parent lineage on version rows

`object_template_versions.parent_template_id` duplicates the stable parent lineage to preserve the exact domain tuple and permit direct composite parent-version references.

### Relationship Definition identity on runtime rows

`runtime_relationship_resolutions.relationship_definition_id` duplicates Definition identity so PostgreSQL can enforce same-Definition coherence declaratively through composite FKs.

These denormalizations are architecture decisions. They must not be removed as cleanup without an explicit architecture change and re-evaluation of the guarantees they enable.

## Runtime/test database configuration

Runtime and automated-test PostgreSQL connections are externally configurable and logically distinct.

Current integration convention:

```text
NETAUTO_DATABASE_URL
    -> runtime / application / Alembic target

TEST_DATABASE_URL
    -> automated real-PostgreSQL test target
```

The application does not provision or manage the PostgreSQL server lifecycle. Schema migration is explicit administration rather than implicit application-startup behavior.

## Alembic and startup revision authority

The installed package contains exactly one durable migration graph:

```text
script location     netauto:migrations
base                0001_m2_kernel
head                0001_m2_kernel
down_revision       None
authoritative tables 15
```

The root revision creates the complete current schema from an empty PostgreSQL
database. `head -> base` removes all and only NETAUTO structures; it is destructive
verification, not an operating rollback procedure. There is no in-place path
from a pre-baseline development schema.

Migration DDL is self-contained and does not import mutable application metadata
as its authority. Development verification requires `compare_metadata == []` and
exact table, column, key, constraint, index, predicate and INCLUDE inventories.

Server startup discovers the unique shipped head from the installed package and
reads the database's current heads through the process runtime engine. Serving is
permitted only for exact singleton equality:

```text
actual_heads == ("0001_m2_kernel",)
```

Missing, base, older, newer, unknown, multiple or unreadable revision state
rejects startup. Installation, application startup, Health and the CLI never
upgrade, downgrade, stamp, create or repair schema. Alembic administration is a
separate explicit process.

## Enforcement boundary summary

DB-enforced examples:

- PK/identity uniqueness;
- exact composite FK existence;
- single-owner child uniqueness;
- exact Relationship resolved-view uniqueness;
- same-Definition runtime-row coherence;
- cross-aggregate reference lifetime;
- local scalar/row-shape checks.

UoW/concurrency-enforced examples:

- lifecycle admission and monotonicity;
- current default must be PUBLISHED;
- active model graph validity;
- effective-schema validity;
- canonical Object-state validity;
- parent-lineage denormalization equality;
- ownership slot compatibility and acyclicity;
- RelationshipDefinition aggregate/equivalence/conflict semantics;
- factual Relationship complete closure;
- complete lifecycle-event-set atomicity.

See `concurrency.md` for transaction and stabilization mechanisms.
