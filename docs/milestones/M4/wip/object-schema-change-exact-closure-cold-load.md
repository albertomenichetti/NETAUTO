# M4 WIP — Object SCHEMA_CHANGE exact ObjectTemplate closure cold-load

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the first cold-load conclusion for immutable semantic inputs used by:

```http
POST /api/v1/core/objects/{object_id}/schema
```

It refines the cache-resolution sequence already frozen for Object schema migration.

## Consumer need

On a `MigrationPlanCache[(template_id, source_version, target_version)]` miss, the planner needs the already-resolved exact effective ObjectTemplate closures for:

```text
SOURCE = (template_id, source_version)
TARGET = (template_id, target_version)
```

The planner compares the two effective schemas directly. It does not need to reconstruct or inspect the exact parent-version chain that produced either closure.

## Existing candidate materializations

The preliminary M4 ObjectTemplate discovery already identified persisted immutable effective-schema materializations for non-DRAFT exact versions:

```text
object_template_effective_properties
    template_id
    template_version
    ordinal
    declaring_template_id
    name
    position
    datatype_id
    datatype_version
    value_mode
    required
    migration_default

object_template_effective_components
    template_id
    template_version
    ordinal
    declaring_template_id
    name
    position
    target_template_id
```

These rows are derived/materialized state owned by the exact ObjectTemplateVersion and are created atomically at publication time from the certified effective schema.

For this consumer, these two materializations contain exactly the semantic payload required to reconstruct an in-memory full exact closure.

## No exact-version ancestry requirement for this consumer

`Object.SCHEMA_CHANGE` does not need an explicit persisted chain such as:

```text
(T,V)
    -> exact parent OTV
    -> exact grandparent OTV
    -> ...
```

The interpretation of that chain has already been paid at ObjectTemplate publication time.

The migration planner operates on:

```text
EffectiveSchema(T, source_version)
vs
EffectiveSchema(T, target_version)
```

Therefore the previously explored candidate:

```text
object_template_version_ancestry
```

is not required for this exact-closure cold-load use case.

This does not globally reject exact-version ancestry if a different M4 consumer later demonstrates an independent need for it.

## Bulk source + target load

If one or both exact closures are absent from the worker cache, source and target must be loadable together in one bounded cold-fill operation.

Conceptually:

```text
load_full_exact_closures(
    template_id = T,
    versions = {source_version, target_version}
)
```

The loader reads the required rows from:

```text
object_template_versions
object_template_effective_properties
object_template_effective_components
```

for both requested exact versions in one PostgreSQL statement/query boundary where practical.

The required asymptotic property is:

```text
DB round trips independent of inheritance depth
DB round trips independent of number of effective members
```

Payload size remains naturally proportional to the number of effective properties/components returned.

The loader must not issue:

```text
one query per exact parent
one query per effective property
one query per effective component
one query for SOURCE + another identical-shaped query for TARGET
```

when both closures are missing together.

## Empty closure vs missing version

A valid exact ObjectTemplateVersion may have:

```text
0 effective properties
0 effective components
```

Therefore zero rows in the effective-member tables cannot by itself mean that the exact version is absent.

The cold-load projection must carry exact-version presence evidence from `object_template_versions` so it can distinguish:

```text
exact OTV exists
+ zero effective properties
+ zero effective components
    -> valid empty exact closure

exact OTV absent
    -> missing exact version
```

For a `PUBLISHED` or `DEPRECATED` exact version, the M4 publication/materialization contract is expected to guarantee that its immutable effective closure has been materialized atomically with publication. A persisted state contradicting that guarantee is an internal invariant/materialization failure, not a reason for the runtime loader to fall back to recursive inheritance reconstruction.

## Cache fill behavior

The database read is a cache-fill source, not a second execution model.

```text
exact closure cache MISS
    -> load missing immutable materialization
    -> construct canonical in-memory closure
    -> mark cache entry/facet READY
    -> resume the same path used by a cache HIT
```

The migration planner itself consumes READY cached closures.

## Denormalization conclusion for this step

For the full exact ObjectTemplate closure needed by Object schema migration:

```text
object_template_effective_properties
    -> KEEP / strong fit

object_template_effective_components
    -> KEEP / strong fit

object_template_version_ancestry
    -> not required by this consumer

additional denormalized table/manifest
    -> no need identified at this step
```

The `object_template_versions` row itself is sufficient as exact-version presence/status anchor for distinguishing a valid empty materialization from a missing exact version.

## Follow-on input

Once source/target effective properties have been loaded, the worker directly knows the exact DataTypeVersion dependency set needed by the next cache-fill stage:

```text
DISTINCT (datatype_id, datatype_version)
FROM SOURCE effective properties
UNION
DISTINCT (datatype_id, datatype_version)
FROM TARGET effective properties
```

The next discovery step is to evaluate the exact DataTypeVersion cold-load path and whether the DataType denormalization/cache design already identified by M4 is sufficient for a bounded bulk fill.
