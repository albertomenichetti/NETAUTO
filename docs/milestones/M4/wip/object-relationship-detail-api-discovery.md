# M4 WIP — Object-relative Relationship detail API discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records only the broad API direction agreed during M4 discovery. It intentionally does not freeze the exact route shape, perspective selector, error semantics, self-loop handling, or DTO details. Those will be reviewed operation by operation later.

## Problem

A factual Relationship is a global fact identified by `relationship_id`, but the public runtime model also exposes object-relative semantic views of that fact.

For a non-symmetric Relationship, the same fact may be visible differently from its two endpoint Objects. Example:

```text
server-1 -> switch-1 / connected_to
switch-1 -> server-1 / connected_from
```

A consumer navigating from `server-1` usually wants the first perspective only. Returning the reciprocal perspective merely because both belong to the same factual Relationship is not necessarily useful in that context.

The existing root read:

```text
GET /relationships/{relationship_id}
```

has no Object context, so returning the complete factual Relationship projection, including all distinct semantic views, is conceptually coherent.

However, it does not directly answer the different question:

```text
show relationship R as seen from object server-1
```

## Agreed broad direction

Introduce an Object-relative Relationship detail read alongside the existing Object-relative Relationship collection.

Conceptually:

```text
GET /objects/{object_id}/relationships
    -> paginated Relationship summaries relative to that Object

GET /objects/{object_id}/relationships/{relationship_id} [perspective discriminator TBD]
    -> one complete Relationship detail relative to that Object
```

The exact route/query design is deliberately OPEN.

The Object-relative detail should normally expose one semantic perspective, for example:

```json
{
  "id": "relationship-id",
  "name": "connected_to",
  "destination": {
    "id": "switch-1-id",
    "canonical_name": "switch-1"
  },
  "relationship_definition_id": "definition-id",
  "relationship_definition_version": 3,
  "properties": {
    "speed": 10000,
    "medium": "fiber"
  }
}
```

It should not automatically include the reciprocal `switch-1 -> server-1 / connected_from` view when the request is explicitly rooted at `server-1`.

## Relationship root read remains a distinct question

The existing root read remains conceptually useful:

```text
GET /relationships/{relationship_id}
    -> factual Relationship viewed independently of a specific Object
```

Because this request has no source Object context, exposing the complete set of public semantic views remains a coherent candidate.

Therefore the two reads answer different questions rather than duplicating each other:

```text
GET /relationships/{id}
    -> what is this factual Relationship globally?

Object-relative detail
    -> what does this factual Relationship mean from this Object?
```

## Properties

The Object-relative Relationship collection is a summary surface and should not return the potentially unbounded Relationship `properties` map.

The Object-relative Relationship detail is a single-resource detail surface and may return the complete factual `properties` map, analogous to the distinction between Object list and Object detail reads.

## Important ambiguity kept open

A factual Relationship can produce more than one semantic view for the same Object in edge cases such as permitted self-loops and overlapping applicable perspectives.

Therefore `object_id + relationship_id` may not always uniquely identify one semantic view.

M4 discovery intentionally does not freeze how the caller selects the intended perspective. Candidate mechanisms to evaluate later include a public relationship name or another stable public selector. Internal persistence identities must not be exposed merely for implementation convenience.

## Deferred decisions

The following are explicitly deferred to the detailed per-route API review:

- exact URL shape;
- whether an additional perspective selector is always required or only when ambiguous;
- whether that selector is a path component or query parameter;
- exact public selector semantics and rename behavior;
- self-loop behavior;
- not-found vs ambiguity error semantics;
- exact DTO naming and field shape;
- ordering and pagination interaction with the collection;
- whether the root `GET /relationships/{id}` representation should include current Object canonical names in all global views;
- exact SQL projection and current-name joins.

## Candidate conclusion

Keep the factual Relationship root read and add a distinct Object-relative Relationship detail capability. The former represents the global fact; the latter represents one complete semantic perspective rooted at a specific Object. Freeze the exact API mechanics only during the later detailed route-by-route review.
