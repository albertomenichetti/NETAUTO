# RD-GET-01 consolidated decision

Status: CONSOLIDATED — M3 discovery WIP, non-normative until M3 contract/steps are frozen.

Public route:

`GET /api/v1/core/relationship-definitions`

## Current behavior

Application `RelationshipDefinitionService.list_definitions()`:

- validates/decodes the `relationship_definitions` cursor with one UUID key;
- enters `coherent_read()`;
- calls `RelationshipDefinitionStore.list_definitions(after, limit + 1)`;
- revalidates every persisted aggregate through `_validate_persisted()` / `validate_definition()`;
- revalidates each persisted `default_version` through `_validate_default_pointers()`, requiring the target exact version to exist and be `PUBLISHED`;
- applies ordinary `limit + 1` pagination and encodes the next cursor from the last returned definition id.

Persistence `RelationshipDefinitionStore.list_definitions()` already executes one SQL statement:

- first pages only `relationship_definitions.id` in an ordered/limited CTE;
- then joins the selected page to the aggregate projection over `relationship_definitions` and `relationship_resolutions`;
- therefore the SQL limit is applied to definitions, not joined resolution rows, and an aggregate cannot be truncated by pagination;
- `_decode_aggregates()` reconstructs the persisted projection and is not itself semantic certification.

## M3 decision

Persisted semantic correctness is mutation-owned. This GET must trust committed RelationshipDefinition state.

Remove from the GET path:

1. `_validate_persisted()` / `validate_definition()` over returned persisted definitions;
2. `_validate_default_pointers()` and its extra exact-version lookup;
3. `coherent_read()` once those multi-statement certification reads are removed.

Preserve:

- cursor route identity `relationship_definitions`;
- UUID keyset semantics;
- the current page CTE + aggregate projection;
- all persisted resolution rows for each selected definition;
- `limit + 1`, `more`, `items`, and next-cursor behavior.

## Target shape

Application target:

- ordinary UoW;
- one call to `RelationshipDefinitionStore.list_definitions(after, limit + 1)`;
- no persisted-state semantic revalidation;
- existing pagination logic unchanged.

Persistence target:

- keep the existing single SQL statement unchanged in structure unless implementation cleanup requires a mechanically equivalent refactor.

Statement count:

- current: 1 aggregate page statement + 1 default-target certification statement;
- target: 1 aggregate page statement.

`coherent_read()` is unnecessary in the target because the public projection is produced by one SQL statement.
