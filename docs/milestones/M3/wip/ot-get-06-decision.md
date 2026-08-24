# M3 — OT-GET-06 Consolidated Discovery Decision

**Status:** CONSOLIDATED / WIP / NON-NORMATIVE

**Route:** `GET /api/v1/core/object-templates/{template_id}/relationship-capabilities`

**Application:** `RelationshipDefinitionService.list_capabilities`

This file records the consolidated M3 discovery decision for OT-GET-06. It is temporary WIP evidence and must later be folded into the main GET/read census and frozen M3 architecture/contract set.

## Current behavior

The route validates only `name`, `cursor`, and `limit`, then delegates to `RelationshipDefinitionService.list_capabilities()`.

The current application flow is:

```text
validate request/cursor
-> coherent_read()
-> load requested ObjectTemplate lineage
-> 404 if absent
-> repeatedly load stable parent lineages to build ancestry
-> re-check ancestry acyclicity with a seen set
-> re-check every persisted parent lineage still exists
-> query RelationshipCapability page for all collected ancestor ids
-> batch-load each returned RelationshipDefinition default target
-> re-check non-null default_version -> PUBLISHED
-> pagination/cursor projection
```

`RelationshipDefinitionStore.list_capabilities()` itself already materializes the capability page with one SQL statement. Its `EXISTS` predicate requiring at least one PUBLISHED RelationshipDefinitionVersion is a collection-membership rule, not read-side semantic recertification, and must be preserved.

## Consolidated decision

```text
request/cursor validation                         PRESERVE
stable lineage ancestry projection                 PRESERVE
path-target 404 semantics                          PRESERVE
PUBLISHED-definition capability eligibility        PRESERVE
name filter                                        PRESERVE
keyset pagination by resolution_id                 PRESERVE

ancestry cycle revalidation                        REMOVE
missing persisted-parent revalidation              REMOVE
default_version -> PUBLISHED revalidation           REMOVE

current coherent_read()                            JUSTIFIED by fragmented read shape
target coherent_read()                             REMOVE
current persistence statements                     ancestry depth + capability query + default-target query
target persistence statements                      1
```

The ObjectTemplate stable ancestry is genuinely part of the public projection: capabilities applicable to the requested template include resolutions whose `from_template_id` matches the requested lineage or one of its stable ancestors. Therefore stable ancestry traversal cannot simply be removed.

However, the GET must trust persisted ancestry semantics. Cycle detection and parent-existence recertification are not read responsibilities. The self-referential `object_templates.parent_template_id` foreign key preserves referenced-parent existence structurally, while acyclicity remains mutation-owned.

The post-query validation that a returned RelationshipDefinition `default_version` still resolves to a PUBLISHED exact version is the same read-side semantic recertification pattern already rejected for DataType and ObjectTemplate lineage reads and must be removed.

## Target single-statement projection

The target persistence shape is one SQL statement with a recursive CTE over the stable ObjectTemplate lineage, followed by the capability page projection.

Conceptually:

```sql
WITH RECURSIVE ancestry AS (
    SELECT
        ot.id,
        ot.parent_template_id,
        0 AS depth
    FROM object_templates AS ot
    WHERE ot.id = :template_id

    UNION ALL

    SELECT
        parent.id,
        parent.parent_template_id,
        child.depth + 1
    FROM ancestry AS child
    JOIN object_templates AS parent
      ON parent.id = child.parent_template_id
),
capability_page AS (
    SELECT
        rr.id AS resolution_id,
        rr.relationship_definition_id,
        rr.name,
        rr.from_template_id,
        rr.to_template_id,
        rd.default_version
    FROM relationship_resolutions AS rr
    JOIN relationship_definitions AS rd
      ON rd.id = rr.relationship_definition_id
    WHERE rr.from_template_id IN (SELECT id FROM ancestry)
      AND EXISTS (
          SELECT 1
          FROM relationship_definition_versions AS rdv
          WHERE rdv.relationship_definition_id = rr.relationship_definition_id
            AND rdv.status = 'PUBLISHED'
      )
      AND (:name IS NULL OR rr.name = :name)
      AND (:after IS NULL OR rr.id > :after)
    ORDER BY rr.id
    LIMIT :limit_plus_one
)
SELECT ... marker ...
FROM ancestry
WHERE depth = 0

UNION ALL

SELECT ... capability rows ...
FROM capability_page
ORDER BY row_kind, resolution_id
```

The marker preserves the three public states:

```text
no rows
    -> requested ObjectTemplate path target absent
    -> 404

marker only
    -> ObjectTemplate exists but capability page is empty
    -> 200 with items = []

marker + capability rows
    -> normal capability page
```

Persistence must absorb the marker before application pagination so `limit + 1`, `more`, `items`, and `next_cursor` operate only on real `RelationshipCapability` rows.

## Pagination

The existing application pagination logic remains valid:

```text
read at most limit + 1 capabilities
more = len(rows) > limit
items = rows[:limit]
next_cursor derives from items[-1].resolution_id only when more
```

Cursor query identity remains bound to:

```text
template_id
name
route = relationship_capabilities
```

## Target read shape

```text
validate request/cursor
-> one recursive stable-ancestry + capability-page statement
-> 404 if marker absent
-> strip marker
-> pagination/cursor projection
```

No `coherent_read()` is required once the complete projection is obtained from one statement snapshot.
