# M1 — Object Lifecycle Changelog

**Status:** DRAFT

## 1. Responsabilità

M1 mantiene un unico lifecycle changelog operativo per rappresentare le transizioni semantiche degli Object.

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
RELATIONSHIP_CREATED
RELATIONSHIP_DELETED
DELETED
```

Intrinsic e structural events appartengono allo stesso event stream.

## 3. Event identity e ordering

Ogni event possiede:

```text
id
occurred_at
```

`id` è opaque kernel-generated UUIDv4.

`occurred_at`:

- è assegnato da NETAUTO, non dal caller;
- rappresenta il timestamp dell'event;
- application-clock vs DB-clock authority resta technical decision.

M1 non introduce global sequence.

Canonical ordering/pagination:

```text
occurred_at
+
event_id deterministic tie-breaker
```

L'event UUID non possiede temporal meaning.

M1 non promette strict global commit order fra transaction concorrenti indipendenti.

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

relationship_id?
relationship_definition_id?
relationship_name?

before_json?
after_json?
```

`object_id` è il primary Object perspective/subject dell'event kind.

La semantica specifica dipende dal kind.

## 5. Intrinsic event

Per:

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
DELETED
```

sono assenti:

```text
destination_object_id
destination_canonical_name
slot_declaring_template_id
slot_name
relationship_id
relationship_definition_id
relationship_name
```

### CREATED

```text
before = absent
after  = initial complete canonical Object snapshot
canonical_name = created/final name
```

### RENAME

```text
before = complete canonical snapshot before
after  = complete canonical snapshot after
```

Unica differenza semanticamente ammessa: `canonical_name`.

### DATA_CHANGE

```text
before = complete canonical snapshot before
after  = complete canonical snapshot after
```

Restano invariati:

```text
canonical_name
template_id
template_version
```

### SCHEMA_CHANGE

```text
before = complete canonical source snapshot
after  = complete canonical target snapshot
```

`template_id` resta invariato.

### DELETED

```text
before = final complete canonical Object snapshot
after  = absent
```

## 6. Ownership structural events

Per:

```text
ATTACH_TO
DETACH_FROM
```

```text
object_id
    = child / subject

destination_object_id
    = parent / owner

slot_declaring_template_id
slot_name
    = historical SlotSemanticKey
```

`canonical_name` e `destination_canonical_name` sono i display metadata osservati dalla mutation.

`before_json`/`after_json` sono assenti.

Ownership mutation reale produce un solo structural event.

## 7. Relationship lifecycle semantic views

R2 Relationship runtime può materializzare più resolved access rows per la stessa factual association.

Il changelog non registra una row per ogni runtime resolution row.

Normative rule:

> una factual Relationship CREATE/DELETE produce esattamente un lifecycle event per ogni **distinct object-relative semantic view** della transizione.

Una semantic view contiene:

```text
object_id
destination_object_id
relationship_name
```

dal punto di vista dell'Object indicato in `object_id`.

La deduplica concettuale all'interno della stessa factual transition usa:

```text
(object_id, destination_object_id, relationship_name)
```

non `relationship_resolution_id`.

## 8. Relationship event shape

Per:

```text
RELATIONSHIP_CREATED
RELATIONSHIP_DELETED
```

ogni event contiene:

```text
object_id
canonical_name

destination_object_id
destination_canonical_name

relationship_id
relationship_definition_id
relationship_name
```

Sono assenti:

```text
slot_declaring_template_id
slot_name
before_json
after_json
```

Non vengono persistiti come lifecycle semantics:

```text
source/target
forward/reverse
direction
relationship_resolution_id
```

L'event è già espresso dal punto di vista dell'Object in `object_id`.

## 9. Relationship event cardinality examples

### Ordinary non-symmetric

```text
VM is_hosted_by Hypervisor
Hypervisor hosts VM
```

produce due event:

```text
VM -> Hypervisor / is_hosted_by
Hypervisor -> VM / hosts
```

### Symmetric same-template, Object distinti

```text
A connects_to B
```

produce:

```text
A -> B / connects_to
B -> A / connects_to
```

due event.

### Symmetric self-loop

```text
A connects_to A
```

produce un solo distinct semantic-view event.

### Non-symmetric self-loop

```text
A manages A
A managed_by A
```

produce due event perché i semantic names sono distinti.

### Inheritance overlap

Più `RuntimeRelationshipResolution` rows possono collassare nella stessa:

```text
A -> B / name
```

semantic view.

Non producono event duplicati.

## 10. Relationship lifecycle names e canonical names

`relationship_name` è lo historical semantic name osservato dalla Relationship mutation da un coherent committed model snapshot.

Una successiva Definition RENAME non modifica event storici.

`canonical_name` / `destination_canonical_name` sono historical display metadata osservati dalla mutation.

Non introducono da soli generic serialization con Object.RENAME.

## 11. Unified stream rationale

Un singolo changelog supporta query come:

```text
latest N global events
timeline di Object X
events after cursor
relationship events by relationship_id
```

Per Relationship event, la complete semantic-view event materialization garantisce che ogni Object endpoint possieda direttamente event con:

```text
object_id = Object.id
```

Per ownership, un Object parent continua invece a comparire come `destination_object_id`.

Una query generale "events involving Object X" può quindi ancora usare:

```text
object_id = X
OR
destination_object_id = X
```

## 12. Historical references, not live FKs

Nel changelog sono historical identity references:

```text
object_id
destination_object_id
slot_declaring_template_id
relationship_id
relationship_definition_id
```

Non devono avere live FK semantics verso current entity rows.

Il changelog deve sopravvivere a:

- Object delete;
- Relationship delete;
- RelationshipDefinition delete;
- ObjectTemplate lineage delete quando altrimenti consentita.

`relationship_name`, canonical names e slot name preservano leggibilità operativa storica.

## 13. Append-only kernel semantics

Lifecycle event:

```text
INSERT
    -> solo come effetto interno della domain mutation

UPDATE
    -> no

DELETE
    -> no
```

Il lifecycle non è un aggregate pubblicamente mutabile.

Le public/domain surface del changelog sono read/query only.

## 14. Event-set atomicity

Normative rule:

> ogni reale domain transition e l'intero lifecycle event set richiesto da quella transition committano o rollbackano insieme.

Per:

```text
Object.CREATE
Object.RENAME
Object.DATA_CHANGE
Object.SCHEMA_CHANGE
Object.ATTACH
Object.DETACH
Object.DELETE
```

l'event set ha cardinalità 1.

Per:

```text
Relationship.CREATE
Relationship.DELETE
```

la cardinalità è il numero di distinct object-relative semantic views.

Sono vietati:

- current-state mutation senza complete event set;
- partial event set;
- event set senza corresponding current-state transition;
- duplicate event set per idempotent no-op.

## 15. Query/read consistency

Changelog reads possono filtrare almeno concettualmente per:

```text
kind
object_id
destination_object_id
relationship_id
relationship_definition_id
relationship_name
time/cursor range
```

Ordinary lifecycle reads osservano committed state.

M1 non implementa automaticamente historical Object/Relationship reconstruction.

Historical `as-of` reconstruction e richer composite timeline sono RFE ad alta priorità M2.

