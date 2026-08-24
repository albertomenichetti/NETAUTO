# M3 — GET / Read Path Census

**Status:** WIP / NON-NORMATIVE

**Role:** repository-based discovery register for the 22 canonical public business GET/read routes.

This file records route-by-route findings and consolidated discovery decisions. It does not become normative implementation authority until the accepted conclusions are propagated into the M3 contract and frozen architecture set.

A conclusion marked **CONSOLIDATED** has been explicitly reviewed during M3 discovery and is no longer an open hypothesis. It may still be changed only by an explicit discovery/design reconsideration before freeze.

## 1. Census criteria

For every GET, record at minimum:

```text
public route
application query method
persisted-state semantic revalidation
coherent_read() usage and justification
current persistence statement count
minimum required statement count / projection shape
failure semantics
cursor/filter semantics where applicable
discovery disposition
```

Working architectural rule:

```text
mutation
    -> validates and preserves semantic invariants

database
    -> preserves structural invariants expressible as constraints / FK

GET / read
    -> trusts persisted state
    -> locates, composes and projects it
    -> does not re-certify semantic invariants already owned by mutation paths
```

`coherent_read()` is allowed only when a genuinely multi-statement projection requires one coherent snapshot. If the required projection can be expressed cleanly by one SQL statement, the stronger read transaction is not justified merely by the current implementation shape.

---

## 2. DataType — 4 / 4 reviewed

### DT-GET-01 — List DataType lineages

```text
GET /api/v1/core/datatypes
application: DataTypeService.list_lineages
status: CONSOLIDATED
```

Current behavior:

```text
request/cursor validation
-> coherent_read()
-> SELECT datatypes page
-> SELECT referenced default DataTypeVersions
-> re-check every non-null default target is PUBLISHED
-> page/cursor projection
```

Decision:

```text
persisted-state semantic revalidation   REMOVE
coherent_read()                         REMOVE
required persistence statements         1
single-statement projection              ALREADY AVAILABLE
request/cursor validation                PRESERVE
pagination semantics                     PRESERVE
```

Rationale:

The GET must trust the persisted `default_version` semantics established by mutation paths. Re-checking `default_version -> PUBLISHED` is semantic re-certification of persisted state and is outside read ownership. Once that validation is removed, the lineage page is already completely materialized by one `datatypes` statement and there is no remaining coherent-snapshot requirement.

Target read shape:

```text
validate request/cursor
-> one lineage-page SELECT
-> pagination/cursor projection
```

### DT-GET-02 — Get one DataType lineage

```text
GET /api/v1/core/datatypes/{datatype_id}
application: DataTypeService.get_lineage
status: CONSOLIDATED
```

Current behavior:

```text
coherent_read()
-> SELECT datatype lineage
-> 404 if absent
-> SELECT referenced default DataTypeVersion when default_version is non-null
-> re-check target is PUBLISHED
-> projection
```

Decision:

```text
persisted-state semantic revalidation   REMOVE
coherent_read()                         REMOVE
required persistence statements         1
single-statement projection              ALREADY AVAILABLE
404 semantics                            PRESERVE
```

Rationale:

As for the lineage list, the GET must not certify that a persisted default is still PUBLISHED. The requested lineage projection is already completely represented by one `datatypes` lookup. Removing the semantic revalidation also removes the only reason for a repeatable coherent snapshot.

Target read shape:

```text
one lineage SELECT
-> 404 if absent
-> projection
```

### DT-GET-03 — List exact DataType versions

```text
GET /api/v1/core/datatypes/{datatype_id}/versions
application: DataTypeService.list_versions
status: CONSOLIDATED
```

Current behavior:

```text
request/cursor validation
-> ordinary UnitOfWork
-> SELECT datatype lineage only to establish URI-target existence
-> 404 if lineage absent
-> SELECT datatype_versions page
-> pagination/cursor projection
```

There is no semantic revalidation of persisted state and no `coherent_read()` today.

The lineage lookup has one legitimate public-contract purpose only: distinguish these states:

```text
path DataType absent
    -> 404 resource_not_found

path DataType exists but no version matches the current filter/cursor
    -> 200 with items = []
```

It does not need to materialize a `DataType` projection and it is not semantically necessary as a separate statement.

Decision:

```text
persisted-state semantic revalidation   NONE / KEEP NONE
coherent_read()                         NONE / DO NOT INTRODUCE
current persistence statements          2
required persistence statements         1
404 vs empty-collection distinction     PRESERVE
status filter                            PRESERVE
keyset pagination                        PRESERVE
```

The target persistence read must express, in one SQL statement, both:

```text
whether the path DataType exists
and
the requested version page (limit + 1)
```

while preserving the distinction between absent parent and existing parent with an empty filtered collection.

A lineage-rooted outer-join/subquery formulation is a viable realization, provided version filters and cursor predicates do not collapse the empty-collection case. The exact SQL construction remains an architecture/implementation realization detail; the consolidated discovery requirement is the one-statement projection and preserved public failure semantics.

The application-level pagination logic remains valid:

```text
read at most limit + 1 version summaries
more = len(rows) > limit
items = rows[:limit]
next_cursor derives from items[-1].version only when more
```

### DT-GET-04 — Get one exact DataTypeVersion

```text
GET /api/v1/core/datatypes/{datatype_id}/versions/{version}
application: DataTypeService.get_version
status: CONSOLIDATED
```

Current behavior:

```text
ordinary UnitOfWork
-> one SELECT datatype_versions
   WHERE datatype_id = :datatype_id
     AND version = :version
-> 404 if absent
-> exact projection
```

Decision:

```text
persisted-state semantic revalidation   NONE
coherent_read()                         NONE
persistence statements                  1
projection shape                        EXACT / COMPLETE
M3 behavioral change                    NONE
```

This GET already matches the M3 read principles and should remain structurally unchanged except for incidental refactoring required by shared implementation work.

---

## 3. DataType family conclusion

The four DataType reads establish the first consolidated M3 census result:

| ID | Read | Revalidation | `coherent_read()` | Statements current -> target | Disposition |
|---|---|---|---|---|---|
| `DT-GET-01` | lineage list | remove | remove | `2 -> 1` | simplify |
| `DT-GET-02` | lineage get | remove | remove | `2 -> 1` | simplify |
| `DT-GET-03` | version list | none | none | `2 -> 1` | single-statement existence + page |
| `DT-GET-04` | exact version get | none | none | `1 -> 1` | keep |

No DataType GET requires `coherent_read()` in the M3 target model.

Request validation, cursor integrity, keyset pagination, exact 404 semantics and the current public DTO projections remain independent concerns and are preserved.

---

## 4. ObjectTemplate — 3 / 6 reviewed

### OT-GET-01 — List ObjectTemplate lineages

```text
GET /api/v1/core/object-templates
application: ObjectTemplateService.list_lineages
status: CONSOLIDATED
```

Current behavior:

```text
request/cursor validation
-> coherent_read()
-> SELECT object_templates page
-> SELECT referenced default ObjectTemplateVersion headers
-> re-check every non-null default target is PUBLISHED
-> page/cursor projection
```

The application and persistence layers already represent the parent filter as a valid tri-state:

```text
parent_filter_set = false
    -> no parent predicate

parent_filter_set = true + parent_template_id = UUID
    -> parent_template_id = UUID

parent_filter_set = true + parent_template_id = null
    -> parent_template_id IS NULL
```

The cursor query identity also preserves the distinction between no parent filter and an explicit root-only filter through `parent_filter_set`.

Decision:

```text
persisted-state semantic revalidation   REMOVE
coherent_read()                         REMOVE
required persistence statements         1
single-statement projection              ALREADY AVAILABLE
request/cursor validation                PRESERVE
pagination/filter semantics              PRESERVE
application parent tri-state             PRESERVE
persistence parent tri-state             PRESERVE
```

Rationale:

As for the DataType lineage reads, `default_version -> PUBLISHED` is a persisted semantic invariant owned by mutation paths and must not be re-certified by this GET. Once `_validate_default_pointers()` is removed, `ObjectTemplateStore.list_lineages()` already materializes the complete requested lineage page with one statement, so no coherent multi-statement snapshot remains to justify `coherent_read()`.

The separate M3 `parent_template_id = null` investigation is now narrowed further: the tri-state is already coherent in the application query and persistence statement. Remaining discovery must verify whether the public HTTP and CLI carriers can express the explicit root-only state canonically.

Target read shape:

```text
validate request/cursor
-> one object_templates lineage-page SELECT
-> pagination/cursor projection
```

### OT-GET-02 — Get one ObjectTemplate lineage

```text
GET /api/v1/core/object-templates/{template_id}
application: ObjectTemplateService.get_lineage
status: CONSOLIDATED
```

Current behavior:

```text
coherent_read()
-> SELECT object_template lineage
-> 404 if absent
-> SELECT referenced default ObjectTemplateVersion header when default_version is non-null
-> re-check target is PUBLISHED
-> projection
```

Decision:

```text
persisted-state semantic revalidation   REMOVE
coherent_read()                         REMOVE
required persistence statements         1
single-statement projection              ALREADY AVAILABLE
404 semantics                            PRESERVE
parent_template_id projection            PRESERVE AS PERSISTED
```

Rationale:

The stable lineage projection is already completely materialized by `ObjectTemplateStore.get_lineage()` with one `object_templates` lookup. The extra default-target read exists only to re-certify the persisted `default_version -> PUBLISHED` invariant and is outside GET ownership. Removing that validation also removes the only reason for `coherent_read()`.

The read must project the persisted `parent_template_id` without validating the parent relationship or inheritance semantics. Those invariants remain owned by mutation paths and database constraints where applicable.

Target read shape:

```text
one object_templates lineage SELECT
-> 404 if absent
-> projection
```

### OT-GET-03 — List exact ObjectTemplate versions

```text
GET /api/v1/core/object-templates/{template_id}/versions
application: ObjectTemplateService.list_versions
status: CONSOLIDATED
```

Current behavior:

```text
request/cursor validation
-> ordinary UnitOfWork
-> SELECT object_templates lineage only to establish URI-target existence
-> 404 if lineage absent
-> SELECT object_template_versions page
-> pagination/cursor projection
```

There is no persisted-state semantic revalidation and no `coherent_read()` in the current implementation.

The first lookup exists only to preserve the public distinction:

```text
path ObjectTemplate absent
    -> 404 resource_not_found

path ObjectTemplate exists but no version matches status/cursor
    -> 200 with items = []
```

Decision:

```text
persisted-state semantic revalidation   NONE / KEEP NONE
coherent_read()                         NONE / DO NOT INTRODUCE
current persistence statements          2
required persistence statements         1
404 vs empty-collection distinction     PRESERVE
status filter                            PRESERVE
keyset pagination                        PRESERVE
```

The target persistence shape is one lineage-rooted SQL statement with a `LEFT JOIN` from `object_templates` to `object_template_versions`. Version-specific predicates, including `status` and the keyset `after` predicate, belong in the join condition rather than the outer `WHERE`, so an existing lineage with zero matching versions still produces a distinguishable null-version row while an absent lineage produces no row.

Conceptual shape:

```sql
SELECT ...
FROM object_templates AS ot
LEFT JOIN object_template_versions AS v
  ON v.template_id = ot.id
 AND (:status IS NULL OR v.status = :status)
 AND (:after IS NULL OR v.version > :after)
WHERE ot.id = :template_id
ORDER BY v.version ASC
LIMIT :limit_plus_one
```

Persistence should absorb the artificial null-version row and expose the three application-relevant states directly:

```text
None
    -> ObjectTemplate path target absent

()
    -> ObjectTemplate exists, zero matching versions

(version1, version2, ...)
    -> ObjectTemplate exists, matching version summaries
```

The exact Python return type is an implementation detail, but the tri-state semantic result is part of the consolidated design direction.

The existing pagination logic remains valid over the real version sequence only:

```text
read at most limit + 1 version summaries
more = len(rows) > limit
items = rows[:limit]
next_cursor derives from items[-1].version only when more
```

---

## 5. Remaining census

```text
ObjectTemplate          3 / 6 reviewed in this census
Object                  0 / 6 reviewed
RelationshipDefinition  0 / 4 reviewed
Relationship            0 / 1 reviewed
Global lifecycle        0 / 1 reviewed
```

Prior walkthrough findings for the remaining ObjectTemplate reads remain in `discovery.md` until each route is reviewed and promoted into this census.
