# RelationshipDefinition CREATE — M4 discovery

Status: WIP / NON-NORMATIVE

## Scope

Operation-level audit of `RelationshipDefinition.CREATE` under the M4 discovery rules. This file records candidate findings only. Lock/concurrency redesign is explicitly deferred to the later global concurrency phase.

## Current semantic shape

A RelationshipDefinition separates:

- stable Definition identity and structural symmetry;
- a complete persisted RelationshipResolution set representing the resolved topology contract;
- mutable Resolution `name` metadata and nullable `default_version`;
- lifecycle-managed exact RelationshipDefinitionVersion property schemas.

The existing `relationship_resolutions` rows are already an intentional model-plane materialization/denormalization: CREATE/RENAME certify the complete topology contract and persist the resolved perspectives so runtime consumers do not reinterpret source/target or forward/reverse semantics.

## CREATE current high-level path

Current CREATE:

1. constructs the complete symmetric/non-symmetric Definition candidate and Resolution set;
2. resolves exact DataType dependencies for initial property declarations;
3. acquires endpoint/DataType lock intents under the global RelationshipDefinition conflict gate;
4. certifies the candidate against the globally committed Definition set and the ObjectTemplate lineage graph;
5. resolves DataType dependencies again under the stabilized lock plan;
6. validates the initial DRAFT version;
7. inserts Definition, Resolution rows, DRAFT v1 and property declarations;
8. commits atomically.

The double dependency resolution is currently part of lock-plan stabilization and is not treated as accidental redundancy in this phase.

## Existing materialization is structurally sufficient for equivalence/conflict

Definition semantic equivalence is exactly:

```text
symmetric
+
complete set of (from_template_id, to_template_id, name)
```

Cross-Definition Resolution conflict is exactly:

```text
same name
AND from-lineage spaces overlap
AND to-lineage spaces overlap
```

With single stable ObjectTemplate inheritance, lineage spaces overlap iff the two lineages are equal or one is an ancestor/descendant of the other.

All Definition/Resolution fields needed by these predicates are already persisted in:

```text
relationship_definitions.symmetric
relationship_resolutions.relationship_definition_id
relationship_resolutions.from_template_id
relationship_resolutions.to_template_id
relationship_resolutions.name
```

Therefore the current resolved graph materialization does not appear to lack structural information for equivalence/conflict certification.

## M4 stable ancestry dependency

M4 has a strong candidate ObjectTemplate stable ancestry closure:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

Prefer self rows (`descendant == ancestor`, `depth == 0`) so equality and ancestry can be handled uniformly.

This closure allows RelationshipDefinition certification to answer endpoint-space overlap directly in PostgreSQL instead of loading the whole ObjectTemplate parent graph and walking it in Python.

## Candidate certification path

Current `_certify()` loads:

```text
all RelationshipDefinitions + all Resolutions
+
all ObjectTemplate (id, parent_template_id) rows
```

and recomputes equivalence/conflict in Python.

Candidate M4 direction:

```text
candidate Definition (max 1-2 Resolutions)
        +
relationship_definitions
relationship_resolutions
object_template_ancestry
        ↓
set-based PostgreSQL certification
        ↓
equivalent_definition_id?
conflicting_definition_id?
conflicting_name?
```

The target is to stop materializing the complete committed catalog into application memory for every CREATE/RENAME.

No additional Relationship-specific expanded applicability table is currently justified. In particular, do not pre-expand each Resolution into all applicable descendant templates: creating a new ObjectTemplate descendant would create fan-out maintenance across unrelated RelationshipDefinitions. The stable ancestry closure gives the same query capability without this inverse maintenance burden.

No persisted semantic-signature hash is currently required. Revisit only if a later operation proves the set-based exact comparison materially insufficient.

## Initial DRAFT version findings

CREATE owns a brand-new Definition UUID. Therefore committed PUBLISHED/DEPRECATED property history for this Definition is necessarily empty.

Candidate simplification:

```text
CREATE v1 DRAFT
    validate declaration shape
    do not query published_history(definition_id)
```

Historical continuity remains necessary for later REVISE/PUBLISH operations.

The new v1 is DRAFT and therefore is not eligible for an immutable RelationshipDefinitionVersion runtime cache.

## Stable topology cache candidate

After successful commit, CREATE already has the complete stable topology candidate in memory.

Candidate worker-local cache:

```text
StableRelationshipDefinitionTopologyCache[definition_id]
    definition_id
    symmetric
    resolutions:
        resolution_id
        from_template_id
        to_template_id
```

Exclude mutable `name` and `default_version`.

Cache population after commit is opportunistic and requires no extra database read. Cache presence never proves current Definition existence.

## DML shape

Current persistence inserts:

```text
1 Definition row
R Resolution rows   (R structurally bounded to 1 or 2)
1 version row
P property rows
```

The Resolution count is bounded and therefore not a major scaling concern, but set-based/bulk insertion is still straightforward. Property declarations are unbounded and should be bulk inserted.

Candidate DML shape:

```text
1 INSERT Definition
1 bulk INSERT Resolution set
1 INSERT version
1 bulk INSERT properties (when non-empty)
```

at most four DML statements, excluding concurrency realization.

## Deliberately deferred

The following remain for the global concurrency phase:

- exact serialization/rendezvous required for conflict certification;
- whether the current advisory conflict gate remains necessary once certification becomes set-based;
- race behavior against concurrent CREATE/RENAME/DELETE;
- interaction with concurrent ObjectTemplate lineage creation/deletion and ancestry materialization;
- exact PostgreSQL locking/failure classification.

## Current candidate conclusion

RelationshipDefinition already has the important model-plane denormalization: the complete persisted `RelationshipResolution` resolved graph. M4 should first exploit this existing materialization together with the stable ObjectTemplate ancestry closure to make equivalence/conflict certification set-based. No additional expanded Relationship topology materialization is currently justified by CREATE.
