# REL-GET-01 decision

Status: CONSOLIDATED (M3 discovery WIP; non-normative until M3 architecture/steps are frozen)

Route:

`GET /api/v1/core/relationships/{relationship_id}`

## Current behavior

The application currently enters `coherent_read()`, calls `RuntimeRelationshipStore.get(relationship_id)` once only to classify a missing URI target as 404, and then calls `_validated(...)`, which loads the same factual Relationship aggregate again.

`_validated(...)` subsequently loads the current `RelationshipDefinition`, endpoint Object template identities, the full ObjectTemplate lineage parent map, the pinned exact `RelationshipDefinitionVersion`, and its DataType dependencies. It re-runs persisted semantic validation (`validate_definition`, `validate_lineage_graph`, `validate_relationship`, schema resolution, property canonicalization) and derives public views with `relationship_views(...)`.

The public response needs only:

- Relationship id;
- pinned RelationshipDefinition id/version;
- persisted properties;
- public views `(object_id, destination_object_id, name)`.

The runtime view endpoints are already materialized in `runtime_relationship_resolutions`. The public view name can be projected directly by joining `relationship_resolutions` through `(resolution_id, relationship_definition_id)`, which is structurally protected by the persisted FK set.

## Consolidated decision

Persisted factual Relationship state is trusted by this GET path. The GET must not re-certify the factual closure, model ancestry, pinned schema, DataType dependencies, or property semantics.

Remove from the GET path:

- the initial `RuntimeRelationshipStore.get(...)` used only for the 404 check;
- `_validated(...)`;
- RelationshipDefinition reconstruction for semantic purposes;
- endpoint Object/template reads;
- full lineage reads;
- exact RDV/DataType reads;
- `validate_definition(...)`;
- `validate_lineage_graph(...)`;
- `validate_relationship(...)`;
- property canonicalization comparison;
- `relationship_views(...)` as a semantic projector;
- `coherent_read()`.

Do not weaken `RuntimeRelationshipStore.get()` / `_runtime_relationship()` globally: mutation flows still use aggregate reconstruction and validation. Introduce a dedicated trusted read projector, conceptually `get_projection(relationship_id)`, for this GET.

## Target persistence projection

Use one statement rooted at `relationships`:

```sql
SELECT DISTINCT
    r.id,
    r.relationship_definition_id,
    r.relationship_definition_version,
    r.properties,
    rr.from_object_id AS object_id,
    rr.to_object_id AS destination_object_id,
    resolution.name
FROM relationships AS r
LEFT JOIN runtime_relationship_resolutions AS rr
  ON rr.relationship_id = r.id
 AND rr.relationship_definition_id = r.relationship_definition_id
LEFT JOIN relationship_resolutions AS resolution
  ON resolution.id = rr.resolution_id
 AND resolution.relationship_definition_id = rr.relationship_definition_id
WHERE r.id = :relationship_id
ORDER BY
    rr.from_object_id,
    rr.to_object_id,
    resolution.name;
```

`DISTINCT` preserves the existing public `relationship_views(...)` set semantics without re-certifying why duplicate public views might exist.

Result interpretation:

- zero rows -> Relationship URI target absent -> 404;
- root row with nullable joined view columns -> Relationship exists with `views=()`;
- root plus joined rows -> normal `RelationshipProjection`.

`properties` is decoded only as the persisted JSON carrier needed for the response; semantic canonicalization is not re-run.

## Target application shape

Use an ordinary read UoW:

```python
async with self._uow_factory() as uow:
    value = await RuntimeRelationshipStore(uow.connection).get_projection(
        relationship_id
    )
    if value is None:
        raise _not_found(relationship_id)
    return value
```

## Statement count

Current: one aggregate SELECT for the 404 check, another aggregate SELECT inside `_validated()`, plus multiple dependency/semantic-certification reads under `coherent_read()`.

Target: one projection SELECT under an ordinary UoW.
