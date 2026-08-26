# RD-GET-03 — GET /relationship-definitions/{relationship_definition_id}/versions

Status: CONSOLIDATED — WIP / non-normative discovery record.

## Current behavior

The application currently:

1. decodes a route/filter-bound cursor using `definition_id` and `status`;
2. opens `coherent_read()`;
3. loads the parent `RelationshipDefinition` to distinguish missing parent (`404`) from an empty version collection;
4. revalidates the persisted default pointer through `_validate_default_pointers()`;
5. lists `RelationshipDefinitionVersion` summaries with optional `status`, keyset `version > after`, ordering by `version`, and `limit + 1`.

The version-page persistence query is already a simple single-table projection over `relationship_definition_versions`.

## Consolidated decision

Preserve:

- parent identity semantics: missing `RelationshipDefinition` -> `404`;
- existing parent with no matching versions -> `200 []`;
- cursor binding to `definition_id` and `status`;
- keyset pagination on `version`;
- `status` filtering;
- `limit + 1` pagination behavior.

Remove from the GET/read path:

- `_validate_default_pointers()` persisted-state semantic revalidation;
- the separate parent-existence read;
- `coherent_read()` once the projection is reduced to one SQL statement.

## Target persistence shape

Use one parent-rooted statement, conceptually:

```sql
FROM relationship_definitions rd
LEFT JOIN relationship_definition_versions rdv
  ON rdv.relationship_definition_id = rd.id
 AND (:status IS NULL OR rdv.status = :status)
 AND (:after IS NULL OR rdv.version > :after)
WHERE rd.id = :definition_id
ORDER BY rdv.version
LIMIT :limit_plus_one
```

The `status` and keyset predicates belong in the `JOIN ... ON`, not the outer `WHERE`, so an existing parent with zero matching versions still produces the empty-collection state rather than being confused with a missing parent.

Persistence should distinguish:

- zero result rows -> parent missing -> `404`;
- parent row with null version projection -> existing parent, empty page -> `200 []`;
- parent row(s) with version projection -> normal page.

## Target read model

- ordinary UoW;
- one SQL statement;
- no persisted-state semantic revalidation;
- unchanged public pagination/filter semantics.
