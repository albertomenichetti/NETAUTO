# RD-GET-02 decision

Status: CONSOLIDATED

Public route:

`GET /api/v1/core/relationship-definitions/{relationship_definition_id}`

Current read shape:

- `RelationshipDefinitionStore.get(definition_id)` loads the aggregate header plus resolutions in one statement.
- Missing definition preserves path-target `404` semantics.
- Application then calls `_validate_persisted(value)`.
- Application then calls `_validate_default_pointers(...)`.
- Current implementation uses `coherent_read()` only because those additional reads fragment the projection.

Decision:

- Preserve aggregate projection and `404` semantics.
- Remove `_validate_persisted()` from the GET path. RelationshipDefinition semantic validity is mutation-owned persisted state and must not be re-certified by reads.
- Remove `_validate_default_pointers()` from the GET path. A persisted `default_version` is trusted by reads and must not be re-certified against a PUBLISHED exact version.
- Replace `coherent_read()` with an ordinary UoW once the redundant read-side certification is removed.

Target:

- one aggregate SELECT;
- ordinary UoW;
- no persisted-state semantic revalidation;
- no behavioral change to successful projection or missing-target 404 semantics.

This is the exact single-resource analogue of the consolidated RD-GET-01 decision.