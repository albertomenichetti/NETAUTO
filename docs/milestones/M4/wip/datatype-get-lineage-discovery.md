# M4 — DataType GET lineage discovery

**Status:** WIP / NON-NORMATIVE

**Role:** bounded discovery note for `GET /api/v1/core/datatypes/{datatype_id}`. This document records AS-IS evidence, findings and working hypotheses only. It does not define the M4 contract, TO-BE architecture, persistence schema, cache contract or public API contract.

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 explicitly freezes a TO-BE delta.

## 1. AS-IS

The current public `DataTypeDto` exposes:

```text
id
namespace
name
description
default_version
```

The current GET performs one PostgreSQL statement against the stable lineage row and is already minimal in statement count.

## 2. Stable vs current state

Under the current semantics:

```text
immutable stable lineage facts
    id
    namespace
    name

current mutable lineage facts
    description
    default_version
```

M4 discovery has additionally identified `base_type` / `PrimitiveType` as semantically stable-lineage state rather than exact-version state.

Working TO-BE shape under investigation:

```text
DataType stable lineage
    id
    namespace
    name
    base_type
    description        # current mutable metadata
    default_version    # current mutable policy
```

## 3. Public response hypothesis

If `base_type` is relocated to the stable lineage, the current working direction is that the public DataType lineage representation should expose it as a first-class field.

This is a public-contract change candidate and is not frozen by this note.

## 4. Cache behavior

The GET cannot be served entirely from the worker-local semantic cache because `description` and `default_version` are current mutable state and must come from PostgreSQL.

Splitting the response into cached stable fields plus a second/current DB projection would not reduce the required statement count and would complicate the read path.

Therefore the working direction is:

```text
GET DataType
    -> one PostgreSQL statement for the complete public current projection
```

The query may nevertheless perform an **opportunistic cache fill at zero additional DB cost**.

From the returned row, cache only the immutable stable descriptor:

```text
StableDataTypeDescriptor
    id
    namespace
    name
    base_type
```

Do not cache as immutable truth:

```text
description
default_version
```

## 5. General opportunistic warm-up rule

Working cache rule:

> When an operation necessarily loads a complete immutable semantic construct as part of its own required PostgreSQL work, that construct may be inserted into the worker-local cache without any additional database round-trip.

Conversely, an operation should not issue an otherwise unnecessary query solely to warm the cache.

This allows the same stable DataType descriptor to be populated by multiple natural paths, including:

```text
GET lineage
cache-miss semantic lineage load
other operations that already return the complete stable descriptor
```

## 6. Deletion and stale cache knowledge

A stable descriptor may remain in a worker cache after the DataType lineage has been deleted.

This is acceptable because cache presence means only:

```text
immutable knowledge about this identity
```

and never:

```text
proof that the lineage currently exists
```

Any operation requiring current existence or admission remains responsible for checking PostgreSQL at its authoritative boundary.

## 7. Current findings

- the GET statement count is already minimal;
- `base_type` is expected to become part of the stable lineage and, provisionally, the public lineage DTO;
- the GET should continue reading PostgreSQL for the complete public projection because it includes mutable fields;
- the same read can opportunistically populate the stable DataType cache at zero extra query cost;
- only immutable stable fields enter that cache;
- no extra query should be introduced solely for warm-up.

## 8. Open points

This note does not yet decide:

- final persistence schema for `base_type`;
- final public DTO versioning/compatibility details;
- concrete cache API/object layout;
- eviction policy;
- whether list operations should opportunistically populate the same stable cache;
- wider GET/read consistency redesign.
