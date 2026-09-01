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

## C-REL-07 RATIFIED — semantic-cell uniqueness B-tree includes `relationship_id` as non-key payload

For the physical semantic-cell uniqueness B-tree over:

```text
(from_object_id, name, to_object_id)
```

M4 ratifies carrying:

```text
INCLUDE (relationship_id)
```

as non-key payload.

Conceptual physical target:

```text
semantic-cell uniqueness B-tree
    KEY
        from_object_id
        name
        to_object_id
    INCLUDE
        relationship_id
```

`relationship_id` remains factual ownership/grouping state. It is **not** part of:

```text
semantic-cell uniqueness
Object-scoped keyset identity
Object-scoped ordering semantics
```

The purpose of the included UUID is read-path access only. The Object-scoped GET already locates/page-orders runtime cells using the semantic key, but each public item also needs the owning factual root:

```text
relationship_id
    -> relationships
    -> relationship_definition_id
    -> relationship_definition_version
    -> properties
```

Including `relationship_id` allows the runtime-side page projection to obtain the owner identifier directly from the same B-tree when PostgreSQL can use an index-only path, without widening the semantic key or requiring a separate Object-rooted page index.

M4 does **not** include factual-root or display fields such as:

```text
relationship_definition_id
relationship_definition_version
properties
Object.canonical_name
```

in this runtime index. Those values remain owned by `relationships` / `objects` and are reached through the normal joins; copying them into the runtime index would be unnecessary denormalization and/or excessive payload.

The exact semantic-uniqueness DDL carrier remains OPEN between the previously identified relational forms, subject to the requirement that the chosen realization can provide the ratified B-tree key plus `INCLUDE (relationship_id)` payload.

## C-REL-08 RATIFIED — Object-scoped GET keeps one root-preserving PostgreSQL statement

The post-definition Object-scoped collection preserves the existing parent-existence semantics without introducing a separate preliminary Object-existence query.

Ratified public boundary remains:

```text
object_id does not identify a current Object
    -> 404 Not Found
       resource_type = object

object_id identifies a current Object but the effective Relationship collection is empty
    -> 200 OK
       items = []
       next_cursor = null
```

The empty-collection case includes zero matches caused by the optional `relationship_definition_id` and/or exact `name` filters and normal keyset continuation exhaustion.

M4 ratifies retaining a **single authoritative PostgreSQL business statement** rooted at the source `objects` row and preserving that root while the paged Relationship projection is optional.

Conceptually:

```text
objects AS source_object
    LEFT JOIN LATERAL (
        runtime_relationship_cells AS c
            JOIN relationships AS r
                ON r.id = c.relationship_id
            JOIN objects AS destination_object
                ON destination_object.id = c.to_object_id

        WHERE c.from_object_id = source_object.id
          [AND c.name = :name]
          [AND r.relationship_definition_id = :relationship_definition_id]
          [AND keyset boundary over (c.name, c.to_object_id)]

        ORDER BY c.name, c.to_object_id
        LIMIT :limit_plus_one
    ) AS page
```

The exact SQL syntax/aggregation carrier may differ in implementation, but the required read boundary is:

```text
source Object root preserved
+
optional paged runtime-cell projection
+
one PostgreSQL statement snapshot
```

Operational interpretation is:

```text
no source_object root row
    -> 404 resource_not_found(object)

source_object root row exists + no page item
    -> 200 empty ObjectRelationshipPage

source_object root row exists + page item(s)
    -> normal ObjectRelationshipPage projection
```

The statement remains entirely data-plane for factual Relationship navigation:

```text
objects AS source_object
runtime_relationship_cells
relationships
objects AS destination_object
```

There is no read-time model-plane reconstruction or semantic recertification:

```text
NO relationship_definitions join required for navigation semantics
NO relationship_definition_space read
NO ObjectTemplate ancestry read
NO RDV/DataType semantic read
NO worker cache
NO explicit locks
NO generation token
NO retry loop for the normal GET
```

The page continues to use the already-ratified keyset tuple `(name, to_object_id)` and `limit + 1` style continuation detection may be used internally to derive `next_cursor`; those mechanics do not alter the public contract.

## C-REL-09 RATIFIED — Object-scoped GET post-definition revalidation is CLOSED

The Object-scoped factual Relationship collection is now **CLOSED again** for the M4 discovery pass after revalidation against the post-`RelationshipResolution` model and `runtime_relationship_cells` persistence.

Ratified public contract is:

```text
GET /api/v1/core/objects/{object_id}/relationships

path:
    object_id: UUID, required

query:
    relationship_definition_id: UUID, optional
    name: string, optional, exact match
    cursor: opaque string, optional
    limit: positive integer 1..500, optional, default 100

body: none

success:
    200 OK
    ObjectRelationshipPage
        items: array<ObjectRelationshipItem>
            relationship_id
            relationship_definition_id
            relationship_definition_version
            properties
            name
            destination_object { id, canonical_name }
        next_cursor: opaque string | null
```

Post-definition semantics are:

```text
one runtime_relationship_cells row with from_object_id = object_id
    -> exactly one public item
    -> no deduplication

name
    -> stable semantic name from runtime_relationship_cells

relationship_definition_id filter
    -> exact factual-root filter through relationships

name filter
    -> exact semantic-name filter on runtime_relationship_cells.name
    -> no prefix/substring/regex/fuzzy/case-insensitive search semantics

cursor scope
    -> collection kind
    -> object_id
    -> relationship_definition_id value or omitted state
    -> name value or omitted state
    -> NOT bound to limit

internal keyset boundary
    -> (name, to_object_id)
    -> opaque / no public ordering meaning
```

Ratified technical read target is:

```text
one root-preserving PostgreSQL statement
    objects AS source root
    -> runtime_relationship_cells
    -> relationships
    -> objects AS destination

missing source Object
    -> 404 resource_not_found(object)

existing source Object with zero effective matches
    -> 200 empty page
```

The runtime semantic-cell uniqueness B-tree is sufficient for the Object-rooted access path when realized over:

```text
(from_object_id, name, to_object_id)
INCLUDE (relationship_id)
```

so no separate Object-page index is required by the current M4 architecture. The exact relational carrier of semantic uniqueness (`PRIMARY KEY` vs `UNIQUE`/equivalent) remains a broader physical-DDL point and does not keep this GET review open.

This closure supersedes the pre-freeze Resolution-dependent assumptions concerning runtime-row deduplication, mutable Resolution names, Resolution-derived keyset tie-breakers and the old dedicated Object-page index shape.

Current factual Relationship review frontier moves to:

```text
POST /api/v1/core/relationships
    -> replace the obsolete resolution_id CREATE selector
    -> preserve the already-ratified route/success acknowledgement where unaffected
    -> derive the new selector from the compact stable RelationshipDefinition semantics
```

## C-REL-10 RATIFIED — CREATE requires the stable semantic `name`; endpoint orientation alone is insufficient

For factual Relationship CREATE, keeping explicit directional endpoint fields:

```text
from_object_id
to_object_id
```

is necessary to state how the caller is presenting the two Objects, but it is **not sufficient in the general model** to identify the intended semantic perspective.

The counterexample is an asymmetric RelationshipDefinition whose endpoint compatibility spaces are identical or inheritance-overlapping. The same ordered pair of concrete Objects may legally satisfy both reciprocal semantic perspectives.

Example:

```text
Manager --manages----> Employee
Employee --managed_by-> Manager
```

with both factual endpoints being `Manager` Objects:

```text
from_object_id = M1
to_object_id   = M2
```

can correspond to either intended observation:

```text
M1 --manages----> M2
```

or:

```text
M1 --managed_by-> M2
```

The ordered endpoint IDs alone therefore do not determine the semantic perspective.

RATIFIED CREATE requirement:

```text
name: string, required
```

The supplied `name` is the stable semantic name of the perspective the caller intends to express from `from_object_id` toward `to_object_id`. It is command semantic input, not an autonomous Resolution identity and not a mutable display label.

This requirement applies to the general CREATE contract even though some particular Definitions with disjoint endpoint spaces could infer a unique perspective from endpoint compatibility alone. The public command shape must be unambiguous for every allowed RelationshipDefinition topology and must not change depending on whether a particular Definition happens to be inferable from its endpoints.

This checkpoint does **not** yet decide whether `relationship_definition_id` must also be supplied explicitly. That is the next selector-boundary question.

Current next micro-point:

```text
POST /api/v1/core/relationships
    -> determine whether relationship_definition_id is required public input
       or can be derived unambiguously from the exact Object-template semantic cell
       selected by (from_object_id, name, to_object_id)
```

## C-REL-11 RATIFIED — CREATE keeps both Definition-selection shapes open until architecture closing

M4 does not close the `relationship_definition_id` selector boundary during the current factual CREATE review.

Two public-body candidates remain intentionally alive:

```text
CANDIDATE A — explicit Definition selector
    relationship_definition_id: UUID   required
    name: string                        required
    from_object_id: UUID               required
    to_object_id: UUID                 required
    relationship_definition_version    optional
    properties                         optional
```

and:

```text
CANDIDATE B — derived Definition owner
    name: string                        required
    from_object_id: UUID               required
    to_object_id: UUID                 required
    relationship_definition_version    optional
    properties                         optional
```

Both candidates preserve the already-ratified requirement that `name` is mandatory semantic command input. The difference is only who supplies/resolves the owning RelationshipDefinition.

Candidate A makes the owning Definition explicit in the request. This can reduce CREATE-side model-plane lookup work and makes the intended Definition binding directly available to the backend, at the cost of carrying information that is semantically redundant with the exact model-plane semantic cell when global semantic-cell ownership is unique.

Candidate B lets the caller express only the concrete semantic observation:

```text
(from_object_id, name, to_object_id)
```

The backend resolves both Objects to their exact ObjectTemplates and then resolves the corresponding exact template-level semantic cell:

```text
(from_template_id, name, to_template_id)
```

whose owning RelationshipDefinition is globally unique by the ratified model-plane invariant. This yields a cleaner semantic command shape but may add model-plane lookup/materialization work on the CREATE path.

M4 explicitly defers the final choice to **architecture closing**, where the two shapes must be compared against the finalized CREATE data path, physical access paths, cache/materialization decisions and measured/expected operational cost.

This deferral must not be interpreted as permission for two simultaneous production request shapes. Architecture closing must choose one final public contract unless new evidence independently justifies multiple variants.

The following CREATE body points remain independent of this deferred selector choice and can continue to be revalidated now:

```text
from_object_id / to_object_id directional semantics
relationship_definition_version optional exact-version/default behavior
properties optional / omission semantics
strict-body / null / unknown-field rules
success acknowledgement
failure taxonomy and precedence
```

Current next micro-point:

```text
POST /api/v1/core/relationships
    -> revalidate the remaining request-body fields that are independent
       from the deferred explicit-vs-derived Definition selector choice
```
