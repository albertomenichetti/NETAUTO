# M4 WIP — Object TO-BE consolidated discovery

**Status:** ROUTE-OWNER CONSOLIDATED / CROSS-CUTTING OWNERS PENDING / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for the M4 Object operation family during discovery.

It replaces route-local fragmentation with one readable checkpoint for the current Object public surface, route-local semantics, logical data paths, cache boundaries, candidate costs, concurrency guarantees and architecture handoffs.

Everything under `wip/` remains non-normative. Local closure wording is only a discovery checkpoint and does not authorize implementation.

The route-owner comparison pass has been completed against the current route-local Object owners. Older route-local and micro-step files remain temporarily in the tree only until the two cross-cutting consolidations are complete and references can be cleaned safely.

Detailed cross-operation component persistence is intentionally kept outside this file and will be consolidated into:

```text
object-components-persistence.md
```

Detailed Object schema-migration mechanics are intentionally kept outside this file and will be consolidated into:

```text
object-schema-change.md
```

Git history is the historical record for superseded discovery checkpoints after cleanup.

# Shared Object runtime candidate

Current intrinsic Object state remains:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties JSONB
```

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
| `POST /objects` | public contract retained; slot persistence revalidated | current binding admission + READY semantic cache + Object/slot materialization |
| `GET /objects` | **full-sweep complete** | one statement on `objects`; bounded summary; no cache/model reads |
| `GET /objects/{id}` | **full-sweep complete** | one current data-plane statement, no component-schema cache |
| `PUT /objects/{id}/canonical-name` | route-local closed | bounded Object read/update + lifecycle |
| `POST /objects/{id}/properties` | route-local closed | binding read + READY semantic cache + short protected UoW |
| `GET /objects/{id}/schema` | route-local closed | one Object -> ObjectTemplate PK-to-PK statement |
| `POST /objects/{id}/schema` | public surface retained; execution active revalidation | immutable migration plan + intrinsic revalidation + slot-delta maintenance |
| `GET /objects/{parent}/components/{slot}` | route-local checkpoint | one current data-plane statement |
| `POST /objects/{parent}/components/{slot}/attach` | public semantics retained; execution revalidated | current slot materialization + ancestry cache + graph admission + FK arbitration |
| `POST /objects/{parent}/components/{slot}/detach` | public semantics retained; execution revalidated | set-based current-edge delete + lifecycle |
| `GET /objects/{child}/owner` | working current-fact candidate | one child-rooted statement over `objects` + `object_components` |
| `DELETE /objects/{id}` | route-local closed | one fused Object DELETE + DELETED lifecycle statement |

Object-relative Relationship and Lifecycle routes remain owned by their later top-down discovery passes even when the URL is rooted under `/objects`.

# 1. CREATE Object

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

## Candidate execution

Three stages remain preferred:

```text
STEP 1 — current binding resolution / early PUBLISHED admission
    PostgreSQL

STEP 2 — semantic preparation / property validation
    worker-local READY immutable semantic cache

STEP 3 — short mutation UoW
    final exact PUBLISHED admission/protection
    + INSERT Object
    + materialize all current component slots
    + CREATED lifecycle
```

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

Once STEP 1 resolves an exact binding, the command stays pinned to it. A concurrent later `SET_DEFAULT` does not retarget the in-flight CREATE.

STEP 1 must not load effective schema, parent chains, DataType semantics, component declarations or unrelated model metadata.

STEP 2 validates only from complete READY exact-version semantic cache state. The cache may contain stable direct-creation knowledge such as `abstract`, effective property semantics, exact DataTypeVersion semantics and compiled validators, but not mutable PUBLISHED/default state.

Missing or partial immutable knowledge is completed before validation and outside the mutation UoW. No model-plane PostgreSQL lock is held during cache fill, compilation, property validation or canonicalization.

Current STEP 3 candidate:

```text
BEGIN

S1
    final exact PUBLISHED admission/protection
    + INSERT objects row
    + bounded INSERT ... SELECT of all exact effective component slots
      into object_component_slots

S2
    INSERT CREATED lifecycle event

COMMIT
```

Object state, exact binding, materialized slot set and CREATED lifecycle transition must be atomic.

Required concurrency outcome:

```text
DEPRECATE wins before final admission
    -> CREATE cannot commit the new binding

CREATE final admission/protection wins first
    -> CREATE may commit
    -> DEPRECATE waits/proceeds afterward
```

Warm route statement direction remains approximately:

```text
1 minimal binding/PUBLISHED lookup
1 final admission + Object + slot materialization statement
1 CREATED lifecycle insert
```

Additional materialization work is proportional to effective slot count `S`, without touching `object_components` because a new Object starts with no ownership edges.

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

No explicit row locks, optimistic fingerprints, retries, coherent multi-statement read protocol or REPEATABLE READ transaction are required.

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

# 4. Mutate canonical name

## Public contract

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
```

Request:

```json
{
  "canonical_name": "server-2"
}
```

Rules:

```text
1..255 characters
no automatic normalization
not unique
not identity
```

Success:

```http
204 No Content
```

Same-name assignment is not treated as a semantic no-op. There is no pre-write equality check; a same-name request follows the normal mutation path and may emit a normal `RENAME` lifecycle event.

## Candidate execution

```text
Q1 unlocked preliminary complete intrinsic Object snapshot
    -> lifecycle before/after preparation

BEGIN

Q2 UPDATE objects.canonical_name by Object PK
    0 rows -> 404 resource_not_found
    1 row  -> continue

Q3 INSERT RENAME lifecycle event

COMMIT
```

Current Object row correctness is strong. RENAME lifecycle before/after snapshot precision under concurrent unrelated intrinsic mutation is deliberately best-effort/approximate.

No explicit Object row lock or optimistic fingerprint is required route-locally. Ordinary PostgreSQL row-update serialization is the current rendezvous for concurrent RENAME assignments.

The mutation updates only `canonical_name`; it must not overwrite concurrent `properties`, exact binding, ownership or Relationship state.

No ObjectTemplate, DataType, effective-schema, ancestry, ownership or Relationship knowledge is required.

Candidate successful cost:

```text
3 PostgreSQL business statements
0 cache
```

# 5. Mutate Object properties

## Public contract

```http
POST /api/v1/core/objects/{object_id}/properties
Content-Type: application/json
```

Request:

```json
{
  "operations": [
    {"op": "SET", "property": "hostname", "value": "srv02"},
    {"op": "REMOVE", "property": "description"}
  ]
}
```

Rules:

```text
operations required and non-empty
same property at most once per request
SET requires value
REMOVE has no value
array order has no semantic mutation-order meaning
```

Sparse semantics:

```text
REMOVE optional          -> key absent
SET optional LIST = []   -> prepared REMOVE/key absence
JSON null                -> invalid
REMOVE required          -> semantic failure
SET required LIST = []   -> semantic failure
```

Success:

```http
204 No Content
```

A semantic no-op also returns `204` but performs no UPDATE and emits no fake DATA_CHANGE event.

This operation mutates only runtime properties. It does not directly change Object identity/name, exact schema binding, ownership/components or Relationships.

## Candidate execution

```text
STEP 1
    minimal objects PK lookup
    -> existence + exact (template_id, template_version)
    -> no properties load

STEP 2
    ensure READY immutable exact-version validation semantics
    -> validate/canonicalize requested operations in worker
    -> no Object lock

STEP 3
    short protected mutation UoW
    -> fresh complete Object row
    -> exact binding must still match prepared binding
    -> apply prepared effects to fresh properties
```

An existing Object may remain pinned to a DEPRECATED exact ObjectTemplateVersion. Property mutation is not a new model-plane binding admission and therefore does not require current PUBLISHED status or current default resolution.

Untouched persisted properties remain valid by construction while the exact binding remains unchanged; the route validates only the requested semantic effects rather than re-certifying the complete Object.

Binding mismatch causes no mutation and a bounded restart from STEP 1/2. Cache fill never occurs while holding the Object lock.

Real change:

```text
protected complete Object read
UPDATE complete properties JSONB
INSERT DATA_CHANGE lifecycle
COMMIT
```

No-op:

```text
protected complete Object read
no UPDATE
no lifecycle INSERT
```

Warm candidate costs:

```text
real change = 4 PostgreSQL statements + COMMIT
no-op      = 2 PostgreSQL statements
```

Cold semantic-cache fill happens before the protected UoW.

Concurrency direction:

```text
property mutation x property mutation
    -> protected fresh-state application prevents lost JSONB updates

property mutation x SCHEMA_CHANGE
    -> property mutation commits on current binding first
       OR sees binding mismatch and restarts on the new binding

property mutation x DELETE
    -> mutation commits first OR later mutation observes absence
    -> no resurrection
```

This route introduces no new Object denormalization.

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

It does not expose effective schema, properties, components, namespace, description, lifecycle status, default state or other ObjectTemplate metadata.

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

The public surface is retained while the execution model remains actively revalidated after `object_component_slots`.

Current component-side direction:

```text
immutable MigrationPlan SOURCE -> TARGET

prepare/migrate intrinsic Object state outside the short UoW where safe

short SCHEMA_CHANGE UoW
    -> protect/revalidate mutable intrinsic Object state
    -> maintain object_component_slots delta atomically
    -> use edge->slot FK as final REMOVE/replacement blocker authority
    -> update Object exact binding + migrated properties
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

The new materialization reopens the earlier assumption that outgoing ownership membership must participate in the optimistic Object fingerprint. Preferred direction is now intrinsic Object fingerprinting plus final relational slot/edge arbitration, but exact fingerprint/UoW decomposition remains OPEN.

Detailed migration semantics, cache inputs, property rules, fingerprint and final UoW belong to the dedicated `object-schema-change.md` consolidation.

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

# 12. DELETE Object

## Public contract

```http
DELETE /api/v1/core/objects/{object_id}
```

No request body and no `force`, cascade, recursive/subtree or implicit-detach option.

Success:

```http
204 No Content
```

Absence is non-convergent:

```text
already absent -> 404 resource_not_found
```

Current lifetime dependency:

```text
-> 409 delete_blocked
```

Public `delete_blocked` detail remains bounded to selected Object identity; blocker identities/counts/constraint names are not required.

DELETE never implicitly:

```text
DETACHes ownership
removes factual Relationships
deletes a subtree
rewrites blockers
```

## Candidate execution

Preferred route-local candidate is one data-modifying PostgreSQL business statement:

```text
BEGIN

Q1
    DELETE objects root by id
    -> retain deleted row server-side
    -> construct DELETED before_state server-side
    -> INSERT exactly one DELETED lifecycle row
    -> return tiny success carrier

COMMIT
```

The server-side fusion avoids transferring the potentially large Object `properties` payload DB -> application -> DB solely to rebuild the historical snapshot.

Outcome classification:

```text
zero deleted/success rows
    -> 404

SQLSTATE 23503 attributable to current references blocking root Object DELETE
    -> 409 delete_blocked

one success row
    -> 204
```

The fused statement requires architecture to preserve unambiguous classification: an unrelated FK failure from the lifecycle branch must never be mislabeled `delete_blocked` merely because it also uses SQLSTATE `23503`.

No blocker precheck, separate Object snapshot read, model-plane recertification, cache work or diagnostic-only DB read is required.

Candidate success cost:

```text
1 PostgreSQL business statement
```

With `object_component_slots`:

```text
Object delete
    -> owned empty/current slot rows cascade
    -> referenced slot FK blocks deletion when attached children remain
```

Empty slot materialization does not itself become a lifetime blocker.

Architecture must prove DELETE races against all current Object-lifetime references and preserve Object deletion + DELETED lifecycle atomicity.

# Nested surfaces owned by later discovery passes

## Object lifecycle history

```http
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

This route remains for the Lifecycle discovery pass.

Important already-discovered consequence of enriching `ObjectDto` with current components:

```text
current ObjectDto
    != historical intrinsic Object snapshot
```

Historical intrinsic lifecycle `before` / `after` should remain bounded snapshots of:

```text
id
canonical_name
template_id
template_version
properties
```

rather than embedding current component projections. A distinct `ObjectSnapshotDto` is the current direction. Ownership history remains represented by explicit ATTACH_TO/DETACH_FROM events.

## Object-relative factual Relationship collection/detail

```text
GET /objects/{object_id}/relationships
Object-relative Relationship detail capability
```

These remain owned by the later factual Relationship top-down pass because public DTO/perspective semantics are still open. They are not folded into this Object operation owner merely because the URL is Object-rooted.

# Cross-operation observations

## Component-schema cache boundary

`object_component_slots` does **not** delete the immutable exact component-schema cache as a system capability.

It removes the normal component-schema cache dependency from these current Object runtime candidates:

```text
GET Object
GET one component slot
ATTACH slot resolution
DETACH
```

Immutable exact schema/validation caches remain useful where semantic validation or migration genuinely needs model-plane knowledge, including CREATE properties validation, properties mutation and SCHEMA_CHANGE preparation.

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
final global LockPlan/deadlock realization
```

Those belong to the later M4 architecture-wide persistence/concurrency phase.

# Route-owner comparison closure

The route-owner consolidation has been checked against the current owner/checkpoint files for:

```text
CREATE
LIST
GET
canonical-name mutation
properties mutation
Object schema GET/public POST surface
component-slot navigation + cursor/data-path checkpoints
ATTACH
DETACH
GET owner working projection
DELETE
```

Non-superseded contract, failure, concurrency and cost details omitted by the first consolidation draft have been recovered here. Historical rationale and already-superseded mechanisms are intentionally not duplicated.

The remaining pre-cleanup work is cross-cutting rather than route-owner reconstruction:

```text
1. build object-components-persistence.md
2. build object-schema-change.md
3. reconcile references from surviving non-Object WIPs
4. then remove superseded Object route-local/micro-step WIPs
```

Until those two cross-cutting owners exist, their current source WIPs remain necessary comparison evidence and should not be deleted.