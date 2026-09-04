# RelationshipDefinition DELETE — M4 discovery

Status: **ACTIVE TECHNICAL REVIEW / RATIFIED ROOT-DELETE GATE CHECKPOINT / WIP / NON-NORMATIVE**

This note is operation-specific source/evidence subordinate to `relationshipdefinition.md` and to the current RelationshipDefinition technical-consolidation ledger. It does not authorize implementation or freeze final FK/lock/gate realization.

## Current M4 semantic boundary

`DELETE /relationship-definitions/{id}` removes the complete stable RelationshipDefinition aggregate.

A current factual Relationship referencing any exact version of the Definition is an external lifetime blocker.

The reviewed M4 failure contract requires only:

```text
409 delete_blocked
    details.blocker_type = relationship
```

Therefore the AS-IS total factual blocker `COUNT` is superseded. Ordinary deletion admission needs only an existence proof / bounded blocker witness and must not enumerate or count all factual Relationships solely for diagnostics.

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

## Minimal admission path

Conceptually the root delete needs only:

```text
RelationshipDefinition current existence
+
EXISTS current factual Relationship referencing the Definition
```

If a factual blocker exists:

```text
-> 409 delete_blocked
-> stop after sufficient blocker proof
```

If no blocker exists, the root aggregate may be deleted atomically with its owned state.

No complete Definition topology, RDV property payload, DataType semantics, ObjectTemplate ancestry or `relationship_definition_space` interpretation is required for admission.

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

The M2 concurrency realization already treated root deletion and factual Relationship CREATE as an independent reference-lifetime race:

```text
RelationshipDefinition root DELETE
    -> root Definition lifetime protection

Relationship.CREATE explicit exact selector
    -> stabilizes Definition lifetime + exact RDV admission

Relationship.CREATE implicit/default selector
    -> stabilizes Definition/default selection + exact RDV admission
```

Therefore M4 carries forward this discovery-level requirement:

```text
root DELETE vs new factual pinning
    -> requires one complete independent lifetime/admission rendezvous
    -> covers both explicit and implicit Relationship.CREATE
```

while classifying the pre-clear itself as:

```text
semantic root-delete requirement
    -> NO

possible defense-in-depth
    -> YES

known AS-IS physical reason
    -> break current default-version FK cycle
```

Architecture must decide whether the final FK design still requires an explicit pre-clear or whether root deletion can own/cascade the complete aggregate directly. That physical choice must not replace the independent new-pinning lifetime rendezvous.

## Cache behavior after delete

Immutable exact-RDV cache entries may survive locally after root deletion without correctness impact:

```text
cache presence != current resource existence
cache presence != current lifecycle admission
```

Definition UUIDs/exact-version identities are not reused for a different semantic resource. Distributed cache invalidation is therefore not a correctness prerequisite; local eviction may be opportunistic.

## Still open before technical closure

The remaining root-DELETE checkpoint is the final logical DML/ownership cost shape, including the treatment of the shared version-allocation row (`last_versions`) and the explicit architecture handoffs for lifetime arbitration and physical cascade/default-FK realization.
