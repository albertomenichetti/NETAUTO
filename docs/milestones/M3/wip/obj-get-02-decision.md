# OBJ-GET-02 decision

Status: **CONSOLIDATED**

Public route:

`GET /api/v1/core/objects/{object_id}`

Application owner:

`ObjectService.get(object_id)`

## Current shape

The read opens an ordinary unit of work, loads the Object through `ObjectStore.get(object_id)`, preserves path-target `404` semantics when the row is absent, then calls `_validate_persisted_object(...)` before returning the already-loaded Object.

`_validate_persisted_object(...)` is a read-side semantic recertification. Through `_runtime_specs(...)` / `_schema_specs(...)` it reloads the pinned ObjectTemplateVersion, resolves the effective ObjectTemplate schema, reloads referenced exact DataTypeVersions, re-checks lifecycle/admissibility and canonical constraints, canonicalizes the persisted Object properties against the reconstructed runtime schema, and compares the canonicalized result with persisted properties.

None of that work is required to construct the GET response.

## Decision

Remove `_validate_persisted_object(...)` completely from the OBJ-GET-02 read path.

GET must trust persisted semantic state. Object/template/datatype semantic admissibility and canonical runtime values are mutation-owned invariants, with database constraints/FKs providing structural integrity where applicable.

Preserve:

- ordinary unit of work;
- the single `ObjectStore.get(object_id)` lookup;
- `404` when the requested Object path target does not exist;
- the existing Object response projection.

Target application shape:

```python
async def get(self, object_id: UUID) -> Object:
    async with self._uow_factory() as uow:
        value = await ObjectStore(uow.connection).get(object_id)
        if value is None:
            raise _not_found(object_id)
        return value
```

## Statement / snapshot outcome

Current: one Object SELECT plus a potentially large transitive set of schema/datatype reads used only for semantic recertification.

Target: exactly one Object SELECT.

`coherent_read()` is not used today and is not required in the target.

## M3 target

Behavioral contract is unchanged except that persisted semantic state is no longer re-certified by the GET path. The read remains a one-statement point projection with path-target `404` semantics.
