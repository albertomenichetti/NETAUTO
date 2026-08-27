# M4 WIP — Object SCHEMA_CHANGE cache-resolution sequence

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the caller-side cache-resolution order agreed for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

The purpose is to make explicit what `Object.SCHEMA_CHANGE` tries to reuse before performing any cold semantic load.

## Step 1 — current Object binding lookup

The command first performs a lookup of the target Object in `objects` and obtains at least:

```text
object_id
template_id
template_version
```

The request already supplies:

```text
target_version
```

Therefore the command immediately knows the migration identity:

```text
(template_id, source_version, target_version)

source_version = objects.template_version
```

Before consulting migration cache:

```text
Object absent
    -> 404

target_version <= source_version
    -> semantic validation failure / 422

target_version > source_version
    -> continue
```

This first lookup discovers the current exact binding. It is not yet the complete Object aggregate snapshot used later for migration preparation and fingerprinting.

## Step 2 — MigrationPlan cache

The command next checks:

```text
MigrationPlanCache[(template_id, source_version, target_version)]
```

### HIT

```text
MigrationPlanCache HIT
    -> reuse the immutable source-to-target migration plan
    -> no semantic-plan reconstruction
```

### MISS

On a `MigrationPlanCache` miss, the command does **not** immediately query PostgreSQL.

It first checks whether the worker already has every immutable semantic input needed to compile the plan locally.

Required cached inputs are:

```text
1. full exact effective ObjectTemplate closure for SOURCE
       (template_id, source_version)

2. full exact effective ObjectTemplate closure for TARGET
       (template_id, target_version)

3. every exact DataTypeVersion semantic definition referenced by
       SOURCE closure
       UNION
       TARGET closure

4. stable ObjectTemplate ancestry knowledge required to decide
       component target compatibility/evolution
```

## Meaning of full exact ObjectTemplate closure

The source and target closures are already-resolved exact effective schemas.

They contain enough information to compare source and target without runtime inheritance traversal, including at least:

```text
effective properties
    PropertySemanticKey
    datatype_id
    datatype_version
    value_mode
    required
    migration_default
    ordering/presentation metadata where relevant

effective component slots
    SlotSemanticKey
    target_template_id
    ordering/presentation metadata where relevant
```

The migration planner must not reconstruct parent inheritance merely because the `MigrationPlan` entry is absent.

## Exact DataTypeVersion semantics

For every DataType used by either exact closure, the worker must possess the exact referenced version semantics needed by migration validation/canonicalization.

Conceptually:

```text
(datatype_id, datatype_version)
    -> immutable exact semantic definition
    -> compiled validation/canonicalization knowledge where applicable
```

No current/default DataType version lookup participates in the migration plan.

## Stable ObjectTemplate ancestry

Component evolution may need to prove facts such as:

```text
SOURCE slot target = EthernetInterface
TARGET slot target = NetworkInterface

EthernetInterface descendant-of NetworkInterface ?
```

Therefore the planner also requires stable template ancestry knowledge sufficient to answer the compatibility relation.

This may be supplied by the stable ancestry cache/materialization already envisioned by M4; it is not a reason to traverse the mutable model graph ad hoc during migration-plan compilation.

## All pieces already cached

If all four semantic input sets are already available:

```text
MigrationPlan MISS
+
SOURCE closure READY
+
TARGET closure READY
+
all referenced exact DTV semantics READY
+
required stable ancestry READY

    -> compile MigrationPlan entirely in memory
    -> store MigrationPlanCache[(T, source, target)]
    -> continue
    -> zero additional PostgreSQL queries for plan construction
```

The compiled plan is immutable for that exact source/target pair because both exact schemas and all exact DataTypeVersion semantics are immutable.

## Missing semantic inputs — cache fill, not alternate execution

If one or more required semantic inputs are absent from the worker cache, the command reads the missing immutable knowledge from PostgreSQL in order to populate the corresponding cache entries.

The cold path does **not** introduce a second migration-planning execution model.

Frozen rule:

```text
cache MISS
    -> load missing immutable semantic knowledge
    -> canonicalize/compile it as required
    -> populate cache entry/facet as READY
    -> resume the same path used by cache HIT
```

The migration planner therefore consumes cached READY semantic structures regardless of whether they were already present before the request or were filled during the current request.

The route must not use temporary DB-returned structures directly as a separate one-off semantic source while leaving the relevant cache miss unresolved.

Conceptually:

```text
MigrationPlan MISS
    -> inspect required semantic inputs

SOURCE closure MISS
    -> load SOURCE exact effective closure
    -> populate SOURCE closure cache

TARGET closure MISS
    -> load TARGET exact effective closure
    -> populate TARGET closure cache

one or more exact DTV MISS
    -> load missing exact DTV semantics
    -> populate exact DTV cache

required ancestry MISS
    -> load missing stable ancestry knowledge
    -> populate ancestry cache

all required semantic inputs READY
    -> compile MigrationPlan in memory
    -> populate MigrationPlanCache[(T, source, target)]
    -> continue
```

## Load only what is missing

A cold fill must not reload immutable semantic entries that are already READY in the worker cache solely because another required input is missing.

Example:

```text
SOURCE closure      HIT
TARGET closure      MISS
DTV A               HIT
DTV B               MISS
DTV C               HIT
ancestry            HIT
```

Required DB semantic load is limited to:

```text
TARGET closure
DTV B
```

After the fill:

```text
TARGET closure      READY
DTV B               READY

-> all MigrationPlan inputs READY
-> compile plan
```

## Bulk-fill rule

Multiple missing entries of the same semantic class must be loaded through a bounded bulk operation rather than one PostgreSQL round-trip per entry.

In particular:

```text
N missing exact DataTypeVersions
    -> bounded bulk DTV fill
    -> NOT N independent DTV queries
```

The same principle applies wherever multiple homogeneous immutable entries are required by one plan compilation.

This freezes the anti-N+1 requirement while leaving the exact SQL/query grouping to the later ObjectTemplate/DataType cache-loader design.

## Unified execution-model invariant

The intended execution model is therefore:

```text
MigrationPlanCache HIT
    -> consume plan

MigrationPlanCache MISS
    -> ensure all immutable inputs READY
       using existing cache entries plus bounded fills
    -> compile plan
    -> cache plan
    -> consume plan
```

There is no semantic distinction between a pre-existing cache hit and an entry made READY during the current request.

## Remaining cold-fill question

This note does not yet freeze how many PostgreSQL statements are required to make all missing SOURCE/TARGET closure, exact DTV and ancestry inputs READY.

The next discovery step is to determine the minimum bounded cold-fill statement sequence and then derive the complete warm/cold cost for `Object.SCHEMA_CHANGE`.
