# M4 — Relationship GET discovery

**Status:** WIP / NON-NORMATIVE

## Scope

Operation: factual `Relationship.GET`.

## Current M3 shape

M3 already moved this read to a trusted one-statement projection rooted at the factual `relationships` row and joined to the already-materialized `runtime_relationship_resolutions` plus current `relationship_resolutions.name`.

The public response needs only:

- Relationship id;
- current pinned RelationshipDefinition id/version;
- persisted properties;
- public views `(object_id, destination_object_id, name)`.

No model/schema/lineage recertification is required.

## M4 finding

No substantive M4 redesign is justified.

The current projection already has the desired separation:

```text
relationships
    current factual root/state

runtime_relationship_resolutions
    materialized stable factual endpoint assignments

relationship_resolutions
    current mutable display name
```

The read must not load or revalidate:

- RelationshipDefinition topology;
- ObjectTemplate ancestry;
- RelationshipDefinitionVersion schema;
- DataType semantics;
- factual closure derivability;
- property canonicality.

## Cache assessment

No M4 cache materially improves this read.

The public payload contains current mutable state (`properties`, exact pin, current existence, Resolution names), while the stable endpoint mapping is already persisted in `runtime_relationship_resolutions`.

Do not compose this GET from stable/immutable worker caches.

## Denormalization assessment

No new denormalization.

Do not copy mutable `Resolution.name` into `runtime_relationship_resolutions`; the current join preserves correct RENAME behavior without an invalidation/update protocol.

## Candidate M4 statement

Preserve the current one-statement authoritative projection.

> `Relationship.GET` is already at the M4 target: factual root + materialized runtime closure + current Resolution names, with no semantic recertification, no cache, and no additional denormalization.
