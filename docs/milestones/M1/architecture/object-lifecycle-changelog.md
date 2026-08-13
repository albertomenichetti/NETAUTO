# M1 — Object Lifecycle Changelog

**Status:** DRAFT

## 1. Responsabilità

M1 mantiene un unico lifecycle changelog operativo per ricostruire le transizioni semantiche degli Object.

Non è un audit/compliance subsystem.

Non introduce requisiti di:

- non-repudiation;
- compliance retention;
- forensic immutability contro DBA;
- actor attribution normativa;
- certification verso standard esterni.

Obiettivo:

> rappresentare in modo affidabile e query-friendly il lifecycle semantico prodotto dalle kernel mutation M1.

## 2. Event kinds M1

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
ATTACH_TO
DETACH_FROM
DELETED
```

Intrinsic e structural events appartengono allo **stesso event stream**.

## 3. Event identity e ordering

Ogni event possiede:

```text
id
occurred_at
```

`id` è una opaque kernel-generated UUIDv4 event identity.

`occurred_at`:

- è assegnato da NETAUTO, non dal caller;
- rappresenta il timestamp dell'event;
- l'esatta application-clock vs database-clock authority è technical decision da finalizzare.

M1 non introduce global sequence.

Canonical query/pagination ordering:

```text
occurred_at
+
event_id as deterministic tie-breaker
```

Per esempio descending:

```text
ORDER BY occurred_at DESC, id DESC
```

L'UUID tie-breaker non possiede temporal semantics; rende soltanto deterministico l'ordine tra timestamp uguali.

M1 non promette strict global commit order fra transazioni concorrenti indipendenti.

## 4. Common event shape

Concettualmente:

```text
ObjectLifecycleEvent
--------------------
id
occurred_at
kind

object_id
canonical_name

destination_object_id?
destination_canonical_name?

slot_declaring_template_id?
slot_name?

before_json?
after_json?
```

`object_id` identifica sempre il **subject** dell'evento.

## 5. Intrinsic event shape

Per:

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
DELETED
```

devono essere assenti:

```text
destination_object_id
destination_canonical_name
slot_declaring_template_id
slot_name
```

Snapshot semantics:

### CREATED

```text
before = absent
after  = initial complete canonical Object snapshot
canonical_name = created/final name
```

### RENAME

```text
before = complete canonical Object snapshot before
after  = complete canonical Object snapshot after
```

Unica differenza semanticamente ammessa:

```text
canonical_name
```

Event column `canonical_name` contiene il nuovo nome.

### DATA_CHANGE

```text
before = complete canonical Object snapshot before
after  = complete canonical Object snapshot after
```

Devono restare uguali:

```text
canonical_name
template_id
template_version
```

Event `canonical_name` contiene il current name after change.

### SCHEMA_CHANGE

```text
before = complete canonical source Object snapshot
after  = complete canonical target Object snapshot
```

`template_id` resta uguale; `template_version` e properties possono cambiare.

Event `canonical_name` contiene il current name.

### DELETED

```text
before = final complete canonical Object snapshot
after  = absent
```

Event `canonical_name` contiene il final/last known name.

## 6. Structural event direction

Per:

```text
ATTACH_TO
DETACH_FROM
```

```text
object_id
    = child / subject

canonical_name
    = child canonical_name at event time

destination_object_id
    = parent / owner

destination_canonical_name
    = parent canonical_name at event time

slot_declaring_template_id
slot_name
    = historical SlotSemanticKey
```

`before_json` e `after_json` sono assenti: la structural transition è completamente descritta dai typed event fields.

Event naming rende la direction esplicita:

```text
child ATTACH_TO parent / slot
child DETACH_FROM parent / slot
```

## 7. Unified stream rationale

Un singolo changelog rende dirette query operative come:

```text
latest N global events
latest N events involving Object X
timeline ordered by occurred_at/id
events after a cursor
```

Per il lifecycle completo di un Object `X`, gli structural event rilevanti includono:

```text
object_id = X
OR
destination_object_id = X
```

perché l'Object può partecipare come child o parent.

## 8. Historical references, not live FKs

Gli identifier salvati nel changelog sono historical identity references.

Non devono dipendere dall'esistenza corrente delle entity citate.

In particolare:

```text
object_id
destination_object_id
slot_declaring_template_id
```

non devono avere semantics di live FK verso current Object/ObjectTemplate rows.

Ragioni:

- `DELETED` deve sopravvivere alla rimozione dell'Object;
- structural history deve sopravvivere alla successiva delete di child/parent;
- il changelog non deve diventare hidden blocker della whole-lineage model delete.

Il fatto che non siano live FK non indebolisce la mutation atomicity: gli identifier vengono registrati nella stessa UoW in cui la transition reale viene validata e committata.

Per gli structural event non viene denormalizzato il canonical FQI della declaring ObjectTemplate; sono sufficienti:

```text
slot_declaring_template_id
slot_name
```

insieme ai canonical names degli Object.

## 9. Append-only kernel semantics

Le normali kernel/application workflow:

```text
INSERT lifecycle event
    -> sì, solo come parte della domain mutation che rappresenta

UPDATE existing lifecycle event
    -> no

DELETE existing lifecycle event
    -> no
```

Una correzione del current state produce una nuova domain mutation/event, non riscrittura della storia precedente.

Il livello di enforcement DB contro direct DBA UPDATE/DELETE è technical/operational policy separata; M1 non pretende compliance-grade forensic guarantees.

## 10. Lifecycle public surface is read-only

Il lifecycle changelog non è un aggregate direttamente mutabile dal dominio.

Non esistono public/domain commands per:

```text
create arbitrary lifecycle event
update lifecycle event
delete lifecycle event
```

Gli eventi vengono prodotti esclusivamente internamente alle rispettive mutation:

```text
Object.CREATE
Object.RENAME
Object.DATA_CHANGE
Object.SCHEMA_CHANGE
Object.ATTACH
Object.DETACH
Object.DELETE
```

Le sole interfacce esposte verso il domain/application changelog sono read/query interfaces.

## 11. Atomicity

Per ogni reale mutation M1:

```text
domain current-state transition
+
corresponding lifecycle event
```

committano o rollbackano insieme.

È vietato un committed current-state change senza event corrispondente e viceversa.

Idempotent no-op non produce eventi duplicati.

## 12. Query/read consistency

Changelog reads possono filtrare almeno concettualmente per:

```text
kind
object_id
destination_object_id
time/cursor range
```

Ordinary lifecycle reads osservano committed event state.

M1 non implementa automaticamente historical reconstruction dell'Object da questa event stream.

Historical `as-of` reconstruction e richer composite timelines sono RFE ad alta priorità M2.
