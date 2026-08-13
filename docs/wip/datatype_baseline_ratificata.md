# DataType — Baseline Relazionale e Concurrency Contract Ratificato

## 1. Modello relazionale di riferimento

La baseline seguente si basa sul modello relazionale PostgreSQL attuale di `DataType`.

### 1.1 `datatypes`

La tabella `datatypes` rappresenta l'identità stabile del DataType.

```text
datatypes
--------
id              TEXT    PRIMARY KEY
namespace       TEXT    NOT NULL
name            TEXT    NOT NULL
description     TEXT    NULL

UNIQUE(namespace, name)
```

Vincoli principali:

- `id` identifica univocamente il DataType;
- `(namespace, name)` deve essere univoco;
- la riga `datatypes(id)` rappresenta l'identità stabile della lineage di versioni.

### 1.2 `datatype_versions`

La tabella `datatype_versions` contiene le versioni del DataType.

```text
datatype_versions
-----------------
datatype_id      TEXT       NOT NULL
version          INTEGER    NOT NULL
status           TEXT       NOT NULL
base_type        TEXT       NOT NULL
constraints_json TEXT       NOT NULL

PRIMARY KEY(datatype_id, version)

FOREIGN KEY(datatype_id)
    REFERENCES datatypes(id)
    ON DELETE RESTRICT
```

Vincoli e semantica principali:

- l'identità esatta di una versione è `(datatype_id, version)`;
- ogni versione deve appartenere a un `DataType` esistente;
- la FK impedisce la persistenza di `DataTypeVersion` orfane;
- il lifecycle ammesso è strettamente monotono:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

- `DEPRECATED` è terminale;
- una nuova versione nasce in stato `DRAFT`;
- `create-next` può utilizzare come source una versione `PUBLISHED` o `DEPRECATED`, mai `DRAFT`.

### 1.3 Riferimenti da `ObjectTemplateProperty`

Le property di un `ObjectTemplateVersion` referenziano una specifica `DataTypeVersion` tramite una FK composta.

```text
object_template_properties
--------------------------
datatype_id
datatype_version
...

FOREIGN KEY(datatype_id, datatype_version)
    REFERENCES datatype_versions(datatype_id, version)
    ON DELETE RESTRICT
```

Questa FK garantisce l'esistenza della versione referenziata, ma **non** può garantire semanticamente che la versione sia `PUBLISHED`.

La condizione:

```text
status == PUBLISHED
```

è quindi un predicato di admission che deve essere protetto dal workflow che crea un nuovo binding.

## 2. Principio di concorrenza adottato

Non viene assunto alcun locking globale del model-plane o cross-plane.

Ogni operazione viene protetta usando il **meccanismo minimo necessario per il proprio specifico invariante**.

I meccanismi ammessi possono quindi differire tra operazioni:

- constraint relazionali;
- atomicità transazionale;
- conditional `UPDATE` / compare-and-swap;
- row lock puntuali;
- lock lato consumer quando il consumer deve mantenere stabile un predicato fino al commit.

Non esiste un unico "protocollo DataType".

## 3. Baseline ratificata delle operazioni DataType

### 3.1 Create di un nuovo DataType

#### Dati toccati

La transazione crea:

```text
datatypes
    id = nuovo UUID

datatype_versions
    datatype_id = nuovo UUID
    version = 1
    status = DRAFT
```

#### Rischi

Non esiste una race semantica che richieda coordinamento esplicito.

Le collisioni concorrenti sono già protette da:

```text
PRIMARY KEY(datatypes.id)
UNIQUE(datatypes.namespace, datatypes.name)
PRIMARY KEY(datatype_versions.datatype_id, datatype_versions.version)
```

La FK:

```text
datatype_versions.datatype_id
    -> datatypes.id
    ON DELETE RESTRICT
```

impedisce la persistenza di una versione orfana.

La v1 nasce inoltre `DRAFT`, quindi non è ammissibile come target di un nuovo binding che richiede una `DataTypeVersion` `PUBLISHED`.

#### Decisione ratificata

**SAFE senza locking esplicito.**

È sufficiente che la creazione del DataType e della sua v1 avvenga nella stessa transazione:

```text
BEGIN

INSERT datatypes(...)
INSERT datatype_versions(... version=1, status=DRAFT)

COMMIT
```

Protezione:

```text
atomicità transazionale
+ PK
+ UNIQUE
+ FK
```

### 3.2 Publish di una DataTypeVersion

#### Dati toccati

La transizione modifica la riga:

```text
(datatype_id, version)
```

portando:

```text
DRAFT -> PUBLISHED
```

#### Rischio

Una semplice sequenza:

```text
READ status
validate DRAFT
UPDATE status=PUBLISHED
```

può prendere una decisione su uno stato ormai stale.

Sono possibili race come:

```text
publish vs publish
publish vs revise
publish vs deprecate
```

Il requisito fondamentale è rendere atomica la precondizione:

```text
status == DRAFT
```

con la transizione stessa.

#### Decisione ratificata

**Nessun lock esplicito.**

Usare un conditional `UPDATE` / CAS sulla singola DataTypeVersion:

```sql
UPDATE datatype_versions
SET status = 'PUBLISHED'
WHERE datatype_id = :datatype_id
  AND version = :version
  AND status = 'DRAFT';
```

Interpretazione:

```text
rowcount == 1
    -> publish riuscita

rowcount == 0
    -> precondizione non più valida
       oppure versione inesistente
```

Il workflow può effettuare una lettura successiva, se necessario, per distinguere i differenti errori di dominio.

### 3.3 Create next version di un DataType

#### Dati letti

L'operazione legge:

```text
source = (datatype_id, source_version)
```

La source deve soddisfare:

```text
status IN {PUBLISHED, DEPRECATED}
```

Viene inoltre letto l'insieme delle versioni appartenenti alla stessa lineage per determinare:

```text
next_version = max(existing_versions) + 1
```

#### Dati scritti

Viene creata:

```text
(datatype_id, next_version)
status = DRAFT
```

#### Rischio di delete concorrente

Non esiste rischio di persistere una versione orfana.

La FK:

```text
datatype_versions.datatype_id
    -> datatypes.id
    ON DELETE RESTRICT
```

rende impossibile lo stato:

```text
DataType assente
+
DataTypeVersion presente
```

#### Validità concorrente della source

Una source `PUBLISHED` può diventare concorrente `DEPRECATED`, ma questo non invalida il predicato di admission:

```text
PUBLISHED  -> source valida
DEPRECATED -> source valida
```

Non è quindi necessario stabilizzare lo status della source per questa operazione.

#### Criticità reale

Due `create-next` concorrenti sullo stesso DataType possono osservare lo stesso insieme di versioni:

```text
T1                         T2

MAX(version) = 4           MAX(version) = 4
next = 5                   next = 5
```

La PK impedirebbe la corruzione, ma una delle due operazioni fallirebbe per collisione tecnica invece di ricevere il successivo numero disponibile.

La risorsa logica da serializzare è quindi:

```text
l'allocazione del prossimo numero
per la lineage del singolo DataType
```

non la specifica source version.

#### Decisione ratificata

Acquisire un row lock sulla riga stabile:

```text
datatypes(id = :datatype_id)
```

**prima** di calcolare il nuovo numero:

```sql
SELECT id
FROM datatypes
WHERE id = :datatype_id
FOR UPDATE;
```

Sequenza:

```text
lock DataType identity
-> read existing versions
-> compute max(version) + 1
-> insert new DRAFT version
-> commit
```

Effetto desiderato:

```text
create-next DT-A vs create-next DT-A
    -> serializzate

create-next DT-A vs create-next DT-B
    -> pienamente concorrenti
```

La riga `datatypes(id)` funge quindi da mutex locale della lineage.

### 3.4 Deprecate di una DataTypeVersion

#### Dati toccati

La transizione modifica:

```text
(datatype_id, version)
```

portando:

```text
PUBLISHED -> DEPRECATED
```

#### Invariante locale

La transizione è valida soltanto se la versione è ancora `PUBLISHED`.

#### Decisione ratificata lato deprecator

**Nessun lock esplicito preventivo.**

Usare un conditional `UPDATE` / CAS:

```sql
UPDATE datatype_versions
SET status = 'DEPRECATED'
WHERE datatype_id = :datatype_id
  AND version = :version
  AND status = 'PUBLISHED';
```

Interpretazione:

```text
rowcount == 1
    -> deprecate riuscita

rowcount == 0
    -> precondizione non più valida
       oppure versione inesistente
```

#### Race con nuovi consumer

Un nuovo consumer può creare un binding solo se la versione è `PUBLISHED`.

Esempio:

```text
ObjectTemplateProperty
    -> exact DataTypeVersion
```

La FK garantisce solamente l'esistenza della versione, non il suo status.

La responsabilità di mantenere stabile:

```text
status == PUBLISHED
```

fino al commit del nuovo binding appartiene quindi **al consumer**.

#### Decisione ratificata lato consumer

Il consumer deve acquisire:

```sql
SELECT ...
FROM datatype_versions
WHERE datatype_id = :datatype_id
  AND version = :version
FOR SHARE;
```

poi:

```text
verify status == PUBLISHED
persist binding
COMMIT
```

`FOR SHARE` è scelto perché:

- più consumer possono leggere contemporaneamente la stessa versione;
- l'`UPDATE` concorrente del `deprecate` deve attendere;
- `FOR KEY SHARE` sarebbe troppo debole, perché il deprecate modifica `status`, non la chiave.

Il contratto risultante è di **admission-time consistency**:

> un nuovo binding può essere creato soltanto verso una DataTypeVersion che rimane `PUBLISHED` fino al commit del binding.

Dopo quel commit, la versione può diventare `DEPRECATED` e il binding esistente rimane valido.

### 3.5 Revise di una DataTypeVersion

#### Dati toccati

La `revise` modifica i dati della versione, principalmente i constraints, mantenendo:

```text
status = DRAFT
```

#### Precondizione

La revise è consentita solo quando:

```text
status == DRAFT
```

#### Race principali

##### Revise vs publish

```text
T1 revise                     T2 publish

READ DRAFT                    READ DRAFT

                               PUBLISH
                               COMMIT

WRITE revise basata
su stato stale
```

##### Revise vs revise

```text
T1                           T2

READ DRAFT/C0                READ DRAFT/C0

produce C1                   produce C2

WRITE C1
COMMIT

                             WRITE C2
                             COMMIT
```

In questo secondo caso C1 viene perso silenziosamente.

Un CAS basato soltanto su:

```text
status == DRAFT
```

non è sufficiente, perché entrambe le revise mantengono `DRAFT`.

#### Decisione ratificata

Acquisire un row lock sulla specifica versione **prima della lettura decisionale**:

```sql
SELECT ...
FROM datatype_versions
WHERE datatype_id = :datatype_id
  AND version = :version
FOR NO KEY UPDATE;
```

Poi:

```text
read current row
verify DRAFT
produce revised constraints
UPDATE
COMMIT
```

`FOR NO KEY UPDATE` è sufficiente perché l'operazione non modifica le chiavi della riga.

Protezione:

```text
revise vs revise
revise vs lifecycle update sulla stessa versione
```

senza bloccare altre versioni o altri DataType.

### 3.6 Delete di un DataType

#### Dati toccati

L'operazione elimina:

```text
tutte le datatype_versions del datatype
+
la riga datatypes
```

nella stessa transazione.

#### Contratto

Il DataType non può essere cancellato se almeno una delle sue versioni è ancora referenziata da una property di un ObjectTemplate.

#### Protezione relazionale

Esiste:

```text
object_template_properties
    (datatype_id, datatype_version)
        -> datatype_versions(datatype_id, version)
        ON DELETE RESTRICT
```

e inoltre:

```text
datatype_versions.datatype_id
    -> datatypes.id
    ON DELETE RESTRICT
```

Questi vincoli rendono impossibile:

- eliminare una DataTypeVersion ancora referenziata;
- creare una reference persistente verso una versione già eliminata;
- lasciare versioni orfane rispetto al DataType.

#### Race con un nuovo riferimento concorrente

Sono possibili solamente due esiti consistenti:

```text
nuovo riferimento vince
-> il delete non può eliminare la versione

oppure

delete vince
-> il nuovo riferimento non può essere persistito
```

Non può esistere uno stato finale con FK dangling.

#### Decisione ratificata

**SAFE senza locking esplicito.**

È sufficiente:

```text
transazione atomica
+ FK RESTRICT
```

L'eventuale pre-check applicativo serve principalmente a restituire un errore semantico come:

```text
DataTypeInUse
```

In presenza di una race persa dal delete, la FK rimane l'autorità finale per la consistenza.

Resta eventualmente da garantire una corretta traduzione della specifica FK violation nel corrispondente errore di dominio.

## 4. Riepilogo operativo

| Operazione | Criticità | Protezione ratificata |
|---|---|---|
| `create datatype` | nessuna race semantica rilevante | transazione + PK/UNIQUE/FK |
| `publish version` | precondizione `DRAFT` stale | conditional `UPDATE` / CAS |
| `create next version` | collisione su `max(version)+1` | `FOR UPDATE` sulla riga `datatypes(id)` prima del computo |
| `deprecate version` | precondizione locale `PUBLISHED` | conditional `UPDATE` / CAS |
| nuovo consumer di DV `PUBLISHED` | `PUBLISHED` può cambiare prima del commit del binding | `FOR SHARE` sulla exact `DataTypeVersion` |
| `revise version` | stale `DRAFT` + lost update | `FOR NO KEY UPDATE` sulla exact `DataTypeVersion` prima della lettura |
| `delete datatype` | riferimenti concorrenti | transazione + FK `RESTRICT`; nessun lock esplicito |

## 5. Principio risultante

La baseline DataType non introduce alcun locking globale.

```text
create
    -> constraint + transaction

publish
    -> CAS

create-next
    -> identity-row lock locale alla lineage

deprecate
    -> CAS

consumer di una versione PUBLISHED
    -> shared row lock sulla exact version

revise
    -> row lock sulla exact version

delete
    -> FK + transaction
```

La granularità della protezione deriva dall'invariante della singola operazione, non dall'appartenenza dell'oggetto a un generico "model-plane".

Quando un futuro consumer dovrà acquisire più lock contemporaneamente — ad esempio un `ObjectTemplate` che referenzia più `DataTypeVersion` — l'ordine deterministico di acquisizione dei lock dovrà essere definito nell'analisi di quella specifica operazione consumer.
