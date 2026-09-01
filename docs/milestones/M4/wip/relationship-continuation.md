# M4 — Factual Relationship temporary continuation

**Status:** TEMPORARY CONTINUATION / WIP / NON-NORMATIVE / MUST MERGE BACK

## Purpose and governance exception

The canonical single owner for factual Relationship remains:

```text
docs/milestones/M4/wip/relationship.md
```

This file exists only as a temporary append-only continuation because the current repository connector cannot safely replace the now-large canonical owner without a lossless full-file round trip.

It is **not** a second factual Relationship owner and must not be treated as an independent source of truth. While it exists:

```text
relationship.md
    -> canonical historical owner up to its latest recorded checkpoint

relationship-continuation.md
    -> temporary ordered continuation containing only later explicitly ratified checkpoints
```

Mandatory consolidation rule:

```text
before factual Relationship review is considered complete
    -> merge this file losslessly back into relationship.md
    -> verify merged content against both source files
    -> delete relationship-continuation.md in the same consolidation step
```

No implementation authorization is implied. All checkpoints remain M4 WIP/non-normative.

---

# Continuation checkpoints

## C-REL-01 RATIFIED — Object-scoped item shape survives post-definition review

For:

```text
GET /api/v1/core/objects/{object_id}/relationships
```

the pre-freeze public item shape remains valid against the ratified `runtime_relationship_cells` data-plane relation:

```text
ObjectRelationshipItem
    relationship_id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: positive integer
    properties: object
    name: string
    destination_object: ObjectReference

ObjectReference
    id: UUID
    canonical_name: string
```

Post-definition semantics and projection are:

```text
runtime_relationship_cells.relationship_id
    -> relationship_id

runtime_relationship_cells.name
    -> name
    -> stable semantic name of this exact Object-level runtime cell

runtime_relationship_cells.to_object_id
    -> destination_object.id

relationships.relationship_definition_id
    -> relationship_definition_id

relationships.relationship_definition_version
    -> relationship_definition_version

relationships.properties
    -> properties

objects[to_object_id].canonical_name
    -> destination_object.canonical_name
```

The route path already supplies the source Object context, so `from_object_id` is intentionally not repeated in each item.

There is:

```text
NO resolution_id
NO autonomous RelationshipResolution identity
NO runtime-row deduplication
NO model-plane RelationshipDefinition read/reconstruction
NO relationship_definition_space read
NO ObjectTemplate ancestry read
```

`name` is no longer mutable Resolution display metadata. It is stable semantic state materialized directly in `runtime_relationship_cells`.

The current Object `canonical_name` remains mutable Object-owned display metadata and is joined live from `objects` rather than copied into the runtime relation.

## C-REL-02 RATIFIED — `relationship_definition_id` Object-scoped filter survives unchanged

The optional public filter remains:

```text
relationship_definition_id: UUID, optional
```

Its semantics remain:

```text
omitted
    -> do not restrict Object-visible factual Relationships by Definition

present
    -> return only Object-visible factual Relationships whose owning factual root
       has relationships.relationship_definition_id = supplied value
```

The post-definition data path is naturally:

```text
runtime_relationship_cells AS c
JOIN relationships AS r
    ON r.id = c.relationship_id

WHERE c.from_object_id = :object_id
  AND r.relationship_definition_id = :relationship_definition_id   # when supplied
```

The join to `relationships` is already required by the item projection for Definition/version/property factual root state, so this filter introduces no model-plane read and provides no reason to duplicate `relationship_definition_id` back into `runtime_relationship_cells`.

Existence/membership semantics remain:

```text
supplied relationship_definition_id does not exist
OR exists but yields no Object-visible factual Relationship
    -> 200 OK
    -> items = []
    -> next_cursor = null
```

because `relationship_definition_id` is a collection filter, not a parent/resource selector on this route.

## C-REL-03 RATIFIED — Object-scoped `name` exact-match filter is restored

The post-definition Object-scoped collection exposes the optional public filter:

```text
name: string, optional
```

with **exact-match semantic filtering** over the stable semantic name already materialized in the factual runtime cell:

```text
runtime_relationship_cells.name = supplied name
```

Conceptually:

```text
runtime_relationship_cells AS c
JOIN relationships AS r
    ON r.id = c.relationship_id

WHERE c.from_object_id = :object_id
  AND c.name = :name                         # when supplied
  AND r.relationship_definition_id = :relationship_definition_id  # when supplied
```

This reverses the pre-freeze M4 removal of the `name` filter. The old removal rationale depended on `RelationshipResolution.name` being mutable model-plane/display state. Under the ratified post-definition model, `name` is instead stable semantic state of the exact Object-level runtime cell, so exact filtering is now a direct navigation predicate over the collection being represented.

Semantics are:

```text
name omitted
    -> do not restrict Object-visible factual Relationship perspectives by semantic name

name present
    -> return only runtime cells visible from object_id whose stable semantic name
       exactly equals the supplied value
```

`name` need not be globally unique. Multiple matching factual Relationships are returned normally. It composes naturally with `relationship_definition_id`:

```text
?name=connected_to
    -> all matching Object-visible perspectives across Definitions

?relationship_definition_id=D1&name=connected_to
    -> matching Object-visible perspectives restricted to D1
```

This endpoint does **not** become a textual/search surface. M4 does not add:

```text
prefix matching
substring/contains matching
regex matching
fuzzy matching
case-insensitive search semantics
```

Those broader discovery semantics remain outside this navigation contract and belong to M5 Search API unless separately justified.

A supplied `name` that matches no current Object-visible runtime cell yields the normal empty collection:

```text
200 OK
items = []
next_cursor = null
```

## C-REL-04 RATIFIED — Object-scoped cursor is bound to the complete filter scope

The opaque keyset cursor is bound to the exact Object-scoped navigation/query scope that produced it.

Post-definition public binding semantics are:

```text
cursor bound to:
    this Object-scoped Relationship collection/cursor kind
    object_id from the route path
    relationship_definition_id filter value,
        including the explicit semantic state "filter omitted"
    name filter value,
        including the explicit semantic state "filter omitted"

cursor not bound to:
    limit
```

Therefore callers may change `limit` while continuing the same traversal, but they may not reuse a cursor across a change in either filter scope.

Examples:

```text
cursor produced by:
    /objects/O1/relationships?name=runs_on

is incompatible with:
    /objects/O1/relationships?name=connected_to
    /objects/O1/relationships
```

and likewise a cursor produced under one `relationship_definition_id` value cannot be reused with another value or with the filter omitted.

A malformed cursor or a cursor incompatible with the current collection kind / `object_id` / `relationship_definition_id` / `name` scope is rejected with:

```text
400 Bad Request
code: invalid_cursor
```

The cursor remains opaque. Clients must not parse, construct or infer the internal keyset tuple from it.

## C-REL-05 RATIFIED — Object-scoped internal keyset boundary is `(name, to_object_id)`

Within one Object-scoped collection, the route fixes:

```text
from_object_id = object_id
```

and the ratified global runtime semantic-cell uniqueness authority is:

```text
(from_object_id, name, to_object_id)
```

Therefore the minimal stable row identity remaining inside one fixed Object scope is:

```text
(name, to_object_id)
```

RATIFIED internal keyset/order tuple:

```text
name
to_object_id
```

Conceptually, without a `name` filter:

```text
WHERE from_object_id = :object_id
ORDER BY name, to_object_id
```

and with an exact `name` filter:

```text
WHERE from_object_id = :object_id
  AND name = :name
ORDER BY to_object_id
```

No `relationship_id` tie-breaker is required. Two current factual Relationships cannot both own the same exact Object-relative semantic cell:

```text
(object_id, same_name, same_to_object_id)
```

because the global semantic-cell uniqueness rule forbids it.

The following values are **not** part of the keyset boundary:

```text
object_id
    -> cursor scope binding fixed by the route

relationship_definition_id
name filter state
    -> cursor scope/filter binding

relationship_id
    -> factual owner identity, unnecessary as a row tie-breaker under semantic-cell uniqueness

relationship_definition_version
properties
Object.canonical_name
    -> mutable/current factual or display state, not stable row identity
```

The internal tuple remains opaque and has no public/domain ordering meaning. Clients must not infer or rely on `(name, to_object_id)` from the cursor representation.

This supersedes the pre-freeze Resolution-derived tie-breaker/keyset assumptions.

## C-REL-06 RATIFIED — no separate Object-rooted page index is required when semantic uniqueness uses the same B-tree tuple

The Object-scoped collection requires an access path beginning with the route-fixed runtime source Object and continuing in the ratified keyset order:

```text
from_object_id
name
to_object_id
```

The already-ratified global semantic-cell uniqueness authority is the same logical tuple:

```text
(from_object_id, name, to_object_id)
```

Therefore, **if** the physical semantic-uniqueness mechanism is realized by a PostgreSQL B-tree index over that tuple, the same index is sufficient for the Object-rooted navigation access pattern and no second dedicated page index is required merely for:

```text
WHERE from_object_id = :object_id
ORDER BY name, to_object_id
```

or:

```text
WHERE from_object_id = :object_id
  AND name = :name
ORDER BY to_object_id
```

This checkpoint deliberately does **not** choose whether semantic uniqueness is physically represented as:

```text
PRIMARY KEY
UNIQUE constraint
explicit unique index
```

That exact DDL form remains OPEN. The ratified point is index sufficiency conditional on the chosen uniqueness realization providing the same B-tree ordering.

Accordingly, M4 does not require recreating a separate successor of the pre-freeze:

```text
ix_runtime_resolutions_from_object_page
```

solely to serve the Object-scoped GET. A second Object-rooted index would require independent measured workload evidence or a physical requirement not already satisfied by the semantic-uniqueness B-tree.

Whether `relationship_id` should be added as an `INCLUDE` payload to that index is a separate optimization question and is not ratified by this checkpoint.

Current next micro-point:

```text
GET /api/v1/core/objects/{object_id}/relationships
    -> assess whether INCLUDE (relationship_id) is justified on the semantic-uniqueness B-tree
```
