# RelationshipDefinition DELETE — M4 discovery

Status: **TECHNICAL DISCOVERY CLOSED EXCEPT CONCURRENCY/PHYSICAL REALIZATION / WIP / NON-NORMATIVE**

This note is operation-specific source/evidence subordinate to `relationshipdefinition.md` and to the current RelationshipDefinition technical-consolidation ledger. It does not authorize implementation or freeze final FK/lock/gate realization.

## Current M4 semantic boundary

`DELETE /relationship-definitions/{id}` removes the complete stable RelationshipDefinition aggregate.

A current factual Relationship referencing any exact version of the Definition is an external lifetime blocker.

The reviewed M4 failure contract requires only:

```text
409 delete_blocked
    details.blocker_type = relationship
```

Therefore the AS-IS total factual blocker `COUNT` is superseded. Ordinary deletion admission must not enumerate or count all factual Relationships solely for diagnostics.

## Stable Definition-owned cleanup

The current post-Resolution model owns:

```text
RelationshipDefinition
    -> RelationshipDefinitionVersion rows
         -> RelationshipDefinitionProperty rows
    -> relationship_definition_space rows
```

There is no autonomous `RelationshipResolution` state in the M4 model.

`relationship_definition_space` is owned by the stable Definition, not by any exact version. Therefore:

```text
DELETE_DRAFT
    -> relationship_definition_space UNCHANGED

DELETE Definition root
    -> relationship_definition_space owned cleanup
```

The preferred semantic direction is root-owned relational cleanup (FK cascade or equivalent ownership mechanism). Exact physical FK/cascade realization remains architecture work.

No topology/name recertification is required before deletion: removing one Definition cannot introduce a new semantic-cell ownership conflict.

## Blocker arbitration — relational authority

A separate factual-reference `COUNT` is not required. A preflight `EXISTS` is also not required for correctness.

The final lifetime authority should be relational/FK arbitration or an equivalent current-state mechanism that remains valid through the root deletion commit boundary.

Conceptually:

```text
attempt root deletion

current factual Relationship reference exists
    -> deletion cannot commit
    -> 409 delete_blocked
    -> blocker_type = relationship

no factual Relationship reference
    -> root deletion may commit
```

An `EXISTS` probe may still be used as a bounded fail-fast optimization, but it is not the correctness authority because a new factual pin could otherwise appear after the probe.

The root DELETE must have an independent complete lifetime/admission rendezvous with new factual pinning for both:

```text
Relationship.CREATE explicit exact selector
Relationship.CREATE implicit/default selector
```

Exact locking/FK-wait/gate realization belongs to architecture/concurrency work.

## `default_version = NULL` before root delete — revalidated classification

The AS-IS path clears `default_version` before deleting the Definition.

The current physical schema has a cycle:

```text
RelationshipDefinition.default_version
    -> exact RelationshipDefinitionVersion

RelationshipDefinitionVersion.relationship_definition_id
    -> RelationshipDefinition
```

Under that schema, pre-clearing the default breaks the FK cycle before root deletion.

A further defensive intuition is that clearing the default appears to close the implicit-version selection surface. However it is **not** a complete or primary root-delete safety predicate:

```text
- the clear is uncommitted inside the same DELETE transaction and is not independently visible as a durable gate;
- it addresses only implicit/default selection, not explicit exact-version binding;
- root DELETE must rendezvous with new factual pinning regardless of selector form.
```

Therefore M4 classifies the pre-clear as:

```text
semantic root-delete requirement
    -> NO

possible defense-in-depth
    -> YES

known AS-IS physical reason
    -> break current default-version FK cycle
```

Architecture must decide whether the final FK design still requires an explicit pre-clear or whether root deletion can own/cascade the complete aggregate directly. That physical choice must not replace the independent new-pinning lifetime rendezvous.

## Logical DML / ownership cost shape — RATIFIED

Application-level work is bounded/constant in the number of owned rows.

Conceptual mutation:

```text
stabilize Definition lifetime

optional physical pre-clear of default_version
    -> only if final FK realization requires it

DELETE RelationshipDefinition root
    -> owned cleanup of:
         RelationshipDefinitionVersion rows
         RelationshipDefinitionProperty rows
         relationship_definition_space rows
```

No application loop over versions, properties or semantic-space rows is required.

Physical cleanup work is naturally proportional to owned state:

```text
O(number of exact versions
  + number of property rows
  + number of relationship_definition_space rows)
```

while application persistence round trips remain bounded/constant.

No complete Definition topology, RDV property payload, DataType semantics, ObjectTemplate ancestry or semantic-space interpretation is required for deletion admission.

## Shared `last_versions` allocator handoff

The cross-domain version-allocation owner deliberately leaves complete-lineage allocator-row lifetime to architecture.

Therefore root DELETE does not independently decide whether:

```text
last_versions row is retained
or
last_versions row is deleted by some final relational policy
```

The only discovery invariant carried here is that allocator behavior must remain coherent with the cross-domain owner and must not reintroduce version-number reuse semantics accidentally.

## Cache behavior after delete

Immutable exact-RDV cache entries may survive locally after root deletion without correctness impact:

```text
cache presence != current resource existence
cache presence != current lifecycle admission
```

Definition UUIDs/exact-version identities are not reused for a different semantic resource. Distributed cache invalidation is therefore not a correctness prerequisite; local eviction may be opportunistic.

## Technical closure checkpoint

```text
RD root DELETE

semantic preparation
    -> NONE

current/root admission
    -> Definition lifetime/current existence

external blocker authority
    -> relational/FK lifetime arbitration
    -> no diagnostic COUNT
    -> optional bounded EXISTS only as fail-fast

writes
    -> root DELETE
    -> optional pre-clear default only if final FK design requires it

owned cleanup
    -> exact versions
    -> version properties
    -> relationship_definition_space

last_versions
    -> cross-domain architecture handoff

cache
    -> no correctness-driven invalidation

response
    -> 204
```

`RelationshipDefinition.DELETE` is therefore technically closed except for concurrency and physical realization.