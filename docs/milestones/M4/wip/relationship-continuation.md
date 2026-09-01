# M4 — Factual Relationship temporary continuation

**Status:** TEMPORARY CONTINUATION / WIP / NON-NORMATIVE / MUST MERGE BACK

## Purpose and governance exception

The canonical single owner for factual Relationship remains:

```text
docs/milestones/M4/wip/relationship.md
```

This file exists only as a temporary append-only continuation because the current repository connector cannot safely replace the now-large canonical owner without a lossless full-file round trip.

It is **not** a second factual Relationship owner and must not be treated as an independent source of truth. While it exists:

```text
relationship.md
    -> canonical historical owner up to its latest recorded checkpoint

relationship-continuation.md
    -> temporary ordered continuation containing only later explicitly ratified checkpoints
```

Mandatory consolidation rule:

```text
before factual Relationship review is considered complete
    -> merge this file losslessly back into relationship.md
    -> verify merged content against both source files
    -> delete relationship-continuation.md in the same consolidation step
```

No implementation authorization is implied. All checkpoints remain M4 WIP/non-normative.

---

# Continuation checkpoints

## C-REL-01 RATIFIED — Object-scoped item shape survives post-definition review

For:

```text
GET /api/v1/core/objects/{object_id}/relationships
```

the pre-freeze public item shape remains valid against the ratified `runtime_relationship_cells` data-plane relation:

```text
ObjectRelationshipItem
    relationship_id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: positive integer
    properties: object
    name: string
    destination_object: ObjectReference

ObjectReference
    id: UUID
    canonical_name: string
```

Post-definition semantics and projection are:

```text
runtime_relationship_cells.relationship_id
    -> relationship_id

runtime_relationship_cells.name
    -> name
    -> stable semantic name of this exact Object-level runtime cell

runtime_relationship_cells.to_object_id
    -> destination_object.id

relationships.relationship_definition_id
    -> relationship_definition_id

relationships.relationship_definition_version
    -> relationship_definition_version

relationships.properties
    -> properties

objects[to_object_id].canonical_name
    -> destination_object.canonical_name
```

The route path already supplies the source Object context, so `from_object_id` is intentionally not repeated in each item.

There is:

```text
NO resolution_id
NO autonomous RelationshipResolution identity
NO runtime-row deduplication
NO model-plane RelationshipDefinition read/reconstruction
NO relationship_definition_space read
NO ObjectTemplate ancestry read
```

`name` is no longer mutable Resolution display metadata. It is stable semantic state materialized directly in `runtime_relationship_cells`.

The current Object `canonical_name` remains mutable Object-owned display metadata and is joined live from `objects` rather than copied into the runtime relation.

## C-REL-02 RATIFIED — `relationship_definition_id` Object-scoped filter survives unchanged

The optional public filter remains:

```text
relationship_definition_id: UUID, optional
```

Its semantics remain:

```text
omitted
    -> do not restrict Object-visible factual Relationships by Definition

present
    -> return only Object-visible factual Relationships whose owning factual root
       has relationships.relationship_definition_id = supplied value
```

The post-definition data path is naturally:

```text
runtime_relationship_cells AS c
JOIN relationships AS r
    ON r.id = c.relationship_id

WHERE c.from_object_id = :object_id
  AND r.relationship_definition_id = :relationship_definition_id   # when supplied
```

The join to `relationships` is already required by the item projection for Definition/version/property factual root state, so this filter introduces no model-plane read and provides no reason to duplicate `relationship_definition_id` back into `runtime_relationship_cells`.

Existence/membership semantics remain:

```text
supplied relationship_definition_id does not exist
OR exists but yields no Object-visible factual Relationship
    -> 200 OK
    -> items = []
    -> next_cursor = null
```

because `relationship_definition_id` is a collection filter, not a parent/resource selector on this route.

Current next micro-point:

```text
GET /api/v1/core/objects/{object_id}/relationships
    -> revalidate whether a `name` query filter remains omitted now that name is stable semantic state
```
