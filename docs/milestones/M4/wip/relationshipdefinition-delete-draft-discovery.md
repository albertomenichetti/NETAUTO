# RelationshipDefinition DELETE_DRAFT discovery

Status: **TECHNICAL DISCOVERY CLOSED EXCEPT CONCURRENCY/PHYSICAL REALIZATION / WIP / NON-NORMATIVE**

This note is operation-specific source/evidence subordinate to `relationshipdefinition.md` and to the current RelationshipDefinition technical consolidation ledger.

## Ratified M4 technical direction

`DELETE_DRAFT` deletes one exact mutable RelationshipDefinitionVersion generation. Admission depends only on the exact-version header:

```text
RelationshipDefinition exists
exact RDV exists
status == DRAFT
revision == expected_revision
```

The complete property declaration payload does not participate in admission and must not be loaded solely for this mutation.

## Logical short-UoW path

Conceptually:

```text
DELETE_DRAFT(definition_id, version, expected_revision)

current admission
    Definition exists
    exact RDV exists
    status == DRAFT
    revision == expected_revision

mutation
    delete exact relationship_definition_versions row

owned cleanup
    relationship_definition_properties
        -> relational ownership cleanup / cascade-equivalent

commit
```

The exact SQL / lock / conditional-delete realization remains architecture work. A single conditional `DELETE ... WHERE status='DRAFT' AND revision=:expected_revision RETURNING ...` is a possible realization only if it preserves the public distinction among absent exact version, lifecycle conflict, stale revision and successful deletion.

## Version allocation consequence

The shared no-reuse allocator is not rewound or changed:

```text
last_versions
    -> UNCHANGED
```

A successfully deleted DRAFT version number is never reusable.

## Explicit ownership boundary: `relationship_definition_space` is unchanged

`relationship_definition_space` is owned by the stable RelationshipDefinition root, not by any exact RelationshipDefinitionVersion.

Its semantic source is:

```text
stable RelationshipDefinition topology/names
+
current stable ObjectTemplate ancestry
```

Therefore deleting one DRAFT exact version does not alter the Definition semantic-cell closure:

```text
DELETE_DRAFT
    relationship_definition_versions      DELETE target exact DRAFT
    relationship_definition_properties    owned cleanup
    relationship_definition_space         UNCHANGED
```

The space is cleaned only when the owning RelationshipDefinition root is deleted, potentially through FK/cascade-equivalent physical ownership chosen later in architecture.

## No other model/runtime work

`DELETE_DRAFT` does not require:

```text
property declaration read
DataType / DataTypeVersion semantics
historical continuity
RelationshipDefinition.default_version
relationship_definition_space read/write
ObjectTemplate state
factual Relationship scan/count
immutable RDV cache interaction
post-delete reload
```

A DRAFT is never published into the immutable RDV cache, so there is no cache invalidation responsibility.

## Response/repeat semantics

```text
first valid DELETE
    -> 204 No Content

repeated DELETE of same exact version
    -> 404 resource_not_found
```

## Concurrency handoff

The material same-generation races are:

```text
DELETE_DRAFT vs REVISE
DELETE_DRAFT vs PUBLISH
DELETE_DRAFT vs DELETE_DRAFT
```

Required invariant:

```text
only one operation can validly consume the mutable DRAFT generation
identified by expected_revision
```

Exact lock/CAS/rendezvous realization remains architecture work.

## Technical closure checkpoint

```text
RD DELETE_DRAFT

semantic preparation
    -> NONE

reads/admission
    -> Definition existence
    -> exact RDV status/revision only

writes
    -> exact RDV DELETE
    -> owned property cleanup

relationship_definition_space
    -> UNCHANGED

last_versions
    -> UNCHANGED

cache
    -> NONE

response
    -> 204
```
