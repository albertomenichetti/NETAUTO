# Public API — Current AS-IS

## Purpose and authority

The public kernel API is an HTTP/JSON adapter over the authoritative application command/query contract.

This document owns the public HTTP namespace, operation inventory, wire DTOs, success mapping, pagination and finite safe failure catalogue. Domain meaning, persistence and runtime deployment remain owned by their current architecture documents.

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

Writable DTOs are operation-specific command contracts, not writable entity snapshots. Read DTOs are semantic projections, not persistence-row mirrors.

## Namespace and method policy

Public kernel namespace:

```text
/api/v1/core
```

`core` is an API capability namespace, not a separate domain/service/repository abstraction.

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

The current kernel does not expose generic PUT/PATCH mutation, an `/actions` or colon-command DSL, or a request that combines semantic UoWs kept distinct by the domain.

## Strict caller-intent rules

- JSON keys are `snake_case`; semantic command path segments are `kebab-case`.
- Unknown command fields are rejected.
- Generic scalar coercion must not silently reinterpret caller intent.
- Caller-controlled IDs, version, revision, status or default state are exposed only when the owning command explicitly accepts them.
- Omission and explicit input are distinct semantic states.
- Defaults/implicit resolution fill **omission only** where the command explicitly defines it.
- Explicit invalid input is rejected and is never repaired or replaced by a default.
- JSON `null` is explicit caller intent and is valid only when null itself is a valid field state.
- Canonical responses follow canonical domain state, not the caller's lexical form.

Examples:

```text
Object CREATE canonical_name omitted
    -> canonical_name = str(Object.id)

canonical_name = null / "" / invalid
    -> invalid explicit input

Object CREATE template_version omitted
    -> resolve ObjectTemplate.default_version
    -> persist the selected exact version

template_version = null
    -> invalid explicit input
```

## Stable lineage vs exact version identity

Public contracts preserve the distinction between stable lineage and exact version identity.

```text
stable DataType/ObjectTemplate/RelationshipDefinition lineage
    id, namespace, name, default_version, ...

exact DataTypeVersion/ObjectTemplateVersion/RelationshipDefinitionVersion
    owning lineage id, version, revision, status, ...
```

No API-only surrogate version ID exists.

## Exact and implicit version selection

There is no generic `VersionSelector` and no public `default`, `latest` or `highest` token.

Stable lineage and exact version use type-specific sibling fields:

```text
template_id / template_version
parent_template_id / parent_version
datatype_id / datatype_version
```

Omitted version means implicit default resolution only in these cases:

```text
Object CREATE
    template_id present
    template_version omitted
    -> ObjectTemplate.default_version

ObjectTemplate CREATE
    parent_template_id omitted
    -> root; parent_version forbidden

    parent_template_id present + parent_version omitted
    -> parent ObjectTemplate.default_version

ObjectTemplate REVISE
    parent_template_id is not a body field

    non-root parent_version omitted
    -> intentional rebind through current parent default

    root parent_version present
    -> invalid

ObjectTemplate property declaration/revision
    datatype_version omitted
    -> intentional DataType.default_version binding/rebinding

Relationship CREATE
    relationship_definition_version omitted
    -> RelationshipDefinition.default_version

RelationshipDefinition property declaration/revision
    datatype_version omitted
    -> intentional DataType.default_version binding/rebinding
```

Preserving a previous exact property or parent pin requires supplying that exact version; omission does not mean "keep current".

Exact-only selectors:

```text
DataType CREATE_NEXT source_version
ObjectTemplate CREATE_NEXT source_version
DataType SET_DEFAULT version
ObjectTemplate SET_DEFAULT version
Object SCHEMA_CHANGE target_version
RelationshipDefinition CREATE_NEXT source_version
RelationshipDefinition SET_DEFAULT version
Relationship SCHEMA_CHANGE target_version
```

Every implicit resolution materializes the resulting exact pin.

## `expected_revision`

Exact DRAFT commands:

```text
REVISE
PUBLISH
DELETE_DRAFT
```

for DataTypeVersion, ObjectTemplateVersion and RelationshipDefinitionVersion require:

```text
?expected_revision=<positive-decimal-integer>
```

This is an application generation token, not resource identity or a generic HTTP resource revision. It is not represented through ETag, If-Match, a custom header or HTTP 412.

```text
missing / malformed / non-positive
    -> invalid_request / 400

well-formed but stale
    -> stale_revision / 409
```

REVISE bodies contain only the desired mutable candidate. PUBLISH and DELETE_DRAFT do not gain artificial bodies solely for the token.

## PrimitiveType public lexical contract

One parser/canonicalizer is reused across Object property values, Relationship
property values, DataType constraints and enum members, and ObjectTemplate
migration defaults.

- `core.string`: JSON string; no trim/lowercase normalization.
- `core.integer`: exact JSON integer; booleans rejected.
- `core.number`: **string-only exact decimal**; no exponent; canonical normalized decimal string.
- `core.boolean`: JSON boolean.
- `core.date`: ISO calendar-date string.
- `core.datetime`: offset/Z input representing an absolute instant; canonical UTC `Z`, at most microsecond precision.
- `core.ip`: canonical IPv4/IPv6 string.
- `core.ip_prefix`: canonical network/prefix string; host-bit-bearing non-canonical input is rejected, not repaired.
- `core.byte_size`: exact integer bytes or strict SI/IEC quantity string; canonical response is exact integer bytes.

SI and IEC byte-size units are distinct. Fractional input is valid only when it converts to an exact integer byte count.

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

### RelationshipDefinition — 10

```text
POST   /api/v1/core/relationship-definitions
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/rename
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/create-next
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/set-default
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/clear-default
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/revise
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/publish
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/deprecate
DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}
```

### Relationship — 4

```text
POST   /api/v1/core/relationships
POST   /api/v1/core/relationships/{relationship_id}/data-change
POST   /api/v1/core/relationships/{relationship_id}/schema-change
DELETE /api/v1/core/relationships/{relationship_id}
```

The current mutation inventory is exactly **41** routes.

## Command-specific wire rules

### DataType

CREATE establishes a stable lineage plus v1 DRAFT.

Required:

```text
namespace
name
base_type
```

Optional:

```text
description omitted -> null
description = null  -> valid
constraints omitted -> {}
constraints = {}    -> explicit zero constraints
constraints = null  -> invalid
```

Caller does not provide `id`, `version`, `revision`, `status` or `default_version`.

REVISE body contains the complete required `constraints` candidate. `{}` means zero constraints; omission does not mean keep-current.

CREATE_NEXT selects an exact eligible source and returns the new exact version.

### ObjectTemplate

CREATE requires explicit `namespace`, `name` and `abstract`; `abstract` has no omitted-to-false fallback.

```text
description omitted -> null
properties omitted  -> []
components omitted  -> []
```

Property declaration requires explicit:

```text
name
position
datatype_id
value_mode
required
```

`datatype_version` omission is the deliberate implicit DataType-default selector. Explicit null is invalid.

```text
required = false
    -> migration_default forbidden/absent

required = true + SCALAR
    -> exactly one valid migration_default

required = true + LIST
    -> non-empty ordered valid migration_default list
```

Component declaration is exactly:

```text
name
position
target_template_id
```

REVISE is complete replacement of local property/component candidates. Both arrays are required, including `[]`; request-array order is not an ordering authority because `position` is explicit state.

### Object

CREATE:

- omitted `properties` means zero caller-supplied properties;
- omitted `template_version` means intentional default resolution;
- omitted `canonical_name` means UUID-string fallback;
- explicit null/empty/invalid values fail.

DATA_CHANGE is a non-empty unordered set of per-property `SET` or `REMOVE` operations. At most one operation may target a property. Array order has no semantic mutation-order meaning.

SCHEMA_CHANGE accepts only exact `target_version` and has no value-remediation payload.

ATTACH/DETACH bodies are exactly `slot_name + child_object_id`. Object DELETE has no body, cascade or force option.

### RelationshipDefinition / Relationship

RelationshipDefinition CREATE/RENAME preserve complete certified symmetric/non-symmetric aggregate semantics without forward/reverse array-order meaning.

Definition CREATE accepts optional complete `properties` declarations and
returns the stable Definition plus exact version 1 DRAFT. CREATE_NEXT, REVISE,
PUBLISH, SET_DEFAULT, CLEAR_DEFAULT, DEPRECATE and DELETE_DRAFT use the same exact
version/default/generation carriers as the other versioned model resources.
REVISE requires a complete `properties` array, including `[]`.

Definition, Resolution and Relationship IDs are kernel-generated at creation.

Relationship CREATE body is exactly:

```text
resolution_id
from_object_id
to_object_id
relationship_definition_version, optional
properties, optional complete object
```

DATA_CHANGE requires a non-empty `operations` array of unique SET/REMOVE property
operations. SCHEMA_CHANGE requires one positive `target_version` and accepts no
remediation values. Self-loop is not structurally rejected at transport level.
Relationship DELETE is exact-ID based and has no cascade or semantic-tuple
alternative.

## Canonical read routes

Current business read/list surface contains exactly **22** routes.

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
GET /api/v1/core/objects/{parent_object_id}/components
GET /api/v1/core/objects/{child_object_id}/owner
GET /api/v1/core/objects/{object_id}/relationships
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

### RelationshipDefinition — 4

```text
GET /api/v1/core/relationship-definitions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
```

### Relationship — 1

```text
GET /api/v1/core/relationships/{relationship_id}
```

### Global lifecycle — 1

```text
GET /api/v1/core/lifecycle-events
```

## Public GET responsibility and coherence

Every one of the 22 public business GET/read routes owns:

```text
strict request carrier validation
strict cursor validation where applicable
path-target existence classification
composition of persisted facts required by the public projection
representational decoding required by the typed response
```

A GET does not re-run mutation-owned semantic certification merely because it is
reading persisted state. Default publication, aggregate mutation validation,
inheritance admission, runtime schema/DataType validation, ownership-slot
admission, Relationship topology/schema/default certification and historical
transition certification remain mutation responsibilities.

A representable persisted semantic surprise remains readable. A mandatory
carrier that cannot be decoded into its required public UUID, integer, string,
closed discriminant or recursive JSON form fails through the bounded
`500 internal_error` boundary. Reads do not repair state, invent defaults,
silently omit required members or return partial projections.

Each route obtains the complete business projection through exactly one
authoritative business SQL statement in an ordinary read Unit of Work. Its
response observes one PostgreSQL statement snapshot:

```text
writer commits before authoritative execute
    -> complete AFTER projection

writer commits after authoritative statement completes
    -> complete BEFORE projection
```

No response may mix incompatible generations from that statement result.
Separate requests/pages have no repeatable-membership guarantee and there is no
public snapshot token.

## Canonical read projections

Single-resource/projection responses have no generic `data` envelope.

Explicit null is used only for genuine nullable or zero-one state. Empty collections/maps use `[]` / `{}`.

### DataType

Stable lineage:

```text
id
namespace
name
description: string|null
default_version: integer|null
```

Exact version:

```text
datatype_id
version
revision
status
base_type
constraints: object
```

Lineage read does not inline versions. Zero constraints is `{}`.

### ObjectTemplate

Stable lineage:

```text
id
namespace
name
description: string|null
abstract
parent_template_id: UUID|null
default_version: integer|null
```

Exact version is the **local** snapshot, not effective schema:

```text
template_id
version
revision
status
parent_template_id: UUID|null
parent_version: integer|null
properties: []
components: []
```

Root exact version exposes both parent fields as null. Local declarations are ordered by `position`.

Local property projection:

```text
name
position
datatype_id
datatype_version
value_mode
required
migration_default  # omitted for optional property
```

Local component projection:

```text
name
position
target_template_id
```

Effective-schema projection is separate and every member includes `declaring_template_id`. Canonical ordering is ancestor/root declaration blocks through leaf, with each local block ordered by `position`.

Relationship capability item:

```text
resolution_id
relationship_definition_id
name
from_template_id
to_template_id
default_version: integer|null
```

`from_template_id` remains explicit because capability may be inherited from an ancestor compatibility space.

### Object and ownership

Object GET is intrinsic state only:

```text
id
canonical_name
template_id
template_version
properties
```

It does not embed owner, components, Relationships or lifecycle.

Component projection:

```text
slot_declaring_template_id
slot_name
child_object_id
```

Owner projection:

```text
parent_object_id
slot_declaring_template_id
slot_name
```

An existing detached Object returns:

```text
HTTP 200
body = null
```

Object-not-found remains distinct.

### RelationshipDefinition and factual Relationship

RelationshipDefinition GET returns the complete aggregate:

```text
id
symmetric
default_version: integer|null
resolutions[]
    resolution_id
    name
    from_template_id
    to_template_id
```

Exact RelationshipDefinitionVersion projection:

```text
relationship_definition_id
version
revision
status
properties[]
    name
    position
    datatype_id
    datatype_version
    value_mode
```

The stable Definition does not inline versions. Exact declarations are ordered by
position. Version lists are ordered by ascending version and may filter exact
status.

There is no standalone RelationshipResolution public resource.

Relationship GET returns:

```text
id
relationship_definition_id
relationship_definition_version
properties
views[]
    object_id
    destination_object_id
    name
```

`views` is the deduplicated semantic-view set, not raw runtime-resolution rows.

Object-relative Relationship item is self-contained:

```text
relationship_id
relationship_definition_id
relationship_definition_version
properties
object_id
destination_object_id
name
```

### Lifecycle event union

Lifecycle reads use a discriminated union by event kind/family, not one wide nullable persistence record.

Intrinsic kinds:

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
DELETED
```

include canonical Object `before`/`after` snapshots; `CREATED.before = null`, `DELETED.after = null`.

Ownership kinds:

```text
ATTACH_TO
DETACH_FROM
```

include subject/destination names and `slot_declaring_template_id + slot_name`, without meaningless before/after fields.

Relationship kinds:

```text
RELATIONSHIP_CREATED
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
RELATIONSHIP_DELETED
```

include object/destination identities and names plus `relationship_id`, `relationship_definition_id` and historical `relationship_name`; they do not expose source/target direction or Resolution IDs.

Their `before`/`after` members are factual states containing exactly
`relationship_definition_version + properties`. Mutation writes produce CREATED
with only `after`, DELETED with only `before`, DATA_CHANGE with equal versions and
different properties, and SCHEMA_CHANGE with a strictly increasing version.

Historical GETs select the discriminated family from the persisted event kind
and decode the mandatory response carriers, including required UUID/string/
integer fields and recursive `JsonValue` materialization. They do not replay
transition admissibility, changedness, version increase or agreement with
current live state. Representable historical semantic surprises remain readable;
materially undecodable mandatory carriers fail through the bounded internal
boundary.

`occurred_at` is canonical UTC `Z` datetime; ordering semantics remain `(occurred_at, id)` rather than strict global commit chronology.

## Collection, pagination and filters

All paginated collections return:

```json
{
  "items": [],
  "next_cursor": null
}
```

Contract:

```text
opaque keyset cursor only
limit omitted -> 100
limit range   -> 1..500
fixed route-specific ordering
no offset/page number
no generic sort/query DSL
no automatic total_count
```

A cursor is bound to the complete semantic query that produced it:

```text
query identity
    = route
    + every membership-affecting path target
    + every membership-affecting query filter
    + required semantic presence bits

position
    = complete canonical ordering tuple

limit
    = not semantic identity
```

It is not a domain identity, DB offset, transaction snapshot or CDC token. A
changed limit remains valid. Any incompatible route, path target, filter,
presence bit or position carrier returns `400 invalid_cursor`.

Each page is snapshot-consistent for its own request. Cross-request repeatable membership is not promised.

The exact cursor-bearing route census and canonical identities are:

| Public route | Codec route | Semantic identity filters | Complete position |
|---|---|---|---|
| `GET /api/v1/core/datatypes` | `datatypes` | `namespace`, `name` | `(namespace, name) ASC` |
| `GET /api/v1/core/datatypes/{datatype_id}/versions` | `datatype_versions` | `datatype_id`, `status` | `(version) ASC` |
| `GET /api/v1/core/object-templates` | `object_templates` | `namespace`, `name`, `abstract`, `parent_template_id`, internal `parent_filter_set` | `(namespace, name) ASC` |
| `GET /api/v1/core/object-templates/{template_id}/versions` | `object_template_versions` | `template_id`, `status` | `(version) ASC` |
| `GET /api/v1/core/object-templates/{template_id}/relationship-capabilities` | `relationship_capabilities` | `template_id`, `name` | `(resolution_id) ASC` |
| `GET /api/v1/core/objects` | `objects` | `template_id`, `template_version`, `canonical_name` | `(id) ASC` |
| `GET /api/v1/core/objects/{parent_object_id}/components` | `object_components` | `parent_object_id`, `slot_name` | `(child_object_id) ASC` |
| `GET /api/v1/core/objects/{object_id}/relationships` | `object_relationships` | `object_id`, `relationship_definition_id`, `name` | `(relationship_id, destination_object_id, name) ASC` |
| `GET /api/v1/core/objects/{object_id}/lifecycle-events` | `lifecycle_events` | lifecycle filters plus `involving_object_id=<path Object UUID>` | `(occurred_at, id) DESC` |
| `GET /api/v1/core/relationship-definitions` | `relationship_definitions` | none | `(id) ASC` |
| `GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions` | `relationship_definition_versions` | `definition_id`, `status` | `(version) ASC` |
| `GET /api/v1/core/lifecycle-events` | `lifecycle_events` | all lifecycle filters plus `involving_object_id=None` | `(occurred_at, id) DESC` |

The lifecycle filters are `kind`, `object_id`, `destination_object_id`,
`relationship_id`, `relationship_definition_id`, `relationship_name`,
`occurred_from` and `occurred_to`. The global and Object-scoped routes remain
cursor-distinct through `involving_object_id` even though they share one codec
route.

ObjectTemplate lineage filtering has the exact public tri-state:

```text
parent_template_id omitted
    -> no parent predicate

parent_template_id=<UUID>
    -> direct children of that stable parent

parent_template_id=null
    -> stable roots only
```

Only exact lowercase lexical `null` is the root sentinel. Empty, malformed,
uppercase/unsupported sentinel and repeated values are `400 invalid_request`.
Internally, omitted uses `parent_template_id=None, parent_filter_set=False`;
root-only uses `None, True`; exact parent uses `str(UUID), True`.
`parent_filter_set` is not public. These three states are mutually incompatible
cursor identities.

`template_version` without `template_id` is invalid because a version number is lineage-local.

`occurred_from`/`occurred_to` reuse the accepted datetime lexical contract.

The Object-specific lifecycle route means involvement:

```text
object_id = X OR destination_object_id = X
```

and does not accept a second `object_id` filter.

## Failure classes

```text
INVALID_REQUEST       -> 400
NOT_FOUND             -> 404
SEMANTIC_VALIDATION   -> 422
STATE_CONFLICT        -> 409
INTERNAL_FAILURE      -> 500
```

Boundary rules:

- 404 is reserved for missing request URI/path target identity.
- Missing command/body operands are semantic validation, normally `referenced_resource_not_found`/422.
- Malformed input decidable without mutable persisted-state interpretation is 400.
- A meaningful command blocked by mutable current state is 409.
- Domain-defined no-op is success only where the owning command explicitly says
  so. Duplicate Relationship CREATE and missing Relationship DELETE are failures.
- Unexpected invariant/integrity/server failure is 500 with no SQL/stack/constraint leakage.

## Canonical error body

```json
{
  "code": "stale_revision",
  "message": "...",
  "details": {}
}
```

`code` is stable machine-readable snake_case. Clients must not branch on `message`. `details` is always a bounded JSON object.

## Public error-code catalog

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

The current finite catalog contains exactly **23** codes. A known supported failure must not be hidden behind a generic conflict escape hatch.

## Bounded error details

`semantic_validation_failed` may expose:

```json
{
  "violations": [
    {"path": "properties.hostname", "rule": "required"}
  ]
}
```

`stale_revision` exposes:

```json
{
  "expected_revision": 7,
  "current_revision": 8
}
```

Not-found codes expose bounded semantic selector fields such as `resource_type`, `id` and optional `version`.

`delete_blocked` exposes bounded blocker type/count information, never an unbounded identity list:

```json
{
  "resource_type": "object",
  "id": "<uuid>",
  "blockers": [
    {"type": "ownership", "count": 1},
    {"type": "relationship", "count": 3}
  ]
}
```

`schema_change_blocked` exposes one sufficient semantic blocker diagnostic, for example object/target, blocker type, member name and optional child identity.

`relationship_fact_conflict` exposes the bounded current `relationship_id`.

All other details remain code-specific, bounded and transport-semantic. SQL, table/column, constraint and stack details are forbidden.

## Success mapping

Successful GET/read/list returns `200` with the canonical projection.

New public resources return `201 Created`, `Location` and the command-specific result:

- DataType CREATE: lineage + created v1 DRAFT;
- ObjectTemplate CREATE: lineage + created v1 DRAFT;
- CREATE_NEXT: created exact version;
- Object CREATE: Object DTO;
- RelationshipDefinition CREATE: stable aggregate + created v1 DRAFT;
- RelationshipDefinition CREATE_NEXT: created exact version;
- Relationship CREATE: factual Relationship DTO.

Normal semantic mutations return `200` with the resulting canonical projection when they have a body.

```text
Relationship CREATE occupied semantic fact
    -> 409 relationship_fact_conflict

ATTACH real or already-current exact edge
    -> 200 + current component projection

DETACH real or already-absent exact edge
    -> 204

successful delete
    -> 204

Relationship DELETE already-absent exact id
    -> 404 resource_not_found
```

The API does not return generic `{success:true}`, `{changed:false}`, SQL affected-row counts or `202 Accepted` for synchronous kernel commands.

## Forbidden public surface

No autonomous mutation resource exists for:

```text
ObjectTemplateProperty
ObjectTemplateComponent
RelationshipResolution
RuntimeRelationshipResolution
ObjectLifecycleEvent
RelationshipDefinitionProperty
```

The current API also excludes implicit Object MOVE, cross-lineage Object
reclassification, Relationship endpoint mutation/reversal, ObjectTemplate parent
change, property-value search, event-set resources, default/latest/highest selector
tokens, JSON Schema compilation/projection and generic CRUD bypasses of semantic
commands.

## Core Health operation

The sole operational route is:

```text
GET /health/core
```

It is separate from `/api/v1/core`, is not one of the 63 business operations and
accepts no query parameter or body. A valid response always uses the exact shape:

```json
{
  "app_status": {"status": "ok"},
  "db_status": {"status": "ok"},
  "execution_time_ms": 1
}
```

Each component status is `ok` or `error`; `message` is omitted when absent.
Ready returns `200`, PostgreSQL not-ready returns `503` with the complete same
DTO, and both carry `Cache-Control: no-store`. Malformed Health input is
`400 invalid_request`; an unexpected defect is a safe canonical `500`, not a
false readiness result. Probe and runtime semantics are owned by
[`health.md`](health.md).

## Exact surface census

```text
/api/v1/core mutations       41
/api/v1/core reads           22
business operations          63
/health/core operations       1
total public HTTP operations 64
```
