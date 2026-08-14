# M1 — API Contract

**Status:** DRAFT — API-01/02 and API-03.1..11B are ratified. Public boundary, routes, command/read/list DTOs, PrimitiveType wire forms and complete success/error HTTP mapping are consolidated.

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

Companion API-03 authority:

```text
api-wire-contract.md
    -> command/wire + PrimitiveType contract + API-03 registry

api-read-contract.md
    -> API-03.9 canonical single/projection DTO

api-list-contract.md
    -> API-03.10 collection envelope, keyset pagination,
       canonical ordering, list-item policy and filters

api-error-contract.md
    -> API-03.11 failure classes, concrete public error catalog,
       bounded details and success HTTP mapping
```

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

### 2.4 Omission, explicit intent e JSON null

Omission e input esplicito sono semanticamente distinti.

Regola generale M1:

> un default o una implicit resolution può colmare esclusivamente **assenza di intent** quando la specifica command assegna una semantica all'omissione. Non corregge, sostituisce o maschera mai un valore esplicito invalido.

Quindi:

```text
field omitted
    -> può attivare una command-specific default/implicit semantics
       soltanto se esplicitamente definita

field explicitly supplied with valid value
    -> il valore esprime caller intent e viene usato secondo il contract

field explicitly supplied with invalid value
    -> command failure
    -> mai fallback/default automatico
```

JSON `null` è un input esplicito. Non è un alias generico per omitted/default/clear/remove.

`null` è valido soltanto quando **null stesso** è uno state/value semanticamente ammesso per quel field, per esempio nullable non-semantic `description`. Quando omission abilita implicit exact-version resolution, il field deve essere realmente omesso: `null` non equivale a omission.

Esempi:

```text
Object CREATE canonical_name omitted
    -> UUID-string fallback definito dalla command

Object CREATE canonical_name = null
    -> invalid explicit intent

Object CREATE template_version omitted
    -> implicit ObjectTemplate default resolution

Object CREATE template_version = null
    -> invalid explicit input

SET_DESCRIPTION description = null
    -> valid nullable state, non fallback
```

Un eventuale `None` usato internamente dal codice per rappresentare tecnicamente "field not supplied" non modifica questa public/application semantics.

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

API-03.9 definisce le canonical single/projection DTO. API-03.10 definisce collection envelope, keyset cursor, canonical ordering, list summaries e route-specific filters. Nessun generic resource DTO viene reintrodotto dalle list surface.

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

`expected_revision` è l'application generation token delle exact DRAFT mutation che lo richiedono:

```text
REVISE
PUBLISH
DELETE_DRAFT
```

per DataTypeVersion e ObjectTemplateVersion.

Non è una generic Object/resource revision e non si applica alle altre mutation M1.

La public HTTP representation è ratificata da API-03.2 in `api-wire-contract.md`:

```text
required query parameter
?expected_revision=<positive-integer>
```

uniformemente per REVISE, PUBLISH e DELETE_DRAFT. M1 non usa ETag/If-Match o custom revision header per questo generation contract.

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

Il flow resta:

```text
domain/application failure
-> stable transport-neutral failure class + concrete code/details
-> HTTP adapter
-> HTTP status + canonical error body
```

API-03.11 in `api-error-contract.md` congela:

```text
INVALID_REQUEST       -> 400
NOT_FOUND             -> 404
SEMANTIC_VALIDATION   -> 422
STATE_CONFLICT        -> 409
INTERNAL_FAILURE      -> 500
```

Boundary importanti:

```text
404
    -> missing URI/path target identity only

missing referenced body/command operand
    -> 422 referenced_resource_not_found

malformed expected_revision
    -> 400

well-formed stale expected_revision
    -> 409 stale_revision

idempotent domain no-op/convergence
    -> success, never conflict solely because zero rows changed
```

Il canonical public error body è flat `{code,message,details}`. Il code catalog M1 è finito e semanticamente stabile; known lifecycle/default/dependency/ownership/schema-change/Relationship conflicts possiedono code dedicati. `internal_error` è l'unico public 500 code e non espone SQL/stack/constraint internals.

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
A1.4  Omission and explicit caller intent are distinct: defaults/implicit resolution may fill omission only; explicit invalid input fails and is never replaced by a default. JSON null is valid only when null itself is a valid semantic field state.
A1.5  Read DTOs are semantic projections and need not mirror persistence rows.
A1.6  Stable lineage and exact version identities remain explicit; no API-only surrogate version identity.
A1.7  expected_revision is an exact-DRAFT application generation token; API-03.2 maps it uniformly to a required positive-integer query parameter for REVISE/PUBLISH/DELETE_DRAFT, without generic ETag semantics.
A1.8  Idempotency/convergence follows domain semantics; no generic Idempotency-Key requirement in M1.
A1.9  Failures are transport-neutral before HTTP mapping; API-03.11 defines the public failure-class/code/status boundary while application/domain remain HTTP-agnostic.
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

Collection GET usa il corresponding API-03.10 keyset/list contract; non introduce alternate resource identity tramite filter.

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

La Object collection usa API-03.10 ordering `id ASC`, summary senza properties e exact filters `template_id`, dependent `template_version`, `canonical_name`.

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

API-03.10 precisa normativamente che la Object-specific route significa **event che coinvolgono l'Object**:

```text
object_id = X
OR
destination_object_id = X
```

Questo include quindi, per esempio, ownership event dove l'Object è parent/destination oltre agli event dove è primary subject.

Lifecycle collection ordering è `(occurred_at,id) DESC`; API-03.10 definisce i first-class filter e opaque keyset pagination. Il cursor non rappresenta strict commit order, snapshot token o CDC token.

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

API-03.11B congela il mapping:

```text
new resource
    -> 201 + Location + canonical/command-specific result

normal semantic mutation
    -> 200 + resulting canonical semantic resource/projection

Relationship CREATE existing fact
    -> 200 + factual Relationship result

ATTACH exact existing edge
    -> 200 + current component projection

DETACH real/no-op
    -> 204

DELETE success
    -> 204

Relationship DELETE absent exact id
    -> 204 idempotent no-op
```

M1 non usa generic `{success:true}`, `{changed:false}`, SQL affected-row counts o `202 Accepted` per le primitive kernel.

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
A2.12 Lifecycle API is read-only under /api/v1/core/lifecycle-events and Object lifecycle projection; the Object-specific route means event involving the Object, i.e. object_id=X OR destination_object_id=X.
A2.13 Generic PATCH/PUT and autonomous owned-child CRUD are explicitly forbidden.
A2.14 Command responses represent semantic result/convergence, not persistence affected-row counts.
A2.15 expected_revision is required on relevant exact-DRAFT commands and is encoded by API-03.2 as a required positive-integer query parameter for REVISE/PUBLISH/DELETE_DRAFT.
A2.16 `core` is an API capability namespace only; it does not create a Core domain/service/repository abstraction.
A2.17 API-03.9/03.10 define canonical read/projection DTOs and one fixed keyset-paginated collection contract; no generic resource DTO, offset pagination or arbitrary sort surface is introduced.
A2.18 API-03.11 defines the transport-neutral failure-class/code to HTTP mapping, finite public error catalog, bounded details and success status/body policy.
```

---

## 6. API architecture status

API-03.1..11B are consolidated. No public HTTP/JSON command/read/list/error/success decision remains open for M1.

The JSON Schema compiler surface, if retained in M1, is a separate remaining architecture question and is not part of the HTTP API mapping contract.
