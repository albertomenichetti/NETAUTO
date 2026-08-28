# M4 TO-BE API — Object GET

Status: PUBLIC CONTRACT RETAINED / DATA PATH REOPENED / M4 WIP / NON-NORMATIVE GLOBALLY

## Reopen notice — per-Object component-slot materialization

The public Object representation in this file remains the current discovery checkpoint.

The previous route-local closure of the following technical areas is **reopened** by [`object-component-slots-data-plane-materialization.md`](object-component-slots-data-plane-materialization.md):

```text
persistence structures
data path
component-schema cache dependency
warm/cold cost
multi-statement coherent-read realization
denormalization conclusion
relational/index implications
```

In particular, the earlier claims:

```text
GET Object warm = 2 PostgreSQL statements + component-schema cache
GET Object cold = 3 PostgreSQL statements + cache fill
no additional Object-specific denormalization is required
```

are retained below only as the superseded checkpoint that triggered further discovery. They must not be used as the current candidate without revalidating against the new per-Object `object_component_slots` materialization.

The active candidate now being explored is one PostgreSQL statement over current Object + materialized current slots + ownership edges + child names, with no normal GET component-schema cache dependency.

This file originally recorded the agreed TO-BE design for the single route `GET /api/v1/core/objects/{object_id}`.

The route had been considered closed for the current M4 top-down sweep across:

- public signature;
- success wire model;
- touched persistence structures;
- AS-IS cost;
- TO-BE hot and cold data paths;
- denormalization/materialization dependencies;
- concurrency/read-coherence requirement;
- cache behavior and fill policy;
- relational-schema implications.

That technical closure is now partially reopened as described above. No WIP closure constitutes the global M4 normative freeze or authorizes implementation by itself.

## Signature

```http
GET /api/v1/core/objects/{object_id}
```

Path parameters:

```text
object_id: UUID
```

Request body: none.

Query parameters: none.

Success status: `200 OK`.

Missing Object: common public `404` resource-not-found semantics.

## Success representation

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "canonical_name": "server-1",
  "object_template": {
    "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "version": 4
  },
  "properties": {
    "hostname": "srv01",
    "serial_number": "ABC123"
  },
  "components": {
    "interfaces": [
      {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "canonical_name": "eth0"
      },
      {
        "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "canonical_name": "eth1"
      }
    ],
    "disks": []
  }
}
```

## Wire model

```text
ObjectDto
    id: UUID
    canonical_name: string
    object_template: ExactObjectTemplateRef
    properties: object<string, JsonValue>
    components: object<slot_name, ObjectReference[]>

ExactObjectTemplateRef
    id: UUID
    version: positive integer

ObjectReference
    id: UUID
    canonical_name: string
```

## Exact ObjectTemplate reference

The ObjectTemplate lineage id and exact version remain part of the public Object representation because together they identify the exact schema contract under which the Object current state is interpreted.

They are exposed as one structured reference:

```json
"object_template": {
  "id": "...",
  "version": 4
}
```

The GET does not include ObjectTemplate `namespace`, `name`, `description`, default state or other mutable metadata. Consumers that need those details use the ObjectTemplate APIs separately.

## Properties semantics

`properties` is the complete current canonical property map of the Object under its current exact ObjectTemplateVersion.

It is not a summary or a sparse projection chosen by the read API. Optional absent properties remain absent keys according to the Object domain contract.

## Components semantics

`components` contains every effective component slot of the Object current exact ObjectTemplateVersion.

A valid slot with no currently attached child is present explicitly as an empty array:

```json
"components": {
  "interfaces": []
}
```

If the exact ObjectTemplateVersion defines no component slots at all, the field remains present:

```json
"components": {}
```

Each direct child is represented only by:

```json
{
  "id": "...",
  "canonical_name": "eth0"
}
```

The GET does not recursively expand child properties or child components.

Concrete projection boundary:

```text
GET server-1
    -> server-1 current properties
    -> all effective direct component slots
    -> direct child identity + current canonical name
    -> STOP
```

## Explicit exclusions

The Object GET does not include:

```text
owner
relationships
child properties
child components recursively
slot_declaring_template_id
ObjectTemplate mutable metadata
```

Reverse owner and factual Relationship navigation remain separate public concerns.

`slot_declaring_template_id` remains an internal semantic identity component for ownership but is not part of the normal public component representation.

## Ordering

JSON object key order has no contractual meaning, including the order of keys inside `components`.

Children inside a slot are returned in deterministic ascending `child_object_id` order. Array position has no domain meaning beyond deterministic projection.

## Superseded technical checkpoint below

Everything from this point through the former route-local closure records the previous cache-based technical candidate. It is kept as discovery evidence, not as the current data-path candidate. See the reopen notice and `object-component-slots-data-plane-materialization.md` before relying on it.

## Persistence structures touched

### Current Object state

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties
```

This remains the authority for the current intrinsic Object state.

### Current ownership/component facts

M4 TO-BE ownership rows are expected to expose the stable slot semantic identity directly:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

For this GET, the persistence path uses:

```text
parent_object_id
slot_declaring_template_id
slot_name
child_object_id
```

and joins `objects AS child` only to obtain each current child `canonical_name`.

### Immutable exact effective component contract

The GET needs the complete effective component-slot set for the Object current exact `(template_id, template_version)` so that empty valid slots can be emitted as `[]`.

That information comes from the M4 exact immutable effective-component materialization discussed during bottom-up discovery, conceptually:

```text
object_template_effective_components
    template_id
    template_version
    declaring_template_id
    name
    position
    target_template_id
```

The Object GET consumes this structure as immutable certified knowledge; it does not recursively reconstruct ObjectTemplate inheritance.

## AS-IS cost

Current `GET /objects/{id}` is one of the cheapest reads in the kernel:

```text
1 PostgreSQL statement
    SELECT objects by primary key

no joins
no ObjectTemplate access
no component access
no cache lookup
```

It returns only root Object state.

The TO-BE representation is intentionally richer, so it necessarily adds work to obtain direct component state and empty effective slots.

## TO-BE data-path principle

The TO-BE path separates three distinct questions:

```text
Q1: what is the current Object root state?
Q2: which current child Objects are actually attached, and through which semantic slots?
Q3: what is the complete immutable effective component-slot contract for the exact ObjectTemplate version?
```

`Q3` is not a mandatory database query on every request: the exact component contract is immutable and is served from a worker-local cache on the warm path.

## TO-BE hot path

The normal warm path is:

```text
BEGIN coherent read

Q1
    objects by object_id
    -> id
    -> canonical_name
    -> template_id
    -> template_version
    -> properties

CACHE LOOKUP
    key = (template_id, template_version)
    facet = exact effective component schema
    -> HIT

Q2
    object_components for parent_object_id
    JOIN objects AS child
    -> slot_declaring_template_id
    -> slot_name
    -> child_object_id
    -> child canonical_name

APPLICATION MERGE
    immutable declared slot set
    + current attached child set
    -> complete components map
    -> missing attached semantic keys become []

END coherent read
```

Database cost on the warm path:

```text
2 PostgreSQL statements
+ 1 worker-local immutable cache lookup
```

No ObjectTemplate database read is performed on the warm path.

## TO-BE cold path

On cache miss, the GET performs one additional read-through load:

```text
BEGIN coherent read

Q1
    current Object root

CACHE LOOKUP
    (template_id, template_version)
    -> MISS

Q3
    load ALL effective component slots for that exact ObjectTemplateVersion
    -> declaring_template_id
    -> name
    -> position
    -> target_template_id

CACHE FILL
    store the complete exact effective-component result

Q2
    current attached child set
    + child canonical names

APPLICATION MERGE
    declared slot set
    + attached child set
    -> complete components map including []

END coherent read
```

Database cost on the cold path:

```text
3 PostgreSQL statements
+ cache fill
```

The cold loader deliberately returns the complete exact effective-component set, not only currently empty slots.

The application computes empty slots by set difference between:

```text
declared semantic slot keys
    (declaring_template_id, name)

and

attached semantic slot keys
    (slot_declaring_template_id, slot_name)
```

This avoids a dedicated `NOT EXISTS` query for empty slots and makes the cold database read reusable immutable knowledge.

## Why Q2 is runtime-first

Existing attachments are read directly from the data-plane ownership facts:

```text
object_components
    WHERE parent_object_id = :object_id
```

The query does not start from the ObjectTemplate model and probe each slot for children.

Because `object_components` carries `slot_declaring_template_id + slot_name`, each existing edge already identifies its stable semantic slot.

The model-plane exact component contract is required only to know the full declared slot set, including slots with zero current edges.

This keeps the potentially high-cardinality portion of the read — current attached children — as a direct data-plane access path.

## Application merge

Example immutable exact component schema:

```text
Device / interfaces
Server / disks
Server / power_supplies
```

Example Q2 current attached state:

```text
Device / interfaces      -> eth0
Device / interfaces      -> eth1
Server / power_supplies  -> psu0
```

Application merge produces:

```text
interfaces      -> [eth0, eth1]
disks           -> []
power_supplies  -> [psu0]
```

The internal merge key is the stable semantic slot identity:

```text
(declaring_template_id, slot_name)
```

The public JSON key remains only `slot_name` according to the frozen wire contract.

## Cache design

The Object GET needs an independently loadable immutable component-schema cache facet.

Conceptually:

```text
EffectiveObjectTemplateComponentsCache[(template_id, version)]
    ordered effective slots:
        declaring_template_id
        name
        position
        target_template_id
```

This may be implemented as a dedicated cache or as an independently fillable facet of a broader immutable ObjectTemplate cache. The architectural requirement is that a GET cache miss must not require loading unrelated property schemas, DataType semantics or compiled validators.

### Cacheability

Only exact immutable ObjectTemplate component contracts are cached.

The cache does not contain:

```text
Object current state
object_components current ownership state
child canonical names
ObjectTemplate mutable default state
```

### Fill policy

```text
GET warm hit
    -> no ObjectTemplate DB query

GET cold miss
    -> Q3 loads complete exact effective component set
    -> same result fills the cache

other paths
    -> may opportunistically fill the same facet if the complete exact effective-component payload is already present
    -> must not issue an extra query solely to warm this cache
```

### Invalidation

No invalidation protocol is required.

The cache key identifies an exact immutable ObjectTemplateVersion. PUBLISHED -> DEPRECATED does not alter the cached semantic component payload.

## Concurrency/read-coherence requirement

The public response must be one coherent observation of current mutable Object state:

```text
root Object exact template pin
root Object properties
current ownership edges
current child canonical names
```

In particular, the GET must not combine:

```text
Object root observed before a concurrent SCHEMA_CHANGE
with
ownership/current child state observed after that change
```

or equivalent mixed observations across concurrent:

```text
SCHEMA_CHANGE
ATTACH
DETACH
Object RENAME on a child
```

Therefore Q1 and Q2 execute inside the same coherent PostgreSQL read snapshot.

Q3/cache data is exact immutable semantic knowledge and can safely be combined with that current-state snapshot without a distributed invalidation protocol.

This route requires read coherence, not application-level row locking. The following architecture phase will choose/confirm the concrete PostgreSQL transaction realization of the coherent read.

## Denormalization/materialization coverage

The bottom-up M4 discoveries already provide the two changes needed by this route:

### Enriched runtime ownership fact

```text
object_components
    + slot_declaring_template_id
```

This prevents Q2 from traversing the ObjectTemplate model simply to recover the declaring lineage for an existing attachment.

### Exact immutable effective-component materialization

```text
object_template_effective_components
```

This prevents Q3 from recursively traversing exact ObjectTemplate inheritance on cache miss.

No additional Object-specific denormalization is currently required by this route.

## Relational-schema implications

For the Object data-plane itself, the route relies on:

```text
objects
    unchanged in conceptual shape

object_components
    enriched with slot_declaring_template_id
```

For immutable model knowledge consumed by the route, it relies on the planned exact effective-component materialization.

The route does not justify copying any of the following into `objects` or `object_components`:

```text
components JSONB
child canonical_name
slot_declaring_template_version
target_template_id
parent ObjectTemplateVersion
slot position
```

Those would introduce mutable/stale duplication or collapse separate authorities.

## Cost characterization

### Warm path

```text
Q1
    primary-key Object lookup

cache
    exact immutable component-contract lookup

Q2
    all ownership rows for one parent
    + child Object PK joins for canonical names

application
    set/group merge
```

Expected scaling:

```text
O(number of direct attached children + number of effective slots)
```

The effective-slot term is handled in worker memory on the warm path.

### Cold path

Adds:

```text
Q3
    one complete exact effective-component range read
```

The cold cost is amortized across subsequent Objects using the same exact ObjectTemplateVersion in the same worker.

The route performs no:

```text
recursive inheritance traversal
DataType loading
property-schema loading
validator compilation
child property loading
transitive child expansion
Relationship loading
N+1 child GETs
```

## Physical index review — deferred architecture item

The logical access paths above are closed, but the exact physical index set is intentionally not frozen in this route document.

The following architecture phase must review the complete M4 workload and confirm the minimal index set that supports at least:

```text
Q1
    objects by primary key

Q2
    object_components by parent_object_id
    efficient grouping/lookup by stable semantic slot
    deterministic child_object_id order where useful
    child objects by primary key

Q3
    exact effective components by (template_id, template_version)
    deterministic position order
```

The review must consider all competing Object/ownership operations before deciding whether existing indexes are replaced, extended or retained. The goal is to avoid route-local duplicate indexes that would unnecessarily increase ATTACH/DETACH write cost.

This index review was the only explicit deferred physical-design item for the superseded cache-based route closure.

## Superseded route-local closure

The following block records the former cache-based technical closure and is no longer the current candidate:

```text
PUBLIC
    GET /objects/{object_id}
    -> complete current Object properties
    -> structured exact ObjectTemplate reference
    -> every effective direct component slot
    -> direct child {id, canonical_name}
    -> explicit [] for empty valid slots

HOT DATA PATH
    coherent read
    Q1 current Object root
    immutable component-schema cache HIT
    Q2 current attachments + child names
    application merge
    -> 2 DB statements

COLD DATA PATH
    coherent read
    Q1 current Object root
    immutable component-schema cache MISS
    Q3 full exact effective component contract
    cache fill
    Q2 current attachments + child names
    application merge
    -> 3 DB statements

CURRENT MUTABLE AUTHORITY
    objects
    object_components
    child objects canonical_name

IMMUTABLE DERIVED KNOWLEDGE
    exact effective component contract
    worker-local cacheable

CONCURRENCY
    Q1 + Q2 must share one coherent PostgreSQL read snapshot
    no application row locks required for this GET

SCHEMA DEPENDENCIES
    object_components.slot_declaring_template_id
    exact effective-component materialization
```
