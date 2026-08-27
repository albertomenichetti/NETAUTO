# M4 WIP — Object Relationship list API discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the M4 brainstorming around `GET /objects/{id}/relationships` after revisiting the public Object and Relationship representations. It is discovery only and does not freeze the public contract.

## Concrete consumer question

Consider `server-1` with several factual Relationships such as:

```text
connected_to -> switch-1
connected_to -> switch-2
powered_by   -> pdu-1
```

The generic relationship list remains useful because, unlike Object components, factual Relationships are not embedded in the candidate `GET /objects/{id}` response.

The collection therefore continues to have a clear role:

```text
GET /objects/server-1/relationships
    -> all factual relationships visible from server-1
    -> filterable / paginated
```

## Candidate summary shape

The current list item contains:

```text
relationship_id
relationship_definition_id
relationship_definition_version
object_id
destination_object_id
name
properties
```

Two changes are strong candidates.

First, `object_id` is redundant in a path-scoped collection because the caller already requested `/objects/{object_id}/relationships`.

Second, a bare `destination_object_id` is inconvenient for ordinary consumers. A consumer commonly needs to display the destination by name and should not require an N+1 series of Object GETs merely to render a page.

Candidate item:

```json
{
  "id": "relationship-id",
  "name": "connected_to",
  "destination": {
    "id": "switch-1-id",
    "canonical_name": "switch-1"
  },
  "relationship_definition_id": "...",
  "relationship_definition_version": 3
}
```

The exact wire naming remains open, but destination Object identity plus current canonical name is a strong candidate.

## Properties should not be part of the collection item

The current `ObjectRelationshipViewDto` includes the factual Relationship `properties` JSON object. M4 brainstorming favors removing it from this paged collection.

Concrete reason:

```text
GET /objects/server-1/relationships?limit=100
```

is a paged lookup over Relationship roots. If each of the 100 items carries an arbitrarily large property set, the cost and payload size of one page become coupled to the complete schema/data size of every Relationship in the page.

This is analogous to the agreed Object-family split:

```text
GET /objects
    -> lightweight Object summaries

GET /objects/{id}
    -> complete Object detail
```

The corresponding Relationship split is therefore a strong candidate:

```text
GET /objects/{id}/relationships
    -> Relationship summaries relative to the requested Object
    -> NO complete factual properties

GET /relationships/{relationship_id}
    -> complete factual Relationship
    -> properties included
```

If a future consumer needs a table that projects selected Relationship properties across many rows, that is a better fit for the planned M5 Query API than for forcing every REST collection item to contain every property.

## Persistence consequence

The current one-statement Object Relationship page remains conceptually correct and should continue to trust admitted persisted runtime state.

The target page projection can be simplified by omitting `relationships.properties` from the selected public fields and adding a join to the destination `objects` row for current `canonical_name`.

No new denormalization or cache is justified for this read. Destination Object name is mutable current truth and should come from PostgreSQL in the same statement snapshot.

## Candidate first-phase conclusion

Keep `GET /objects/{id}/relationships` as the generic paginated/filterable Relationship collection, but make each item a Relationship summary rather than a complete factual Relationship.

Strong candidate summary fields:

```text
relationship id
relationship name
relationship_definition_id
relationship_definition_version
destination Object {id, canonical_name}
```

Do not return Relationship `properties` in this collection; expose them through `GET /relationships/{id}` instead.

## Open decisions

- exact DTO/wire field names (`id` vs `relationship_id`, nested `destination` shape);
- whether `relationship_definition_version` is useful enough to keep in the summary;
- exact ordering/cursor implications if the public item shape changes;
- whether current Relationship name remains a direct scalar or a more explicit perspective object;
- compatibility strategy for clients currently consuming collection `properties`.