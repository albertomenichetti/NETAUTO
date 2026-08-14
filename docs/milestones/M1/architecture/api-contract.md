# M1 — API Contract

**Status:** DRAFT — API-01 e API-02 ratificati; boundary, public namespace e canonical route inventory consolidati. DTO/wire shape e failure mapping vengono definiti nei successivi API point.

## 1. Scopo

Questo documento definisce la baseline API M1 come adapter pubblico del kernel consolidato.

Catena normativa:

```text
HTTP request / wire DTO
-> transport parsing + syntactic validation
-> application command/query
-> semantic Unit of Work
-> domain + persistence
-> application result / transport-neutral failure
-> HTTP response mapping
```

Il domain/application contract è autorevole. HTTP/JSON non introduce una seconda semantica CRUD del kernel.

---

## 2. API-01 — boundary e principi

### 2.1 Application contract prima del transport

Le semantic operation del kernel sono l'application API autorevole. FastAPI, Pydantic/OpenAPI e JSON sono adapter/boundary di trasporto e non appartengono al domain model.

Transport model e domain/application model possono avere shape differenti quando ciò rende esplicito l'intent della command o evita leakage della persistence representation.

### 2.2 Una mutation semantica, una command surface

Ogni primitive mutation M1 possiede una command surface distinta.

Non è ammesso un generic CRUD/PATCH che possa fondere nella stessa request due Unit of Work semanticamente separate, per esempio:

```text
Object.RENAME
Object.DATA_CHANGE
Object.SCHEMA_CHANGE
Object.ATTACH
Object.DETACH
Object.DELETE
```

Lo stesso principio vale per lifecycle/default/version mutation di DataType/ObjectTemplate e per RelationshipDefinition/Relationship.

### 2.3 Operation-specific command DTO

I writable input DTO sono command-specific, non writable entity snapshots.

Esempio concettuale:

```text
CreateObjectCommand
    template_id
    template_version?       # omission => implicit default resolution
    canonical_name?
    properties

RenameObjectCommand
    canonical_name

DataChangeObjectCommand
    operations[]

SchemaChangeObjectCommand
    target_version
```

Il transport non deve inferire un intent ambiguo confrontando un generic entity payload con lo state current.

### 2.4 Omission vs JSON null

Omission e JSON `null` sono semanticamente distinti.

Regola generale:

> JSON `null` non è un alias generico per omitted/default/clear/remove.

Quando il dominio definisce una command esplicita di clear, per esempio `CLEAR_DEFAULT`, si usa quella command. Quando omission abilita una specifica semantics, per esempio implicit exact-version default resolution, il field è omesso.

`null` può essere ammesso soltanto quando il field domain stesso è esplicitamente nullable, per esempio nullable non-semantic `description`; non acquisisce per questo generic clear semantics per altri field.

### 2.5 Read DTO come semantic projection

Le response/read DTO non sono mirror obbligatori delle persistence rows.

M1 distingue almeno:

```text
current resource state
aggregate read
semantic capability/projection read
lifecycle/history read
```

Esempi:

- Object GET espone l'intrinsic current canonical state, non ownership/runtime Relationship child rows raw;
- RelationshipDefinition GET espone header + complete Resolution aggregate;
- Object Relationship read espone `ObjectRelationshipView`, non raw `RuntimeRelationshipResolution` rows;
- lifecycle read espone historical event projection read-only.

### 2.6 Stable lineage identity vs exact version identity

Le API mantengono esplicita la distinzione fra stable lineage identity ed exact version identity.

Esempio lineage:

```text
id
namespace
name
default_version
```

Esempio exact version:

```text
template_id / datatype_id
version
revision
status
...
```

M1 non introduce un API-only surrogate `version_id`.

### 2.7 `expected_revision`

`expected_revision` è prima di tutto un application generation token delle exact DRAFT mutation che lo richiedono (`REVISE`, `PUBLISH`, `DELETE_DRAFT`).

Non viene reinterpretato come generic Object/resource revision. La concrete HTTP representation — body/query/header/ETag integration — viene decisa separatamente nel wire contract; il transport non cambia la semantica del token.

### 2.8 Idempotency/convergence

L'idempotenza API deriva dalla semantic operation:

```text
exact ATTACH already current        -> success/no-op
exact DETACH already absent         -> success/no-op
REL.CREATE existing factual view    -> converge on current Relationship
REL.DELETE absent exact id          -> success/no-op
DATA_CHANGE semantic no-op          -> success/no-op without lifecycle event
```

M1 non introduce un generic HTTP `Idempotency-Key` requirement. Request deduplication infrastructure è distinta dal domain idempotency contract.

### 2.9 Transport-neutral failure contract

Domain/application code non produce `HTTPException` o HTTP status come primary failure semantics.

Il flow è:

```text
domain/application failure
-> stable transport-neutral failure classification
-> HTTP status + error-body mapping
```

Il failure catalog e il mapping HTTP vengono ratificati in un API point dedicato.

### 2.10 Public transport baseline

La baseline pubblica M1 resta:

```text
HTTP/JSON
FastAPI transport adapter
OpenAPI exposure
```

FastAPI/Pydantic types restano confinati al transport/composition boundary. M1 non introduce un nuovo protocol stack perché nessuna invariant/capability del kernel lo richiede.

### 2.11 Public core namespace

La public API del kernel M1 è namespaced sotto:

```text
/api/v1/core
```

`core` è un API capability namespace pubblico, non un ulteriore domain/application layer o aggregate boundary. Future capability non-core possono usare sibling namespace sotto la stessa API version, per esempio `/api/v1/discovery/...`, senza modificare la semantic identity delle resource core.

La versione appartiene alla public API nel suo complesso; M1 non introduce versioning indipendente per capability namespace.

---

## 3. API-01 decisions

```text
A1.1  Application command/query contracts are authoritative; HTTP/JSON is an adapter.
A1.2  One semantic mutation primitive maps to one explicit command surface; no generic PATCH combining kernel UoWs.
A1.3  Command DTOs are operation-specific, not writable entity DTOs.
A1.4  Omitted and JSON null are distinct; null is not a generic default/clear/remove alias.
A1.5  Read DTOs are semantic projections and need not mirror persistence rows.
A1.6  Stable lineage and exact version identities remain explicit; no API-only surrogate version identity.
A1.7  expected_revision is an application generation token first; HTTP representation is a separate transport decision.
A1.8  Idempotency/convergence follows domain semantics; no generic Idempotency-Key requirement in M1.
A1.9  Failures are transport-neutral before HTTP mapping.
A1.10 M1 public transport baseline is HTTP/JSON via FastAPI/OpenAPI with framework types confined to the adapter.
A1.11 M1 public kernel namespace is /api/v1/core; core is API namespacing, not a new domain layer.
```

---

## 4. API-02 — canonical route inventory

### 4.1 Route convention

Canonical route grammar:

```text
/api/v1/core/resources
/api/v1/core/resources/{stable_id}
/api/v1/core/resources/{stable_id}/versions/{version}

POST   .../{kebab-case-command}
GET    ...
DELETE ...
```

M1 usa il verbo come ultimo path segment per semantic command. Non usa `:command`, non introduce `/actions/...`, non usa `PUT`/`PATCH` come generic mutation primitive.

Identity placement rule:

> il path identifica il target stable/exact della command; selector, target candidate e altri operand restano nel body.

### 4.2 DataType routes

Writes:

```text
DT.C     POST   /api/v1/core/datatypes
DT.CN    POST   /api/v1/core/datatypes/{datatype_id}/create-next
DT.R     POST   /api/v1/core/datatypes/{datatype_id}/versions/{version}/revise
DT.P     POST   /api/v1/core/datatypes/{datatype_id}/versions/{version}/publish
DT.SD    POST   /api/v1/core/datatypes/{datatype_id}/set-default
DT.CD    POST   /api/v1/core/datatypes/{datatype_id}/clear-default
DT.D     POST   /api/v1/core/datatypes/{datatype_id}/versions/{version}/deprecate
DT.DD    DELETE /api/v1/core/datatypes/{datatype_id}/versions/{version}
DT.DL    DELETE /api/v1/core/datatypes/{datatype_id}
DT.DESC  POST   /api/v1/core/datatypes/{datatype_id}/set-description
```

Reads:

```text
GET /api/v1/core/datatypes
GET /api/v1/core/datatypes/{datatype_id}
GET /api/v1/core/datatypes/{datatype_id}/versions
GET /api/v1/core/datatypes/{datatype_id}/versions/{version}
```

Qualified-name discovery resta collection filtering/query capability, non seconda identity route.

### 4.3 ObjectTemplate routes

Writes:

```text
OT.C     POST   /api/v1/core/object-templates
OT.CN    POST   /api/v1/core/object-templates/{template_id}/create-next
OT.R     POST   /api/v1/core/object-templates/{template_id}/versions/{version}/revise
OT.P     POST   /api/v1/core/object-templates/{template_id}/versions/{version}/publish
OT.SD    POST   /api/v1/core/object-templates/{template_id}/set-default
OT.CD    POST   /api/v1/core/object-templates/{template_id}/clear-default
OT.D     POST   /api/v1/core/object-templates/{template_id}/versions/{version}/deprecate
OT.DD    DELETE /api/v1/core/object-templates/{template_id}/versions/{version}
OT.DL    DELETE /api/v1/core/object-templates/{template_id}
OT.DESC  POST   /api/v1/core/object-templates/{template_id}/set-description
```

Reads:

```text
GET /api/v1/core/object-templates
GET /api/v1/core/object-templates/{template_id}
GET /api/v1/core/object-templates/{template_id}/versions
GET /api/v1/core/object-templates/{template_id}/versions/{version}
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

Exact-version GET espone l'aggregate version snapshot/local declarations; `effective-schema` è una projection derivata separata.

`relationship-capabilities` espone Resolution applicabili alla lineage come semantic capability projection, non come autonomous RelationshipResolution CRUD.

### 4.4 Object / ownership routes

Writes:

```text
OBJ.C    POST   /api/v1/core/objects
OBJ.RN   POST   /api/v1/core/objects/{object_id}/rename
OBJ.DC   POST   /api/v1/core/objects/{object_id}/data-change
OBJ.SC   POST   /api/v1/core/objects/{object_id}/schema-change
OBJ.A    POST   /api/v1/core/objects/{parent_object_id}/attach
OBJ.DET  POST   /api/v1/core/objects/{parent_object_id}/detach
OBJ.DEL  DELETE /api/v1/core/objects/{object_id}
```

Reads:

```text
GET /api/v1/core/objects
GET /api/v1/core/objects/{object_id}
GET /api/v1/core/objects/{object_id}/components
GET /api/v1/core/objects/{object_id}/owner
GET /api/v1/core/objects/{object_id}/relationships
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

`components` è outgoing ownership projection; `owner` è zero-or-one incoming ownership projection. `object_components` non è public CRUD resource.

Il parent nel path di ATTACH/DETACH rappresenta il semantic mutation target e il parent ownership concurrency domain. `child_object_id` e `slot_name` restano operand nel body. Non viene introdotta una PUT-to-owner semantics che suggerirebbe implicit MOVE.

### 4.5 RelationshipDefinition routes

Writes:

```text
RD.C    POST   /api/v1/core/relationship-definitions
RD.RN   POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/rename
RD.DEL  DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}
```

Reads:

```text
GET /api/v1/core/relationship-definitions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}
```

GET exact Definition espone header + complete Resolution set nello stesso aggregate snapshot.

Non esistono public mutation route autonome per RelationshipResolution.

### 4.6 Runtime Relationship routes

Writes:

```text
REL.C    POST   /api/v1/core/relationships
REL.DEL  DELETE /api/v1/core/relationships/{relationship_id}
```

`REL.CREATE` riceve nel body:

```text
resolution_id
from_object_id
to_object_id
```

La endpoint pair non è REST identity e non viene codificata nel path. La factual Relationship identity nasce dalla successful semantic CREATE/convergence.

Reads:

```text
GET /api/v1/core/relationships/{relationship_id}
```

La response è una semantic factual aggregate projection; non espone raw persistence runtime-resolution rows come public representation.

Object-relative navigation usa `/api/v1/core/objects/{object_id}/relationships` e deduplica in `ObjectRelationshipView`.

### 4.7 Lifecycle routes

Read-only:

```text
GET /api/v1/core/lifecycle-events
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

Non esistono lifecycle-event create/update/delete public route.

### 4.8 HTTP method policy

```text
GET
    side-effect-free read/projection

POST collection
    create a new aggregate/factual resource

POST command route
    execute exactly one explicit semantic mutation

DELETE exact resource route
    execute the corresponding domain delete primitive
```

M1 non usa `PUT` o `PATCH` nella canonical kernel mutation surface.

### 4.9 Negative API surface

Explicitly forbidden generic mutation routes:

```text
PATCH/PUT /api/v1/core/datatypes/{id}
PATCH/PUT /api/v1/core/object-templates/{id}
PATCH/PUT /api/v1/core/objects/{id}
PATCH/PUT /api/v1/core/relationship-definitions/{id}
PATCH/PUT /api/v1/core/relationships/{id}
```

Non esistono autonomous mutation route per:

```text
ObjectTemplateProperty
ObjectTemplateComponent
RelationshipResolution
RuntimeRelationshipResolution
ObjectLifecycleEvent
```

Non esistono primitive M1 route per capability fuori dominio, inclusi almeno:

```text
Object MOVE
Object cross-lineage RECLASSIFY
Relationship endpoint mutation/reverse
ObjectTemplate parent change
```

### 4.10 Mutation census traceability

La route inventory copre esattamente le 32 primitive mutation del semantic concurrency census:

```text
DataType                10
ObjectTemplate          10
Object / Ownership       7
RelationshipDefinition   3
Relationship              2
                        --
                         32
```

Ogni primitive M1 possiede esattamente una canonical public command route. Una futura primitive nuova deve essere aggiunta sia al semantic operation census sia alla public command inventory oppure dichiarata esplicitamente kernel-internal.

### 4.11 Command response principle

Una command restituisce semantic result/convergence, non SQL affected-row count.

Esempi:

```text
REL.CREATE existing fact
    -> current factual Relationship result

ATTACH exact existing edge
    -> semantic success/current ownership result

DATA_CHANGE equivalent candidate
    -> semantic success/no-op, no event
```

Exact HTTP status e response-body detail vengono definiti nei successivi success/failure/wire contract.

---

## 5. API-02 decisions

```text
A2.1  M1 public kernel API is namespaced under /api/v1/core.
A2.2  Canonical command style is POST /resource/{identity}/kebab-case-command; no colon syntax or /actions namespace.
A2.3  GET is for reads, POST for create/semantic commands, DELETE for actual domain delete primitives; PUT/PATCH absent from M1 baseline.
A2.4  Path parameters identify the stable/exact command target; selectors/candidates/other operands remain in the body.
A2.5  All 32 canonical M1 mutation primitives have exactly one public command route.
A2.6  DT/OT expose stable lineage + nested exact-version reads; OTV effective schema is a separate projection.
A2.7  Object exposes intrinsic, owner, components, relationships and lifecycle semantic projections; ownership rows are not CRUD resources.
A2.8  RelationshipDefinition GET returns complete aggregate; RelationshipResolution has no autonomous mutation API.
A2.9  Relationship CREATE is POST /api/v1/core/relationships with resolution_id/from_object_id/to_object_id body; endpoint pair is not REST identity.
A2.10 Object relationship navigation returns semantic ObjectRelationshipView, never raw runtime rows.
A2.11 Relationship capability discovery is GET /api/v1/core/object-templates/{template_id}/relationship-capabilities.
A2.12 Lifecycle API is read-only under /api/v1/core/lifecycle-events and Object lifecycle projection.
A2.13 Generic PATCH/PUT and autonomous owned-child CRUD are explicitly forbidden.
A2.14 Command responses represent semantic result/convergence, not persistence affected-row counts.
A2.15 expected_revision remains required by relevant exact-DRAFT commands; exact HTTP encoding is deferred to API-03.
A2.16 `core` is an API capability namespace only; it does not create a Core domain/service/repository abstraction.
```

---

## 6. Next point

API-03 definisce canonical command DTO / JSON wire shape, inclusi:

- UUID/version/revision scalar representation;
- omission/null/unknown-field rules;
- exact/implicit version selector representation;
- expected_revision encoding;
- DataType constraints and primitive values;
- OTV complete candidate property/component shape;
- Object properties and DATA_CHANGE operation union;
- RelationshipDefinition discriminated CREATE/RENAME inputs;
- Relationship CREATE selector/endpoints;
- response DTO identity/status conventions.
