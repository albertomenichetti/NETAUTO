# M4 WIP — Working-set navigation index

**Status:** ACTIVE NAVIGATION MAP / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file maps the current M4 working set and the progress of the ongoing top-down review.

Everything under `wip/` remains globally non-normative. `CLOSED`, `FROZEN`, `REVIEWED BASELINE` or similar wording in this directory is only an M4 discovery/review checkpoint and never authorizes implementation by itself.

Navigation role and review state are separate dimensions:

```text
SPINE
    first place to read for current working direction

ACTIVE INPUT
    distributed current discovery not yet consolidated/closed

SUPPORT / HANDOFF
    reusable cross-domain or later-architecture input

SOURCE MATERIAL
    evidence/traceability behind a current owner; not standalone authority

REVIEWED BASELINE
    relevant current owner/support has passed the present review/revalidation
    and may be reused as baseline input for later review steps

ACTIVE REVIEW FRONTIER
    topic currently being revalidated; legacy/open assumptions may still exist
```

`SPINE` answers **where to read**. `REVIEWED BASELINE` / `ACTIVE REVIEW FRONTIER` answers **how far review has progressed**.

## External interpretation anchors

Read these before interpreting M4 WIP:

- [`AGENTS.md`](../../../../AGENTS.md)
- [`README.md`](../../../../README.md)
- [`docs/general/linee_guida_progetto.md`](../../../general/linee_guida_progetto.md)
- [`docs/milestones/M4/status.md`](../status.md)
- [`docs/architecture/README.md`](../../../architecture/README.md)

Until M4 explicitly freezes/promotes a TO-BE delta, delivered architecture remains the normative AS-IS baseline.

# 1. Current review-state snapshot

## REVIEWED BASELINE

```text
general-domain-principles.md
version-allocation.md

object.md
object-revision.md
object-components-persistence.md
```

## REVIEWED BASELINE SUPPORT

```text
object-template-ancestry-cache.md
```

The route-level Object sweep is now complete. `object.md` directly owns the reviewed Object public routes, while cross-operation responsibilities remain intentionally separate in their dedicated owners.

The focused SCHEMA_CHANGE, component-slot GET, ATTACH, DETACH and GET-owner closures are all losslessly represented in `object.md`, including:

```text
POST /objects/{id}/schema
GET /objects/{parent_object_id}/components/{slot_name}
POST /objects/{parent_object_id}/components/{slot_name}/attach
POST /objects/{parent_object_id}/components/{slot_name}/detach
GET /objects/{child_object_id}/owner
```

including their public contracts, logical data paths, cache behavior, failure semantics, concurrency outcomes, cost profiles and architecture handoffs.

Additional reviewed Object-family decisions now explicitly represented in `object.md` are:

```text
GET /objects/{id}
    -> complete first-level Object representation
    -> direct-child fan-out deliberately unbounded
    -> no pagination, truncation or backend cardinality guard on this route

Object UUID identity
    -> lifetime-global semantic identity
    -> never reusable after allocation, including after DELETE
    -> positive ObjectLineageCache entries may safely outlive current existence

future ObjectTemplate sweep
    -> material changes to effective-property, effective-component or stable-ancestry contracts
       trigger targeted revalidation of dependent Object routes
    -> unaffected Object routes remain reviewed baseline
```

The former ATTACH/DETACH route-local source families, the shared ownership-command route-shape checkpoint, the dedicated component read-projection source and the superseded component-persistence exploration source family have been removed after explicit lossless absorption and reference cleanup; Git history remains the historical reasoning record.

Cross-operation responsibilities remain intentionally separate:

```text
object-revision.md
    -> intrinsic Object generation / expected_revision protocol

object-components-persistence.md
    -> current component-slot / ownership persistence boundary
```

The dedicated SCHEMA_CHANGE/fingerprint micro-WIP family was already removed after its earlier lossless consolidation; its non-superseded findings are represented by `object.md`, the cross-operation owners above and lifecycle discovery consumers.

Object-relative factual Relationship and Lifecycle surfaces are not reopened as Object routes merely because their URLs are Object-rooted; they remain owned by their later top-down family passes.

## ACTIVE REVIEW FRONTIER

The next data-plane construct in the top-down sequence is:

```text
factual Relationship
```

Current distributed inputs are the factual Relationship files listed in section 5 below.

No reviewed factual-Relationship route owner comparable to `object.md` exists yet. Selecting the first public route and its exact review order is the first step of that focused pass; this navigation index does not invent that sequencing decision in advance.

# 2. Current M4 spine

## Cross-cutting principles and method

### [`general-domain-principles.md`](general-domain-principles.md) — SPINE / REVIEWED BASELINE

Current owner for ratified general M4 principles, including:

```text
version number identifies exact version + allocation order only
validity of one exact version != cross-version migrability
REVISE/PUBLISH do not absorb future runtime-migration responsibility
lifecycle payload = complete operation-owned semantic transition
failure semantics/details derive from the efficient legal execution path
    -> no backend work solely for diagnostic enrichment
```

### [`version-allocation.md`](version-allocation.md) — SPINE / REVIEWED BASELINE

Current owner for shared monotonic/no-reuse version allocation and the logical `last_versions(id,last_version)` direction.

### [`discovery.md`](discovery.md) — SPINE / discovery framing / NOT REVIEWED BASELINE

Initial M4 motivation, workload hypotheses and design exploration.

### [`top-down-api-closure-sweep.md`](top-down-api-closure-sweep.md) — SPINE / operating method / NOT REVIEWED BASELINE

Method used to close routes from public contract through data path, cache, concurrency, persistence and architecture handoff.

### [`mutation-response-semantics-discovery.md`](mutation-response-semantics-discovery.md) — ACTIVE INPUT

Cross-family mutation-response vs GET-representation discovery.

### [`milestone-relational-schema-closure-requirement.md`](milestone-relational-schema-closure-requirement.md) — SUPPORT / HANDOFF

Governance input requiring milestone closure to document the resulting relational schema; not a current DDL freeze.

# 3. Object current owners

### [`object.md`](object.md) — SPINE / REVIEWED BASELINE / Object family owner

Primary family owner for Object public surfaces and route-local navigation.

Current full-sweep checkpoints include:

```text
POST /objects
GET /objects
GET /objects/{id}
PUT /objects/{id}/canonical-name
POST /objects/{id}/properties
GET /objects/{id}/schema
POST /objects/{id}/schema
GET /objects/{parent}/components/{slot}
POST /objects/{parent}/components/{slot}/attach
POST /objects/{parent}/components/{slot}/detach
GET /objects/{child}/owner
DELETE /objects/{id}
```

For `GET /objects/{id}`, use the GET-Object section in `object.md` for the complete first-level representation and its deliberately unbounded direct-child fan-out. The route returns every current effective slot and every current direct child without pagination, truncation or a backend cardinality guard; cost remains `O(P + S + C)`.

For `POST /objects/{id}/schema`, use the SCHEMA_CHANGE section in `object.md` for:

```text
exact-target and equal-target no-op semantics
SOURCE/TARGET exact effective-schema comparison
property/component migration matrix
immutable MigrationPlan and bounded semantic cache fills
single-generation Object preparation
expected_revision retry/reprepare
final TARGET PUBLISHED admission
current slot-delta maintenance/FK arbitration
failure taxonomy and precedence
operation-owned lifecycle binding + changed-property delta
no-op/warm/cold cost character
architecture handoff
```

For `GET /objects/{parent}/components/{slot}`, use the component-slot GET section in `object.md` for:

```text
explicit one-slot nested collection contract
slot absent vs empty semantics
child {id, canonical_name} page
semantic-slot cursor identity
SCHEMA_CHANGE cursor continuity/replacement rules
one-statement current data path
failure precedence
bounded 0/1-statement cost profile
physical plan/index handoff
```

For the ownership mutation pair, use the shared command-surface rationale immediately before the ATTACH section in `object.md`. It owns why ATTACH/DETACH are explicit symmetric semantic command routes rather than generic CRUD on the `components` read projection or DELETE-with-body semantics.

For `POST /objects/{parent}/components/{slot}/attach`, use the ATTACH section in `object.md` for:

```text
explicit /attach command route
strict atomic batch 1..100 + 204 success
parent vs nested-slot 404 distinction
positive-only ObjectLineageCache[object_id] -> template_id
lifetime-global non-reusable Object UUID identity
no semantic negative Object-existence cache
full READY stable ancestry/neighborship cache from object_template_ancestry
protected ownerlessness + root-only cycle admission
no mutable root materialization
strict bulk edge insert
child lifetime FK current-existence authority
semantic-slot FK ownership_slot_unavailable arbitration
PK/self-edge CHECK unexpected-failure classification after successful admission
required parent/child historical canonical_name read after successful edge insertion
one ATTACH_TO lifecycle row per committed edge
execution-path failure precedence + no diagnostic-only rereads/default retry
warm 6 / full-cold 8 logical statement baseline
architecture cache/SQL/FK/lock/index handoff
```

For `POST /objects/{parent}/components/{slot}/detach`, use the DETACH section in `object.md` for:

```text
explicit /detach command route
strict atomic batch 1..100 + 204 success
parent-before-self-reference precedence
persisted ownership edge as semantic slot-identity authority
no current-slot/schema/cache/ancestry/graph/revision preparation
no requested-child existence scan solely for diagnostics
all incomplete exact-edge states -> 409 ownership_conflict
one-statement delete-first strict-batch certification
required parent/child historical canonical_name capture during deletion
conditional fused DETACH_FROM lifecycle, one event per committed removed edge
no lifecycle work for inadmissible batches
one PostgreSQL business-statement + COMMIT success baseline
route-local lock-order policy deferred to architecture/core LockPlanner
```

For `GET /objects/{child}/owner`, use the GET-owner section in `object.md` for:

```text
strict no-query/no-body GET surface
child absent -> 404 resource_not_found
child present + ownerless -> 200 null
owned DTO = parent ObjectReference {id, canonical_name} + slot_name
slot_declaring_template_id excluded from public DTO
one child-rooted current-state PostgreSQL statement
no object_component_slots/model/cache/revision/lock/lifecycle work
ordinary statement-snapshot concurrency semantics
constant bounded one-statement cost profile
no new relational/materialization/cache requirement
physical plan/index handoff
```

The Object family closure is explicitly dependency-aware. A material future change to ObjectTemplate certified exact effective-property semantics, certified exact effective-component semantics or stable complete ancestry reopens only the dependent Object routes identified by the revalidation-trigger section in `object.md`.

Current component persistence mechanics are owned by `object-components-persistence.md`; intrinsic Object generation by `object-revision.md`; reusable stable ObjectTemplate ancestry-cache semantics by `object-template-ancestry-cache.md`.

### [`object-revision.md`](object-revision.md) — SPINE / REVIEWED BASELINE

Owner for the universal intrinsic `objects.revision` generation/CAS protocol:

```text
CREATE -> revision=1
prepared intrinsic mutation -> expected_revision
persisted intrinsic mutation -> revision+1 atomically
stale generation -> no mutation/lifecycle + bounded retry
revision scope excludes ownership/Relationship facts outside objects
```

### [`object-components-persistence.md`](object-components-persistence.md) — SPINE / REVIEWED BASELINE

Owner for current component/ownership persistence:

```text
object_component_slots
object_components
semantic slot identity
materialization invariant
edge -> current semantic-slot dependency
relational blocker arbitration
architecture physical-design handoff
```

### [`object-template-ancestry-cache.md`](object-template-ancestry-cache.md) — SUPPORT / REVIEWED BASELINE SUPPORT

Reusable stable ObjectTemplate lineage ancestry/compatibility cache backed by the denormalized `object_template_ancestry` closure. A source becomes READY only after its complete ancestor/neighborship set is loaded. Exact physical/cache implementation remains architecture work.

# 4. Model-plane families — ACTIVE INPUT sets

These families do not yet have one consolidated reviewed owner comparable to the Object owners above. The following filename sets represent their current distributed working state.

## DataType

```text
datatype-create-next-discovery.md
datatype-delete-draft-discovery.md
datatype-delete-lineage-discovery.md
datatype-deprecate-discovery.md
datatype-get-lineage-discovery.md
datatype-get-version-discovery.md
datatype-list-lineages-discovery.md
datatype-list-versions-discovery.md
datatype-revise-discovery.md
datatype-set-default-discovery.md
datatype-set-description-discovery.md
```

Version allocation is cross-domain and owned by `version-allocation.md`.

## ObjectTemplate

```text
objecttemplate-create-discovery.md
objecttemplate-create-next-discovery.md
objecttemplate-delete-draft-discovery.md
objecttemplate-delete-lineage-discovery.md
objecttemplate-deprecate-discovery.md
objecttemplate-get-effective-schema-discovery.md
objecttemplate-get-lineage-discovery.md
objecttemplate-get-version-discovery.md
objecttemplate-list-lineages-discovery.md
objecttemplate-list-versions-discovery.md
objecttemplate-publish-discovery.md
objecttemplate-relationship-capabilities-discovery.md
objecttemplate-revise-discovery.md
objecttemplate-set-default-discovery.md
objecttemplate-set-description-discovery.md
objecttemplate-clear-default-discovery.md
```

Support/handoff:

```text
objecttemplate-validation-loader-handoff.md
```

## RelationshipDefinition

```text
relationshipdefinition-create-discovery.md
relationshipdefinition-create-next-discovery.md
relationshipdefinition-delete-discovery.md
relationshipdefinition-delete-draft-discovery.md
relationshipdefinition-deprecate-discovery.md
relationshipdefinition-get-discovery.md
relationshipdefinition-get-version-discovery.md
relationshipdefinition-list-definitions-discovery.md
relationshipdefinition-list-versions-discovery.md
relationshipdefinition-publish-discovery.md
relationshipdefinition-rename-discovery.md
relationshipdefinition-revise-discovery.md
relationshipdefinition-set-default-discovery.md
relationshipdefinition-clear-default-discovery.md
```

Version allocation is cross-domain and owned by `version-allocation.md`.

# 5. Factual Relationship — ACTIVE REVIEW FRONTIER / ACTIVE INPUT

Current distributed factual Relationship discovery:

```text
relationship-create-discovery.md
relationship-create-runtime-closure-discovery.md
relationship-get-discovery.md
relationship-list-for-object-discovery.md
relationship-data-change-discovery.md
relationship-delete-discovery.md
relationship-schema-change-discovery.md

object-relationship-list-api-discovery.md
object-relationship-detail-api-discovery.md
```

These are the current inputs for the next top-down family pass. They are not yet reviewed public-contract owners, and their internal assumptions must be revalidated route by route rather than promoted wholesale.

# 6. Lifecycle — ACTIVE INPUT with reviewed mutation payload inputs

Current lifecycle discovery:

```text
object-lifecycle-read-discovery.md
lifecycle-list-detail-api-discovery.md
lifecycle-summary-data-path-discovery.md
```

The files remain ACTIVE INPUT as complete documents, but mutation-owned payload semantics already ratified by reviewed Object owners are baseline inputs, including:

```text
RENAME
    -> exact canonical_name transition

DATA_CHANGE
    -> exact binding context + changed-property delta

SCHEMA_CHANGE
    -> exact binding transition + actual changed-property delta

ATTACH
    -> edge semantic identity
       child_object_id
       parent_object_id
       slot_declaring_template_id
       slot_name
    -> required historical child/parent canonical_name display metadata
    -> exactly one ATTACH_TO event per committed ownership edge

DETACH
    -> exact removed edge semantic identity
       child_object_id
       parent_object_id
       slot_declaring_template_id
       slot_name
    -> required historical child/parent canonical_name display metadata
    -> exactly one DETACH_FROM event per committed removed ownership edge
```

The lifecycle API pass still owns final collection/detail DTOs, discriminated detail carrier, persistence decoding and read-side physical realization.

# 7. Object source material retained behind current owners

Source material is evidence only. If it conflicts with a reviewed owner/general principle, revalidate explicitly rather than treating the source as authority.

## Component navigation / ownership route source cleanup

The former dedicated navigation cursor/data-path files, broad Object-components brainstorming files, focused component-slot GET route owner, dedicated component read-projection source and shared ownership-command route-shape checkpoint were removed after lossless consolidation into:

```text
object.md / Object family route semantics and ownership command-surface rationale
object-components-persistence.md / shared persistence boundary
```

`object-components-reads-discovery.md` was removed after the GET-owner full sweep confirmed that its route-local owner projection was fully absorbed by `object.md` and its still-relevant persistence/read consequences were already represented by `object-components-persistence.md`.

`object-ownership-command-routes.md` was removed after its remaining unique rationale was absorbed into the shared ownership command-surface note in `object.md`: ATTACH/DETACH are explicit symmetric semantic commands; DETACH of a caller-selected child subset is not represented as DELETE of the slot collection with a request body; a future detach-all capability would be a distinct semantic operation.

Git history is their historical source.

## ATTACH source-family cleanup

The former route-specific files matching:

```text
object-attach-*.md
to-be-api-object-attach-*.md
```

were removed after the ATTACH full sweep, explicit lossless absorption into `object.md` / reviewed cross-operation owners, and reference cleanup. They are no longer part of the live M4 working set and cannot compete with the reviewed ATTACH owner.

Git history is the historical source for the earlier rationale and superseded mechanisms.

## DETACH source-family cleanup

The former route-specific files matching:

```text
object-detach-*.md
to-be-api-object-detach-*.md
```

were removed after the DETACH full sweep, explicit lossless absorption into `object.md` / reviewed cross-operation owners, and reference cleanup. They are no longer part of the live M4 working set and cannot compete with the reviewed DETACH owner.

Git history is the historical source for the earlier rationale and superseded mechanisms.

## Component-persistence source-family cleanup

The former focused component-persistence exploration files:

```text
object-component-slots-data-plane-materialization.md
object-component-slots-fk-arbitration.md
object-components-runtime-schema-discovery.md
object-components-physical-index-candidate.md
object-components-physical-schema-discovery.md
```

were removed after an explicit final lossless check against:

```text
object-components-persistence.md
    -> shared current persistence/materialization owner
    -> retained architecture physical-design/evidence handoff

object.md
    -> full-swept route-local consequences
```

`object-components-persistence.md` already records the consolidated current materialization shape, fields deliberately omitted, semantic/public identities, lifetime composition, edge-to-slot dependency, PostgreSQL FK-arbitration evidence, cross-operation consequences, storage/workload trade-off, migration/backfill direction, physical candidate alternatives and the required `EXPLAIN`/storage/write evidence gate. Exact PK/UNIQUE/FK/index DDL remains architecture work.

The removed source files included first-phase or intermediate candidates that are now superseded where they differ from the consolidated owners; for example, older ATTACH cost variants and the earlier edge-only direction must not compete with current route/persistence ownership.

Git history remains the historical source for their earlier rationale and superseded alternatives.

## SCHEMA_CHANGE source family cleanup

The former dedicated SCHEMA_CHANGE/fingerprint micro-WIP family and the focused SCHEMA_CHANGE route owner were removed after the full sweep and lossless consolidation into:

```text
object.md
object-revision.md
object-components-persistence.md
lifecycle discovery consumers
```

Git history is the historical source.

# 8. Maintenance rules

When a new WIP is created:

```text
1. classify navigation role
2. if it participates in current review, classify review state
3. do not imply completion merely by indexing it
```

When a review target closes:

```text
1. complete the route/owner full sweep
2. perform lossless consolidation/comparison
3. remove or demote superseded source material only when safe
4. promote the current owner/support to REVIEWED BASELINE
5. advance ACTIVE REVIEW FRONTIER
6. update this index
```

If a reviewed assumption is materially reopened:

```text
mark the affected topic/owner as ACTIVE REVIEW FRONTIER
state the reopened boundary
retain unaffected reviewed findings where ownership permits
```

If SOURCE MATERIAL conflicts with a SPINE owner or ratified general principle:

```text
DO NOT silently choose one
DO NOT infer a resolution
revalidate the specific point explicitly
record the result in the correct owner
```

# 9. Current-state precedence

Use this order to reconstruct M4 today:

```text
repository governance + M4 status
    -> interpretation boundary

general-domain-principles.md
    -> ratified cross-domain principles

version-allocation.md
    -> shared numeric allocation semantics

cross-operation reviewed owner when relevant
    -> e.g. object-revision.md / object-components-persistence.md

current family/topic owner
    -> reviewed baseline or active review frontier

ACTIVE INPUT set where no owner is consolidated

SUPPORT / HANDOFF

SOURCE MATERIAL
    -> evidence/explicit revalidation only
```

Review-state classification never changes topic ownership; it states whether the owner is safe to reuse as a closed baseline for subsequent review work.

## Completeness convention

Explicit filename lists and filename-pattern groups in this index both count as represented working sets. A WIP file outside those represented sets should not be assumed to contribute to current M4 state merely because it exists in the directory. If it becomes relevant again, add/reclassify it explicitly.
