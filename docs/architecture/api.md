# Public API — Current AS-IS

## Boundary

The public kernel API is an HTTP/JSON adapter over the authoritative application command/query contract.

Normative flow:

```text
HTTP request / wire DTO
-> transport parsing + syntactic validation
-> application command/query
-> semantic Unit of Work
-> domain + persistence
-> application result / transport-neutral failure
-> HTTP response mapping
```

FastAPI, Pydantic and OpenAPI are transport/composition concerns. Domain/application code does not use HTTP exceptions or status codes as primary semantic failures.

## Namespace and method policy

Public kernel namespace:

```text
/api/v1/core
```

`core` is an API capability namespace, not a separate domain/service/repository abstraction.

Method policy:

```text
GET
    -> side-effect-free read/projection

POST collection
    -> create a new aggregate/factual resource

POST .../{kebab-case-command}
    -> execute exactly one semantic mutation

DELETE exact resource route
    -> execute the corresponding domain delete primitive
```

The current kernel does not use generic PUT/PATCH mutation or an `/actions`/colon-command DSL.

One semantic mutation primitive maps to one explicit command surface. A public request must not combine semantic UoWs that the domain keeps distinct.

## Command DTO principles

Writable DTOs are operation-specific command contracts rather than writable entity snapshots.

Rules:

- unknown fields are rejected;
- transport coercion must not silently reinterpret caller intent;
- caller-controlled IDs/version/revision/status/default state are exposed only when the owning command explicitly accepts them;
- omission and explicit input are different semantic states;
- default/implicit resolution may fill **omission only** when the command explicitly defines that behavior;
- an explicit invalid value is rejected and never replaced by a default;
- JSON `null` is explicit caller intent and is valid only when null itself is a valid field state.

Examples:

```text
Object CREATE canonical_name omitted
    -> UUID-string fallback

canonical_name = null
    -> invalid explicit input

Object CREATE template_version omitted
    -> resolve current ObjectTemplate default
    -> persist exact selected version

template_version = null
    -> invalid explicit input
```

## Stable lineage vs exact version identity

Public contracts preserve the difference between stable lineage and exact version identity.

DataType/ObjectTemplate lineage:

```text
id
namespace
name
default_version
...
```

Exact version:

```text
datatype_id / template_id
version
revision
status
...
```

No API-only surrogate version ID exists.

## `expected_revision`

Exact DRAFT commands:

```text
REVISE
PUBLISH
DELETE_DRAFT
```

for DataTypeVersion and ObjectTemplateVersion require:

```text
?expected_revision=<positive-integer>
```

as a required query parameter.

This is an application generation token, not a generic HTTP resource revision. The current API does not reinterpret it through ETag/If-Match or HTTP 412 semantics.

Malformed/missing required `expected_revision` is request invalidity; a well-formed stale value is a state conflict.

## PrimitiveType public lexical contract

One parser/canonicalizer is reused across Object values, DataType constraints/enums and ObjectTemplate migration defaults.

Current public/value semantics include:

- `core.string`: JSON string, no trim/lowercase normalization;
- `core.integer`: exact JSON integer, booleans rejected;
- `core.number`: **string-only exact decimal**, no exponent notation, canonical response/persistence as normalized exact-decimal string;
- `core.boolean`: JSON boolean;
- `core.date`: ISO calendar-date string;
- `core.datetime`: offset/Z input representing an absolute instant, canonical response UTC `Z` with at most microsecond precision;
- `core.ip`: canonical IPv4/IPv6 string;
- `core.ip_prefix`: canonical network/prefix string; host-bit-bearing non-canonical input is rejected rather than corrected;
- `core.byte_size`: exact integer bytes or strict SI/IEC quantity string input; canonical response/persistence is exact integer bytes.

For byte size, SI and IEC units are semantically distinct and a fractional quantity is valid only when it converts to an exact integer number of bytes.

JSON Schema is not a public validation language or schema projection.

## Canonical mutation routes

### DataType — 10

```text
POST   /api/v1/core/datatypes
POST   /api/v1/core/datatypes/{datatype_id}/create-next
POST   /api/v1/core/datatypes/{datatype_id}/versions/{version}/revise
POST   /api/v1/core/datatypes/{datatype_id}/versions/{version}/publish
POST   /api/v1/core/datatypes/{datatype_id}/set-default
POST   /api/v1/core/datatypes/{datatype_id}/clear-default
POST   /api/v1/core/datatypes/{datatype_id}/versions/{version}/deprecate
DELETE /api/v1/core/datatypes/{datatype_id}/versions/{version}
DELETE /api/v1/core/datatypes/{datatype_id}
POST   /api/v1/core/datatypes/{datatype_id}/set-description
```

### ObjectTemplate — 10

```text
POST   /api/v1/core/object-templates
POST   /api/v1/core/object-templates/{template_id}/create-next
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/revise
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/publish
POST   /api/v1/core/object-templates/{template_id}/set-default
POST   /api/v1/core/object-templates/{template_id}/clear-default
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/deprecate
DELETE /api/v1/core/object-templates/{template_id}/versions/{version}
DELETE /api/v1/core/object-templates/{template_id}
POST   /api/v1/core/object-templates/{template_id}/set-description
```

### Object / ownership — 7

```text
POST   /api/v1/core/objects
POST   /api/v1/core/objects/{object_id}/rename
POST   /api/v1/core/objects/{object_id}/data-change
POST   /api/v1/core/objects/{object_id}/schema-change
POST   /api/v1/core/objects/{parent_object_id}/attach
POST   /api/v1/core/objects/{parent_object_id}/detach
DELETE /api/v1/core/objects/{object_id}
```

### RelationshipDefinition — 3

```text
POST   /api/v1/core/relationship-definitions
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/rename
DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}
```

### Relationship — 2

```text
POST   /api/v1/core/relationships
DELETE /api/v1/core/relationships/{relationship_id}
```

The mutation inventory therefore contains exactly 32 current kernel mutation routes.

## Command-specific wire rules

### DataType

CREATE establishes a stable lineage plus v1 DRAFT. Optional constraints default to `{}` only when omitted.

REVISE supplies the complete new constraint candidate for the exact DRAFT.

CREATE_NEXT selects an exact eligible source and returns the created exact version.

### ObjectTemplate

CREATE requires explicit `namespace`, `name` and `abstract`. `abstract` has no omitted-to-false fallback.

Omitted local properties/components on CREATE mean empty declaration collections.

Property declaration requires explicit semantic state such as name, position, DataType lineage, value mode and required flag. Omission of DataType version is the deliberate implicit-default selector; explicit null is not.

REVISE supplies complete local property/component candidate arrays, including `[]` for an empty local set. Array order does not replace explicit `position` as ordering authority.

### Object

CREATE:

- omitted `properties` means no caller-supplied properties;
- omitted template version means intentional default resolution;
- omitted canonical name uses UUID-string fallback.

DATA_CHANGE is a non-empty unordered set of per-property `SET` or `REMOVE` operations with no duplicate property operation.

SCHEMA_CHANGE accepts only an exact target version; it has no value-remediation payload.

ATTACH/DETACH use `slot_name + child_object_id` operands. DELETE exposes no cascade/force option.

### RelationshipDefinition / Relationship

RelationshipDefinition CREATE/RENAME bodies preserve certified symmetric/non-symmetric aggregate semantics without introducing forward/reverse array ordering.

Definition, Resolution and Relationship IDs are kernel-generated at creation.

Relationship CREATE body is exactly:

```text
resolution_id
from_object_id
to_object_id
```

Self-loop is not rejected structurally at transport level. Relationship DELETE is exact-ID based and has no cascade or semantic-tuple alternative.

## Canonical read routes

Current read/list surface contains 20 routes.

### DataType — 4

```text
GET /api/v1/core/datatypes
GET /api/v1/core/datatypes/{datatype_id}
GET /api/v1/core/datatypes/{datatype_id}/versions
GET /api/v1/core/datatypes/{datatype_id}/versions/{version}
```

### ObjectTemplate — 6

```text
GET /api/v1/core/object-templates
GET /api/v1/core/object-templates/{template_id}
GET /api/v1/core/object-templates/{template_id}/versions
GET /api/v1/core/object-templates/{template_id}/versions/{version}
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

### Object — 6

```text
GET /api/v1/core/objects
GET /api/v1/core/objects/{object_id}
GET /api/v1/core/objects/{object_id}/components
GET /api/v1/core/objects/{object_id}/owner
GET /api/v1/core/objects/{object_id}/relationships
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

### RelationshipDefinition — 2

```text
GET /api/v1/core/relationship-definitions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}
```

### Relationship — 1

```text
GET /api/v1/core/relationships/{relationship_id}
```

### Global lifecycle — 1

```text
GET /api/v1/core/lifecycle-events
```

## Read projections

Read DTOs are semantic projections and need not mirror persistence rows.

Key distinctions:

- DataType/ObjectTemplate stable lineage reads are distinct from exact-version reads;
- ObjectTemplate exact version exposes local snapshot state, while effective schema is a separate derived projection;
- Object GET is intrinsic state only;
- Object ownership reads expose semantic slot keys/projections, not `object_components` rows;
- RelationshipDefinition GET returns the complete Definition/Resolution aggregate;
- Relationship GET returns the factual aggregate and semantic views, not raw runtime-resolution rows;
- lifecycle reads expose a discriminated historical event-family union.

Existing detached Object owner read returns:

```text
HTTP 200
JSON null
```

## Collection and pagination contract

All paginated collections use:

```json
{
  "items": [],
  "next_cursor": null
}
```

with:

```text
opaque keyset cursor only
limit default = 100
limit max = 500
fixed route-specific ordering
no offset/page number
generic sort/query DSL absent
```

Each page is snapshot-consistent for its own request. The cursor is not a cross-request snapshot, CDC or repeatable-membership token.

Current important route order/filter contracts include:

```text
DataType lineages
    -> (namespace, name) ASC
    -> exact namespace/name filters

nested DataType versions
    -> version ASC
    -> status filter

ObjectTemplate lineages
    -> (namespace, name) ASC
    -> namespace/name/abstract/parent_template_id filters

nested ObjectTemplate versions
    -> version ASC
    -> status filter

relationship capabilities
    -> resolution_id ASC
    -> exact name filter

Objects
    -> id ASC
    -> template_id, dependent template_version, exact canonical_name filters

Object components
    -> child_object_id ASC
    -> exact slot_name filter

Object relationships
    -> (relationship_id, destination_object_id, name) ASC
    -> relationship_definition_id/name filters

RelationshipDefinitions
    -> id ASC

lifecycle events
    -> (occurred_at, id) DESC
    -> route-defined exact filters including kind, relationship ids and historical relationship_name
```

The Object-specific lifecycle route means events in which the Object is either primary or destination subject:

```text
object_id = X OR destination_object_id = X
```

## Failure classes

Transport-neutral failure classes map to HTTP as:

```text
INVALID_REQUEST       -> 400
NOT_FOUND             -> 404
SEMANTIC_VALIDATION   -> 422
STATE_CONFLICT        -> 409
INTERNAL_FAILURE      -> 500
```

Boundary rules:

- 404 is reserved for the request URI/path target identity being absent;
- absent referenced body/command operands map to semantic validation;
- malformed input that does not require persisted-state interpretation maps to 400;
- meaningful commands blocked by mutable current state map to 409;
- idempotent no-op/convergence remains success;
- unexpected invariant/integrity/server failure maps to 500 without exposing SQL/stack/constraint internals.

## Canonical error body

```json
{
  "code": "stale_revision",
  "message": "...",
  "details": {}
}
```

`code` is stable machine-readable snake_case; clients must not branch on message text. `details` is always a bounded JSON object and must not leak raw persistence structure.

## Public error-code catalog

The current finite catalog is:

| HTTP | Code |
|---:|---|
| 400 | `invalid_request` |
| 400 | `invalid_cursor` |
| 404 | `resource_not_found` |
| 422 | `referenced_resource_not_found` |
| 422 | `semantic_validation_failed` |
| 409 | `stale_revision` |
| 409 | `lifecycle_state_conflict` |
| 409 | `version_source_conflict` |
| 409 | `default_version_unavailable` |
| 409 | `dependency_not_admissible` |
| 409 | `qualified_name_conflict` |
| 409 | `default_version_conflict` |
| 409 | `active_dependency_conflict` |
| 409 | `delete_blocked` |
| 409 | `ownership_slot_unavailable` |
| 409 | `ownership_conflict` |
| 409 | `ownership_mismatch` |
| 409 | `ownership_cycle` |
| 409 | `schema_change_blocked` |
| 409 | `relationship_definition_equivalent` |
| 409 | `relationship_definition_conflict` |
| 409 | `relationship_fact_conflict` |
| 500 | `internal_error` |

A known supported failure must not be hidden behind a generic public `conflict` escape hatch. A new supported semantic failure that cannot be represented correctly is an architecture/API finding.

## Success mapping

Successful GET/read/list operations return `200` with the canonical projection.

Newly created public resources return `201 Created` plus `Location` and the command-specific/canonical result:

- DataType CREATE: lineage + created v1 DRAFT;
- ObjectTemplate CREATE: lineage + created v1 DRAFT;
- CREATE_NEXT: created exact version;
- Object CREATE: Object DTO;
- RelationshipDefinition CREATE: complete aggregate;
- Relationship CREATE new factual fact: factual Relationship DTO.

Normal semantic mutations return `200` with the resulting canonical resource/projection when they have a response body.

Special current rules:

```text
Relationship CREATE existing semantic fact
    -> 200 + current factual Relationship

ATTACH real/already-current exact edge
    -> 200 + current component projection

DETACH real/already-absent exact edge
    -> 204

successful delete primitive
    -> 204

Relationship DELETE already-absent exact id
    -> 204
```

The API does not return generic `{success:true}`, `{changed:false}`, SQL affected-row counts or `202 Accepted` for synchronous kernel primitives.

## Forbidden public surface

The current API does not expose autonomous mutation resources for:

```text
ObjectTemplateProperty
ObjectTemplateComponent
RelationshipResolution
RuntimeRelationshipResolution
ObjectLifecycleEvent
```

It also does not expose current primitives for implicit Object MOVE, cross-lineage reclassification, Relationship endpoint mutation/reverse, ObjectTemplate parent change, JSON Schema compilation/projection or generic CRUD bypasses of semantic commands.
