# M4 — Relationship LIST for Object discovery

**Status:** WIP / NON-NORMATIVE

## Scope

First-phase audit of factual `Relationship.LIST for Object` on branch `M4`.

Lock/concurrency redesign remains deferred to the global concurrency phase.

## Current read shape

The persistence path pages directly from `runtime_relationship_resolutions`, joins the factual `relationships` root for current exact-version pin and properties, and joins `relationship_resolutions` for the current public relationship name.

The page is filtered by `from_object_id = requested object`, supports optional RelationshipDefinition and name filters, applies keyset ordering on `(relationship_id, to_object_id, name)`, deduplicates public views before pagination, and is wrapped in an Object-rooted projection so the public contract distinguishes:

- requested Object absent -> 404;
- requested Object present with no matching views -> empty page;
- normal page -> current factual Relationship views.

The complete operation is already one PostgreSQL statement.

## Existing materialization is sufficient

`runtime_relationship_resolutions` is already the correct factual navigation/materialization layer for this query. It directly stores the stable object-relative Resolution assignment needed to navigate from one Object to current factual Relationships.

No Definition reconstruction, ObjectTemplate ancestry traversal, exact RDV semantic read, DataType read, or factual semantic recertification is needed.

The current `DISTINCT` is semantically meaningful: multiple exact runtime rows can collapse to one public `(relationship_id, object_id, destination_object_id, name)` view, especially for symmetric Definitions with overlapping lineage spaces. Deduplication must remain before pagination.

## Index support

The runtime PK

```text
(resolution_id, from_object_id, to_object_id)
```

is not the primary navigation index for this route. The schema already provides the dedicated page index:

```text
ix_runtime_resolutions_from_object_page
(
    from_object_id,
    relationship_id,
    to_object_id,
    resolution_id
)
INCLUDE (relationship_definition_id)
```

which matches the Object restriction, keyset-order prefix, Resolution join and Definition filtering/projection needs of this path.

No M4 index addition is justified by the current public route.

## Cache assessment

No worker cache should serve this read.

The public item contains current mutable state:

```text
relationship_definition_version
properties
relationship name
current factual existence
```

The stable endpoint/Resolution assignment that could otherwise be cached is already durably materialized in `runtime_relationship_resolutions` and is needed in the authoritative query anyway.

Mixing DB state with stable caches would not remove the authoritative round-trip and would complicate the projection without material benefit.

## Denormalization assessment

No additional denormalization is justified.

Ownership remains clean:

```text
runtime_relationship_resolutions
    stable/resolved factual topology

relationships
    current factual exact-version pin + properties

relationship_resolutions
    current mutable display name
```

Do not copy current `Resolution.name`, factual properties, or exact version onto runtime closure rows.

## Candidate M4 decision

`Relationship.LIST for Object` is already at the desired M4 read shape:

```text
one authoritative SQL statement
-> Object existence marker
-> current factual rows through materialized runtime closure
-> DISTINCT public views before pagination
-> current state from each owning table
```

No cache, new denormalization, new index, or semantic recertification is justified.
