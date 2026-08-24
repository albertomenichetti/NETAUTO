# RD-GET-04 — GET /relationship-definitions/{id}/versions/{version}

Status: CONSOLIDATED WIP decision for M3 discovery. Non-normative until M3 contract/architecture/steps are frozen.

## Current behavior

The application currently performs a coherent read composed of:

1. `RelationshipDefinitionStore.get(definition_id)` to establish parent identity and return RelationshipDefinition 404 when the parent is absent.
2. `RelationshipDefinitionVersionStore.get_version(definition_id, version)` to load the exact version.
3. `get_version()` itself performs two persistence statements: exact version header, then exact version properties.
4. `validate_relationship_definition_version(value)` re-certifies the persisted exact version semantically and maps failures to internal error.

Therefore the current read path uses three SELECT statements plus semantic revalidation, and `coherent_read()` is genuinely justified only because the projection is fragmented across those statements.

## Consolidated decision

Persisted RelationshipDefinitionVersion semantic invariants are trusted by this GET. Remove `validate_relationship_definition_version(value)` from the read path.

Preserve the public distinction between:

- missing RelationshipDefinition parent -> RelationshipDefinition 404;
- existing parent but missing exact version -> RelationshipDefinitionVersion 404;
- existing exact version with zero properties -> successful exact RDV with `properties=()`;
- existing exact version with properties -> successful exact RDV with properties ordered by position.

## Target projection

Replace the separate parent, header, and property reads with one parent-rooted statement equivalent to:

```sql
FROM relationship_definitions rd
LEFT JOIN relationship_definition_versions rdv
  ON rdv.relationship_definition_id = rd.id
 AND rdv.version = :version
LEFT JOIN relationship_definition_properties prop
  ON prop.relationship_definition_id = rdv.relationship_definition_id
 AND prop.relationship_definition_version = rdv.version
WHERE rd.id = :definition_id
ORDER BY prop.position
```

Result interpretation:

- zero rows -> parent missing -> RelationshipDefinition 404;
- parent row with `rdv.version IS NULL` -> exact version missing -> RelationshipDefinitionVersion 404;
- exact version row with null property columns -> exact version exists with no properties;
- exact version row(s) with property columns -> build the exact typed RDV, preserving property position order.

No artificial marker is required because parent identity and exact-version presence are naturally distinguishable from the joined columns.

## Target architecture

PRESERVE:
- parent-missing 404 semantics;
- exact-version-missing 404 semantics;
- complete exact-version projection;
- property ordering by position;
- typed persistence decoding needed to construct the response.

REMOVE:
- persisted RDV semantic revalidation;
- separate parent aggregate read;
- separate exact header read;
- separate exact properties read;
- `coherent_read()`.

TARGET:
- one SQL statement;
- ordinary UoW;
- no read-side semantic certification.
