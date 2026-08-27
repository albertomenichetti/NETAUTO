# M4 — Relationship DELETE discovery

**Status:** WIP / NON-NORMATIVE

## Scope

First-phase M4 audit of factual `Relationship.DELETE`. Lock redesign and concurrency protocol changes are explicitly deferred to the global concurrency phase.

## Current shape

The current application flow acquires the factual Relationship lock and then calls `_validated()`. That helper reloads the factual aggregate, RelationshipDefinition, endpoint template ids, the complete ObjectTemplate lineage graph, exact RelationshipDefinitionVersion semantics and exact DataType dependencies, and revalidates persisted topology, runtime closure and canonical properties. The DELETE path then calls `LifecycleStore.relationship_views()` to reload the persisted runtime closure plus current Resolution names and endpoint Object canonical names, deletes the factual root, inserts the complete DELETE lifecycle event set, and commits.

## First-phase findings

### Semantic recertification is unnecessary

`Relationship.DELETE` does not make an admission decision based on RelationshipDefinition topology, ObjectTemplate ancestry, exact schema semantics, DataType semantics, or re-derived runtime closure. If the current factual Relationship exists, it can be deleted. The operation only needs the authoritative factual before-state and coherent historical display metadata for the DELETE lifecycle event.

Therefore `_validated()` is the wrong read shape for DELETE and should not be part of the target hot path.

### Candidate pre-delete projection

A single authoritative PostgreSQL projection can provide:

- factual root: `id`, `relationship_definition_id`, `relationship_definition_version`, `properties`;
- complete persisted `runtime_relationship_resolutions` closure;
- current `RelationshipResolution.name` for each closure row;
- current canonical names for both endpoint Objects.

This projection should retain only structural coherence checks needed to materialize one persisted aggregate; it should not re-derive the expected closure from model topology.

### Delete DML

`RuntimeRelationshipStore.delete()` already deletes only the factual root. `runtime_relationship_resolutions` is owned state with `ON DELETE CASCADE`, so no explicit closure delete is required.

Target DML remains conceptually:

```text
1 DELETE relationships row
    -> runtime closure CASCADE
```

The complete DELETE lifecycle event set is already inserted in bulk and should remain atomic with the root delete.

### Ordering

Historical event metadata must be captured before deleting the factual root because the runtime closure disappears by cascade. Conceptually:

```text
capture factual before-state + current display metadata
DELETE factual root (closure cascades)
INSERT complete DELETE event set
COMMIT
```

### Cache / denormalization

No M4 cache is useful for this operation. RDV/DataType semantics, ObjectTemplate ancestry, and stable RelationshipDefinition topology are not needed. Resolution names and Object canonical names are mutable current metadata and must come from PostgreSQL.

No new denormalization is justified; the existing factual root, materialized runtime closure and lifecycle event table already provide the required durable state.

## Candidate M4 data path

```text
lock current factual Relationship
-> one authoritative pre-delete projection
   - factual root
   - complete persisted closure
   - current Resolution names
   - current endpoint canonical names
-> DELETE factual root
   - runtime closure CASCADE
-> bulk INSERT complete RELATIONSHIP_DELETED event set
-> COMMIT
```

## Deferred to concurrency phase

The exact synchronization needed to make lifecycle display metadata coherent with concurrent Object/RelationshipDefinition renames remains open for the global concurrency phase. This WIP does not redesign locks.
