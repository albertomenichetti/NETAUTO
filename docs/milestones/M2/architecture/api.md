# M2 Public API Architecture

**Status:** DRAFT — WIRE DESIGN COMPLETE — CROSS-OWNER/TRACEABILITY/CONSISTENCY CLOSURE PASSED — READY FOR FREEZE REVIEW

**Authority:** NORMATIVE M2 ARCHITECTURE DRAFT

## Authority and scope

This document owns the M2 TO-BE public HTTP architecture for:

```text
/api/v1/core business routes
/health/core operational route
request path, query and JSON body carriers
omission and explicit-null semantics
success status, Location and response projections
public failure classes, codes and bounded details
collection filters, ordering and opaque keyset cursors
lifecycle discriminated wire union
final public operation inventory consumed by the official CLI
```

Its implementation authority, once this document and the complete M2 architecture set are frozen, is:

```text
docs/architecture/api.md
    delivered public API AS-IS
+
docs/milestones/M2/contract.md
    FINAL / FROZEN obligations and explicit deltas
+
docs/milestones/M2/architecture/relationship.md
    normative Relationship domain semantics
+
this document
    normative M2 HTTP/wire realization
```

This document does not own:

```text
Relationship lifecycle, schema-evolution or factual semantics
    -> relationship.md

relational tables, codecs, indexes or Alembic DDL
    -> persistence.md

pairwise mutation interleavings
    -> concurrency-matrix.md

PostgreSQL locks, gates, retry and deadlock realization
    -> concurrency.md

Health application/check execution
    -> health.md

CLI grammar, selectors, transport client and presentation
    -> cli.md

verification scenarios and acceptance evidence
    -> verification.md
```

Those owners must realize the wire contract defined here without redefining it. Discovery material under `../wip/` is non-normative and is superseded by this document for the areas owned here.

---

## 1. Governing HTTP boundary

The public API remains an HTTP/JSON adapter over transport-neutral application commands, queries and failures.

```text
HTTP request
-> strict transport parsing
-> application command/query
-> semantic Unit of Work
-> domain and persistence
-> transport-neutral result/failure
-> canonical HTTP response
```

Writable DTOs are operation-specific command carriers. They are not generic writable entity snapshots.

Read DTOs are semantic projections. They are not persistence-row mirrors and never expose physical child rows as autonomous resources.

FastAPI, Pydantic and generated OpenAPI remain transport/composition mechanisms. Generated OpenAPI must accurately describe the frozen DTOs, but it is not a dynamic semantic authority and the official CLI does not derive its command model from it at runtime.

---

## 2. Namespaces and method policy

### 2.1 Business kernel API

The business namespace remains:

```text
/api/v1/core
```

Method policy remains:

```text
GET
    side-effect-free read or semantic projection

POST collection
    create one new aggregate or factual resource

POST .../{kebab-case-command}
    execute one explicit semantic mutation

DELETE exact resource route
    execute the corresponding exact delete primitive
```

M2 introduces no generic PUT, PATCH, action DSL, bulk mutation or multi-command transaction endpoint.

### 2.2 Operational Health API

The operational namespace is separate:

```text
/health
```

M2 introduces exactly:

```text
GET /health/core
```

There is no aggregate `GET /health` route in M2.

Health is a runtime-readiness surface, not a business resource and not a replacement for the startup Alembic revision guard.

### 2.3 Response envelopes

Single-resource, mutation and projection responses have no generic `data` envelope.

Paginated business collections use exactly:

```json
{
  "items": [],
  "next_cursor": null
}
```

Successful DELETE and other explicitly bodyless success responses use `204 No Content` with an empty body.

Health uses its own bounded readiness response and does not use the business failure envelope for a valid readiness outcome.

---

## 3. Strict caller-intent and common carriers

The delivered strict-intent rules remain authoritative.

```text
JSON keys
    snake_case

semantic command path segments
    kebab-case

unknown body fields
    rejected

unknown or repeated query parameters
    rejected

implicit resolution
    fills omission only

explicit null
    valid only when null is a declared field state

canonical response
    follows canonical domain state, not caller lexical form
```

No generic scalar coercion may reinterpret caller intent.

### 3.1 UUID

Public UUID carriers are textual UUID values. Non-string body carriers and malformed path/query/body UUIDs are invalid requests.

Canonical responses use the standard hyphenated textual UUID form.

### 3.2 Positive integers

Version, revision, position, target/source selectors and page limit use positive integers. Boolean is never accepted as integer.

Path and query positive integers use positive decimal lexical form:

```text
[1-9][0-9]*
```

Malformed, zero or negative values are `invalid_request`.

### 3.3 Closed vocabularies

The relevant M2 closed wire vocabularies are case-sensitive:

```text
VersionStatus
    DRAFT
    PUBLISHED
    DEPRECATED

ValueMode
    SCALAR
    LIST

DataChange operation
    SET
    REMOVE

Health status
    ok
    error
```

### 3.4 Primitive values

Relationship property values reuse the delivered PrimitiveType lexical and canonical response contract used by Object state, DataType constraints and ObjectTemplate migration defaults.

In particular:

```text
core.number
    input and response are canonical exact-decimal strings

core.datetime
    response is canonical UTC Z

core.byte_size
    response is exact integer bytes

JSON null
    never a runtime property value
```

JSON Schema is not a public schema or validation language.

### 3.5 No-body commands

Commands declared with no body reject any non-empty request body, including `{}`.

Query parameters are route-specific. Supplying an unlisted or repeated parameter is `invalid_request`.

---

## 4. Final public operation inventory

The final M2 business surface contains:

```text
41 mutation routes
22 read routes
63 total /api/v1/core operations
```

The operational surface adds one route:

```text
1 GET /health/core
```

The final public HTTP inventory therefore contains 64 operations.

### 4.1 Business mutation routes — 41

#### DataType — 10, unchanged

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

#### ObjectTemplate — 10, unchanged

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

#### Object and ownership — 7, unchanged

```text
POST   /api/v1/core/objects
POST   /api/v1/core/objects/{object_id}/rename
POST   /api/v1/core/objects/{object_id}/data-change
POST   /api/v1/core/objects/{object_id}/schema-change
POST   /api/v1/core/objects/{parent_object_id}/attach
POST   /api/v1/core/objects/{parent_object_id}/detach
DELETE /api/v1/core/objects/{object_id}
```

#### RelationshipDefinition and exact versions — 10

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

#### Factual Relationship — 4

```text
POST   /api/v1/core/relationships
POST   /api/v1/core/relationships/{relationship_id}/data-change
POST   /api/v1/core/relationships/{relationship_id}/schema-change
DELETE /api/v1/core/relationships/{relationship_id}
```

### 4.2 Business read routes — 22

#### DataType — 4, unchanged

```text
GET /api/v1/core/datatypes
GET /api/v1/core/datatypes/{datatype_id}
GET /api/v1/core/datatypes/{datatype_id}/versions
GET /api/v1/core/datatypes/{datatype_id}/versions/{version}
```

#### ObjectTemplate — 6

```text
GET /api/v1/core/object-templates
GET /api/v1/core/object-templates/{template_id}
GET /api/v1/core/object-templates/{template_id}/versions
GET /api/v1/core/object-templates/{template_id}/versions/{version}
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

The first five retain their delivered contract. Relationship-capability items are extended as defined below.

#### Object — 6

```text
GET /api/v1/core/objects
GET /api/v1/core/objects/{object_id}
GET /api/v1/core/objects/{object_id}/components
GET /api/v1/core/objects/{object_id}/owner
GET /api/v1/core/objects/{object_id}/relationships
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

Object-relative Relationship and lifecycle projections are extended as defined below. Other Object reads remain unchanged.

#### RelationshipDefinition — 4

```text
GET /api/v1/core/relationship-definitions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
```

#### Factual Relationship — 1

```text
GET /api/v1/core/relationships/{relationship_id}
```

#### Global lifecycle — 1

```text
GET /api/v1/core/lifecycle-events
```

### 4.3 Operational route — 1

```text
GET /health/core
```

This inventory is the canonical HTTP-operation input to `cli.md`. CLI grammar and command names remain owned by that document.

---

## 5. Preserved business API surface

Unless explicitly changed below, all delivered DataType, ObjectTemplate, Object, ownership, pagination, error and success contracts remain unchanged.

In particular M2 preserves:

```text
/api/v1/core namespace
strict request models
stable-lineage versus exact-version identity
expected_revision as query generation token
PrimitiveType lexical contract
operation-specific command endpoints
DataType and ObjectTemplate lifecycle/default behavior
Object CREATE, RENAME, DATA_CHANGE and SCHEMA_CHANGE behavior
ownership ATTACH/DETACH behavior
keyset pagination
finite error-code catalog
bounded details and no SQL/internal leakage
```

No M2 DTO change is authorization to alter an unrelated delivered field, status, omission rule or error mapping.

---

## 6. RelationshipDefinition wire contract

### 6.1 Stable and exact identities

Stable Definition path identity is:

```text
relationship_definition_id: UUID
```

Exact version path identity is:

```text
relationship_definition_id: UUID
version: positive integer
```

There is no API-only version UUID and no top-level `/relationship-definition-versions` collection.

### 6.2 Property declaration request

One declaration request contains exactly:

```text
name: string
position: positive integer
datatype_id: UUID
datatype_version: positive integer, optional but explicit null forbidden
value_mode: SCALAR | LIST
```

Rules:

```text
unknown fields
    invalid_request

name
    [a-z][a-z0-9_]*
    maximum length 64

request-array order
    non-semantic

position
    sole ordering authority

required / nullable / migration_default / default_value
    forbidden unknown fields
```

Omitted `datatype_version` means deliberate resolution through `DataType.default_version`; the selected exact version is materialized. Explicit null never means omission.

Duplicate names, duplicate positions and historical evolution violations are semantic candidate failures rather than alternate ordering or overwrite semantics.

### 6.3 RelationshipDefinition CREATE body

CREATE retains the delivered discriminated topology bodies and adds optional top-level `properties`.

#### Non-symmetric

```json
{
  "symmetric": false,
  "perspectives": [
    {"template_id": "<uuid>", "name": "hosts"},
    {"template_id": "<uuid>", "name": "hosted_by"}
  ],
  "properties": []
}
```

Exact rules:

```text
symmetric
    strict boolean false

perspectives
    exactly two items
    each item exactly template_id + name
    array order has no forward/reverse authority
```

#### Symmetric

```json
{
  "symmetric": true,
  "endpoint_template_ids": ["<uuid>", "<uuid>"],
  "name": "peers",
  "properties": []
}
```

Exact rules:

```text
symmetric
    strict boolean true

endpoint_template_ids
    exactly two UUID items
    order is non-semantic
```

For both variants:

```text
properties omitted
    -> []

properties = []
    -> exact empty v1 schema

properties = null
    -> invalid_request
```

Caller cannot supply:

```text
Definition ID
Resolution IDs
version
revision
status
default_version
```

### 6.4 RelationshipDefinition CREATE response

Success is:

```text
201 Created
Location: /api/v1/core/relationship-definitions/{relationship_definition_id}
```

Body:

```json
{
  "relationship_definition": {
    "id": "<uuid>",
    "symmetric": false,
    "default_version": null,
    "resolutions": [
      {
        "resolution_id": "<uuid>",
        "name": "hosts",
        "from_template_id": "<uuid>",
        "to_template_id": "<uuid>"
      }
    ]
  },
  "version": {
    "relationship_definition_id": "<uuid>",
    "version": 1,
    "revision": 1,
    "status": "DRAFT",
    "properties": []
  }
}
```

`Location` identifies the stable aggregate created by the collection operation. The exact v1 resource is available through its canonical nested version route.

### 6.5 Stable Definition DTO

The stable projection is exactly:

```text
id
symmetric
default_version: integer | null
resolutions[]
    resolution_id
    name
    from_template_id
    to_template_id
```

`resolutions[]` is deterministically ordered by `resolution_id ASC`. Versions are never inlined.

Definition list items use this same complete stable projection.

### 6.6 Rename

Rename retains the delivered bodies.

Non-symmetric body:

```json
{
  "resolutions": [
    {"resolution_id": "<uuid>", "name": "contains"},
    {"resolution_id": "<uuid>", "name": "contained_by"}
  ]
}
```

The array contains exactly two distinct Resolution IDs and covers the complete owned set.

Symmetric body:

```json
{"name": "peers"}
```

Rename returns `200` with the stable Definition DTO, including current `default_version`. It never accepts properties or version lifecycle fields.

### 6.7 Exact version commands

| Operation | Query | Body | Success |
|---|---|---|---|
| CREATE_NEXT | none | exactly `{source_version}` | `201` exact RDV + exact-version `Location` |
| REVISE | required `expected_revision` | exactly `{properties: [...]}` | `200` revised exact RDV |
| PUBLISH | required `expected_revision` | none | `200` PUBLISHED exact RDV |
| DEPRECATE | none | none | `200` DEPRECATED exact RDV |
| DELETE_DRAFT | required `expected_revision` | none | `204` |
| SET_DEFAULT | none | exactly `{version}` | `200` stable Definition DTO |
| CLEAR_DEFAULT | none | none | `200` stable Definition DTO |

CREATE_NEXT success sets:

```text
Location: /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
```

`source_version`, `version` and `expected_revision` are positive integers. Explicit null is invalid.

REVISE requires the `properties` member. Omission or null is invalid; `[]` is a complete empty replacement.

PUBLISH, DEPRECATE, CLEAR_DEFAULT and DELETE_DRAFT accept no body. PUBLISH and DELETE_DRAFT accept no query other than their required `expected_revision`. DEPRECATE has no `expected_revision`.

### 6.8 Exact version projections

Full exact version DTO:

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

`properties[]` is ordered by `position ASC`.

Version summary DTO:

```text
relationship_definition_id
version
revision
status
```

The summary never contains declarations.

### 6.9 Exact version reads

```text
GET /relationship-definitions/{id}/versions/{version}
    -> 200 full exact version DTO

GET /relationship-definitions/{id}/versions
    -> 200 paginated summary page
```

Version-list query:

```text
status: DRAFT | PUBLISHED | DEPRECATED, optional
cursor: opaque, optional
limit: 1..500, default 100
```

The path stable Definition must exist. An existing Definition with no matching versions returns an empty page; a missing path Definition returns `resource_not_found`.

### 6.10 Definition delete

Definition DELETE accepts no body or query and returns `204` only after a real admitted root deletion. Current factual Relationship references produce `delete_blocked`.

There is no force/cascade request option and no implicit factual Relationship deletion.

### 6.11 No standalone children

M2 introduces no autonomous public resource for:

```text
RelationshipResolution
RelationshipDefinition property declaration
RuntimeRelationshipResolution
```

Resolution and property declarations are complete aggregate/version members and are mutated only through their owning command.

---

## 7. Factual Relationship wire contract

### 7.1 CREATE body

CREATE accepts exactly:

```text
resolution_id: UUID
from_object_id: UUID
to_object_id: UUID
relationship_definition_version: positive integer, optional but null forbidden
properties: JSON object, optional but null forbidden
```

Canonical omission semantics:

```text
relationship_definition_version omitted
    -> resolve RelationshipDefinition.default_version

properties omitted
    -> {}
```

`relationship_definition_id` is not accepted because `resolution_id` already selects the stable Definition.

Self-loop is not rejected by transport shape. Endpoint and schema/property validity are semantic admission concerns.

CREATE success always means a new factual resource:

```text
201 Created
Location: /api/v1/core/relationships/{relationship_id}
```

An already-current semantic fact is never a success response in M2; it returns `relationship_fact_conflict`.

### 7.2 DATA_CHANGE body

```json
{
  "operations": [
    {"op": "SET", "property": "weight", "value": 10},
    {"op": "REMOVE", "property": "comment"}
  ]
}
```

Rules:

```text
operations
    required and non-empty

SET
    exactly op + property + value

REMOVE
    exactly op + property
    value forbidden

same property more than once
    invalid_request

operation-array order
    non-semantic

SET value = null
    syntactically carried but semantic_validation_failed
```

DATA_CHANGE accepts no `expected_revision`, schema selector or remediation payload.

Success is `200` with the current factual Relationship DTO. A semantic no-op returns the same canonical DTO and emits no event.

### 7.3 SCHEMA_CHANGE body

```json
{"target_version": 3}
```

The body contains exactly one positive `target_version`.

It accepts no target Definition ID, default/latest token, expected revision, property overrides or remediation values.

Success is `200` with the migrated factual Relationship DTO.

### 7.4 DELETE

DELETE accepts no body or query.

```text
current exact relationship_id
    -> 204 No Content

absent exact relationship_id
    -> 404 resource_not_found
```

No semantic endpoint tuple or force/cascade alternative exists.

### 7.5 Factual Relationship DTO

Relationship GET and mutation responses expose exactly:

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

`properties` appears once at fact level and is shared by every view.

`views[]` is the distinct semantic-view set, not raw runtime rows, and is deterministically ordered by:

```text
(object_id, destination_object_id, name) ASC
```

JSON object key order inside `properties` has no semantic meaning.

### 7.6 Object-relative Relationship item

Each item of:

```text
GET /api/v1/core/objects/{object_id}/relationships
```

exposes:

```text
relationship_id
relationship_definition_id
relationship_definition_version
object_id
destination_object_id
name
properties
```

The exact version and properties are factual state projected into each Object-relative item. They are not independently mutable view state.

The collection query remains:

```text
relationship_definition_id: UUID, optional
name: Relationship identifier, optional
cursor: opaque, optional
limit: 1..500, default 100
```

Ordering and cursor identity remain:

```text
(relationship_id, destination_object_id, name) ASC
```

`relationship_definition_version` and `properties` are intentionally excluded from cursor identity because they are mutable factual state, not item identity or order.

---

## 8. Relationship capability projection

The existing route remains:

```text
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

Query remains:

```text
name: Relationship identifier, optional
cursor: opaque, optional
limit: 1..500, default 100
```

Item DTO becomes:

```text
resolution_id
relationship_definition_id
name
from_template_id
to_template_id
default_version: integer | null
```

One item represents one applicable Resolution and appears at most once, irrespective of how many PUBLISHED versions the Definition owns.

The semantic membership predicate is owned by `relationship.md`:

```text
topologically applicable Resolution
AND
at least one PUBLISHED RelationshipDefinitionVersion
```

A null default does not suppress the item when another explicit PUBLISHED version exists.

The collection remains ordered by:

```text
resolution_id ASC
```

and filtered by exact `name`. Neither `default_version` nor version-set state enters cursor identity.

The item never inlines:

```text
version summaries
property declarations
published-version count
```

---

## 9. Relationship lifecycle wire union

The lifecycle routes remain:

```text
GET /api/v1/core/lifecycle-events
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

Existing intrinsic and ownership event DTOs remain unchanged.

### 9.1 Common Relationship event context

Every Relationship event contains:

```text
id
occurred_at
kind
object_id
canonical_name
destination_object_id
destination_canonical_name
relationship_id
relationship_definition_id
relationship_name
```

It does not expose:

```text
Resolution ID
source/target direction
raw runtime row identity
views[]
```

`occurred_at` remains canonical UTC `Z`. Public ordering remains `(occurred_at, id) DESC`; it is deterministic but not a global commit sequence.

### 9.2 Factual state DTO

Relationship factual state is exactly:

```text
relationship_definition_version
properties
```

It contains no live links or inlined schema declarations.

### 9.3 Created event

```text
kind = RELATIONSHIP_CREATED
before = null
after = RelationshipFactualState
```

### 9.4 Changed events

```text
kind = RELATIONSHIP_DATA_CHANGE | RELATIONSHIP_SCHEMA_CHANGE
before = RelationshipFactualState
after = RelationshipFactualState
```

For DATA_CHANGE, before and after version are equal and properties differ.

For SCHEMA_CHANGE, after version is greater than before version; properties may be equal.

### 9.5 Deleted event

```text
kind = RELATIONSHIP_DELETED
before = RelationshipFactualState
after = null
```

### 9.6 Lifecycle kind filter

The public `kind` query vocabulary becomes:

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
DELETED
ATTACH_TO
DETACH_FROM
RELATIONSHIP_CREATED
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
RELATIONSHIP_DELETED
```

All other lifecycle filters, route-specific involvement semantics, ordering and cursor rules remain unchanged.

### 9.7 Event fan-out is not visible as raw persistence

The API returns one row per distinct Object-relative semantic view produced by the domain transition. It never exposes or allows clients to infer that lifecycle cardinality must equal raw runtime-resolution row cardinality.

There is no standalone Relationship lifecycle route, transition resource or event-set grouping resource.

---

## 10. Core Health wire contract

### 10.1 Request

```text
GET /health/core
```

accepts no body and no query parameters.

A syntactically valid request always returns the Core Health response with status `200` or `503`.

An unknown/repeated query or non-empty body is caller-invalid rather than a readiness failure and returns `400 invalid_request` through the canonical bounded error body. It must not be represented as `db_status = error`.

### 10.2 Component status DTO

```text
status: ok | error
message: string, optional and omitted when absent
```

`message = null` is not emitted.

Messages are safe controlled diagnostics and never include raw exception text, credentials, database URLs, usernames, hosts, SQL or stack details.

### 10.3 Core Health DTO

```text
app_status: component status
db_status: component status
execution_time_ms: integer >= 0
```

Healthy example:

```json
{
  "app_status": {"status": "ok"},
  "db_status": {"status": "ok"},
  "execution_time_ms": 12
}
```

Unhealthy example:

```json
{
  "app_status": {"status": "ok"},
  "db_status": {
    "status": "error",
    "message": "connection to database failed"
  },
  "execution_time_ms": 27
}
```

### 10.4 Status semantics

```text
200 OK
    every required component status is ok

503 Service Unavailable
    at least one required component status is error
    complete Core Health DTO still returned
```

A valid readiness failure does not use:

```text
{code, message, details}
```

The PostgreSQL check has the dedicated two-second semantic timeout owned by `health.md`.

Health does not inspect Alembic revision state, execute migration or perform remediation.

### 10.5 Cache behavior

Every Core Health response, healthy or unhealthy, must include:

```text
Cache-Control: no-store
```

Runtime readiness must not be served from an intermediary cache.

---

## 11. Pagination, filtering and canonical order

The delivered collection contract remains:

```text
opaque keyset cursor only
limit omitted -> 100
limit range   -> 1..500
fixed route-specific order
no offset/page number
no generic sort/query DSL
no automatic total_count
```

A cursor is bound to:

```text
route identity
canonical ordering
active filters
stable path-scope identity when applicable
```

`limit` is not part of semantic query identity and may change between pages.

A cursor is not:

```text
domain identity
database offset
transaction snapshot
CDC token
cross-request consistency token
```

Each page is coherent for its own request. Cross-request repeatable membership is not promised.

### 11.1 Final route-specific ordering and filters

```text
DataType lineages
    order (namespace, name) ASC
    filters namespace, name

DataType versions
    order version ASC
    filter status

ObjectTemplate lineages
    order (namespace, name) ASC
    filters namespace, name, abstract, parent_template_id

ObjectTemplate versions
    order version ASC
    filter status

Relationship capabilities
    order resolution_id ASC
    filter name

Objects
    order id ASC
    filters template_id, dependent template_version, exact canonical_name

Object components
    order child_object_id ASC
    filter slot_name

Object relationships
    order (relationship_id, destination_object_id, name) ASC
    filters relationship_definition_id, name

RelationshipDefinitions
    order id ASC
    no domain filter

RelationshipDefinitionVersions
    order version ASC
    filter status

Lifecycle events
    order (occurred_at, id) DESC
    filters kind, object_id, destination_object_id,
            relationship_id, relationship_definition_id,
            relationship_name, occurred_from, occurred_to
```

The Object-specific lifecycle route means involvement:

```text
object_id = path Object
OR
destination_object_id = path Object
```

It does not accept a second `object_id` query parameter.

### 11.2 Cursor payload authorities

Conceptual keysets are:

```text
RelationshipDefinitions
    [id]

RelationshipDefinitionVersions
    [version]

Relationship capabilities
    [resolution_id]

Object relationships
    [relationship_id, destination_object_id, name]

Lifecycle events
    [occurred_at, id]
```

Cursor payload is opaque. These conceptual keys do not authorize clients to construct or decode cursor strings.

---

## 12. Success and Location mapping

### 12.1 Created resources

```text
RelationshipDefinition.CREATE
    201
    Location stable Definition route
    body {relationship_definition, version}

RelationshipDefinitionVersion.CREATE_NEXT
    201
    Location exact nested version route
    body exact RDV

Relationship.CREATE
    201
    Location exact Relationship route
    body factual Relationship
```

Existing DataType, ObjectTemplate and Object create mappings remain unchanged.

### 12.2 Normal mutations

```text
RelationshipDefinition.RENAME
SET_DEFAULT
CLEAR_DEFAULT
    -> 200 stable Definition

RDV.REVISE
RDV.PUBLISH
RDV.DEPRECATE
    -> 200 exact RDV

Relationship.DATA_CHANGE
Relationship.SCHEMA_CHANGE
    -> 200 factual Relationship
```

A DATA_CHANGE semantic no-op is still `200` with current canonical state.

### 12.3 Deletes

```text
RDV.DELETE_DRAFT
RelationshipDefinition.DELETE
Relationship.DELETE
    -> 204 on real successful deletion
```

Relationship DELETE on absent exact ID is `404`, not an idempotent `204`.

### 12.4 Forbidden generic success forms

The API does not return:

```text
{success: true}
{changed: false}
SQL affected-row counts
202 Accepted for synchronous kernel commands
```

---

## 13. Failure contract

### 13.1 Failure classes

The delivered classes remain unchanged:

```text
INVALID_REQUEST       -> 400
NOT_FOUND             -> 404
SEMANTIC_VALIDATION   -> 422
STATE_CONFLICT        -> 409
INTERNAL_FAILURE      -> 500
```

### 13.2 Canonical business error body

```json
{
  "code": "stale_revision",
  "message": "The draft revision does not match the expected revision.",
  "details": {}
}
```

`code` is stable and machine-readable. Clients must not branch on `message`.

`details` is always a bounded JSON object. SQL, table, column, constraint, driver, stack and secret details are forbidden.

### 13.3 Finite public code catalog

M2 reuses the delivered 23-code catalog without adding a code:

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

A supported known failure must not be hidden behind a generic conflict or internal error.

### 13.4 Boundary rules for M2 Relationship operations

| Condition | Public result |
|---|---|
| malformed path/query/body, forbidden null, unknown field/query, repeated query, duplicate DATA_CHANGE property operation | `400 invalid_request` |
| malformed/incompatible cursor | `400 invalid_cursor` |
| missing URI/path target Definition, exact RDV or factual Relationship | `404 resource_not_found` |
| missing command/body operand such as source version, referenced Object, Resolution, DataTypeVersion or schema-change target | `422 referenced_resource_not_found` |
| invalid topology, property candidate/value, lineage admission, evolution rule or non-forward target | `422 semantic_validation_failed` |
| stale DRAFT generation | `409 stale_revision` |
| lifecycle-ineligible exact version command | `409 lifecycle_state_conflict` |
| CREATE_NEXT source is not PUBLISHED/DEPRECATED | `409 version_source_conflict` |
| implicit selector has no default | `409 default_version_unavailable` |
| explicitly selected or final exact dependency/binding is not PUBLISHED | `409 dependency_not_admissible` |
| attempted deprecation of current default | `409 default_version_conflict` |
| active PUBLISHED model consumer blocks DTV deprecation | `409 active_dependency_conflict` |
| root delete has current external references | `409 delete_blocked` |
| Definition candidate duplicates an existing stable type | `409 relationship_definition_equivalent` |
| Definition candidate has a cross-Definition Resolution conflict | `409 relationship_definition_conflict` |
| requested semantic fact is already occupied | `409 relationship_fact_conflict` |
| current factual value cannot be preserved under target schema | `409 schema_change_blocked` |
| persisted invariant corruption or unexpected failure | `500 internal_error` |

A corrupt non-null default pointer, malformed persisted exact pin, incomplete closure or invalid persisted lifecycle row is `internal_error`; it is not a caller conflict and is never hidden by fallback.

### 13.5 Bounded detail shapes

Not-found and referenced-not-found details identify bounded selectors:

```text
resource_type
id
version, when exact version identity applies
```

`stale_revision` exposes:

```text
expected_revision
current_revision
```

`relationship_fact_conflict` exposes at least:

```text
relationship_id
```

identifying the current conflicting fact. It does not return the current fact as a successful CREATE body.

`schema_change_blocked` exposes one sufficient bounded blocker:

```text
relationship_id
target_version
blocker_type = property
member_name
```

`delete_blocked` exposes bounded blocker type/count entries and never an unbounded identity list.

`semantic_validation_failed` exposes bounded path/rule violations.

### 13.6 Health failures versus transport failures

A valid Health readiness failure returns `503` with the Core Health DTO, not a business error body.

A malformed Health request is a caller transport error and may use `400 invalid_request`; it is not represented as a false readiness component failure.

Unexpected failure before a valid bounded Health response can be produced is an internal transport failure and must not leak internal details.

---

## 14. Coherent projection and corruption boundary

Every single-resource read and every collection page is coherent for its request.

M2 public projections must not combine:

```text
Relationship pin from one committed state
properties from another committed state
runtime closure from another committed state
Definition default from another committed state
partial declaration sets
partial lifecycle fan-out rows interpreted as a complete aggregate response
```

A read may observe complete state before or after a concurrent commit, never an impossible hybrid.

When one represented aggregate is persistently corrupt:

```text
single-resource read
    -> 500 internal_error

collection page
    -> complete page fails with 500
    -> no partial items response
```

The API performs no silent repair, default/latest fallback, unknown-property removal or closure reconstruction.

---

## 15. Official CLI coverage boundary

This API inventory is the sole public-operation authority consumed by `cli.md`.

The CLI architecture must provide a complete mapping:

```text
each of the 63 /api/v1/core operations
    -> one corresponding remote CLI operation

GET /health/core
    -> interactive /connect and /status behavior
```

No redundant business-style Health command is required.

The API does not change resource identity, add lookup routes or weaken ambiguity rules solely for CLI convenience.

The CLI may compose additional read-only requests through existing public routes, but it never becomes an alternate API authority.

Same-release CLI/server compatibility is owned by the frozen contract and `runtime-deployment.md`; this API defines no version-negotiation endpoint.

---

## 16. Forbidden public surface

M2 introduces no autonomous resource or generic API for:

```text
RelationshipResolution CRUD
Relationship property-declaration CRUD
RuntimeRelationshipResolution CRUD
standalone Relationship lifecycle timeline
lifecycle event mutation
event-set/transition grouping
generic runtime property query
property-value search
JSON Schema projection
default/latest/highest selector token
generic version selector
factual endpoint mutation or reversal
Relationship move/reclassification
bulk or generic PATCH mutation
```

No public persistence row, database constraint name or implementation-specific lock token is exposed.

---

## 17. Explicit AS-IS wire deltas

M2 intentionally changes only the following delivered wire behavior:

```text
RelationshipDefinition.CREATE
    response becomes {relationship_definition, version}
    initial version is v1 DRAFT revision 1
    optional initial properties schema added

RelationshipDefinition stable DTO
    default_version added

RelationshipDefinitionVersion
    nested command/read routes and DTOs added

Relationship capability item
    default_version added
    item omitted when no PUBLISHED RDV exists

Relationship.CREATE body
    optional relationship_definition_version added
    optional properties added

Relationship.CREATE duplicate
    409 relationship_fact_conflict replaces successful convergence

Relationship DTOs
    relationship_definition_version and properties added

Relationship.DATA_CHANGE and SCHEMA_CHANGE
    routes and request/response DTOs added

Relationship.DELETE absent target
    404 replaces idempotent 204

Relationship lifecycle
    before/after factual state added to CREATED/DELETED
    DATA_CHANGE and SCHEMA_CHANGE kinds added

GET /health/core
    operational route added
```

All other delivered business wire behavior is preserved.

No additional observable divergence is authorized without contract reopening.

---

## 18. Contract traceability

This document is the primary wire-level architecture owner for:

```text
M2-OUT-04
    public factual Relationship mutations

M2-OUT-06
    complete coherent read projections

M2-OUT-07
    Relationship lifecycle public observability

M2-OUT-11
    Core Health HTTP contract, shared with health.md

M2-OUT-12
    canonical HTTP operation inventory consumed by cli.md
```

It provides wire authority required by:

```text
M2-AC-01 ... M2-AC-14
M2-AC-23
M2-AC-28
M2-AC-31
```

Shared owner boundaries are:

```text
Relationship semantic preconditions and outcomes
    -> relationship.md

state and history physical decoding
    -> persistence.md

interleaving result completeness
    -> concurrency-matrix.md and concurrency.md

Health operation execution
    -> health.md

CLI command and transport behavior
    -> cli.md

deterministic evidence
    -> verification.md
```

Final traceability must link every cited acceptance criterion across these owners without duplicating authority.

---

## 19. API consistency closure

```text
final route inventory                                  CLOSED
strict path/query/body carrier rules                   CLOSED
omission versus explicit null                         CLOSED
RelationshipDefinition CREATE/rename wire             CLOSED
RDV nested lifecycle/read wire                        CLOSED
factual CREATE/DATA_CHANGE/SCHEMA_CHANGE/DELETE wire  CLOSED
stable/exact/factual response projections             CLOSED
capability projection and pagination                  CLOSED
lifecycle discriminated union                         CLOSED
Health route/status/response wire                     CLOSED
success/Location mapping                              CLOSED
finite failure catalog and M2 boundary mapping        CLOSED
CLI operation-coverage boundary                       CLOSED
AS-IS wire delta register                             CLOSED
```

No open HTTP/wire decision remains inside this owner.

Cross-owner realization, operation coverage, traceability and consistency closure have passed.

This document remains `NOT FROZEN` only until the dedicated architecture-set freeze transition is explicitly approved and committed.
