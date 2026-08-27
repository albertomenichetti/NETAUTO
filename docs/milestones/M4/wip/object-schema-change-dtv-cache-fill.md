# M4 WIP — Object SCHEMA_CHANGE bulk exact-DataType cache fill

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the exact DataTypeVersion cold-fill step used while compiling an Object schema-change MigrationPlan.

## Input

After SOURCE and TARGET exact effective ObjectTemplate closures are READY, the planner can derive the complete required exact DataType pin set from their effective properties:

```text
required_exact_dtv
    = DISTINCT(
        SOURCE effective property (datatype_id, datatype_version)
        UNION
        TARGET effective property (datatype_id, datatype_version)
      )
```

The worker then subtracts exact DataTypeVersion entries already READY in the immutable cache:

```text
missing_exact_dtv
    = required_exact_dtv - cached_READY_exact_dtv
```

## Warm case

```text
missing_exact_dtv is empty
    -> zero PostgreSQL queries
```

## Cold case

If one or more exact DTV entries are missing, all missing identities are loaded in **one bounded bulk PostgreSQL statement**, not one query per DTV.

Conceptually the bulk read joins:

```text
datatype_versions
    -> exact version constraints / immutable exact semantic payload

JOIN datatypes
    -> stable lineage-wide base_type and other stable semantic fields needed by runtime compilation
```

The query is required because the effective ObjectTemplate closure contains the exact `(datatype_id, datatype_version)` pins but deliberately does not duplicate each exact DataTypeVersion constraint payload.

Therefore the cold-fill sequence is:

```text
1. deduplicate SOURCE U TARGET exact DataType pins
2. remove entries already READY in cache
3. one bulk query for all remaining exact pins
4. canonicalize/compile returned immutable semantics
5. populate stable DataType cache entries as needed
6. populate exact DataTypeVersion cache entries as READY
7. resume the same MigrationPlan compilation path used by a pre-existing cache hit
```

## No extra denormalization required for this consumer

The current M4 direction remains to keep exact DataType constraint payload in the DataType model rather than copy it into ObjectTemplate effective-property materialization.

For Object.SCHEMA_CHANGE this yields a bounded cold path:

```text
N missing exact DTVs
    -> 1 bulk query
```

rather than widening ObjectTemplate materialization with duplicated constraint payload.

## Frozen rule

```text
required DTV identities
    = deduplicated SOURCE U TARGET exact pins

all READY
    -> 0 DB queries

one or more missing
    -> exactly one bounded bulk DTV load for the missing set
    -> fill cache to READY
    -> no per-DTV N+1
```
