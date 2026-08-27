# M4 TO-BE API — Object GET

Status: ROUTE-LOCAL FREEZE / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the agreed TO-BE public contract for the single route `GET /api/v1/core/objects/{object_id}`. The route-level signature and success representation are frozen for the current M4 top-down sweep. This does not constitute the global M4 normative freeze and does not authorize implementation by itself.

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

## Route-local freeze

For the current M4 top-down sweep, the following are frozen for this route:

- HTTP method and path;
- absence of request body and query parameters;
- `200` success and common `404` missing-resource behavior;
- success JSON shape;
- structured exact ObjectTemplate reference `{id, version}`;
- complete canonical `properties`;
- complete effective direct `components` map;
- explicit empty slots;
- non-recursive child representation `{id, canonical_name}`;
- exclusion of owner and Relationships from the Object representation;
- deterministic child ordering with no semantic array-position meaning.

The next review steps for this same route are intentionally separate: touched data structures, AS-IS cost, TO-BE data path, denormalization coverage, concurrency guarantees, caching and relational-schema implications.
