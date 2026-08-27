# Object.CREATE cold-cache discovery — WIP / NON-NORMATIVE

## Scope

This note records first-phase M4 discovery for the cold-cache path used by `Object.CREATE` after the current ObjectTemplate lineage/default/exact-version admission has selected one authoritative exact `(template_id, version)`.

It is non-normative. Lock/concurrency redesign remains deferred to the global second phase.

## Working principle

A worker-local immutable cache miss is expected to trigger a read-through load. The miss is not an error and it is not merely an optional warm-up opportunity.

Conceptual flow:

```text
PostgreSQL current admission
    -> resolve authoritative exact (template_id, version)
    -> require selected exact OTV PUBLISHED
    -> require lineage non-abstract

lookup ImmutableObjectTemplateCache[(template_id, version)]

HIT
    -> consume compiled effective schema

MISS
    -> load authoritative immutable semantic payload from PostgreSQL
    -> compile worker-local runtime structures
    -> populate cache
    -> consume the newly populated entry immediately
```

Cache presence never proves current lineage existence, abstract state, default selection or current PUBLISHED admission. Those remain PostgreSQL authority.

## What the cold path must avoid

A cache miss must not fall back to the current AS-IS reconstruction pattern:

```text
GET selected exact OTV
GET parent lineage
GET parent OTV
GET grandparent lineage
GET grandparent OTV
...
GET DTV 1
GET DTV 2
GET DTV 3
...
```

M4 materialization exists precisely so that one cold miss does not reproduce exact-parent traversal and N+1 DataType semantic reads.

## Candidate one-statement immutable projection

The preferred direction is one PostgreSQL statement rooted in the immutable effective-schema materialization:

```text
object_template_effective_properties
object_template_effective_components
```

For effective properties, the projection should also expose the immutable DataType semantic payload required to compile runtime validation structures, conceptually by joining the exact DataType pins to stable DataType facts and exact immutable DataTypeVersion semantics.

The result should be sufficient to materialize locally:

```text
ObjectTemplate effective properties
    declaring_template_id
    name
    position / ordinal
    value_mode
    required
    migration_default
    datatype_id
    datatype_version

ObjectTemplate effective components
    declaring_template_id
    name
    position / ordinal
    target_template_id

DataType immutable semantics used by those properties
    datatype_id
    datatype_version
    stable base_type
    canonical constraints
```

The physical SQL shape is still open, but the performance target is one immutable semantic load per cold exact OTV, not recursive reconstruction.

## Compile and fill on miss

The loader converts canonical persisted semantics into execution-oriented worker-local structures, for example:

```text
RuntimePropertySpec
compiled regex / enum / primitive validation structures
component-slot lookup maps
property lookup maps
semantic-key maps where useful to migrations
```

The resulting runtime-oriented entry is stored in:

```text
ImmutableObjectTemplateCache[(template_id, version)]
```

The same projection may opportunistically populate:

```text
ImmutableDataTypeVersionCache[(datatype_id, version)]
```

because it already carries the immutable DataType payload required by the selected ObjectTemplate effective properties.

This avoids rereading the same DataType semantics when later consumers request those exact versions.

## Reusable loader capability

The cold-load behavior should be implemented as a reusable semantic-cache capability rather than hidden inside `Object.CREATE`.

Conceptually:

```text
load_compiled_object_template(template_id, version)

cache HIT
    -> return entry

cache MISS
    -> authoritative immutable projection
    -> compile
    -> publish local cache entry
    -> return entry
```

Potential consumers include at least:

```text
Object.CREATE
Object.DATA_CHANGE
Object.SCHEMA_CHANGE
Object.ATTACH
Object.DETACH
```

Each operation still owns its separate PostgreSQL current-state/current-admission obligations.

## Expected runtime shape

First use of one exact OTV on a worker:

```text
DB current admission
cache MISS
1 immutable semantic cold-load statement
local compile/cache fill
canonicalize/validate runtime candidate
mutation DML
```

Subsequent uses of the same exact OTV on that worker:

```text
DB current state/admission as required by the operation
cache HIT
canonicalize/validate runtime candidate
mutation DML
```

No distributed cache invalidation protocol is required because only immutable/stable semantic knowledge enters this cache. PUBLISHED -> DEPRECATED does not change the cached exact semantics.

## Open items

- exact SQL projection/joins for one-statement OTV + DTV immutable cold loading;
- cache class/layout and eviction policy;
- whether DataType cache fill should always occur when the OTV loader already has the payload;
- eager vs lazy compilation of specific validator artifacts;
- concurrency/lock interaction remains deferred to the global second phase.
