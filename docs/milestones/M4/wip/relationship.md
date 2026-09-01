# M4 — Factual Relationship working owner

**Status:** ACTIVE REVIEW FRONTIER / WIP / NON-NORMATIVE

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
