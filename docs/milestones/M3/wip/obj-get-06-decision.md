# OBJ-GET-06 — Object relationship collection decision

Status: CONSOLIDATED (M3 discovery WIP, non-normative)

## Public read

`GET /api/v1/core/objects/{object_id}/relationships`

Application owner: `RelationshipService.list_for_object()`.

## Current behavior

The application currently:

1. binds cursor identity only to `relationship_definition_id` and `name`;
2. opens `coherent_read()`;
3. checks the path Object exists with a separate `ObjectStore.get(object_id)` call to preserve 404 semantics;
4. loads the relationship-view page with `RuntimeRelationshipStore.list_object_views(...)`;
5. reloads every Relationship aggregate in the page through `_validated_many()`;
6. reloads RelationshipDefinitions, endpoint Object templates, the full ObjectTemplate stable lineage graph, exact RelationshipDefinitionVersions and DataTypeVersions;
7. re-runs definition, lineage, Relationship, schema, dependency and property-canonicalization semantic validation;
8. compares each already-projected page row back against the reconstructed semantic projection and raises internal failure if they differ.

The page query itself already projects all public fields required by `ObjectRelationshipView`: relationship id, definition id/version, properties, object id, destination object id and relationship name. It applies the optional definition/name filters, deterministic ordering, keyset cursor and limit.

## Cursor decision

The current cursor identity is incomplete because it omits the path target Object. A cursor produced for one Object can therefore be accepted for another Object when the other filters match.

Target cursor filters must include:

```python
filters = {
    "object_id": str(object_id),
    "relationship_definition_id": (
        None if relationship_definition_id is None else str(relationship_definition_id)
    ),
    "name": name,
}
```

The existing keyset remains:

```text
(relationship_id, destination_object_id, name)
```

## Read-side semantic responsibility decision

Remove `_validated_many()` and the subsequent page-vs-aggregate comparison from this GET path.

The GET must trust the persisted factual Relationship projection. It must not re-certify:

- Relationship aggregate validity;
- RelationshipDefinition validity;
- ObjectTemplate lineage validity;
- endpoint-template compatibility;
- exact RelationshipDefinitionVersion validity;
- DataType dependency validity;
- Relationship property canonicality;
- equality between the already-projected page row and a newly reconstructed semantic aggregate.

Those are mutation-side/domain invariants, with structural persistence constraints providing the database guarantees that belong at the storage layer.

## Target persistence shape

Use one statement that combines path-target existence and the relationship page.

Conceptually:

```sql
WITH target_object AS (
    SELECT o.id
    FROM objects AS o
    WHERE o.id = :object_id
),
relationship_page AS (
    SELECT DISTINCT
        rr.relationship_id,
        rr.relationship_definition_id,
        r.relationship_definition_version,
        r.properties,
        rr.from_object_id AS object_id,
        rr.to_object_id AS destination_object_id,
        definition_resolution.name
    FROM runtime_relationship_resolutions AS rr
    JOIN target_object AS target
      ON target.id = rr.from_object_id
    JOIN relationship_resolutions AS definition_resolution
      ON definition_resolution.id = rr.resolution_id
    JOIN relationships AS r
      ON r.id = rr.relationship_id
    WHERE
        (:relationship_definition_id IS NULL
         OR rr.relationship_definition_id = :relationship_definition_id)
      AND (:name IS NULL OR definition_resolution.name = :name)
      AND (
          :after_relationship_id IS NULL
          OR (
              rr.relationship_id,
              rr.to_object_id,
              definition_resolution.name
          ) > (
              :after_relationship_id,
              :after_destination_object_id,
              :after_name
          )
      )
    ORDER BY
        rr.relationship_id,
        rr.to_object_id,
        definition_resolution.name
    LIMIT :limit_plus_one
)
SELECT
    page.relationship_id,
    page.relationship_definition_id,
    page.relationship_definition_version,
    page.properties,
    page.object_id,
    page.destination_object_id,
    page.name
FROM target_object AS target
LEFT JOIN relationship_page AS page
  ON TRUE
ORDER BY
    page.relationship_id,
    page.destination_object_id,
    page.name;
```

The nullable row produced by the final `LEFT JOIN` is projection framing, not semantic validation:

- zero rows => path Object does not exist => 404;
- one row with `relationship_id IS NULL` => Object exists but collection is empty => 200 with `items=[]`;
- non-null relationship rows => normal page.

A real Relationship id is non-null, so no explicit `row_kind` marker is required.

## Pagination

Preserve the current `limit + 1` pattern:

- `more = len(rows) > limit`;
- `items = rows[:limit]`;
- next cursor is encoded from the final returned `(relationship_id, destination_object_id, name)` tuple when `more` is true.

## `coherent_read()` decision

`coherent_read()` is defensible for the current fragmented multi-statement implementation because path existence, page projection and subsequent re-certification must otherwise share a coherent snapshot.

In the M3 target it is unnecessary: the public read becomes one database statement. Use an ordinary read UoW.

## Consolidated target

- fix cursor binding by including `object_id`;
- preserve 404-vs-empty-collection semantics;
- preserve optional filters, DISTINCT semantics, ordering, 3-column keyset and pagination;
- remove `_validated_many()` and all read-side persisted semantic revalidation;
- remove page-vs-aggregate consistency certification;
- collapse path existence and relationship page into one statement;
- remove `coherent_read()` in the target;
- no public response-shape change.
