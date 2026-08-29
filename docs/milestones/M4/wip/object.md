# M4 WIP — Object TO-BE consolidated discovery

**Status:** ROUTE-OWNER CONSOLIDATED / CROSS-CUTTING OWNERS PENDING / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for the M4 Object operation family during discovery.

It replaces route-local fragmentation with one readable checkpoint for the current Object public surface, route-local semantics, logical data paths, cache boundaries, candidate costs, concurrency guarantees and architecture handoffs.

Everything under `wip/` remains non-normative. Local closure wording is only a discovery checkpoint and does not authorize implementation.

The route-owner comparison pass has been completed against the current route-local Object owners. Older route-local and micro-step files remain temporarily in the tree only until the relevant lossless consolidations are complete and references can be cleaned safely.

Detailed cross-operation component persistence is intentionally kept outside this file and is owned by:

```text
object-components-persistence.md
```

Detailed Object schema-migration mechanics are intentionally kept outside this file and are owned by:

```text
object-schema-change.md
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
| `GET /objects/{id}/schema` | route-local closed | one Object -> ObjectTemplate PK-to-PK statement |
| `POST /objects/{id}/schema` | public surface retained; execution active revalidation | immutable migration plan + universal expected-revision intrinsic freshness + slot-delta maintenance |
| `GET /objects/{parent}/components/{slot}` | route-local checkpoint | one current data-plane statement |
| `POST /objects/{parent}/components/{slot}/attach` | public semantics retained; execution revalidated | current slot materialization + ancestry cache + graph admission + FK arbitration |
| `POST /objects/{parent}/components/{slot}/detach` | public semantics retained; execution revalidated | set-based current-edge delete + lifecycle |
| `GET /objects/{child}/owner` | working current-fact candidate | one child-rooted statement over `objects` + `object_components` |
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

Application/result work is bounded by page size:

```text
O(page size)
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

No M4 denormalization/materialization is required for this route.

## Architecture handoff

The logical route is full-sweep complete.

Deferred only to the later architecture-wide physical-design phase:

```text
final physical index set
final PostgreSQL plan/EXPLAIN evidence
```

No route-local physical index is ratified during discovery. Architecture must evaluate Object LIST together with the complete Object workload and preserve the one-statement bounded-summary path above.

# 3. GET Object

## Public contract

```http
GET /api/v1/core/objects/{object_id}
```

Query parameters/body: none.

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

## Architecture handoff

Still physical/open:

```text
exact SQL/SQLAlchemy carrier
aggregated facts vs tagged row stream
final indexes
EXPLAIN/BUFFERS evidence
real payload/runtime measurements
```

These physical choices must preserve:

```text
one authoritative statement
root transferred once logically
O(S + C) fact volume
application-side components assembly
```

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

# 6. GET current Object schema binding

## Public contract

```http
GET /api/v1/core/objects/{object_id}/schema
```

Success:

```json
{
  "template_id": "<template-id>",
  "template_name": "Server",
  "version": 4
}
```

The route answers only:

```text
which exact ObjectTemplate binding governs this Object now?
```

It does not expose effective schema, properties, components, namespace, description, lifecycle status, default state, revision or other ObjectTemplate metadata.

`template_id` is authoritative lineage identity. `template_name` is stable human-readable convenience and does not participate in identity.

## Data path

Preferred bounded shape:

```text
1 PostgreSQL statement
objects PK(object_id)
    -> template_id/template_version
object_templates PK(template_id)
    -> stable template name

0 cache
0 locks
0 semantic schema reconstruction
```

A cache for stable template name is not justified because PostgreSQL must already be consulted for current Object existence/binding and the PK-to-PK join adds no round trip.

Concurrent SCHEMA_CHANGE is observed before or after commit, never as an intermediate binding.

Missing Object:

```text
0 rows -> 404
```

Physical-plan verification is deferred to architecture.

# 7. POST Object schema change

## Public contract

```http
POST /api/v1/core/objects/{object_id}/schema
Content-Type: application/json
```

Request:

```json
{
  "target_version": 5
}
```

The mutation changes only the exact version inside the Object current stable ObjectTemplate lineage; it does not select another `template_id`.

Success:

```http
204 No Content
```

The resulting current state is read through:

```text
GET /objects/{id}
GET /objects/{id}/schema
```

## Current high-level candidate

The public surface is retained while the execution model remains actively revalidated after `object_component_slots` and the universal Object revision decision.

Current component-side direction:

```text
immutable MigrationPlan SOURCE -> TARGET

prepare/migrate intrinsic Object state outside the short UoW where safe

short SCHEMA_CHANGE UoW
    -> use expected_revision for intrinsic Object generation freshness
    -> protect final TARGET mutable admission
    -> maintain object_component_slots delta atomically
    -> use edge->slot FK as final REMOVE/replacement blocker authority
    -> update Object exact binding + migrated properties + revision
    -> append SCHEMA_CHANGE lifecycle
    -> COMMIT
```

Candidate slot delta:

```text
ADD
    -> INSERT current slot row

REMOVE
    -> DELETE current slot row

continuous target widening
    -> UPDATE target_template_id

semantic replacement
    -> key-changing slot_declaring_template_id UPDATE
       + target_template_id as required

position-only change
    -> no slot DML
```

Existing `object_components` edges remain unchanged on a successful normal migration.

The universal persisted `revision` supersedes the earlier intrinsic Object fingerprint as the preferred stale-success guard for `objects`-row state. Structural slot/ownership facts remain outside revision scope and still rely on their own relational admission/arbitration.

Detailed migration semantics, cache inputs, property rules, expected-revision retry behavior and final UoW belong to the dedicated `object-schema-change.md` consolidation and must be revalidated there before SCHEMA_CHANGE full-sweep closure.

# 8. GET one component slot

## Public contract

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

`slot_name` is a path resource identity, not an optional search filter.

The TO-BE surface does not retain a generic cross-slot route:

```text
GET /objects/{parent}/components
    -> not retained
```

The complete Object GET already exposes all direct slots/children; this specialized route exists for selective bounded pagination of one potentially large slot.

No additional component filter is part of the current candidate; query parameters are only `cursor` and `limit`.

Response uses the same child representation as Object GET:

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

Public outcomes:

```text
malformed slot carrier
    -> normal 400 invalid_request boundary

parent absent
    -> 404 resource_not_found / object

parent present + current slot absent
    -> 404 resource_not_found / object_component_slot

parent present + slot present + empty
    -> 200 empty page

parent present + slot present + children
    -> 200 bounded page
```

## Cursor

Opaque cursor identity:

```text
route identity
    object_component_slot_children

semantic query identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    excluded from identity
```

`slot_declaring_template_id` remains internal opaque cursor material. Same-name semantic slot replacement invalidates an old cursor rather than silently continuing against a different collection.

Static malformed/incompatible cursor carriers return:

```text
400 invalid_cursor
```

Current-state precedence:

```text
parent absent
    -> 404 object

slot absent
    -> 404 object_component_slot

slot present but cursor declaring lineage differs
    -> 400 invalid_cursor

otherwise
    -> normal continuation
```

ATTACH/DETACH, child RENAME and target widening do not invalidate a cursor merely because membership/display state changes; cross-request repeatable membership is not promised.

The route reuses the existing versioned canonical-JSON + URL-safe-Base64 cursor envelope with a distinct route identity; no global cursor-envelope version bump is introduced by this route-local change.

## Data path

Current candidate:

```text
1 PostgreSQL statement
objects parent
+ requested object_component_slots row
+ bounded object_components page
+ child objects for canonical_name

0 component-schema cache
0 ObjectTemplate effective-schema reads
0 recursive traversal
0 explicit locks
```

All mutable response facts and current semantic cursor compatibility come from one statement snapshot.

Cursor generation itself adds:

```text
0 DB statements
0 model-plane reads
0 cache lookups
```

Final indexes/plan evidence remain architecture work.

# 9. ATTACH children to one slot

## Public contract

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/attach
```

Request:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>"
  ]
}
```

Rules:

```text
non-empty batch
duplicate ids invalid
input order has no semantic meaning
parent id cannot appear in child ids
atomic batch
add membership only
no implicit DETACH/replacement
```

Any requested child already owning any edge causes whole-batch failure, including the exact same current parent/slot edge. There is no convergent `ON CONFLICT` success and no partial success.

Success:

```http
204 No Content
```

## Current preparation candidate

One current parent+slot statement returns:

```text
parent existence
parent canonical_name
slot existence
slot_declaring_template_id
target_template_id
```

from current data-plane state.

```text
parent absent
    -> 404 resource_not_found

parent present + slot absent
    -> 409 ownership_slot_unavailable
```

No parent exact-template read or component-schema cache lookup is required merely to resolve the current slot contract. A parent pinned to a DEPRECATED exact OTV remains governed by its current materialized slot contract; ATTACH is not a new parent-binding admission.

One bulk child Object read returns:

```text
id
template_id
canonical_name
```

and stable-lineage compatibility is checked against slot `target_template_id` through the stable ObjectTemplate ancestry cache.

A READY ancestry source contains its complete sparse ancestor set, including self. Missing source lineages are loaded in bounded bulk; there is no per-child N+1 ancestry query.

## Current mutation candidate

```text
BEGIN

Q1 acquire OWNERSHIP_GRAPH_WRITE_GATE

Q2 protected graph admission
    -> any requested child currently owned?
    -> root(parent) among requested ids?

Q3 bulk INSERT object_components
    -> semantic slot FK must still reference current slot

Q4 bulk ATTACH_TO lifecycle INSERT

COMMIT
```

Graph admission precedence:

```text
owned requested child
    -> ownership_conflict

otherwise root(parent) requested
    -> ownership_cycle

otherwise
    -> proceed
```

Current relational responsibilities:

```text
PK object_components(child_object_id)
    -> single owner

FK child -> objects
    -> child lifetime

FK semantic parent slot -> object_component_slots
    -> current parent/slot existence + semantic identity

self-edge CHECK
    -> relational backstop

graph gate + protected root check
    -> DAG acyclicity
```

The slot FK is the preferred narrow ATTACH x SCHEMA_CHANGE arbitration point for slot REMOVE/semantic replacement. Target widening is non-key and semantically monotonic.

Parent/child canonical names used in ATTACH lifecycle history remain best-effort display metadata; no extra DB reread is added solely for display-name freshness.

Candidate public/failure precedence:

```text
1. invalid wire/static request
    -> 400 invalid_request

2. parent path target absent
    -> 404 resource_not_found

3. parent appears in child_object_ids
    -> 422 semantic_validation_failed / self_reference

4. current slot unavailable
    -> 409 ownership_slot_unavailable

5. one or more child Objects absent
    -> 422 referenced_resource_not_found

6. one or more present children incompatible with slot target lineage
    -> 422 semantic_validation_failed

7. protected graph admission finds an owned requested child
    -> 409 ownership_conflict

8. otherwise root(parent) is requested
    -> 409 ownership_cycle

9. residual edge-insert constraint race
    -> translate from the known violated constraint class
```

A final mapping is still required for the race where the current semantic slot disappears/replaces after unlocked preparation but before edge INSERT. No diagnostic-only query may be added solely to enrich this classification.

Candidate successful costs:

```text
warm      = 6 PostgreSQL statements + COMMIT
full-cold = 7 PostgreSQL statements + COMMIT
```

The only normal semantic-cache cold fill left is stable child-lineage ancestry.

Still open:

```text
final slot-disappearance/replacement failure mapping
final direct parent-FK necessity
architecture-wide FK/locking/deadlock proof
```

# 10. DETACH children from one slot

## Public contract

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

Request:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>"
  ]
}
```

Static validation:

```text
malformed/missing body
missing/empty child_object_ids
malformed UUID carriers
duplicate child_object_ids
invalid transport carriers
    -> 400 invalid_request

parent_object_id included in child_object_ids
    -> 422 semantic_validation_failed / self_reference
```

DETACH is strict, non-convergent and atomic:

```text
all requested exact edges current
    -> remove all

missing child
    -> whole batch fails

existing child but exact edge absent/different
    -> whole batch fails

already absent exact edge
    -> not a successful no-op
```

Success:

```http
204 No Content
```

## Current data path

DETACH needs only current persisted facts. It does not need normal:

```text
ObjectTemplate effective-schema reconstruction
component-schema cache
ancestry cache
target_template_id
compatibility validation
cycle validation
graph-write gate
```

Current candidate:

```text
BEGIN

Q1 one fresh set-based statement
    -> prove parent existence
    -> classify requested child existence
    -> bulk DELETE exact requested ownership rows
    -> RETURNING semantic edge + lifecycle display material

Q2 one bulk DETACH_FROM lifecycle INSERT

COMMIT
```

Failure precedence:

```text
1. static invalid request
    -> 400 invalid_request

2. self-reference
    -> 422 semantic_validation_failed / self_reference

3. parent absent
    -> 404 resource_not_found

4. requested child absent
    -> 422 referenced_resource_not_found

5. requested exact edge set incomplete
    -> 409 ownership_conflict

6. persistence/lifecycle failure
    -> normal bounded persistence classification
```

No diagnostics-only DB reads are introduced.

Canonical names used in lifecycle history remain best-effort historical display metadata.

Candidate cost:

```text
success                  = 2 PostgreSQL statements + COMMIT
failure classified by Q1 = 1 statement + rollback
static failure            = 0 DB
```

A parent Object stabilization statement is no longer preferred solely as generic SCHEMA_CHANGE rendezvous. Edge removal cannot create a graph/schema violation; slot REMOVE/replacement arbitration occurs at the referenced slot FK boundary.

# 11. GET current owner

## Current public surface baseline

```http
GET /api/v1/core/objects/{child_object_id}/owner
```

The detailed top-down public DTO has not yet received the same route-local closure treatment as the operations above. The current working direction retains the existing ownership projection semantics while simplifying the data path.

Current projection concept:

```text
OwnerProjection
    parent_object_id
    slot_declaring_template_id
    slot_name
```

The public-surface shape remains a point to recheck during the Object consistency sweep before architecture freeze; this section must not silently create a new public contract from current implementation alone.

## Data-path candidate

With semantic slot identity persisted directly on `object_components`:

```text
child objects PK lookup
LEFT JOIN object_components by child_object_id PK
```

naturally distinguishes:

```text
child Object absent
    -> 404

child exists and detached
    -> owner = null

child exists and attached
    -> current owner projection
```

Candidate runtime path:

```text
1 PostgreSQL statement
0 ObjectTemplate traversal
0 effective-schema read
0 cache
0 semantic recertification
```

This is a pure current-fact read.

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
    -> payload boundary remains to be revalidated by its own full sweep
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
ATTACH slot resolution
DETACH
```

Immutable exact schema/validation caches remain useful where semantic validation or migration genuinely needs model-plane knowledge, including CREATE properties validation, properties mutation and SCHEMA_CHANGE preparation.

CREATE may also opportunistically warm the exact component-semantic cache facet when its cold semantic load can do so with bounded marginal work and no additional PostgreSQL round trip solely for warming. That warming is a reusable performance side effect, not a CREATE correctness prerequisite.

## Current read boundary

Pure current runtime projections should prefer current PostgreSQL facts when the required semantic identity has already been admitted/materialized:

```text
GET Object
GET component slot
GET owner
```

Model-plane exact schema remains semantic authority, but normal current reads should not recertify admitted/materialized state solely to reconstruct identifiers/facts already persisted relationally.

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
Object schema GET/public POST surface
component-slot navigation + cursor/data-path checkpoints
ATTACH
DETACH
GET owner working projection
DELETE
```

The current Object DATA_CHANGE full sweep has been losslessly absorbed here, including public contract, requested-effects-only validation, application-side complete JSON mutation, semantic no-op cost rule, universal revision CAS/retry, exact changed-property lifecycle delta, failure mapping, warm/cold cost direction and architecture handoff. The older first-phase DATA_CHANGE discovery is superseded where it proposed full-candidate semantic recertification; its still-relevant cache/authority and hot-path no-recertification findings are preserved above.

Non-superseded contract, failure, concurrency and cost details omitted by earlier consolidation drafts have been recovered here. Historical rationale and already-superseded mechanisms are intentionally not duplicated.

For routes marked `full-sweep complete`, dedicated route-only legacy WIPs may be removed after this explicit lossless absorption/reference check; Git history remains the historical record. Cross-operation owners and source families needed by routes that are not yet full-swept remain in the working set until their own revalidation/cleanup passes.