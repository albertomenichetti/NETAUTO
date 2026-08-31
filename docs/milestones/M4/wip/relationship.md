# M4 — Factual Relationship working owner

**Status:** ACTIVE REVIEW FRONTIER / WIP / NON-NORMATIVE

## Purpose and ownership

This is the single M4 WIP owner for the factual `Relationship` family.

All factual Relationship route discovery, review decisions, data-path findings and open questions must be maintained here instead of creating one WIP per operation or micro-point. Separate files remain appropriate only for genuinely cross-domain owners/support not owned by factual Relationship.

This WIP remains non-normative under M4 governance: ratified discovery checkpoints recorded here do not authorize implementation until milestone closure/promotion.

This owner absorbs the former distributed WIPs for CREATE, runtime closure/conflict persistence, global GET, Object-scoped Relationship navigation, DATA_CHANGE, SCHEMA_CHANGE, DELETE and Object-relative API exploration. Git history remains the historical source for superseded intermediate reasoning.

---

# 1. AS-IS public capability surface

Current factual Relationship HTTP capabilities are:

```text
POST   /relationships
GET    /relationships/{relationship_id}
POST   /relationships/{relationship_id}/data-change
POST   /relationships/{relationship_id}/schema-change
DELETE /relationships/{relationship_id}
GET    /objects/{object_id}/relationships
```

There is currently:

```text
NO generic root Relationship collection GET
NO Object-relative single-Relationship detail GET
NO endpoint-reassignment mutation
```

A factual Relationship is one global fact with lifetime identity `relationship_id`. Its persisted runtime closure can expose multiple object-relative semantic views, including reciprocal views and overlap/self-loop cases.

---

# 2. Ratified M4 functional capability checkpoints

These are ratified review decisions for the current M4 discovery pass. Exact DTOs, payload fields, filters, pagination, SQL realization and physical optimization are separate later decisions.

## REL-API-01 — specific Relationship detail is global

The specific factual Relationship is queried outside Object scope:

```text
GET /relationships/{relationship_id}
```

This answers:

```text
what is this factual Relationship globally?
```

The Relationship has its own identity; an Object used to navigate to it is context, not part of that identity. The global detail can therefore coherently expose the complete factual state and all distinct semantic views.

## REL-API-02 — Object-scoped Relationship collection is required

The Object-scoped collection is a fundamental capability:

```text
GET /objects/{object_id}/relationships
```

This answers:

```text
which factual Relationships are visible from this Object?
```

Its role is Object-context navigation/query. Exact item representation and route-detail mechanics remain deferred until the functional coverage gate is closed.

## REL-API-03 — no Object-scoped single-Relationship detail for now

Do not introduce a route conceptually equivalent to:

```text
GET /objects/{object_id}/relationships/{relationship_id}
```

unless a concrete caller need later proves that global detail plus Object-scoped collection is insufficient.

Reasons:

```text
Relationship already has global identity/detail
Object scope is navigation context, not ownership
object_id + relationship_id can be perspective-ambiguous
scoped detail would force selector/ambiguity/rename/error semantics
without a demonstrated need
```

The former candidate proposing Object-relative single-Relationship detail is superseded.

## REL-API-04 — functional coverage precedes route-detail design

The current phase is a functional capability coverage audit.

```text
absence from AS-IS != automatic rejection
candidate capability != automatic new endpoint
```

A missing capability must be justified by caller/domain need. Do not review payload weight, exact fields, SQL or performance until M4 functional coverage is explicitly closed.

## REL-API-05 — global Relationship discovery is real but deferred to M5 Search API

There is a real need to discover/query factual Relationships without already knowing a `relationship_id` or a starting Object.

That need is not rejected, but it does not justify a generic root `LIST relationships` in M4. Global Relationship discovery is materially search-oriented: useful criteria naturally span endpoints, RelationshipDefinition and factual data.

Therefore:

```text
NO M4 requirement for generic GET /relationships collection
M5 Search API owns global Relationship discovery/query
```

This is a milestone-scope decision, not a statement that the need is unnecessary.

## REL-API-06 — endpoint binding is part of factual Relationship identity

M4 does not require an identity-preserving endpoint reassignment/reversal capability.

Changing one of the participating Objects changes the fact itself. The correct composition is:

```text
DELETE old factual Relationship
+
CREATE new factual Relationship
    -> new relationship_id
```

A non-symmetric Relationship already exposes reciprocal semantic views of the same fact; reading the reciprocal perspective is not an endpoint-reversal mutation.

The same principle applies to replacing/repointing an endpoint: there is no caller requirement for the old `relationship_id` to survive.

## REL-API-07 — M4 functional capability coverage is closed

The factual Relationship functional coverage gate is ratified as complete for M4.

Required M4 capabilities are exactly:

```text
CREATE
GET global detail by relationship_id
GET Object-scoped Relationship collection
DATA_CHANGE
SCHEMA_CHANGE
DELETE
```

No additional factual Relationship capability is required by M4 at this checkpoint.

This closure is dependency-aware rather than universal: a later concrete caller need may reopen the affected capability boundary, and global Relationship discovery remains explicitly handed to M5 Search API.

---

# 3. Functional capability coverage gate — CLOSED

M4 factual Relationship covers the operational lifecycle needed by the data-plane:

```text
CREATE
    create/admit a factual Relationship

GET global detail
    retrieve one known fact by lifetime identity

GET Object-scoped collection
    discover/navigate facts from one Object

DATA_CHANGE
    mutate factual property data while preserving fact identity/binding

SCHEMA_CHANGE
    migrate the exact schema-version binding of the same fact

DELETE
    remove the fact
```

Coverage decisions are:

```text
specific detail
    -> global GET by relationship_id

Object-context discovery
    -> Object-scoped collection

Object-scoped single detail
    -> not required for now

global discovery/query
    -> real need, deferred to M5 Search API

endpoint reassignment/repointing
    -> not an identity-preserving M4 capability
    -> DELETE + CREATE
```

Adjacent needs are owned elsewhere rather than by new factual Relationship operations:

```text
historical/audit navigation
    -> Lifecycle family

Relationship name/topology mutation
    -> RelationshipDefinition family

global multi-criteria discovery
    -> M5 Search API
```

Current concrete HTTP/CLI/test surfaces do not expose evidence for another distinct factual Relationship operation beyond the ratified set.

The functional capability gate is therefore closed. The family remains an ACTIVE REVIEW FRONTIER because the exact public REST contracts and later technical realization are not yet reviewed/closed.

---

# 4. Persisted factual model and runtime closure

Current durable ownership is conceptually:

```text
relationships
    id
    relationship_definition_id
    relationship_definition_version
    properties

runtime_relationship_resolutions
    resolution_id
    from_object_id
    to_object_id
    relationship_id
    relationship_definition_id
```

`runtime_relationship_resolutions` is both:

```text
complete deterministic runtime closure
+
authoritative exact-view ownership/conflict index
```

Its exact row identity is:

```text
(resolution_id, from_object_id, to_object_id)
```

M4 should not create a second Relationship-specific materialization/conflict table for the same semantic space without new evidence.

Current factual Relationship persistence also participates in Object lifetime arbitration through database-enforced Object references. Any material change to the Relationship persistence/FK graph must trigger targeted revalidation of reviewed Object.DELETE lifetime assumptions.

---

# 5. CREATE — current first-phase findings

Concurrency/lock redesign remains deferred to the global concurrency phase.

## 5.1 Current preparation cost

Current CREATE performs, before conflict arbitration/DML, work including:

```text
resolution -> complete RelationshipDefinition
explicit/default exact RDV selection
lock-plan stabilization/repeated model reads
endpoint Object -> ObjectTemplate identity
complete ObjectTemplate parent-graph load
Python ancestry walking -> deterministic runtime closure
repeated exact RDV/schema load
exact DataType semantic loads
property canonicalization
```

Reads existing solely for lock-plan stabilization remain concurrency-phase concerns.

## 5.2 Redundant exact-schema reload

After stabilization the selected exact RDV is already known. Reloading the same exact RDV solely to construct runtime property specs is redundant independently of cache design.

Target separation:

```text
stabilized exact RDV
+
DataType semantic payloads
-> resolved runtime Relationship schema
```

## 5.3 Immutable exact RDV cache candidate

Published/deprecated exact RelationshipDefinitionVersion semantics are immutable and fit:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
    ordered property declarations
    exact DataType pins
    value modes
    compiled RuntimePropertySpec / validators
```

The cache must exclude mutable state such as RDV status and Definition default version. PostgreSQL remains authority for current CREATE admission; cache presence never proves current existence/admissibility.

## 5.4 Full ObjectTemplate graph load should leave the data-plane

CREATE needs bounded endpoint ancestry predicates, not the complete ObjectTemplate graph. Stable closure owner:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

with self rows supports those predicates. A READY/full stable ancestry cache may provide complete ancestor sets in memory.

Stable RelationshipDefinition topology is also a natural cache candidate:

```text
StableRelationshipDefinitionTopologyCache[definition_id]
    symmetric
    resolutions:
        resolution_id
        from_template_id
        to_template_id
```

Mutable Resolution names are excluded.

## 5.5 Conflict-owner lookup

Once complete deterministic closure is known, a selected-view exact-owner pre-check is informationally contained in a closure-wide ownership lookup.

If a pre-check remains, one set-based closure-owner projection is sufficient. Whether pre-checking remains at all or the runtime-closure PK arbitrates first remains a concurrency decision.

Observed conflicting owners do not need full semantic recertification merely to return/prove current owner identity.

## 5.6 Runtime closure DML

Candidate write shape:

```text
1 INSERT factual Relationship root
1 bulk INSERT complete runtime closure
```

Closure materialization remains all-or-nothing. Partial `ON CONFLICT DO NOTHING` is not acceptable.

`LifecycleStore.insert_relationship_events()` is already bulk and should remain so.

## 5.7 Lifecycle display metadata reread

CREATE currently rereads runtime closure plus mutable Resolution/Object display names after insertion. Eliminating that reread is possible only if coherent metadata is preserved under concurrent renames, so this remains OPEN / concurrency-dependent.

---

# 6. Global Relationship GET

Current M3 GET is already a trusted one-statement authoritative projection rooted at `relationships`, joined to materialized runtime closure and current Resolution names.

It does not need model/schema/lineage recertification.

Target remains:

```text
one authoritative PostgreSQL statement
no worker cache
no new denormalization
no semantic recertification
```

Do not copy mutable `Resolution.name` into runtime closure rows merely to avoid the join.

---

# 7. Object-scoped Relationship collection — technical baseline

The current persistence path pages from `runtime_relationship_resolutions`, joins `relationships` for factual current state and `relationship_resolutions` for current names, and is Object-rooted so it distinguishes absent Object from present Object with an empty page.

The operation is already one PostgreSQL statement and must not reconstruct RelationshipDefinition topology, ObjectTemplate ancestry, exact schema semantics or factual derivability.

Multiple exact runtime rows can collapse to one public object-relative semantic view, especially for symmetric definitions with overlapping lineage spaces; deduplication must therefore remain before pagination.

Existing navigation support is conceptually:

```text
ix_runtime_resolutions_from_object_page
(
    from_object_id,
    relationship_id,
    to_object_id,
    resolution_id
)
INCLUDE (relationship_definition_id)
```

No additional index/cache/denormalization is justified by current route evidence.

**Important:** exact selected columns, DTO shape, destination display fields, `properties`, filters and pagination contract remain deliberately deferred to the public REST contract review.

---

# 8. DATA_CHANGE — current first-phase findings

DATA_CHANGE mutates only `relationships.properties`; it does not alter Definition identity/version pin, endpoint identities or materialized runtime closure.

Therefore the target hot path must not recertify RelationshipDefinition topology, ObjectTemplate ancestry or closure derivability.

Candidate warm path:

```text
validate operations in memory
-> lock/load current factual Relationship
-> ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
-> apply_data_change()
-> canonical no-op: no UPDATE / no lifecycle event
-> otherwise one UPDATE relationships.properties
-> coherent lifecycle metadata/event path
-> COMMIT
```

The existing pinned RDV may be PUBLISHED or DEPRECATED; mutating an already-admitted fact does not require re-proving its source pin as currently PUBLISHED.

Repeated exact-schema loading is redundant once exact schema semantics are available. Lifecycle display-metadata optimization remains concurrency-dependent.

---

# 9. SCHEMA_CHANGE — current first-phase findings

SCHEMA_CHANGE changes only:

```text
relationship_definition_version
properties
```

Definition identity and runtime closure remain unchanged, so topology, endpoint compatibility, ObjectTemplate ancestry and closure completeness must not be recertified on the normal data-plane path.

Publication is the model-plane certification boundary. Runtime migration must not reload complete published/deprecated history and re-run publication certification.

Source and target exact semantic schemas fit the immutable RDV cache. PostgreSQL remains authority for current target existence/status and required direct exact DataType admission.

Numeric version order does **not** prove migrability. The older candidate requirement:

```text
target_version > source_version
```

is not current direction and must not be carried forward. Exact migration admission must derive from migration semantics, consistent with GP-01.

Conceptual DML remains:

```text
one UPDATE
    relationship_definition_version = target_version
    properties = migrated canonical map
```

Runtime closure remains unchanged. A changed exact schema pin remains semantically meaningful even if migrated canonical properties are equal; equal-target/no-op semantics must be reviewed in the detailed route sweep.

---

# 10. DELETE — current first-phase findings

DELETE needs authoritative factual before-state and coherent historical display metadata, not full model/schema recertification.

Candidate pre-delete projection contains factual root, complete persisted closure, current Resolution names and current endpoint Object canonical names. It must not re-derive expected closure from model topology.

Current ownership supports:

```text
1 DELETE relationships row
    -> runtime_relationship_resolutions CASCADE
```

Historical event metadata must be captured before the root delete because closure rows disappear by cascade. The complete DELETE event set remains bulk/atomic with the root deletion.

No RDV/DataType/ObjectTemplate cache is useful for DELETE. Mutable display names come from PostgreSQL. Exact synchronization with concurrent renames remains a concurrency question.

---

# 11. Cross-operation constraints and dependencies

## 11.1 Mutation response vs GET richness

Per the top-down review method, mutation acknowledgement/response shape is independent from the richness/cost of GET projections. Do not assume Relationship mutations must return the global GET DTO merely because AS-IS does.

## 11.2 Relationship persistence -> Object lifetime revalidation trigger

Relationship references currently participate in Object.DELETE blocker arbitration. Material changes to Relationship persistence/FKs reopen only the affected Object lifetime/delete assumptions.

## 11.3 No diagnostic-only backend work

Failure details/classification derive from the efficient legal execution path. Do not add reads solely for richer diagnostics.

---

# 12. Concurrency boundary

First-phase findings do not freeze lock planning, collision restart realization, rename-race synchronization or final transaction rendezvous.

Later concurrency review must prove at least:

```text
CREATE exact-view arbitration/collision classification
coherent lifecycle display metadata under Object/Resolution renames
SCHEMA_CHANGE final target admission
DATA_CHANGE/SCHEMA_CHANGE current fact lock/generation behavior
DELETE before-state capture vs concurrent metadata mutation
```

---

# 13. Exact public REST contract review

The functional capability coverage gate is closed. The Relationship pass reviews the six ratified M4 capabilities **one API at a time** to define the exact public REST contract before returning to technical realization.

For each API, this pass owns only the public contract, including:

```text
exact HTTP method + REST endpoint/path
exact path/query input parameters
exact request body, when present
exact success output body, when present
```

The pass may compare against AS-IS and previously recorded WIP candidates, but no existing shape is promoted automatically. Each API contract is revalidated explicitly before moving to the next one.

This pass deliberately does **not** decide how the API will technically implement the required semantics. In particular, defer:

```text
application/data-path realization
SQL statement shape
persistence schema/FKs
cache use/invalidation
indexes/query plans
locking/concurrency protocol
transaction rendezvous/retry
bulk-vs-row DML
physical denormalization
performance optimization
```

The technical findings already retained in sections 4–12 remain input for the later implementation/concurrency/physical sweep; they must not constrain the public contract merely because they were discovered earlier.

## 13.1 CREATE — route identity RATIFIED

The CREATE route is ratified as:

```text
POST /api/v1/core/relationships
```

with:

```text
path parameters:  none
query parameters: none
```

The factual Relationship is a global fact with its own lifetime identity, so CREATE is rooted at the global Relationship collection rather than subordinated under one Object or one RelationshipDefinition.

## 13.2 CREATE — request body RATIFIED

The CREATE request body is ratified as a strict object with exactly these public fields:

```text
resolution_id: UUID                         required
from_object_id: UUID                        required
to_object_id: UUID                          required
relationship_definition_version: integer   optional, positive, non-null when present
properties: object                          optional, non-null when present, omission -> {}
```

Semantic meaning:

```text
resolution_id
    selects the public RelationshipResolution / semantic perspective used to create the fact

from_object_id
    Object occupying the selected resolution's from side

to_object_id
    Object occupying the selected resolution's to side

relationship_definition_version omitted
    select the current default version of the RelationshipDefinition owning resolution_id

relationship_definition_version present
    select that explicit exact positive version

properties omitted
    equivalent to an empty property candidate {}
```

`resolution_id` remains the public selector rather than `name` because resolution identity is stable while its display name is renameable. Supplying `relationship_definition_id` in addition to `resolution_id` would be redundant because the selected resolution already belongs to exactly one RelationshipDefinition.

`from_object_id` and `to_object_id` remain directional rather than anonymous endpoint fields. Their meaning is interpreted against the selected resolution's public `from_template_id` / `to_template_id` semantics, including symmetric definitions.

Omission is not `null`: optional fields may be omitted to request default/empty semantics, but explicit `null` is not a valid substitute. Unknown body fields are rejected by the strict public-body contract.

## 13.3 CREATE — success response RATIFIED

Successful CREATE returns:

```text
201 Created
Location: /api/v1/core/relationships/{new_relationship_id}
```

with:

```text
success body: none
```

The new factual `relationship_id` is server-generated. `Location` is the canonical acknowledgement carrier for the created resource identity; a duplicate `{id}` response body is unnecessary.

CREATE does not return the global Relationship GET representation. Callers that need the canonical current factual representation follow the `Location` and use `GET /relationships/{relationship_id}`. This keeps mutation acknowledgement independent from GET richness and avoids coupling CREATE to the global detail `views` contract.

## 13.4 CREATE — public contract CLOSED

The complete ratified CREATE public contract is therefore:

```text
POST /api/v1/core/relationships
path params: none
query params: none
body:
    resolution_id required UUID
    from_object_id required UUID
    to_object_id required UUID
    relationship_definition_version optional positive integer, non-null when present
    properties optional object, non-null when present, omission -> {}
success:
    201 Created
    Location: /api/v1/core/relationships/{new_relationship_id}
    no body
```

No CREATE implementation/data-path decision is implied by this contract closure.

## 13.5 GET global detail — route/input RATIFIED

The global factual Relationship detail route is ratified as:

```text
GET /api/v1/core/relationships/{relationship_id}
```

with:

```text
path parameter:
    relationship_id: UUID, required

query parameters: none
request body: none
```

`relationship_id` is the factual Relationship lifetime-global identity. The route is rooted globally rather than under an Object or RelationshipDefinition because those entities are context/model inputs, not owners of the factual Relationship identity.

This checkpoint decides only method/path and request inputs. The exact successful response representation remains open and is the next GET contract micro-point.

Current next public-contract target:

```text
GET /api/v1/core/relationships/{relationship_id}
    -> exact 200 response representation
```

Ratified capability set to review contract-by-contract:

```text
CREATE
GET global detail by relationship_id
GET Object-scoped Relationship collection
DATA_CHANGE
SCHEMA_CHANGE
DELETE
```

Do not reopen global Relationship discovery in this pass; it remains owned by M5 Search API unless a new M4 caller requirement explicitly reopens that decision.