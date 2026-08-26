# M3 — OT-GET-04 consolidated decision

**Status:** WIP / NON-NORMATIVE / CONSOLIDATED DISCOVERY DECISION

Route:

```text
GET /api/v1/core/object-templates/{template_id}/versions/{version}
application: ObjectTemplateService.get_version
```

Current behavior:

```text
coherent_read()
-> SELECT exact ObjectTemplateVersion header
-> 404 if absent
-> SELECT local properties ordered by position
-> SELECT local components ordered by position
-> assemble one ObjectTemplateVersion
```

There is no persisted-state semantic revalidation in this GET. With the current three-statement persistence shape, `coherent_read()` is justified because a concurrent DRAFT change could otherwise cause header, properties and components from different committed states to be assembled into one projection that never existed atomically.

Consolidated target:

```text
persisted-state semantic revalidation   NONE / KEEP NONE
coherent_read() current                 JUSTIFIED
current persistence statements          3
required persistence statements         1
coherent_read() target                  REMOVE
404 semantics                           PRESERVE
properties/components ordering          PRESERVE
```

The exact header, local properties and local components must be materialized by one SQL statement. The preferred projection is a typed `UNION ALL` result rather than joining both declaration tables directly, avoiding `properties x components` cartesian multiplication.

Conceptual row kinds:

```text
0 = exact version header
1 = local property
2 = local component
```

A common exact-target CTE may anchor all branches:

```sql
WITH target AS (
    SELECT *
    FROM object_template_versions
    WHERE template_id = :template_id
      AND version = :version
)
SELECT ... FROM target
UNION ALL
SELECT ... FROM object_template_properties JOIN target ...
UNION ALL
SELECT ... FROM object_template_components JOIN target ...
ORDER BY row_kind, position
```

Persistence reconstructs the `ObjectTemplateVersion` from the typed result. No header row means the exact path target is absent and preserves the existing 404. Properties and components preserve their independent `position` ordering.

Because the target uses one PostgreSQL statement snapshot, the stronger coherent-read transaction is no longer required.

The added SQL complexity is accepted deliberately for this read. Exact ObjectTemplateVersion retrieval is expected to be a high-frequency path, so reducing three database round trips plus a stronger read transaction to one statement is considered a favorable tradeoff while keeping the complexity confined to persistence.

This file temporarily records OT-GET-04 because the connector blocked a whole-file replacement of `get-read-census.md`; it should be folded into the main census during the next successful census consolidation.
