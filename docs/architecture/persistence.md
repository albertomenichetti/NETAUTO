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

Total authoritative tables: **13**.

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

No `property_id` or `slot_id` surrogate is introduced.

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

A current persisted edge that does not resolve exactly one current effective slot is invariant corruption, not supported legacy state.

## Relationship persistence

### Model plane

```text
relationship_definitions(
    id,
    symmetric
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
    relationship_definition_id
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

Intrinsic before/after state uses canonical JSONB. Structural event metadata uses typed columns rather than a generic event payload object.

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
- Object properties and intrinsic lifecycle snapshots use canonical JSONB.

## Primitive persistence codec

One canonical primitive persistence mapping is reused across:

- DataType constraints/enums;
- property migration defaults;
- Object values;
- lifecycle intrinsic snapshots.

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
Relationship           -> RuntimeRelationshipResolution
```

Current cross-aggregate/domain references use `RESTRICT`, including exact parent/version dependencies, DataType property pins, Object exact schema pins, ownership references, Relationship/Resolution/Object references and current model dependencies.

No `SET NULL` baseline exists for current semantic references.

Cascade is physical cleanup **after** semantic root-delete admission; it is not the delete-admission mechanism itself.

## Baseline indices

Indices exist where justified by constraint support, invariant lookup or current API/read paths.

Model/dependency:

```text
object_template_properties(datatype_id, datatype_version)
object_template_versions(parent_template_id, parent_version)
object_templates(parent_template_id)
object_template_components(target_template_id)
relationship_resolutions(from_template_id)
relationship_resolutions(to_template_id)
```

Object/ownership:

```text
objects(template_id, template_version)
objects(canonical_name, id)
object_components(parent_object_id, slot_name, child_object_id)
```

Relationship runtime:

```text
runtime_relationship_resolutions PK(resolution_id, from_object_id, to_object_id)
runtime_relationship_resolutions(from_object_id)
runtime_relationship_resolutions(to_object_id)
runtime_relationship_resolutions(relationship_id)
relationships(relationship_definition_id)
```

Lifecycle:

```text
(occurred_at, id)
(object_id, occurred_at, id)
(destination_object_id, occurred_at, id)
(relationship_id, occurred_at, id)
(relationship_definition_id, occurred_at, id)
(kind, occurred_at, id)
(relationship_name, occurred_at, id) WHERE relationship_name IS NOT NULL
```

No baseline GIN index exists on Object properties or historical snapshots. No ancestry closure or reverse-dependency materialization is authoritative.

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
