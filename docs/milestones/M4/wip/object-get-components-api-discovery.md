# M4 WIP — Object GET and components API discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the current M4 brainstorming around the public shape of `GET /objects/{id}` and the role of `GET /objects/{id}/components` after the proposed enrichment of `object_components` with stable slot semantic identity.

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

## Role of GET /objects/{id}/components

If Object GET contains all first-level components, `/objects/{id}/components` becomes intentionally a subset of the Object representation. That is acceptable only if it has a concrete specialized role.

The current endpoint has two capabilities the complete Object GET would not necessarily provide:

```text
slot_name filtering
cursor/limit pagination
```

The current candidate role is therefore:

```text
GET /objects/{id}
    -> normal complete first-level Object view

GET /objects/{id}/components
    -> specialized paged/filterable access to the same direct children
```

The component endpoint should not expose a different, poorer representation of the same child.

Current candidate child representation in both surfaces:

```json
{
  "id": "...",
  "canonical_name": "eth0"
}
```

If `/components` is called without `slot_name`, it may additionally need enough slot information to distinguish rows belonging to different slots, for example `slot_name`. Whether `slot_declaring_template_id` remains a public wire field is OPEN: it is required internally for semantic identity but may not be necessary for an ordinary consumer.

## Abstract architectural reading

The concrete proposal corresponds to treating public Object GET as a complete first-level representation of the current Object instance rather than exposing only the fields colocated in the root persistence row.

The ownership graph remains non-recursive at this surface: direct composition is included, transitive graph expansion is not.

The specialized `/components` collection remains justified only as a navigation/query surface for filtering and pagination over large direct-child sets, not as a second semantic representation of ownership.

## Open decisions

- whether complete first-level components become mandatory in `ObjectDto`;
- whether every effective empty slot is included as `[]`;
- exact ordering of component-slot keys and children;
- whether `/components` remains in the public API after Object GET enrichment;
- if retained, exact `/components` item shape and whether `slot_declaring_template_id` is public;
- performance/size guardrails, if any, for Objects with very large direct child sets;
- whether Object mutation responses (`CREATE`, `RENAME`, `DATA_CHANGE`, `SCHEMA_CHANGE`) use the same enriched Object representation or retain a mutation-specific lighter shape;
- interaction with lifecycle snapshots, whose current historical `ObjectDto` shape contains only root Object fields.
