# RelationshipDefinition LIST definitions — M4 discovery

Status: WIP / NON-NORMATIVE

## AS-IS

`RelationshipDefinitionStore.list_definitions()` already realizes the public collection as one PostgreSQL statement:

- page Definition IDs first;
- join that bounded page to `relationship_resolutions`;
- reconstruct complete Definition aggregates;
- preserve cursor ordering by Definition ID.

The page-first CTE avoids applying LIMIT to the row-multiplied Definition+Resolution join.

Each public item needs the fields already projected:

- Definition `id`;
- `symmetric`;
- mutable `default_version`;
- Resolution `id`;
- mutable `name`;
- `from_template_id`;
- `to_template_id`.

No material over-read was identified.

## M4 candidate

Keep the current one-statement paginated aggregate projection.

The result naturally contains enough immutable/stable topology to populate a worker-local stable cache without any extra SQL:

```text
StableRelationshipDefinitionTopologyCache[definition_id]
    id
    symmetric
    resolutions:
        resolution_id
        from_template_id
        to_template_id
```

However, broad LIST-driven cache population should remain an optional cache policy rather than a required semantic behavior: paginated browsing may touch many Definitions that the worker never consumes on the data plane, so mandatory warming could create cache pollution.

Do not add query columns solely for cache warming.

## Denormalization

No new denormalization is justified. `relationship_resolutions` already is the persisted resolved model graph consumed by the public projection.

## Candidate decision

`RelationshipDefinition.LIST` remains the current one-statement paginated aggregate read. Optional opportunistic stable-topology cache fill is acceptable; mandatory bulk warming is not required.
