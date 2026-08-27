# M4 WIP — Object SCHEMA_CHANGE stable ancestry cache fill

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the final immutable semantic input required before compiling:

```text
MigrationPlanCache[(template_id, source_version, target_version)]
```

for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Why stable ancestry is still required

The full exact SOURCE and TARGET ObjectTemplate closures already contain the effective component slots and each slot's `target_template_id`, but they do not by themselves prove lineage compatibility between two different component targets.

Example:

```text
SOURCE slot target = EthernetInterface
TARGET slot target = NetworkInterface

question:
    EthernetInterface descendant-of NetworkInterface ?
```

This relation is needed to distinguish an allowed target widening from an unsupported narrowing or unrelated target change.

## Required durable source

The preliminary M4 stable-lineage closure remains the appropriate durable source:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

with the reflexive row `(T, T, 0)` as previously envisioned.

The relation is stable in the descendant-to-ancestors direction because ObjectTemplate lineage parentage is stable for the lineage lifetime.

No exact-version ancestry is required for this decision.

## Cache-resolution sequence

After SOURCE and TARGET exact effective closures are READY, derive the unique ObjectTemplate lineage identities involved in component-target compatibility comparisons.

Conceptually:

```text
required component target lineages
    = DISTINCT(
        relevant SOURCE target_template_id
        UNION
        relevant TARGET target_template_id
      )
```

Check the worker-local stable ancestry cache for the required descendant-to-ancestor knowledge.

```text
all required ancestry READY
    -> zero PostgreSQL queries

one or more required ancestry entries missing
    -> one bounded bulk query against object_template_ancestry
    -> populate missing stable ancestry cache entries
    -> mark required ancestry READY
```

The cold fill must not perform one query per component slot, target lineage or ancestry pair.

## Bulk-query invariant

For one MigrationPlan compilation, all missing stable ancestry knowledge needed by the relevant component-target comparisons must be retrieved in one PostgreSQL statement.

Conceptually:

```text
N missing ancestry requirements
    -> 1 bulk ancestry query
    -> NOT N independent queries
```

The exact SQL shape and physical indexes remain an architecture-wide persistence/index-review concern, but query count must remain bounded independently of the number of component slots.

## No new denormalization required

For this consumer, the previously proposed:

```text
object_template_ancestry
```

is sufficient.

No additional ancestry representation or ObjectTemplate exact-version closure is required to compile the component portion of the MigrationPlan.

## MigrationPlan readiness boundary

Once the following are READY:

```text
SOURCE full exact effective closure
TARGET full exact effective closure
all required exact DataTypeVersion semantics
all required stable ObjectTemplate ancestry knowledge
```

the worker has every immutable semantic input needed to compile the migration plan entirely in memory:

```text
compile MigrationPlan(template_id, source_version, target_version)
    -> store MigrationPlanCache[(template_id, source_version, target_version)]
    -> READY
```

After this point the schema-change command no longer needs model-plane semantic reads for that plan. The next phase is to re-read the current complete Object aggregate, compute its whole-aggregate fingerprint and prepare the concrete Object migration candidate using the READY MigrationPlan.
