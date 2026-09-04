# M4 — Factual Relationship working owner

**Status:** REVIEWED BASELINE / WIP / NON-NORMATIVE / ARCHITECTURE CLOSING PENDING

## Review resumed — upstream model-plane semantics sufficiently stabilized

The M4 factual `Relationship` review is now **RESUMED**.

The earlier freeze was introduced because factual/runtime decisions depended on unstable `RelationshipDefinition` / `RelationshipResolution` semantics. The upstream model-plane review has now stabilized the semantics required by the factual data plane far enough to resume this WIP:

```text
RelationshipDefinition
    -> compact stable semantic contract
    -> no autonomous RelationshipResolution entity
    -> no resolution_id model identity
    -> stable directional semantic names
    -> materialized exact-template semantic closure
```

This does **not** mean that every `RelationshipDefinition` physical/API detail is closed. Remaining upstream details may still be reviewed separately. The factual review may temporarily return upstream only if a concrete data-plane blocker requires one of those details.

The review must keep the planes separate:

```text
MODEL PLANE
    RelationshipDefinition semantic contract
    relationship_definition_space exact-template closure

DATA PLANE
    factual Relationship identity/version/properties
    concrete Object-level semantic closure
```

The model-plane relational shape is not copied mechanically into factual persistence. The factual schema is reviewed on its own data-plane responsibilities.

Previously ratified factual public-contract checkpoints and technical findings remain preserved below as review history. Any item that depended on autonomous `RelationshipResolution`, `resolution_id`, mutable Resolution names, or the old runtime-row identity is explicitly reopened and must be revalidated against the post-review model-plane semantics.

In particular, the following pre-freeze areas are historical inputs rather than current settled shape until revalidated:

```text
CREATE selector based on resolution_id
GET global detail fields based on resolution_id
runtime_relationship_resolutions row identity
live join to relationship_resolutions for relationship name
Object-scoped pagination tie-breakers based on resolution identity
technical GET/index conclusions whose key shape includes resolution_id
```

This resumed review remains M4 WIP only. It does not authorize implementation or promote any decision to normative architecture.

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

# 4. RATIFIED post-definition data-plane relational baseline

The `RelationshipDefinition` review changed the model plane, not the factual root responsibilities. The factual data plane therefore keeps the existing root shape conceptually unchanged:

```text
relationships
    id
    relationship_definition_id
    relationship_definition_version
    properties
```

RATIFIED meaning:

```text
id
    lifetime-global factual Relationship identity

relationship_definition_id
    stable model-plane Definition binding of the factual Relationship

relationship_definition_version
    exact version pin for factual property-schema semantics

properties
    current canonical factual property state
```

The endpoint pair and complete oriented factual semantics remain materialized in an owned runtime child relation rather than being moved onto the root.

The old child shape depended on autonomous model-plane Resolutions:

```text
runtime_relationship_resolutions
    relationship_id
    relationship_definition_id
    resolution_id
    from_object_id
    to_object_id
```

That shape is superseded because the post-review model plane has no `RelationshipResolution` entity and no `resolution_id`.

## 4.1 RATIFIED runtime materialization — exact Object-level semantic cells

The factual runtime materialization directly owns the concrete Object-level semantic cells expressed by one factual Relationship.

Working TO-BE relation name:

```text
runtime_relationship_cells
```

The exact final SQL table name remains a physical naming detail; the ratified logical row shape is:

```text
runtime_relationship_cells
    relationship_id
    from_object_id
    name
    to_object_id
```

One row means exactly:

```text
from Object
    -- stable semantic name -->
to Object
```

The materialized semantic information is therefore the exact ordered Object-level cell:

```text
(from_object_id, name, to_object_id)
```

This is the data-plane analogue of, but not the same relation as, the model-plane exact-template closure:

```text
MODEL PLANE
relationship_definition_space
    relationship_definition_id
    from_template_id
    name
    to_template_id

DATA PLANE
runtime_relationship_cells
    relationship_id
    from_object_id
    name
    to_object_id
```

The model-plane closure certifies which exact-template semantic cells are expressible. The data-plane runtime relation materializes which exact-Object semantic cells are actually expressed by current factual Relationships.

## 4.2 RATIFIED runtime semantic-cell uniqueness and ownership

The semantic/exact-view identity of one current runtime cell is:

```text
(from_object_id, name, to_object_id)
```

RATIFIED rule:

```text
one exact Object-level semantic cell
    -> at most one current factual Relationship owner globally
```

`relationship_id` is **not** part of the semantic identity. Its role is relational ownership/grouping:

```text
runtime cell
    -> belongs to exactly one factual Relationship

relationship_id
    -> groups the complete runtime closure of that factual Relationship
    -> supports root-relative reads/delete
    -> provides the child -> relationships ownership reference
```

The exact physical realization of the semantic key as `PRIMARY KEY`, `UNIQUE`, or another equivalent relational mechanism remains a later DDL decision. The semantic uniqueness itself is ratified.

## 4.3 RATIFIED — no duplicated RelationshipDefinition identity in runtime child

`relationship_definition_id` is not required in the runtime child.

The owning Definition is already determined transitively and unambiguously:

```text
runtime_relationship_cells.relationship_id
    -> relationships.id
    -> relationships.relationship_definition_id
```

The old duplicated `relationship_definition_id` existed materially to enforce same-Definition coherence between factual Relationship and autonomous `RelationshipResolution` through composite references. Once `resolution_id` / `RelationshipResolution` disappear, that structural reason disappears as well.

RATIFIED direction:

```text
runtime_relationship_cells
    -> do not duplicate relationship_definition_id
```

Any future proposal to copy it back must be justified as an explicit measured denormalization, not as required semantic state.

## 4.4 RATIFIED — semantic `name` is materialized; Object canonical names are not

The runtime `name` is now part of the stable semantic cell itself. It is **not** a copied mutable display field and no longer requires a live join to a model-plane `relationship_resolutions` table.

Therefore:

```text
runtime_relationship_cells.name
    -> materialized stable semantic state
    -> read directly from the runtime child
```

Object `canonical_name` remains different:

```text
objects.canonical_name
    -> mutable current Object display state
    -> not part of runtime semantic-cell identity
    -> not copied into runtime_relationship_cells
```

GET projections that need current Object display metadata continue to join the two endpoint Object rows live in PostgreSQL.

This preserves the prior M4 decision against Object-name fan-out on Object RENAME while eliminating the old model-plane join that existed only to recover `RelationshipResolution.name`.

## 4.5 Runtime closure examples

Asymmetric Definition:

```text
VirtualMachine --runs_on--> Hypervisor
Hypervisor     --hosts----> VirtualMachine
```

Factual Objects `VM1` and `H1` materialize:

```text
relationship_id = R1
VM1  runs_on  H1
H1   hosts    VM1
```

Symmetric disjoint-space Definition:

```text
Router --connected_to--> Switch
```

Factual Objects `R1` and `S1` materialize:

```text
relationship_id = R2
R1  connected_to  S1
S1  connected_to  R1
```

Symmetric same-space with distinct Objects:

```text
Alice friend_of Bob
```

materializes:

```text
relationship_id = R3
Alice  friend_of  Bob
Bob    friend_of  Alice
```

Symmetric same-space self-loop:

```text
Alice friend_of Alice
```

materializes one exact cell only:

```text
relationship_id = R4
Alice  friend_of  Alice
```

Asymmetric inheritance-overlap example:

```text
Manager  --manages----> Employee
Employee --managed_by-> Manager
```

For two Manager Objects `M1` and `M2` the factual closure is losslessly:

```text
relationship_id = R5
M1  manages     M2
M2  managed_by  M1
```

## 4.6 Relational responsibilities retained/open

The ratified logical ownership/reference roles are:

```text
relationship_id
    -> owned-child reference to relationships

from_object_id
to_object_id
    -> references to current Objects

(from_object_id, name, to_object_id)
    -> global exact semantic-cell uniqueness authority
```

Exact SQL PK/FK/UNIQUE forms, `ON DELETE` actions, indexes, ordering support and table naming remain physical-design questions unless separately ratified.

The factual runtime child remains both:

```text
complete deterministic runtime semantic closure
+
authoritative exact Object-level semantic-cell ownership/conflict index
```

M4 should not add a second Relationship-specific materialization/conflict authority for the same data-plane semantic space without new evidence.

Because the runtime relation still references endpoint Objects, its final FK realization remains relevant to Object.DELETE lifetime arbitration and must be revalidated when the physical schema is closed.

## 4.7 Revalidation effect on pre-freeze findings

The following old assumptions are now explicitly superseded:

```text
runtime row identity includes resolution_id
runtime child duplicates relationship_definition_id for Resolution coherence
GET must join relationship_resolutions to recover relationship name
runtime name would be a denormalized copy of mutable Resolution metadata
```

The following higher-level data-plane principles remain valid and are carried forward:

```text
relationships is the factual root
runtime closure is owned by the factual root
closure materialization is complete/all-or-nothing
GET consumes trusted persisted factual state rather than re-certifying model semantics
Object canonical names remain live Object-owned display state
```

Sections 5–14 below retain the detailed pre-freeze review history. Any Resolution-dependent statement in those sections must be interpreted as historical input until explicitly revalidated against this ratified data-plane baseline.

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

This section is retained as pre-freeze history. Under the ratified post-definition data-plane baseline, runtime `name` is now stable semantic state already stored in `runtime_relationship_cells`, so the old requirement to join `relationship_resolutions` for the name is superseded. The global GET is the current active revalidation frontier.

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

**Post-definition revalidation marker:** the route/capability decisions in this section remain review history, but any request/response/filter/pagination field whose justification depends on autonomous `RelationshipResolution`, `resolution_id`, mutable Resolution names, or the old runtime-row key is reopened. Independent route, version/property and success/error decisions are not revoked automatically.

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
    identifies implicitly the owning RelationshipDefinition
    determines the semantic direction used to interpret from_object_id -> to_object_id

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

The CREATE command uses `resolution_id` as the fastest unambiguous selector for both the RelationshipDefinition and the intended traversal/perspective of that Definition. It is a command selector: it orients how the two supplied endpoint Objects are interpreted and from that selector the complete factual runtime closure is derived. The factual Relationship root does not persist a distinguished "creation resolution" after creation; it persists its own identity/schema/data while the complete runtime closure carries all exact resolutions of the admitted fact.

`from_object_id` and `to_object_id` remain directional rather than anonymous endpoint fields. Their names are intentionally retained because they make the selected resolution orientation explicit and readable: `from_object_id` occupies the selected resolution's from side and `to_object_id` its to side, including for symmetric definitions.

Omission is not `null`: optional fields may be omitted to request default/empty semantics, but explicit `null` is not a valid substitute. Unknown body fields are rejected by the strict public-body contract.

**REOPENED:** this request body cannot survive unchanged because `resolution_id` no longer exists in the model plane. Its replacement selector is deferred until the factual CREATE review resumes after the GET revalidation.

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

CREATE does not return the global Relationship GET representation. Callers that need the canonical current factual representation follow the `Location` and use `GET /relationships/{relationship_id}`. This keeps mutation acknowledgement independent from GET richness and avoids coupling CREATE to the global detail contract.

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

**Post-definition status:** route/success acknowledgement remain ratified; the body is reopened solely where it depends on `resolution_id`.

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

## 13.6 GET global detail — success representation RATIFIED

Successful global detail returns `200 OK` with the factual root state plus the **complete exact runtime resolution closure**, not the deduplicated Object-relative `views` projection used for navigation.

Conceptual response:

```text
RelationshipDetail
    id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: positive integer
    properties: object
    resolutions: array<RelationshipResolutionView>

RelationshipResolutionView
    resolution_id: UUID
    name: string
    from_object: ObjectReference
    to_object: ObjectReference

ObjectReference
    id: UUID
    canonical_name: string
```

Semantics:

```text
resolutions
    complete lossless exact closure of the factual Relationship
    no collapse/deduplication into Object-relative semantic views
    complete collection with no semantic public ordering
    clients MUST NOT rely on array position/order

resolution_id
    stable public identity of the exact RelationshipResolution represented by the closure row

name
    current mutable display name of that RelationshipResolution

from_object / to_object
    current Object references occupying the exact resolution direction

ObjectReference.canonical_name
    current mutable Object display metadata
    not part of Relationship or resolution identity
```

The global detail intentionally exposes the resolution identities because its role is to represent the factual Relationship losslessly. The Object-scoped collection remains the natural owner for a perspective-oriented/deduplicated navigation projection.

The response shape does not imply that Resolution names or Object canonical names are copied into factual persistence; they are current public display metadata.

An implementation may emit `resolutions` in a deterministic order for operational stability, but that order has no domain/public meaning and is not part of the REST contract.

**REOPENED:** the lossless-global-detail objective remains ratified, but the nested closure item must be redefined because there is no `resolution_id`, and `name` is now stable runtime semantic state rather than mutable Resolution display metadata. `ObjectReference {id, canonical_name}` remains a valid previously ratified display projection and is being revalidated against the new runtime relation.

## 13.7 GET global detail — public contract CLOSED

The complete pre-freeze global-detail contract was:

```text
GET /api/v1/core/relationships/{relationship_id}
path:
    relationship_id required UUID
query: none
body: none
success:
    200 OK
    RelationshipDetail
        id
        relationship_definition_id
        relationship_definition_version
        properties
        complete unordered resolutions[]
            resolution_id
            current name
            from_object { id, current canonical_name }
            to_object   { id, current canonical_name }
```

No global-GET implementation/data-path decision was implied by this contract closure.

**Post-definition status:** route/input and the requirement for a complete lossless global factual projection remain ratified; the exact nested runtime-cell representation is the current active review frontier.

## 13.8 GET Object-scoped collection — route/path RATIFIED

The Object-scoped factual Relationship collection route is ratified as:

```text
GET /api/v1/core/objects/{object_id}/relationships
```

with:

```text
path parameter:
    object_id: UUID, required

request body: none
query parameters: under review
```

The Object is the navigation context, not the owner of the factual Relationship identity. This route answers which factual Relationships are visible from the selected Object and remains distinct from global Relationship discovery/query, which is owned by M5 Search API.

## 13.9 GET Object-scoped collection — RelationshipDefinition filter RATIFIED

The collection supports the optional stable filter:

```text
relationship_definition_id: UUID, optional
```

Semantics:

```text
omitted
    do not restrict visible factual Relationships by RelationshipDefinition

present
    return only factual Relationships visible from object_id whose owning
    RelationshipDefinition has the supplied stable identity
```

This remains an Object-scoped navigation filter rather than global search: the path already fixes the Object navigation domain and the filter only narrows that domain to one stable RelationshipDefinition identity.

## 13.10 GET Object-scoped collection — `name` query filter REMOVED

The M4 TO-BE contract does **not** expose the AS-IS `name` query parameter.

`RelationshipResolution.name` is mutable display/semantic-label state rather than stable identity. Filtering this navigation endpoint by that string would make the route behave like a partial search API and creates coupling to renameable model-plane display state without a demonstrated navigation requirement.

No `resolution_id` replacement filter is introduced automatically. A specific perspective filter would require a concrete caller need before being added to this API.

Textual/perspective-name discovery belongs to the M5 Search API unless a later M4 caller requirement explicitly reopens this boundary.

**REOPENED rationale only:** the original justification based on mutable `RelationshipResolution.name` is superseded because semantic names are now stable. Whether the Object-scoped GET should still omit a `name` filter must be revalidated later from caller/navigation requirements rather than carried forward from the old mutability argument.

## 13.11 GET Object-scoped collection — keyset cursor RATIFIED

The collection uses keyset pagination and exposes:

```text
cursor: opaque string, optional
```

Semantics:

```text
cursor omitted
    request the first page under the current collection/filter scope

cursor present
    continue keyset pagination from the server-defined boundary encoded
    by the opaque cursor
```

The cursor is an opaque continuation token. Clients must not parse, construct or assign semantic meaning to its contents. Offset pagination is not part of this contract.

This checkpoint ratifies the existence of cursor-based keyset pagination only. Cursor payload/encoding, cursor-to-scope/filter binding rules and invalid-cursor semantics remain OPEN and must be reviewed explicitly.

## 13.12 GET Object-scoped collection — page limit RATIFIED

The collection exposes the optional page-size parameter:

```text
limit: positive integer, optional
```

with exact public bounds:

```text
omitted -> 100
minimum -> 1
maximum -> 500
```

`limit` bounds only the requested page size. It does not alter collection membership or introduce offset semantics, and it composes with the ratified opaque keyset `cursor`.

Current ratified request surface is therefore:

```text
GET /api/v1/core/objects/{object_id}/relationships
path:
    object_id: UUID, required
query:
    relationship_definition_id: UUID, optional
    cursor: opaque string, optional
    limit: positive integer 1..500, optional, default 100
    no name query parameter
body: none
```

Cursor payload/encoding, cursor-to-scope/filter binding rules and invalid-cursor semantics remain OPEN.

## 13.13 GET Object-scoped collection — item representation RATIFIED

Each collection item is the factual Relationship as seen from the Object fixed by the path, not the global lossless runtime closure.

The ratified item shape is:

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

Semantics:

```text
relationship_id
    stable factual Relationship identity and navigation key to global detail

relationship_definition_id
relationship_definition_version
    current exact Definition binding of the fact; retained in the item so the
    Object-scoped projection remains self-contained for common callers

properties
    current factual Relationship property state

name
    current mutable display/semantic label of the Object-relative perspective;
    returned as display context but not accepted as an M4 query filter

destination_object
    current Object reference reached from the Object fixed by the route path
```

The path `object_id` is intentionally not repeated in every item. The item also does not expose a single `resolution_id`: multiple exact runtime resolution rows can collapse to the same Object-relative public semantic view, so selecting one exact resolution identity would be arbitrary. Callers that need the complete lossless exact resolution closure use the global Relationship detail endpoint.

`destination_object.canonical_name` and `name` are current mutable display metadata and are not part of factual Relationship identity.

Cursor payload/encoding, cursor-to-scope/filter binding rules and invalid-cursor semantics remain OPEN.

**Post-definition revalidation required:** the item intent remains Object-relative, but statements about runtime-resolution collapse, mutable relationship names and resolution identity must be rechecked against `runtime_relationship_cells`.

## 13.14 GET Object-scoped collection — page envelope RATIFIED

Successful collection reads use the minimal page envelope:

```text
ObjectRelationshipPage
    items: array<ObjectRelationshipItem>
    next_cursor: string | null
```

Semantics:

```text
items
    current page of Object-relative Relationship items, bounded by limit

next_cursor
    opaque continuation cursor when another page exists
    null when the current page has no continuation
```

The page envelope does not expose a total count and does not introduce offset/page-number semantics. The cursor remains opaque as ratified above; cursor validity/binding rules remain separate decisions.

## 13.15 GET Object-scoped collection — ordering/keyset semantics RATIFIED

The collection is emitted in a deterministic order solely to support stable keyset continuation.

Public semantics are:

```text
items order
    deterministic for pagination continuity
    no domain or business meaning
    clients MUST NOT rely on item position/order

keyset boundary
    server-defined and carried only by the opaque cursor
    based on stable identities sufficient to distinguish Object-relative public items
    independent from mutable display/factual state
```

In particular, the pagination key must not depend on:

```text
RelationshipResolution.name
Object.canonical_name
Relationship.properties
relationship_definition_version
```

because those values can change while the factual Relationship or its endpoint binding remains the same.

The implementation may use stable fact/endpoint identities plus a stable resolution-derived tie-breaker when more than one distinct Object-relative perspective of the same fact reaches the same destination. The exact internal key tuple is intentionally not part of the public REST contract and remains a technical realization detail; only its stability and opacity are public requirements.

**REOPENED where Resolution-dependent:** `name` is now stable semantic state, not mutable display metadata, and no resolution-derived tie-breaker exists. Exact keyset identity will be revalidated later against the runtime semantic-cell key.

## 13.16 GET Object-scoped collection — cursor binding and invalid-cursor semantics RATIFIED

A continuation cursor is bound to the exact navigation/query scope that produced it.

Public binding semantics are:

```text
cursor bound to:
    this Object-scoped Relationship collection/cursor kind
    object_id from the route path
    relationship_definition_id filter value, including the explicit semantic state "filter omitted"

cursor not bound to:
    limit
```

Therefore callers may change `limit` while continuing the same traversal, but a cursor produced for one Object or one RelationshipDefinition-filter scope cannot be reused for another.

The cursor is rejected with:

```text
400 Bad Request
code: invalid_cursor
```

when it is malformed, uses an unsupported/unrecognized cursor version or shape, belongs to another collection/cursor kind, or is incompatible with the current `object_id` / `relationship_definition_id` scope.

The token represents a stable keyset boundary, not a foreign-key-like reference to the item that originally ended the prior page. Deletion of that boundary item after cursor issuance therefore does not by itself invalidate the cursor; continuation proceeds beyond the encoded stable boundary.

The exact cursor payload fields, serialization and encoding remain implementation details as long as the token remains opaque and the ratified binding/validation semantics are preserved.

## 13.17 GET Object-scoped collection — parent/filter existence semantics RATIFIED

The route distinguishes the existence of the Object addressed by the path from collection/filter membership.

Ratified behavior is:

```text
object_id does not exist
    -> 404 Not Found
       resource_type = object

object_id exists but no factual Relationship is visible
    -> 200 OK
       items = []
       next_cursor = null

object_id exists and relationship_definition_id produces no matches
    -> 200 OK
       items = []
       next_cursor = null
```

The last case also applies when the supplied `relationship_definition_id` does not identify any existing RelationshipDefinition. In this route it is a collection filter, not a parent/resource selector, so a non-matching or nonexistent filter value produces an empty collection rather than a referenced-resource error.

## 13.18 GET Object-scoped collection — public contract CLOSED

The complete ratified Object-scoped collection contract is therefore:

```text
GET /api/v1/core/objects/{object_id}/relationships
path:
    object_id: UUID, required
query:
    relationship_definition_id: UUID, optional
    cursor: opaque string, optional
    limit: positive integer 1..500, optional, default 100
    no name query parameter
body: none
success:
    200 OK
    ObjectRelationshipPage
        items: array<ObjectRelationshipItem>
            relationship_id
            relationship_definition_id
            relationship_definition_version
            properties
            current name
            destination_object { id, current canonical_name }
        next_cursor: opaque string | null
pagination:
    keyset only
    deterministic order with no public/domain ordering meaning
    stable opaque boundary independent from mutable display/factual state
    cursor bound to object_id + relationship_definition_id scope, not to limit
errors/empty semantics:
    malformed/incompatible cursor -> 400 invalid_cursor
    missing object_id -> 404 resource_not_found(object)
    existing Object with zero matches -> 200 empty page
```

No Object-scoped collection implementation/data-path decision is implied by this contract closure. Exact internal key tuple, cursor payload/encoding, SQL realization, index design and deduplication mechanics remain technical realization concerns subject to the later sweep.

**Post-definition status:** route/basic page semantics remain historical ratified input; name-filter rationale, item semantics where they depend on mutable Resolution names, and keyset realization are reopened for later revalidation.

## 13.19 DATA_CHANGE — route identity and Object-alignment principle RATIFIED

The Relationship DATA_CHANGE public route is ratified as:

```text
POST /api/v1/core/relationships/{relationship_id}/properties
```

with:

```text
path parameter:
    relationship_id: UUID, required

query parameters: none
```

The M4 TO-BE route intentionally supersedes the AS-IS `/relationships/{relationship_id}/data-change` path. `DATA_CHANGE` remains the capability/lifecycle name, while the HTTP resource being mutated is the factual Relationship `properties` sub-resource.

This aligns the Relationship mutation surface with the already-consolidated Object M4 contract:

```text
POST /api/v1/core/objects/{object_id}/properties
POST /api/v1/core/relationships/{relationship_id}/properties
```

The review principle is to keep Object and Relationship property-mutation wire contracts and behavior analogous wherever their domain semantics permit. Any divergence must be justified by a concrete Relationship-specific semantic requirement rather than inherited from AS-IS shape.

This checkpoint ratifies only route/path/query identity and the alignment principle. The exact Relationship request body, success response, no-op semantics and failure mapping remain OPEN and must be reviewed explicitly.

## 13.20 DATA_CHANGE — request body RATIFIED

The Relationship properties-mutation request body is intentionally identical field-for-field and rule-for-rule to the already-consolidated Object properties-mutation body.

Conceptual transport model:

```text
RelationshipPropertiesMutationBody
    operations: PropertyOperation[1..N]

PropertyOperation
    SET
        property: string
        value: JsonValue

    REMOVE
        property: string
```

Ratified structural/request semantics are:

```text
operations
    required
    non-empty

same property
    at most once per request

SET
    requires value

REMOVE
    forbids value

array order
    no semantic mutation-order meaning

whole request
    atomic
    no partial success
```

Unknown body fields are rejected by the strict public-body contract.

No Relationship-specific wire-level property-name regex is introduced. `property` is structurally a string; whether that property exists and whether the requested effect is admissible belong to semantic validation against the Relationship's exact pinned RelationshipDefinitionVersion schema.

A `SET` operation with `value: null` is not interpreted as `REMOVE` or omission. It remains a structurally meaningful SET attempt whose null runtime value is semantically invalid under the runtime property model.

This checkpoint ratifies request shape and request-operation semantics only. Exact success response, semantic no-op behavior and complete failure mapping remain OPEN and must be reviewed explicitly.

## 13.21 DATA_CHANGE — success response and semantic no-op policy RATIFIED

Relationship DATA_CHANGE follows the already-consolidated Object properties-mutation success/no-op contract.

Successful real changes return:

```text
204 No Content
```

with no response body. The canonical current Relationship representation remains owned by `GET /api/v1/core/relationships/{relationship_id}`.

A semantic no-op also returns:

```text
204 No Content
```

When no-op recognition falls naturally out of applying the requested operations to current canonical Relationship properties, the implementation may elide persistence/history work:

```text
cheaply recognized no-op
    -> no Relationship properties UPDATE
    -> no DATA_CHANGE lifecycle event
```

Canonical examples are:

```text
SET p = canonical V
    current p == V
        -> no-op

REMOVE p
    p already absent
        -> no-op
```

No additional PostgreSQL statement, lock round trip, schema/cache lookup or second whole-map equality pass is introduced solely to prove a no-op. If classifying a request as a no-op would require material extra work, normal persisted mutation behavior remains allowed; throughput is preferred over artificial no-op classification.

This public checkpoint deliberately does not introduce or ratify a Relationship generation/revision mechanism. Any such concurrency/freshness realization remains part of the later technical/concurrency sweep.

## 13.22 DATA_CHANGE — failure mapping and precedence RATIFIED

Relationship DATA_CHANGE follows the Object properties-mutation failure taxonomy wherever the domains are equivalent, with only the Relationship-schema differences that actually exist.

Public failures are:

```text
400 invalid_request
    malformed relationship_id carrier
    any query parameter
    malformed/static request body
    operations missing or empty
    unknown operation kind
    duplicate operation for the same property
    SET without value
    REMOVE with value
    unknown body fields

404 resource_not_found
    selected factual Relationship does not exist

422 semantic_validation_failed
    requested property does not exist in the exact pinned RelationshipDefinitionVersion
    SET null
    wrong SCALAR/LIST shape
    primitive validation/canonicalization failure
    exact DataTypeVersion constraint violation

500 internal_error
    required persisted exact Relationship schema/dependency unexpectedly missing or corrupt
    unexpected persistence/lifecycle/invariant failure
    eventual bounded concurrency stabilization failure, if the later technical realization requires such retries
```

Unlike Object DATA_CHANGE, Relationship DATA_CHANGE has no `REMOVE required` or `required LIST=[]` failure because the current Relationship property schema has no `required` property dimension.

There is no normal `409` concurrency/business-conflict response for this capability. Any stale-attempt/retry mechanism introduced by the later concurrency realization is internal control flow unless a distinct domain conflict is independently proven.

Public precedence is:

```text
static transport/request validation
    -> authoritative current Relationship existence/state
    -> requested-effect semantic validation against the exact pinned schema
    -> candidate/no-op derivation
    -> real mutation commit when required
```

A factual Relationship pinned to a RelationshipDefinitionVersion that is now DEPRECATED remains mutable. DATA_CHANGE does not create a new model-plane binding and therefore does not require the current exact pin to be PUBLISHED, default or latest.

## 13.23 DATA_CHANGE — public contract CLOSED

The complete ratified Relationship DATA_CHANGE public contract is:

```text
POST /api/v1/core/relationships/{relationship_id}/properties
path:
    relationship_id: UUID, required
query: none
body:
    operations: PropertyOperation[1..N], required
    SET    { op, property, value }
    REMOVE { op, property }
    same property at most once
    array order has no mutation-order meaning
    atomic / no partial success
success:
    204 No Content
    no body
no-op:
    204 No Content
    cheaply recognized no-op may elide UPDATE and DATA_CHANGE lifecycle
failures:
    malformed/static request -> 400 invalid_request
    missing Relationship -> 404 resource_not_found
    invalid requested property effect/value -> 422 semantic_validation_failed
    impossible persisted/infrastructure failure -> 500 internal_error
    no normal 409
```

No DATA_CHANGE implementation/data-path/concurrency mechanism is implied by this public-contract closure. Exact semantic-cache use, current-state carrier, write shape, lifecycle physical carrier, locking/retry strategy and any Relationship generation mechanism remain later technical/concurrency decisions.

## 13.24 SCHEMA_CHANGE — route identity and Object-alignment principle RATIFIED

The Relationship SCHEMA_CHANGE public route is ratified as:

```text
POST /api/v1/core/relationships/{relationship_id}/schema
```

with:

```text
path parameter:
    relationship_id: UUID, required

query parameters: none
```

The M4 TO-BE route intentionally supersedes the AS-IS `/relationships/{relationship_id}/schema-change` path. `SCHEMA_CHANGE` remains the capability/lifecycle name, while `/schema` identifies the exact schema-binding sub-resource being mutated.

This aligns the Relationship mutation surface with the already-consolidated Object M4 contract:

```text
POST /api/v1/core/objects/{object_id}/schema
POST /api/v1/core/relationships/{relationship_id}/schema
```

The review principle is to keep Object and Relationship schema-mutation wire contracts and behavior analogous wherever their domain semantics permit. Any divergence must be justified by a concrete Relationship-specific semantic requirement rather than inherited from AS-IS shape.

This checkpoint ratifies only route/path/query identity and the alignment principle. The exact Relationship request body, exact-target semantics, success response, same-version behavior and failure mapping remain OPEN and must be reviewed explicitly.

## 13.25 SCHEMA_CHANGE — request body, exact-target command and equal-target semantics RATIFIED

The Relationship schema-mutation request body is intentionally identical to the already-consolidated Object schema-mutation body:

```text
RelationshipSchemaMutationBody
    target_version: positive integer, required
```

Equivalent JSON shape:

```json
{
  "target_version": 5
}
```

Missing, explicit-null, malformed/non-positive `target_version` and unknown body fields are invalid static request input.

For current exact RelationshipDefinition binding:

```text
SOURCE = D@VS
TARGET = D@VT
```

SCHEMA_CHANGE is an **exact-target migration command**. Version numbers identify exact versions and their allocation/creation order within one RelationshipDefinition lineage; they do not by themselves define genealogy, compatibility or migration direction.

Therefore:

```text
VT > VS
VT < VS
```

carry no migration-admission meaning by themselves. In particular, the AS-IS/older `target_version > source_version` requirement is not part of the M4 TO-BE contract.

Intermediate numeric versions are not implicitly replayed. A distinct request is evaluated as the exact SOURCE -> TARGET pair selected by the command.

Equal target is aligned exactly with Object TO-BE semantics:

```text
VT == VS
    -> 204 No Content
    -> no migration plan / schema migration work
    -> no Relationship UPDATE
    -> no SCHEMA_CHANGE lifecycle event
```

An equal-target request creates no new binding. The current exact RelationshipDefinitionVersion may therefore already be DEPRECATED; equal-target success does not require re-admitting it as PUBLISHED/default/latest.

This checkpoint ratifies request shape, exact-target semantics, removal of forward-only numeric admission and equal-target success/no-op behavior only. Distinct-target admission, migrability rules, real-migration success semantics and complete failure mapping remain OPEN.

## 13.26 SCHEMA_CHANGE — distinct-target admission and migrability RATIFIED

For a distinct exact target:

```text
VT != VS
```

Relationship SCHEMA_CHANGE follows the same target-admission model as Object SCHEMA_CHANGE.

The selected target is the exact RelationshipDefinitionVersion within the Relationship's existing stable RelationshipDefinition lineage:

```text
TARGET = D@VT
```

and must satisfy:

```text
exact D@VT exists
exact D@VT is PUBLISHED through the new-binding commit
```

Public target-admission outcomes are:

```text
exact D@VT does not exist
    -> 422 referenced_resource_not_found

exact D@VT exists but is not PUBLISHED
    -> 409 dependency_not_admissible
```

The SOURCE exact version is already the Relationship's current admitted binding and may be PUBLISHED or DEPRECATED. SCHEMA_CHANGE does not require SOURCE to be re-admitted as PUBLISHED merely because the Relationship is leaving it.

Migrability is evaluated directly for the exact SOURCE -> TARGET pair. No intermediate version is replayed and numeric direction has no admission meaning.

Relationship-specific migration remains simpler than Object migration because factual Relationship schema has no ObjectTemplate inheritance/component-slot dimension and no `required`/`migration_default` property dimension. Public migration semantics are:

```text
property present only in TARGET
    -> starts absent

property present only in SOURCE
    -> omitted from TARGET factual state

semantically continuous property with current value
    -> preserve current information when the exact TARGET semantics admit it

SCALAR -> LIST continuity
    -> preserve x as [x]

current factual information not representable/valid under TARGET semantics
    -> 409 schema_change_blocked
```

A successful real distinct-target migration returns:

```text
204 No Content
```

with no response body. The canonical current state remains owned by the global Relationship GET.

Successful SCHEMA_CHANGE preserves:

```text
relationship_id
relationship_definition_id
endpoint identities
complete runtime resolution closure
```

and changes only the exact RelationshipDefinitionVersion binding plus the canonical factual property state required by that target.

This checkpoint ratifies distinct-target admission, direct exact-pair migrability, the concrete-data blocker class and real-migration success acknowledgement. Complete static/failure mapping and precedence remain OPEN and are reviewed next.

## 13.27 SCHEMA_CHANGE — failure mapping and precedence RATIFIED

The complete public failure set is:

```text
400 invalid_request
    malformed relationship_id carrier
    any query parameter
    malformed/static request body
    target_version missing, explicit-null, malformed or non-positive
    unknown body fields

404 resource_not_found
    selected factual Relationship does not exist

422 referenced_resource_not_found
    distinct exact target D@VT does not exist

409 dependency_not_admissible
    distinct exact target D@VT exists but is not PUBLISHED

409 schema_change_blocked
    current factual information cannot be preserved/represented under TARGET semantics

500 internal_error
    required persisted exact Relationship schema/dependency unexpectedly missing or corrupt
    unexpected persistence/lifecycle/invariant failure
    eventual bounded concurrency stabilization failure, if the later technical realization requires such retries
```

The two `409` outcomes are domain conflicts, not exposure of technical contention: `dependency_not_admissible` means the requested new exact binding is not currently admissible, while `schema_change_blocked` means the current factual state cannot be migrated losslessly to the requested exact target.

Public precedence is:

```text
static request validation
    -> authoritative current Relationship existence + SOURCE binding
    -> VT == VS ?
         yes -> 204 semantic no-op
         no  -> exact TARGET existence
              -> TARGET PUBLISHED admission
              -> exact SOURCE -> TARGET migrability against current factual state
              -> real migration commit
```

Consequently, an equal-target request does not re-check whether the already-current exact version is still PUBLISHED. It creates no new binding and is already satisfied by the current factual state.

Any later stale-attempt/retry mechanism remains technical control flow. It must not introduce an additional public concurrency-conflict class unless a distinct domain conflict is independently proven.

## 13.28 SCHEMA_CHANGE — public contract CLOSED

The complete ratified Relationship SCHEMA_CHANGE public contract is:

```text
POST /api/v1/core/relationships/{relationship_id}/schema
path:
    relationship_id: UUID, required
query: none
body:
    target_version: positive integer, required
semantics:
    exact-target command within current RelationshipDefinition lineage
    numeric direction has no migration-admission meaning
    no intermediate-version replay
    equal target -> semantic no-op
success:
    204 No Content
    no body
equal target:
    204 No Content
    no migration / UPDATE / SCHEMA_CHANGE lifecycle
distinct target:
    exact target must exist and be PUBLISHED
    direct exact SOURCE -> TARGET migrability
    current information preserved where semantically continuous
    incompatible current factual information -> 409 schema_change_blocked
failures:
    malformed/static request -> 400 invalid_request
    missing Relationship -> 404 resource_not_found
    missing distinct target -> 422 referenced_resource_not_found
    non-PUBLISHED distinct target -> 409 dependency_not_admissible
    concrete migration blocker -> 409 schema_change_blocked
    impossible persisted/infrastructure failure -> 500 internal_error
```

No SCHEMA_CHANGE implementation/data-path/concurrency mechanism is implied by this public-contract closure. Exact semantic-cache/MigrationPlan realization, current-state carrier, write/lifecycle shape, locking/retry strategy and any Relationship generation mechanism remain later technical/concurrency decisions.

## 13.29 DELETE — route and request surface RATIFIED

The Relationship DELETE public route is ratified as:

```text
DELETE /api/v1/core/relationships/{relationship_id}
```

with:

```text
path parameter:
    relationship_id: UUID, required

query parameters: none
request body: none
```

The factual Relationship is deleted directly through its lifetime-global identity. No subordinate `/delete` command route or Object-scoped deletion surface is introduced.

This request surface is intentionally aligned with Object DELETE:

```text
DELETE /api/v1/core/objects/{object_id}
DELETE /api/v1/core/relationships/{relationship_id}
```

This checkpoint ratifies only method/path/request carriers. Success acknowledgement, repeated/missing-target behavior and complete public failure mapping remain OPEN and are reviewed explicitly next.

## 13.30 DELETE — success and missing/repeated-target semantics RATIFIED

Relationship DELETE follows the already-consolidated Object DELETE success/absence semantics.

Successful deletion of an existing factual Relationship returns:

```text
204 No Content
```

with no response body. DELETE does not return the deleted Relationship representation.

An absent target is not treated as convergent success:

```text
relationship_id does not identify a current factual Relationship
    -> 404 resource_not_found
       resource_type = relationship
```

Consequently, repeating DELETE after a previously committed successful deletion also returns `404 resource_not_found`; the operation does not collapse "already absent" into another `204` success.

This checkpoint ratifies only success acknowledgement and missing/repeated-target behavior. Complete public failure mapping and precedence remain OPEN and are reviewed next.

## 13.31 DELETE — failure mapping and precedence RATIFIED

The complete public failure set is:

```text
400 invalid_request
    malformed relationship_id carrier
    any query parameter
    request body present

404 resource_not_found
    selected factual Relationship does not exist
    including repeated DELETE after a previously committed successful deletion

500 internal_error
    required persisted factual Relationship/root/closure state unexpectedly inconsistent
    unexpected persistence/lifecycle/invariant failure
    eventual bounded concurrency stabilization failure, if the later technical realization requires such retries
```

Relationship DELETE has no normal `409` or `422` outcome. No current Relationship-owned runtime closure row is an external lifetime blocker to its owning factual Relationship; owned closure removal is part of the deletion transition rather than a caller-resolvable conflict.

Public precedence is:

```text
static request validation
    -> authoritative current Relationship existence
    -> atomic factual deletion + required DELETE lifecycle transition
    -> 204 No Content
```

If another operation has already removed the factual Relationship before authoritative existence is established, the observable outcome is `404 resource_not_found`. Technical contention/retry behavior does not by itself create a public `409` class.

## 13.32 DELETE — public contract CLOSED

The complete ratified Relationship DELETE public contract is:

```text
DELETE /api/v1/core/relationships/{relationship_id}
path:
    relationship_id: UUID, required
query: none
body: none
success:
    204 No Content
    no body
absence/repeated delete:
    404 resource_not_found
    resource_type = relationship
failures:
    malformed/static request -> 400 invalid_request
    missing Relationship -> 404 resource_not_found
    impossible persisted/infrastructure failure -> 500 internal_error
    no normal 409 or 422
```

No DELETE implementation/data-path/concurrency mechanism is implied by this public-contract closure. Exact before-state carrier, lifecycle physical carrier, delete statement shape, locking/retry strategy and persistence/FK realization remain later technical/concurrency decisions.

## 13.33 Exact public REST contract sweep — PRE-FREEZE CLOSED / PARTIALLY REOPENED

Before the upstream Definition review, the factual Relationship exact public REST contract sweep was closed for all six M4 capabilities:

```text
CREATE                                  PRE-FREEZE CLOSED
GET global detail by relationship_id    ACTIVE REVALIDATION
GET Object-scoped Relationship collection REVALIDATION REQUIRED WHERE RESOLUTION-DEPENDENT
DATA_CHANGE                             CLOSED
SCHEMA_CHANGE                           CLOSED
DELETE                                  CLOSED
```

The route inventory remains:

```text
POST   /api/v1/core/relationships
GET    /api/v1/core/relationships/{relationship_id}
GET    /api/v1/core/objects/{object_id}/relationships
POST   /api/v1/core/relationships/{relationship_id}/properties
POST   /api/v1/core/relationships/{relationship_id}/schema
DELETE /api/v1/core/relationships/{relationship_id}
```

Global Relationship discovery remains owned by M5 Search API, Object-scoped single detail remains unnecessary absent a new caller requirement, and endpoint reassignment remains DELETE + CREATE with new factual identity.

Current resumed frontier:

```text
GET /api/v1/core/relationships/{relationship_id}
    -> revalidate exact lossless response against ratified runtime_relationship_cells schema
    -> then revalidate Object-scoped Relationship collection
    -> then revisit CREATE selector
```

---

# 14. Technical realization / concurrency / physical revalidation

The pre-freeze technical sweep below is retained as detailed review history. It was based on the old runtime Resolution model and is superseded wherever it requires `relationship_resolutions`, `resolution_id`, duplicated runtime `relationship_definition_id`, or mutable Resolution-name joins.

The currently ratified factual relational baseline is section 4. The active technical frontier has returned to the global GET.

## 14.1 GET global detail — materialized closure + live display joins PRE-FREEZE HISTORY

The global factual Relationship GET kept the then-materialized factual/runtime split:

```text
relationships
    -> factual root identity
    -> current exact RelationshipDefinitionVersion pin
    -> current factual properties

runtime_relationship_resolutions
    -> complete exact runtime resolution closure
    -> exact factual endpoint/resolution identities
```

`runtime_relationship_resolutions` was the durable materialized structural source for the complete exact closure. The GET consumed that closure directly; it did not reconstruct or re-certify closure membership from RelationshipDefinition topology, ObjectTemplate ancestry or endpoint template compatibility.

Current mutable display metadata was deliberately **not** copied into the runtime closure. In particular pre-freeze M4 did not add:

```text
runtime_relationship_resolutions.resolution_name
runtime_relationship_resolutions.from_object_canonical_name
runtime_relationship_resolutions.to_object_canonical_name
```

The normal read path instead used one live PostgreSQL projection combining:

```text
relationships
runtime_relationship_resolutions
relationship_resolutions
objects AS from_object
objects AS to_object
```

The live joins supplied:

```text
RelationshipResolution.name
from Object.canonical_name
to Object.canonical_name
```

Under the post-review model this specific join shape is superseded: semantic `name` now lives directly in `runtime_relationship_cells`, while Object canonical names remain live joins.

The higher-level target read character remains useful input:

```text
one authoritative PostgreSQL business statement
one statement snapshot
trusted persisted factual root
trusted materialized exact runtime closure
live current Object display metadata
no semantic closure re-derivation
no schema/DataType/ancestry reads
no worker cache
```

## 14.2 GET global detail — hot-path one-statement projection and denormalization PRE-FREEZE HISTORY

The pre-freeze target used:

```text
relationships AS r
    LEFT JOIN enriched_runtime_closure AS c

where enriched_runtime_closure was:

runtime_relationship_resolutions AS rr
    INNER JOIN relationship_resolutions AS resolution
    INNER JOIN objects AS from_object
    INNER JOIN objects AS to_object
```

The root-preserving boundary distinguished:

```text
no relationships root row
    -> 404 resource_not_found

relationships root exists but no runtime closure row is visible
    -> persisted factual invariant corruption
    -> 500 internal_error
```

The old additional-denormalization analysis is now split by semantic ownership:

```text
relationship semantic name
    -> no longer optional display denormalization
    -> now intrinsic runtime semantic-cell state
    -> model-plane name join disappears

Object.canonical_name
    -> remains mutable Object-owned display state
    -> copying it would still create Object.RENAME fan-out
    -> remain live joins unless later evidence proves otherwise
```

Thus the old conclusion against copying Object names survives, while the old conclusion against copying `resolution_name` is superseded because there is no Resolution-name copy anymore: the runtime cell owns its stable `name` directly.

## 14.3 GET global detail — projection/index conclusions PRE-FREEZE HISTORY / REOPENED

The old projector decoded one exact runtime row into one public Resolution item with a row shape containing:

```text
resolution_id
resolution_name
from_object_id
from_canonical_name
to_object_id
to_canonical_name
```

That exact row identity/order/index analysis is reopened because `resolution_id` no longer exists.

The following principles remain useful:

```text
zero SQL rows
    -> factual Relationship root absent
    -> 404 resource_not_found

root exists + no complete runtime closure
    -> persisted factual invariant corruption
    -> 500 internal_error

properties
    -> trust persisted factual JSON carrier
    -> no schema/DataType recertification on GET

GET concurrency
    -> one PostgreSQL statement snapshot
    -> no explicit locks/generation/retry loop
```

The old operational order and covering-index candidate based on `resolution_id` are superseded and must be reconsidered against:

```text
runtime semantic-cell key
    (from_object_id, name, to_object_id)
```

Current next technical frontier:

```text
GET /api/v1/core/relationships/{relationship_id}
    -> exact lossless public item shape over runtime_relationship_cells
    -> one-statement join shape with current Object canonical names
    -> deterministic operational ordering
    -> index sufficiency only after projection shape is reclosed
```

## 14.4 RATIFIED post-definition GET global lossless projection

The global factual Relationship GET continues to represent the fact **globally and losslessly**. It consumes the ratified data-plane runtime closure directly and does not collapse it into an Object-relative navigation view.

RATIFIED logical response content is:

```text
RelationshipDetail
    id
    relationship_definition_id
    relationship_definition_version
    properties
    <runtime-cell collection>[]
        name
        from_object
            id
            canonical_name
        to_object
            id
            canonical_name
```

The exact public field name of the runtime-cell collection remains OPEN. This checkpoint ratifies the collection semantics and item content, not whether the final label is `cells`, `perspectives`, or another name.

One public nested item corresponds exactly to one persisted `runtime_relationship_cells` row:

```text
runtime_relationship_cells
    from_object_id
    name
    to_object_id
```

with current Object display metadata added live:

```text
from_object
    id             <- runtime_relationship_cells.from_object_id
    canonical_name <- objects.canonical_name

to_object
    id             <- runtime_relationship_cells.to_object_id
    canonical_name <- objects.canonical_name

name               <- runtime_relationship_cells.name
```

There is:

```text
NO resolution_id
NO autonomous runtime-item identity beyond the semantic cell itself
NO exact-row deduplication
NO model-plane RelationshipDefinition reconstruction
NO relationship_definition_space read
NO relationship_resolutions join
NO ObjectTemplate ancestry read
NO RDV/DataType semantic recertification
```

The `relationship_definition_id`, exact version pin and factual `properties` remain root state read from `relationships`; they are not repeated inside each runtime item.

Object `canonical_name` remains current mutable display state and is therefore projected live from `objects`, not copied into `runtime_relationship_cells`.

### One-statement target

The normal GET remains one authoritative PostgreSQL business statement conceptually rooted as:

```text
relationships AS r
    LEFT JOIN enriched_runtime_cells AS c

where enriched_runtime_cells is:

runtime_relationship_cells AS c
    INNER JOIN objects AS from_object
    INNER JOIN objects AS to_object
```

The former model-plane join used only to retrieve `RelationshipResolution.name` is eliminated because `name` is now intrinsic stable data-plane semantic state.

### Trusted-state and failure boundary

The pre-freeze trusted-read rule survives:

```text
no relationships root row
    -> 404 resource_not_found

relationships root exists but no runtime cell is visible
    -> persisted factual invariant corruption
    -> 500 internal_error
```

The GET does not re-derive the expected closure from model-plane semantics to prove completeness. Complete/all-or-nothing closure certification remains a write-side invariant; the GET trusts persisted current factual state and only detects impossible structural absence exposed by its legal projection path.

`properties` is returned as persisted factual JSON state without schema/DataType revalidation or re-canonicalization.

The normal read concurrency model remains one PostgreSQL statement snapshot with no explicit locks, generation token, retry loop or multi-statement coherent-read wrapper.

### Still OPEN before final GET closure

```text
exact public name for the nested runtime-cell collection
deterministic operational ordering, if retained
index sufficiency / covering-index performance handoff after ordering is known
```

This checkpoint supersedes the old Resolution-based global GET item shape and the old `relationship_resolutions` name join while preserving the previously ratified lossless-global-detail objective and live Object canonical-name projection.

## 14.5 RATIFIED — global GET collection label is `perspectives`

The public nested collection in the global factual Relationship GET is named:

```text
perspectives
```

RATIFIED response shape:

```text
RelationshipDetail
    id
    relationship_definition_id
    relationship_definition_version
    properties
    perspectives[]
        name
        from_object
            id
            canonical_name
        to_object
            id
            canonical_name
```

`perspectives` describes the oriented semantic projections exposed by the factual Relationship without implying autonomous item identity and without leaking the physical `runtime_relationship_cells` table name into the HTTP contract.

This checkpoint supersedes the OPEN collection-label marker in section 14.4. It does not change the already-ratified one-runtime-cell-to-one-public-item mapping, lossless semantics, or lack of public/domain ordering meaning.

Remaining global-GET closure points are now:

```text
deterministic operational ordering, if retained
index sufficiency / covering-index performance handoff after ordering is known
```

## 14.6 RATIFIED — deterministic operational ordering is not a public contract property

The global GET implementation may emit `perspectives[]` in deterministic operational order using the ratified runtime semantic-cell tuple:

```text
from_object_id
name
to_object_id
```

Conceptually:

```text
ORDER BY
    from_object_id,
    name,
    to_object_id
```

This ordering exists only for implementation reproducibility, stable tests/diffs and operational predictability. It introduces no additional Relationship semantics and requires no model-plane read or reconstruction.

RATIFIED public boundary:

```text
perspectives[]
    -> complete lossless collection
    -> no public/domain ordering meaning
    -> array position is not part of the API contract
    -> clients must not depend on the emitted position/order
```

Therefore the exact operational tuple is **not exposed as a public contract property**. The server remains free to change the internal deterministic ordering in a later implementation/optimization without changing the public API, provided collection completeness and item semantics are preserved.

In particular, the GET does not attempt to recover or expose an `A -> B / B -> A` ordering from `RelationshipDefinition`; doing so would reintroduce model-plane work solely for presentation with no additional data-plane meaning.

The remaining global-GET closure point is now limited to:

```text
index sufficiency / covering-index performance handoff
```

## 14.7 RATIFIED — global GET owner index and post-definition technical closure

The global factual Relationship GET enters the runtime child by factual owner identity:

```text
relationship_id
```

The ratified semantic-cell uniqueness key:

```text
(from_object_id, name, to_object_id)
```

is the authoritative global conflict/ownership identity, but its leading column does not support the root-relative access pattern used by:

```text
GET /api/v1/core/relationships/{relationship_id}
```

M4 therefore ratifies a dedicated runtime-child owner access path:

```text
INDEX runtime_relationship_cells (relationship_id)
```

This is a data-plane access index only. It does not add semantic identity and does not change the fact that `relationship_id` is ownership/grouping state rather than part of the semantic-cell key.

No wider covering/order-preserving index such as:

```text
(relationship_id, from_object_id, name, to_object_id)
```

is required by the M4 architecture for the global GET. The owner slice is small, operational perspective ordering is not a public API property, and the read must still join the endpoint `objects` rows to obtain current `canonical_name`. A wider covering index may be reconsidered only from measured workload evidence; it is not part of the ratified logical/physical baseline.

The expected normal access path is therefore:

```text
relationships primary-key lookup by id
    -> runtime_relationship_cells INDEX (relationship_id)
    -> objects primary-key lookup for from_object
    -> objects primary-key lookup for to_object
```

No model-plane access is introduced.

### Global GET post-definition closure

The global factual Relationship GET is now **CLOSED** again for the M4 discovery pass.

Ratified post-definition result:

```text
GET /api/v1/core/relationships/{relationship_id}

RelationshipDetail
    id
    relationship_definition_id
    relationship_definition_version
    properties
    perspectives[]
        name
        from_object { id, canonical_name }
        to_object   { id, canonical_name }
```

with:

```text
complete lossless runtime-cell projection
one public perspective per runtime semantic cell
no resolution_id
semantic name read directly from runtime_relationship_cells
Object canonical names joined live
no model-plane read/reconstruction
one authoritative PostgreSQL statement snapshot
root absent -> 404
root present but no runtime cell visible -> 500 persisted-invariant corruption
optional deterministic operational order only; no public ordering contract
runtime child owner access through INDEX (relationship_id)
no required covering index
```

This closure supersedes earlier `ACTIVE REVALIDATION` / `remaining global-GET closure point` markers in this WIP wherever they refer to the post-definition global GET.

Current factual Relationship review frontier is now:

```text
GET /api/v1/core/objects/{object_id}/relationships
    -> revalidate Object-scoped navigation semantics and projection against runtime_relationship_cells
    -> revalidate filters/pagination only where old Resolution assumptions mattered
    -> revalidate Object-rooted access path/index shape
```

After the Object-scoped GET revalidation, the factual CREATE selector remains the next reopened public-contract dependency because `resolution_id` no longer exists.

## 14.8 RATIFIED — Object-scoped runtime-cell projection is one-to-one

The post-definition Object-scoped Relationship collection is rooted directly in the factual runtime semantic cells:

```text
GET /api/v1/core/objects/{object_id}/relationships

runtime_relationship_cells
    WHERE from_object_id = object_id
```

RATIFIED mapping:

```text
one matching runtime_relationship_cells row
    -> exactly one Object-scoped public Relationship item
```

No additional grouping or deduplication layer is required between the persisted runtime relation and the Object-relative public projection.

The reason is structural rather than an implementation shortcut. The ratified global semantic-cell uniqueness authority is:

```text
(from_object_id, name, to_object_id)
```

so two current runtime rows cannot independently express the same exact Object-relative semantic cell:

```text
(object_id, name, destination_object_id)
```

The old M4 deduplication requirement was a consequence of the former Resolution/inheritance-expanded runtime model, where multiple exact `runtime_relationship_resolutions` rows could collapse to the same Object-relative public view. That premise is superseded by `runtime_relationship_cells`.

Examples:

```text
Alice friend_of Bob
Bob   friend_of Alice

GET /objects/Alice/relationships
    -> matches only (Alice, friend_of, Bob)
    -> one item
```

```text
Alice friend_of Alice

GET /objects/Alice/relationships
    -> matches the single self-loop runtime cell
    -> one item
```

```text
VM1 runs_on H1
H1  hosts    VM1

GET /objects/VM1/relationships
    -> matches only (VM1, runs_on, H1)
    -> one item
```

This read remains data-plane trusted-state projection. It does not reconstruct Definition topology or re-certify why the runtime cell exists.

This checkpoint supersedes the pre-freeze technical baseline statement that Object-scoped projection must deduplicate multiple runtime Resolution rows before pagination.

Current next micro-point:

```text
GET /api/v1/core/objects/{object_id}/relationships
    -> revalidate exact ObjectRelationshipItem shape against the 1:1 runtime-cell mapping
```

---

# Post-definition continuation checkpoints

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

## C-REL-29 RATIFIED — DATA_CHANGE lifecycle snapshot excludes revision and fans out one-to-one with runtime semantic cells

A real factual Relationship DATA_CHANGE preserves the historical Relationship factual snapshot shape already established by the lifecycle contract:

```text
before_state = {
    relationship_definition_version: V,
    properties: P_before
}

after_state = {
    relationship_definition_version: V,
    properties: P_after
}
```

with:

```text
P_before != P_after
```

A cheaply recognized semantic no-op emits no lifecycle event, so a persisted `RELATIONSHIP_DATA_CHANGE` transition always represents a real factual property-state change while keeping the exact RelationshipDefinitionVersion pin unchanged.

The technical factual-root generation token does not enter historical semantic state:

```text
relationships.revision
    -> private current-state freshness / CAS metadata
    -> NOT part of before_state
    -> NOT part of after_state
```

Historical lifecycle snapshots therefore remain about semantic factual state rather than the implementation generation used to protect a write.

The stable post-definition runtime closure is already stored directly as exact Object-relative semantic cells:

```text
runtime_relationship_cells
    relationship_id
    from_object_id
    name
    to_object_id
```

DATA_CHANGE does not mutate that closure. Therefore lifecycle fan-out is directly:

```text
one runtime_relationship_cells row
    -> one RELATIONSHIP_DATA_CHANGE event row
```

No Resolution-derived projection or semantic-view deduplication stage remains necessary.

RATIFIED event-set cardinality matches the persisted factual closure exactly:

```text
asymmetric
    -> 2 RELATIONSHIP_DATA_CHANGE event rows

symmetric disjoint-space
    -> 2 rows

symmetric same-space with distinct Objects
    -> 2 rows

symmetric same-space self-loop
    -> 1 row
```

Each event row carries the Object-relative semantic metadata of its exact runtime cell:

```text
relationship_id
relationship_definition_id

object_id
    <- runtime_relationship_cells.from_object_id

relationship_name
    <- runtime_relationship_cells.name

destination_object_id
    <- runtime_relationship_cells.to_object_id

canonical_name
destination_canonical_name
    <- coherent historical Object display observations captured for this transition
```

`relationship_name` is the stable semantic name persisted in the runtime cell. There is no RelationshipResolution read and no mutable relationship-name lookup.

The historical endpoint `canonical_name` values remain Object-owned display observations. All endpoint names captured for one Relationship transition must come from one coherent observation boundary; the writer must not assemble one event set from incompatible independently observed Object generations. The exact SQL/projection mechanism used to achieve that coherence remains architecture work.

For the real-write branch, C-REL-27 and this lifecycle boundary compose as:

```text
observed factual generation R
+
P_before
+
validated canonical P_after
+
expected_revision = R

successful commit:
    relationships.properties := P_after
    relationships.revision := R + 1
    +
    complete RELATIONSHIP_DATA_CHANGE event set
        every row carries identical before_state / after_state
    -> one atomic COMMIT
```

Any failure before that commit leaves:

```text
properties unchanged
revision unchanged
no RELATIONSHIP_DATA_CHANGE event row from the failed attempt
```

A revision mismatch is likewise a stale internal attempt and emits no lifecycle transition before bounded retry from a fresh factual generation.

DATA_CHANGE lifecycle construction does not reopen model-plane or runtime-topology validation:

```text
NO RelationshipResolution read
NO semantic-view deduplication
NO RelationshipDefinition topology read
NO relationship_definition_space read
NO ObjectTemplate ancestry read
NO runtime closure reconstruction or semantic re-proof
NO revision in historical factual snapshots
```

Exact projection statement shape, sequencing around the final CAS/write, batch INSERT realization and physical lifecycle-table details remain architecture-closing work.

Current next micro-point:

```text
Relationship DATA_CHANGE
    -> assess post-definition DATA_CHANGE discovery closure
       and enumerate only any decisions intentionally deferred to architecture closing
```

## C-REL-30 RATIFIED — post-definition Relationship DATA_CHANGE discovery is complete

The post-definition factual/domain discovery pass for:

```text
POST /api/v1/core/relationships/{relationship_id}/properties
```

is complete.

Current status is:

```text
DISCOVERY COMPLETE
PUBLIC CONTRACT CLOSED
ARCHITECTURE CLOSING PENDING
```

The already-ratified public contract remains unchanged:

```text
path:
    relationship_id: UUID, required

query:
    none

body:
    operations: PropertyOperation[1..N]
    SET    { op, property, value }
    REMOVE { op, property }
    same property at most once
    array order has no mutation-order meaning
    atomic / no partial success

success:
    204 No Content
    no body

no-op:
    204 No Content
    cheaply recognized no-op may elide root UPDATE and DATA_CHANGE lifecycle

failures:
    malformed/static request
        -> 400 invalid_request

    missing Relationship
        -> 404 resource_not_found

    invalid requested property effect/value
        -> 422 semantic_validation_failed

    persisted invariant/infrastructure or bounded stabilization failure
        -> 500 internal_error

    no normal 409
```

Post-definition execution semantics are now also discovery-complete:

```text
observe current factual generation:
    relationship_definition_id = D
    relationship_definition_version = V
    properties = P
    revision = R

resolve immutable semantic validation snapshot:
    ImmutableRelationshipDefinitionVersionCache[(D, V)]

cache miss:
    full exact D@V load
    + complete declarations
    + every exact referenced DataTypeVersion semantic dependency
    -> one resolved immutable validation snapshot

validate/canonicalize candidate:
    against that resolved exact snapshot

real mutation:
    properties := P_after
    revision := R + 1
    complete RELATIONSHIP_DATA_CHANGE event set
    -> atomic commit against expected_revision = R
```

DATA_CHANGE performs no new model-plane admission and is invariant to lifecycle status of the already-pinned exact schema:

```text
NO RelationshipDefinition.default_version read
NO RDV PUBLISHED/default/latest admission
NO DataTypeVersion lifecycle admission
NO dependency_not_admissible outcome
```

It also performs no factual topology recertification:

```text
NO RelationshipResolution read
NO RelationshipDefinition topology re-proof
NO relationship_definition_space read
NO ObjectTemplate ancestry read
NO runtime semantic-closure reconstruction
NO semantic-view deduplication
```

The lifecycle boundary remains:

```text
before_state = {
    relationship_definition_version: V,
    properties: P_before
}

after_state = {
    relationship_definition_version: V,
    properties: P_after
}

relationships.revision
    -> private technical generation state
    -> excluded from historical factual snapshots

one runtime_relationship_cells row
    -> one RELATIONSHIP_DATA_CHANGE event row
```

No additional factual DATA_CHANGE capability or semantic/public-contract decision is currently known to be missing.

The remaining work is intentionally architecture/physical realization only:

```text
exact semantic-cache implementation and process topology
cache capacity / eviction / warm-up policy
exact cache-miss PostgreSQL statement and batching realization
relationships.revision type / CHECK / default DDL details
exact CAS and PostgreSQL row-lock/wait realization
bounded retry count / backoff policy
coherent endpoint canonical_name projection mechanism
lifecycle batch INSERT and DML sequencing
```

Those decisions must preserve the ratified public/factual semantics and must not reopen DATA_CHANGE merely to choose an implementation mechanism.

Current factual Relationship review frontier moves to:

```text
POST /api/v1/core/relationships/{relationship_id}/schema
    -> post-definition SCHEMA_CHANGE revalidation
```

## C-REL-31 RATIFIED — Relationship SCHEMA_CHANGE inherits the M4 Object SCHEMA_CHANGE execution pattern by delta

Relationship SCHEMA_CHANGE does not define an independent execution architecture from first principles. M4 ratifies the already-full-swept Object SCHEMA_CHANGE design as the baseline pattern and requires Relationship SCHEMA_CHANGE to reuse that pattern wherever the two domains are semantically equivalent.

The governing review rule is:

```text
Object SCHEMA_CHANGE full sweep
    -> baseline

Relationship SCHEMA_CHANGE
    -> preserve shared patterns
    -> remove Object-only concerns
    -> introduce a divergence only when a concrete Relationship-domain requirement justifies it
```

This delta-oriented rule prevents repeated reinvention of patterns already analyzed and keeps analogous versioned factual mutations architecturally coherent.

For Relationship factual state:

```text
SOURCE = D@VS
TARGET = D@VT

current factual generation:
    relationship_definition_id = D
    relationship_definition_version = VS
    properties = P
    revision = R
```

The shared Object-derived three-stage execution skeleton is RATIFIED.

```text
STEP 1 — authoritative current-generation observation

    read one coherent factual Relationship generation:
        relationship_definition_id = D
        source_version = VS
        properties = P
        revision = R

    the same bounded current-state read may also observe
    requested distinct TARGET D@VT existence/current status
    without requiring a standalone preliminary TARGET round trip

    Relationship absent
        -> 404 resource_not_found

    VT == VS
        -> 204 semantic no-op
        -> no MigrationPlan work
        -> no final mutation UoW
        -> no revision increment
        -> no SCHEMA_CHANGE lifecycle

    VT != VS + TARGET absent
        -> 422 referenced_resource_not_found

    VT != VS + TARGET currently non-PUBLISHED
        -> 409 dependency_not_admissible
```

The early TARGET observation is only an early current-state filter. A successful real distinct-target mutation still requires final TARGET PUBLISHED admission/protection through commit.

```text
STEP 2 — immutable exact-pair semantic preparation

    obtain/build READY RelationshipDefinitionMigrationPlan(D, VS, VT)

    apply the plan to current properties P

    derive:
        complete canonical target_properties
        concrete semantic migration blocker, if any
        lifecycle before/after factual transition inputs

    build one prepared candidate carrying:
        relationship_id
        relationship_definition_id = D
        source_version = VS
        target_version = VT
        expected_revision = R
        target_properties
        lifecycle transition inputs
```

The exact-pair migration plan is immutable and factual-Relationship-independent:

```text
RelationshipDefinitionMigrationPlan(D, VS, VT)
    = f(
        ImmutableRelationshipDefinitionVersionCache[(D, VS)],
        ImmutableRelationshipDefinitionVersionCache[(D, VT)]
      )
```

Conceptual reusable cache:

```text
RelationshipDefinitionMigrationPlanCache[(D, VS, VT)]
```

A READY plan may contain compiled immutable SOURCE/TARGET property-continuity, shape-transformation and TARGET validation/canonicalization rules. It must not contain one factual Relationship's mutable:

```text
properties
revision
current TARGET lifecycle status
runtime_relationship_cells
endpoint Object state
```

Plan resolution follows the same READY path as Object SCHEMA_CHANGE:

```text
HIT
    -> consume exact-pair plan

MISS
    -> make required exact SOURCE/TARGET RDV semantic snapshots READY
       using the C-REL-28 full resolved immutable cache boundary
    -> compile/cache exact-pair plan
    -> consume plan
```

Thus cold Relationship planning reuses the existing immutable exact-RDV snapshot cache rather than reconstructing model semantics through a one-off SCHEMA_CHANGE path.

```text
STEP 3 — short real-migration mutation UoW

    final protected exact D@VT PUBLISHED admission
    + require current relationships.revision == expected_revision R
    + atomically persist:
        relationships.relationship_definition_version := VT
        relationships.properties := complete target_properties
        relationships.revision := R + 1
        complete RELATIONSHIP_SCHEMA_CHANGE lifecycle event set
    -> COMMIT
```

No cache fill, MigrationPlan compilation, SOURCE/TARGET schema comparison, property transformation or TARGET value validation belongs inside the final protected path.

The same universal C-REL-27 retry rule is inherited from Object SCHEMA_CHANGE:

```text
revision mismatch
    -> stale internal attempt
    -> no mutation/lifecycle from that attempt
    -> bounded fresh retry from STEP 1

fresh SOURCE == previous SOURCE
    -> reuse READY MigrationPlan(D, SOURCE, TARGET)
    -> reapply to fresh properties

fresh SOURCE != previous SOURCE
    -> old exact-pair plan is not applicable
    -> resolve/build MigrationPlan(D, fresh_SOURCE, requested_TARGET)

fresh SOURCE == requested TARGET
    -> 204 semantic no-op
    -> no new mutation/revision/lifecycle

bounded retry exhaustion
    -> 500 internal_error
```

The authority split is likewise inherited:

```text
PostgreSQL/current-state authority
    current factual Relationship generation
    distinct TARGET existence
    distinct TARGET current PUBLISHED admission
    final TARGET PUBLISHED protection through binding commit
    revision freshness
    atomic persistence

immutable semantic caches
    exact SOURCE/TARGET resolved RDV semantics
    exact-pair migration relation / reusable MigrationPlan
```

Cache presence never proves current TARGET admission.

Relationship SCHEMA_CHANGE is a strict simplification of Object SCHEMA_CHANGE. The following Object-specific concerns are absent from Relationship migration and must not be recreated speculatively:

```text
NO ObjectTemplate inheritance/effective-schema traversal
NO stable ancestry cache
NO component-slot migration matrix
NO object_component_slots delta
NO object_components child/membership scan
NO slot target narrowing/unrelated analysis
NO edge -> slot FK migration blocker/arbitration
NO ownership graph work
```

Likewise, the post-RelationshipDefinition redesign leaves factual runtime semantic closure stable across SCHEMA_CHANGE:

```text
runtime_relationship_cells
    -> unchanged
    -> no reconstruction
    -> no topology recertification
```

The exact public Relationship SCHEMA_CHANGE contract remains the already-ratified one: exact target, numeric direction without admission meaning, equal-target no-op, distinct TARGET PUBLISHED admission, direct SOURCE -> TARGET migration and bounded domain failure classes.

This checkpoint ratifies the shared execution/pattern baseline and the delta-only review method. It does not yet freeze the Relationship-specific property migration matrix, lifecycle fan-out details or physical SQL/locking/cache realization.

Current next micro-point:

```text
Relationship SCHEMA_CHANGE
    -> derive the Relationship property migration matrix
       from the already-ratified Object SCHEMA_CHANGE matrix
       by removing Object-only required/migration_default/inheritance/component semantics
```

## C-REL-32 RATIFIED — Relationship SCHEMA_CHANGE property migration matrix is target-oriented and preservation-or-block

Relationship SCHEMA_CHANGE inherits the already-ratified Object SCHEMA_CHANGE property-migration discipline and removes the Object-only required/default/inheritance branches.

Historical semantic identity for a Relationship property is:

```text
RelationshipPropertySemanticKey
    = (relationship_definition_id, name)
```

Within one RelationshipDefinition, remove/re-add of the same property name preserves the same historical semantic identity and does not reset evolution constraints. `position` is presentation/order state and does not participate in migration identity.

The exact-pair `RelationshipDefinitionMigrationPlan(D, VS, VT)` is target-oriented:

```text
target_properties = {}

for each TARGET semantic property:
    identify the matching SOURCE semantic property, if any
    derive the TARGET candidate from current SOURCE factual information
    validate/canonicalize the candidate under TARGET exact semantics
```

Canonical cases are:

```text
TARGET-only property
    -> absent

SOURCE-only property
    -> omitted from TARGET factual state

continuous property + SOURCE value absent
    -> absent

continuous property + SOURCE value present
    -> preserve all factual information
    -> apply only the exact shape transformation required by SOURCE/TARGET modes
    -> validate/canonicalize under TARGET exact DataTypeVersion semantics
    -> incompatibility blocks the migration
```

Relationship properties have no:

```text
required
nullable factual state
create default
migration_default
```

so no Object-style requiredness/default branch exists and no model-plane default may invent factual Relationship data during migration.

The SCALAR/LIST matrix is inherited from Object exact-pair migration where applicable.

```text
SCALAR -> SCALAR
    SOURCE x
        -> x
        -> validate/canonicalize under TARGET exact DTV

LIST -> LIST
    SOURCE [x, y, ...]
        -> preserve order and multiplicity
        -> validate/canonicalize every item under TARGET exact DTV

SCALAR -> LIST
    SOURCE x
        -> [x]
        -> TARGET validation/canonicalization
```

The delivered AS-IS model-plane publication-history rule allowed only `SCALAR -> LIST`. The current M4 RelationshipDefinition reviewed baseline instead permits both `SCALAR -> LIST` and `LIST -> SCALAR` when defining a valid exact RDV.

Factual `Relationship.SCHEMA_CHANGE` remains a separate preserve-or-block decision over one concrete current factual state. A TARGET SCALAR exact version may therefore be valid at model-plane level while migration of a factual multi-item LIST value to that TARGET remains blocked because it would require information loss. Numeric version direction has no runtime migration-admission meaning.

RATIFIED conditional lossless rule:

```text
LIST -> SCALAR

SOURCE property absent
    -> TARGET property absent

SOURCE value = [x]
    -> TARGET candidate x
    -> validate/canonicalize under TARGET exact DTV

SOURCE list cardinality > 1
    -> information loss would be required
    -> 409 schema_change_blocked
```

Cardinality is literal:

```text
[x, x]
    -> two items
    -> not lossless
    -> schema_change_blocked
```

SCHEMA_CHANGE never performs:

```text
first-item selection
last-item selection
arbitrary item selection
deduplicate-then-collapse
drop incompatible existing information merely because TARGET permits absence
replacement of incompatible information with a default
```

For one continuous semantic property, the stable `datatype_id` lineage is preserved by model-plane publication history while the exact `datatype_version` may differ between SOURCE and TARGET.

Therefore:

```text
existing factual information
    -> preserve
    -> apply the required SCALAR/LIST shape transformation
    -> validate/canonicalize against TARGET exact DataTypeVersion
```

If the concrete value is not representable under TARGET exact constraints:

```text
-> 409 schema_change_blocked
```

No cross-DataType-lineage or cross-PrimitiveType conversion is invented by factual migration. If supposedly certified immutable SOURCE/TARGET RDV semantics violate the model-plane historical identity/evolution invariants, the runtime observes persisted certification corruption:

```text
-> 500 internal_error
```

not a normal factual migration class.

Intermediate versions are irrelevant to runtime planning. Example:

```text
D@1: property p present
D@2: property p absent
D@3: property p present
```

A direct `D@1 -> D@3` plan treats `p` as one continuous semantic property because `(D, p)` is its historical identity. The operation does not replay D@2 and does not walk publication history at runtime.

Unlike Object SCHEMA_CHANGE, Relationship SCHEMA_CHANGE has no component/structural exact-pair relation that can make an otherwise certified pair categorically non-migrable before considering factual state.

Accordingly, for same-Definition certified immutable RDV pairs:

```text
pair semantics coherent + concrete factual state migrable
    -> produce canonical TARGET candidate

pair semantics coherent + concrete current information not losslessly representable
    -> 409 schema_change_blocked

supposedly certified pair semantics internally incoherent
    -> 500 internal_error
```

No additional normal `422 semantic_validation_failed` pair-class is introduced for Relationship SCHEMA_CHANGE. This preserves the already-closed Relationship SCHEMA_CHANGE public failure catalog.

The MigrationPlan may precompile all immutable continuity, SOURCE/TARGET value-mode transformation and TARGET exact-validation rules. Applying that plan to one factual Relationship is the only step that decides concrete `schema_change_blocked` outcomes.

Current next micro-point:

```text
Relationship SCHEMA_CHANGE
    -> revalidate RELATIONSHIP_SCHEMA_CHANGE lifecycle fan-out / factual snapshot boundary
       against stable runtime_relationship_cells and relationships.revision
```

## C-REL-33 RATIFIED — SCHEMA_CHANGE lifecycle uses exact factual snapshots, 1:1 runtime-cell fan-out, and non-equal version transition semantics

A real factual Relationship SCHEMA_CHANGE preserves the established Relationship lifecycle snapshot contract rather than adopting the Object-specific delta payload shape.

For a prepared and successfully committed exact migration:

```text
SOURCE
    relationship_definition_version = VS
    properties = P_before
    revision = R

TARGET
    relationship_definition_version = VT
    properties = P_after
```

with:

```text
VT != VS
```

the canonical historical factual transition is:

```text
before_state = {
    relationship_definition_version: VS,
    properties: P_before
}

after_state = {
    relationship_definition_version: VT,
    properties: P_after
}
```

`P_before` and `P_after` may be equal. A distinct exact-version pin is itself a real factual schema transition and therefore produces `RELATIONSHIP_SCHEMA_CHANGE` even when canonical property state is unchanged.

The technical factual-root generation token remains excluded from historical semantic state:

```text
relationships.revision
    -> private freshness / CAS metadata
    -> NOT part of before_state
    -> NOT part of after_state
```

The post-definition factual runtime semantic closure is stable across SCHEMA_CHANGE:

```text
runtime_relationship_cells
    relationship_id
    from_object_id
    name
    to_object_id
```

Therefore lifecycle fan-out is directly:

```text
one runtime_relationship_cells row
    -> one RELATIONSHIP_SCHEMA_CHANGE event row
```

with no Resolution-derived projection or semantic-view deduplication stage.

RATIFIED event-set cardinality matches the persisted closure exactly:

```text
asymmetric
    -> 2 RELATIONSHIP_SCHEMA_CHANGE event rows

symmetric disjoint-space
    -> 2 rows

symmetric same-space with distinct Objects
    -> 2 rows

symmetric same-space self-loop
    -> 1 row
```

Each event row carries the Object-relative semantic metadata of its exact runtime cell:

```text
relationship_id
relationship_definition_id

object_id
    <- runtime_relationship_cells.from_object_id

relationship_name
    <- runtime_relationship_cells.name

destination_object_id
    <- runtime_relationship_cells.to_object_id

canonical_name
destination_canonical_name
    <- coherent historical Object display observations captured for this transition
```

`relationship_name` is stable semantic state persisted directly in the runtime cell. There is no RelationshipResolution read and no mutable relationship-name lookup.

Endpoint `canonical_name` values remain historical Object display observations and must be captured from one coherent transition observation boundary. Exact projection/statement realization remains architecture work.

For the real-write branch, C-REL-27/C-REL-31 compose with this lifecycle boundary as:

```text
final TARGET PUBLISHED admission
+
expected_revision = R
+
relationships.relationship_definition_version := VT
relationships.properties := P_after
relationships.revision := R + 1
+
complete RELATIONSHIP_SCHEMA_CHANGE event set
    every row carries identical before_state / after_state

-> one atomic COMMIT
```

Any failed/blocked/stale attempt leaves:

```text
source pin unchanged
source properties unchanged
revision unchanged
runtime_relationship_cells unchanged
no RELATIONSHIP_SCHEMA_CHANGE event row from that attempt
```

This includes:

```text
TARGET absent/inadmissible
schema_change_blocked
revision mismatch before successful retry
persistence/lifecycle failure causing rollback
```

Equal-target semantics remain:

```text
VT == VS
    -> 204 No Content
    -> no MigrationPlan work
    -> no root UPDATE
    -> no revision increment
    -> no RELATIONSHIP_SCHEMA_CHANGE lifecycle
```

M4 explicitly supersedes the historical forward-only lifecycle transition invariant.

The old decoder/persistence rule:

```text
RELATIONSHIP_SCHEMA_CHANGE
    after.relationship_definition_version
        > before.relationship_definition_version
```

is no longer valid because M4 exact-target semantics permit a real migration to an exact numerically lower PUBLISHED target.

RATIFIED lifecycle invariant becomes:

```text
RELATIONSHIP_SCHEMA_CHANGE
    before != null
    after != null
    before.relationship_definition_version
        != after.relationship_definition_version
```

No `>` or `<` ordering relation between the two exact version numbers has lifecycle meaning.

Example:

```text
before.version = 5
after.version  = 3
```

is a valid historical `RELATIONSHIP_SCHEMA_CHANGE` when `D@3` was an admitted exact target and the factual state migrated successfully.

Lifecycle reads/decoders must therefore validate distinctness of the exact pin rather than forward numeric direction. This change is required by the already-ratified public exact-target contract and is not a new migration capability.

SCHEMA_CHANGE lifecycle construction performs no:

```text
RelationshipResolution read
semantic-view deduplication
RelationshipDefinition topology read
relationship_definition_space read
ObjectTemplate ancestry read
runtime closure reconstruction
revision persistence inside historical factual snapshots
```

Exact coherent canonical-name projection, event batch insertion, SQL/CAS sequencing and physical lifecycle-table checks remain architecture-closing work.

Current next micro-point:

```text
Relationship SCHEMA_CHANGE
    -> assess post-definition SCHEMA_CHANGE discovery closure
       against the already-closed public contract and the ratified Object-derived execution baseline
```

## C-REL-34 RATIFIED — post-definition Relationship SCHEMA_CHANGE discovery is complete

The post-definition factual/domain discovery pass for:

```text
POST /api/v1/core/relationships/{relationship_id}/schema
```

is complete.

Current status is:

```text
DISCOVERY COMPLETE
PUBLIC CONTRACT CLOSED
ARCHITECTURE CLOSING PENDING
```

The already-ratified public contract remains unchanged:

```text
path:
    relationship_id: UUID, required

query:
    none

body:
    target_version: positive integer, required

semantics:
    exact TARGET within the current stable RelationshipDefinition
    numeric version direction has no migration-admission meaning
    no intermediate-version replay

success:
    204 No Content
    no body

equal TARGET:
    204 No Content
    no MigrationPlan
    no root UPDATE
    no revision increment
    no SCHEMA_CHANGE lifecycle

distinct TARGET:
    exact TARGET must exist and remain PUBLISHED through commit
    direct SOURCE -> TARGET migration
    preserve current information where losslessly representable

failures:
    malformed/static request
        -> 400 invalid_request

    missing Relationship
        -> 404 resource_not_found

    missing distinct TARGET
        -> 422 referenced_resource_not_found

    non-PUBLISHED distinct TARGET
        -> 409 dependency_not_admissible

    concrete factual information not losslessly representable
        -> 409 schema_change_blocked

    persisted certification/infrastructure or bounded stabilization failure
        -> 500 internal_error
```

Relationship SCHEMA_CHANGE inherits the already-full-swept Object SCHEMA_CHANGE execution architecture by delta rather than defining a parallel pattern.

Canonical execution boundary is:

```text
STEP 1 — authoritative current-generation observation
    relationship_definition_id = D
    source_version = VS
    properties = P
    revision = R
    + optional early distinct TARGET existence/status observation

STEP 2 — immutable exact-pair semantic preparation
    RelationshipDefinitionMigrationPlanCache[(D, VS, VT)]
        built/reused from fully resolved immutable exact-RDV semantic snapshots

    apply plan to P
        -> complete canonical target_properties
        OR
        -> 409 schema_change_blocked

STEP 3 — short real-migration UoW
    final protected TARGET PUBLISHED admission
    + expected_revision = R freshness
    + relationship_definition_version := VT
    + properties := target_properties
    + revision := R + 1
    + complete RELATIONSHIP_SCHEMA_CHANGE event set
    -> one atomic COMMIT
```

The migration plan is immutable and reusable for one exact pair:

```text
RelationshipDefinitionMigrationPlan(D, VS, VT)
    = f(
        ImmutableRelationshipDefinitionVersionCache[(D, VS)],
        ImmutableRelationshipDefinitionVersionCache[(D, VT)]
      )
```

Cache presence never proves current TARGET admission. PostgreSQL remains authority for current TARGET existence/PUBLISHED status, final protection through binding commit, factual generation freshness and atomic persistence.

The Relationship property migration matrix is target-oriented and preservation-or-block:

```text
RelationshipPropertySemanticKey
    = (relationship_definition_id, name)

TARGET-only property
    -> absent

SOURCE-only property
    -> removed from TARGET state

continuous property + SOURCE value absent
    -> absent

continuous property + SOURCE value present
    -> preserve information
    -> apply SOURCE/TARGET value-mode transformation
    -> validate/canonicalize under TARGET exact DTV
    -> incompatibility => 409 schema_change_blocked
```

Supported exact-pair factual shape handling is:

```text
SCALAR -> SCALAR
LIST   -> LIST
SCALAR -> LIST

LIST -> SCALAR
    absent -> absent
    [x]    -> x + TARGET validation/canonicalization
    cardinality > 1 -> 409 schema_change_blocked
```

Relationship properties have no required/default/migration-default branch, and Relationship SCHEMA_CHANGE has no Object-style component/inheritance structural pair blocker. Therefore no additional normal categorical `422 semantic_validation_failed` pair class is introduced.

For supposedly certified immutable SOURCE/TARGET semantics:

```text
coherent pair + migrable factual state
    -> canonical TARGET candidate

coherent pair + concrete information not losslessly representable
    -> 409 schema_change_blocked

certification contradiction / corrupt immutable semantic state
    -> 500 internal_error
```

No historical publication walk, intermediate-version replay or runtime topology re-proof belongs to SCHEMA_CHANGE preparation.

The universal factual-root generation protocol remains:

```text
revision mismatch
    -> stale internal attempt
    -> no mutation / no lifecycle
    -> bounded fresh retry

fresh SOURCE unchanged
    -> reuse exact-pair MigrationPlan and reapply to fresh properties

fresh SOURCE changed
    -> resolve/build plan for the fresh SOURCE and requested TARGET

fresh SOURCE == requested TARGET
    -> 204 semantic no-op

bounded retry exhaustion
    -> 500 internal_error
```

The runtime semantic closure remains unchanged by SCHEMA_CHANGE:

```text
runtime_relationship_cells
    -> stable across migration
    -> no reconstruction
    -> no semantic recertification
```

The lifecycle boundary is:

```text
before_state = {
    relationship_definition_version: VS,
    properties: P_before
}

after_state = {
    relationship_definition_version: VT,
    properties: P_after
}

VS != VT
P_before may equal P_after

relationships.revision
    -> private technical generation state
    -> excluded from historical snapshots

one runtime_relationship_cells row
    -> one RELATIONSHIP_SCHEMA_CHANGE event row
```

M4 supersedes the historical forward-only lifecycle invariant. Lifecycle validation requires only exact-version distinctness:

```text
before.relationship_definition_version
    != after.relationship_definition_version
```

and attaches no `>`/`<` semantic meaning to version numbers.

No additional factual SCHEMA_CHANGE capability or semantic/public-contract decision is currently known to be missing.

Remaining work is intentionally architecture/physical realization only:

```text
exact STEP-1 PostgreSQL carrier
MigrationPlan/cache layout, local fill coordination, capacity/eviction
bounded exact-RDV/DTV semantic-loader realization
final TARGET PUBLISHED protection mechanism
relationships.revision DDL and exact CAS/row-lock/wait realization
bounded retry count/backoff
exact root UPDATE / statement fusion-decomposition
coherent endpoint canonical_name projection
lifecycle batch INSERT sequencing
lifecycle DB/decoder realization of version != rather than >
constraint/SQLSTATE -> public failure translation
physical indexes and EXPLAIN/BUFFERS evidence
JSONB/TOAST/WAL/latency/contention measurements
```

Those decisions must preserve the ratified factual/public semantics and must not reopen SCHEMA_CHANGE merely to choose an implementation mechanism.

Current factual Relationship review frontier moves to:

```text
DELETE /api/v1/core/relationships/{relationship_id}
    -> post-definition DELETE revalidation
```

## C-REL-35 RATIFIED — post-definition Relationship DELETE discovery is complete

```text
DELETE /api/v1/core/relationships/{relationship_id}

DISCOVERY COMPLETE
PUBLIC CONTRACT CLOSED
ARCHITECTURE CLOSING PENDING
```

Public contract remains:

```text
relationship_id UUID required
query none
body none
success -> 204 No Content
absent/repeated DELETE -> 404 resource_not_found / relationship
static invalid request -> 400 invalid_request
unexpected persistence/lifecycle/infrastructure failure -> 500 internal_error
no normal 409 or 422
```

### Root deletion / owned closure

Application explicitly deletes only the factual root:

```text
relationships[id = relationship_id]
```

`runtime_relationship_cells` is owned child state and is removed through the `relationship_id -> relationships.id` FK with `ON DELETE CASCADE`. Application code does not explicitly delete runtime cells.

DELETE consumes the persisted runtime closure only as historical source material. It does not recertify it:

```text
NO expected-cell-count check
NO closure reconstruction
NO RelationshipDefinition / relationship_definition_space read
NO ObjectTemplate ancestry
NO RDV/DataType semantic read
NO semantic cache
```

### Revision

DELETE terminates the current factual generation; it does not prepare a replacement generation:

```text
NO preliminary generation SELECT
NO expected_revision
NO revision CAS
NO revision increment
NO DELETE-owned stabilization retry
```

The factual root row actually deleted is the authoritative DELETE before-state. DATA_CHANGE and SCHEMA_CHANGE remain responsible for their own generation freshness.

### Lifecycle

DELETE is the inverse of CREATE:

```text
RELATIONSHIP_CREATED
    before_state = null
    after_state = { relationship_definition_version, properties }

RELATIONSHIP_DELETED
    before_state = { relationship_definition_version, properties }
    after_state = null
```

`relationships.revision` is excluded from historical factual state.

Each persisted runtime semantic cell supplies one historical DELETE perspective:

```text
relationship_id
relationship_definition_id
object_id              <- from_object_id
relationship_name      <- runtime cell name
destination_object_id  <- to_object_id
canonical_name / destination_canonical_name
    <- one coherent current Object display observation
```

A concurrent Object RENAME may make DELETE observe either old or new committed display names; both are valid, but the complete event set must be internally coherent.

Required atomicity:

```text
relationships root disappearance
+ FK CASCADE of owned runtime cells
+ complete RELATIONSHIP_DELETED event set
-> one atomic COMMIT
```

### Logical target cost

```text
static invalid request -> 0 DB
missing Relationship   -> max 1 PostgreSQL business statement
successful DELETE      -> 1 PostgreSQL business statement + COMMIT
model/cache work        -> 0
revision preparation   -> 0
```

The one statement must be able to consume the factual/runtime/display information required by lifecycle before cascade removes the runtime cells, delete only the root explicitly, persist the DELETE event set and return a minimal result carrier. Exact SQL/SQLAlchemy realization remains architecture work.

### Semantic concurrency

```text
DELETE x DELETE
    one -> 204 + one complete DELETE transition
    other -> 404

DELETE x DATA_CHANGE / SCHEMA_CHANGE
    mutation first -> DELETE removes resulting current generation
    DELETE first -> prepared mutation cannot commit after root disappearance

DELETE x equivalent CREATE
    old fact current -> semantic-cell uniqueness prevents duplicate current fact
    DELETE first -> later CREATE may create new fact Y with new id
    late DELETE(old_id) -> 404 and never affects Y

DELETE x Object.DELETE
    Relationship DELETE first -> endpoint references disappear
    Object DELETE while Relationship remains current -> runtime FK keeps Object alive

DELETE x RelationshipDefinition.DELETE
    Relationship DELETE first -> factual reference released
    Definition DELETE while Relationship remains current -> factual reference blocks deletion
```

Lock modes, waits, FK/UNIQUE rendezvous, ordering and deadlock proof remain architecture-closing work.

### Architecture handoff

Remaining physical decisions:

```text
exact FK / ON DELETE CASCADE DDL
exact one-statement SQL/SQLAlchemy carrier
pre-cascade lifecycle source carrier
server-side vs application-side before_state construction
coherent canonical_name projection
lifecycle batch insert sequencing
lock/wait/FK interaction and deadlock proof
SQLSTATE translation
indexes / EXPLAIN / runtime measurements
```

Architecture must preserve exact-id deletion, root-only explicit DELETE, owned-child cascade, no closure recertification, no model/cache work, no DELETE revision protocol, atomic DELETE history, ABA safety and the one-business-statement target.

### Factual-domain delta discovered during DELETE review — self-reference forbidden

M4 ratifies:

```text
from_object_id != to_object_id
```

A factual Relationship cannot relate an Object to itself.

CREATE behavior:

```text
from_object_id == to_object_id
    -> 422 semantic_validation_failed
    -> rule = self_reference
```

This intentionally supersedes the delivered AS-IS self-loop allowance and the self-loop branches recorded earlier in C-REL-23, C-REL-25, C-REL-29 and C-REL-33.

The invariant is enforced at CREATE/admission/relational-authority boundaries. DELETE and other consumers of current persisted closure do not recertify it.

### Closure

Relationship DELETE is full-sweep complete. No additional factual Relationship route-local discovery point is currently known. Existing architecture-closing items from earlier checkpoints remain open, including the C-REL-26 CREATE Candidate A vs Candidate B selector decision and the global physical/concurrency closure.

---

## C-REL-36 RATIFIED — implicit default resolution freezes the exact RDV selection

For factual `Relationship.CREATE`, omission of `relationship_definition_version` resolves the current `default_version` of the already selected owning RelationshipDefinition. The result of that resolution is one concrete exact binding:

```text
D.default_version = V
    -> selected target = D@V
```

The command remains pinned to `D@V` after resolution. A concurrent later `SET_DEFAULT`, `CLEAR_DEFAULT`, or first-default establishment affects later implicit selections only; it neither retargets the command nor requires the final UoW to prove that the default pointer still equals `V`.

The final CREATE admission continues to require that the selected exact `D@V` exists, belongs to `D`, and remains `PUBLISHED` through the new factual binding commit. It also preserves the already-ratified semantic-cell and runtime-cell arbitration. Default-pointer equality is not a commit predicate.

Consequences:

```text
CLEAR_DEFAULT before resolution
    -> default_version_unavailable

CLEAR_DEFAULT after D@V resolution
    -> D@V remains selected
    -> final exact-target admission decides success

SET_DEFAULT(D@W) before resolution
    -> D@W is selected

SET_DEFAULT(D@W) after D@V resolution
    -> D@V remains selected

first PUBLISH establishes a default before resolution
    -> the new default may be selected

resolution observes NULL before concurrent first PUBLISH
    -> default_version_unavailable may be returned
    -> no mandatory chase/restart loop
```

If `D@V` becomes `DEPRECATED` before final admission, CREATE fails because the exact selected target is no longer admissible, not because the default pointer changed. If CREATE commits first, later deprecation remains allowed because factual pins are not deprecation blockers.

This rule applies identically to both still-open Definition-selection candidates:

```text
candidate A
    explicit relationship_definition_id

candidate B
    owning Definition derived from the exact semantic cell
```

Whichever selector architecture closing chooses, the committed factual root stores the exact `(relationship_definition_id, relationship_definition_version)` pair and never follows future default changes.
