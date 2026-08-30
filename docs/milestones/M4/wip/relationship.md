# M4 — Factual Relationship working owner

**Status:** ACTIVE REVIEW FRONTIER / WIP / NON-NORMATIVE

## Purpose and ownership

This is the single M4 WIP owner for the factual `Relationship` family.

All route-level factual Relationship discovery, review decisions, data-path findings and open questions must be maintained here instead of creating one WIP file per operation or micro-point. Dedicated files remain appropriate only for genuinely cross-domain owners/support that are not owned by the factual Relationship family.

This WIP remains non-normative under M4 governance: ratified discovery checkpoints recorded here do not authorize implementation until the milestone promotes/finalizes the corresponding TO-BE architecture.

This owner absorbs the previously distributed factual Relationship WIPs for:

```text
CREATE
GET /relationships/{relationship_id}
GET /objects/{object_id}/relationships
DATA_CHANGE
SCHEMA_CHANGE
DELETE
runtime-closure/conflict persistence
Object-relative Relationship API exploration
```

Git history remains the historical source for the absorbed intermediate reasoning.

---

# 1. AS-IS public capability surface

The current factual Relationship API exposes these six capabilities:

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
NO root Relationship collection GET
NO Object-relative single-Relationship detail GET
```

The public/runtime model distinguishes one global factual Relationship from one or more object-relative semantic views of that fact.

A factual Relationship has its own lifetime identity (`relationship_id`). Its persisted runtime closure may expose several public semantic views, including reciprocal views for non-symmetric definitions and multiple views in overlap/self-loop cases.

---

# 2. Ratified M4 API capability checkpoints

These are ratified review decisions for the current M4 discovery pass. They remain non-normative until milestone closure/promotion.

## REL-API-01 — specific Relationship detail is global

The specific factual Relationship is queried outside Object scope:

```text
GET /relationships/{relationship_id}
```

This answers:

```text
what is this factual Relationship globally?
```

The Relationship is a global fact with its own identity. An Object used to navigate to that fact is context, not part of the fact identity.

The global detail may therefore coherently expose the complete factual state, including all distinct public semantic views belonging to the fact.

## REL-API-02 — Object-scoped Relationship collection is required

The Object-scoped collection remains a fundamental public capability:

```text
GET /objects/{object_id}/relationships
```

This answers:

```text
which factual Relationships are visible from this Object?
```

Its role is navigation/query in Object context. Exact response shape, fields, filters, pagination contract and physical data path are deliberately deferred until the functional capability coverage gate is closed.

## REL-API-03 — no Object-scoped single-Relationship detail for now

Do **not** introduce a route conceptually equivalent to:

```text
GET /objects/{object_id}/relationships/{relationship_id}
```

unless a concrete caller need later proves that the global detail plus the Object-scoped collection is insufficient.

Reasons:

1. the factual Relationship already has a global identity and root detail;
2. Object scope is navigation context rather than ownership/identity;
3. `object_id + relationship_id` does not necessarily identify one unique semantic perspective in overlap/self-loop cases;
4. introducing a scoped detail would force additional public selector, ambiguity, rename and error semantics without a demonstrated caller requirement.

The earlier candidate direction that proposed an Object-relative single-Relationship detail is therefore **superseded by this checkpoint** and must not be treated as current direction.

## REL-API-04 — functional coverage precedes route-detail design

The current phase is a functional capability coverage audit. Before reviewing DTO fields, payload weight, exact filters, SQL shape or route-level optimization, determine whether the factual Relationship family exposes every caller capability that M4 needs.

Therefore:

```text
absence from AS-IS != automatic rejection
candidate capability != automatic new endpoint
```

A missing capability must be evaluated from a concrete caller/domain need and ratified explicitly. Conversely, no route or operation is introduced merely because it is theoretically possible.

In particular, the following are currently **coverage questions**, not ratified additions and not ratified exclusions:

```text
global Relationship collection/discovery independent of one Object
endpoint reassignment/reversal as a first-class mutation vs delete+create
any other factual-Relationship capability surfaced by concrete callers
```

---

# 3. Current functional capability coverage gate

The AS-IS surface already covers these user-level needs:

```text
CREATE
    create/admit a factual Relationship between Objects

GET global detail
    retrieve one known factual Relationship by its lifetime identity

GET Object-scoped collection
    discover factual Relationships visible from one Object

DATA_CHANGE
    mutate factual Relationship property data while preserving identity/binding

SCHEMA_CHANGE
    migrate the factual Relationship exact schema-version binding

DELETE
    remove the factual Relationship
```

Two read-capability decisions are already ratified:

```text
known specific Relationship -> global GET by relationship_id
Object-context navigation -> Object-scoped Relationship collection
```

and one candidate has been rejected for now:

```text
Object-scoped single-Relationship detail
```

The coverage gate is **not yet closed** because the current six operations may still omit a caller capability.

## Current first open coverage question

The first missing-AS-IS capability to evaluate is:

```text
global discovery/listing of factual Relationships
without starting from a specific Object
```

Conceptually this would answer a different functional question from both ratified reads:

```text
GET /relationships/{id}
    -> I already know the Relationship identity; give me that fact

GET /objects/{object_id}/relationships
    -> starting from this Object, which Relationship facts are visible?

global Relationship discovery
    -> which Relationship facts exist/match criteria independently of one Object?
```

At this stage do **not** decide route spelling, response DTO, fields, pagination, filters or data path. First decide only whether that third caller capability is needed at all.

The exact representation of the Object-scoped collection, including whether it carries `properties`, destination names or other fields, is explicitly deferred until this functional coverage gate is closed.

---

# 4. Persisted factual model and runtime closure

Current durable ownership is conceptually:

```text
relationships
    factual root
    id
    relationship_definition_id
    relationship_definition_version
    properties

runtime_relationship_resolutions
    complete deterministic runtime closure
    resolution_id
    from_object_id
    to_object_id
    relationship_id
    relationship_definition_id
```

`runtime_relationship_resolutions` is both:

```text
materialized factual runtime closure
+
authoritative exact-view ownership/conflict index
```

Its exact row identity is:

```text
(resolution_id, from_object_id, to_object_id)
```

M4 should not introduce a second Relationship-specific materialization/conflict table for the same semantic space without new evidence.

Current factual Relationship references also participate in Object lifetime arbitration through database-enforced Object foreign keys. A material change to Relationship persistence or Object-reference FK behavior must therefore trigger targeted revalidation of the reviewed Object.DELETE lifetime dependency.

---

# 5. CREATE — current first-phase findings

Concurrency/lock redesign remains deferred to the global concurrency phase.

## 5.1 Current expensive preparation shape

Before factual conflict arbitration/DML, the current CREATE path performs work including:

1. resolution -> complete RelationshipDefinition aggregate;
2. explicit/default exact RelationshipDefinitionVersion selection;
3. lock-plan stabilization/repeated model reads;
4. endpoint Object -> ObjectTemplate identity reads;
5. complete ObjectTemplate parent-graph load;
6. Python ancestry walking to derive deterministic runtime closure;
7. another exact RDV/schema load through runtime property-spec construction;
8. exact DataType semantic loads;
9. property canonicalization.

Reads that exist specifically for lock-plan stabilization remain concurrency-phase concerns.

## 5.2 Redundant exact-schema reload

After stabilization the selected exact RDV is already known, including its property declarations. Reloading the same RDV again solely to construct runtime property specs is redundant independently of any cache design.

Candidate separation:

```text
stabilized target RDV
+
DataType semantic payloads
-> resolved runtime Relationship schema
```

## 5.3 Immutable exact RDV runtime cache candidate

Published/deprecated exact RelationshipDefinitionVersion property semantics are immutable.

Candidate worker cache:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
    ordered property declarations
    exact DataType pins
    value modes
    compiled RuntimePropertySpec / validators
```

The cache must not own mutable lifecycle state such as RDV status or Definition default version.

PostgreSQL remains authority for current CREATE admission, including current existence, selected target currently `PUBLISHED`, and required current admission of direct exact DataType dependencies.

Cache presence never proves current admissibility.

## 5.4 Full ObjectTemplate graph load should leave the data-plane

CREATE only needs bounded ancestry predicates for the involved resolution topology and endpoint templates. The M4 stable closure owner:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

with self rows can answer them directly.

A positive/full worker cache over stable ancestry may then support in-memory closure derivation without loading the entire ObjectTemplate graph:

```text
StableObjectTemplateAncestryCache[template_id]
    -> complete ancestor set including self
```

Stable RelationshipDefinition topology is also a natural cache candidate:

```text
StableRelationshipDefinitionTopologyCache[definition_id]
    symmetric
    resolutions:
        resolution_id
        from_template_id
        to_template_id
```

Mutable Resolution names are excluded from stable topology cache ownership.

## 5.5 Conflict pre-check redundancy

Once the complete deterministic runtime closure has been derived, a selected-view exact-owner pre-check is informationally contained in a closure-wide ownership lookup.

If a pre-check remains in the final concurrency design, one set-based current-owner projection over the complete closure is sufficient.

Whether pre-checking remains at all, or collision is first arbitrated by the runtime-closure PK followed by post-rollback classification, remains a concurrency-phase decision.

Observed conflicting Relationship owners do not need full semantic recertification merely to return/prove current owner identity.

## 5.6 Runtime closure DML

Current conceptual DML can be improved from N row inserts to:

```text
1 INSERT factual Relationship root
1 bulk INSERT complete runtime closure
```

The closure remains all-or-nothing. Partial `ON CONFLICT DO NOTHING` materialization is not acceptable because a factual Relationship requires its complete deterministic closure.

## 5.7 CREATE lifecycle metadata reread remains open

The current lifecycle path rereads runtime closure plus mutable Resolution/Object display names after insertion.

It may be possible to acquire/reuse those names earlier, but any elimination of the reread must preserve a coherent metadata snapshot under concurrent Object/RelationshipDefinition renames.

Therefore this optimization remains concurrency-dependent and OPEN.

---

# 6. Global Relationship GET

Current M3 persistence already projects the factual detail in one authoritative PostgreSQL statement rooted at `relationships`, joined to the persisted runtime closure and current Resolution names.

Required factual detail includes:

```text
Relationship id
exact RelationshipDefinition id/version pin
persisted properties
all distinct public semantic views
```

No model/schema/lineage recertification is required.

Current first-phase conclusion:

```text
preserve one-statement authoritative factual projection
no worker cache
no new denormalization
no semantic recertification
```

Do not copy mutable `Resolution.name` into runtime closure rows merely to avoid the current join; the join preserves correct current-name behavior without invalidation/update protocols.

---

# 7. Object-scoped Relationship collection — technical data path

The current persistence path pages directly from `runtime_relationship_resolutions`, joins `relationships` for factual current state and joins `relationship_resolutions` for current relationship names.

It is Object-rooted so the public behavior distinguishes:

```text
requested Object absent
requested Object present + no matching Relationship views
normal non-empty page
```

The operation is already one PostgreSQL statement.

The current runtime closure is the correct navigation/materialization layer; this read must not reconstruct RelationshipDefinition topology, ObjectTemplate ancestry, exact schema semantics or factual derivability.

## 7.1 DISTINCT is semantically meaningful

Multiple exact runtime rows can collapse to one public object-relative semantic view, particularly with symmetric definitions and overlapping lineage spaces.

Deduplication therefore must happen before pagination.

## 7.2 Existing navigation index is already aligned

Current dedicated page support is conceptually:

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

No additional M4 index is justified by the current route evidence.

## 7.3 Cache/denormalization

No worker cache is justified for the authoritative collection read. Stable endpoint/resolution assignment is already durably materialized, while other useful public fields are current mutable state.

Exact selected columns and DTO content are deliberately deferred until the functional capability coverage gate in section 3 is closed. The technical findings in this section are retained only because they are independent of that later representation decision.

---

# 8. DATA_CHANGE — current first-phase findings

`DATA_CHANGE` changes only factual `relationships.properties`; it does not change Definition identity/version pin, endpoints or persisted runtime closure.

Therefore the target hot path should not re-certify:

```text
RelationshipDefinition topology
ObjectTemplate ancestry
runtime closure derivability
persisted factual canonicality as a whole
```

The operation needs authoritative current factual state plus exact immutable schema semantics for the already-pinned RDV.

Candidate warm path:

```text
validate operation set in memory
-> lock/load current factual Relationship
-> ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
-> apply_data_change()
-> if canonical no-op: no UPDATE and no DATA_CHANGE lifecycle event
-> else one UPDATE relationships.properties
-> coherent lifecycle metadata/event path
-> COMMIT
```

The source exact RDV may be `PUBLISHED` or `DEPRECATED`; an already-admitted fact does not need a current `PUBLISHED` check for its existing pin merely to mutate data.

Current repeated exact-schema loading is redundant once the schema has been resolved once.

Lifecycle display-metadata reread/locking remains concurrency-dependent and OPEN.

---

# 9. SCHEMA_CHANGE — current first-phase findings

SCHEMA_CHANGE changes only:

```text
relationship_definition_version
properties
```

It preserves Definition identity and materialized runtime closure.

Therefore the normal data-plane path should not recertify Definition topology, endpoint compatibility, ObjectTemplate ancestry or closure completeness.

## 9.1 Published-history recertification should leave the data-plane

Publication is the model-plane certification boundary for immutable exact RDV semantics/history rules. Runtime migration should not reload complete published/deprecated history and re-run publication certification.

## 9.2 Source/target immutable exact schemas are cache candidates

Migration needs exact source/target semantic declarations and compiled validators, naturally owned by:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
```

PostgreSQL remains authority for current target admission (`target exists`, same Definition, currently `PUBLISHED`, required direct exact DTV admission).

## 9.3 Numeric version order does not prove migrability

An older candidate path contained:

```text
target_version > source_version
```

as a runtime requirement.

That assumption is **not current direction**. It conflicts with the ratified general M4 principle that numeric version ordering/allocation and cross-version migrability are distinct concerns.

The exact Relationship runtime migration-admission rule must therefore be revalidated from migration semantics rather than inferred from version number ordering.

## 9.4 DML shape

The existing conceptual write shape remains good:

```text
one UPDATE
    relationship_definition_version = target_version
    properties = migrated canonical map
```

Runtime closure remains unchanged.

A schema-change event remains semantically meaningful when the exact version pin changes even if the migrated canonical properties happen to be equal; final no-op/equal-target behavior must be reviewed consistently with the general version/migration principles during the detailed route sweep.

Concurrency/current-admission realization and lifecycle display metadata remain open for the concurrency phase.

---

# 10. DELETE — current first-phase findings

DELETE does not need model/schema semantic recertification. If the current factual Relationship exists and the operation is otherwise admissible, deletion needs authoritative factual before-state and coherent historical display metadata for lifecycle emission.

Candidate pre-delete projection:

```text
factual root
complete persisted runtime closure
current RelationshipResolution names
current endpoint Object canonical names
```

Do not re-derive expected runtime closure from model topology.

Current ownership via cascade supports:

```text
1 DELETE relationships row
    -> runtime_relationship_resolutions CASCADE
```

Historical event metadata must be captured before root deletion because the runtime closure disappears by cascade.

Conceptual path:

```text
lock/load current factual Relationship
-> one authoritative pre-delete projection
-> DELETE factual root
-> closure cascades
-> bulk INSERT complete RELATIONSHIP_DELETED event set
-> COMMIT
```

No RDV/DataType/ObjectTemplate cache is useful for DELETE. Mutable display names must come from current PostgreSQL state.

Exact synchronization with concurrent renames remains a concurrency-phase question.

---

# 11. Cross-operation constraints and dependencies

## 11.1 Mutation response vs GET richness

Per the cross-family top-down review method, mutation acknowledgement/response shape must be evaluated independently from the cost/richness of GET projections. Relationship route review must not assume mutations must return the complete global GET DTO merely because that is the current AS-IS behavior.

## 11.2 Relationship persistence -> Object lifetime revalidation trigger

Current factual Relationship rows/runtime closure hold database-enforced references to endpoint Objects and therefore participate in Object.DELETE blocker arbitration.

If the Relationship persistence/FK graph materially changes, re-open only the affected reviewed Object lifetime/delete assumptions rather than silently carrying them forward.

## 11.3 No diagnostic-only backend work

Failure details/classification should derive from the efficient legal execution path. Do not add backend reads solely to enrich diagnostics when the operation can already classify the public outcome without them.

---

# 12. Concurrency boundary

The first-phase findings above intentionally do not freeze lock planning, collision restart realization, rename-race synchronization or final transaction rendezvous.

The later concurrency sweep must prove, among other things:

```text
CREATE exact-view arbitration / collision classification
coherent lifecycle display metadata under Object/Resolution renames
SCHEMA_CHANGE final target admission
DATA_CHANGE/SCHEMA_CHANGE current fact generation/lock behavior
DELETE before-state capture vs concurrent metadata mutation
```

Do not reinterpret first-phase read/DML simplifications as final concurrency protocols.

---

# 13. Current review order

Before any route-level payload/read-shape or deep mutation optimization work, close the factual Relationship **functional capability coverage gate**.

Current sequence:

```text
1. enumerate caller/domain capabilities already covered by AS-IS
2. examine plausible missing capabilities one at a time against concrete caller need
3. explicitly ratify required capabilities or reject/defer them
4. only when functional coverage is closed, review exact public contracts/read shapes
5. then continue the route-by-route data-path/concurrency/physical sweep
```

Current next coverage question:

```text
do callers need global Relationship discovery/listing
independently of a specific Object?
```

Do not discuss Object-scoped collection fields, `properties`, destination display data, pagination details or SQL realization until the coverage gate is closed.

After functional coverage is explicitly closed, continue the family sweep through the ratified public operations rather than inventing theoretical endpoints.

For each coverage decision:

```text
state functional problem
state concrete AS-IS/caller evidence
compare capability alternatives and semantic cost
ratify explicitly
update this owner
re-read diff/current owner for consistency
```
