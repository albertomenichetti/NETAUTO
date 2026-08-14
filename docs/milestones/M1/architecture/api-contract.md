# M1 — API Contract

**Status:** DRAFT — API-01 ratificato; route inventory, DTO/wire shape e failure mapping vengono consolidati nei successivi API point.

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
```

---

## 4. Next point

API-02 definisce la canonical route/resource/command inventory per tutte le 32 mutation M1 e per le primitive read necessarie, inclusi:

- route naming convention;
- HTTP method;
- target identity placement nel path;
- selector/candidate placement nel body;
- read-resource vs semantic-projection routes;
- endpoint che non devono esistere perché reintrodurrebbero generic CRUD semantics.
