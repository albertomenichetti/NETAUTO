# M2 WIP — Relationship Properties Index Design

**Status:** INDEX INVENTORY AND ACCESS-PATH DESIGN CLOSED

**Authority:** DISCOVERY CAPTURE — NON-NORMATIVE

This document is the index-design addendum to:

```text
docs/milestones/M2/wip/relationship-properties.md
docs/milestones/M2/wip/relationship-properties-persistence.md
docs/milestones/M2/wip/relationship-properties-lifecycle.md
```

It closes the persistence-design item previously described as:

```text
exact index inventory justified by concrete read/write paths
```

It does not yet close the Alembic migration, persistence consistency closure, semantic concurrency matrix, PostgreSQL lock/gate realization, verification registries or normative propagation.

---

## 1. Governing principle

The M2 baseline does not maximize the number of indexes. It establishes one explicit access-path authority for every identity, reference, admission predicate and public read shape that the kernel already owns.

Every permanent index must be justified by at least one of:

```text
IDENTITY
    primary or exact uniqueness authority

REFERENCE
    FK support and target delete/update arbitration

READ
    public list/filter/projection/order path

ADMISSION
    lifecycle/default/dependency predicate

CONCURRENCY
    final conflict arbitration or fresh current-state lookup
```

`MIGRATION` is not a permanent-index category. An index useful only during a one-shot backfill does not enter the runtime baseline.

The design deliberately preserves several absences:

```text
no GIN on runtime properties
no lifecycle snapshot indexes
no duplicated partial PUBLISHED index
no standalone default_version index
no second factual-identity index
no event-set/grouping index
```

---

## 2. Constraint-owned indexes remain authoritative

PostgreSQL already creates indexes for every `PRIMARY KEY` and `UNIQUE` constraint.

The following constraint-owned structures are retained and must not be duplicated by equivalent explicit indexes:

```text
relationship_definition_versions
    PK (relationship_definition_id, version)

relationship_definition_properties
    PK (
        relationship_definition_id,
        relationship_definition_version,
        name
    )

relationship_definition_properties
    UNIQUE (
        relationship_definition_id,
        relationship_definition_version,
        position
    )

relationships
    PK (id)

relationships
    UNIQUE (id, relationship_definition_id)

relationship_resolutions
    PK (id)

relationship_resolutions
    UNIQUE (id, relationship_definition_id)

runtime_relationship_resolutions
    PK (resolution_id, from_object_id, to_object_id)
```

The two composite technical `UNIQUE` constraints remain FK-support structures, not business identities:

```text
uq_relationship_resolutions_id_definition
uq_relationships_id_definition
```

---

## 3. RelationshipDefinitionVersion indexes

### 3.1 Exact identity and unfiltered list

The RDV primary key:

```text
(relationship_definition_id, version)
```

supports:

```text
exact GET
version lock/admission
unfiltered version list
version > cursor
ORDER BY version ASC
max(version) + 1 allocation
owned-version lookup for root delete
```

No additional unfiltered-list index is introduced.

### 3.2 Status-aware lists and active-version scans

Add:

```text
ix_relationship_definition_versions_status_definition_version
    (
        status,
        relationship_definition_id,
        version
    )
```

It supports:

```text
RDV list filtered by status
capability EXISTS for PUBLISHED RDV
model-plane status scans
future active-model verification
```

`status` is first so the same structure can serve both one-Definition lists and cross-Definition active-model scans. `version` remains the final keyset ordering column.

Do not add a second partial index:

```sql
WHERE status = 'PUBLISHED'
```

because it would duplicate the PUBLISHED subset of an index already required for all three lifecycle states.

### 3.3 Cross-domain consistency

Equivalent version resources expose the same status-filtered collection semantics. Add the corresponding hardening indexes:

```text
ix_datatype_versions_status_datatype_version
    (status, datatype_id, version)

ix_object_template_versions_status_template_version
    (status, template_id, version)
```

This keeps persistence support symmetric across DataTypeVersion, ObjectTemplateVersion and RelationshipDefinitionVersion.

---

## 4. Relationship property declaration indexes

### 4.1 Exact schema read

The version-position `UNIQUE` index already supports:

```text
WHERE relationship_definition_id = ?
  AND relationship_definition_version = ?
ORDER BY position ASC
```

No third exact-schema index is introduced.

### 4.2 Historical semantic continuity

Add:

```text
ix_relationship_definition_properties_semantic_history
    (
        relationship_definition_id,
        name,
        relationship_definition_version DESC
    )
```

It supports the historical semantic key:

```text
(relationship_definition_id, name)
```

and allows REVISE/PUBLISH certification to find the most recent historical declaration even after remove/re-add and independently of presentation position.

Equivalent M1 historical queries are hardened with:

```text
ix_object_template_properties_semantic_history
    (template_id, name, template_version DESC)

ix_object_template_components_semantic_history
    (template_id, name, template_version DESC)
```

### 4.3 Reverse exact DataTypeVersion dependency

Add:

```text
ix_relationship_definition_properties_datatype_version
    (datatype_id, datatype_version)
```

It supports:

```text
exact DTV lifetime checks
DataType lineage external-reference counts
DTV.DEPRECATE active-consumer lookup
FK RESTRICT target arbitration
consistency verification
```

Do not widen the key or add `INCLUDE` columns. The exact DTV pair is the selector; consumer RDV identity is read from the matched declaration and joined through the RDV primary key.

---

## 5. Active dependency lookup

A PUBLISHED RDV is an active DataTypeVersion consumer.

The canonical lookup is:

```text
1. find declarations through
       (datatype_id, datatype_version)
2. exact-join each consumer RDV through its PK
3. filter status = PUBLISHED
4. stop at the first match
```

Use `EXISTS`, not `COUNT`, when only admission is required.

No additional index is introduced for this join. Once declaration rows expose the exact RDV key, the RDV PK is the optimal exact lookup. Status is evaluated on the one joined row.

Do not denormalize RDV status onto declarations and do not materialize an active-dependency graph.

---

## 6. Stable RelationshipDefinition and Resolution indexes

### 6.1 Definition default pointer

No standalone index on:

```text
relationship_definitions.default_version
```

is introduced.

Every operation starts from the Definition primary key `id`; version numbers are Definition-local. The same-Definition default FK is supported by the Definition PK on the referencing side and RDV PK on the target side.

### 6.2 Resolution aggregate loading and Definition cleanup

Add:

```text
ix_relationship_resolutions_definition_id
    (relationship_definition_id, id)
```

It supports:

```text
complete Definition aggregate load
complete rename set update
Definition-owned Resolution cleanup
referencing-side FK/CASCADE lookup
consistency certification
```

The current from/to endpoint indexes do not cover this parent-child access path.

### 6.3 Resolution name filtering

Add:

```text
ix_relationship_resolutions_name_id
    (name, id)
```

It supports:

```text
relationship-capabilities name filter
Object-relative Relationship name filter through the Resolution join
future certified-set conflict scans by navigation name
```

`name` remains mutable non-key metadata. This index does not make it identity or introduce a semantic `UNIQUE` constraint.

---

## 7. Factual Relationship exact-RDV consumers

Replace:

```text
ix_relationships_definition
    (relationship_definition_id)
```

with:

```text
ix_relationships_definition_version
    (
        relationship_definition_id,
        relationship_definition_version
    )
```

The new index supports:

```text
exact RDV consumer lookup
FK RESTRICT target arbitration
Definition root-delete blocker count through the prefix
after-SCHEMA_CHANGE reference verification
consistency scans
```

Do not retain both indexes. The new composite index has the same `relationship_definition_id` prefix and fully subsumes the M1 single-column structure.

For Definition delete details, `COUNT(*) WHERE relationship_definition_id = ?` uses the prefix of the same index. A separate standalone Definition index would be redundant.

---

## 8. Factual uniqueness and runtime closure

### 8.1 Factual uniqueness authority

Retain as the sole factual conflict authority:

```text
runtime_relationship_resolutions
PRIMARY KEY (
    resolution_id,
    from_object_id,
    to_object_id
)
```

It supports:

```text
exact selected-view lookup
candidate closure tuple-IN collision lookup
winner relationship_id lookup
final concurrent INSERT arbitration
fresh CREATE re-evaluation
```

Do not add a second semantic-fact key on the Relationship header, endpoint tuple, RDV or properties. Such a structure would duplicate and potentially contradict symmetric/closure semantics.

### 8.2 Complete closure load

Retain:

```text
ix_runtime_resolutions_relationship
    (relationship_id)
```

Do not widen it to include structural ordering columns.

A complete closure is semantically bounded to at most four raw rows. Once the exact Relationship is selected, sort cost is negligible; a wide index would add write amplification to every CREATE and DELETE without a material read benefit.

The same index supports child lookup for the Relationship-owned `CASCADE`.

---

## 9. Object-relative Relationship navigation

### 9.1 From-object page path

Replace:

```text
ix_runtime_resolutions_from_object
    (from_object_id)
```

with:

```text
ix_runtime_resolutions_from_object_page
    (
        from_object_id,
        relationship_id,
        to_object_id,
        resolution_id
    )
    INCLUDE (relationship_definition_id)
```

It supports:

```text
subject Object restriction
keyset order prefix:
    relationship_id
    destination_object_id
Resolution join via resolution_id
Definition projection/filter without heap access to the runtime row
endpoint FK reverse lookup
```

`relationship_name` cannot be stored in this index because it belongs to `relationship_resolutions`; the name-first alternative is provided by `ix_relationship_resolutions_name_id`.

No second index dedicated to `relationship_definition_id` filtering is introduced at baseline. The included Definition value supports index-only filtering while avoiding another large runtime-child index.

### 9.2 To-object lifetime and involvement path

Replace:

```text
ix_runtime_resolutions_to_object
    (to_object_id)
```

with:

```text
ix_runtime_resolutions_to_object_relationship
    (to_object_id, relationship_id)
```

It supports:

```text
endpoint Object FK reverse lookup
Object delete blocker counts
distinct Relationship involvement lookup
future destination-oriented navigation without another index replacement
```

---

## 10. Lifecycle writer access paths

No new writer-specific index is introduced.

The coherent Relationship metadata projection is fully supported by:

```text
runtime_relationship_resolutions(relationship_id)
relationship_resolutions PK(id)
objects PK(id)
```

Snapshot version and properties are obtained from the already loaded/locked Relationship header and do not create a new SQL selector.

---

## 11. Lifecycle read indexes

Retain the seven selector-plus-time access paths:

```text
ix_lifecycle_events_occurred
    (occurred_at, id)

ix_lifecycle_events_object
    (object_id, occurred_at, id)

ix_lifecycle_events_destination
    (destination_object_id, occurred_at, id)

ix_lifecycle_events_relationship
    (relationship_id, occurred_at, id)

ix_lifecycle_events_definition
    (relationship_definition_id, occurred_at, id)

ix_lifecycle_events_kind
    (kind, occurred_at, id)

ix_lifecycle_events_relationship_name
    (relationship_name, occurred_at, id)
```

Make the nullable-selector indexes partial:

```sql
ix_lifecycle_events_destination
    WHERE destination_object_id IS NOT NULL

ix_lifecycle_events_relationship
    WHERE relationship_id IS NOT NULL

ix_lifecycle_events_definition
    WHERE relationship_definition_id IS NOT NULL
```

The relationship-name index remains partial:

```sql
WHERE relationship_name IS NOT NULL
```

Rationale:

```text
queries only search concrete non-null selectors
irrelevant event families should not occupy these indexes
new Relationship DATA_CHANGE/SCHEMA_CHANGE volume remains isolated
```

The global occurred, object and kind indexes remain non-partial because their leading fields are always meaningful.

PostgreSQL backward scan serves the public DESC ordering; duplicate DESC indexes are not introduced.

Do not add compound filter permutations such as:

```text
(relationship_id, kind, occurred_at, id)
(definition_id, name, occurred_at, id)
```

The API permits many independent filter combinations; PostgreSQL may combine selector indexes through bitmap plans. Baseline indexes should represent primary selectors, not every combination.

---

## 12. Explicitly absent JSONB indexes

Do not introduce:

```text
GIN (relationships.properties)
GIN (before_state)
GIN (after_state)
expression index on embedded relationship_definition_version
expression index on a named runtime property
functional cast index on property values
```

There is no public query contract for:

```text
arbitrary Relationship property search
historical property search
historical RDV-version filtering
```

A future typed property search must first define:

```text
schema/version scope
operators per PrimitiveType
SCALAR/LIST semantics
null/absence semantics
pagination and ordering
```

Only then may it introduce dedicated projection/index structures. A generic GIN would add write cost now without establishing safe typed semantics.

---

## 13. Migration-time index sequencing

The lossless M1 -> M2 migration must use this ordering:

```text
1. create new tables with required PK/UNIQUE structures
2. add new nullable columns
3. backfill RDV v1 rows
4. backfill Relationship exact pins and properties
5. backfill Relationship lifecycle snapshots
6. create permanent new indexes
7. create permanent replacement indexes
8. drop superseded M1 indexes
9. add/validate final FK, CHECK and NOT NULL constraints
```

No temporary migration-only index is introduced. The backfills are intentional one-shot complete scans.

No `CREATE INDEX CONCURRENTLY` is used in the atomic baseline migration. A future zero-downtime rollout would require an explicit multi-revision expand/migrate/contract design rather than weakening the first M2 upgrade transaction.

---

## 14. FK support matrix

| Foreign key | Target support | Referencing-side support |
|---|---|---|
| RDV -> Definition | Definition PK | RDV PK prefix `relationship_definition_id` |
| RD property -> RDV | RDV PK | property PK / position-UNIQUE prefix |
| RD property -> DTV | DTV PK | `ix_relationship_definition_properties_datatype_version` |
| Definition default -> RDV | RDV PK | Definition PK `id`; one referencing row |
| Relationship -> exact RDV | RDV PK | `ix_relationships_definition_version` |
| Runtime row -> Relationship | technical UNIQUE | `ix_runtime_resolutions_relationship` |
| Runtime row -> Resolution | technical UNIQUE | runtime PK prefix `resolution_id` |
| Runtime row -> from Object | Object PK | `ix_runtime_resolutions_from_object_page` |
| Runtime row -> to Object | Object PK | `ix_runtime_resolutions_to_object_relationship` |
| Resolution -> Definition | Definition PK | `ix_relationship_resolutions_definition_id` |

This matrix is authoritative for reference-support completeness. No mechanical one-index-per-FK rule is applied where an existing prefix already serves the reference safely.

---

## 15. Final permanent index inventory

### 15.1 New Relationship/M2 indexes

```text
ix_relationship_definition_versions_status_definition_version
    (status, relationship_definition_id, version)

ix_relationship_definition_properties_datatype_version
    (datatype_id, datatype_version)

ix_relationship_definition_properties_semantic_history
    (
        relationship_definition_id,
        name,
        relationship_definition_version DESC
    )

ix_relationship_resolutions_definition_id
    (relationship_definition_id, id)

ix_relationship_resolutions_name_id
    (name, id)

ix_relationships_definition_version
    (
        relationship_definition_id,
        relationship_definition_version
    )
```

### 15.2 Runtime replacements

```text
ix_runtime_resolutions_from_object_page
    (
        from_object_id,
        relationship_id,
        to_object_id,
        resolution_id
    )
    INCLUDE (relationship_definition_id)

ix_runtime_resolutions_to_object_relationship
    (to_object_id, relationship_id)
```

These replace the corresponding simple from/to Object indexes.

### 15.3 Cross-domain hardening indexes

```text
ix_datatype_versions_status_datatype_version
    (status, datatype_id, version)

ix_object_template_versions_status_template_version
    (status, template_id, version)

ix_object_template_properties_semantic_history
    (template_id, name, template_version DESC)

ix_object_template_components_semantic_history
    (template_id, name, template_version DESC)
```

### 15.4 Lifecycle predicate changes

The following become partial while retaining their names and column order:

```text
ix_lifecycle_events_destination
ix_lifecycle_events_relationship
ix_lifecycle_events_definition
```

---

## 16. Superseded indexes

Remove after their replacements exist:

```text
ix_relationships_definition
ix_runtime_resolutions_from_object
ix_runtime_resolutions_to_object
```

Do not keep old and new structures in parallel; each replacement has the old leading selector and strictly extends its supported paths.

---

## 17. Negative index contract

The baseline explicitly forbids introduction of:

```text
standalone relationship_definitions(default_version)
partial PUBLISHED RDV index duplicating the status index
wide complete-closure ordering index
second runtime page index dedicated only to Definition filtering
GIN on Relationship properties
GIN/expression index on lifecycle snapshots
event_set_id or transition grouping index
property-value EAV indexes
semantic-fact header tuple index
```

These absences are part of the design and must be asserted by schema verification.

---

## 18. Verification contract

### 18.1 Static metadata assertions

Verify exact:

```text
index name
column order
ASC/DESC direction
UNIQUE flag
partial predicate
INCLUDE columns
presence of replacements
absence of superseded/forbidden indexes
```

### 18.2 Alembic drift and round-trip

After:

```text
upgrade
intermediate inspection
downgrade
re-upgrade
```

assert that live PostgreSQL indexes match SQLAlchemy metadata and that unrelated external objects remain untouched.

### 18.3 Plan eligibility

For critical paths, use representative seeded datasets and:

```sql
EXPLAIN (FORMAT JSON, COSTS OFF)
SET LOCAL enable_seqscan = off
```

Validate eligibility of one of the approved indexes for:

```text
RDV status list
capability PUBLISHED EXISTS
DTV reverse consumer lookup
Relationship exact-RDV consumer lookup
Object-relative Relationship page
lifecycle Relationship selector
```

Do not assert exact cost values, row estimates, one rigid node tree or wall-clock latency.

### 18.4 Negative verification

Assert absence of:

```text
JSONB GIN/expression indexes
standalone default indexes
partial PUBLISHED duplicate
superseded simple runtime indexes
migration-only permanent indexes
```

---

## 19. Closed versus open work

Closed by this addendum:

```text
baseline index census
constraint/index responsibility split
RDV list and active-version access paths
property exact-read and historical continuity paths
DTV reverse dependency support
stable Definition/Resolution access paths
factual exact-RDV consumer path
runtime uniqueness and closure path
Object-relative navigation paths
lifecycle selector hardening
JSONB negative-index contract
migration index sequencing
FK support matrix
index verification contract
```

Still open before persistence design is complete:

```text
lossless Alembic migration M1 -> M2
persistence consistency closure
handoff to semantic concurrency design
```
