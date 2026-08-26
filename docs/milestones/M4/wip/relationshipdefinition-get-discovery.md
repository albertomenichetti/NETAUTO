# RelationshipDefinition GET discovery

Status: WIP / NON-NORMATIVE

## Scope

M4 discovery for the public `RelationshipDefinition.GET` read path. This file records candidate findings only; it does not freeze architecture or authorize implementation.

## Current shape

The current persistence read uses one aggregate projection over `relationship_definitions` and `relationship_resolutions` and reconstructs the complete public aggregate in memory.

The public result requires:

- Definition `id`;
- `symmetric`;
- current nullable `default_version`;
- complete Resolution set with `resolution_id`, current mutable `name`, `from_template_id`, and `to_template_id`.

The aggregate has at most one or two Resolution rows by structural contract, so the current join is bounded.

## Stable versus mutable knowledge

Stable / immutable topology:

- Definition `id`;
- `symmetric`;
- Resolution `id`;
- Resolution membership in the Definition;
- `from_template_id`;
- `to_template_id`.

Current / mutable state:

- Resolution `name`;
- Definition `default_version`.

A candidate worker-local `StableRelationshipDefinitionTopologyCache[definition_id]` should therefore exclude `name` and `default_version`.

## M4 candidate

Keep the public GET as an authoritative one-statement PostgreSQL aggregate read.

Do not bifurcate the DTO read path into cache-hit versus cache-miss variants merely to avoid returning a few stable UUIDs. The public read still needs current names, current default state, and current existence.

The result may opportunistically populate the stable topology cache with no additional database read:

```text
StableRelationshipDefinitionTopologyCache[definition_id]
    id
    symmetric
    resolutions:
        resolution_id
        from_template_id
        to_template_id
```

Cache presence never proves current existence.

## Denormalization

No new relational denormalization is justified for this operation. `relationship_resolutions` already represents the resolved model-plane topology required by the aggregate.

## Candidate conclusion

`RelationshipDefinition.GET` is already essentially minimal: one authoritative aggregate projection, optional stable-topology cache fill from the returned data, no additional query, and no new denormalization.
