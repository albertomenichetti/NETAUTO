# M4 WIP — Object TO-BE consolidated discovery

**Status:** ACTIVE CONSOLIDATION / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for the M4 Object operation family during discovery.

It exists to replace the growing set of route-local and micro-step Object WIPs with one readable current checkpoint while preserving the project rule that everything under `wip/` remains non-normative until deliberately adopted into the M4 contract/architecture set.

During this first consolidation pass the older route-local files still remain in the repository as comparison evidence. After a lossless consistency check, superseded micro-WIPs can be removed; Git history remains the historical record.

Detailed cross-operation component persistence is intentionally kept outside this file and is currently owned by the materialization/schema WIPs that will be consolidated separately into `object-components-persistence.md`.

Detailed Object schema-migration mechanics are intentionally kept outside this file and will be consolidated separately into `object-schema-change.md`.

## Shared Object runtime candidate

Current intrinsic Object state remains:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties JSONB
```

Current Object component/ownership candidate is:

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

It is not a second semantic authority. The semantic source remains the Object current exact ObjectTemplateVersion and its certified immutable effective schema. The data-plane table is a transactionally maintained runtime derivative.

Fundamental candidate invariant:

```text
MaterializedSlots(O)
    ==
EffectiveComponentSlots(
    O.template_id,
    O.template_version
)
```

The Object exact binding and the corresponding materialized slot set must become visible atomically.

Current semantic slot identity is:

```text
(slot_declaring_template_id, slot_name)
```

Current public/runtime slot lookup is:

```text
(object_id, slot_name)
```

The current ownership-edge candidate references the current semantic slot relationally:

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
| `POST /objects` | public contract retained; slot persistence revalidated | current admission + READY semantic cache + Object/slot materialization |
| `GET /objects` | route-local closed | one statement on `objects` |
| `GET /objects/{id}` | revalidated after slot materialization | one current data-plane statement, no component-schema cache |
| `PUT /objects/{id}/canonical-name` | route-local closed | bounded Object read/update + lifecycle |
| `POST /objects/{id}/properties` | route-local closed | binding read + READY semantic cache + short protected UoW |
| `GET /objects/{id}/schema` | route-local closed | one Object -> ObjectTemplate PK-to-PK statement |
| `POST /objects/{id}/schema` | public surface retained; execution active revalidation | immutable migration plan + intrinsic revalidation + slot-delta maintenance |
| `GET /objects/{parent}/components/{slot}` | route-local discovery checkpoint | one current data-plane statement |
| `POST /objects/{parent}/components/{slot}/attach` | public semantics retained; execution revalidated | current slot materialization + ancestry cache + graph admission + FK arbitration |
| `POST /objects/{parent}/components/{slot}/detach` | public semantics retained; execution revalidated | set-based current-edge delete + lifecycle |
| `GET /objects/{child}/owner` | working current-fact candidate | one child-rooted statement over `objects` + `object_components` |
| `DELETE /objects/{id}` | route-local closed | one fused Object DELETE + DELETED lifecycle statement |

Object-relative Relationship and Lifecycle routes are listed near the end of this file for navigation, but their semantic/detail closure remains owned by the later Relationship/Lifecycle discovery passes.

# 1. CREATE Object

## Public contract

```http
POST /api/v1/core/objects
Content-Type: application/json
```

Request candidate:

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
    -> exact (template_id, version)

version omitted
    -> current default_version of template_id

no default
    -> failure

no latest/highest-PUBLISHED fallback
```

The Object id is server-generated.

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
optional scalar/list omitted -> key absent
optional LIST = []            -> canonical key absence
JSON null                     -> invalid
required property omitted     -> invalid
required LIST = []            -> invalid
```

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

STEP 1 must not load effective schema, parent chains, DataType semantics or unrelated model metadata.

STEP 2 validates only from complete READY exact-version semantic cache state. Missing/partial immutable knowledge is completed before validation and outside the mutation UoW.

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

Warm route statement direction remains approximately:

```text
1 minimal binding/PUBLISHED lookup
1 final admission + Object + slot materialization statement
1 CREATED lifecycle insert
```

Additional materialization work is proportional to effective slot count `S`, without touching `object_components` because a new Object starts with no ownership edges.

# 2. LIST Objects

## Public contract

```http
GET /api/v1/core/objects
```

Supported query parameters:

```text
object_template_id: UUID | optional
object_template_version: positive integer | optional
canonical_name: string | optional
cursor: string | optional
limit: positive integer | optional, default 100
```

Validation:

```text
object_template_version requires object_template_id
```

Filters are exact and non-polymorphic:

```text
object_template_id
    -> objects.template_id equality only

object_template_version
    -> objects.template_version equality within selected lineage

canonical_name
    -> exact equality
```

Unknown filter values return an empty `200` page rather than `404`.

Response item:

```json
{
  "id": "<object-id>",
  "canonical_name": "server-1",
  "object_template": {
    "id": "<template-id>",
    "version": 4
  }
}
```

Collection items intentionally exclude:

```text
properties
components
owner
relationships
ObjectTemplate mutable metadata
```

Pagination remains deterministic keyset pagination by Object id:

```text
ORDER BY objects.id ASC
cursor position = last Object id
cursor identity = complete active filter set
```

## Data path

```text
1 PostgreSQL statement on objects
0 cache
0 locks
0 model-plane reads
```

The query projects only:

```text
id
canonical_name
template_id
template_version
```

Physical index review remains architecture-wide.

# 3. GET Object

## Public contract

```http
GET /api/v1/core/objects/{object_id}
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

while public representation exposes only `slot_name`.

The SQL carrier must preserve these semantic cases:

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

The preferred logical result must avoid transferring the potentially large root `properties` payload once per child. The exact physical carrier is deliberately open between equivalent one-statement realizations such as aggregated fact carriers or tagged fact streams.

Required logical work remains:

```text
O(1 + S + C)
```

where:

```text
S = effective current slot count
C = direct child count
```

Typical workload expectation used during revalidation is `S << C`; the GET must read the `C` component facts anyway, making the additional `S` current-slot rows a small incremental data-plane cost in the common case.

The key comparison against the former warm cache path is therefore:

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

Because the slot materialization is assumed to exist independently for other Object workloads, its storage/write-maintenance cost is not attributed to this GET decision.

## Concurrency/read semantics

One response must be explainable by one current PostgreSQL statement snapshot.

The candidate correctly handles:

```text
SCHEMA_CHANGE
    -> old binding + old slot set OR new binding + new slot set
    -> never a cross-generation mixture

ATTACH
    -> child absent before commit / present after commit

DETACH
    -> child present before commit / absent after commit
    -> current slot remains visible as [] when last child is removed

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

Same-name assignment is not treated as a semantic no-op. The command follows the normal mutation path and may emit a normal `RENAME` lifecycle event.

## Candidate execution

```text
Q1 unlocked preliminary complete intrinsic Object snapshot
    -> lifecycle before/after preparation

BEGIN

Q2 UPDATE objects.canonical_name by Object PK

Q3 INSERT RENAME lifecycle event

COMMIT
```

Current Object row correctness is strong. RENAME lifecycle before/after snapshot precision under concurrent unrelated intrinsic mutation is deliberately best-effort/approximate.

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

Sparse semantics remain:

```text
REMOVE optional -> key absent
SET optional LIST = [] -> prepared REMOVE/key absence
JSON null -> invalid
REMOVE required -> semantic failure
SET required LIST = [] -> semantic failure
```

Success:

```http
204 No Content
```

A semantic no-op also returns `204` but performs no UPDATE and emits no fake DATA_CHANGE event.

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

Binding mismatch causes no mutation and a bounded restart from STEP 1/2.

Real change:

```text
protected Object read
UPDATE complete properties JSONB
INSERT DATA_CHANGE lifecycle
COMMIT
```

No-op:

```text
protected Object read
no UPDATE
no lifecycle INSERT
```

Warm candidate costs:

```text
real change = 4 PostgreSQL statements + COMMIT
no-op      = 2 PostgreSQL statements
```

Cold semantic-cache fill happens before the protected UoW.

This route does not read ownership/components/Relationships and introduces no new Object denormalization.

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

It does not expose effective schema, properties, components or other ObjectTemplate metadata.

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

The public surface is retained, while the execution model remains actively revalidated after `object_component_slots`.

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

Detailed migration semantics, cache inputs, property rules, fingerprint and final UoW are intentionally deferred to the dedicated consolidated `object-schema-change.md` owner to be created in the next consolidation pass.

# 8. GET one component slot

## Public contract

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

There is no generic public cross-slot collection in the TO-BE candidate:

```text
GET /objects/{parent}/components
    -> not retained
```

The complete Object GET already exposes all direct slots/children; the specialized route exists for selective bounded pagination of one slot.

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

Current-state precedence:

```text
parent absent -> 404 object
slot absent -> 404 object_component_slot
slot present but cursor declaring lineage differs -> 400 invalid_cursor
otherwise -> normal continuation
```

ATTACH/DETACH, child RENAME and target widening do not invalidate a cursor merely because membership/display state changes; cross-request repeatable membership is not promised.

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

Any requested child already owning any edge causes whole-batch failure, including the exact same current parent/slot edge. There is no convergent `ON CONFLICT` success.

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

No parent exact-template read or component-schema cache lookup is required merely to resolve the current slot contract.

One bulk child Object read returns:

```text
id
template_id
canonical_name
```

and stable-lineage compatibility is checked against slot `target_template_id` through the stable ObjectTemplate ancestry cache.

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

Graph admission precedence remains:

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

The slot FK becomes the preferred narrow ATTACH x SCHEMA_CHANGE arbitration point for slot REMOVE/semantic replacement. Target widening is non-key and semantically monotonic.

Candidate successful costs:

```text
warm      = 6 PostgreSQL statements + COMMIT
full-cold = 7 PostgreSQL statements + COMMIT
```

The only normal semantic-cache cold fill left is stable child-lineage ancestry.

Still open:

```text
final failure mapping when slot disappears/replaces after unlocked preparation
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

Failure direction:

```text
parent absent -> 404
requested child absent -> 422 referenced_resource_not_found
incomplete exact edge set -> 409 ownership_conflict
```

No diagnostics-only DB reads are introduced.

Candidate cost:

```text
success = 2 PostgreSQL statements + COMMIT
failure classified by Q1 = 1 statement + rollback
static failure = 0 DB
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

The public-surface shape remains a point to recheck during the Object consistency sweep before architecture freeze; this section must not silently create a new public contract from the current implementation alone.

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

root Object DELETE current-reference FK violation
    -> 409 delete_blocked

one success row
    -> 204
```

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

Architecture must preserve unambiguous failure classification for fused DELETE/lifecycle work and prove DELETE races against all current Object-lifetime references.

# Nested surfaces owned by later discovery passes

The repository currently also exposes or explores Object-rooted routes whose business owner is not the Object aggregate itself.

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

Historical lifecycle `before` / `after` should remain bounded intrinsic snapshots rather than recursively embedding current component projections. A distinct `ObjectSnapshotDto` is the current direction.

## Object-relative factual Relationship collection/detail

```text
GET /objects/{object_id}/relationships
Object-relative Relationship detail capability
```

These remain owned by the later factual Relationship top-down pass because public DTO/perspective semantics are still open. They are not folded into this Object operation owner merely because the URL is Object-rooted.

# Cross-operation observations

## Current component-schema cache consumers

`object_component_slots` does **not** delete the immutable exact component-schema cache as a system capability.

It currently removes the normal cache dependency from these Object runtime candidates:

```text
GET Object
GET one component slot
ATTACH slot resolution
DETACH
```

Immutable exact schema/validation caches remain useful where semantic validation or migration genuinely needs model-plane knowledge.

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

# Consolidation sources

This first consolidated version was built from the current route-local owners and current revalidation findings, including at least:

```text
to-be-api-object-create.md
to-be-api-object-list.md
to-be-api-object-get.md
to-be-api-object-rename.md
to-be-api-object-properties-mutation.md
to-be-api-object-schema.md
object-components-navigation-public-contract.md
to-be-api-object-attach-batch.md
to-be-api-object-detach-batch.md
object-components-reads-discovery.md
to-be-api-object-delete.md
object-component-slots-data-plane-materialization.md
```

The older files remain temporarily in the tree for a lossless comparison pass. Their continued presence during consolidation does not make older superseded checkpoints preferable to the current candidate summarized here.

# Next consolidation steps

Before removing old Object WIPs:

```text
1. compare this consolidated owner against every route-local owner
2. recover any non-superseded semantic/error/cost detail accidentally omitted
3. reconcile cross-references that point to micro-WIPs
4. consolidate component persistence into object-components-persistence.md
5. consolidate SCHEMA_CHANGE internals into object-schema-change.md
6. only then delete superseded Object micro-WIPs
```

Git history remains the source for historical discovery checkpoints after cleanup.
