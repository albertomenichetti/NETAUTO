# M1 — API List / Pagination Contract

**Status:** DRAFT — API-03.10 collection envelope, keyset pagination, canonical ordering, list-item policy and route-specific filters ratified.

## 1. Scopo

Questo documento è l'authority API-03.10 per le collection/read-list surface M1.

Dipende da:

- `api-contract.md` — canonical public route inventory;
- `api-read-contract.md` — API-03.9 canonical single/projection DTO;
- `api-wire-contract.md` — API-03.1..08 request/wire rules;
- `persistence-model.md` — PERSIST-15 supporting read-path indices;
- owning domain read-consistency contracts.

M1 separa intenzionalmente:

```text
single/projection DTO shape
    -> API-03.9

collection envelope / ordering / filters / pagination
    -> API-03.10
```

---

## 2. Uniform collection envelope

Ogni collection paginabile restituisce:

```json
{
  "items": [],
  "next_cursor": null
}
```

Quando esiste una pagina successiva:

```json
{
  "items": [],
  "next_cursor": "<opaque-token>"
}
```

M1 non aggiunge genericamente:

```text
data
page
page_size
page_count
total_count
has_more
previous_cursor
```

`next_cursor != null` è l'unico segnale di continuation.

Non viene calcolato automaticamente `total_count`: il costo di count non viene imposto a ogni collection read e il valore non rappresenterebbe comunque uno snapshot cross-request stabile sotto mutation concorrenti.

---

## 3. `limit`

Query parameter comune:

```text
?limit=N
```

Contract M1:

```text
omitted -> 100
minimum -> 1
maximum -> 500
```

Empty, malformed, zero, negative o >500 sono transport-input failure.

Il caller può cambiare `limit` fra pagine della stessa semantic query.

---

## 4. Opaque keyset cursor

M1 usa esclusivamente keyset/cursor pagination.

```text
?cursor=<opaque-token>
```

Non esistono M1:

```text
offset
page-number
page-size + offset semantics
```

Il cursor:

- è opaco per il caller;
- è specifico della route/collection;
- è legato al canonical ordering della route;
- è legato al filter set attivo;
- non è una domain identity;
- non è un DB offset;
- non è un transaction/snapshot token;
- non è un change-feed/CDC token.

L'encoding interno del cursor non è public contract. L'implementation può usare una struttura interna versionata e autenticata/validata purché preservi la semantica sopra.

Un cursor usato su una route diversa o con filter semanticamente diversi è invalid input.

`limit` non fa parte della semantic query identity e può cambiare mantenendo lo stesso cursor.

---

## 5. Consistency fra pagine

Ogni pagina è una normale read operation snapshot-consistent secondo il relativo domain contract.

Non è garantita repeatability fra richieste separate:

```text
page 1
-> concurrent committed mutations
-> page 2
```

non equivale a una lunga REPEATABLE READ transaction.

Il cursor significa soltanto:

> continua dopo l'ultima canonical ordering key osservata dalla pagina precedente.

Concurrent create/delete/update possono quindi modificare la membership delle pagine successive secondo il nuovo committed state.

M1 non presenta questa pagination come snapshot export o synchronization protocol.

---

## 6. Fixed canonical ordering

M1 non espone genericamente:

```text
sort
order_by
direction
```

Ogni route ha un solo canonical ordering e relativo keyset cursor.

Ordering M1:

```text
DataType lineage collection
    (namespace, name) ASC

DataTypeVersion nested collection
    version ASC

ObjectTemplate lineage collection
    (namespace, name) ASC

ObjectTemplateVersion nested collection
    version ASC

Object collection
    id ASC

RelationshipDefinition collection
    id ASC

ObjectTemplate relationship-capabilities
    resolution_id ASC

Object components
    child_object_id ASC

Object-relative relationships
    (relationship_id, destination_object_id, name) ASC

Lifecycle event collections
    (occurred_at, id) DESC
```

`Object.id` è deliberatamente la pagination key della Object collection: `canonical_name` è mutable e non unique e non viene quindi usato come primary list-order cursor key.

Lifecycle ordering è deterministico ma non promette strict commit chronology; `occurred_at` conserva la `transaction_timestamp()` semantics già ratificata.

---

## 7. List item policy

M1 non assume che list item == exact GET DTO.

Quando l'exact resource può contenere state arbitrariamente/grandemente variabile, la list usa un summary bounded.

### 7.1 DataType lineage

Il lineage DTO API-03.9 è bounded e può essere riusato integralmente.

### 7.2 DataTypeVersion summary

```json
{
  "datatype_id": "<uuid>",
  "version": 3,
  "revision": 5,
  "status": "PUBLISHED",
  "base_type": "core.integer"
}
```

`constraints` non viene incluso nella version list.

### 7.3 ObjectTemplate lineage

Il lineage DTO API-03.9 è bounded e può essere riusato integralmente.

### 7.4 ObjectTemplateVersion summary

```json
{
  "template_id": "<uuid>",
  "version": 4,
  "revision": 7,
  "status": "DRAFT",
  "parent_template_id": "<uuid>",
  "parent_version": 3
}
```

Per root OTV `parent_template_id` e `parent_version` sono `null`.

Local `properties`/`components` non vengono inclusi nella version list.

### 7.5 Object summary

```json
{
  "id": "<uuid>",
  "canonical_name": "router-01",
  "template_id": "<uuid>",
  "template_version": 4
}
```

`properties` non viene incluso nella Object list.

### 7.6 RelationshipDefinition

Il complete Definition aggregate API-03.9 è bounded per costruzione (una o due Resolution) e viene riusato come list item.

### 7.7 Nested semantic projections

Le collection:

```text
relationship-capabilities
Object components
Object-relative relationships
```

riusano integralmente i rispettivi projection item API-03.9; non introducono una seconda summary shape.

### 7.8 Lifecycle

M1 non possiede una separate exact lifecycle-event detail route. Le lifecycle list restituiscono quindi il complete discriminated event DTO API-03.9, inclusi `before`/`after` per gli intrinsic event.

---

## 8. Route-specific filters

M1 non introduce generic query DSL, arbitrary expression language o fuzzy-search semantics.

Ogni filter è explicit e route-specific.

### 8.1 DataType lineage collection

Supporta exact filters:

```text
namespace
name
```

Qualified-name discovery resta collection filtering, non una seconda identity route.

### 8.2 ObjectTemplate lineage collection

Supporta:

```text
namespace=<exact>
name=<exact>
abstract=true|false
parent_template_id=<uuid>
```

### 8.3 Nested version collections

DataTypeVersion/ObjectTemplateVersion collection supportano:

```text
status=DRAFT|PUBLISHED|DEPRECATED
```

### 8.4 Object collection

Supporta:

```text
template_id=<uuid>
template_version=<positive-integer>
canonical_name=<exact-string>
```

`template_version` senza `template_id` è invalid input perché il version number non identifica globalmente una OTV lineage.

`canonical_name` è exact match; M1 non implica substring/fuzzy/full-text search.

### 8.5 RelationshipDefinition collection

M1 baseline non aggiunge filter specifici oltre a cursor/limit.

### 8.6 Relationship capability collection

Supporta:

```text
name=<exact>
```

### 8.7 Object components

Supporta:

```text
slot_name=<exact>
```

### 8.8 Object-relative relationships

Supporta:

```text
relationship_definition_id=<uuid>
name=<exact>
```

Non viene introdotto un graph query language.

### 8.9 Lifecycle collections

Global lifecycle route supporta:

```text
kind=<event-kind>
object_id=<uuid>
destination_object_id=<uuid>
relationship_id=<uuid>
relationship_definition_id=<uuid>
relationship_name=<exact-name>
occurred_from=<API-03.8 datetime>
occurred_to=<API-03.8 datetime>
```

La Object-specific lifecycle route non accetta un ulteriore `object_id`: il path identifica già l'Object coinvolto.

`occurred_from` / `occurred_to` riusano il canonical accepted `core.datetime` lexical contract API-03.8.

---

## 9. Object-specific lifecycle semantics

`GET /api/v1/core/objects/{object_id}/lifecycle-events` significa:

> tutti gli event che coinvolgono l'Object indicato.

Il predicate semantico è:

```text
object_id = X
OR
destination_object_id = X
```

Questo è necessario perché per ownership event:

```text
object_id             = child / subject
destination_object_id = parent / owner
```

mentre Relationship event materializzano già una semantic view per endpoint.

Object inesistente vs historical events referencing a deleted Object resta materia del route/failure contract: API-03.10 non trasforma il lifecycle changelog in current-resource FK state.

---

## 10. Cursor + filters

Il cursor viene costruito dopo l'applicazione dei filter e identifica la continuation della semantic query filtrata.

Esempio:

```text
GET /objects?template_id=T&limit=100
    -> next_cursor=C

GET /objects?template_id=T&cursor=C&limit=200
    -> valid continuation

GET /objects?template_id=T2&cursor=C
    -> invalid cursor
```

Il server non deve silenziosamente reinterpretare un cursor sotto una query diversa.

---

## 11. Persistence/index consequence

API-03.10 crea tre nuovi read-path requirement M1 da propagare a PERSIST-15:

```text
objects(canonical_name, id)

object_lifecycle_events(kind, occurred_at, id)

object_lifecycle_events(relationship_name, occurred_at, id)
    WHERE relationship_name IS NOT NULL
```

Il terzo è un partial index perché `relationship_name` esiste soltanto per Relationship lifecycle event.

Gli indici esistenti continuano a supportare almeno:

```text
objects(template_id, template_version)
object_components(parent_object_id, slot_name, child_object_id)
relationship_resolutions(from_template_id)
runtime_relationship_resolutions(from_object_id)
object_lifecycle_events(occurred_at, id)
object_lifecycle_events(object_id, occurred_at, id)
object_lifecycle_events(destination_object_id, occurred_at, id)
object_lifecycle_events(relationship_id, occurred_at, id)
object_lifecycle_events(relationship_definition_id, occurred_at, id)
```

---

## 12. Decisioni API-03.10

```text
A3.104
Every paginated collection uses {items:[...], next_cursor:string|null}.
No generic data wrapper, total_count, page count or has_more field.

A3.105
Pagination uses opaque keyset cursors only.
M1 exposes no offset/page-number pagination.

A3.106
limit is optional with default 100 and allowed range 1..500.

A3.107
A cursor is route/query-filter/order specific and is not a domain identity,
DB offset, snapshot token or change-feed token.
Its internal encoding is not public contract.

A3.108
Each page is independently snapshot-consistent.
Pagination across requests does not promise repeatable dataset membership
under concurrent mutation.

A3.109
M1 collection ordering is fixed per route; no generic sort/order query
surface is exposed.

A3.110
Default canonical orders are:
DataType/ObjectTemplate lineages -> namespace,name ASC;
nested versions -> version ASC;
Objects -> id ASC;
RelationshipDefinitions -> id ASC;
capabilities -> resolution_id ASC;
components -> child_object_id ASC;
ObjectRelationshipView -> relationship_id,destination_object_id,name ASC;
lifecycle -> occurred_at,id DESC.

A3.111
Collection routes use summary DTOs when the exact resource can carry
unbounded/large state: DTV list omits constraints; OTV list omits
declarations; Object list omits properties. Small/bounded lineage and
Definition aggregates may reuse full read DTOs.

A3.112
Nested capability/components/ObjectRelationshipView collections use their
complete API-03.9 projection item shape.

A3.113
Lifecycle collection items are complete API-03.9 event DTOs because M1
does not introduce a separate lifecycle-event detail route.

A3.114
/api/v1/core/objects/{object_id}/lifecycle-events means events involving
the Object: object_id == X OR destination_object_id == X.

A3.115
M1 filters are explicit route-specific exact filters; no generic query DSL
or fuzzy-search semantics are implied.

A3.116
Object list supports template_id, dependent template_version and exact
canonical_name filters. template_version without template_id is invalid.

A3.117
Lifecycle lists support kind, object/destination Object IDs,
relationship/definition IDs, exact relationship_name and occurred_from/to.

A3.118
Cursor continuation is bound to the active filter set.
Changing filters while reusing a cursor is invalid; limit may change.

A3.119
API-03.10 establishes new M1 read-path index requirements:
objects(canonical_name,id),
lifecycle(kind,occurred_at,id), and partial
lifecycle(relationship_name,occurred_at,id) WHERE relationship_name IS NOT NULL.

A3.120
These index additions are normative PERSIST-15 requirements and must be
kept aligned with the persistence model.
```

---

## 13. Non-goals M1

Fuori API-03.10/M1:

```text
arbitrary client sorting
offset pagination
automatic total counts
fuzzy/full-text Object search
generic query DSL
graph query language
cross-page repeatable snapshot token
CDC/change-feed semantics derived from ordinary list cursors
```
