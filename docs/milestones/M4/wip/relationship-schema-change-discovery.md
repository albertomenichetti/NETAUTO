# M4 — Relationship SCHEMA_CHANGE Discovery

**Status:** WIP / NON-NORMATIVE

## Scope

First-phase audit of factual `Relationship.SCHEMA_CHANGE`. Concurrency protocol and lock design remain deferred to the later global concurrency phase.

## Current behavior

The current path:

- reads factual Relationship header;
- loads the complete RelationshipDefinition aggregate;
- loads the target exact RelationshipDefinitionVersion and requires `PUBLISHED`;
- stabilizes locks;
- revalidates the whole persisted factual aggregate via `_validated()`, including Definition topology, endpoint Object template ids, complete ObjectTemplate lineage graph, runtime closure, source exact RDV, exact DataTypes and canonical properties;
- reloads the target RDV;
- reloads complete PUBLISHED/DEPRECATED RelationshipDefinitionVersion history and recertifies target history;
- loads source exact schema + DTVs;
- loads target exact schema + DTVs;
- migrates properties;
- updates exact version pin and full properties map in one UPDATE;
- emits the complete SCHEMA_CHANGE event set.

## Findings

### Complete RelationshipDefinition aggregate is unnecessary

A factual Relationship already has a stable `relationship_definition_id` and current exact version pin. SCHEMA_CHANGE does not change Definition identity or runtime closure. The target can be addressed directly as `(relationship_definition_id, target_version)`. Symmetry, Resolution names and topology are not migration inputs.

### Persisted topology and runtime closure must not be recertified

A successful SCHEMA_CHANGE changes only:

```text
relationship_definition_version
properties
```

The materialized `runtime_relationship_resolutions` closure is preserved unchanged. Therefore the normal data-plane path does not need to revalidate Definition topology, ObjectTemplate ancestry, endpoint compatibility or closure completeness.

### `published_history()` must leave the data-plane

The target version is required to be already PUBLISHED. RelationshipDefinitionVersion publication is the model-plane certification boundary, including all-history property continuity required for out-of-order publication safety. Once published, target semantic content is immutable.

Therefore SCHEMA_CHANGE must trust the already-certified target instead of reloading all PUBLISHED/DEPRECATED versions and calling `validate_relationship_property_history()` again.

### Source and target semantic schemas are immutable cache candidates

Migration requires source and target exact semantic declarations, including:

- property name;
- position;
- stable datatype lineage id;
- exact datatype version;
- value mode;
- compiled runtime validator semantics.

These are immutable for PUBLISHED/DEPRECATED versions and belong in:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
```

The source may be PUBLISHED or DEPRECATED. The target must be PUBLISHED at mutation time.

### PostgreSQL remains authority for current target admission

Cache presence cannot prove current lifecycle admission. PostgreSQL must verify current target existence and `status == PUBLISHED` and preserve the current lifecycle rule for direct exact DataType dependencies of an active target.

The target current-admission projection should be narrow and set-based; it should not need full RDV property/constraint payloads when compiled immutable semantics are already cached.

### DML is already conceptually correct

`RuntimeRelationshipStore.update_schema()` atomically updates the factual exact version pin and complete canonical properties map in one UPDATE. Runtime closure remains unchanged.

## Candidate data path

```text
validate target_version

load/lock current factual Relationship
    id
    definition_id
    source_version
    properties
    runtime closure/event state

require target_version > source_version

PostgreSQL current target admission
    same Definition exact target exists
    target status == PUBLISHED
    direct exact DTV dependencies currently admissible

immutable cache lookup
    source compiled exact schema
    target compiled exact schema

migrate_relationship_properties(...)

one UPDATE
    relationship_definition_version = target_version
    properties = migrated canonical map

runtime closure unchanged

emit complete SCHEMA_CHANGE event set
COMMIT
```

A SCHEMA_CHANGE event is still emitted even when source and migrated canonical maps are equal, because the exact schema pin changes.

## Deferred concurrency questions

The exact lock/current-admission protocol remains open for the global concurrency phase. The optimization of lifecycle display-metadata acquisition also remains open because it must preserve coherent metadata under concurrent Object or RelationshipDefinition renames.
