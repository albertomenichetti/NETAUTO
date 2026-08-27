# M4 WIP — Object SCHEMA_CHANGE exact DataType cold fill

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the exact-DataType cold-fill step used while resolving a `MigrationPlanCache` miss for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Input set

After the SOURCE and TARGET full exact ObjectTemplate closures are READY, collect every exact DataTypeVersion pin referenced by either closure:

```text
required_exact_dtv =
    SOURCE effective property pins
    UNION
    TARGET effective property pins
```

The set is deduplicated by exact semantic identity:

```text
(datatype_id, datatype_version)
```

Before touching PostgreSQL, subtract every exact DTV already READY in the worker cache.

Conceptually:

```text
missing_exact_dtv =
    distinct(required_exact_dtv)
    - cached_ready_exact_dtv
```

If `missing_exact_dtv` is empty, this step performs zero PostgreSQL statements.

## One bounded bulk query

If one or more exact DTV entries are missing, all missing entries are loaded in one bounded PostgreSQL statement.

The query is keyed by the requested exact pairs, conceptually through a `VALUES` relation, composite tuple predicate, array/unnest input or another equivalent set-based PostgreSQL shape.

The physical realization must preserve:

```text
1 request
-> N distinct missing exact DTV identities
-> 1 PostgreSQL statement
-> N immutable semantic payloads
```

It must never degrade to one query per DataTypeVersion.

## Stable DataType lineage payload in the same query

M4 preliminary DataType discovery moved `base_type` to the stable `datatypes` lineage row rather than repeating it on each exact version.

Therefore the same bulk statement should join each requested `datatype_versions` row to its owning `datatypes` row and return enough stable + exact immutable knowledge to populate both cache layers:

```text
StableDataTypeCache[datatype_id]
    id
    namespace
    name
    base_type

ImmutableDataTypeVersionCache[(datatype_id, version)]
    canonical constraints
    compiled validator / regex / enum structures as applicable
```

No additional query is needed solely to discover stable `base_type` for DTVs being cold-loaded.

The exact compilation of validators remains application-local after the DB read.

## Lifecycle/status boundary

The migration planner consumes immutable exact semantics. It does not use current DataType lifecycle status as an admission authority during Object schema migration.

An exact DTV referenced by a certified immutable ObjectTemplate effective closure is an already-established semantic dependency. `PUBLISHED -> DEPRECATED` does not invalidate its cached semantic payload.

Consequently this bulk load is a semantic-payload fill, not a current default/status admission check.

No DataType default pointer participates.

## Missing rows are invariant failures

A SOURCE/TARGET materialized effective closure contains exact DataTypeVersion pins that were certified when the ObjectTemplateVersion became immutable.

Therefore, if the bulk query fails to return one of the requested exact identities, the runtime must not reinterpret that as a caller-level missing operand or silently fall back to another DataType version.

Conceptually:

```text
requested exact DTV from certified effective closure
+
row unexpectedly absent
    -> persisted invariant / reference-lifetime failure
    -> internal failure
```

The loader never substitutes:

```text
default_version
latest version
another PUBLISHED version
```

## Cache-fill invariant

The cold result is used to make the cache miss become a cache hit before migration-plan compilation:

```text
bulk DB read
-> decode canonical stable/exact semantics
-> populate missing StableDataTypeCache entries
-> populate missing ImmutableDataTypeVersionCache entries
-> compile runtime validators where applicable
-> mark requested exact semantics READY
-> resume normal cache-HIT MigrationPlan compilation path
```

There is no separate one-off planner path that consumes uncached DB rows directly.

## Frozen decision

```text
required exact DTV identities
    = deduplicated SOURCE ∪ TARGET exact property pins

already READY exact DTV entries
    = excluded before DB access

0 missing
    -> 0 DB statements

1..N missing
    -> exactly 1 bounded bulk DB statement

same statement
    -> joins stable `datatypes` payload needed by the cache
    -> avoids separate base_type lookup

unexpected missing certified exact DTV
    -> internal invariant failure

result
    -> cache entries become READY
    -> MigrationPlan compilation resumes from cache
```
