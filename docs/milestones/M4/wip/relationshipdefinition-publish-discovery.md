# RelationshipDefinition PUBLISH — M4 discovery

Status: **WIP / NON-NORMATIVE**

This note records M4 discovery findings for `RelationshipDefinition.PUBLISH`. It does not change the current architecture contract and does not authorize implementation.

## Current semantic boundary

Publishing a `RelationshipDefinitionVersion` converts one exact DRAFT snapshot into an immutable PUBLISHED snapshot. Property declarations are already the complete exact relationship schema; unlike `ObjectTemplate`, there is no inherited/effective schema that needs a separate relational materialization.

The publication boundary must still re-certify the candidate against the complete committed published history, because distinct versions may be published out of numeric order. It must also verify that every directly pinned `DataTypeVersion` remains currently PUBLISHED at the admission boundary.

## AS-IS observations

The current application path loads the complete `RelationshipDefinition` aggregate and the complete exact DRAFT before lock-plan stabilization, then reloads both after stabilization. The complete Definition payload is larger than the publication logic requires: outside concurrency realization, publication needs current Definition existence and current `default_version`, not the complete Resolution aggregate.

History validation currently loads the complete PUBLISHED/DEPRECATED property history. The M4 REVISE discovery already identified a semantically equivalent set-based historical-conflict check that only needs to detect violations for candidate property names.

Current DataType dependency certification loads the exact referenced versions and checks current lifecycle. The semantic payload is also exactly the input needed to compile runtime property validators/specifications.

The current DML path then:

1. updates exact-version status to PUBLISHED;
2. if the Definition has no default, calls `set_default()`;
3. `set_default()` performs the UPDATE and reloads the complete Definition aggregate even though PUBLISH ignores that returned aggregate;
4. PUBLISH reloads the complete exact version again only to return the newly PUBLISHED value.

Those two post-DML reads are not semantically required.

## Candidate M4 data path

A targeted publication projection should carry only the current information required before certification:

```text
Definition:
    exists
    default_version

Exact version:
    relationship_definition_id
    version
    revision
    status
    complete ordered properties
```

The precise interaction with lock acquisition/revalidation remains deferred to the global concurrency phase.

After stabilization, publication should:

1. re-check expected revision and DRAFT lifecycle;
2. run the set-based historical-conflict check against all committed PUBLISHED/DEPRECATED history;
3. certify direct exact DataType dependencies as currently PUBLISHED using a set-based read;
4. compile the immutable runtime relationship schema from the exact property snapshot plus DataType semantics;
5. update status to PUBLISHED;
6. set the Definition default to this version only if the current default is still NULL, using a minimal conditional mutation rather than a helper that reloads the whole aggregate;
7. commit;
8. opportunistically warm the immutable worker-local exact-version cache from data already held in memory;
9. return the in-memory exact snapshot with status changed to PUBLISHED, without a post-update reload.

## Immutable runtime cache candidate

PUBLISH is the natural boundary for creating a worker-local immutable runtime representation:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
    ordered properties:
        name
        position
        datatype_id
        datatype_version
        value_mode
        runtime validator/spec linkage
        compiled semantic structures
```

The exact property declaration set is immutable after publication. A later PUBLISHED -> DEPRECATED transition does not alter its semantics, so the same cache entry remains valid.

The cache must not contain mutable/current state such as:

```text
status
default_version
RelationshipResolution.name
```

Cache presence never proves current existence or current admissibility. PostgreSQL remains authoritative where callers need current lifecycle/admission or current mutable metadata.

## No new relational denormalization at PUBLISH

No additional relational materialization is currently justified for RelationshipDefinitionVersion publication. `relationship_definition_properties` already stores the complete exact schema snapshot. The M4 optimization is to certify and compile that immutable snapshot once for frequent factual Relationship operations, rather than introduce another persisted copy of the same schema.

## Deferred concurrency questions

The following remain deliberately open until the global concurrency phase:

- whether the current pre/post-stabilization reload pattern can be reduced;
- the exact rendezvous between PUBLISH, DEPRECATE, SET_DEFAULT/CLEAR_DEFAULT and factual Relationship admission;
- the precise conditional/default-setting statement and lock/FK predicates needed to preserve first-publication default semantics;
- whether current dependency lifecycle checks can be absorbed into a broader publication statement without weakening diagnostics.
