# M4 WIP — Object TO-BE consolidated discovery

**Status:** ROUTE-OWNER CONSOLIDATED / CROSS-CUTTING OWNERS PENDING / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for the M4 Object operation family during discovery.

It replaces route-local fragmentation with one readable checkpoint for the current Object public surface, route-local semantics, logical data paths, cache boundaries, candidate costs, concurrency guarantees and architecture handoffs.

Everything under `wip/` remains non-normative. Local closure wording is only a discovery checkpoint and does not authorize implementation.

The route-owner comparison pass has been completed against the current route-local Object owners. Full-swept route-local owners are absorbed here losslessly; cross-operation owners remain separate where their scope spans multiple Object operations.

Detailed cross-operation component persistence is intentionally kept outside this file and is owned by:

```text
object-components-persistence.md
```

Cross-operation intrinsic Object generation semantics are owned by:

```text
object-revision.md
```

Git history is the historical record for superseded discovery checkpoints after cleanup.

# Shared Object runtime candidate

Current intrinsic Object state is:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties JSONB
    revision BIGINT NOT NULL
```

`revision` is the internal technical generation token for the intrinsic `objects` row. It starts at `1` on CREATE and every persisted intrinsic Object mutation derived from a previously observed generation uses `expected_revision`; a successful persisted mutation advances the generation atomically. It is not ObjectTemplate version, business/domain version, lifecycle sequence, ownership generation or public Object state. Detailed cross-operation semantics are owned by [`object-revision.md`](object-revision.md).

Current component/ownership candidate is:

```text
object_component_slots
    object_id
    slot_declaring_template_id
    slot_name
    target_template_id

object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

`object_component_slots` contains one row for every component slot currently effective for one Object, including empty slots.

It is not a second semantic authority. The semantic source remains the Object current exact ObjectTemplateVersion and its certified immutable effective schema. The slot table is a transactionally maintained data-plane derivative.

Fundamental candidate invariant:

```text
MaterializedSlots(O)
    ==
EffectiveComponentSlots(
        O.template_id,
        O.template_version
    )
```

The Object exact binding and corresponding materialized slot set must become atomically visible.

Current semantic slot identity:

```text
(slot_declaring_template_id, slot_name)
```

Current public/runtime slot lookup:

```text
(object_id, slot_name)
```

Current ownership-edge relational dependency candidate:

```text
(parent_object_id, slot_declaring_template_id, slot_name)
    -> object_component_slots(
           object_id,
           slot_declaring_template_id,
           slot_name
       )
```

Exact PK/UNIQUE/FK/index DDL remains architecture-phase physical design.

# Operation map

| Operation | Current discovery state | Main runtime direction |
|---|---|---|
| `POST /objects` | **full-sweep complete** | non-abstract lineage + exact target PUBLISHED admission + READY validation cache + explicit `revision=1` + atomic Object/slot/lifecycle materialization |
| `GET /objects` | **full-sweep complete** | one statement on `objects`; bounded summary; no cache/model reads |
| `GET /objects/{id}` | **full-sweep complete** | one current data-plane statement, no component-schema cache |
| `PUT /objects/{id}/canonical-name` | **full-sweep complete** | read old name + revision, expected-revision CAS, `revision+1`, exact minimal RENAME lifecycle |
| `POST /objects/{id}/properties` | **full-sweep complete** | read full Object generation, READY requested-effect validation, application-side complete properties candidate, cheap no-op or expected-revision replacement + exact DATA_CHANGE delta |
| `GET /objects/{id}/schema` | **full-sweep complete** | one coherent Object PK -> ObjectTemplate PK statement; no cache/locks/revision/OTV admission |
| `POST /objects/{id}/schema` | **full-sweep complete** | exact-pair MigrationPlan + universal expected-revision freshness + set-based slot delta + final TARGET admission |
| `GET /objects/{parent}/components/{slot}` | **full-sweep complete** | one current root-preserving data-plane statement + semantic-slot keyset cursor |
| `POST /objects/{parent}/components/{slot}/attach` | **full-sweep complete** | materialized current slot + stable Object-lineage/ancestry caches + protected graph admission + FK arbitration + post-edge lifecycle display read |
| `POST /objects/{parent}/components/{slot}/detach` | **full-sweep complete** | one fused exact-edge DELETE + conditional DETACH_FROM lifecycle; no schema/cache/graph/revision work |
| `GET /objects/{child}/owner` | **full-sweep complete** | one child-rooted current-state statement returning parent ObjectReference + slot name or null; no schema/cache/revision work |
| `DELETE /objects/{id}` | **full-sweep complete** | DB-enforced lifetime arbitration + one fused Object DELETE + DELETED lifecycle statement |

Object-relative Relationship and Lifecycle routes remain owned by their later top-down discovery passes even when the URL is rooted under `/objects`.

# 1. CREATE Object — full sweep complete

## Public contract

```http
POST /api/v1/core/objects
Content-Type: application/json
```

Query parameters: none.

Request:

```json
{
  "object_template": {
    "id": "<template-id>",
    "version": 4
  },
  "canonical_name": "server-1",
  "properties": {
    "hostname": "srv01"
  }
}
```

Conceptual request model:

```text
ObjectCreateBody
    object_template: ObjectTemplateSelector
    canonical_name: string | omitted
    properties: object<string, JsonValue> | omitted

ObjectTemplateSelector
    id: UUID
    version: positive integer | omitted
```

Selector semantics:

```text
version present
    -> request exact (template_id, version)

version omitted
    -> resolve current default_version of template_id

no current default
    -> implicit CREATE fails

no latest/highest-PUBLISHED fallback
```

Explicit JSON `null` is not omission.

The Object id is server-generated and never caller-supplied.

`canonical_name`:

```text
optional on CREATE
omitted -> generated Object UUID string
persisted value required
1..255 characters
mutable
not unique
not identity
```

Properties remain sparse canonical JSONB:

```text
properties omitted          -> {}
optional SCALAR omitted     -> key absent
optional LIST omitted       -> key absent
optional LIST = []          -> canonical key absence
JSON null runtime value     -> invalid
required property omitted   -> invalid
required LIST = []          -> invalid
```

`migration_default` is not a CREATE default mechanism.

Success:

```http
201 Created
Location: /api/v1/core/objects/{new_object_id}
```

Response body: none. The canonical current representation is obtained through `GET /objects/{id}`.

## Semantic admission and validation

Object CREATE must always resolve and persist one concrete exact ObjectTemplate binding:

```text
(template_id, template_version)
```

No created Object persists `default`, `latest`, `highest`, `follow-current`, or any other floating version reference.

Explicit selector:

```text
object_template = { id: T, version: V }
    -> selected exact binding = T@V
```

Implicit selector:

```text
object_template = { id: T }
    -> resolve current T.default_version = V
    -> selected exact binding = T@V
```

If `default_version` is absent, implicit CREATE fails even if other PUBLISHED versions of the lineage exist. Once the exact binding `T@V` has been resolved, the in-flight CREATE remains pinned to it; a concurrent later default change must not retarget the command.

Object CREATE owns exactly two direct model-plane admission predicates:

```text
selected ObjectTemplate lineage T
    -> abstract == false

selected exact ObjectTemplateVersion T@V
    -> status == PUBLISHED through the new Object binding commit
```

`abstract == false` is stable direct-creation eligibility owned by the selected ObjectTemplate lineage. A PUBLISHED exact version of an abstract lineage is still not a valid target for Object CREATE.

Object CREATE does not independently re-admit, re-certify or lifecycle-check any other model-plane dependency.

This relies on the active-model graph invariant paid by model-plane mutations. Publication admits direct lifecycle-sensitive exact dependencies only while they are PUBLISHED, and later deprecation is blocked while an active PUBLISHED consumer still pins them. Therefore a PUBLISHED ObjectTemplateVersion is already a lifecycle-consistent active-model anchor.

Conceptually:

```text
PUBLISHED ObjectTemplateVersion
    -> exact DataTypeVersion
```

prevents that exact DataTypeVersion from becoming DEPRECATED while the active PUBLISHED dependency exists, and:

```text
PUBLISHED child ObjectTemplateVersion
    -> exact parent ObjectTemplateVersion
```

prevents that exact parent from becoming DEPRECATED while the active PUBLISHED dependency exists.

Transitive lifecycle consistency follows from these direct active-model invariants. CREATE therefore does not recursively inspect parent/ancestor ObjectTemplateVersion status or the status of exact DataTypeVersions used by effective properties.

This active-model guarantee does not subsume direct-creation eligibility. `abstract` is a stable lineage semantic property and remains an explicit CREATE admission predicate.

CREATE also performs no cross-version reasoning. It does not infer admission from numeric order, creation order, genealogy, widening/narrowing, compatibility or migrability. The selected lineage/exact pair either satisfies `abstract == false` and `T@V == PUBLISHED`, or it is not admissible for a new Object.

After resolving exact `T@V`, caller properties are validated against the complete effective property schema certified for that exact version, including inherited properties.

For every effective property, runtime validation consumes:

```text
property name
value mode
required flag
exact DataTypeVersion pin
```

and the immutable exact DataTypeVersion semantics:

```text
PrimitiveType
canonicalization rules
constraints
```

Conceptually:

```text
raw caller value
    -> SCALAR/LIST shape validation
    -> PrimitiveType parsing/validation
    -> primitive canonicalization
    -> exact DataTypeVersion constraint validation
    -> canonical runtime value
```

CREATE persists the complete canonical validated runtime property map, not the raw request payload.

Property rules include:

```text
unknown property
    -> invalid

required property omitted
    -> invalid

JSON null
    -> invalid

SCALAR property receives a list
    -> invalid

LIST property receives a scalar
    -> invalid

optional LIST = []
    -> canonical absence / key omitted

required LIST = []
    -> invalid

non-empty LIST
    -> every item independently validated and canonicalized
       against the same exact DataTypeVersion
```

LIST order is preserved and duplicate values are allowed unless forbidden by an independent semantic rule.

`migration_default` is exclusively migration-oriented schema metadata and is never a CREATE default mechanism:

```text
required property omitted
+ migration_default exists
    -> CREATE still fails
```

A newly created Object starts with the complete effective component-slot contract of the selected exact `T@V` and zero current ownership edges. No child attachment is part of Object CREATE. The Object exact binding and its current effective slot contract must correspond to the same exact `T@V`; the persistence/materialization realization is handled by the execution/data-path block.

## Ratified execution/data-path direction

CREATE is split into three deliberately separate stages:

```text
STEP 1 — current binding resolution / early PUBLISHED admission
    PostgreSQL

STEP 2 — stable direct-creation eligibility + semantic preparation / property validation
    worker-local READY immutable/stable semantic cache

STEP 3 — short mutation UoW
    final exact PUBLISHED admission/protection
    + INSERT Object generation 1
    + materialize all current component slots
    + CREATED lifecycle
```

### STEP 1 — minimal current binding resolution

STEP 1 always consults PostgreSQL. Cache state must never resolve a mutable current default or prove current PUBLISHED status.

Explicit selector:

```text
(T,V)
    -> exact version must exist and currently be PUBLISHED
```

Implicit selector:

```text
T
    -> resolve current default V
    -> exact (T,V) must currently be PUBLISHED
```

Once STEP 1 resolves an exact binding, the command stays pinned to it. A concurrent later `SET_DEFAULT` or `CLEAR_DEFAULT` does not retarget or invalidate the in-flight CREATE merely by changing the lineage default pointer.

STEP 1 must remain current-state oriented and must not load effective property/component schema, parent chains, DataType semantic payload or transitive dependency lifecycle state.

### STEP 2 — READY semantic cache and opportunistic cross-facet warming

STEP 2 consumes complete READY stable/immutable semantic cache state for the facets CREATE actually requires.

Required CREATE knowledge includes:

```text
stable direct-creation eligibility
    abstract

complete effective property semantics
    declaring_template_id
    name
    value_mode
    required
    exact datatype_id/version pin

exact immutable DataTypeVersion semantics required by those properties
    primitive/base type
    canonical constraints

compiled/runtime validation structures
    RuntimePropertySpec or equivalent
    reusable compiled validators where beneficial
```

The cache is not authority for:

```text
current default_version
current T@V PUBLISHED/DEPRECATED status
transitive dependency lifecycle admission
```

Because `abstract` is stable lineage semantics, it may be consumed from the semantic cache and does not require a second mutable-state protection at commit. The current exact-version `PUBLISHED` predicate is the lifecycle-sensitive admission that must be revalidated/protected through the binding commit.

A missing or partial required facet is completed before validation and outside the mutation UoW. The cold-load capability must remain bounded and must not regress to recursive ObjectTemplate parent traversal, per-property reads or N+1 exact DataTypeVersion loads.

The exact component-semantic facet is **not** a correctness prerequisite for Object CREATE. CREATE does not need worker-side component semantics to validate the new Object or to persist its initial empty ownership state.

However, the same exact ObjectTemplateVersion is useful to other consumers, and the component facet is immutable. Therefore a CREATE-driven cold load should opportunistically warm exact effective component semantics when the same bounded load already carries them or can include them without an otherwise unnecessary PostgreSQL round trip.

Conceptually:

```text
CREATE requires
    stable direct-creation facet READY
    validation/property facet READY

CREATE cold fill may additionally publish
    component semantic facet READY
        declaring_template_id
        name
        target_template_id

component-facet READY
    != CREATE semantic prerequisite
```

Cross-facet warming policy:

```text
same bounded load naturally provides component semantics
    -> warm component facet too

component semantics can be included with bounded marginal work
and no additional DB round trip
    -> warm component facet too

an additional PostgreSQL round trip would exist solely for speculative warming
    -> not required by Object.CREATE
```

This keeps CREATE correctness dependent only on the facets it consumes while allowing later operations to benefit from work already paid during the cold load.

No model-plane PostgreSQL lock is held during cache fill, compilation, direct-creation eligibility evaluation, property validation or canonicalization.

### STEP 3 — short mutation UoW

STEP 3 begins only after the complete canonical Object candidate is ready.

Conceptually:

```text
ObjectCandidate
    id
    canonical_name
    template_id = T
    template_version = V
    canonical properties
    revision = 1
```

No cache fill, semantic reconstruction or property validation belongs inside the mutation UoW.

Current logical mutation direction:

```text
BEGIN

S1
    final exact T@V PUBLISHED admission/protection
    + INSERT objects row with revision = 1 explicitly
    + bounded DB-internal copy of all certified exact effective component slots
      from object_template_effective_components(T,V)
      into object_component_slots

S2
    INSERT CREATED lifecycle event

COMMIT
```

The component materialization path is intentionally DB-internal. CREATE does not need to transfer exact component semantics DB -> worker -> DB merely to create `object_component_slots` rows.

Object state, exact binding, intrinsic generation `1`, complete materialized current slot set and CREATED lifecycle transition must become visible atomically.

CREATE writes:

```text
objects
object_component_slots
object lifecycle persistence
```

and does not create or otherwise touch current ownership edges:

```text
object_components
    -> no CREATE write
```

### Concurrency boundary

The direct lifecycle race owned by CREATE is:

```text
Object.CREATE against T@V
vs
ObjectTemplate.DEPRECATE(T@V)
```

Required outcome:

```text
DEPRECATE makes T@V non-PUBLISHED before final admission
    -> CREATE cannot commit the new binding

CREATE final admission/protection wins first
    -> CREATE may commit the new binding
    -> DEPRECATE may proceed afterward
```

A successful Object may later remain pinned to that exact version after it becomes DEPRECATED; the lifecycle-sensitive predicate applies to the creation of the new binding, not to historical binding validity.

CREATE does not independently close races against parent/ancestor OTV or exact DTV deprecation. Those transitions are already constrained by the active PUBLISHED model graph while the target T@V remains PUBLISHED.

Whole-lineage deletion is also a direct binding race at the final admission boundary:

```text
DELETE_LINEAGE wins before final admission
    -> selected exact T@V no longer exists
    -> CREATE cannot commit

CREATE binding commits first
    -> the new Object reference becomes a normal lineage-delete blocker
```

Exact PostgreSQL arbitration remains architecture work.

### Cost direction

Warm target:

```text
STEP 1
    1 minimal current binding/PUBLISHED lookup

STEP 2
    required cache facets HIT
    CPU-only abstract check + property validation/canonicalization

STEP 3
    1 final admission + Object generation-1 + slot materialization candidate statement
    1 CREATED lifecycle statement
    COMMIT

~3 PostgreSQL business statements + COMMIT
```

Cold target:

```text
warm path
+ 1 bounded stable/immutable semantic cold-load statement where physically feasible
+ local compilation/cache fill
+ opportunistic component-facet warming under the no-extra-round-trip rule

~4 PostgreSQL business statements + COMMIT
```

These counts are discovery cost targets, not a frozen SQL realization. Exact statement fusion, lock mode, physical loader query shape, indexes and final PostgreSQL arbitration belong to architecture. The route-level requirement is bounded work, no recursive/N+1 semantic reconstruction, and no cache fill while holding final model-plane admission protection.

### Relational/materialization implication

CREATE introduces no route-specific denormalization beyond already identified M4 candidates and the shared cross-operation Object revision column:

```text
object_template_effective_properties
    -> certified exact property source for semantic cold loading

object_template_effective_components
    -> certified exact component source for DB-internal slot materialization

object_component_slots
    -> current per-Object derived slot contract

objects.revision
    -> shared intrinsic generation token
    -> CREATE explicitly initializes it to 1
```

## Failure mapping and precedence

`POST /objects` is a collection CREATE. ObjectTemplate selectors supplied in the request body are referenced command operands, not URI/path target identities. Missing referenced ObjectTemplate resources therefore do not produce `404`.

Public failure set:

```text
400 invalid_request

422 referenced_resource_not_found
422 semantic_validation_failed

409 default_version_unavailable
409 dependency_not_admissible

500 internal_error
```

Precedence on the normal command path:

```text
1. malformed/static request input
       -> 400 invalid_request

2. selected ObjectTemplate lineage operand absent
       -> 422 referenced_resource_not_found
          resource_type = object_template

3. implicit selector + current default_version is NULL
       -> 409 default_version_unavailable

4. selected explicit exact ObjectTemplateVersion absent
       -> 422 referenced_resource_not_found
          resource_type = object_template_version

5. selected exact ObjectTemplateVersion exists but is not PUBLISHED
       -> 409 dependency_not_admissible

6. selected lineage is abstract
       -> 422 semantic_validation_failed
          rule = abstract_template

7. Object property validation/canonicalization fails
       -> 422 semantic_validation_failed

8. final admission race
       exact T@V disappeared
           -> 422 referenced_resource_not_found

       exact T@V still exists but is no longer PUBLISHED
           -> 409 dependency_not_admissible

9. impossible invariant/integrity failure encountered on required CREATE state
       -> 500 internal_error
```

For an implicit selector, a persisted `default_version` pointing to an exact version that does not exist is an invariant failure rather than caller operand absence:

```text
500 internal_error
```

`semantic_validation_failed` remains the aggregate Object-candidate validation code. Bounded `details.violations` carries stable `path` / `rule` diagnostics for `abstract_template`, unknown/required properties, SCALAR/LIST shape, primitive validation and exact DataTypeVersion constraint failures.

The route introduces no `404 resource_not_found`, canonical-name conflict or ownership/schema-change-specific failure class.

## CREATE consistency boundary — no proactive consistency sweep

Object CREATE validates only the invariants required to certify the state it is creating.

Required CREATE certification is bounded to:

```text
selected lineage T
    -> abstract == false

selected exact T@V
    -> PUBLISHED through new-binding commit

Object candidate properties
    -> valid and canonical under certified exact T@V semantics

new persisted Object state
    -> exact binding
    -> intrinsic revision = 1
    -> complete current effective slot materialization
    -> zero ownership edges
    -> CREATED lifecycle transition
    -> atomic visibility
```

CREATE is **not** a domain consistency sweep. It must not proactively:

```text
re-check parent/ancestor OTV lifecycle
re-check exact DTV lifecycle dependencies
re-certify the active model graph
scan for dangling model references
rebuild/re-certify effective schema construction
validate invariants owned by unrelated domain mutations
perform diagnostic-only reads to search for corruption
```

Those invariants are preserved by the mutations that own them. Downstream CREATE consumes the certified state they establish.

If an impossible invariant violation is encountered incidentally while consuming state that CREATE already needs on its required path, it is classified as `500 internal_error`. This classification does not authorize additional consistency queries or traversal solely to discover such violations.

Principle:

```text
each mutation pays for the invariants it owns

downstream consumers trust
already-certified upstream invariants
```

## Architecture handoff and full-sweep closure

The logical `POST /objects` route is full-sweep complete.

Deferred only to later M4 architecture-wide physical/concurrency realization:

```text
exact STEP-1 SQL projections
exact cold semantic-loader SQL/carrier
final cache class/layout/eviction and local fill coordination
exact STEP-3 SQL statement fusion
final lock mode / rendezvous against DEPRECATE and DELETE_LINEAGE
final PK/UNIQUE/FK realization
final physical revision type/default/check details preserving explicit CREATE revision=1
final indexes
EXPLAIN/BUFFERS and measured row/payload evidence
constraint/SQLSTATE realization preserving the ratified public failure classes
```

Those choices must preserve the public contract, bounded three-stage data path, no-consistency-sweep boundary, failure precedence, exact new-binding admission, explicit initial intrinsic generation, opportunistic component warming policy and atomic Object/slot/lifecycle state defined above.

# 2. LIST Objects — full sweep complete

## Public contract

```http
GET /api/v1/core/objects
```

Request body: none.

Supported query parameters:

```text
object_template_id: UUID | optional
object_template_version: positive integer | optional
canonical_name: string | optional
cursor: opaque string | optional
limit: integer 1..500 | optional, default 100
```

Unknown or repeated query parameters are invalid request input.

Validation:

```text
object_template_version requires object_template_id
```

The M4 public names intentionally differ from the current AS-IS `template_id` / `template_version` query names. The caller-facing M4 surface uses the explicit `object_template_*` namespace consistently with the nested ObjectTemplate reference in the response.

Filters are exact and non-polymorphic:

```text
object_template_id
    -> objects.template_id equality only

object_template_version
    -> objects.template_version equality within selected lineage

canonical_name
    -> exact equality
```

No ObjectTemplate ancestry expansion is implied. A filter for one lineage does not include Objects pinned to descendant lineages.

Unknown filter values return an empty `200` page rather than `404`.

Success representation:

```json
{
  "items": [
    {
      "id": "<object-id>",
      "canonical_name": "server-1",
      "object_template": {
        "id": "<template-id>",
        "version": 4
      }
    }
  ],
  "next_cursor": null
}
```

Conceptual wire model:

```text
ObjectSummaryDto
    id: UUID
    canonical_name: string
    object_template:
        id: UUID
        version: positive integer

ObjectPageDto
    items: ObjectSummaryDto[]
    next_cursor: string | null
```

Collection items intentionally exclude:

```text
properties
components
owner
relationships
ObjectTemplate mutable metadata
revision
```

LIST is a bounded search/navigation surface. It does not reuse the richer exact-resource DTO solely for representation uniformity.

## Pagination

Pagination is deterministic keyset pagination by Object id:

```text
ORDER BY objects.id ASC
cursor position = last returned Object id
```

The cursor is opaque and bound to:

```text
route identity
complete active filter set:
    object_template_id
    object_template_version
    canonical_name
canonical ordering
```

`limit` is not part of semantic cursor identity and may change between pages.

Therefore:

```text
same route + same filters + same cursor + different limit
    -> valid continuation

same cursor + different active filters
    -> invalid_cursor
```

The route exposes no:

```text
offset
page number
total_count
has_more
previous_cursor
sort
order_by
direction
```

`next_cursor != null` is the only continuation signal.

Each page is independently snapshot-consistent. Cross-request pagination does not promise a repeatable dataset snapshot:

```text
page 1
-> concurrent committed mutations
-> page 2
```

may observe changed membership according to the new committed state. The cursor is a continuation token, not a snapshot/export/CDC token.

## Failure mapping and precedence

Static request validation happens before cursor interpretation:

```text
request body present
unknown/repeated query parameter
malformed object_template_id
malformed/non-positive object_template_version
object_template_version without object_template_id
malformed/out-of-range limit
    -> 400 invalid_request
```

When static request carriers are valid, cursor validation is:

```text
malformed cursor envelope
wrong route identity
cursor filter/presence identity differs from the current request
unusable cursor position carrier
    -> 400 invalid_cursor
```

Then the authoritative current-state statement yields only collection outcomes:

```text
no current Object matches the valid request/filter/cursor position
    -> 200 {"items": [], "next_cursor": null}

current matching rows are materializable
    -> 200 ObjectPageDto

mandatory persisted response carrier cannot be materialized
    -> 500 internal_error
```

Unknown-but-well-formed filter values remain normal collection membership and therefore produce an empty `200` page rather than `404`.

There is no normal LIST-level:

```text
404
409
422
```

No diagnostic-only follow-up query is permitted solely to classify or enrich an unexpected projection failure.

## Data path

The route is a pure current mutable data-plane read.

Required logical source:

```text
objects only
```

One PostgreSQL statement projects only:

```text
id
canonical_name
template_id
template_version
```

with:

```text
optional exact equality filters
optional id > :cursor_id predicate
ORDER BY id ASC
LIMIT :limit_plus_one
```

The application then:

```text
reads at most limit + 1 rows
returns the first limit rows
emits next_cursor from the last returned id when an extra row exists
reshapes template_id/template_version into object_template {id, version}
```

Current target profile:

```text
PostgreSQL statements     1
tables                    objects only
projected columns         4
cache                     0
model-plane reads         0
component reads           0
relationship reads        0
lifecycle reads           0
explicit locks            0
multi-statement coherence 0
denormalization required  0
```

The route must not read:

```text
properties JSONB
revision
object_component_slots
object_components
ObjectTemplate rows/effective-schema materializations
DataType state
Relationship state
Lifecycle state
worker-local semantic caches
```

The persisted `(template_id, template_version)` is already the Object's current exact binding and is reported as current state. LIST does not re-admit or reinterpret that binding against current ObjectTemplate lifecycle/default state.

An Object may therefore remain visible with a binding to an exact ObjectTemplateVersion that is now DEPRECATED; LIST reports the current Object state and does not ask whether the same exact version would be admissible for a new binding today.

## Consistency and concurrency

One authoritative PostgreSQL statement is the complete public projection. Its statement snapshot is the complete read-consistency boundary.

No explicit row locks, optimistic fingerprints, revision checks, retries, coherent multi-statement read protocol or REPEATABLE READ transaction are required.

Concurrent Object mutations are observed according to ordinary statement visibility:

```text
CREATE
    -> row absent before commit / visible after commit

DELETE
    -> row visible before commit / absent after commit

RENAME
    -> old or new canonical_name from one row version in one statement snapshot

SCHEMA_CHANGE
    -> old or new exact binding from one row version in one statement snapshot
```

The page cannot mix fields from multiple independently observed Object generations because every summary is read by the same statement.

## Complexity and weight

Let:

```text
L = requested page limit, 1..500
```

Target cost:

```text
PostgreSQL business statements    1
rows materialized                 at most L + 1
response items                    at most L
application work                  O(L)
response payload                  O(L)
cache/model/schema/graph work      0
warm/cold distinction             none
```

plus PostgreSQL filtering/keyset access cost.

The route does not scale with:

```text
Object property count
component count
ownership depth
ObjectTemplate inheritance depth
Relationship count
lifecycle-event count
```

## Relational implication

LIST introduces no route-specific persistence requirement:

```text
new table             none
new persisted field   none
new materialization   none
new cache             none
new semantic invariant none
```

The route consumes only current `objects` summary columns and introduces no M4 denormalization/materialization requirement.

## Architecture handoff

The logical route is full-sweep complete.

Deferred only to the later architecture-wide physical-design phase:

```text
final physical index set
final PostgreSQL plan/EXPLAIN evidence
```

No route-local physical index is ratified during discovery. Architecture must evaluate Object LIST together with the complete Object workload and preserve:

```text
one authoritative PostgreSQL statement
bounded limit + 1 work
keyset ordering by Object id
exact filter semantics
no properties JSONB read
no component/model/cache work
```

## Full-sweep closure

The logical `GET /objects` route is **full-sweep complete** on:

```text
public route/query/summary contract
exact non-polymorphic filter semantics
strict request/cursor validation and failure precedence
keyset cursor identity and limit independence
empty-filter result vs error semantics
one-statement current data path
statement-snapshot concurrency semantics
bounded L+1 cost profile
no cache/model/component/relationship/lifecycle dependency
no new relational/materialization requirement
architecture physical-index/plan handoff
no diagnostic-only follow-up reads
```

# 3. GET Object

## Public contract

```http
GET /api/v1/core/objects/{object_id}
```

Path:

```text
object_id UUID
```

Query parameters: none.

Request body: none.

Static/request-shape failures are:

```text
malformed object_id
any query parameter
request body present
    -> 400 invalid_request
```

Missing Object:

```text
404 resource_not_found
```

Success representation:

```json
{
  "id": "<object-id>",
  "canonical_name": "server-1",
  "object_template": {
    "id": "<template-id>",
    "version": 4
  },
  "properties": {
    "hostname": "srv01"
  },
  "components": {
    "interfaces": [
      {
        "id": "<child-id>",
        "canonical_name": "eth0"
      }
    ],
    "disks": []
  }
}
```

Conceptual DTO:

```text
ObjectDto
    id
    canonical_name
    object_template {id, version}
    properties
    components: map<slot_name, ObjectReference[]>

ObjectReference
    id
    canonical_name
```

`properties` is the complete current canonical sparse property map.

`components` contains every current effective slot, including empty slots. If the Object has no component slots:

```json
"components": {}
```

Child Objects stop at `{id, canonical_name}`; child properties/components are never recursively expanded.

Explicit exclusions:

```text
owner
relationships
slot_declaring_template_id
child properties
recursive child components
ObjectTemplate mutable metadata
revision
```

Child arrays are deterministic by `child_object_id ASC`. JSON object-key order is not contractual.

## Revalidated data path after `object_component_slots`

The previous warm/cold component-schema-cache path is superseded as the preferred GET candidate.

Given that `object_component_slots` exists for cross-operation reasons and is atomically maintained with the Object exact binding, GET should consume that current materialization directly rather than reconstruct the same complete slot set from exact-schema cache on every normal read.

Current logical sources:

```text
objects parent
object_component_slots
object_components
objects child
```

Preferred route-local candidate:

```text
1 authoritative PostgreSQL statement
0 component-schema cache lookups
0 ObjectTemplate/model-plane reads
0 explicit locks
1 statement snapshot
```

Logical information returned by the statement:

```text
ROOT
    id
    canonical_name
    template_id
    template_version
    properties

SLOT FACTS
    slot_declaring_template_id
    slot_name

CHILD FACTS
    slot_declaring_template_id
    slot_name
    child_object_id
    child_canonical_name
```

Application assembly remains preferred:

```text
initialize every SLOT as []
append CHILD facts to the matching semantic slot
expose public key by slot_name
build ObjectDto
```

Internal grouping uses:

```text
(slot_declaring_template_id, slot_name)
```

while the public representation exposes only `slot_name`.

The SQL carrier must preserve:

```text
parent absent
    -> 404

parent present + zero slots
    -> 200 with components = {}

slot present + zero children
    -> slot present as []

slot populated
    -> current children with current canonical names
```

The preferred logical result must avoid transferring the potentially large root `properties` payload once per child. The exact physical carrier remains open between equivalent one-statement realizations such as aggregated fact carriers or tagged fact streams.

Required logical work:

```text
O(1 + S + C)
```

where:

```text
S = current effective slot count
C = direct child count
```

The typical workload expectation used in this revalidation is:

```text
S << C
```

The GET must read the `C` membership/child facts anyway, so reading the additional `S` small current-slot facts is a small incremental data-plane cost in the common case.

Key comparison:

```text
former warm path
    2 DB statements
    + exact component-schema cache lookup
    + coherent multi-statement read requirement
    + slot facts from worker memory

current materialized-slot candidate
    1 DB statement
    + S small current slot facts
    + no component-schema cache dependency
    + no multi-statement coherent-read protocol
```

Because slot materialization exists independently for other Object workloads, its storage/write-maintenance cost is not attributed to this GET decision.

## Concurrency/read semantics

One response must be explainable by one current PostgreSQL statement snapshot.

```text
SCHEMA_CHANGE
    -> old binding + old slot set OR new binding + new slot set
    -> never a cross-generation mixture

ATTACH
    -> child absent before commit / present after commit

DETACH
    -> child present before commit / absent after commit
    -> slot remains visible as [] when last child is removed

child RENAME
    -> old or new child canonical_name from the same statement snapshot

parent RENAME / properties mutation
    -> old or new root state from the statement snapshot

DELETE
    -> existing Object representation or 404 according to snapshot visibility
```

The GET does not expose or use `revision` merely to provide a current representation. The statement snapshot is already the complete read-consistency boundary.

The GET does not re-certify the materialized slot invariant against model-plane schema. Invariant verification belongs to write constraints, migration verification, tests/evidence or diagnostic tooling, not to the normal hot read path.

## Failure semantics and precedence

Bounded public failure set:

```text
400 invalid_request
404 resource_not_found
500 internal_error
```

Normal precedence:

```text
1. malformed/static request carrier
       -> 400 invalid_request

2. authoritative current-state statement
       Object absent
           -> 404 resource_not_found
              resource_type = object

       Object present + complete mandatory projection materializable
           -> 200 ObjectDto

       mandatory persisted/current state cannot be materialized
           -> 500 internal_error
```

Examples of the final class include required UUID/string/integer/JSON carrier failure or an impossible missing/ambiguous structural fact encountered while constructing the mandatory representation. The route does not add backend work solely to determine a more specific cause.

There is no normal GET-Object:

```text
409
422
```

No diagnostic-only follow-up query is permitted solely to enrich an impossible or ambiguous result.

## Cost profile

Let:

```text
P = size of the current properties representation
S = current effective slot count
C = direct child count
```

Target profile:

```text
PostgreSQL business statements    1
row/fact structural work          O(1 + S + C)
semantic response/payload size    O(P + S + C)
application assembly              O(S + C) + properties decode/copy cost proportional to P
cache/model/schema work           0
revision dependency               0
explicit locks                    0
lifecycle work                    0
warm/cold distinction             none
```

The one-statement carrier must avoid an effective `O(P * C)` transfer caused by repeating the root properties payload for every child fact. Root properties are transferred once logically.

## Relational implication

GET Object introduces no route-specific persistence structure or invariant:

```text
new table             none
new persisted field   none
new materialization   none
new cache             none
new semantic invariant none
```

It consumes the already-reviewed `objects`, `object_component_slots` and `object_components` candidates. `object_component_slots` exists for cross-operation reasons and is consumed by this GET; this route is not an independent semantic authority for that materialization.

## Architecture handoff

Still physical/open:

```text
exact SQL/SQLAlchemy carrier
aggregated facts vs tagged row stream
root-preserving absence discrimination
final PK/UNIQUE/FK realization
final indexes
EXPLAIN/BUFFERS evidence
real payload/runtime measurements
```

These physical choices must preserve:

```text
one authoritative statement
root transferred once logically
O(P + S + C) semantic payload/work
complete current slot set including empty slots
complete direct-child set
child ordering by child_object_id ASC
no model/cache/schema reconstruction
no diagnostic follow-up query
application-side components assembly
```

## Full-sweep closure

The logical `GET /objects/{object_id}` route is **full-sweep complete** on:

```text
strict UUID/no-query/no-body request surface
complete ObjectDto with all current direct slots and children
empty-slot and zero-slot representation semantics
bounded 400/404/500 failure precedence
one authoritative current data-plane statement
no component-schema/model/cache/revision/lock/lifecycle dependency
statement-snapshot concurrency semantics
formal O(P + S + C) payload/work profile
deliberately unbounded direct-child fan-out with no pagination, truncation or backend cardinality guard
no new relational/cache/materialization requirement
architecture one-statement/root-payload/index/plan handoff
no diagnostic-only follow-up reads
```

Direct-child fan-out is deliberately unbounded in the current M4 contract. `GET /objects/{id}` returns the complete first-level child set with no pagination, truncation or backend cardinality guard. The `O(P + S + C)` cost therefore intentionally remains proportional to the current direct-child count `C`.

# 4. Mutate canonical name — full sweep complete

## Public contract

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
Content-Type: application/json
```

Path:

```text
object_id UUID
```

Query parameters: none.

Request:

```json
{
  "canonical_name": "server-2"
}
```

`canonical_name` is required and remains:

```text
string
1..255 characters
no automatic normalization
not unique
not Object identity
```

Malformed body/carrier, missing or explicit-null `canonical_name`, empty string and values longer than 255 characters belong to the normal:

```text
400 invalid_request
```

Success:

```http
204 No Content
```

The mutation returns no Object representation. Current state remains owned by `GET /objects/{id}`.

Missing path target:

```text
404 resource_not_found
```

## Same-name assignment

The operation is assignment:

```text
Object O canonical_name := requested_name
```

not a change-only-if-different command.

Therefore:

```text
current name differs
    -> normal successful mutation
    -> 204

current name already equals requested name
    -> normal successful mutation
    -> 204
```

No equality precheck is introduced solely to classify same-name requests. A successful same-name assignment follows the normal RENAME lifecycle path and may record:

```text
old_name == new_name
```

Same-name assignment is a persisted intrinsic mutation and therefore advances technical `revision` like any other successful RENAME.

This is intentionally distinct from DATA_CHANGE, where a cheap semantic no-op can commit no state transition and therefore no revision/lifecycle.

## Semantic responsibility boundary

RENAME changes only:

```text
canonical_name
```

It preserves and does not re-certify:

```text
Object.id
Object.template_id
Object.template_version
Object.properties
ownership/component facts
factual Relationships
```

`revision` advances as technical intrinsic-generation metadata; that does not widen RENAME's business semantic responsibility.

Normal RENAME therefore requires no:

```text
ObjectTemplate reads
DataType reads
effective-schema reconstruction
ancestry reads
ownership reads
Relationship reads
semantic cache
```

RENAME is not a domain consistency sweep. It validates caller-supplied `canonical_name` and pays only for the current-state/lifecycle facts that its own contract changes.

## Lifecycle — exact minimal semantic transition

M4 uses the general lifecycle principle:

```text
lifecycle payload
    = complete exact semantic transition owned by the operation

not automatically
    = complete aggregate before + complete aggregate after
```

For RENAME the complete semantic transition is exactly:

```text
canonical_name: old -> new
```

Conceptually:

```text
RENAME event
    object_id = O

    before:
        canonical_name = exact old_name

    after:
        canonical_name = requested_name
```

Equivalent generic JSON-carrier direction:

```json
{
  "before": {
    "canonical_name": "server-1"
  },
  "after": {
    "canonical_name": "server-2"
  }
}
```

The event must not duplicate unchanged/technical state merely for payload uniformity:

```text
id inside before/after when object_id already identifies the event subject
template_id
template_version
properties
revision
ownership/components
Relationships
```

The historical transition remains exact. What is removed is irrelevant unchanged state, not precision.

## Ratified logical execution/data path

RENAME uses the universal intrinsic-generation rule from [`object-revision.md`](object-revision.md).

```text
validate canonical_name
    -> CPU only

Q1
    read one current Object generation:
        id
        canonical_name = old_name
        revision = R

    absent
        -> 404 resource_not_found

Q2
    commit only against expected_revision = R

    canonical_name := requested_name
    revision       := R + 1
    append exactly one RENAME lifecycle event:
        old_name -> requested_name
```

If Q2 observes that revision `R` is no longer current:

```text
stale attempt
    -> no Object mutation
    -> no lifecycle
    -> bounded retry from a fresh Object generation
```

The universal generation CAS replaces a separate canonical-name-specific logical freshness mechanism. Exact SQL/lock/wait realization remains architecture work.

Preferred uncontended successful cost:

```text
2 PostgreSQL business statements + COMMIT

Q1
    exact old-name + revision read

Q2
    expected-revision canonical_name + revision UPDATE
    + RENAME lifecycle INSERT
```

There is no warm/cold distinction.

Data/cache profile:

```text
current Object columns needed
    id
    canonical_name
    revision

properties JSONB read
    0

ObjectTemplate/DataType reads
    0

component/ownership reads
    0

Relationship reads
    0

semantic cache
    0
```

## Concurrency outcomes

All intrinsic Object writers use the same expected-revision generation protocol.

```text
RENAME x RENAME
    -> one writer advances R -> R+1
    -> the other stale attempt retries
    -> each successful assignment records exact old -> new

RENAME x DATA_CHANGE
    -> one commits first and advances revision
    -> other stale attempt retries even though fields are semantically independent
    -> conservative retry is intentional

RENAME x SCHEMA_CHANGE
    -> same universal generation ordering/retry

RENAME x DELETE
    -> RENAME commits first and DELETE may remove the resulting generation
       OR DELETE wins and a fresh retry observes absence
    -> no mutation-after-delete / resurrection
```

RENAME is semantically independent from ATTACH/DETACH ownership state. If ownership or factual Relationship mutations require coherent historical display names, that observation belongs to those mutations' own lifecycle responsibility; RENAME does not load or validate their state.

The accepted conservative false-positive retries keep one intrinsic generation mechanism instead of operation-specific freshness exceptions. If measured same-Object contention later proves the trade-off unacceptable, the cross-operation revision decision may be reopened.

## Failure mapping

Bounded public failures remain:

```text
400 invalid_request
    malformed/static transport input
    invalid canonical_name carrier/value

404 resource_not_found
    selected Object absent on the authoritative generation read/retry

500 internal_error
    unexpected persistence/lifecycle/invariant failure
    bounded generation retry cannot stabilize
```

Revision mismatch itself is internal stale-attempt control flow, not a public `409` conflict.

The route introduces no:

```text
409 state-conflict class
422 semantic/dependency admission class
canonical-name uniqueness conflict
schema admission
ownership admission
```

## Cache / relational implications

No cache is useful or required.

No route-specific table, denormalization, materialization or index is introduced. The operation uses current `objects.revision`, current canonical name and Object lifecycle persistence.

## Architecture handoff and full-sweep closure

The logical `PUT /objects/{id}/canonical-name` route is full-sweep complete, including the focused revision revalidation.

Deferred only to architecture-wide realization:

```text
exact expected-revision SQL / SQLAlchemy carrier
exact PostgreSQL lock / wait behavior under CAS contention
bounded retry count/backoff
final UPDATE + lifecycle statement fusion
lifecycle physical JSON/typed carrier and constraints
physical index / EXPLAIN evidence
```

No PostgreSQL-major-specific `OLD/NEW` facility is part of the M4 semantic contract.

Architecture must preserve:

```text
exact old canonical_name from generation R
exact requested/new canonical_name
expected_revision stale-success protection
atomic canonical_name + revision R+1 + RENAME lifecycle
serially explainable same-Object intrinsic generations
no lost same-field rename transition
no mutation-after-delete / resurrection
```

# 5. Mutate Object properties — full sweep complete

## Public contract

```http
POST /api/v1/core/objects/{object_id}/properties
Content-Type: application/json
```

Path:

```text
object_id UUID
```

Query parameters: none.

Request:

```json
{
  "operations": [
    {"op": "SET", "property": "hostname", "value": "srv02"},
    {"op": "REMOVE", "property": "description"}
  ]
}
```

Conceptual transport model:

```text
ObjectPropertiesMutationBody
    operations: PropertyOperation[1..N]

PropertyOperation
    SET
        property: string
        value: JsonValue

    REMOVE
        property: string
```

Static/request-shape rules:

```text
operations required and non-empty
same property at most once per request
SET requires value
REMOVE forbids value
array order has no semantic mutation-order meaning
request is atomic; no partial success
```

No new wire-level property-name regex is introduced. `property` is structurally a string; property existence belongs to exact-schema semantic validation.

Malformed body/carriers, empty/missing operations, unknown `op`, duplicate operations for one property, SET without value, REMOVE with value and unknown body fields are:

```text
400 invalid_request
```

A SET `value: null` is structurally interpretable JSON but semantically invalid runtime property state; it is never REMOVE/omission.

Sparse property semantics:

```text
REMOVE optional
    -> key absent

SET optional LIST = []
    -> canonical absence / prepared REMOVE

SET runtime JSON null
    -> semantic validation failure

REMOVE required
    -> semantic validation failure

SET required LIST = []
    -> semantic validation failure
```

Success:

```http
204 No Content
```

The canonical current Object representation remains the responsibility of `GET /objects/{id}`.

DATA_CHANGE semantically changes only runtime properties. It does not directly change/re-certify Object id, canonical name, ObjectTemplate lineage/exact version, components/ownership or Relationships. A persisted real DATA_CHANGE also advances technical intrinsic `revision` according to the shared generation contract.

## Semantic no-op and cost rule

A semantic no-op returns:

```http
204 No Content
```

and may elide all persistence/history work when recognizing it falls naturally out of the normal application-side operation application.

Canonical rule:

```text
cheaply recognized no-op
    -> no Object UPDATE
    -> no revision increment
    -> no DATA_CHANGE lifecycle

recognizing no-op would require material extra work
    -> normal persisted mutation is allowed
    -> throughput is preferred over artificial no-op classification work
```

No-op classification must not introduce solely for that purpose:

```text
additional PostgreSQL statement
additional lock / lock round trip
additional semantic cache/model lookup
second whole-property-map equality pass
whole-Object recertification
```

With the current application-layer mutation direction, the route already examines each requested key while applying prepared operations to the current full property map:

```text
SET p = canonical V
    current p == V
        -> operation contributes no change

REMOVE p
    p absent
        -> operation contributes no change
```

A `changed` flag and lifecycle delta are accumulated in that same requested-operation pass; no later `candidate == before` whole-map comparison is required merely to classify the result.

If all requested effects are no-ops, STEP 3 is skipped entirely. A concurrent intrinsic mutation after the coherent generation read does not invalidate the response because this no-op command persisted no state and is serially explainable before the later mutation.

## Execution/data-path direction

The ratified logical path has three stages:

```text
STEP 1 — read one current intrinsic Object generation
    PostgreSQL

STEP 2 — READY semantic preparation + application-side complete candidate derivation
    worker-local immutable cache + application/domain layer

STEP 3 — expected-revision commit UoW for real changes only
    PostgreSQL
```

Authority split:

```text
PostgreSQL
    -> authoritative current state
    -> expected-revision generation arbitration
    -> atomic current-state + lifecycle persistence

application/domain layer
    -> SET/REMOVE semantics
    -> requested-effect validation/canonicalization
    -> complete property-map transformation
    -> semantic no-op detection
    -> exact DATA_CHANGE lifecycle-delta derivation
```

PostgreSQL JSONB mutation primitives are **not** the normal M4 DATA_CHANGE semantic mutation layer. A real mutation persists the complete application-derived `properties` candidate. DB-side JSON mutation remains only a future evidence-driven optimization possibility.

### STEP 1 — current mutation generation

One current-state read supplies:

```text
ObjectMutationGeneration
    object_id
    template_id
    template_version
    revision = R
    complete properties
```

Conceptually:

```sql
SELECT template_id, template_version, revision, properties
FROM objects
WHERE id = :object_id;
```

Exact SQL/transaction realization remains architecture work.

Absent Object:

```text
404 resource_not_found
```

The exact persisted binding selects immutable validation semantics. Existing Objects pinned to a DEPRECATED exact OTV remain mutable; DATA_CHANGE is not new model-plane binding admission and does not require current PUBLISHED/default/latest status.

### STEP 2 — READY semantics and requested-effect validation

Missing immutable semantic knowledge is completed outside the commit UoW. Normal DATA_CHANGE must not traverse ObjectTemplate/DataType persistence ad hoc per property.

Required immutable knowledge includes:

```text
effective property declaration
    declaring_template_id
    property name
    value_mode
    required
    exact datatype_id/version pin

exact DataTypeVersion semantics
    primitive/base type
    canonical constraints

compiled/runtime validators where useful
```

No Object lock is held during cache fill, validation, canonicalization or application-side candidate construction.

DATA_CHANGE validates/canonicalizes **only requested effects**:

```text
SET p
    p exists
    correct SCALAR/LIST shape
    exact PrimitiveType validation/canonicalization
    exact DTV constraints
    required LIST is non-empty
    optional LIST=[] -> canonical absence
    JSON null invalid

REMOVE p
    p exists
    p.required == false
```

Consequent semantic failures are:

```text
unknown property
REMOVE required
SET null
SCALAR/LIST mismatch
primitive validation failure
exact DTV constraint failure
required LIST=[]
    -> 422 semantic_validation_failed
```

Untouched persisted properties are trusted as already-admitted current state and preserved without:

```text
PrimitiveType reparse
DTV constraint recheck
recanonicalization
whole-map semantic recertification
```

This local proof depends on the current property model having no independent cross-property invariant that must be recomputed after every SET/REMOVE. Introducing such an invariant reopens DATA_CHANGE.

Semantic validation cost is therefore:

```text
O(requested operation count + supplied-value size)
```

Complete candidate materialization is separately proportional to current property-map size because the application intentionally builds a complete replacement value; that is persistence/application work, not full-map semantic recertification.

Prepared operations retain lifecycle semantic identity:

```text
PropertySemanticKey
    = (declaring_template_id, property_name)
```

Application application against generation `R` derives in one requested-operation pass:

```text
candidate_properties
changed yes/no
for each requested semantic property:
    old canonical value | ABSENT
    new canonical value | ABSENT
```

Untouched keys are copied/preserved exactly, not revalidated.

A semantic failure proved against coherent generation `R` may be returned immediately without a revision refresh solely to see whether a concurrent mutation removed the failure. Such a conservative stale failure cannot commit invalid state; a later caller retry naturally evaluates the newer generation.

### STEP 3 — real-change expected-revision replacement

STEP 3 runs only when application-side derivation found at least one actual property transition.

Prepared commit input:

```text
object_id
expected_revision = R
complete candidate_properties
exact binding context T@V
exact changed-property lifecycle delta
```

The final write may commit only if generation `R` is still current:

```text
current revision == R
    -> properties := complete candidate_properties
    -> revision   := R + 1
    -> append exactly one DATA_CHANGE lifecycle delta
    -> COMMIT

current revision != R
    -> stale attempt
    -> no Object mutation
    -> no lifecycle
    -> bounded retry
```

A successful revision check also proves that no committed intrinsic SCHEMA_CHANGE altered the binding since STEP 1; no second binding-freshness mechanism is needed for the same generation.

Properties replacement, revision increment and lifecycle append are atomic. If lifecycle persistence fails, the new Object generation must not commit.

Logical target for a real mutation is one final PostgreSQL business statement for CAS/write+lifecycle where practical. Exact DML/CTE/RETURNING realization is architecture work and must not move JSON semantic mutation into SQL merely for fusion.

## Retry behavior

Revision mismatch is internal stale-attempt control flow, not a public business conflict.

On stale CAS:

```text
persist nothing
emit no lifecycle
return to normal STEP 1
```

The fresh STEP 1 naturally distinguishes:

```text
Object absent
    -> 404 resource_not_found

Object present at newer revision
    -> continue retry
```

No diagnostic query is added solely to classify a zero-row CAS result.

After re-read:

```text
same exact binding T@V
    -> immutable prepared/canonical requested operations remain reusable
    -> re-apply them to fresh complete properties
    -> derive fresh candidate/delta/no-op

different exact binding T@W
    -> resolve READY T@W semantics
    -> revalidate/canonicalize original requested effects
    -> apply to fresh properties
```

No cache fill occurs while holding a final commit boundary.

Retry is bounded. If revision cannot stabilize within the bounded policy:

```text
500 internal_error
```

No route-local `409 concurrent_modification` / state-conflict response is introduced.

## DATA_CHANGE lifecycle — exact operation-owned delta

Lifecycle records the complete exact semantic transition DATA_CHANGE owns, not whole Object snapshots.

Event context:

```text
object_id
exact ObjectTemplate binding:
    template_id
    template_version
```

Each actually changed property is identified by:

```text
PropertySemanticKey
    declaring_template_id
    property_name
```

and records:

```text
before
    canonical value | ABSENT

after
    canonical value | ABSENT
```

`ABSENT` is a semantic state distinct from JSON `null`; runtime null is invalid property state.

Examples:

```text
SET previously absent p = V
    ABSENT -> canonical V

SET p = V2
    canonical V1 -> canonical V2

REMOVE existing optional p
    canonical V -> ABSENT
```

Only actual state changes appear. No-op requested operations in a mixed request are omitted from lifecycle history.

DATA_CHANGE lifecycle does not duplicate:

```text
canonical_name
revision
unchanged properties
components / ownership
Relationships
complete Object before snapshot
complete Object after snapshot
```

The delta is semantic history, not a raw request audit log. `revision` remains technical generation metadata and is not automatically lifecycle payload.

Exact persistence/detail DTO carrier remains Lifecycle architecture/API work, but must preserve exact binding context, semantic property identity, value-vs-ABSENT and only changed properties.

## Concurrency outcomes

All intrinsic Object writers use the universal revision protocol.

```text
DATA_CHANGE x DATA_CHANGE
    both read R
    first real writer -> complete properties replacement + R+1 + lifecycle
    second CAS on R -> stale, retries from R+1
    -> no lost full-JSON replacement

DATA_CHANGE x RENAME
    one advances revision
    other stale attempt retries
    -> conservative retry is intentional despite independent business fields

DATA_CHANGE x SCHEMA_CHANGE
    DATA_CHANGE first -> SCHEMA_CHANGE prepared on old generation must retry
    SCHEMA_CHANGE first -> DATA_CHANGE old-binding candidate cannot CAS
                         -> retry/revalidate on new binding

DATA_CHANGE x DELETE
    DATA_CHANGE first -> DELETE may remove resulting generation
    DELETE first -> fresh retry observes absence
    -> no resurrection
```

Exact PostgreSQL wait/lock behavior remains architecture work.

## Cache behavior

Warm exact binding:

```text
STEP 1
    full current Object generation read

STEP 2
    READY cache HIT
    validate/canonicalize requested effects
    application-side candidate + delta

no-op
    -> return immediately

real change
    -> STEP 3 expected-revision replacement + lifecycle
```

Cold/partial exact binding adds only bounded immutable semantic-cache fill outside the commit UoW.

A stale retry with unchanged exact binding reuses READY semantics and prepared canonical operations, but always re-reads/re-applies against fresh full current properties.

## Cost and physical trade-off

Warm real change target:

```text
S1
    one Object PK read:
        template_id
        template_version
        revision
        full properties

STEP 2
    cache HIT + requested-effect validation
    application full candidate construction
    lifecycle delta derivation

S2
    expected-revision complete properties replacement
    + revision R+1
    + DATA_CHANGE lifecycle append

COMMIT
```

Target:

```text
2 PostgreSQL business statements + COMMIT
```

Warm semantic no-op target:

```text
S1 full current generation read
STEP 2 detects zero changes
return 204

= 1 PostgreSQL business statement
= 0 UPDATE / lifecycle / revision increment
```

Application-side complete replacement intentionally pays:

```text
full properties DB -> worker
application decode/copy/mutation
full candidate encode
full candidate worker -> DB on real change
```

in exchange for keeping JSON semantic mutation in application/domain code and keeping the database focused on current-state authority, generation CAS, referential integrity and atomic persistence.

M4 does not assume DB-side JSONB patching would remove PostgreSQL MVCC/WAL/TOAST write cost. Architecture must benchmark realistic property-map sizes/frequencies/contention/network/Python CPU/PostgreSQL CPU/WAL/TOAST/p50-p99 latency before physical freeze. Evidence may reopen the physical realization, but PostgreSQL JSON mutation primitives are not the current baseline.

Invariant/audit tooling may separately verify persisted canonical/current Object state; removal of hot-path recertification does not require every consistency diagnostic to disappear from the system.

## Failure mapping and precedence

Public set:

```text
400 invalid_request
    malformed/static request

404 resource_not_found
    Object absent on authoritative STEP 1 / retry

422 semantic_validation_failed
    unknown property
    REMOVE required
    SET null
    wrong SCALAR/LIST shape
    primitive validation failure
    exact DTV constraint violation
    required LIST=[]

500 internal_error
    required persisted semantic dependency unexpectedly missing/corrupt
    persistence/lifecycle invariant failure
    bounded revision retry exhaustion
```

No normal `409` is introduced for revision contention.

Precedence:

```text
static transport validation
    -> coherent Object generation read
    -> requested-effect semantic validation
    -> candidate/no-op derivation

semantic failure
    -> return 422; no revision refresh solely to eliminate conservative stale failure

no-op
    -> return 204; no revision refresh because no state is committed

real mutation
    -> expected_revision CAS
       stale -> bounded retry from STEP 1
       fresh success -> atomic properties + revision + lifecycle
```

A fresh retry determines the current outcome; for example a SCHEMA_CHANGE between attempts may turn a formerly valid property operation into a new `422`, or DELETE may turn the retry into `404`.

## Data structures / architecture handoff and closure

DATA_CHANGE adds no route-specific table or denormalization.

Mutable state:

```text
objects
    read exact binding + revision + full properties
    replace complete properties on real change
    advance revision atomically

object_lifecycle_events
    exactly one DATA_CHANGE delta event on real change
```

Immutable semantic dependencies:

```text
worker-local ObjectTemplate effective-property validation facet
worker-local exact DataTypeVersion semantics/validators
bounded certified semantic loader for cold fills
```

Normal DATA_CHANGE does not require:

```text
object_components
Relationship runtime state
ObjectTemplate current default
ObjectTemplate current lifecycle status
```

Deferred physical architecture work:

```text
exact SQL/SQLAlchemy generation-read carrier
exact CAS UPDATE + lifecycle fusion carrier
exact PostgreSQL wait/locking realization
bounded retry count/backoff
physical indexes / EXPLAIN evidence
JSONB/TOAST/WAL measured costs
lifecycle physical detail carrier/constraints
```

Architecture must preserve:

```text
application owns JSON mutation semantics
one coherent generation supplies source full properties
requested effects only are semantically validated
untouched values are preserved without recertification
real write is guarded by expected_revision
stale candidate can never overwrite newer intrinsic state
real DATA_CHANGE atomically writes complete properties + revision+1 + exact lifecycle delta
cheap semantic no-op performs no write/revision/lifecycle
no diagnostic-only DB reads for stale classification
```

The logical `POST /objects/{id}/properties` route is **full-sweep complete**.

# 6. GET current Object schema binding — full sweep complete

## Public contract

```http
GET /api/v1/core/objects/{object_id}/schema
```

Path:

```text
object_id: UUID
```

Query parameters: none.

Request body: none.

Success:

```json
{
  "template_id": "<template-id>",
  "template_name": "Server",
  "version": 4
}
```

Conceptual DTO:

```text
ObjectSchemaBindingDto
    template_id: UUID
    template_name: string
    version: positive integer
```

The route answers only:

```text
which exact ObjectTemplate binding governs this Object now?
```

It deliberately does not become a second effective-schema API. The detailed model-plane surface remains:

```http
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
```

Explicitly excluded from the Object-relative schema response:

```text
namespace
description
abstract
status
revision
parent binding
properties
effective properties
components
effective components
DataType semantics
```

`template_id` is the authoritative ObjectTemplate-lineage identity. `template_name` is stable human-readable convenience only and does not participate in identity. Exact schema identity remains `(template_id, version)`.

## Read/data path

The route is a bounded current-state read over one Object and its stable ObjectTemplate lineage header.

Required logical access path:

```text
objects PK(object_id)
    -> template_id
    -> template_version

object_templates PK(template_id)
    -> stable template_name
```

One coherent PostgreSQL statement supplies the complete public result. A simple join is one acceptable realization, but M4 does not freeze textual SQL or join order; architecture must prove the bounded PK -> PK access path with physical-plan evidence.

The route does **not** read `object_template_versions` merely to restate or re-admit the exact version:

```text
no exact OTV status read
no PUBLISHED/DEPRECATED admission
no default/latest resolution
no effective-schema reconstruction
```

The persisted `(template_id, template_version)` is already the Object's exact current binding. Existing Objects pinned to a DEPRECATED exact version remain normal `200` results.

Current database integrity already constrains `objects(template_id, template_version)` to an existing exact ObjectTemplateVersion, whose lineage in turn depends on `object_templates`. The normal GET therefore trusts the admitted referential invariant rather than adding a second diagnostic query to search for impossible corruption.

## Cache / denormalization decision

```text
0 cache
0 denormalized template_name on objects
```

Although `ObjectTemplate.name` is stable and cacheable, PostgreSQL must already be consulted for current Object existence and exact binding. Reading the stable lineage name through the same bounded PK-to-PK statement is simpler than splitting one response across database state and a worker-cache lookup/fill and does not add a round trip.

## Coherence and concurrency

One statement snapshot is the complete coherence boundary. The route needs no locks, retry protocol or `revision` read merely to return current state.

```text
GET schema x SCHEMA_CHANGE
    statement before schema-change commit
        -> old exact version
    statement after schema-change commit
        -> new exact version
    -> never an intermediate/mixed Object binding

GET schema x DELETE
    statement snapshot sees Object
        -> 200
    statement snapshot sees committed absence
        -> 404
```

RENAME, DATA_CHANGE, ATTACH, DETACH and factual Relationship mutations require no special coordination with this GET because they do not change the public facts projected by this route. PostgreSQL's ordinary statement visibility is sufficient.

Technical `objects.revision` is neither projected nor read for coherence. A pure read does not become a public CAS/versioning surface merely because the intrinsic row carries a generation token.

## Failure mapping and precedence

Bounded public failure set:

```text
400 invalid_request
    malformed/static request carrier
    malformed object_id carrier
    unsupported query/body carrier

404 resource_not_found
    selected Object path target absent

500 internal_error
    impossible required persisted dependency/invariant failure encountered
    unexpected database/persistence failure
```

There is no normal:

```text
409 state conflict
422 semantic/dependency admission failure
```

Precedence:

```text
1. static transport validation
       -> 400 invalid_request

2. authoritative single-statement read
       Object absent
           -> 404 resource_not_found

       required persisted dependency inconsistency incidentally detected
           -> 500 internal_error

       normal row
           -> 200
```

The route does not add a second PostgreSQL query solely to distinguish or diagnose corruption that the database referential model already prevents in admitted state. A chosen one-statement carrier may preserve the Object root explicitly if architecture wants incidental invariant detection, but that must not worsen the bounded one-statement path.

## Cost target

```text
1 PostgreSQL business statement
    Object PK lookup
    ObjectTemplate PK lookup

0 cache lookups
0 locks
0 retries
0 revision read
0 exact-OTV lifecycle/admission read
0 effective-schema/model reconstruction
0 lifecycle work
0 diagnostic-only follow-up reads
```

## Architecture handoff and full-sweep closure

The logical `GET /objects/{id}/schema` route is **full-sweep complete**.

Deferred only to architecture-wide physical design:

```text
exact SQL / SQLAlchemy carrier
exact join/root-preserving realization
final physical indexes
EXPLAIN (ANALYZE, BUFFERS) / equivalent plan evidence
```

Architecture must preserve:

```text
exact public DTO {template_id, template_name, version}
one coherent PostgreSQL statement
bounded Object PK -> ObjectTemplate PK access
no cache or template-name denormalization
no locks/retries/revision read
no exact-OTV admission/recertification
no effective-schema reconstruction
0 rows for absent Object -> 404
no diagnostic-only second query
```

# 7. POST Object schema change — full sweep complete

## Public contract

```http
POST /api/v1/core/objects/{object_id}/schema
Content-Type: application/json
```

Path:

```text
object_id: UUID
```

Query parameters: none.

Request:

```json
{
  "target_version": 5
}
```

Conceptual transport model:

```text
ObjectSchemaMutationBody
    target_version: positive integer
```

Unknown/malformed request carriers remain normal static invalid-request input.

The operation keeps the Object's stable `template_id` and selects one exact ObjectTemplateVersion inside that lineage.

Success:

```http
204 No Content
```

The resulting current state is read through:

```text
GET /objects/{id}
GET /objects/{id}/schema
```

## Exact-target command semantics

For current exact binding:

```text
SOURCE = T@VS
```

and request:

```text
TARGET = T@VT
```

SCHEMA_CHANGE is an **exact-target migration command**.

Canonical version rule:

```text
version number
    = exact-version identity
    + creation/allocation order within one lineage

version number
    != genealogy
    != semantic evolution order
    != compatibility order
    != migration order
    != publication order
```

Therefore:

```text
VT > VS
VT < VS
```

carry no migration-admission meaning by themselves. Terms such as upgrade/downgrade must not be inferred from the numeric relation alone.

Intermediate numeric versions are never replayed:

```text
T@VS -> T@VT
    = compare EffectiveSchema(T@VS) directly with EffectiveSchema(T@VT)
```

### Equal target is a semantic no-op

```text
VT == VS
    -> 204 No Content
    -> no MigrationPlan
    -> no Object UPDATE
    -> no slot DML
    -> no revision increment
    -> no SCHEMA_CHANGE lifecycle
```

The no-op is serially explainable at the coherent current generation observation. No final revision refresh/CAS is added solely to preserve the no-op through response time.

The current exact version may already be DEPRECATED. Equal-target success creates no new binding and therefore does not re-admit PUBLISHED status.

### Distinct target is a real new binding

```text
VT != VS
    -> exact SOURCE -> TARGET migration candidate
```

The real migration owns two separate questions:

```text
TARGET admission
    -> does exact T@VT exist and remain PUBLISHED through commit?

SOURCE -> TARGET migrability
    -> can this exact schema pair, and where required this concrete Object state,
       be migrated according to the rules below?
```

SOURCE is an already-current binding and may be PUBLISHED or DEPRECATED. It does not need a new PUBLISHED admission merely because the Object is leaving it.

## Exact schema comparison and semantic identity

The immutable planner compares:

```text
EffectiveSchema(SOURCE)
vs
EffectiveSchema(TARGET)
```

It does not derive runtime migration behavior from:

```text
numeric version order
version adjacency
intermediate versions
local declarations alone
name equality alone
current defaults
```

Property continuity:

```text
PropertySemanticKey
    = (declaring_template_id, property_name)
```

Component-slot continuity:

```text
SlotSemanticKey
    = (declaring_template_id, slot_name)
```

The same effective name under a different declaring lineage is semantic replacement, not continuity by name alone.

Differences caused by different exact parent-version pins are classified solely from the resolved SOURCE/TARGET effective schemas; declaration/inheritance provenance is not a separate runtime migration class.

## Immutable reusable MigrationPlan

For one exact pair:

```text
(template_id, source_version, target_version)
```

certified SOURCE/TARGET semantics are immutable. Therefore:

```text
MigrationPlan(T, VS, VT)
    = f(EffectiveSchema(T@VS), EffectiveSchema(T@VT))
```

is immutable and Object-independent.

Conceptual cache:

```text
ObjectTemplateMigrationPlanCache[(T, VS, VT)]
```

A READY plan may contain compiled immutable rules for:

```text
property semantic continuity/replacement
requiredness/add/remove
SCALAR/LIST transformation
conditional LIST -> SCALAR cardinality rule
TARGET exact-DTV validation/canonicalization
TARGET migration_default behavior
component semantic continuity/replacement
slot ADD/REMOVE/widening/position changes
categorically unsupported component target relations
current object_component_slots delta
```

It must not contain one Object's mutable:

```text
properties
canonical_name
ownership membership
revision
current TARGET lifecycle status
```

## MigrationPlan cache resolution

Normal execution consumes the same READY-plan path whether the plan was already cached or became READY during the request.

```text
HIT
    -> consume plan

MISS
    -> make required immutable semantic inputs READY
    -> compile/cache plan
    -> consume plan
```

Required immutable inputs are bounded by semantic class:

```text
SOURCE/TARGET certified exact effective ObjectTemplate closures
exact DataTypeVersion semantics referenced by SOURCE union TARGET
stable ObjectTemplate lineage ancestry required for component-target relation
```

Cold-loading rules:

```text
load only missing immutable entries
bulk homogeneous misses
no per-property DTV query
no per-slot ancestry query
no recursive inheritance reconstruction fallback
no one-off raw-DB planner path
```

Current cold upper-bound direction:

```text
missing SOURCE/TARGET exact closures
    -> at most 1 bounded bulk semantic-loader statement

missing exact DTV semantics
    -> at most 1 bounded bulk semantic-loader statement

missing stable ancestry sources
    -> at most 1 bounded bulk semantic-loader statement
```

Thus cold preparation adds `0..3` bounded semantic-loader classes, independent in round-trip count from inheritance depth and effective-member count. Payload naturally scales with returned semantics.

For certified PUBLISHED/DEPRECATED exact versions, unexpectedly missing/incomplete immutable materialization or referenced exact DTV state is an internal invariant failure. Runtime does not substitute default/latest/another exact version and does not fall back to recursive reconstruction.

## Property migration matrix

Target properties are built **from TARGET semantic properties**. The migration is not a textual JSON-key patch program.

For each TARGET semantic property, preparation selects exactly one of:

```text
preserved/transformed SOURCE semantic information
canonical TARGET migration_default
absence
```

SOURCE-only semantic properties are not selected into the target state.

### Add/remove

```text
ADD optional
    -> absent

ADD required
    -> canonical TARGET migration_default

REMOVE optional/required
    -> SOURCE semantic value omitted from TARGET state
```

Removed data is not archived or copied to an extras bucket.

### Requiredness

```text
optional -> required
    SOURCE value present
        -> preserve information
        -> apply all simultaneous TARGET transformations/validation
        -> incompatibility blocks this Object migration
        -> never replace existing incompatible information with migration_default

    SOURCE value absent
        -> canonical TARGET migration_default

required -> optional
    -> preserve existing information
    -> apply all simultaneous TARGET transformations/validation
    -> incompatibility blocks this Object migration
    -> never drop merely because TARGET permits absence
```

`migration_default` fills absence only; it is never remediation for incompatible existing information.

### SCALAR -> LIST

```text
SOURCE value present x
    -> [x]
    -> complete TARGET validation/canonicalization

SOURCE optional value absent
    -> absent unless independent TARGET requiredness supplies migration_default
```

### Conditional lossless LIST -> SCALAR

A continuous LIST property may migrate to SCALAR only when the concrete Object transformation preserves all information.

```text
SOURCE value absent
    -> TARGET absent
       unless independent TARGET requiredness supplies canonical migration_default

SOURCE value = [x]
    -> TARGET candidate x
    -> complete TARGET exact-DTV validation/canonicalization

SOURCE value contains more than one item
    -> 409 schema_change_blocked for this Object
```

Cardinality is literal:

```text
[x, x]
    -> two items
    -> not lossless
    -> blocked
```

LIST order and multiplicity are semantic runtime information. SCHEMA_CHANGE never performs:

```text
first-item selection
last-item selection
arbitrary item selection
deduplicate-then-collapse
drop-to-absence because TARGET is optional
migration_default replacement of incompatible existing information
```

### Exact DataTypeVersion change

For a continuous semantic property within the same stable `datatype_id` lineage:

```text
existing information
    -> preserve/shape-transform as applicable
    -> validate/canonicalize under TARGET exact DTV

TARGET incompatibility
    -> 409 schema_change_blocked for this Object
```

LIST order is preserved. No cross-DataType-lineage or cross-PrimitiveType conversion is invented by Object migration.

### Semantic replacement

Same textual name with different `PropertySemanticKey` means:

```text
REMOVE old semantic property
ADD new semantic property
```

No value carry-forward occurs merely because JSON field names match.

## Component-slot migration matrix

Current component runtime state uses the reviewed `object_component_slots` / `object_components` boundary.

For supported SOURCE -> TARGET slot deltas:

```text
ADD
    -> INSERT current slot row
    -> new semantic slot starts empty

REMOVE
    -> DELETE current slot row
    -> no implicit DETACH
    -> referenced old edge blocks final removal

same SlotSemanticKey + equal target
    -> preserve slot/edges

same SlotSemanticKey + target widening toward ancestor
    -> UPDATE target_template_id
    -> preserve edges
    -> no current-child compatibility revalidation

position-only
    -> no current-slot DML
    -> ownership unchanged

semantic replacement
    -> old semantic identity removed + new semantic identity added/replaced
    -> no implicit rebind/detach+reattach
    -> referenced old edge blocks replacement
    -> new semantic slot starts empty
```

Successful normal SCHEMA_CHANGE does not rewrite `object_components` membership.

### Categorically unsupported relations

For one continuous slot:

```text
SOURCE target ancestor
TARGET target descendant
    -> narrowing

SOURCE/TARGET targets unrelated
    -> unrelated relation
```

Both exact-pair relations are categorically non-migrable through normal SCHEMA_CHANGE:

```text
narrowing  -> 422 semantic_validation_failed
unrelated  -> 422 semantic_validation_failed
```

Current children never rescue the pair:

```text
zero children
all current children happen to satisfy narrower TARGET
```

are irrelevant to migration admission.

Operational consequence:

```text
0 current child reads
0 per-child compatibility checks
0 membership freshness/protection for component-target admission
```

The immutable MigrationPlan is sufficient to reject the pair.

### REMOVE/replacement blocker authority

Current membership matters only at the final relational slot boundary for REMOVE/semantic replacement.

With the reviewed edge -> current semantic-slot dependency:

```text
DETACH removes last old edge first
    -> slot removal/replacement may proceed

old edge still references slot at final transition
    -> slot DELETE/key change cannot commit
    -> 409 schema_change_blocked
```

No preparatory ownership snapshot, child list, blocker count or child-specific diagnostic read is required.

## One-generation preparation path

Each attempt begins with one coherent current intrinsic Object generation read.

Required Object projection:

```text
template_id = T
template_version = VS
properties
revision = R
```

`object_id` is already the path target. `canonical_name` is not required by SCHEMA_CHANGE semantics/lifecycle. Current ownership membership is not part of normal preparation.

The same STEP 1 may also observe requested distinct TARGET existence/current status so that obviously unusable targets can be rejected before semantic preparation **without adding a standalone preliminary TARGET round trip**.

Conceptual flow:

```text
STEP 1 — one authoritative current-generation statement
    Object generation T@VS + properties + revision R
    optionally requested TARGET header/existence/status in same bounded statement

    Object absent
        -> 404 resource_not_found

    VT == VS
        -> 204 semantic no-op

    VT != VS + TARGET absent
        -> 422 referenced_resource_not_found

    VT != VS + TARGET DRAFT/DEPRECATED
        -> 409 dependency_not_admissible

STEP 2 — worker/application semantic preparation
    obtain/build READY MigrationPlan(T, VS, VT)
    reject categorically unsupported component pair
    apply plan to current properties
    derive complete canonical target_properties
    derive actual changed-property lifecycle delta
    retain immutable/current-slot delta
    build PreparedSchemaChange(expected_revision=R)

STEP 3 — short real-migration UoW
    final protected TARGET PUBLISHED admission
    expected_revision freshness
    relational slot arbitration/maintenance
    atomic Object + revision + slots + lifecycle persistence
```

Normal preparation reads no:

```text
child Objects
object_components membership
Relationship state
lifecycle state
current object_component_slots for semantic reconstruction
```

### Conservative semantic failures

A semantic failure derived from coherent generation `R` may return immediately without a final revision refresh solely to discover whether a concurrent later mutation changed the answer.

Examples:

```text
multi-item LIST -> SCALAR
current property value incompatible with TARGET exact DTV
categorically unsupported component target relation
```

These paths commit no stale state. The response is serially explainable at the generation observed.

Canonical principle:

```text
expected-revision CAS is required for writes
not for no-op or semantic failure paths that persist nothing
```

## PreparedSchemaChange

Conceptually:

```text
PreparedSchemaChange
    object_id
    template_id
    source_version
    target_version
    expected_revision
    target_properties
    component_slot_delta | MigrationPlan reference
    lifecycle binding transition
    lifecycle changed-property delta
```

It is mechanically applicable once final mutable admissions succeed. Expensive schema comparison, property migration and TARGET value validation are not repeated simply because the final UoW begins.

## Final TARGET admission and short UoW

A real distinct TARGET is a lifecycle-sensitive new binding.

Final success requires exact TARGET:

```text
same template_id
exact requested target_version
current status == PUBLISHED
```

protected through the binding commit by a SHARE-equivalent semantic hold or another architecture-proven mechanism.

The final short UoW owns:

```text
A. protect/re-admit TARGET PUBLISHED through commit

B. require current Object revision == expected_revision R

C. apply current object_component_slots delta subject to DB referential arbitration

D. atomically commit:
       objects.template_version := VT
       objects.properties       := complete target_properties
       objects.revision         := R + 1
       complete current slot delta
       exactly one SCHEMA_CHANGE lifecycle event

E. leave object_components membership unchanged
```

No cache fill, MigrationPlan compilation, property transformation, TARGET value validation, child scan or lifecycle semantic reconstruction belongs inside the final protected path.

Exact SQL/lock/statement fusion remains architecture work.

## Intrinsic freshness and retry

`objects.revision` is the only intrinsic-row freshness token.

```text
candidate prepared from generation R

current revision == R
    -> exact intrinsic generation used for preparation is still current

current revision != R
    -> stale attempt
    -> no Object mutation
    -> no slot mutation
    -> no lifecycle
    -> bounded fresh retry from STEP 1
```

No canonical-JSON/SHA fingerprint or second binding-specific freshness mechanism is retained.

### Retry with unchanged SOURCE

```text
fresh SOURCE == previous SOURCE
    -> existing READY MigrationPlan(T, SOURCE, TARGET) reusable
    -> reapply to fresh properties
    -> recompute concrete migration outcome and lifecycle delta
```

### Retry with changed SOURCE

```text
fresh SOURCE != previous SOURCE
    -> old exact-pair plan not applicable
    -> resolve/build MigrationPlan(T, fresh_SOURCE, requested_TARGET)
    -> reprepare from fresh properties
```

### Retry reaches requested TARGET

```text
fresh source_version == requested target_version
    -> 204 semantic no-op
    -> no new mutation/revision/lifecycle
```

### Retry exhaustion

Retry is bounded. Exact count/backoff is architecture work.

If the internal policy cannot stabilize one intrinsic generation:

```text
-> 500 internal_error
```

There is no public route-specific `409 concurrent_modification` or `schema_change_blocked/concurrent_object_change` for stale revision contention.

Only stale `expected_revision` is an automatic intrinsic retry trigger. TARGET absence/inadmissibility, semantic migration failure, slot blocker and persistence defects retain their own normal classifications.

## Failure semantics and precedence

Public failure families:

```text
400 invalid_request
404 resource_not_found
422 referenced_resource_not_found
422 semantic_validation_failed
409 dependency_not_admissible
409 schema_change_blocked
500 internal_error
```

Normal precedence:

```text
1. malformed/static request carrier
    -> 400 invalid_request

2. current Object absent on authoritative generation read/retry
    -> 404 resource_not_found

3. target_version == current source_version
    -> 204 semantic no-op

4. distinct exact TARGET absent
    -> 422 referenced_resource_not_found
       resource_type = object_template_version
       id = template_id
       version = target_version

5. distinct exact TARGET exists but is DRAFT/DEPRECATED
    -> 409 dependency_not_admissible

6. immutable SOURCE -> TARGET migration relation categorically unsupported
    -> 422 semantic_validation_failed
    -> bounded violation identifies the unsupported schema-change rule/member

7. supported migration pair blocked by concrete current Object property state
    -> 409 schema_change_blocked
    -> blocker_type = property
    -> bounded semantic property identity/name detail

8. final TARGET re-admission
    TARGET became DRAFT/DEPRECATED
        -> 409 dependency_not_admissible

    TARGET absent
        -> 422 referenced_resource_not_found
        -> not a revision retry trigger

9. expected_revision stale
    -> internal bounded retry from STEP 1

10. final slot REMOVE/replacement blocked by current edge reference
    -> 409 schema_change_blocked
    -> blocker_type = component_slot_in_use
    -> bounded slot semantic identity detail
    -> no blocker count/child-id diagnostic query required

11. bounded revision retry exhausted
    -> 500 internal_error

12. unexpected persistence/cache/materialization/invariant failure
    -> 500 internal_error
```

A TARGET observation made during STEP 1 is only an early failure filter. Successful real migration still depends on final protected PUBLISHED admission.

No diagnostic-only DB read is introduced merely to enrich a failure.

## SCHEMA_CHANGE lifecycle

A successful real `SOURCE != TARGET` migration appends exactly one:

```text
kind = SCHEMA_CHANGE
```

Equal-target no-op, semantic failure, blocked migration and rolled-back attempts emit no SCHEMA_CHANGE event.

The event follows the general operation-owned lifecycle principle and does **not** persist full intrinsic Object before/after snapshots.

Canonical semantic payload:

```text
SCHEMA_CHANGE event
    object_id = O

    binding transition
        template_id = T
        source_version = VS
        target_version = VT

    changed runtime properties only
        PropertySemanticKey
            declaring_template_id
            property_name

        before
            canonical value | ABSENT

        after
            canonical value | ABSENT
```

The binding transition is always present for a real migration, even when no runtime property value changes:

```text
T@4 -> T@5
property_changes = []
```

is still a real historical SCHEMA_CHANGE.

Property deltas record actual semantic value transitions only. Unchanged property values are omitted.

Examples:

```text
ADD required via migration_default
    ABSENT -> canonical default

REMOVE present property
    canonical value -> ABSENT

SCALAR -> LIST
    x -> [x]

LIST -> SCALAR
    [x] -> x

DTV change that changes canonical representation
    old canonical -> new canonical
```

For semantic replacement, identical textual names do not merge identities. Example:

```text
(Device, hostname): "srv01" -> ABSENT
(Server, hostname): ABSENT -> "unknown"
```

rather than a false single-property rename/value change.

`ABSENT` is distinct from JSON null; null remains invalid runtime property state.

Lifecycle does not duplicate:

```text
canonical_name
revision
full properties before/after
unchanged properties
object_component_slots rows
components/ownership membership
Relationships
template display/status/default/description metadata
effective-schema snapshots
```

The slot delta is derived current-state materialization of the exact binding transition and is not copied into lifecycle. Ownership membership is unchanged by successful SCHEMA_CHANGE and ownership history remains owned by ATTACH/DETACH events.

Lifecycle binding + changed-property delta is derived during normal application-side MigrationPlan application; no second full-property-map pass or extra DB statement is required solely to build history.

Object binding/properties/revision, current slot materialization and the lifecycle event commit atomically.

## Concurrency outcomes

### Intrinsic writers

```text
SCHEMA_CHANGE x RENAME
SCHEMA_CHANGE x DATA_CHANGE
SCHEMA_CHANGE x SCHEMA_CHANGE
```

share the universal revision protocol. One committed intrinsic writer advances revision; a candidate based on the prior generation becomes stale and retries from fresh current state.

No lost intrinsic transition or stale full-properties overwrite is allowed.

### DELETE

```text
SCHEMA_CHANGE commits first
    -> DELETE may remove the resulting generation

DELETE commits first
    -> fresh SCHEMA_CHANGE retry observes Object absence
    -> 404
```

No mutation-after-delete or resurrection is permitted.

### ATTACH/DETACH

For preserved/equal/widened slots, membership changes do not invalidate an intrinsic property candidate merely because membership changed.

For REMOVE/replacement:

```text
ATTACH old slot commits first
    -> referenced slot cannot be removed/key-changed
    -> SCHEMA_CHANGE blocked

SCHEMA_CHANGE slot removal/replacement commits first
    -> later old-slot ATTACH cannot satisfy current semantic-slot FK

DETACH first
    -> may remove the final relational blocker
```

No parent Object revision bump or generic parent-lock rendezvous is required solely for slot continuity.

## Cost profile

### Equal-target no-op

```text
1 authoritative Object generation statement
0 MigrationPlan work
0 semantic-loader work
0 final UoW
0 UPDATE
0 slot DML
0 lifecycle
0 revision increment
```

### Warm real migration

With `MigrationPlan(T, VS, VT)` READY:

```text
1 preparation statement
    -> current Object generation
    -> optional distinct TARGET early existence/status observation in same statement

0 semantic-loader statements

application/worker CPU
    -> apply MigrationPlan
    -> construct complete target_properties
    -> derive actual changed-property lifecycle delta
    -> retain slot delta

1 bounded short final UoW + COMMIT
    -> final TARGET admission
    -> expected_revision freshness
    -> set-based slot maintenance / FK arbitration
    -> Object binding + full properties + revision + lifecycle persistence
```

Discovery deliberately does not freeze the physical statement count inside the final UoW. Architecture may safely fuse/decompose DML/protection while preserving the semantic contract. The UoW statement count must remain bounded independently of schema member count and child count.

### Cold preparation

Cold semantic work adds at most:

```text
0..1 exact closure bulk load
0..1 exact DTV bulk load
0..1 stable ancestry bulk load
```

No N+1 query growth is allowed.

### Application complexity

Let:

```text
P = effective property count involved in target-oriented candidate construction
V = size of current/target property values processed
D = component-slot delta size
```

Application semantic/candidate work is bounded by:

```text
O(P + V + D)
```

It does not scale with:

```text
current child count
ownership depth
Relationship count
lifecycle-event count
ObjectTemplate inheritance depth
```

LIST -> SCALAR needs no extra DB read because current list state is already in the full property map.

Slot maintenance must be set-based/bulk; M4 does not accept one PostgreSQL statement per slot as the intended architecture direction.

### Full property replacement trade-off

SCHEMA_CHANGE intentionally reads the full current property map and writes the full canonical TARGET map:

```text
PostgreSQL -> application
    full current properties

application/domain
    MigrationPlan application
    TARGET canonicalization/validation
    lifecycle property delta

application -> PostgreSQL
    complete target properties
```

This is appropriate because schema migration may affect the whole property contract. PostgreSQL remains current-state/CAS/referential/atomicity authority; application/domain code owns migration semantics.

Architecture must measure realistic:

```text
JSONB payload size
network transfer
Python decode/encode/CPU
PostgreSQL CPU
TOAST/WAL amplification
p50/p95/p99 latency
same-Object contention/retry amplification
```

before physical freeze.

## Architecture handoff

SCHEMA_CHANGE route semantics are full-sweep complete. Deferred to architecture-wide realization only:

```text
exact SQL / SQLAlchemy carriers
exact STEP-1 root/TARGET join carrier
final-UoW statement fusion/decomposition
exact TARGET/Object/slot lock modes
wait-for ordering and deadlock proof
exact bounded retry count/backoff
slot-delta set-based DML realization
PK/UNIQUE/FK actions/timing/constraint names
constraint/SQLSTATE -> ratified public failure translation
lifecycle JSON/typed persistence carrier
cache layout/eviction/local fill coordination
final physical indexes
EXPLAIN/BUFFERS evidence
JSONB/TOAST/WAL/storage/runtime measurements
```

Architecture must preserve:

```text
exact-target semantics; numeric order never decides migrability
equal-target one-read 204 no-op
one authoritative intrinsic Object generation read per attempt
no standalone preliminary TARGET query
bounded bulk immutable semantic fills; no N+1
application-side target-oriented property migration
conditional lossless LIST -> SCALAR only
categorical component target narrowing/unrelated rejection
no child/ownership semantic-preparation scan
expected_revision as only intrinsic freshness authority
bounded fresh retry; exhaustion -> 500
final protected TARGET PUBLISHED admission for real bindings
set-based current-slot maintenance
edge->slot FK final REMOVE/replacement arbitration
no diagnostic-only queries
atomic binding + properties + revision + current slots + lifecycle
operation-owned lifecycle binding transition + changed-property delta
no ownership membership rewrite on successful normal SCHEMA_CHANGE
```

## Full-sweep closure

The logical `POST /objects/{id}/schema` route is **full-sweep complete** on:

```text
public route/body/success contract
exact-target and equal-target no-op semantics
SOURCE/TARGET semantic identity and exact-pair planning
immutable MigrationPlan/cache boundary
property migration matrix including lossless LIST -> SCALAR
component migration matrix including categorical narrowing/unrelated rejection
single-generation Object preparation
TARGET early/final admission responsibilities
universal revision CAS + bounded retry/reprepare
slot FK arbitration and no child-preparation scan
public failure taxonomy/precedence
operation-owned lifecycle payload
concurrency outcomes
no-op/warm/cold cost character
architecture handoff
```

The former SCHEMA_CHANGE/fingerprint micro-WIP family was removed after lossless consolidation into this family owner and the reviewed cross-operation owners. Git history remains the historical reasoning record for its superseded alternatives and retained rationale.

# 8. GET one component slot — full sweep complete

## Public contract

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

Path:

```text
parent_object_id
    UUID

slot_name
    canonical component-slot name
    ^[a-z][a-z0-9_]{0,63}$
```

Query:

```text
cursor
    opaque string
    optional

limit
    positive integer 1..500
    optional
    default 100
```

No request body. Unknown or repeated query parameters are invalid request input. No additional child filter is part of the M4 contract.

The TO-BE surface does not retain the generic cross-slot route:

```http
GET /api/v1/core/objects/{parent_object_id}/components
```

`slot_name` is a path resource identity, not an optional filter. The route is the bounded/paginated view of one current direct-child collection already visible in the complete first-level `GET /objects/{id}` representation.

## Response and nested-resource semantics

Response:

```json
{
  "items": [
    {
      "id": "<child-object-id>",
      "canonical_name": "eth0"
    }
  ],
  "next_cursor": null
}
```

The child representation is exactly the same first-level reference used by Object GET. It does not expose:

```text
slot_declaring_template_id
target_template_id
child ObjectTemplate binding
child properties
child components
```

Canonical ordering:

```text
child_object_id ASC
```

Public current-resource outcomes:

```text
parent absent
    -> 404 resource_not_found
       resource_type = object

parent present + current slot absent
    -> 404 resource_not_found
       resource_type = object_component_slot

parent present + current slot present + zero children
    -> 200 {"items": [], "next_cursor": null}

parent present + current slot present + children
    -> 200 bounded page
```

A valid empty slot is therefore distinct from a nonexistent nested slot resource.

## Cursor semantics

The cursor identifies the semantic slot collection, not the complete parent Object generation and not a repeatable membership snapshot.

Canonical cursor identity:

```text
codec route
    object_component_slot_children

semantic query identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    excluded from semantic identity
```

`slot_declaring_template_id` is internal opaque cursor material only. It remains excluded from the public path/query/response contract.

It is required because one public path `(parent_object_id, slot_name)` can later resolve after SCHEMA_CHANGE to a different semantic slot declaration.

Consequences:

```text
same-name semantic replacement
    current slot_declaring_template_id differs
    -> 400 invalid_cursor

current slot removal
    -> 404 object_component_slot

SCHEMA_CHANGE preserving the same semantic slot identity
    -> cursor remains semantically compatible

target widening preserving semantic slot identity
    -> cursor remains compatible

ATTACH / DETACH
child RENAME
    -> do not structurally invalidate cursor
```

The cursor is not a cross-request snapshot. Membership/display changes between page requests are visible according to ordinary keyset semantics.

The position child need not remain current:

```text
cursor key = child C
C later detached or deleted
    -> continuation still uses child_object_id > C
    -> no lookup/admission of C itself
```

`limit` may change between pages.

Publicly the cursor remains only an opaque string. The current realization may reuse the existing v1 canonical-JSON/base64url envelope with a route-specific identity and no server-side cursor state; exact envelope internals are not a caller contract.

## Failure precedence

Static request validation:

```text
malformed parent_object_id
malformed slot_name
malformed/out-of-range limit
unknown/repeated query parameter
request body present
    -> 400 invalid_request
```

Static cursor validation happens before database access:

```text
malformed envelope
wrong route identity
cursor parent != requested parent
cursor slot_name != requested slot
missing/malformed internal semantic id
malformed position key
    -> 400 invalid_cursor
```

Then the authoritative current-state statement classifies in this order:

```text
parent absent
    -> 404 resource_not_found / object

parent present + slot absent
    -> 404 resource_not_found / object_component_slot

slot present + continuation semantic id differs
    -> 400 invalid_cursor

otherwise
    -> 200 current page
```

Unexpected persistence/invariant failures encountered on the required path are `500 internal_error`.

There is no normal route-level:

```text
409
422
```

No diagnostic-only second query is permitted solely to enrich failure details or search for impossible corruption.

## Current data path

The normal route reads only current data-plane state:

```text
objects parent
object_component_slots requested current slot
object_components current semantic-slot membership
objects child for current canonical_name
```

Required logical path:

```text
one root-preserving PostgreSQL statement

parent Object PK lookup
-> requested current slot by (object_id, slot_name)
-> compare current slot_declaring_template_id with cursor semantic id when present
-> bounded semantic-slot membership page
-> child Object id/current canonical_name
```

The membership branch uses the resolved current semantic identity:

```text
parent_object_id
slot_declaring_template_id
slot_name
child_object_id > cursor_child_id when present
ORDER BY child_object_id ASC
LIMIT limit + 1
```

For a continuation cursor, the bounded child-page branch should be gated by semantic-id equality so a stale same-name replacement cursor does not scan a page that will be rejected.

The application returns the first `limit` rows and builds `next_cursor` from the last returned child only when the `limit + 1` probe proves another row exists.

Cursor generation requires no additional database read.

## Authority boundary

ObjectTemplate exact effective schema remains the semantic/model-plane authority for component-slot definitions.

`object_component_slots` is the transactionally maintained current per-Object derivative produced by Object CREATE/SCHEMA_CHANGE.

The read consumes the already-admitted current invariant:

```text
MaterializedSlots(O)
    == EffectiveComponentSlots(O.template_id, O.template_version)
```

It does not re-certify that invariant on the hot path.

Normal route work therefore requires no:

```text
parent template binding read for schema interpretation
object_template_effective_components
ObjectTemplate inheritance traversal
component semantic cache
DataType semantics
ancestry cache
objects.revision
explicit row locks
lifecycle reads/writes
```

The current persistence model is also responsible for preventing dangling membership/child facts. The GET does not add integrity sweeps or diagnostic reads to re-prove those write-owned invariants.

## Coherence and concurrency

One PostgreSQL statement snapshot is the complete current-read coherence boundary.

```text
SCHEMA_CHANGE
    -> old semantic slot state OR new semantic slot state
    -> never an intermediate mixture

same-name semantic replacement
    snapshot before replacement
        -> old cursor may continue on old semantic collection
    snapshot after replacement
        -> current semantic id differs
        -> invalid_cursor

slot removal visible in snapshot
    -> 404 object_component_slot

ATTACH
    -> child absent before commit / present after commit

DETACH
    -> child present before commit / absent after commit

child RENAME
    -> old or new canonical_name according to the same statement snapshot

parent DELETE
    -> current parent result or 404 according to statement visibility
```

No revision check, retry or multi-statement coherent-read protocol is needed.

## Cost profile

Static request/cursor failure:

```text
0 PostgreSQL statements
```

Every path that consults current state, including:

```text
first page
continuation page
empty valid slot
missing slot
missing parent
stale semantic cursor
```

has target cost:

```text
1 PostgreSQL business statement maximum
0 cache lookups
0 model-plane reads
0 recursive traversal
0 explicit locks
0 lifecycle work
```

Logical work:

```text
O(1) parent lookup
+ O(1) requested current-slot lookup / semantic-id comparison
+ O(page size) membership and child-name rows
```

It must not scale with:

```text
total slots on the parent
total children in other slots
Object property count
ObjectTemplate inheritance depth
Relationship count
lifecycle-event count
```

## Architecture handoff

Deferred physical decisions:

```text
exact SQL / SQLAlchemy root-preserving carrier
LEFT/LATERAL vs equivalent realization
final PK/UNIQUE/index realization
edge index key order / INCLUDE choices
EXPLAIN (ANALYZE, BUFFERS) evidence
payload/runtime measurements
```

Architecture must prove the bounded path:

```text
objects PK(parent_object_id)
-> one current slot by (object_id, slot_name)
-> one keyset range for that semantic slot only
-> child Object PK/name access
```

and preserve:

```text
one statement
limit + 1 pagination
no semantic N+1
no other-slot scan
no model/cache dependency
no diagnostic follow-up query
```

No route-local physical index is frozen during discovery.

## Full-sweep closure

The logical `GET /objects/{parent_object_id}/components/{slot_name}` route is **full-sweep complete** on:

```text
public route/query/response contract
removal of generic cross-slot GET surface
slot absent vs empty semantics
semantic-slot cursor identity
keyset ordering and limit semantics
SCHEMA_CHANGE cursor compatibility/replacement behavior
failure precedence
one-statement current data path
no cache/model/revision/lock/lifecycle boundary
statement-snapshot concurrency semantics
bounded cost profile
architecture physical-design handoff
```

The former navigation cursor/data-path and broad Object-components brainstorming files were removed after lossless consolidation into this owner and the reviewed component-persistence owner. Git history remains the historical reasoning record.

## Ownership command-surface rationale

ATTACH and DETACH are semantic ownership mutation commands, not generic CRUD operations on the `components` read projection. The public mutation surface therefore uses explicit, symmetric command path segments:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/attach
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

A route such as:

```http
DELETE /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

would naturally read as deleting the slot collection or its current membership as a whole, while DETACH selects a caller-provided subset of child Object ids. The explicit `/detach` command avoids overloading DELETE request-body semantics and keeps ATTACH/DETACH visibly symmetric.

A future true "detach all children from this slot" capability, if required, is a separate semantic operation and is not introduced by M4.

# 9. ATTACH children to one slot — full sweep complete

## Public contract

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/attach
Content-Type: application/json
```

Path:

```text
parent_object_id
    UUID

slot_name
    canonical component-slot name
    ^[a-z][a-z0-9_]{0,63}$
```

Query parameters: none.

Request body:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>"
  ]
}
```

Static/request-shape rules:

```text
child_object_ids required
batch size 1..100
every child id is a UUID
duplicate child ids invalid
input order has no semantic meaning
unknown body fields invalid
unknown/repeated query parameters invalid
atomic batch
```

The parent may not appear in `child_object_ids`; that is a semantic self-reference failure after current parent/slot resolution, not a wire-shape failure.

ATTACH is a strict add-membership command:

```text
add only
no implicit DETACH
no move
no replacement
no partial success
no ON CONFLICT convergence
```

Any requested child that already owns any current edge causes whole-batch failure, including the exact same current parent/semantic-slot edge.

Success:

```http
204 No Content
```

The command returns no component projection. Current state remains owned by Object/component GET surfaces.

## Authority and data structures

ATTACH consumes:

```text
objects
    current parent existence/template lineage in S1
    current child existence only at the persistence/lifecycle boundary where required

object_component_slots
    current requested semantic slot identity
    current target_template_id admission contract

object_components
    current ownership graph
    final ownership edges

object_template_ancestry
    denormalized stable lineage closure used only to fill READY ancestry cache misses

ObjectLineageCache
    worker-local stable object_id -> template_id knowledge

StableObjectTemplateAncestryCache
    worker-local complete source-lineage ancestry/neighborship knowledge

object lifecycle persistence
    ATTACH_TO history
```

`object_component_slots` remains current mutable runtime truth derived atomically from the parent exact ObjectTemplate binding. Worker caches never replace PostgreSQL as authority for current parent/slot existence, current ownership or final child lifetime.

## S1 — current parent + semantic slot

One current PostgreSQL statement resolves the path target and requested nested slot directly from data-plane materialization.

Required logical result:

```text
parent existence
parent template_id
slot existence
slot_declaring_template_id
target_template_id
```

It does not need:

```text
parent template_version
parent canonical_name
parent revision
component-schema cache
ObjectTemplate exact-schema reconstruction
```

Public outcomes:

```text
parent absent
    -> 404 resource_not_found
       resource_type = object

parent present + current slot absent
    -> 404 resource_not_found
       resource_type = object_component_slot

parent + slot present
    -> continue with the current semantic slot identity/target
```

A parent pinned to a DEPRECATED exact ObjectTemplateVersion remains governed by its current materialized slot contract; ATTACH is not a new parent-binding admission.

`parent.template_id` can opportunistically populate the stable Object-lineage cache without an additional PostgreSQL statement.

## S2 — cache-first stable semantic preparation

S2 is not a mandatory PostgreSQL child read. It makes the stable semantic knowledge required for compatibility READY, then evaluates compatibility in memory.

### Stable Object-lineage cache

Conceptual cache:

```text
ObjectLineageCache[object_id] -> template_id
```

Meaning:

```text
if Object identity X exists,
its stable ObjectTemplate lineage is T
```

It does **not** mean:

```text
Object X exists now
```

`template_id` is stable for one Object identity; normal Object operations never reclassify an Object to another ObjectTemplate lineage. Object identity is lifetime-global and never reusable: once UUID `X` has identified one Object, `X` can never identify another Object incarnation, including after deletion. DELETE removes current existence, not the semantic identity history. No historical UUID registry/tombstone table is introduced solely to enforce this; kernel-generated UUIDv4 plus current PK authority is the accepted realization of the non-reuse invariant.

Consequently a positive:

```text
X -> T
```

may remain useful stable knowledge even after X is deleted. It must never be interpreted as current-existence proof.

Negative absence is different:

```text
X -> NOT_FOUND
```

is only a current observation and is not stable semantic knowledge. M4 therefore introduces no permanent semantic negative cache for Object absence. Architecture may later evaluate bounded temporary negative caching/TTL only as a performance policy, never as current-state authority.

For one ATTACH batch:

```text
1. lookup every required Object identity in ObjectLineageCache
2. retain every HIT
3. collect all and only MISS object ids
4. if MISS set is non-empty, issue one bounded bulk PostgreSQL read
5. cache every positive object_id -> template_id result
6. require complete lineage resolution before compatibility evaluation
```

The bulk fill is set-based over all missing ids, never one query per child. Parent lineage may already be supplied by S1; the cold fill therefore normally concerns only child identities not already READY.

If one or more requested child misses are absent from the bulk result:

```text
-> 422 referenced_resource_not_found
-> cache positive rows that were actually found
-> do not create stable negative entries for absent ids
-> stop this ATTACH attempt
```

No dedicated current-existence read is performed for child ids already present in `ObjectLineageCache`.

### Stable ancestry/neighborship cache

For all DISTINCT child `template_id` values needed by compatibility, ATTACH consumes:

```text
StableObjectTemplateAncestryCache[source_template_id]
```

A READY source contains its complete stable ancestor/neighborship set, including self. The persistent source is the already denormalized closure:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

including the reflexive row:

```text
(A, A, 0)
```

For every source not READY, ATTACH accumulates all missing source ids and fills them together with one bounded statement over `object_template_ancestry`. Each source is loaded completely and only then marked READY. There is no recursive ObjectTemplate traversal on the ATTACH data plane and no N+1 query per child/source/target pair.

Compatibility is then CPU/in-memory only:

```text
child.template_id compatible with slot.target_template_id
iff
slot.target_template_id is present in READY ancestry[child.template_id]
```

A READY negative is authoritative for stable lineage semantics; PostgreSQL cannot reveal a later new ancestor for the same existing source lineage.

### Conservative cache-staleness failure is acceptable

A positive Object-lineage cache entry may outlive current Object existence. Therefore this attempt is possible:

```text
cache: child C -> lineage T
C has since been deleted
T is incompatible with slot target
```

S2 may return:

```text
422 semantic_validation_failed / incompatible_template_lineage
```

instead of the currently fresher `referenced_resource_not_found` result.

This diagnostic imprecision is accepted because the mutation cannot proceed and stale cache knowledge must never enable an invalid commit. Current referential validity is still enforced at the persistence boundary. Cache refresh, TTL, eviction, explicit refresh APIs and local fill coordination belong to architecture; correctness must not depend on them.

## Mutation Unit of Work

After S1/S2 and self-reference validation succeed:

```text
BEGIN

Q1  acquire OWNERSHIP_GRAPH_WRITE_GATE

Q2  one fresh protected graph-admission statement
    -> has_owned_requested_child
    -> derive root(parent) through the single-owner chain
    -> root_is_requested

Q3  one strict bulk INSERT object_components
    -> N ownership edges

Q4  one bounded Object display-name read
    -> parent canonical_name
    -> canonical_name for all N inserted children

Q5  one bulk ATTACH_TO lifecycle INSERT
    -> exactly N lifecycle events

COMMIT
```

The graph edge-add gate is held through graph certification, edge persistence, lifecycle work and commit. ATTACH does not acquire an explicit parent row lock merely to stabilize the prepared semantic slot and does not use `objects.revision` as a parent freshness fence.

The semantic-slot FK is the final narrow ATTACH x SCHEMA_CHANGE stabilization/arbitration boundary.

## Q2 — protected ownership/cycle admission

Q2 owns only fresh mutable ownership-graph predicates:

```text
has_owned_requested_child
root_is_requested
```

Application precedence:

```text
has_owned_requested_child = true
    -> 409 ownership_conflict

otherwise root_is_requested = true
    -> 409 ownership_cycle

otherwise
    -> continue
```

Q2 does not certify child current existence and does not join `objects` solely for that purpose. A deleted requested child may simply appear ownerless; final lifetime authority remains Q3's child FK.

Under single-owner ownership, once every requested child is ownerless, an ownerless requested child can already be an ancestor of the parent only if it is exactly `root(parent)`. Therefore one recursive upward root traversal for the parent is sufficient for the entire batch.

M4 does not materialize or worker-cache mutable:

```text
object_id -> root_object_id
```

because ATTACH/DETACH would then require subtree-wide derived-state maintenance. Root lookup remains bounded by ownership depth rather than batch size.

## Q3 — strict bulk edge persistence and final arbitration

Q3 inserts every requested edge in one multi-row statement:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

There is no `ON CONFLICT`, per-child loop or partial-success branch.

Relational responsibilities and failure meanings are deliberately separated.

### `PK(child_object_id)`

The PK is the final structural at-most-one-owner authority.

However, after successful fresh Q2 under a graph gate respected by every edge-add writer, a normal competing ATTACH cannot create a new owner between Q2 and Q3. A PK violation after successful Q2 is therefore **not** the normal public ownership-conflict path; it indicates an invariant/concurrency-protocol failure or an edge-add writer bypassing the required arbitration.

Current discovery mapping:

```text
unexpected PK violation after successful Q2
    -> 500 internal_error
```

Architecture must prove that every writer capable of adding ownership edges participates in the required graph-add arbitration.

### `FK child_object_id -> objects.id`

This FK is the final current child lifetime/existence authority.

Normal race:

```text
S2 stable lineage knowledge is valid/compatible
child is deleted before Q3
Q3 child FK fails
```

Mapping:

```text
422 referenced_resource_not_found
resource_type = object
operand = child_object_ids
```

The exact missing child id may be omitted when it is not already known. No row lock or diagnostic reread is introduced solely to identify it.

### semantic-slot FK

Candidate dependency:

```text
(parent_object_id, slot_declaring_template_id, slot_name)
    -> object_component_slots(
           object_id,
           slot_declaring_template_id,
           slot_name
       )
```

This is the final current semantic-slot identity authority and the preferred narrow ATTACH x SCHEMA_CHANGE arbitration boundary.

If the prepared semantic slot is removed or semantically replaced before Q3 can establish its reference:

```text
-> semantic-slot FK failure
-> 409 ownership_slot_unavailable
```

Bounded public details use only already-known public context:

```text
resource_type = object_component_slot
parent_object_id
slot_name
```

No diagnostic reread is performed to distinguish REMOVE from same-name semantic replacement, and discovery does not automatically reprepare/retry after this `ownership_slot_unavailable` failure. Ambiguous failure alone never authorizes additional backend work.

If Q3 establishes the FK reference first, slot removal or referenced-key replacement cannot commit while the edge remains. `target_template_id` is deliberately non-key, so monotonic target widening may race without creating a false ATTACH failure.

### self-edge CHECK

```text
CHECK(parent_object_id <> child_object_id)
```

remains a structural backstop. Self-reference is already determined from request operands before the UoW. Therefore a CHECK failure after that validation is an unexpected invariant/protocol defect:

```text
-> 500 internal_error
```

The need for a separate direct `parent_object_id -> objects.id` FK remains an architecture-wide relational-schema question because parent lifetime is already implied through the referenced current semantic slot.

## Q4 — lifecycle display-name read after edge success

Parent/child canonical names are **required historical display metadata** for `ATTACH_TO`. Lifecycle must remain useful even after the referenced Object ids no longer exist.

They are not ownership identity or admission facts and therefore do not belong in S1/S2 merely to prepare ATTACH.

Only after Q3 has inserted the complete edge batch successfully, Q4 performs one bounded read for:

```text
parent_object_id
+
all requested child_object_ids
```

and returns:

```text
object_id -> canonical_name
```

Expected result cardinality is exactly:

```text
N children + 1 parent
```

because successful Q3 has established child lifetime references and the semantic-slot reference protects parent/slot lifetime through the surrounding transaction. Therefore an incomplete Q4 result is not a normal domain absence result:

```text
Q4 cannot read parent or one inserted child
    -> 500 internal_error
    -> rollback complete ATTACH
```

A concurrent RENAME may determine whether Q4 observes the old or new name. Exact name freshness at the instant of edge commit is not correctness-bearing and no extra locks/retries/rereads are added solely to improve display-name freshness.

## Q5 — edge-oriented lifecycle persistence

A successful batch with `N` new edges creates exactly `N` `ATTACH_TO` lifecycle events in one bulk statement.

There is no request-level aggregate ATTACH event.

Each event carries at least:

```text
child_object_id
child_canonical_name
parent_object_id
parent_canonical_name
slot_declaring_template_id
slot_name
```

Thus:

```text
N committed ownership edges
==
N committed ATTACH_TO events
```

Q3 edges and Q5 lifecycle rows belong to the same UoW. If Q5 fails:

```text
-> rollback
-> no ownership edge from the batch commits
-> 500 internal_error
```

The simplest/economical timestamp realization is acceptable: all rows produced by the one lifecycle bulk statement may share one `occurred_at` value. Per-row timestamp differentiation carries no ATTACH semantic requirement.

## Public failure semantics and execution precedence

Canonical rule:

```text
public failure
    = first decisive failure observed by the normal execution path

no additional backend work is performed
solely to discover a logically "better" or more current diagnostic
```

Because stable Object-lineage knowledge is cache-first, there is no longer one global child-absence-before-compatibility ordering independent of cache state.

Normal path:

```text
1. malformed/static request
    -> 400 invalid_request

2. S1 parent absent
    -> 404 resource_not_found / object

3. S1 current slot absent
    -> 404 resource_not_found / object_component_slot

4. parent_object_id appears in child_object_ids
    -> 422 semantic_validation_failed / self_reference

5. S2 stable semantic preparation
    ObjectLineageCache MISS fill proves one or more child ids absent
        -> 422 referenced_resource_not_found

    otherwise READY compatibility proves one or more child lineages incompatible
        -> 422 semantic_validation_failed
           rule = incompatible_template_lineage

6. Q2 protected graph admission
    has_owned_requested_child
        -> 409 ownership_conflict

    otherwise root_is_requested
        -> 409 ownership_cycle

7. Q3 bulk edge INSERT
    child lifetime FK failure
        -> 422 referenced_resource_not_found

    semantic-slot FK failure
        -> 409 ownership_slot_unavailable

    unexpected child PK violation after successful Q2
        -> 500 internal_error

    unexpected self-edge CHECK violation
        -> 500 internal_error

8. Q4 incomplete required lifecycle-name read
    -> 500 internal_error

9. Q5 lifecycle persistence failure
    -> 500 internal_error

10. other unexpected persistence/cache/materialization/invariant failure
    -> 500 internal_error
```

A stale positive ObjectLineageCache entry for a deleted child may cause an incompatible-lineage 422 before current absence is observed. That conservative failure is accepted because no invalid mutation can commit. If the cached lineage is compatible, Q3's child FK remains the final current-existence authority.

No failure-only diagnostic SELECT is allowed. Public details must use request/prepared context or the known failed constraint class and must not expose raw PostgreSQL text, SQL, table/column names or constraint names.

`ownership_slot_unavailable` reuses the existing finite public error code for an ATTACH slot that becomes unavailable after valid current selection. In M4, a slot already absent during S1 is instead `404 resource_not_found / object_component_slot`; this `409` is reserved for the later persistence/arbitration conflict above. No new global public error code is introduced.

## Cost profile

The logical discovery baseline deliberately does not assume SQL statement fusion that belongs to architecture.

Warm successful path, excluding `BEGIN`:

```text
S1  parent + current semantic slot read            1
S2  ObjectLineageCache + ancestry cache HIT        0
Q1  graph-write gate acquisition                   1
Q2  fresh ownership/root graph admission           1
Q3  strict bulk object_components INSERT           1
Q4  parent + N child canonical_name read            1
Q5  bulk N ATTACH_TO lifecycle INSERT              1
-----------------------------------------------------
                                                    6 PostgreSQL statements + COMMIT
```

Full-cold adds at most:

```text
+1 bounded bulk ObjectLineageCache fill
+1 bounded bulk full-ancestry/neighborship fill
```

therefore:

```text
warm      = 6 PostgreSQL statements + COMMIT
full-cold = 8 PostgreSQL statements + COMMIT
```

Batch cardinality `1..100` changes row volume, not normal statement count. Q2 recursive work scales with parent ownership depth. The ancestry fill reads already-denormalized closure rows and does not recursively reconstruct ObjectTemplate parentage.

Architecture may later reduce the physical round-trip count, especially around S1/Q2 or by safe write/lifecycle fusion, but `6/8` is the current logical discovery baseline and no optimization may weaken the responsibilities separated above.

## Architecture handoff

Deferred physical/cache decisions include:

```text
ObjectLineageCache concrete class/layout
positive-entry eviction / TTL / refresh policy
optional temporary negative caching policy
explicit cache refresh API or other freshness mechanism
local concurrent-fill coordination

S1 exact root/slot query carrier and possible safe fusion
Q2 exact recursive carrier and possible safe optimization/fusion
OWNERSHIP_GRAPH_WRITE_GATE physical realization
final transaction/isolation/wait ordering and deadlock proof
semantic-slot FK DDL/actions/timing
child lifetime FK DDL/actions/timing
direct parent FK necessity
constraint/SQLSTATE -> public failure classification
bulk edge SQL carrier
Q4 display-name carrier / possible lifecycle INSERT-SELECT fusion
Q5 lifecycle bulk carrier and timestamp realization
final indexes / EXPLAIN/BUFFERS evidence
realistic row-volume/latency measurements
```

Architecture must preserve:

```text
cache never proves current Object existence/current ownership/current slot state
positive object_id -> template_id knowledge remains stable semantic knowledge
Object UUID identity is lifetime-global and never reusable after allocation
no permanent semantic negative Object-existence cache
full source ancestry is READY before authoritative negative compatibility
no recursive/N+1 model traversal on ATTACH
no explicit parent lock or revision fence solely for slot continuity
fresh ownerlessness + root-only cycle admission under the graph edge-add gate
strict non-convergent atomic edge insert
child FK as final current child-existence authority
semantic-slot FK as final slot continuity/arbitration boundary
no diagnostic-only backend work after decisive failure
no automatic discovery-default retry after ownership_slot_unavailable
required historical parent/child names read only after successful edge insertion
one lifecycle row per edge, atomic with ownership state
```

## Full-sweep closure

The logical `POST /objects/{parent_object_id}/components/{slot_name}/attach` route is **full-sweep complete** on:

```text
explicit /attach command route
exact batch request/success contract and 1..100 bound
strict non-convergent add-only semantics
parent vs nested-slot 404 distinction
self-reference semantics
cache-first Object stable-lineage preparation
lifetime-global non-reusable Object UUID identity supporting durable positive lineage knowledge
positive-only stable Object-lineage knowledge / no semantic negative absence cache
full denormalized ancestry-neighborship READY cache
compatibility and accepted conservative cache-staleness diagnostic behavior
protected ownerlessness + root-only cycle admission
no mutable root materialization
strict bulk edge persistence
child lifetime FK / semantic-slot FK / PK / CHECK failure classification
ownership_slot_unavailable boundary with no diagnostic reread or default retry
post-edge required canonical-name read
edge-oriented required ATTACH_TO lifecycle metadata/atomicity
execution-path failure precedence
warm 6 / full-cold 8 logical cost baseline
architecture cache/SQL/FK/lock/index handoff
```

The former `object-attach-*` / `to-be-api-object-attach-*` route-local source files were removed after lossless consolidation. Their superseded mechanisms — including mandatory preliminary child reads, parent exact-binding lock/recheck, entry-time `ownership_slot_unavailable` for a slot already absent during initial current-state resolution, `concurrent_object_change`, old 7/9 or 6/7 costs and PK-as-normal-residual-race behavior — do not override this owner. Git history remains the historical reasoning record.

# 10. DETACH children from one slot — full sweep complete

## Public contract

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
Content-Type: application/json
```

Path:

```text
parent_object_id
    UUID

slot_name
    canonical component-slot name
    ^[a-z][a-z0-9_]{0,63}$
```

Query parameters: none.

Request body exactly:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>"
  ]
}
```

Static/request-shape rules:

```text
child_object_ids required
batch size 1..100
every child id is a UUID
duplicate child ids invalid
input order has no semantic meaning
unknown body fields invalid
unknown/repeated query parameters invalid
atomic batch
```

The parent may not appear in `child_object_ids`; that is a semantic self-reference failure after current parent resolution, not a wire-shape failure.

DETACH is a strict, non-convergent remove-membership command:

```text
remove exactly the requested current ownership edges
no implicit move
no replacement
no partial success
already-absent edge is not successful convergence
```

For every requested child id, success requires one current exact edge identified publicly by:

```text
parent_object_id
slot_name
child_object_id
```

The persisted edge is richer:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

and `slot_declaring_template_id` is taken from the edge actually removed. DETACH does not resolve or reinterpret the current ObjectTemplate schema merely to delete an already-admitted ownership fact.

If any requested exact edge cannot be removed, the whole batch fails atomically. This includes, without requiring separate diagnosis:

```text
child Object absent
child ownerless
child owned by another parent
child owned by the same parent under another slot
requested slot name with no matching current edge
edge already detached
```

Success:

```http
204 No Content
```

The command returns no component projection. Current state remains owned by Object/component GET surfaces.

## Authority and dependency boundary

DETACH consumes only current data-plane facts needed to perform the legal removal and persist its history:

```text
objects parent
    -> path-target existence
    -> required lifecycle canonical_name

objects child
    -> required lifecycle canonical_name only for edges actually removed

object_components
    -> authoritative current ownership fact
    -> persisted semantic slot identity

object lifecycle persistence
    -> DETACH_FROM history
```

`object_component_slots` is not a normal DETACH read source. Its existing relational dependency with `object_components` remains part of database arbitration, especially against concurrent slot REMOVE/semantic replacement, but DETACH performs no current-slot existence lookup merely to classify an error.

Normal DETACH therefore requires no:

```text
ObjectTemplate / ObjectTemplateVersion read
ObjectTemplate effective component-schema reconstruction
object_template_effective_components read
target_template_id
component-schema cache
ObjectLineageCache
StableObjectTemplateAncestryCache
compatibility validation
cycle validation
ownership graph traversal
OWNERSHIP_GRAPH_WRITE_GATE
objects.revision
MigrationPlan
```

The route removes an already-authoritative current fact; it does not re-admit the fact before deleting it.

## One-statement mutation Unit of Work

After static request validation, DETACH enters the mutation UoW directly.

Logical discovery baseline:

```text
BEGIN

Q1  one data-modifying PostgreSQL business statement

    parent
        -> prove current parent existence
        -> capture parent canonical_name

    deleted
        -> enabled only when self_reference = false
        -> bulk DELETE all requested exact object_components rows
        -> consume current child rows only to capture required canonical_name
        -> RETURNING authoritative removed-edge identity + display metadata

    certification
        -> deleted_count = number of actually removed requested edges
        -> complete iff deleted_count == requested_count

    lifecycle
        -> bulk INSERT exactly N DETACH_FROM rows from deleted material
        -> executed only when complete = true

    result/classification carrier
        -> parent_exists
        -> request-derived self_reference fact
        -> deleted_count

COMMIT
```

The exact SQL/CTE/SQLAlchemy spelling remains architecture work. The route-level requirement is one PostgreSQL business statement on the normal mutation path that can carry the `DELETE ... RETURNING` material directly into the conditional lifecycle `INSERT ... SELECT` or an equivalent one-statement realization.

### Parent and self-reference precedence

Self-reference is known from the request before PostgreSQL access, but parent path-target absence has precedence.

The same Q1 therefore observes the parent while gating edge deletion when self-reference is present:

```text
parent absent
    -> no DELETE
    -> no lifecycle
    -> 404 resource_not_found / object

parent present + self_reference
    -> no DELETE
    -> no lifecycle
    -> 422 semantic_validation_failed / self_reference
```

No standalone preliminary parent SELECT is introduced solely to obtain this precedence.

### Delete-first strict-batch certification

DETACH does not pre-read all requested edges and then delete the same facts in a second statement.

Instead:

```text
DELETE matching exact edges
RETURNING actual removed set
compare deleted_count with requested_count
```

If only a subset was removable, those row deletions remain inside the open transaction and the application rolls the transaction back:

```text
requested_count = 100
deleted_count   = 99
    -> lifecycle INSERT = 0
    -> 409 ownership_conflict
    -> ROLLBACK restores the 99 physical deletions
```

No partial DETACH becomes committed.

### No requested-child existence classification

DETACH does not independently classify current existence for requested child ids that have no matching edge.

On a valid success path, an existing `object_components` edge is already protected by the Object lifetime FK. The child row is read only because its canonical name is required for lifecycle history. Reading otherwise-unmatched requested child rows would exist solely to distinguish diagnostic subcases and is therefore excluded.

Consequently all non-current exact-edge states collapse naturally to:

```text
deleted_count < requested_count
    -> 409 ownership_conflict
```

There is no normal DETACH `422 referenced_resource_not_found` for a missing child operand.

### No current-slot existence classification

The semantic slot identity needed for history comes from the edge actually deleted:

```text
slot_declaring_template_id
slot_name
```

DETACH therefore does not read `object_component_slots` merely to decide whether a requested `slot_name` is currently defined. If the parent exists but the requested exact edge set cannot be removed, the normal observable result remains incomplete deletion and therefore `409 ownership_conflict`.

There is no DETACH-specific:

```text
404 object_component_slot
```

unless a future legal success path independently requires a current-slot read for another correctness reason and thereby changes the information obtained naturally by the operation.

## DETACH_FROM lifecycle

A successful batch with `N` removed edges creates exactly `N` `DETACH_FROM` lifecycle events. There is no request-level aggregate DETACH event.

For every removed edge the same Q1 captures the required historical display metadata and semantic ownership identity:

```text
child_object_id
child_canonical_name
parent_object_id
parent_canonical_name
slot_declaring_template_id
slot_name
```

Event mapping:

```text
kind                       = DETACH_FROM
object_id                  = child_object_id
canonical_name             = child_canonical_name
destination_object_id      = parent_object_id
destination_canonical_name = parent_canonical_name
slot_declaring_template_id = slot_declaring_template_id
slot_name                  = slot_name
```

Ownership lifecycle events do not need intrinsic `before_state` / `after_state` Object snapshots. Historical structural identity is the exact removed edge identity.

Canonical names are required historical display fields, but their precise freshness relative to a concurrent RENAME is not ownership identity. DETACH does not add locks, retries or rereads solely to choose a different display-name observation.

Lifecycle rows are inserted only after the same statement has certified the complete requested delete set. Therefore an inadmissible batch performs no lifecycle insert work. If lifecycle persistence fails, the statement/transaction fails and all edge removals are rolled back.

All rows produced by the one bulk lifecycle branch may share one transaction/statement timestamp; per-row timestamp differentiation carries no DETACH semantic requirement.

## Public failure semantics and execution precedence

Canonical project rule applies directly:

```text
public failure
    = information naturally obtained while executing the legal action
      as efficiently as possible

no additional backend work is performed
solely to discover a more specific or fresher diagnostic
```

Normal precedence:

```text
1. malformed/static request
    malformed parent_object_id
    malformed slot_name
    malformed/missing body
    missing/empty child_object_ids
    batch size outside 1..100
    malformed child UUID
    duplicate child ids
    unknown body fields
    unknown/repeated query parameters
        -> 400 invalid_request

2. Q1 parent absent
        -> 404 resource_not_found
           resource_type = object

3. Q1 parent present + parent_object_id appears in child_object_ids
        -> 422 semantic_validation_failed
           rule = self_reference

4. Q1 parent present + no self-reference + deleted_count < requested_count
        -> 409 ownership_conflict

5. complete delete but persistence/lifecycle/invariant failure
        -> 500 internal_error
```

The following public distinctions are intentionally absent because the one-statement legal path does not need to establish them:

```text
404 object_component_slot
422 referenced_resource_not_found for child
ownerless vs wrong parent vs wrong slot
missing child vs absent edge
ownership_slot_unavailable
ownership_cycle
concurrent_object_change
```

No failure-only diagnostic SELECT, schema reread or retry is allowed merely because the returned error family is broad. In particular, an ambiguous failure is never sufficient reason for additional backend operations.

## Concurrency outcomes

DETACH owns no additional synchronization protocol beyond current relational arbitration. Exact lock/wait ordering is architecture work and composes with the existing core LockPlanner.

Explicit route-local exclusions:

```text
NO parent Object FOR NO KEY UPDATE solely for DETACH
NO Object revision fence/bump
NO OWNERSHIP_GRAPH_WRITE_GATE
NO model/cache preparation lock
NO current-slot lock/read solely for continuity
NO automatic diagnostic/stale retry
```

### DETACH vs DETACH

The same `object_components` row is the rendezvous for concurrent removal.

```text
first DETACH commits the edge removal
    -> first may return 204
    -> competing strict DETACH can no longer remove its complete requested set
    -> competing request returns 409 ownership_conflict

first DETACH rolls back
    -> competing request may subsequently remove the edge and succeed
```

For overlapping multi-row batches the route freezes no lock acquisition order. Architecture must integrate the statement with the core LockPlanner and prove deadlock/wait ordering globally rather than introducing a route-local pre-lock SELECT solely for DETACH.

### DETACH vs ATTACH

DETACH does not join ATTACH's graph edge-add gate merely because both mutate ownership.

```text
ATTACH observes the old edge before DETACH commit
    -> ATTACH may conservatively fail ownership_conflict
    -> DETACH may then commit

DETACH commits first
    -> the child becomes ownerless
    -> a later/fresh ATTACH may independently pass its normal admission

ATTACH creates a new edge while DETACH's requested old edge is not current/visible
    -> DETACH cannot remove its complete requested set
    -> 409 ownership_conflict
```

DETACH does not wait/retry solely because a concurrent mutation might later make the command admissible.

### DETACH vs SCHEMA_CHANGE

DETACH does not interpret the parent's exact binding. Current slot REMOVE/semantic replacement arbitration is supplied by the existing edge -> semantic-slot relational dependency:

```text
DETACH commits the final old edge removal first
    -> slot reference disappears
    -> REMOVE/replacement may proceed

slot transition reaches FK arbitration while old edge still references the key
    -> relational FK enforcement prevents invalid slot removal/key change
```

Preserved/equal slots and non-key target widening require no DETACH-specific stabilization.

### DETACH vs Object DELETE

Current ownership FKs protect parent/child lifetime while the edge exists. Removing the edge may legitimately remove a lifetime blocker:

```text
DETACH commits first
    -> DELETE may subsequently succeed if no other blocker remains

DELETE reaches lifetime arbitration while edge still exists
    -> DELETE may fail delete_blocked
```

DETACH captures required display names in the same statement that removes the edge, so it does not need to keep parent/child alive merely for a later lifecycle-name read.

## Cost profile

There is no warm/cold distinction.

Static failure:

```text
0 PostgreSQL statements
```

Every path that reaches current state uses one PostgreSQL business statement:

```text
parent absent
self-reference after parent resolution
incomplete exact-edge set
successful complete DETACH
```

Successful logical baseline, excluding `BEGIN`:

```text
Q1  parent resolution
    + exact-edge bulk DELETE ... RETURNING
    + strict deleted-count certification
    + conditional bulk DETACH_FROM lifecycle INSERT
-------------------------------------------------------
    1 PostgreSQL business statement + COMMIT
```

For batch cardinality `N <= 100`:

```text
round trips         O(1)
edge delete work    O(N)
lifecycle rows      O(N) on success, 0 on inadmissible batch
cache/model work    0
graph traversal     0
```

No statement count scales with batch size.

## Architecture handoff

Deferred physical/concurrency work:

```text
exact one-statement SQL / SQLAlchemy data-modifying carrier
exact DELETE ... RETURNING -> certification -> lifecycle INSERT realization
final transaction/isolation/wait behavior
integration with the existing core LockPlanner
multi-row lock ordering and global deadlock proof
final PK/UNIQUE/FK actions/timing and SQLSTATE classification
lifecycle physical carrier / timestamp realization
final indexes / EXPLAIN/BUFFERS evidence
realistic N<=100 row-volume/latency measurements
```

Architecture must preserve:

```text
strict non-convergent atomic batch semantics
1..100 public batch bound
no current-slot/schema/cache/ancestry/graph/revision preparation
persisted edge as semantic slot-identity authority
parent absence before self-reference in public precedence
no requested-child existence scan solely for diagnostics
all incomplete exact-edge states -> ownership_conflict
required parent/child historical display names captured during the delete statement
exactly one DETACH_FROM row per committed removed edge
no lifecycle work for an inadmissible batch
one PostgreSQL business-statement logical success baseline
no diagnostic-only backend work or retry
route-local lock-order policy deferred to architecture/core LockPlanner
```

## Full-sweep closure

The logical `POST /objects/{parent_object_id}/components/{slot_name}/detach` route is **full-sweep complete** on:

```text
exact /detach public route and 1..100 wire contract
strict non-convergent atomic removal semantics
parent-before-self-reference precedence
persisted edge semantic identity / no current-slot lookup
no requested-child existence diagnostic classification
409 ownership_conflict collapse for every incomplete exact-edge set
one-statement delete-first strict-batch certification
required display-name capture in the delete statement
conditional fused edge-oriented DETACH_FROM lifecycle
one-statement success cost / no warm-cold path
no schema/cache/ancestry/graph/revision dependency
DETACH x DETACH / ATTACH / SCHEMA_CHANGE / DELETE concurrency outcomes
LockPlanner/deadlock realization architecture handoff
no diagnostic-only backend work
```

The former `object-detach-*` / `to-be-api-object-detach-*` route-local source files were removed after lossless consolidation. Their superseded mechanisms — including zero-DB self-reference precedence, requested-child existence classification, `422 referenced_resource_not_found` for missing child operands, current parent-stabilization variants and the split two/three-statement lifecycle paths — do not override this owner. Git history remains the historical reasoning record.

# 11. GET current owner — full sweep complete

## Public contract

```http
GET /api/v1/core/objects/{child_object_id}/owner
```

Path:

```text
child_object_id
    UUID
```

Query parameters: none.

Request body: none.

Static/request-shape failures are:

```text
malformed child_object_id
any query parameter
request body present
    -> 400 invalid_request
```

The route is a current ownership projection of the selected child Object. `/owner` is not an independently existing nested resource whose absence should become `404`.

If the child exists and is currently owned, success is:

```http
200 OK
```

```json
{
  "parent": {
    "id": "<parent-object-id>",
    "canonical_name": "server-1"
  },
  "slot_name": "parts"
}
```

Conceptual wire model:

```text
OwnerProjection
    parent: ObjectReference
        id
        canonical_name
    slot_name
```

`ObjectReference {id, canonical_name}` is the same first-level Object reference shape already used by Object/component read projections. `parent.canonical_name` is current display state observed by this GET; it is not ownership identity or historical metadata.

If the child exists and is currently ownerless, success remains:

```http
200 OK
```

```json
null
```

Public outcomes are therefore:

```text
child Object absent
    -> 404 resource_not_found
       resource_type = object

child Object present + no current ownership edge
    -> 200 null

child Object present + current ownership edge
    -> 200 OwnerProjection
```

The owned projection intentionally does not expose:

```text
slot_declaring_template_id
parent ObjectTemplate binding
parent properties
parent components
parent revision
```

`slot_declaring_template_id` remains part of persisted semantic edge identity and relational correctness, but it is not needed by callers to identify the current public owner relation and is not part of this wire DTO.

## Current data path and authority boundary

GET owner is a pure current mutable data-plane read.

Required logical sources:

```text
objects child
    -> path-target existence

object_components
    -> current ownership edge
    -> parent_object_id
    -> slot_name

objects parent
    -> current parent canonical_name when an edge exists
```

Preferred logical path:

```text
one root-preserving PostgreSQL statement

objects child PK(child_object_id)
LEFT JOIN object_components by child_object_id
LEFT JOIN objects parent by edge.parent_object_id
```

The one statement naturally distinguishes all public states:

```text
no child root
    -> 404

child root + no edge
    -> 200 null

child root + edge + parent
    -> 200 {
         parent: {id, canonical_name},
         slot_name
       }
```

The query does not need to project or interpret `slot_declaring_template_id`; persistence retains that field for edge semantic identity and cross-operation invariants, not because every consumer must expose it.

Normal GET owner does not read:

```text
object_component_slots
ObjectTemplate / ObjectTemplateVersion
object_template_effective_components
objects.template_id
objects.template_version
objects.properties
objects.revision
DataType state
ancestry state
worker-local semantic caches
lifecycle state
```

No semantic recertification is performed. The current `object_components` fact has already been admitted by the mutations that own ownership validity.

The current relational model is responsible for ensuring that an edge cannot remain committed with a nonexistent parent/current semantic slot. If the required one-statement path incidentally encounters an impossible edge-without-parent state, that is an invariant/persistence failure:

```text
500 internal_error
```

This does not authorize a second diagnostic query to search for its cause.

## Failure semantics and precedence

Bounded public failure set:

```text
400 invalid_request
404 resource_not_found
500 internal_error
```

Normal precedence:

```text
1. malformed/static request carrier
       -> 400 invalid_request

2. authoritative current-state statement
       child absent
           -> 404 resource_not_found / object

       child present + edge absent
           -> 200 null

       child present + valid edge/parent
           -> 200 OwnerProjection

       impossible required persisted invariant failure encountered
           -> 500 internal_error
```

There is no normal GET-owner:

```text
409
422
404 for ownerless state
404 object_component_slot
```

No failure-only follow-up read is permitted solely to enrich an impossible or ambiguous result.

## Coherence and concurrency

One PostgreSQL statement snapshot is the complete current-read coherence boundary.

No explicit lock, LockPlanner participation, revision read, retry, graph gate or multi-statement coherent-read protocol is required.

### GET owner vs ATTACH

```text
snapshot before ATTACH commit
    -> child present + no edge
    -> 200 null

snapshot after ATTACH commit
    -> child present + edge
    -> 200 OwnerProjection
```

### GET owner vs DETACH

```text
snapshot before DETACH commit
    -> 200 OwnerProjection

snapshot after DETACH commit
    -> 200 null
```

### GET owner vs parent RENAME

`parent.canonical_name` is current display state. The statement may observe the old or new committed parent name according to ordinary PostgreSQL visibility:

```text
old canonical_name
or
new canonical_name
```

No synchronization is added merely to select a different display-name observation.

### GET owner vs child DELETE

```text
snapshot sees child current
    -> 200 null / OwnerProjection

snapshot sees committed child absence
    -> 404 resource_not_found
```

### GET owner vs parent DELETE

While a current ownership edge exists, the reviewed ownership lifetime composition prevents the parent/current semantic slot from disappearing as committed state. Therefore a normal statement cannot legitimately observe a committed edge with an absent parent.

If the edge has already been removed, GET owner simply observes ownerless child state and has no reason to read or diagnose a former parent.

### GET owner vs SCHEMA_CHANGE

For a preserved semantic slot or target widening, the edge remains current and the public projection remains the same owner/slot relation.

For slot REMOVE or same-name semantic replacement, the edge -> current semantic-slot dependency prevents the transition from committing while the old edge still references the old semantic slot. Therefore SCHEMA_CHANGE cannot silently reinterpret a current edge merely because this public DTO exposes only `slot_name`.

`slot_declaring_template_id` remains the internal semantic identity that enforces that invariant even though it is not returned by this GET.

## Cost profile

There is no warm/cold distinction.

Static invalid request:

```text
0 PostgreSQL statements
```

Every current-state outcome has target cost:

```text
1 PostgreSQL business statement maximum
```

Logical access is bounded and child-rooted:

```text
objects child PK lookup
+ object_components lookup by child_object_id
+ objects parent PK lookup only when owned
```

Target profile:

```text
statement count       O(1)
rows/facts consumed   O(1)
payload               O(1)
cache                  0
model-plane reads      0
schema reads           0
graph traversal        0
revision               0
explicit locks         0
lifecycle              0
```

The route does not scale with:

```text
Object property count
parent component-slot count
parent child count
ownership depth
ObjectTemplate inheritance depth
Relationship count
lifecycle-event count
```

## Relational implication

GET owner introduces no route-specific persistence structure:

```text
new table / materialization    none
new cache                      none
new persisted field            none
new semantic invariant         none
```

The route consumes the already-reviewed candidates:

```text
objects
    id
    canonical_name

object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

The current `child_object_id` at-most-one-owner direction remains the natural child-rooted access input. `parent.canonical_name` stays authoritative on `objects` and is deliberately not denormalized onto the edge merely to serve this GET.

## Architecture handoff

Deferred physical decisions:

```text
exact SQL / SQLAlchemy root-preserving carrier
final PK / UNIQUE / FK realization
final child-rooted physical access path
final indexes
EXPLAIN (ANALYZE, BUFFERS) / equivalent evidence
```

Architecture must preserve:

```text
one PostgreSQL statement maximum
child absent -> 404
child present + edge absent -> 200 null
child present + edge -> 200 parent ObjectReference + slot_name
current parent canonical_name from the same statement snapshot
no slot_declaring_template_id in the public DTO
no object_component_slots/model/cache/revision dependency
no explicit locks/retry/graph gate/lifecycle work
no diagnostic follow-up query
constant bounded logical work
```

No route-local physical index is frozen during discovery.

## Full-sweep closure

The logical `GET /objects/{child_object_id}/owner` route is **full-sweep complete** on:

```text
exact GET route and strict no-query/no-body request surface
child 404 vs current ownerless 200 null semantics
parent ObjectReference {id, canonical_name} + slot_name owned DTO
removal of public slot_declaring_template_id
one-statement child-rooted current data path
no object_component_slots/model/cache/revision dependency
bounded 400/404/500 failure precedence
statement-snapshot ATTACH/DETACH/RENAME/DELETE/SCHEMA_CHANGE semantics
constant one-statement cost profile
no new relational/cache/materialization requirement
architecture physical-plan/index handoff
no diagnostic-only follow-up reads
```

The former `object-components-reads-discovery.md` source was removed after lossless consolidation. Its still-relevant cross-operation persistence findings are represented by `object-components-persistence.md`; its GET-owner route-local findings are absorbed here. Git history remains the historical reasoning record.

# 12. DELETE Object — full sweep complete

## Public contract

```http
DELETE /api/v1/core/objects/{object_id}
```

Path:

```text
object_id UUID
```

No request body is accepted. No query parameter is introduced for:

```text
force
cascade
recursive/subtree deletion
implicit detach
implicit Relationship deletion
```

Successful deletion returns:

```http
204 No Content
```

The deleted Object representation is not returned.

A repeated DELETE after a committed deletion is not convergent success:

```text
Object already absent
    -> 404 resource_not_found
```

A current external lifetime dependency produces:

```text
409 delete_blocked
```

The public `delete_blocked` detail is intentionally bounded to the selected Object identity. The contract does not require blocker identities, blocker types, exact blocker counts or PostgreSQL constraint names, and no PostgreSQL statement may be required solely to enrich this diagnostic.

DELETE removes only the selected Object. It never implicitly DETACHes ownership, deletes factual Relationships, removes a subtree or rewrites blockers merely to make deletion admissible.

## Lifetime admission boundary

Object DELETE owns only the admission needed to terminate the selected Object lifetime:

```text
Object.DELETE(O) may commit
iff
no current external fact requires O to remain alive
```

Current lifetime blockers include:

```text
current ownership edge where O is child
current ownership edge where O is parent
current factual Relationship runtime-closure reference involving O
any future current external fact whose semantics require O lifetime
```

Not blockers:

```text
O's owned object_component_slots
O's outgoing exact ObjectTemplateVersion binding
lifecycle/history rows
worker caches
immutable model semantics
```

`object_component_slots` is owned derived state. Empty/current slot rows disappear with the Object and do not keep it alive. When a current ownership edge references one of those semantic slot rows, that external edge is the blocker; Object DELETE must not implicitly remove it.

The Object's exact `(template_id, template_version)` reference points outward to model-plane state. DELETE releases that reference; the target OTV does not have to be re-admitted, lifecycle-checked or stabilized merely for the Object to remove its outgoing binding.

Lifecycle history has no live current-resource lifetime semantics and survives deletion without blocking it.

DELETE is not a domain consistency sweep. It must not proactively:

```text
re-certify ObjectTemplate/DataType semantics
validate persisted Object properties against schema
re-derive Relationship runtime closure
validate ownership consistency
re-certify object_component_slots against model-plane schema
count or enumerate all blocker families
scan for dangling references
perform diagnostic-only reads searching for corruption
```

The route trusts invariants established by the mutations that own them and consumes only the current database lifetime result required by DELETE.

## Ratified execution/data path

DELETE has no semantic-preparation phase and no cache path. The current route candidate is one data-modifying PostgreSQL business statement inside one semantic transaction:

```text
BEGIN

Q1
    DELETE Object root by id

    -> database current-lifetime arbitration
    -> owned derived Object state disappears as allowed
    -> retain the exact deleted intrinsic Object row server-side
    -> construct DELETED before_state server-side
    -> INSERT exactly one DELETED lifecycle row
    -> return a tiny success carrier

COMMIT
```

The route performs:

```text
0 preliminary Object SELECTs
0 blocker-precheck/count statements
0 ObjectTemplate/DataType/model-plane reads
0 semantic recertification
0 cache operations
0 diagnostic-only PostgreSQL reads
```

The root delete itself is the current lifetime-admission point. Conceptually:

```text
zero deleted/success rows
    -> 404 resource_not_found

current database lifetime reference rejects the root delete
    -> 409 delete_blocked

one success carrier
    -> 204 No Content
```

The server-side fusion is intentional because the potentially large `properties` JSONB need not travel:

```text
PostgreSQL -> application -> PostgreSQL
```

solely to construct the mandatory historical event. The exact row actually deleted feeds the lifecycle snapshot inside PostgreSQL.

Candidate successful cost, excluding transaction control:

```text
1 PostgreSQL business statement
```

There is no warm/cold distinction.

## DELETED lifecycle and atomicity

For one successfully deleted Object row, the intrinsic historical snapshot remains bounded to:

```text
kind           = DELETED
object_id      = deleted.id
canonical_name = deleted.canonical_name
before_state   = {
    id,
    canonical_name,
    template_id,
    template_version,
    properties
}
after_state    = null
```

Technical `revision` is not added to the semantic DELETED payload merely because it exists on the persistence row.

Current ownership, component slots, owner projection and factual Relationships are not embedded in the intrinsic DELETED snapshot. Their structural history remains represented by their own lifecycle families.

Required atomicity:

```text
root Object DELETE fails
    -> no DELETED event

DELETED lifecycle INSERT fails
    -> whole statement/transaction fails
    -> Object deletion does not commit

statement succeeds + COMMIT
    -> Object absence + exactly one DELETED event become durable together
```

No committed Object deletion may exist without the required DELETED event.

## Failure mapping

The bounded public outcomes are:

```text
missing Object
    -> 404 resource_not_found

current external lifetime blocker
    -> 409 delete_blocked

unexpected persistence/integrity defect
    -> normal bounded persistence/internal-failure classification
```

A foreign-key violation can map to `delete_blocked` only when it is attributable to the root Object lifetime deletion. The fused lifecycle branch must not cause an unrelated FK failure to be mislabeled merely because it shares SQLSTATE `23503`.

Architecture must therefore preserve one of:

```text
lifecycle INSERT cannot generate an unrelated 23503

or

the persistence boundary can distinguish the failure source
without issuing a diagnostic-only query
```

## Referential-integrity dependency and revalidation trigger

The one-statement DELETE contract deliberately depends on complete database-enforced Object lifetime integrity.

Every current external fact whose semantics require an Object to remain alive must participate in atomic database-level arbitration with the root Object DELETE, preferably through immediate `RESTRICT` / `NO ACTION` foreign-key semantics or another globally proven database mechanism with equivalent guarantees.

Conceptually:

```text
current external lifetime reference commits/is effective first
    -> root Object DELETE cannot commit

root Object DELETE commits first
    -> a new conflicting current lifetime reference cannot commit
```

This is part of the route contract, not merely a physical optimization. It is what permits the DELETE path to avoid blocker scans, blocker census and application-side admission logic.

Therefore any material persistence change to the Object lifetime-reference graph or its database arbitration **reopens Object.DELETE** and requires the route to be re-proven before the new design can be considered compatible.

Revalidation triggers include:

```text
adding a new current Object reference that must keep the Object alive
removing or changing an existing lifetime FK
changing CASCADE / RESTRICT / NO ACTION semantics
moving a current lifetime dependency outside DB-enforced arbitration
introducing deferred or materially different enforcement timing
changing object_component_slots / object_components lifetime composition
changing factual Relationship endpoint lifetime enforcement
```

Dependency direction:

```text
Object.DELETE one-statement contract
    depends on
complete DB-enforced current Object lifetime integrity
```

## Ratified concurrency outcomes

Object DELETE requires serially explainable lifetime outcomes. Discovery does not freeze exact PostgreSQL lock modes, advisory gates, ordering, wait strategy or retry counts.

General rule:

```text
Object.DELETE may commit
iff
no current external fact still requires Object lifetime
at the database lifetime-arbitration point
```

### DELETE vs DELETE

```text
first DELETE commits
    -> 204
    -> exactly one DELETED lifecycle event

second concurrent/later DELETE observes absence
    -> 404 resource_not_found
    -> no second DELETED event
```

Two DELETE commands must never both report successful deletion of the same current Object generation.

### DELETE vs intrinsic Object mutation

This includes canonical-name mutation, properties mutation and SCHEMA_CHANGE.

```text
intrinsic mutation commits first
    -> DELETE removes that resulting current Object generation
    -> DELETED.before_state is the row actually deleted

DELETE commits first
    -> intrinsic mutation cannot later commit against or recreate the deleted Object
```

Required guarantees:

```text
no mutation-after-delete
no resurrection
serially explainable current state
```

The intrinsic writer's expected-revision CAS is one side of this guarantee; the root DELETE/lifetime arbitration remains the deletion authority.

For SCHEMA_CHANGE, Object exact binding and materialized slot set remain one atomic Object generation: either the schema transition commits first and DELETE removes the new generation, or DELETE commits first and SCHEMA_CHANGE cannot publish replacement current state afterward.

### DELETE vs ATTACH

ATTACH creates a new current Object lifetime reference whether the selected Object participates as parent or child.

```text
ATTACH lifetime reference commits first
    -> DELETE cannot commit
    -> 409 delete_blocked

DELETE commits first
    -> ATTACH cannot commit a new current reference to the absent Object
```

### DELETE vs DETACH

DETACH removes a current ownership lifetime reference.

```text
DETACH removal commits first
    -> that blocker disappears
    -> DELETE may succeed if no other blocker remains

DELETE reaches arbitration while the edge still blocks
    -> DELETE may return 409 delete_blocked
```

DELETE does not promise to wait for concurrent DETACH, auto-retry until it commits or perform DETACH implicitly. A later caller retry may succeed.

A successful DELETE while the blocking ownership edge remains committed is forbidden.

### DELETE vs factual Relationship.CREATE

```text
Relationship.CREATE endpoint reference commits first
    -> DELETE cannot commit
    -> 409 delete_blocked

DELETE commits first
    -> Relationship.CREATE cannot commit a runtime endpoint reference to the absent Object
```

No committed factual Relationship runtime closure may reference an absent Object.

### DELETE vs factual Relationship.DELETE

```text
Relationship.DELETE commits first
    -> owned runtime closure disappears
    -> endpoint blocker disappears
    -> DELETE may succeed if no other blocker remains

DELETE reaches arbitration while the Relationship reference still exists
    -> DELETE may return 409 delete_blocked
```

As with DETACH, DELETE has no obligation to wait or retry internally merely because a concurrent operation is removing the blocker.

### DELETE vs Relationship mutation retaining endpoints

A Relationship mutation that preserves the factual Relationship endpoint references does not release Object lifetime:

```text
current factual Relationship still references O
    -> O remains delete_blocked
```

Object DELETE does not inspect or re-certify Relationship schema semantics to determine this; the persisted current endpoint reference is sufficient.

### DELETE vs ObjectTemplate whole-lineage deletion

The lifetime dependency is outgoing from Object:

```text
Object O
    -> exact ObjectTemplateVersion T@V
```

Therefore:

```text
Object O still exists
    -> ObjectTemplate.DELETE_LINEAGE(T) remains blocked by O

Object.DELETE commits first
    -> O -> T@V reference disappears
    -> whole-lineage deletion may subsequently become admissible
```

ObjectTemplate lifecycle/default mutations such as DEPRECATE, SET_DEFAULT and CLEAR_DEFAULT are not Object.DELETE admission predicates.

## Concurrency/architecture handoff

Architecture must realize the ratified outcomes while preserving:

```text
no dangling current references
no mutation-after-delete
no resurrection
no double DELETE success
exactly one DELETED event for the deleted Object generation
no false-success DELETE
atomic Object disappearance + DELETED lifecycle
serially explainable outcomes
```

Discovery deliberately does not ratify:

```text
FOR UPDATE / FOR KEY SHARE / exact row-lock modes
specific advisory gates
final lock ordering
retry count
wait strategy
deadlock realization
```

The referential-integrity revalidation trigger above applies to this concurrency proof too: material changes to the DB-enforced Object lifetime graph invalidate the assumptions behind this route and require DELETE to be reopened.

## Full-sweep closure

The logical `DELETE /objects/{id}` route is full-sweep complete on:

```text
public 204 / 404 / 409 semantics
no force/cascade/implicit blocker mutation
bounded delete_blocked diagnostics
external-current-fact lifetime boundary
owned-derived/history non-blocker boundary
no proactive consistency sweep
one-statement direct lifetime transition
server-side DELETED before_state construction
atomic Object disappearance + lifecycle
one-statement success cost / no cache
DB-enforced referential-integrity dependency
explicit persistence-change revalidation trigger
failure mapping including 23503 qualification
serially explainable concurrency outcomes
```

Deferred only to later architecture-wide physical/concurrency realization:

```text
final PK/UNIQUE/FK/CASCADE/RESTRICT realization
exact root DELETE + lifecycle SQL carrier
exact SQLSTATE/constraint-source classification
final lock modes / advisory gates / wait-for ordering
retry/wait/deadlock strategy
final indexes and PostgreSQL plan evidence
verification of the complete Object lifetime-reference graph
```

Those physical choices must preserve the route contract above. A change to the lifetime-reference graph is not transparent to this closure and explicitly reopens DELETE.

# Nested surfaces owned by later discovery passes

## Object lifecycle history

```http
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

This route remains for the Lifecycle discovery pass.

Important already-discovered consequence of enriching `ObjectDto` with current components:

```text
current ObjectDto
    != lifecycle event payload
```

Lifecycle payloads are operation-specific historical facts. They record the complete exact semantic transition owned by the mutation, not automatically a complete Object aggregate snapshot.

Current consequences already ratified during Object route discovery:

```text
RENAME
    -> exact canonical_name old -> new only

DATA_CHANGE
    -> exact delta of actually changed semantic properties
    -> event binding context T@V
    -> semantic key (declaring_template_id, property_name)
    -> before/after value | ABSENT

DELETE
    -> broad intrinsic before snapshot remains justified because the Object ceases to exist

CREATE
    -> broad created-state after snapshot may remain justified by whole-resource creation

SCHEMA_CHANGE
    -> exact binding transition T@SOURCE -> T@TARGET
    -> exact delta of actually changed semantic properties
    -> semantic key (declaring_template_id, property_name)
    -> before/after value | ABSENT
    -> no full intrinsic before/after snapshot
```

Technical `revision` is not automatically lifecycle semantic payload.

Ownership history remains represented by explicit `ATTACH_TO` / `DETACH_FROM` events rather than being embedded into unrelated intrinsic events.

The Lifecycle discovery pass owns the final discriminated detail DTO/persistence carrier for these operation-specific payloads.

## Object-relative factual Relationship collection/detail

```text
GET /objects/{object_id}/relationships
Object-relative Relationship detail capability
```

These remain owned by the later factual Relationship top-down pass because public DTO/perspective semantics are still open. They are not folded into this Object operation owner merely because the URL is Object-rooted.

# Cross-operation observations

## Intrinsic Object generation boundary

[`object-revision.md`](object-revision.md) owns one universal intrinsic-generation protocol:

```text
CREATE
    -> revision = 1

prepared/derived intrinsic mutation
    -> observe revision R
    -> commit only against expected_revision = R

persisted intrinsic mutation
    -> revision R + 1 atomically

stale expected_revision
    -> no stale state/lifecycle commit
    -> bounded retry
```

The deliberate result is that RENAME, DATA_CHANGE and SCHEMA_CHANGE use one generation token even when this creates conservative retries between otherwise-independent fields. Revision proves only `objects`-row freshness; it does not cover ownership/Relationship facts outside the intrinsic row.

Pure reads do not need to expose or CAS on revision merely because the column exists.

## Component-schema cache boundary

`object_component_slots` does **not** delete the immutable exact component-schema cache as a system capability.

It removes the normal component-schema cache dependency from these current Object runtime candidates:

```text
GET Object
GET component slot
GET owner
ATTACH slot resolution
DETACH
```

Immutable exact schema/validation caches remain useful where semantic validation or migration genuinely needs model-plane knowledge, including CREATE properties validation, properties mutation and SCHEMA_CHANGE preparation.

CREATE may also opportunistically warm the exact component-semantic cache facet when its cold semantic load can do so with bounded marginal work and no additional PostgreSQL round trip solely for warming. That warming is a reusable performance side effect, not a CREATE correctness prerequisite.

## Current read boundary

Pure current runtime projections should prefer current PostgreSQL facts when the required semantic identity has already been admitted/materialized:

```text
GET Object
GET Object schema binding
GET component slot
GET owner
```

Model-plane exact schema remains semantic authority, but normal current reads should not recertify admitted/materialized state solely to reconstruct identifiers/facts already persisted relationally.

## Upstream ObjectTemplate revalidation triggers

The reviewed Object family closure assumes the current upstream ObjectTemplate contracts for:

```text
certified immutable exact effective-property semantics
    -> available for PUBLISHED/DEPRECATED exact ObjectTemplateVersions

certified immutable exact effective-component semantics
    -> available for exact ObjectTemplateVersions
    -> able to drive current Object slot materialization

stable complete ObjectTemplate lineage ancestry
    -> immutable for an existing lineage
    -> completely materializable
    -> includes reflexive ancestry
```

A material change to those contracts during the later ObjectTemplate sweep does not automatically reopen the entire Object family. It reopens the dependent Object routes and requires their affected data-path, cost, cache, concurrency and persistence proofs to be revalidated.

Current targeted dependency map:

```text
effective-property contract changes
    -> revalidate Object CREATE
    -> revalidate DATA_CHANGE
    -> revalidate SCHEMA_CHANGE

effective-component contract/materialization changes
    -> revalidate Object CREATE
    -> revalidate SCHEMA_CHANGE
    -> revalidate GET Object / GET component slot
       if the current-slot materialization invariant changes
    -> revalidate ATTACH
       if current slot source/target semantics change

stable-ancestry contract changes
    -> revalidate ATTACH
    -> revalidate SCHEMA_CHANGE component-target relation planning
```

Until such an upstream contract changes, these are dependency/revalidation triggers rather than open Object design questions; the Object route-level sweep remains reviewed/full-sweep complete.

## Physical-design boundary

This WIP intentionally does not ratify:

```text
final PK/UNIQUE/FK set
final indexes
final query plans
EXPLAIN evidence
storage/write measurements
final global lock/wait/deadlock realization
```

Those belong to the later M4 architecture-wide persistence/concurrency phase.

# Route-owner comparison closure

The route-owner consolidation has been checked against the current owner/checkpoint files for:

```text
CREATE
LIST
GET
canonical-name mutation
properties mutation / DATA_CHANGE
Object schema GET
Object SCHEMA_CHANGE
component-slot navigation / GET
ATTACH
DETACH
GET owner
DELETE
```

The current Object DATA_CHANGE full sweep has been losslessly absorbed here, including public contract, requested-effects-only validation, application-side complete JSON mutation, semantic no-op cost rule, universal revision CAS/retry, exact changed-property lifecycle delta, failure mapping, warm/cold cost direction and architecture handoff. The older first-phase DATA_CHANGE discovery is superseded where it proposed full-candidate semantic recertification; its still-relevant cache/authority and hot-path no-recertification findings are preserved above.

The current `GET /objects/{id}/schema` full sweep has also been losslessly absorbed here, including exact public DTO, stable `template_name` convenience, one-statement Object-PK -> ObjectTemplate-PK read path, no exact-OTV admission/recertification, no cache/lock/revision dependency, bounded failure mapping, concurrency semantics, cost target and physical-plan handoff.

The current `POST /objects/{id}/schema` full sweep is now losslessly absorbed here, including exact-target/equal-target semantics, immutable exact-pair MigrationPlan, complete property/component migration matrices, one-generation preparation, universal revision retry, final TARGET admission, slot-FK arbitration, failure precedence, operation-owned lifecycle delta, concurrency outcomes, bounded cold classes and architecture handoff.

The current `GET /objects/{parent}/components/{slot}` full sweep is now losslessly absorbed here, including exact route/query/response contract, semantic-slot cursor identity, slot-absent vs empty semantics, keyset continuation, one-statement current data path, failure precedence, snapshot concurrency semantics, bounded cost profile and physical-design handoff.

The current `POST /objects/{parent}/components/{slot}/attach` full sweep is now losslessly absorbed here, including the strict batch command contract, nested-slot 404 semantics, stable Object-lineage cache, denormalized ancestry-neighborship cache, protected graph admission, FK arbitration/failure mapping, required historical display-name read, edge-oriented lifecycle, execution-path failure precedence, warm/full-cold cost profile and architecture handoff.

The current `POST /objects/{parent}/components/{slot}/detach` full sweep is now losslessly absorbed here, including the symmetric 1..100 wire contract, strict non-convergent removal semantics, parent-before-self-reference precedence, persisted-edge semantic authority, deliberate collapse of missing-child/edge/slot diagnostic subcases into `ownership_conflict`, one-statement delete-first certification, conditional fused DETACH_FROM lifecycle, required historical display-name capture, concurrency outcomes, one-statement cost baseline and LockPlanner/physical architecture handoff.

The current `GET /objects/{child}/owner` full sweep is now losslessly absorbed here, including strict no-query/no-body request semantics, child-absence vs ownerless-null distinction, parent ObjectReference + slot-name DTO, removal of public `slot_declaring_template_id`, one-statement child-rooted current-state projection, bounded failure/concurrency semantics, constant cost profile and physical-plan handoff.

Non-superseded contract, failure, concurrency and cost details omitted by earlier consolidation drafts have been recovered here. Historical rationale and already-superseded mechanisms are intentionally not duplicated.

Former route-local Object WIPs removed after lossless consolidation remain historical Git evidence only and do not compete with this owner. Cross-operation owners and source families needed by later family sweeps remain in the working set until their own revalidation/cleanup passes.