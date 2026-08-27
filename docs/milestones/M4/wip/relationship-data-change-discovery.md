# M4 — Relationship DATA_CHANGE discovery

**Status:** WIP / NON-NORMATIVE

## Scope

First-phase operation audit only. Lock design, lifecycle-display metadata race handling, and final concurrency proofs are deferred to the global concurrency phase.

## Current path

The current `Relationship.DATA_CHANGE` path validates the operation set, checks/locks the factual Relationship, then calls `_validated()` before applying the data change. `_validated()` currently reloads and revalidates the factual aggregate, RelationshipDefinition topology, endpoint Object template ids, the complete ObjectTemplate parent graph, exact RelationshipDefinitionVersion schema, exact DataType dependencies, and persisted property canonicality. Immediately afterwards `DATA_CHANGE` calls `_relationship_schema()` again, causing the same exact RelationshipDefinitionVersion and DataType semantic payload to be loaded/reconstructed a second time.

## Findings

### 1. Persisted topology/closure must not be recertified for DATA_CHANGE

`DATA_CHANGE` mutates only `relationships.properties`. It does not alter:

- `relationship_definition_id`;
- `relationship_definition_version`;
- `runtime_relationship_resolutions`;
- factual endpoint identities.

The factual Relationship has already been admitted and its complete runtime closure is already materialized. Revalidating RelationshipDefinition topology, ObjectTemplate ancestry, and runtime closure on every property mutation is therefore read-side/model-side recertification in the hot data-plane path.

Candidate M4 rule:

```text
Relationship.DATA_CHANGE
    trusts admitted persisted relationship identity + runtime closure
    does not reconstruct/recertify model topology or ObjectTemplate ancestry
```

### 2. Exact schema semantics belong in the immutable RDV cache

A factual Relationship remains pinned to one exact RelationshipDefinitionVersion. That exact version may later be `DEPRECATED`, but its semantic payload remains immutable and valid for the already-admitted factual Relationship.

Candidate cache:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
    ordered property declarations
    exact DataType pins
    compiled RuntimePropertySpec / validators
```

For `DATA_CHANGE`, no current `PUBLISHED` admission check is required for the existing source version. PostgreSQL remains authority for the current factual row, while the cache provides immutable exact-schema semantics.

Hot-path target:

```text
PostgreSQL
    current factual Relationship state

worker cache
    immutable exact RDV compiled schema

apply_data_change(...)
```

This removes, on a warm cache path:

- RDV property rereads;
- DataType semantic-payload rereads;
- repeated RuntimePropertySpec construction.

The existing second `_relationship_schema()` load after `_validated()` is unconditionally redundant once the current exact schema is already available.

### 3. No-op handling remains valuable

If `apply_data_change()` yields the same canonical properties as the current factual state, preserve the no-op behavior:

```text
no properties UPDATE
no DATA_CHANGE lifecycle event
```

### 4. Lifecycle display metadata optimization remains OPEN

`LifecycleStore.relationship_views()` currently rereads runtime closure, current RelationshipResolution names, and endpoint Object canonical names for the response/event projection. A future targeted factual projection may be able to capture those values once and reuse them.

However, this interacts with concurrent Object rename / RelationshipDefinition rename and the requirement that historical lifecycle metadata be coherent. Therefore elimination or relocation of this read is explicitly deferred to the concurrency phase.

## Candidate target path

```text
validate operation set in memory
-> lock current Relationship
-> load current factual state required for mutation/response
-> immutable RDV runtime-cache lookup
-> apply_data_change()
-> if no-op: no UPDATE/event
-> else one UPDATE relationships.properties
-> coherent lifecycle metadata/event path
-> COMMIT
```

## Non-decisions

This WIP does not redesign locks, define rename-race behavior for lifecycle metadata, or freeze cache implementation details.
