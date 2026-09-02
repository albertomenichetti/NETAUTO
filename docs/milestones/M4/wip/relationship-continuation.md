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
    to_object_id: UUID                  required
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

## C-REL-12 RATIFIED — CREATE preserves optional exact RelationshipDefinitionVersion selection

The factual Relationship CREATE keeps the pre-freeze `relationship_definition_version` request semantics unchanged.

Public field:

```text
relationship_definition_version: positive integer, optional
```

with:

```text
omitted
    -> select the current default_version of the owning RelationshipDefinition

present
    -> select exactly the supplied positive RelationshipDefinitionVersion

explicit null
    -> invalid request

zero / negative / malformed value
    -> invalid request
```

The selected version governs the factual Relationship property-schema binding only. It does not select the semantic perspective, alter endpoint orientation, or replace the required stable semantic `name`.

These semantics apply identically to both still-open Definition-selection candidates:

```text
CANDIDATE A
    owning Definition supplied explicitly
    -> omitted version resolves that Definition's current default_version

CANDIDATE B
    owning Definition derived from the exact semantic cell
    -> derive Definition first
    -> omitted version resolves that Definition's current default_version
```

Supplying an explicit version remains an exact-version request, not a latest/minimum/compatible-version hint. Exact existence/status/admission and related failure mapping remain separate CREATE review points.

## C-REL-13 RATIFIED — CREATE preserves optional `properties` omission semantics

The factual Relationship CREATE keeps the pre-freeze `properties` request semantics unchanged.

Public field:

```text
properties: object, optional
```

with:

```text
omitted
    -> equivalent to an empty factual property candidate {}

present
    -> use the supplied object as the complete candidate factual property map

explicit null
    -> invalid request

non-object value
    -> invalid request
```

The candidate property map is semantically validated and canonicalized against the exact RelationshipDefinitionVersion selected for the new factual Relationship. `properties` does not participate in semantic perspective selection, Definition ownership selection, or endpoint compatibility.

These semantics apply identically to both still-open Definition-selection candidates. Unknown/invalid property names and invalid values remain semantic-validation concerns against the selected exact RelationshipDefinitionVersion; the strict-body/unknown top-level field rules and full failure taxonomy remain separate CREATE review points.

## C-REL-14 RATIFIED — CREATE keeps strict body rules and directional endpoint command semantics

The factual Relationship CREATE keeps explicit directional endpoint fields:

```text
from_object_id: UUID, required
to_object_id: UUID, required
```

Together with the already-ratified required semantic `name`, the command is interpreted as the requested concrete observation:

```text
from_object_id --name--> to_object_id
```

`from_object_id` and `to_object_id` therefore express only the orientation of the CREATE command relative to the supplied stable semantic `name`. They do **not** create or preserve an autonomous factual A/B endpoint identity, do not encode the RelationshipDefinition authoring-side A/B slots, and do not imply that the factual Relationship root stores a distinguished creation direction after admission.

The server uses that oriented command input to validate/admit the selected semantic perspective and materialize the complete factual runtime closure. Once created, the factual Relationship is represented by its root plus all owned `runtime_relationship_cells`; the creation-side `from`/`to` presentation is not retained as separate factual identity state.

RATIFIED structural request rules common to both still-open Definition-selection candidates are:

```text
name
    required string
    explicit null invalid

from_object_id
    required UUID
    explicit null invalid

to_object_id
    required UUID
    explicit null invalid

relationship_definition_version
    optional positive integer
    explicit null invalid when present

properties
    optional object
    explicit null invalid when present

unknown top-level fields
    invalid request
```

The final allowed top-level field set depends on the Definition-selection candidate chosen at architecture closing:

```text
CANDIDATE A
    relationship_definition_id is also required UUID
    explicit null invalid

CANDIDATE B
    relationship_definition_id is not part of the request shape
    and would therefore be an unknown top-level field
```

This strict-body rule does not decide deeper semantic failures such as nonexistent Objects, semantic-cell incompatibility, Definition/version admission, property validation, or runtime semantic-cell ownership conflicts; those remain part of the CREATE failure-taxonomy review.

## C-REL-15 RATIFIED — CREATE success acknowledgement remains unchanged

The factual Relationship CREATE keeps the pre-freeze success acknowledgement unchanged and independent from the still-deferred Definition-selection request shape.

Successful creation returns:

```text
201 Created
Location: /api/v1/core/relationships/{new_relationship_id}
```

with:

```text
success body: none
```

The factual `relationship_id` remains server-generated lifetime identity. `Location` is the canonical acknowledgement carrier for the newly created resource identity; the response does not duplicate that identity in a body.

CREATE does not return the global Relationship detail representation. A caller that needs the canonical current factual representation follows the `Location` and uses:

```text
GET /api/v1/core/relationships/{relationship_id}
```

This keeps mutation acknowledgement decoupled from global GET representation richness and applies identically whether architecture closing selects Candidate A or Candidate B for Definition selection.

## C-REL-16 RATIFIED — CREATE failure boundary keeps static 400, no normal 404, and 422 for absent referenced operands

The factual Relationship CREATE keeps the project-wide failure-class boundary between structural invalidity, absent command operands and semantic candidate invalidity.

Because:

```text
POST /api/v1/core/relationships
```

has no existing resource identity selected by its URI/path, CREATE has **no normal `404 resource_not_found` case**. `404 resource_not_found` remains reserved for an absent resource identity selected by the request path.

RATIFIED first failure layer:

```text
400 invalid_request
    malformed JSON / wrong body carrier
    missing required public fields
    malformed UUID/string/positive-integer carrier
    explicit null where forbidden
    unknown top-level fields
    any query parameter
    other static request invalidity decidable without persisted-state interpretation
```

RATIFIED absent explicit command-operand layer:

```text
422 referenced_resource_not_found
    from_object_id does not identify a current Object
    to_object_id does not identify a current Object

    Candidate A only:
        supplied relationship_definition_id does not identify a RelationshipDefinition

    either candidate, when relationship_definition_version is explicitly supplied:
        the exact selected RelationshipDefinitionVersion does not exist
```

The Definition-selection candidates differ when the caller does **not** explicitly reference a Definition.

For Candidate B, if both Objects exist but the exact template-level semantic cell implied by:

```text
(from_object_id, name, to_object_id)
```

has no owning RelationshipDefinition, this is **not** `referenced_resource_not_found`: the client did not reference a missing Definition identity. It is instead semantic inadmissibility of the requested fact:

```text
422 semantic_validation_failed
    requested concrete semantic observation is not expressible by the current model
```

Likewise, under Candidate A, an existing supplied Definition whose stable semantic contract does not admit the oriented `(from_object_id, name, to_object_id)` observation is a semantic-validation failure rather than a not-found result.

RATIFIED public precedence boundary at this stage is:

```text
1. static transport/request validation
    -> 400 invalid_request

2. existence of explicit referenced command operands needed to interpret the request
    -> 422 referenced_resource_not_found

3. semantic admission of the requested fact
    -> 422 semantic_validation_failed
       OR a later-ratified current-state 409 conflict
```

This checkpoint deliberately does **not** yet close the individual `409` cases or their finer precedence. In particular, default-version availability, exact-version lifecycle admission and current runtime semantic-cell ownership conflict remain the next CREATE failure micro-points.

## C-REL-17 RATIFIED — CREATE preserves `default_version_unavailable` for omitted version selection

The factual Relationship CREATE preserves the existing implicit-version state-conflict semantics.

When:

```text
relationship_definition_version is omitted
+
the owning RelationshipDefinition has been resolved
+
that Definition currently has no default_version
```

the command fails with:

```text
409 Conflict
code: default_version_unavailable
```

This is a current-state conflict rather than semantic invalidity. The caller has requested a valid implicit-version operation, but the current RelationshipDefinition state does not provide the default exact version needed to complete that request. The same semantic intent may become admissible after the Definition acquires a default version.

The rule applies identically to both still-open Definition-selection candidates:

```text
CANDIDATE A
    resolve the explicitly supplied RelationshipDefinition
    -> omitted version requires that Definition's current default_version

CANDIDATE B
    derive the owning RelationshipDefinition from the requested semantic cell
    -> omitted version requires that derived Definition's current default_version
```

`default_version_unavailable` is impossible when `relationship_definition_version` is explicitly supplied. In that case CREATE performs exact-version selection and never consults default availability as part of the public command semantics.

RATIFIED local precedence is:

```text
static request invalidity
    -> 400 invalid_request

absent explicit command operands needed to interpret the request
    -> 422 referenced_resource_not_found

requested oriented semantic observation not admitted by the owning Definition/model
    -> 422 semantic_validation_failed

owning Definition resolved + version omitted + no current default_version
    -> 409 default_version_unavailable

selected exact RelationshipDefinitionVersion admission
    -> later checkpoint

property candidate validation / runtime factual conflict
    -> later checkpoints
```

This checkpoint does not yet decide `dependency_not_admissible` or `relationship_fact_conflict`.

## C-REL-18 RATIFIED — CREATE admits only an exact PUBLISHED RelationshipDefinitionVersion

Factual Relationship CREATE is a new model binding and therefore follows the same admission rule already used by Object CREATE and the other versioned model-resource bindings:

```text
selected exact RelationshipDefinitionVersion must currently be PUBLISHED
```

The exact selected version may originate from either request mode:

```text
explicit selection
    relationship_definition_version supplied

implicit selection
    relationship_definition_version omitted
    -> owning RelationshipDefinition.default_version
```

For an **explicit** exact version selector:

```text
exact RDV absent
    -> 422 referenced_resource_not_found

exact RDV exists but status != PUBLISHED
    -> 409 dependency_not_admissible

exact RDV exists and status == PUBLISHED
    -> version lifecycle admission succeeds
```

`DRAFT` and `DEPRECATED` are therefore not valid targets for a newly created factual Relationship binding.

For an **implicit/default** selector, M4 carries forward the versioned model-resource invariant that a non-null current `default_version` points to an exact current `PUBLISHED` version. Consequently:

```text
default_version is null
    -> 409 default_version_unavailable

default_version is non-null
    -> selected exact default target is expected to exist and be PUBLISHED
```

If persisted state instead contains:

```text
non-null default_version -> missing exact RDV
OR
non-null default_version -> exact RDV whose status != PUBLISHED
```

that is an invariant/integrity failure and maps to:

```text
500 internal_error
```

rather than exposing `dependency_not_admissible` for an implicit selector. The client did not explicitly request an inadmissible exact version; the model-plane default pointer itself is corrupt/incoherent.

This is consistent with the existing model lifecycle: publication may establish a default when none exists, and the current default version cannot be deprecated while it remains the default.

The rule applies identically after the owning Definition has been resolved under Candidate A or Candidate B.

RATIFIED local ordering remains:

```text
static request invalidity
    -> 400 invalid_request

absent explicit operands
    -> 422 referenced_resource_not_found

semantic perspective / endpoint admission
    -> 422 semantic_validation_failed

implicit version requested but no default
    -> 409 default_version_unavailable

explicit exact RDV exists but is not PUBLISHED
    -> 409 dependency_not_admissible

implicit default target violates model-plane default invariants
    -> 500 internal_error

property candidate validation / runtime factual ownership conflict
    -> later checkpoints
```

## C-REL-19 RATIFIED — CREATE validates and canonicalizes the complete property candidate before factual conflict arbitration

After the owning RelationshipDefinition has been resolved and the selected exact RelationshipDefinitionVersion has passed current lifecycle admission, CREATE validates the complete initial `properties` candidate against that exact version before evaluating current factual semantic-cell ownership conflicts.

The already-ratified omission rule remains:

```text
properties omitted
    -> candidate {}
```

The candidate is validated and canonicalized against the exact selected RelationshipDefinitionVersion semantic schema. Caller-attributable property failures map to:

```text
422 semantic_validation_failed
```

including, where applicable:

```text
property name not declared by the exact RDV
null runtime value
wrong SCALAR/LIST value shape
primitive validation or canonicalization failure
exact DataTypeVersion constraint violation
```

The factual Relationship property schema currently has no required-property dimension, so CREATE does not introduce an Object-style "missing required property" rule solely for Relationship.

A PUBLISHED RelationshipDefinitionVersion is already a certified model-plane artifact. Therefore a missing/corrupt exact DataType dependency, malformed persisted constraint set, invalid persisted RDV property declaration, or other contradiction of certification invariants discovered while resolving its runtime property semantics is not caller semantic validation. It maps to:

```text
500 internal_error
```

RATIFIED ordering is:

```text
exact RDV selected and admitted
    -> resolve exact immutable property semantics
    -> validate/canonicalize complete initial properties candidate
    -> only then evaluate current runtime semantic-cell ownership / factual conflict
```

Thus an invalid property candidate is rejected as `422 semantic_validation_failed` even if the requested semantic cells would also collide with an existing factual Relationship. CREATE does not perform factual-conflict arbitration first merely to return a different failure for a candidate that is not itself semantically valid.

## C-REL-20 RATIFIED — CREATE uses an immutable exact-RDV semantic cache after PostgreSQL admission

The exact RelationshipDefinitionVersion semantic payload used for factual property validation is a cache candidate with the same architectural boundary intended for exact ObjectTemplate schema semantics.

RATIFIED direction:

```text
ImmutableRelationshipDefinitionVersionCache[
    (relationship_definition_id, relationship_definition_version)
]
```

Conceptual cached payload includes only immutable exact-version semantics needed by the data plane, for example:

```text
ordered Relationship property declarations
exact DataTypeVersion pins
value modes
canonical/compiled RuntimePropertySpec equivalents
compiled primitive/DataType validators where useful
```

The cache must **not** own mutable current admission state such as:

```text
RelationshipDefinition.default_version
RelationshipDefinitionVersion.status
```

CREATE therefore keeps the authority split:

```text
PostgreSQL
    -> resolve current owning Definition/default when needed
    -> prove exact RDV existence
    -> prove current exact RDV status == PUBLISHED for a new binding

immutable exact-RDV cache
    -> supply already-resolved immutable schema semantics
    -> validate/canonicalize the candidate properties efficiently
```

Cache presence never proves that the exact RDV still exists or is currently admissible for CREATE. A lifecycle transition from PUBLISHED to DEPRECATED changes current admission but does not change the already-certified exact semantic payload; the cache entry can remain semantically valid while PostgreSQL rejects that version for a new binding.

A cache miss may load/resolve the immutable exact-version semantic payload from authoritative persisted model state and populate the cache. If that load discovers persisted state contradicting PUBLISHED-version certification invariants, the outcome is `500 internal_error`, not a caller error.

This checkpoint promotes the earlier M4 exact-RDV cache candidate into the factual CREATE technical direction. Exact cache implementation, process topology, warm-up policy, capacity/eviction and shared-vs-local realization remain architecture-closing/implementation details.

## C-REL-21 RATIFIED — CREATE conflicts on any already-owned candidate runtime semantic cell

After Definition/perspective admission, exact RelationshipDefinitionVersion lifecycle admission and complete initial property validation/canonicalization have succeeded, CREATE derives the complete deterministic candidate factual runtime semantic closure:

```text
candidate_runtime_closure = set of exact Object-level semantic cells

(from_object_id, name, to_object_id)
```

The already-ratified global factual uniqueness authority applies directly to every candidate cell:

```text
one exact Object-level semantic cell
    -> at most one current factual Relationship owner globally
```

RATIFIED conflict rule:

```text
if ANY cell in candidate_runtime_closure
is already owned by a current factual Relationship
    -> 409 Conflict
    -> code: relationship_fact_conflict
    -> no factual mutation
    -> no lifecycle event
```

This is true regardless of how much of the candidate closure overlaps current factual state. In particular:

```text
all candidate cells are already owned by one current Relationship
    -> relationship_fact_conflict

only one/subset of candidate cells is already owned
    -> relationship_fact_conflict

candidate cells are already owned across more than one current Relationship
    -> relationship_fact_conflict
```

CREATE therefore has **no factual convergence/idempotent-create success path**. Attempting to recreate exactly the same currently represented fact still returns `409 relationship_fact_conflict`; it does not return the existing Relationship and does not reinterpret the request as success.

The exact RelationshipDefinitionVersion pin and the candidate `properties` map do not participate in factual uniqueness and cannot create a parallel fact once any required semantic cell is already owned. They are state of the factual root after admission, not a dimension of runtime semantic-cell identity.

This rule applies identically whether architecture closing selects Candidate A or Candidate B for Definition ownership selection. Once the owning Definition and complete deterministic closure are known, factual arbitration is purely data-plane over `runtime_relationship_cells`.

This checkpoint deliberately does **not** yet ratify:

```text
exact bounded public details for relationship_fact_conflict
which conflicting owner id(s) are exposed when multiple cells/owners collide
physical pre-check vs unique-index-first arbitration
race/retry/transaction rendezvous mechanics
```

Those remain separate public-detail and technical/concurrency micro-points.

Current next micro-point:

```text
POST /api/v1/core/relationships
    -> define bounded public details for 409 relationship_fact_conflict
       without adding diagnostic-only backend work
```

## C-REL-22 RATIFIED / REVALIDATE AT ARCHITECTURE CLOSING — `relationship_fact_conflict` may expose one current owner without diagnostic-only reads

The current M4 target for factual Relationship CREATE conflict details is:

```text
409 Conflict
code: relationship_fact_conflict
details:
    relationship_id: UUID
```

`details.relationship_id` identifies **one current factual Relationship** that owns at least one exact Object-level semantic cell in the candidate runtime closure. It does not promise to enumerate every conflicting owner when several candidate cells collide with more than one current Relationship.

The governing constraint is:

```text
NO PostgreSQL statement
NO cache/model lookup
NO aggregate recertification
```

may be introduced **solely** to enrich the public conflict details.

The owner id may be exposed only when it falls out of the legal semantic arbitration/classification path already required to determine that a current conflict really exists.

The ratified runtime semantic-cell access path already supports this direction:

```text
(from_object_id, name, to_object_id)
INCLUDE (relationship_id)
```

so a set-based current-owner lookup over the candidate semantic cells can return the owning `relationship_id` directly from the data-plane conflict authority without joining the factual root or re-reading model-plane semantics.

For a collision first discovered by the PostgreSQL uniqueness authority, a fresh post-rollback current-owner classification is not considered diagnostic-only work when it is required to distinguish:

```text
current owner still exists
    -> real current-state 409 relationship_fact_conflict

colliding winner already disappeared
    -> no stale conflict response
    -> bounded retry/restart may be required
```

If that required classification naturally yields a current owner id, the same id may populate `details.relationship_id` with no additional diagnostic read.

M4 deliberately does not expose richer conflict diagnostics such as:

```text
relationship_ids[]
conflicting_cells[]
conflict_count
from_object_id/name/to_object_id diagnostic payloads
```

unless a future caller requirement independently justifies them.

**Mandatory architecture-closing revalidation:** this public detail is not allowed to force the final physical CREATE path. During architecture closing, after the exact pre-check/unique-index/race-classification strategy is chosen, `details.relationship_id` must be revalidated against the final efficient legal path. If the final realization cannot obtain a current owner id without an otherwise unnecessary diagnostic-only query, the public detail must be reduced/revised rather than adding that query merely to preserve this M4 candidate shape.

Exact owner-selection determinism when multiple owners collide, exact race/retry mechanics and the final physical arbitration strategy remain OPEN until that architecture/concurrency closing pass.

## C-REL-23 RATIFIED — after exact semantic-cell admission, factual runtime closure derives without another ancestry walk

Factual Relationship CREATE separates model-plane polymorphic admission from data-plane factual closure materialization.

The caller expresses one oriented concrete observation:

```text
from_object_id --name--> to_object_id
```

with exact endpoint ObjectTemplates:

```text
from_template_id = template(from_object_id)
to_template_id   = template(to_object_id)
```

Model-plane admission first proves that the exact template-level semantic cell:

```text
(from_template_id, name, to_template_id)
```

is currently expressible and identifies its unique owning RelationshipDefinition under the ratified global semantic-cell ownership invariant. `relationship_definition_space` is the model-plane closure that may serve this exact admission/owner-resolution role.

Once that exact semantic cell has been admitted, factual closure derivation does **not** perform another ObjectTemplate ancestry walk and does not enumerate every model-plane cell of the Definition that happens to be compatible with the two concrete endpoint templates.

Instead, the complete factual runtime closure derives only from:

```text
the admitted oriented concrete observation
+
the compact stable semantic contract of the owning RelationshipDefinition
```

RATIFIED closure rules are:

```text
ASYMMETRIC
    input:
        O1 --name1--> O2

    closure:
        O1 --name1--> O2
        O2 --name2--> O1

    where name2 is the distinct stable reciprocal name
    of the same owning RelationshipDefinition
```

The rule also holds when asymmetric endpoint compatibility spaces overlap or are identical. Concrete endpoint-template compatibility with both semantic perspectives does not cause additional runtime cells to be generated.

```text
SYMMETRIC, DISJOINT ENDPOINT SPACES
    input:
        O1 --name--> O2

    closure:
        O1 --name--> O2
        O2 --name--> O1
```

```text
SYMMETRIC, SAME ENDPOINT SPACE, O1 != O2
    closure:
        O1 --name--> O2
        O2 --name--> O1
```

```text
SYMMETRIC, SAME ENDPOINT SPACE, O1 == O2
    closure:
        O1 --name--> O1

    exactly one cell
```

The self-loop contains one row because reciprocal materialization would produce the exact same Object-level semantic cell.

Therefore the complete runtime-closure cardinality is bounded by the stable Definition topology:

```text
asymmetric
    -> exactly 2 cells

symmetric disjoint-space
    -> exactly 2 cells

symmetric same-space with distinct Objects
    -> exactly 2 cells

symmetric same-space self-loop
    -> exactly 1 cell
```

The critical overlap example remains:

```text
Manager  --manages----> Employee
Employee --managed_by-> Manager
```

with `M1` and `M2` both Manager Objects. A CREATE command:

```text
M1 --manages--> M2
```

materializes only:

```text
M1 manages M2
M2 managed_by M1
```

It does not additionally materialize every other semantic perspective that the same exact endpoint templates could independently satisfy.

RATIFIED responsibility split is:

```text
relationship_definition_space
    -> certify/admit the exact template-level semantic cell
    -> identify the unique owning RelationshipDefinition

compact RelationshipDefinition
    -> determine the reciprocal stable semantic perspective/name

runtime_relationship_cells
    -> materialize only the concrete Object-level semantic cells
       of this single admitted factual Relationship
```

This supersedes the old `derive_runtime_closure()` dependency on autonomous `selected_resolution_id` plus repeated ObjectTemplate ancestry walking. Exact admission SQL/cache realization remains architecture work; the semantic rule is that ancestry is an admission concern and is not repeated merely to expand a factual closure whose reciprocal semantics are already fixed by the owning compact Definition.

## C-REL-24 RATIFIED — CREATE persists factual root and complete runtime closure atomically

The factual Relationship remains one transactional aggregate whose authoritative current state is split between:

```text
relationships
    id
    relationship_definition_id
    relationship_definition_version
    properties

+

runtime_relationship_cells
    complete deterministic runtime semantic closure
```

A successful CREATE may become visible only as the complete aggregate.

RATIFIED persistence boundary:

```text
one factual Relationship CREATE
    -> one PostgreSQL transaction
    -> persist the factual root
    -> persist every runtime semantic cell in the complete derived closure
    -> commit only when the complete aggregate is valid and persisted
```

The write is strictly all-or-nothing:

```text
SUCCESS
    factual root persisted
    +
    every required runtime_relationship_cells row persisted
    -> COMMIT

ANY FAILURE
    root persistence failure
    OR
    any runtime-cell persistence failure
    OR
    runtime semantic-cell uniqueness conflict
    OR
    any other integrity failure before commit
    -> ROLLBACK the complete CREATE attempt
```

Therefore no committed state may contain:

```text
Relationship root without its runtime closure
partial runtime closure
runtime cell without its owning Relationship root
only one cell of an otherwise two-cell factual closure
```

Example:

```text
candidate closure:
    O1 --runs_on--> O2
    O2 --hosts----> O1
```

If persistence of the reciprocal cell collides after earlier writes in the same attempt:

```text
insert factual root
insert O1 --runs_on--> O2
insert O2 --hosts----> O1
    -> semantic-cell uniqueness conflict
```

then the result is:

```text
rollback factual root
rollback first runtime cell
no partial factual Relationship remains
-> public conflict handling follows the already-ratified relationship_fact_conflict boundary
```

This checkpoint deliberately does **not** choose the physical DML/arbitration order. The following remain architecture/concurrency-closing decisions:

```text
root-first vs another legal physical order
pre-check vs unique-index-first arbitration
single statement / CTE vs multiple statements in one transaction
bulk/batch INSERT realization
savepoint use
exact race/retry/rendezvous mechanics
```

The semantic requirement is only that the final legal realization preserves the same atomic aggregate boundary.

The CREATED lifecycle event belongs to the same successful mutation transaction in the existing architecture, but exact event payload/construction is kept outside this checkpoint and remains a separate lifecycle-detail question.

## C-REL-25 RATIFIED — CREATE lifecycle fan-out is one-to-one with runtime semantic cells

A successful factual Relationship CREATE persists its complete `RELATIONSHIP_CREATED` lifecycle event set in the same PostgreSQL transaction as the factual root and complete runtime semantic closure.

RATIFIED atomic boundary:

```text
successful CREATE transaction
    factual root
    + complete runtime_relationship_cells closure
    + complete RELATIONSHIP_CREATED event set
    -> one atomic COMMIT
```

Therefore any rollback of the CREATE attempt, including `relationship_fact_conflict`, leaves:

```text
no factual Relationship root
no runtime semantic cells
no RELATIONSHIP_CREATED event rows
```

The Relationship lifecycle transition semantics remain:

```text
RELATIONSHIP_CREATED
    before_state = null
    after_state = {
        relationship_definition_version,
        properties
    }
```

The factual snapshot remains self-contained historical state and does not require `resolution_id` or another model-plane perspective identity.

Each persisted runtime semantic cell already is one exact Object-relative semantic view:

```text
runtime_relationship_cells
    relationship_id
    from_object_id
    name
    to_object_id
```

so CREATE lifecycle fan-out is directly:

```text
one runtime_relationship_cells row
    -> one RELATIONSHIP_CREATED event item
```

with semantic projection:

```text
relationship_id
    -> factual Relationship lifetime identity

relationship_definition_id
    -> owning factual Definition binding

object_id
    -> runtime cell from_object_id

relationship_name
    -> runtime cell stable semantic name

destination_object_id
    -> runtime cell to_object_id

canonical_name / destination_canonical_name
    -> coherent Object display observations captured for the event

before_state
    -> null

after_state
    -> exact factual version/property snapshot
```

There is no `resolution_id` in the lifecycle event contract.

Because `runtime_relationship_cells` already stores semantic cells rather than lower-level normalization rows, the old semantic-view deduplication stage is no longer required for CREATE lifecycle fan-out. Runtime persistence normalization must not introduce additional event rows beyond the actual semantic-cell closure.

RATIFIED event-set cardinality therefore matches the factual closure exactly:

```text
asymmetric
    -> 2 RELATIONSHIP_CREATED event rows

symmetric disjoint-space
    -> 2 rows

symmetric same-space with distinct Objects
    -> 2 rows

symmetric same-space self-loop
    -> 1 row
```

The exact physical mechanism used to capture coherent current `canonical_name` values, build the event batch and order the INSERT work remains architecture-closing implementation design. This checkpoint freezes only the lifecycle semantic shape, the 1:1 fan-out with runtime semantic cells and the shared atomic transaction boundary.

Current next micro-point:

```text
POST /api/v1/core/relationships
    -> assess post-definition CREATE review closure
       and enumerate only the decisions intentionally deferred to architecture closing
```

## C-REL-26 RATIFIED — post-definition factual CREATE discovery is complete; architecture closing remains pending

The factual/domain discovery pass for:

```text
POST /api/v1/core/relationships
```

is complete after revalidation against the compact post-`RelationshipResolution` model and the `runtime_relationship_cells` data-plane representation.

Current status is explicitly:

```text
DISCOVERY COMPLETE
ARCHITECTURE CLOSING PENDING
PUBLIC CONTRACT NOT YET CLOSED
```

The public contract is not yet CLOSED because architecture closing must choose exactly one of the two still-open Definition-selection request shapes:

```text
CANDIDATE A
    explicit relationship_definition_id

CANDIDATE B
    derive the owning Definition from the admitted exact semantic cell
```

All remaining CREATE work is intentionally architectural/physical rather than a missing factual-domain rule. Architecture closing must resolve only the deferred points already identified by this discovery pass:

```text
1. choose Candidate A vs Candidate B as the single final public request contract
2. finalize the exact semantic-cell admission / owning-Definition access path
3. finalize the immutable exact-RDV cache realization
4. choose the physical relational carrier of runtime semantic-cell uniqueness
5. choose the legal conflict-arbitration and DML strategy
   including pre-check vs unique-index-first and physical write ordering
6. close concurrency behavior:
   rollback, race rendezvous, current-owner reclassification and bounded retry/restart
7. revalidate C-REL-22 details.relationship_id against that final efficient path;
   do not add diagnostic-only work merely to preserve the detail
8. finalize coherent lifecycle canonical_name projection and event batch/write realization
```

Those decisions must preserve all already-ratified factual semantics, including:

```text
required oriented name/from/to command semantics
exact-version/default selection semantics
PUBLISHED-only new binding admission
immutable exact-RDV property validation semantics
complete deterministic 1-or-2-cell runtime closure
one exact Object-level semantic cell -> at most one current factual owner
409 relationship_fact_conflict with no CREATE convergence
root + complete closure + complete CREATED event set atomically committed
```

No additional factual CREATE capability or semantic decision is currently known to be missing.

This checkpoint is a review-status closure only. It does not authorize implementation and does not pre-decide any of the architecture-closing choices above.

## C-REL-27 RATIFIED — `relationships.revision` is the universal factual-root generation token

M4 aligns factual Relationship intrinsic mutation freshness with the already-ratified Object intrinsic-generation direction by introducing one technical generation token on the factual Relationship root:

```text
relationships
    id
    relationship_definition_id
    relationship_definition_version
    properties
    revision
```

`revision` identifies the committed generation of the mutable factual Relationship root.

Canonical interpretation is:

```text
Relationship.revision
    = universal technical factual-root generation token

Relationship.revision
    != RelationshipDefinitionVersion.version
    != RelationshipDefinitionVersion.revision
    != lifecycle event sequence
    != runtime semantic-cell identity
    != public Relationship identity
```

The generation token is internal technical concurrency/persistence state. Existing public Relationship request/response DTOs do not expose it and mutation routes do not accept a caller-supplied `expected_revision` merely because the persistence root carries one.

CREATE materializes the first factual-root generation explicitly:

```text
new Relationship
    -> revision = 1
```

This is persistence alignment only and does not reopen the already-completed factual CREATE discovery/public semantics.

Every Relationship mutation whose candidate is derived from a previously observed factual root generation carries the observed revision internally as:

```text
expected_revision = R
```

A real factual-root mutation may commit only if that same generation is still current:

```text
current revision == R
    -> operation may commit if its own semantic admissions succeed

current revision != R
    -> stale internal attempt
    -> no factual-root mutation from that attempt
    -> no lifecycle transition from that attempt
    -> bounded retry from a fresh factual-root generation
```

Every committed mutation that writes a new `relationships` root generation increments revision atomically with that root mutation:

```text
new_revision = R + 1
```

Current cross-operation alignment is:

```text
CREATE
    -> revision = 1

DATA_CHANGE real persisted mutation
    -> properties change
    -> revision R -> R + 1
    -> DATA_CHANGE lifecycle transition in the same successful commit

DATA_CHANGE cheap semantic no-op elided
    -> no root UPDATE
    -> no lifecycle event
    -> revision remains R

SCHEMA_CHANGE distinct target with real persisted migration
    -> relationship_definition_version and properties change atomically
    -> revision R -> R + 1
    -> SCHEMA_CHANGE lifecycle transition in the same successful commit

SCHEMA_CHANGE target already current
    -> semantic no-op
    -> no root UPDATE
    -> no lifecycle event
    -> revision remains R

DELETE
    -> removes the current factual-root generation
    -> no surviving row exists on which to persist R + 1
```

The revision is intentionally one conservative generation token for all mutable factual-root state. In particular, a DATA_CHANGE prepared from:

```text
relationship_definition_version = V
properties = P
revision = R
```

cannot commit that prepared candidate after a concurrent SCHEMA_CHANGE has advanced the same factual root to another generation. A revision mismatch triggers a fresh attempt, which re-observes the current exact pin and validates the requested DATA_CHANGE against the schema semantics of that current generation.

Likewise, a SCHEMA_CHANGE candidate prepared from one exact pin/property generation cannot overwrite a concurrent DATA_CHANGE generation without first becoming stale and being retried.

The token deliberately covers only state physically owned by `relationships`:

```text
relationship_definition_version
properties
```

`relationship_definition_id` is the stable Definition binding for the factual lifetime and is not reassigned by M4 factual mutations, but it remains part of the same root row.

The revision does **not** turn `runtime_relationship_cells` into mutable revisioned state. The already-ratified runtime semantic closure is created atomically with the fact, remains stable across DATA_CHANGE and SCHEMA_CHANGE, and is removed with DELETE. Therefore:

```text
Relationship.revision does not represent
    runtime closure generation
    endpoint Object generation
    RelationshipDefinition lifecycle
    RelationshipDefinitionVersion lifecycle
    model-plane semantic-cell ownership
```

Operation-specific admission remains separate. Revision freshness proves only that the observed factual-root generation has not been replaced by another committed factual-root mutation; it does not prove target RDV PUBLISHED admission for SCHEMA_CHANGE, property semantic validity, or any model/data fact outside the `relationships` row.

Revision mismatch is internal concurrency control, not a normal public business conflict. DATA_CHANGE keeps no normal `409`; bounded retry exhaustion remains an internal stabilization failure mapped to `500 internal_error`. The corresponding SCHEMA_CHANGE concurrency treatment must preserve the same internal stale-attempt principle when that action is post-definition revalidated.

Exact SQL type, CHECK/default DDL, CAS statement form, PostgreSQL row-lock/wait realization, retry count/backoff and related physical details remain architecture-closing work. The direction architecture must preserve is:

```text
first factual-root generation starts explicitly at revision 1
one revision token covers the mutable factual Relationship root
real root mutation advances revision atomically
stale expected revision cannot commit factual state or lifecycle
stale mismatch is handled by bounded internal retry
no-op elision does not advance revision
DELETE terminates the current generation without a surviving increment
revision stays private technical state unless a later public contract explicitly changes that boundary
```

Current factual review frontier remains DATA_CHANGE, with the next micro-point focused on exact pinned-schema semantic loading/caching and property validation without model-plane recertification or lifecycle-status admission.

## C-REL-28 RATIFIED — DATA_CHANGE validates against a fully resolved immutable exact-RDV semantic cache

Relationship DATA_CHANGE derives its property-validation semantics from the exact RelationshipDefinitionVersion already pinned by the current factual Relationship generation. It does not perform a new model-plane admission.

For an observed current factual root generation:

```text
relationship_definition_id = D
relationship_definition_version = V
properties = P
revision = R
```

DATA_CHANGE resolves the immutable semantic validation snapshot under:

```text
ImmutableRelationshipDefinitionVersionCache[(D, V)]
```

The cache entry is a fully resolved immutable execution snapshot, not merely the raw RDV header/declaration rows. Conceptually it contains everything needed to validate and canonicalize Relationship runtime properties without further model-plane reads, including:

```text
exact RelationshipDefinitionVersion identity (D, V)
ordered property declarations
property value modes
exact DataTypeVersion pins for every declaration
resolved primitive/base semantics
exact DataTypeVersion constraints / enum semantics where applicable
compiled RuntimePropertySpec / validator / canonicalizer equivalents where useful
```

On a cache hit:

```text
DATA_CHANGE performs no RDV/DataType model-plane read
```

On a cache miss, the loader performs one complete semantic materialization for that exact RDV:

```text
load exact RelationshipDefinitionVersion D@V
+
load the complete declaration set of D@V
+
load all exact DataTypeVersion dependencies referenced by those declarations
+
load the constraint/enum/semantic payload required by those exact DataTypeVersions
+
validate persisted immutable-schema invariants
+
build one resolved immutable semantic snapshot
+
populate cache[(D, V)]
```

The physical number/form of PostgreSQL statements used by the cache-miss loader remains architecture work; the semantic requirement is that the miss resolves the complete exact dependency set needed for runtime validation rather than causing per-property/per-value model lookups during mutation validation.

DATA_CHANGE is lifecycle-status invariant with respect to the already-pinned schema. Therefore neither cache hit nor cache miss performs admission checks such as:

```text
NO RelationshipDefinition.default_version read
NO RelationshipDefinitionVersion.status == PUBLISHED check
NO DataTypeVersion current lifecycle-status admission check
NO dependency_not_admissible outcome
```

The reason is that DATA_CHANGE does not create or rebind a model-plane dependency. `D@V` and every exact DataTypeVersion dependency reachable from its certified property schema were admitted when the factual binding became valid. Subsequent lifecycle transitions such as PUBLISHED -> DEPRECATED do not change the immutable semantic payload governing that already-existing fact.

Accordingly, a factual Relationship pinned to a now-DEPRECATED exact RDV remains property-mutable, and a cached immutable snapshot remains valid across such lifecycle-status changes.

If a cache miss discovers that an exact persisted dependency required by the already-admitted factual pin is missing, malformed or contradicts immutable publication/certification invariants, that is persisted invariant corruption rather than caller semantic invalidity or current lifecycle inadmissibility:

```text
-> 500 internal_error
```

After obtaining the resolved semantic snapshot, DATA_CHANGE applies the requested SET/REMOVE operations to the complete current property map `P`, then validates and canonicalizes the resulting candidate using that snapshot.

Caller-attributable property failures keep the already-ratified public boundary:

```text
422 semantic_validation_failed
```

including undeclared property names, SET null, wrong SCALAR/LIST shape, primitive/canonicalization failures and exact DataTypeVersion constraint violations.

For the real-write branch, the candidate belongs to factual generation `R` and therefore uses the C-REL-27 generation protocol:

```text
expected_revision = R

if current revision == R
    -> properties := canonical candidate
    -> revision := R + 1
    -> DATA_CHANGE lifecycle set
    -> atomic commit

if current revision != R
    -> stale internal attempt
    -> no mutation/event from that attempt
    -> bounded retry from a fresh factual generation
```

A fresh retry re-observes the current exact RDV pin and uses the cache entry for that exact `(D,V)` generation, loading a different exact snapshot only if a concurrent SCHEMA_CHANGE changed the factual pin.

Cheap semantic no-op elision remains unchanged:

```text
candidate properties == current canonical properties
    -> 204 No Content
    -> no factual-root UPDATE
    -> no DATA_CHANGE lifecycle event
    -> revision does not advance
```

DATA_CHANGE does not revalidate or reconstruct factual Relationship topology while doing this work. In particular:

```text
NO RelationshipDefinition semantic/topology recertification
NO relationship_definition_space read
NO ObjectTemplate ancestry read
NO runtime_relationship_cells reconstruction or semantic re-proof
```

Those facts belong to the already-admitted stable factual Relationship and are not changed by property mutation.

Current next micro-point:

```text
Relationship DATA_CHANGE
    -> revalidate lifecycle event fan-out / snapshot boundary
       against stable runtime_relationship_cells and relationships.revision
```
