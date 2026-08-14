# M1 — API Read Contract

**Status:** DRAFT — API-03.9 canonical single-resource/projection read DTO contract e API-03.10 collection/list contract ratificati. Success/failure HTTP mapping resta separato.

## 1. Scopo

Questo documento è l'authority API-03.9 per le canonical public single-resource/projection read DTO M1.

Non introduce un generic entity/resource DTO. Le read surface restano semantic projections distinte:

```text
stable lineage read
exact version read
effective schema read
Object intrinsic current-state read
ownership projection
RelationshipDefinition aggregate read
factual Relationship semantic projection
Object-relative Relationship projection
lifecycle/history read
```

Le persistence rows non sono public DTO authority.

Collection envelope, pagination, filters, canonical list ordering e summary/full list-item policy sono authority separata in `api-list-contract.md` / API-03.10.

---

## 2. Regole comuni

Single-resource/projection response non usa generic `data` envelope.

Canonical scalar representation:

```text
UUID        -> canonical hyphenated string
version     -> positive JSON integer
revision    -> positive JSON integer
status      -> DRAFT | PUBLISHED | DEPRECATED
value_mode  -> SCALAR | LIST
Primitive   -> canonical API-03.8 representation
```

Explicit `null` viene usato soltanto per genuine nullable/zero-one state. Collection/map semanticamente vuote usano `[]` / `{}` e non `null`.

Esempi di nullable state:

```text
description
lineage default_version
ObjectTemplate parent lineage on root
Object.owner projection when detached
CREATED.before
DELETED.after
```

Una field semanticamente assente ma non nullable resta omessa quando il domain contract lo richiede. In particolare una optional ObjectTemplate property non espone `migration_default:null`: `migration_default` è assente.

---

## 3. DataType read DTO

### 3.1 Stable lineage

`GET /api/v1/core/datatypes/{datatype_id}`:

```json
{
  "id": "<uuid>",
  "namespace": "network.routing",
  "name": "asn",
  "description": "BGP ASN",
  "default_version": 3
}
```

`description` e `default_version` possono essere `null`.

La lineage read non inlinea automaticamente l'intera version collection.

### 3.2 Exact DataTypeVersion

`GET /api/v1/core/datatypes/{datatype_id}/versions/{version}`:

```json
{
  "datatype_id": "<uuid>",
  "version": 3,
  "revision": 5,
  "status": "PUBLISHED",
  "base_type": "core.integer",
  "constraints": {
    "minimum": 1,
    "maximum": 4294967295
  }
}
```

`constraints` è sempre object; zero constraints => `{}`.

`revision` resta esposta anche dopo publication come generation della candidate da cui deriva la snapshot; non diventa generic HTTP resource revision.

---

## 4. ObjectTemplate read DTO

### 4.1 Stable lineage

`GET /api/v1/core/object-templates/{template_id}`:

```json
{
  "id": "<uuid>",
  "namespace": "network",
  "name": "router",
  "description": null,
  "abstract": false,
  "parent_template_id": "<uuid>",
  "default_version": 4
}
```

Root lineage espone `parent_template_id:null`. `default_version` può essere `null`.

### 4.2 Exact local ObjectTemplateVersion snapshot

`GET /api/v1/core/object-templates/{template_id}/versions/{version}` restituisce la snapshot locale autorevole, non l'effective schema:

```json
{
  "template_id": "<uuid>",
  "version": 4,
  "revision": 7,
  "status": "DRAFT",
  "parent_template_id": "<uuid>",
  "parent_version": 3,
  "properties": [],
  "components": []
}
```

Root exact version espone:

```json
{
  "parent_template_id": null,
  "parent_version": null
}
```

Local `properties` e `components` sono sempre esplicite arrays e sono ordinate canonicalmente per `position`.

Property read shape:

```json
{
  "name": "hostname",
  "position": 10,
  "datatype_id": "<uuid>",
  "datatype_version": 2,
  "value_mode": "SCALAR",
  "required": true,
  "migration_default": "unknown"
}
```

Per property optional `migration_default` è assente.

Component read shape:

```json
{
  "name": "interfaces",
  "position": 10,
  "target_template_id": "<uuid>"
}
```

### 4.3 Effective schema projection

`GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema`:

```json
{
  "template_id": "<uuid>",
  "version": 4,
  "properties": [],
  "components": []
}
```

Ogni effective property/component include `declaring_template_id` perché la semantic identity è rispettivamente `PropertySemanticKey` / `SlotSemanticKey`.

Effective property example:

```json
{
  "declaring_template_id": "<uuid>",
  "name": "hostname",
  "position": 10,
  "datatype_id": "<uuid>",
  "datatype_version": 2,
  "value_mode": "SCALAR",
  "required": true,
  "migration_default": "unknown"
}
```

Effective component example:

```json
{
  "declaring_template_id": "<uuid>",
  "name": "interfaces",
  "position": 20,
  "target_template_id": "<uuid>"
}
```

Canonical effective ordering segue il domain contract:

```text
ancestor/root blocks -> ... -> leaf block
within each local block -> position ascending
```

Questo response ordering derivato non rende semanticamente significativo l'ordine degli array request API-03.5.

---

## 5. Relationship capability read

`GET /api/v1/core/object-templates/{template_id}/relationship-capabilities` espone semantic capability item:

```json
{
  "resolution_id": "<uuid>",
  "relationship_definition_id": "<uuid>",
  "name": "hosts",
  "from_template_id": "<uuid>",
  "to_template_id": "<uuid>"
}
```

`from_template_id` resta esplicito anche se la route è ancorata a una lineage, perché la Resolution applicabile può essere dichiarata su un ancestor compatibility space.

---

## 6. Object current-state read

`GET /api/v1/core/objects/{object_id}` restituisce esclusivamente intrinsic current state:

```json
{
  "id": "<uuid>",
  "canonical_name": "router-01",
  "template_id": "<uuid>",
  "template_version": 4,
  "properties": {
    "hostname": "router-01"
  }
}
```

`properties` usa sempre canonical PrimitiveType output. Canonical zero-cardinality property resta key assente.

Non vengono embedded automaticamente owner, components, Relationships o lifecycle.

---

## 7. Ownership projections

### 7.1 Components

`GET /api/v1/core/objects/{parent_object_id}/components` usa item semanticamente risolto:

```json
{
  "slot_declaring_template_id": "<uuid>",
  "slot_name": "interfaces",
  "child_object_id": "<uuid>"
}
```

La projection non espone `object_components` come public persistence resource.

### 7.2 Owner

`GET /api/v1/core/objects/{child_object_id}/owner` quando owned:

```json
{
  "parent_object_id": "<uuid>",
  "slot_declaring_template_id": "<uuid>",
  "slot_name": "interfaces"
}
```

Quando l'Object esiste ma è detached:

```text
HTTP 200
body = null
```

Object inesistente resta una distinct NotFound failure. La zero-cardinality projection non viene reinterpretata come resource-not-found.

---

## 8. RelationshipDefinition aggregate read

`GET /api/v1/core/relationship-definitions/{relationship_definition_id}` restituisce sempre complete aggregate:

```json
{
  "id": "<uuid>",
  "symmetric": false,
  "resolutions": [
    {
      "resolution_id": "<uuid>",
      "name": "hosts",
      "from_template_id": "<uuid>",
      "to_template_id": "<uuid>"
    }
  ]
}
```

La complete `resolutions` collection non possiede forward/reverse ordering semantic. `relationship_definition_id` non viene duplicato nei child nested perché l'aggregate parent è già esplicito.

RelationshipResolution non diventa una standalone public CRUD/read resource.

---

## 9. Factual Relationship read

`GET /api/v1/core/relationships/{relationship_id}` espone factual aggregate semantic projection:

```json
{
  "id": "<uuid>",
  "relationship_definition_id": "<uuid>",
  "views": [
    {
      "object_id": "<uuid-a>",
      "destination_object_id": "<uuid-b>",
      "name": "hosts"
    }
  ]
}
```

`views` è il distinct semantic-view set della factual Relationship, non la physical `RuntimeRelationshipResolution` closure.

Inheritance overlap può produrre più raw runtime rows ma non duplicate public semantic views. Symmetric self-loop può produrre una sola view; non-symmetric self-loop può produrre più views con names distinti.

---

## 10. Object-relative Relationship read

`GET /api/v1/core/objects/{object_id}/relationships` usa self-contained `ObjectRelationshipView` item:

```json
{
  "relationship_id": "<uuid>",
  "relationship_definition_id": "<uuid>",
  "object_id": "<uuid>",
  "destination_object_id": "<uuid>",
  "name": "hosts"
}
```

`object_id` resta esplicito anche se coincide con il path, così la projection conserva autonomamente la propria semantic perspective.

La read applica semantic deduplication e non espone raw runtime rows.

---

## 11. Lifecycle event read DTO

Lifecycle public read usa una discriminated union per event family/kind e non un'unica persistence-shaped record con numerosi nullable field.

### 11.1 Intrinsic events

Per `CREATED`, `RENAME`, `DATA_CHANGE`, `SCHEMA_CHANGE`, `DELETED`:

```json
{
  "id": "<event-uuid>",
  "occurred_at": "2026-08-14T16:40:00.123456Z",
  "kind": "DATA_CHANGE",
  "object_id": "<uuid>",
  "canonical_name": "router-01",
  "before": {
    "id": "<uuid>",
    "canonical_name": "router-01",
    "template_id": "<uuid>",
    "template_version": 4,
    "properties": {}
  },
  "after": {
    "id": "<uuid>",
    "canonical_name": "router-01",
    "template_id": "<uuid>",
    "template_version": 4,
    "properties": {}
  }
}
```

`before` / `after` riusano la canonical Object snapshot shape.

```text
CREATED.before -> null
DELETED.after  -> null
```

Qui `null` significa genuine historical state absence.

### 11.2 Ownership events

Per `ATTACH_TO` / `DETACH_FROM`:

```json
{
  "id": "<event-uuid>",
  "occurred_at": "2026-08-14T16:40:00.123456Z",
  "kind": "ATTACH_TO",
  "object_id": "<child-uuid>",
  "canonical_name": "nic-01",
  "destination_object_id": "<parent-uuid>",
  "destination_canonical_name": "server-01",
  "slot_declaring_template_id": "<uuid>",
  "slot_name": "interfaces"
}
```

Non vengono aggiunti meaningless `before`/`after` null field.

### 11.3 Relationship events

Per `RELATIONSHIP_CREATED` / `RELATIONSHIP_DELETED`:

```json
{
  "id": "<event-uuid>",
  "occurred_at": "2026-08-14T16:40:00.123456Z",
  "kind": "RELATIONSHIP_CREATED",
  "object_id": "<uuid-a>",
  "canonical_name": "vm-01",
  "destination_object_id": "<uuid-b>",
  "destination_canonical_name": "host-01",
  "relationship_id": "<uuid>",
  "relationship_definition_id": "<uuid>",
  "relationship_name": "is_hosted_by"
}
```

Non vengono esposti direction/source/target o Resolution IDs.

`occurred_at` viene serializzato come canonical UTC `Z` datetime secondo API-03.8; la temporal semantics resta PostgreSQL `transaction_timestamp()` come definita nel lifecycle domain contract.

---

## 12. Decisioni API-03.9

```text
A3.89
Single-resource/projection responses have no generic data envelope.

A3.90
Canonical read DTOs expose explicit null only for genuine nullable/zero-one
state; empty collections/maps use []/{} and are not null.

A3.91
DataType lineage and exact-version reads remain separate DTOs;
lineage does not inline its version collection.

A3.92
ObjectTemplate lineage, exact-version local snapshot and effective-schema
projection are three separate DTOs.

A3.93
Effective-schema members include declaring_template_id and are returned
in canonical effective ordering; request-array ordering remains unrelated.

A3.94
Relationship capability items expose resolution_id,
relationship_definition_id, name, from_template_id and to_template_id.

A3.95
Object GET exposes only intrinsic current state:
id/canonical_name/template exact pin/canonical properties.

A3.96
Ownership reads are semantic projections and expose SlotSemanticKey data;
they never expose object_components as a CRUD/resource representation.

A3.97
GET Object.owner returns JSON null for an existing detached Object;
Object-not-found remains a distinct failure.

A3.98
RelationshipDefinition GET always returns the complete
Definition + Resolution aggregate.

A3.99
Relationship GET returns a factual aggregate with deduplicated semantic
views, never raw RuntimeRelationshipResolution rows.

A3.100
Object-relative Relationship read returns self-contained
ObjectRelationshipView items and performs semantic deduplication.

A3.101
Lifecycle read DTO is a discriminated union by event kind/family,
not one wide nullable persistence-shaped record.

A3.102
Intrinsic lifecycle before/after reuse canonical Object snapshot shape;
null means historical state absence for CREATED/DELETED.

A3.103
Collection route envelopes, list-item policy, pagination and filters are
defined separately by API-03.10 in api-list-contract.md.
```

---

## 13. API-03.10 relationship

API-03.10 in `api-list-contract.md` is normative for all collection routes built from these DTO/projection shapes.

Key consequences:

```text
uniform envelope
    {items:[...], next_cursor:string|null}

pagination
    opaque keyset cursor only
    limit default 100, range 1..500
    no offset/page-number

ordering
    fixed per route; no generic sort/order surface

list item policy
    bounded/full where cheap
    summary for DTV/OTV/Object where exact state may be large

filters
    explicit route-specific exact filters only

consistency
    every page independently snapshot-consistent
    cursor is not a cross-request snapshot/CDC token
```

Object-specific lifecycle route means events involving the Object (`object_id=X OR destination_object_id=X`).

The three API-03.10 read-path index requirements are normative in PERSIST-15.

Success/failure HTTP status and error-body mapping are deliberately outside API-03.9/03.10 and remain the next API architecture point.
