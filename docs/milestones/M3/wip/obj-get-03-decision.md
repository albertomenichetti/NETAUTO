# OBJ-GET-03 decision — Object component collection

Status: **CONSOLIDATED** (M3 discovery WIP, non-normative until M3 contract/architecture is frozen).

Public route:

`GET /api/v1/core/objects/{parent_object_id}/components`

Application owner: `ObjectService.list_components()`.

## Current shape

The current read path:

1. validates `slot_name` / cursor request state;
2. opens `coherent_read()`;
3. loads the parent Object to preserve path-target `404` semantics;
4. resolves the parent Object's complete exact effective schema through `_schema_specs()`;
5. loads the ownership-fact page from `object_components`;
6. looks each persisted `slot_name` up in the resolved effective schema;
7. raises an internal failure if a persisted ownership fact cannot be matched to a semantic slot;
8. projects `(slot_declaring_template_id, slot_name, child_object_id)`;
9. applies `limit + 1` keyset pagination on `child_object_id`.

`_schema_specs()` is substantially broader than this projection needs: it loads exact ObjectTemplate versions, properties, components, DataType versions and constraint/runtime information and performs persisted-state semantic certification.

## Cursor identity finding

The current cursor filter identity contains only:

```python
{"slot_name": slot_name}
```

This does not bind the cursor to the path target. A cursor obtained for one parent Object can therefore be structurally compatible with another parent Object when the remaining filters match.

Target cursor identity:

```python
{
    "parent_object_id": str(parent_object_id),
    "slot_name": slot_name,
}
```

The key remains `child_object_id`.

## Read-side semantic revalidation to remove

The GET must not re-certify persisted semantic invariants. Remove from this read path:

- complete `_schema_specs()` / effective-schema resolution;
- property and DataType loading that exists only because of `_schema_specs()`;
- read-side validation that persisted ownership `slot_name` still has a semantic slot;
- any inherited declaration collision / ancestry validity certification reached through effective-schema resolution.

The GET trusts invariants established by mutation paths plus structural database constraints.

## Projection that must be preserved

The response still requires the declaring ObjectTemplate lineage for each effective component slot. This is projection data, not validation.

The minimal persisted inputs are:

- the parent Object's exact `(template_id, template_version)` pin;
- the exact ObjectTemplate parent chain through `(parent_template_id, parent_version)`;
- the paged ownership facts from `object_components`;
- component declarations from `object_template_components` matching each ownership fact's `slot_name` on the exact chain.

`object_template_components.template_id` is the projected `slot_declaring_template_id`.

## Target statement shape

Target: one recursive SQL statement.

Conceptually:

```sql
WITH RECURSIVE target_object AS (
    SELECT o.id, o.template_id, o.template_version
    FROM objects AS o
    WHERE o.id = :parent_object_id
),
exact_chain AS (
    SELECT
        v.template_id,
        v.version,
        v.parent_template_id,
        v.parent_version
    FROM object_template_versions AS v
    JOIN target_object AS o
      ON v.template_id = o.template_id
     AND v.version = o.template_version

    UNION ALL

    SELECT
        parent.template_id,
        parent.version,
        parent.parent_template_id,
        parent.parent_version
    FROM exact_chain AS child
    JOIN object_template_versions AS parent
      ON parent.template_id = child.parent_template_id
     AND parent.version = child.parent_version
),
component_page AS (
    SELECT oc.child_object_id, oc.slot_name
    FROM object_components AS oc
    JOIN target_object AS o
      ON o.id = oc.parent_object_id
    WHERE (:slot_name IS NULL OR oc.slot_name = :slot_name)
      AND (:after IS NULL OR oc.child_object_id > :after)
    ORDER BY oc.child_object_id
    LIMIT :limit_plus_one
)
SELECT
    0 AS row_kind,
    NULL AS slot_declaring_template_id,
    NULL AS slot_name,
    NULL AS child_object_id
FROM target_object

UNION ALL

SELECT
    1 AS row_kind,
    declaration.template_id AS slot_declaring_template_id,
    page.slot_name,
    page.child_object_id
FROM component_page AS page
JOIN exact_chain AS chain ON TRUE
JOIN object_template_components AS declaration
  ON declaration.template_id = chain.template_id
 AND declaration.template_version = chain.version
 AND declaration.name = page.slot_name

ORDER BY row_kind, child_object_id;
```

The declaration join completes the response projection. It must not be interpreted as a read-side semantic certification step.

## Result semantics

The target persistence result must preserve the three externally meaningful states:

- no marker / no rows: parent Object absent -> `404`;
- marker only: parent Object exists, no matching component facts -> `200` with an empty page;
- marker plus component rows: normal component page.

Pagination remains `limit + 1`, ordered/keyed by `child_object_id`, with the cursor encoded from the last returned item when `more` is true.

## Transaction decision

Current `coherent_read()` is justified only by the fragmented multi-statement projection. Once the projection is implemented as one recursive statement, use an ordinary UoW and remove `coherent_read()` from this GET path.

## Consolidated M3 decision

- fix cursor identity by binding `parent_object_id`;
- remove full effective-schema/runtime semantic certification from the GET;
- preserve parent `404`, slot filter and keyset pagination;
- project `slot_declaring_template_id` directly from exact-chain component declarations;
- target one recursive statement with a parent-existence marker;
- remove `coherent_read()` in the target implementation.
