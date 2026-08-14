# M1 — Object Lifecycle Changelog

**Status:** DRAFT — lifecycle semantics, metadata observation e public read/list semantics ratificate; allineato a REALIZE-14/15 e API-03.9/03.10.

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

`id` è opaque UUID row identity usata anche come deterministic tie-breaker. Non possiede domain semantics e viene generata da PostgreSQL nella stessa Unit of Work della domain mutation; l'application può ottenere il valore tramite `INSERT ... RETURNING id`.

Questa scelta è intenzionalmente diversa dalle domain identity come `Object.id`, `Relationship.id` e `RelationshipDefinition.id`, che sono kernel/application-generated.

`occurred_at` è PostgreSQL-clock authoritative:

```text
TIMESTAMPTZ NOT NULL
DEFAULT transaction_timestamp()
```

`CURRENT_TIMESTAMP` è semanticamente equivalente in PostgreSQL.

Conseguenze:

- tutti gli event della stessa semantic Unit of Work condividono lo stesso transaction-start timestamp;
- `occurred_at` non rappresenta physical commit time;
- `occurred_at` non definisce strict global commit order tra transaction concorrenti;
- per event con display metadata osservati più tardi nella stessa transaction, `occurred_at` non è il timestamp dell'observation snapshot e non impone causal ordering rispetto a concurrent metadata mutation.

M1 non introduce global sequence.

Canonical deterministic ordering key:

```text
occurred_at
+
event_id deterministic tie-breaker
```

Per le public lifecycle collection API-03.10 fissa l'ordine:

```text
(occurred_at, id) DESC
```

così le timeline espongono gli event più recenti per primi. Questo ordering resta deterministico, non una promessa di strict commit chronology.

L'event UUID non possiede temporal meaning.

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

La persistence fisica tipizzata, inclusi i campi JSONB `before_state`/`after_state`, è definita in `persistence-model.md`.

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

`canonical_name` e `destination_canonical_name` sono historical display metadata osservati dalla mutation; non fanno parte della ownership fact identity.

REALIZE-15 fissa il concrete observation contract:

```text
destination_canonical_name
    -> proviene dalla parent Object row già stabilizzata
       dal parent ownership owner lock

canonical_name
    -> committed child display metadata osservato
       dopo la parent stabilization
       senza introdurre un child lock soltanto per l'evento
```

Una concurrent child `RENAME` può quindi produrre nell'event il committed old o new child name secondo l'observation point. Questo non modifica la semantica dell'ownership fact e non introduce un nuovo safety predicate.

Ownership produce un solo structural event per real transition, quindi non necessita della multi-event snapshot machinery usata dai Relationship event.

`before_json`/`after_json` sono assenti.

Ownership mutation reale produce un solo structural event; una ownership no-op non produce event.

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

La concurrency requirement completa per questi metadata è `S-REL-EVENT-SNAPSHOT` in `concurrency-semantic-matrix.md`, realizzata in `concurrency-postgresql-realization-relationship.md`.

Concrete M1 observation rule:

> una singola real Relationship CREATE/DELETE deriva l'intero lifecycle semantic-view event set da **un solo SQL metadata-observation statement** a `READ COMMITTED`, contenente tutti i required Resolution names e source/destination Object canonical names nello stesso MVCC snapshot.

Non sono ammesse più metadata SELECT indipendenti per costruire parti dello stesso event set. Non vengono presi `FOR SHARE`/`FOR UPDATE` soltanto per questi historical metadata.

Per CREATE la metadata observation avviene dopo la complete runtime closure insertion riuscita; per DELETE avviene prima della closure removal. La semantic-view dedup può essere eseguita nella stessa query.

Una concurrent Definition/Object rename che committa dopo il metadata observation point ma prima del factual Relationship commit non invalida il captured event set.

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

Normative Object-specific timeline rule API-03.10:

```text
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

significa **event che coinvolgono l'Object** e usa quindi:

```text
object_id = X
OR
destination_object_id = X
```

Non significa soltanto `object_id = X`; altrimenti il parent non vedrebbe i propri ATTACH/DETACH structural event.

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

Append-only è un kernel/application contract M1, non un compliance-grade trigger/DB immutability contract.

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

## 15. Query/read consistency e public filters

Changelog reads osservano committed state e possono filtrare concettualmente per:

```text
kind
object_id
destination_object_id
relationship_id
relationship_definition_id
relationship_name
time/cursor range
```

API-03.9 definisce il canonical discriminated lifecycle event DTO.

API-03.10 rende public first-class i filter globali:

```text
kind
object_id
destination_object_id
relationship_id
relationship_definition_id
relationship_name
occurred_from
occurred_to
```

`relationship_name` è exact-match historical name. `occurred_from/to` riusano il public datetime lexical contract API-03.8.

La Object-specific lifecycle route usa il path Object come involving predicate e non accetta un secondo `object_id` query selector.

Pagination M1 usa opaque keyset cursor, default `limit=100`, max 500 e canonical ordering `(occurred_at,id) DESC`. Il cursor non è snapshot token, CDC token o strict commit-order token.

PERSIST-15 contiene gli indici read-path richiesti da questi filter, inclusi `(kind, occurred_at, id)` e il partial `(relationship_name, occurred_at, id) WHERE relationship_name IS NOT NULL`.

M1 non implementa automaticamente historical Object/Relationship reconstruction.

Historical `as-of` reconstruction e richer composite timeline sono RFE ad alta priorità M2.
