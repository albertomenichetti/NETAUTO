# M4 WIP — Object.DELETE discovery

Status: WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `Object.DELETE`. This note records current data needs, removable semantic work, and candidate persistence shape. Lock/concurrency redesign remains deferred to the global second phase.

## Current path

Current DELETE roughly does:

1. acquire the Object mutation/delete lock;
2. load the current Object snapshot;
3. call `_validate_persisted_object(...)`, which reloads exact ObjectTemplate/DataType semantics and re-canonicalizes persisted properties;
4. derive current ownership and factual-Relationship blocker counts;
5. reject with `delete_blocked` if blockers exist;
6. delete the Object row;
7. rely on RESTRICT foreign keys as final concurrent-reference authority;
8. append the intrinsic DELETED lifecycle event with the saved before snapshot;
9. commit.

## Finding: persisted schema/property recertification is not part of DELETE admission

DELETE admission depends on current reference isolation, not on re-proving that the persisted Object state is semantically valid under its exact ObjectTemplate/DataType schema.

`_validate_persisted_object(...)` therefore performs unnecessary model-plane work for this operation. DELETE needs the current Object snapshot for the lifecycle before-state and the current reference graph for blocker classification.

Candidate required data:

```text
current Object
    id
    canonical_name
    template_id
    template_version
    properties

current blockers
    ownership_count
    relationship_count
```

No ObjectTemplate effective schema, DataType semantic payload, ancestry, component-slot interpretation or Relationship semantic recertification is required.

## Current blocker semantics remain appropriate

Ownership blocking is any current `object_components` row where the target Object is either child or parent.

Relationship blocking is the number of distinct factual Relationship roots involving the Object through `runtime_relationship_resolutions`; DISTINCT relationship identity is necessary because one factual Relationship may own multiple runtime resolution rows.

The richer M4 candidate `object_components` shape:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

does not alter DELETE semantics. DELETE only asks whether an ownership edge currently involves the Object; it does not need to interpret the slot semantic identity.

## Candidate projection simplification

Current persistence obtains ownership and Relationship counts through two separate statements. Since both counts are always needed together for diagnostics, a candidate M4 shape is one statement containing two scalar subqueries, while preserving exact blocker counts rather than reducing them to EXISTS.

Conceptually:

```sql
SELECT
    ownership_count,
    relationship_count;
```

where ownership counts current incoming/outgoing ownership edges and relationship counts distinct current factual Relationships involving the Object.

This is a round-trip reduction only. It does not justify new denormalized blocker state.

## DML and race authority

The root DML remains one Object-row DELETE. Current FK RESTRICT constraints from ownership and runtime Relationship rows remain the final persistence authority against concurrent references appearing before the delete commits.

DELETE must not implicitly detach ownership edges or delete Relationships to make itself admissible.

## Candidate first-phase path

```text
stabilize/load current Object snapshot
    -> one current blocker projection
    -> reject if ownership/Relationship blockers exist
    -> DELETE Object
    -> append DELETED intrinsic lifecycle event from saved before snapshot
    -> COMMIT
```

No cache, schema recertification or new materialization is needed.

## Deferred

Exact locking/retry behavior and fresh blocker re-evaluation under concurrent ATTACH/Relationship.CREATE remain deferred to the global concurrency phase.
