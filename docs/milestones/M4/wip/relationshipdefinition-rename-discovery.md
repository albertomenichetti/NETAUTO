# RelationshipDefinition RENAME — M4 discovery

Status: WIP / NON-NORMATIVE

## Scope

Operation-by-operation M4 discovery for RelationshipDefinition RENAME. Lock redesign is explicitly deferred to the later global concurrency phase.

## Current semantic shape

RENAME changes only mutable `RelationshipResolution.name` metadata.

Stable topology remains unchanged:

- `RelationshipDefinition.id`;
- `RelationshipDefinition.symmetric`;
- `RelationshipResolution.id`;
- `from_template_id`;
- `to_template_id`.

`default_version` is unrelated current mutable state.

## AS-IS data path

Current application flow:

1. acquire the Definition header lock plus the global RelationshipDefinition conflict gate;
2. load the complete current Definition aggregate;
3. construct the renamed candidate while preserving Definition/Resolution identity and endpoint topology;
4. run global `_certify()`;
5. update the complete Resolution name set;
6. commit.

The current `_certify()` loads:

- the complete persisted RelationshipDefinition + Resolution catalog;
- the complete ObjectTemplate parent graph;

and re-evaluates equivalence/conflict in Python.

The persistence DML for the rename itself is already set-based: all Resolution names are updated by one `UPDATE ... CASE` statement.

## M4 finding: reuse existing resolved-graph materialization

`relationship_resolutions` is already the materialized resolved topology contract for a Definition.

Equivalence and cross-Definition conflict require only:

- persisted `relationship_definitions.symmetric`;
- persisted Resolution `(from_template_id, to_template_id, name)` tuples;
- stable ObjectTemplate ancestry overlap.

Once M4 introduces the stable ObjectTemplate ancestry closure, RENAME certification can be expressed set-based against:

```text
candidate renamed Resolution set
+
relationship_definitions
+
relationship_resolutions
+
object_template_ancestry
```

rather than loading/revalidating the entire certified set and ObjectTemplate graph in the application.

No additional Relationship-specific denormalization is currently required for this operation.

## Cache implication

A candidate stable RelationshipDefinition topology cache should contain only stable topology, for example:

```text
StableRelationshipDefinitionTopologyCache[definition_id]
    id
    symmetric
    resolutions:
        resolution_id
        from_template_id
        to_template_id
```

`name` and `default_version` must not be part of that stable cache because they are mutable current state.

Therefore RENAME does not invalidate the stable topology cache.

Consumers requiring the current Resolution name continue to use PostgreSQL current truth unless a separate explicitly mutable cache protocol is ever introduced; M4 does not propose such a protocol.

## Candidate M4 data path

Conceptually:

```text
load current Definition aggregate
    -> build renamed candidate

set-based equivalence/conflict certification
    candidate resolutions
    + relationship_resolutions
    + object_template_ancestry

single bulk UPDATE of names
COMMIT
```

The initial aggregate read is not considered a meaningful optimization target because RENAME is a rare model-plane mutation and must know the current Definition shape and Resolution membership anyway.

## Deferred concurrency question

The existing Definition lock and global conflict gate are not redesigned here. The later global concurrency phase must prove how concurrent CREATE/RENAME/DELETE operations preserve semantic uniqueness and cross-Definition conflict freedom with the new set-based certification path.
