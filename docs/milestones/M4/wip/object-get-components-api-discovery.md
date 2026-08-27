# M4 WIP — Object GET and components API discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the current M4 brainstorming around the public shape of `GET /objects/{id}`, the role of component-slot navigation, and the interaction with the proposed enrichment of `object_components` with stable slot semantic identity.

This is discovery only. It does not freeze the public contract.

## Concrete consumer problem

Consider an Object `server-1` whose exact ObjectTemplate schema contains:

```text
properties:
    hostname
    serial_number

components:
    interfaces -> Interface
    disks      -> Disk
```

with current runtime state:

```text
properties:
    hostname      = srv01
    serial_number = ABC123

components:
    interfaces -> eth0
    interfaces -> eth1
    disks      -> disk0
```

The current `GET /objects/server-1` returns the property values but none of the direct components. That shape is easy to explain from the persistence model because properties live in the `objects.properties` JSONB column while components live in `object_components`, but persistence convenience is not a sufficient public-API reason for exposing properties and omitting components.

The analogous ObjectTemplate effective-schema API already returns a complete exact schema even though inheritance depth and resulting member count are not structurally bounded. Therefore `0..N` component cardinality alone is not a sufficient architectural argument for excluding direct components from Object GET.

## Strong candidate Object GET shape

Current brainstorming favors a first-level complete projection such as:

```json
{
  "id": "...",
  "canonical_name": "server-1",
  "template_id": "...",
  "template_version": 4,
  "properties": {
    "hostname": "srv01",
    "serial_number": "ABC123"
  },
  "components": {
    "interfaces": [
      {"id": "...", "canonical_name": "eth0"},
      {"id": "...", "canonical_name": "eth1"}
    ],
    "disks": [
      {"id": "...", "canonical_name": "disk0"}
    ]
  }
}
```

The projection stops after one component level. Child Objects are represented only by stable Object identity and current canonical name; their own properties/components are not recursively expanded.

Concrete boundary:

```text
GET server-1
    -> server-1 properties
    -> direct children eth0, eth1, disk0
    -> STOP

GET eth0 separately
    -> required to inspect eth0 itself
```

The parent Object's current owner is intentionally not injected into this representation. If `eth0` is attached to `server-1.interfaces`, that fact originates from the parent Object's component slot, not from the `Interface` ObjectTemplate contract. Reverse ownership therefore remains a separate navigation concern.

## Empty effective slots

A strong candidate is to include effective component slots even when currently empty:

```json
"components": {
  "interfaces": [],
  "disks": [
    {"id": "...", "canonical_name": "disk0"}
  ]
}
```

This lets a consumer distinguish:

```text
slot exists but has no attached child
```

from:

```text
slot does not exist in this Object's exact schema
```

If this shape is retained, construction needs the exact immutable effective-component materialization for the Object's `(template_id, template_version)` plus current ownership edges and child Object names.

## Relationship to M4 object_components enrichment

The proposed runtime ownership row is:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

with no `slot_declaring_template_version`, no copied target lineage, and no copied parent exact version.

This materially simplifies complete Object projection. Current ownership facts already contain the stable slot semantic identity; GET no longer needs recursive exact-ObjectTemplate traversal merely to rediscover `slot_declaring_template_id`.

A candidate one-statement projector can combine:

```text
Object root
+ exact immutable effective component slots
+ current object_components edges
+ child objects for canonical_name
```

without model-plane recertification.

## Specialized component-slot endpoint

Once `GET /objects/{id}` exposes all direct children, the old generic endpoint:

```text
GET /objects/{id}/components
```

would mostly repeat a subset of the Object response. Its only concrete extra value is selective access to one potentially large slot with pagination.

The current strong candidate is therefore to replace the generic optional-filter shape with an explicit slot resource:

```text
GET /objects/{id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

Example:

```text
GET /objects/server-1/components/interfaces?limit=100
```

Candidate response:

```json
{
  "items": [
    {"id": "...", "canonical_name": "eth0"},
    {"id": "...", "canonical_name": "eth1"}
  ],
  "next_cursor": null
}
```

The endpoint therefore becomes a paged view of exactly one slot already visible inside `GET /objects/{id}`. It must not expose a second poorer child representation.

Candidate child representation in both surfaces:

```json
{
  "id": "...",
  "canonical_name": "eth0"
}
```

`slot_declaring_template_id` remains required internally for semantic identity but is not currently justified as a normal public child field.

## Slot existence semantics

The explicit slot path enables a useful distinction:

```text
slot exists and has no children
    -> 200 {"items": [], "next_cursor": null}

slot does not exist in this Object's exact effective schema
    -> explicit error / not-found style outcome for the requested slot
```

Returning an empty list for a nonexistent slot would hide the difference between an empty valid slot and an invalid slot name.

The precise public error code/status remains OPEN for later API-contract design.

## Reverse owner endpoint remains distinct

`GET /objects/{child}/owner` is not equivalent to the parent component projection.

Concrete example:

```text
server-1.interfaces -> eth0
```

`GET /objects/server-1` naturally exposes `eth0` under `interfaces` because that slot belongs to `server-1`'s exact template contract.

`GET /objects/eth0` should not automatically expose `server-1` as part of the Object representation because the fact that another Object contains `eth0` does not originate from `eth0`'s own template.

Therefore:

```text
GET /objects/{id}
    -> properties and component slots defined by that Object's exact template

GET /objects/{id}/components/{slot_name}
    -> paged access to one of those slots

GET /objects/{id}/owner
    -> reverse lookup: which parent currently contains this Object, if any
```

The owner endpoint therefore remains conceptually useful even if generic `/components` is replaced by the explicit slot endpoint.

## Abstract architectural reading

The concrete proposal corresponds to treating public Object GET as a complete first-level representation of the current Object instance rather than exposing only the fields colocated in the root persistence row.

The ownership graph remains non-recursive at this surface: direct composition is included, transitive graph expansion is not.

The specialized component-slot endpoint is justified as a bounded navigation/query surface for one large direct-child set, not as a second semantic representation of ownership.

Reverse owner navigation remains separate because it is an incoming reference defined by another Object's component slot rather than a member declared by the child's own ObjectTemplate.

## Open decisions

- whether complete first-level components become mandatory in `ObjectDto`;
- whether every effective empty slot is included as `[]`;
- exact ordering of component-slot keys and children;
- exact public route/status semantics for a nonexistent requested slot;
- whether `slot_declaring_template_id` disappears from the public component-slot response entirely;
- performance/size guardrails, if any, for Objects with very large direct child sets;
- whether Object mutation responses (`CREATE`, `RENAME`, `DATA_CHANGE`, `SCHEMA_CHANGE`) use the same enriched Object representation or retain a mutation-specific lighter shape;
- interaction with lifecycle snapshots, whose current historical `ObjectDto` shape contains only root Object fields;
- whether the existing generic `GET /objects/{id}/components` route is removed or retained only for compatibility during transition.
