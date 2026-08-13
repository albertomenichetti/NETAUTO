# Object Rename — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `rename Object`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application
- invarianti di rename
- garanzie relazionali PostgreSQL
- race concorrenti
- protocollo transazionale
- atomicità mutation + audit
```

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
```

Nessun locking globale del model-plane o cross-plane viene introdotto.

---

# 2. Obiettivo dell'operazione

`rename Object` modifica esclusivamente:

```text
objects.canonical_name
```

della exact Object row identificata da:

```text
objects.id
```

e produce atomicamente:

```text
object_changes
kind = RENAME
```

Non modifica:

```text
id
template_id
template_version
properties_json
object_components
```

---

# 3. Precondizioni Domain

La request deve fornire esplicitamente:

```text
new canonical_name
```

Regole:

```text
new canonical_name omitted
    -> invalid

new canonical_name == ""
    -> invalid

new canonical_name non-empty
    -> valid candidate
```

Il fallback:

```text
canonical_name omitted
-> str(id)
```

appartiene esclusivamente a `create Object` e NON si applica a `rename Object`.

`canonical_name` non è UNIQUE.

Due Object distinti possono quindi condividere lo stesso canonical name.

---

# 4. Race fondamentale: rename vs rename

Scenario senza coordinamento:

```text
initial:
    canonical_name = A

T1                           T2

READ A                       READ A

candidate B                  candidate C

UPDATE B
audit A -> B
COMMIT

                             UPDATE C
                             audit A -> C
                             COMMIT
```

Lo stato finale:

```text
canonical_name = C
```

può sembrare valido, ma l'audit di T2 sarebbe semanticamente falso.

La transizione reale sarebbe infatti:

```text
B -> C
```

non:

```text
A -> C
```

Il requisito concorrente non è quindi soltanto evitare un lost update.

È necessario garantire:

> ogni mutation costruisce il proprio `before` snapshot dallo stato corrente effettivamente serializzato dell'Object.

---

# 5. Exact Object row come state gate

La risorsa naturale è:

```text
objects(id)
```

La rename deve acquisire:

```sql
SELECT ...
FROM objects
WHERE id = :object_id
FOR NO KEY UPDATE;
```

prima di leggere lo stato decisionale.

Solo dopo il lock vengono letti:

```text
canonical_name
template_id
template_version
properties_json
```

necessari per costruire il canonical `before` snapshot.

La exact Object row funge quindi da:

```text
Object state gate
```

per questa mutation.

---

# 6. Perché `FOR NO KEY UPDATE`

La rename modifica soltanto:

```text
canonical_name
```

e non modifica:

```text
objects.id
```

né altre key referenziate.

`FOR NO KEY UPDATE` è quindi più preciso di:

```text
FOR UPDATE
```

e sufficiente a serializzare le mutation del live Object state.

L'obiettivo è proteggere:

```text
current-state read
candidate derivation
before/after audit
```

senza introdurre un lock più forte del necessario.

---

# 7. Rename vs rename con state gate

Con il protocollo:

```text
initial:
    name = A

T1                           T2

FOR NO KEY UPDATE

                             FOR NO KEY UPDATE
                             WAIT

READ A
UPDATE B
audit A -> B
COMMIT

                             acquire
                             READ B
                             UPDATE C
                             audit B -> C
                             COMMIT
```

L'audit risultante è coerente:

```text
RENAME A -> B
RENAME B -> C
```

---

# 8. Regola candidata trasversale sul live Object state

La rename fa emergere una regola probabilmente condivisa da:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
```

Tutte queste operation:

```text
1. leggono current Object state
2. costruiscono una candidate
3. persistono un nuovo state
4. registrano before/after audit
```

La candidata regola generale è:

> qualsiasi mutation del live Object state che dipenda dal current state deve acquisire preventivamente `FOR NO KEY UPDATE` sulla exact Object row.

Questo documento ratifica la regola per `rename Object`.

L'estensione definitiva a `DATA_CHANGE` e `SCHEMA_CHANGE` verrà rivalutata nelle rispettive action.

---

# 9. Rename vs DATA_CHANGE

Se entrambe le mutation usano la exact Object row come state gate, gli ordini possibili restano semanticamente coerenti.

Esempio:

```text
initial:
    name=A
    properties=P0
```

Ordine 1:

```text
RENAME:
    A/P0 -> B/P0

DATA_CHANGE:
    B/P0 -> B/P1
```

Ordine 2:

```text
DATA_CHANGE:
    A/P0 -> A/P1

RENAME:
    A/P1 -> B/P1
```

Entrambi producono audit before/after corretti.

---

# 10. Rename vs SCHEMA_CHANGE

Una schema migration può modificare:

```text
template_id
template_version
properties_json
```

mentre rename modifica:

```text
canonical_name
```

Se entrambe leggessero lo stesso stale snapshot potrebbero produrre eventi audit incoerenti.

La serializzazione sulla exact Object row evita questo problema.

La rename non deve acquisire alcun lifecycle lock sulla ObjectTemplateVersion, perché non prende decisioni sullo schema.

---

# 11. Rename vs delete

La rename e la delete devono coordinarsi sulla stessa live Object row.

Possibili ordini semanticamente validi:

```text
rename wins
    -> rename commit
    -> delete sees renamed final state
```

oppure:

```text
delete wins
    -> Object no longer exists
    -> rename fails
```

Il protocollo concreto della delete sarà analizzato separatamente.

Non è necessario alcun lock aggiuntivo lato rename.

---

# 12. Rename vs attach/detach

La rename non modifica:

```text
template pin
ownership
slot compatibility
ownership graph
```

Il canonical Object snapshot ratificato non contiene gli attachment.

Quindi la rename non deve acquisire:

```text
ownership graph lock
slot lock
parent/child lock
```

solo perché l'Object partecipa a `object_components`.

`rename` e `attach/detach` possono restare indipendenti quando i rispettivi protocolli lo consentono.

---

# 13. Nessun lifecycle predicate esterno

La rename non crea un nuovo schema binding.

Un Object può essere pinnato a una ObjectTemplateVersion ormai:

```text
DEPRECATED
```

e deve comunque poter essere rinominato.

Non serve quindi:

```text
FOR SHARE exact OTV
verify PUBLISHED
```

e non servono lock su DataTypeVersion.

La FK esistente continua a garantire l'esistenza del pin.

---

# 14. Canonical before snapshot

Dopo aver acquisito il lock viene costruito:

```json
{
  "canonical_name": "old-name",
  "template_id": "...",
  "template_version": 3,
  "properties": {
    "...": "..."
  }
}
```

Questo snapshot rappresenta lo stato effettivamente corrente dell'Object prima della mutation.

---

# 15. Canonical after snapshot

La candidate after mantiene invariati:

```text
template_id
template_version
properties
```

e modifica esclusivamente:

```text
canonical_name
```

Esempio:

```json
{
  "canonical_name": "new-name",
  "template_id": "...",
  "template_version": 3,
  "properties": {
    "...": "..."
  }
}
```

---

# 16. Domain invariant di `RENAME`

Un audit event:

```text
kind = RENAME
```

significa:

> cambia esclusivamente `canonical_name`.

Devono rimanere invariati:

```text
id
template_id
template_version
properties
```

Questa è una garanzia Domain/Application.

Non viene introdotto un CHECK DB che confronti semanticamente i due JSON.

---

# 17. `object_changes.canonical_name`

Per un evento:

```text
RENAME
```

la colonna:

```text
object_changes.canonical_name
```

deve contenere:

```text
new canonical_name
```

e quindi coincide con:

```text
after_json.canonical_name
```

secondo la canonical snapshot semantics.

---

# 18. Rename verso lo stesso nome

Semantica ratificata:

```text
current canonical_name = X
requested canonical_name = X
```

produce:

```text
no-op idempotente
```

con:

```text
nessun UPDATE
nessun RENAME audit event
```

La decisione deve essere presa soltanto dopo aver acquisito l'Object state gate.

Questo evita race come:

```text
T1 rename A -> B
T2 rename -> B
```

dove T2, dopo aver atteso T1, osserva:

```text
current = B
requested = B
```

e diventa correttamente un no-op.

---

# 19. Mutation + audit atomicity

La mutation live e l'audit sono una singola unità semantica.

Non deve essere possibile committare:

```text
canonical_name modificato
senza RENAME audit
```

né:

```text
RENAME audit
senza mutation live
```

Protocollo:

```text
BEGIN

lock Object

build before

UPDATE canonical_name

build after

INSERT object_changes RENAME

COMMIT
```

Se l'audit insert fallisce:

```text
ROLLBACK
```

dell'intera rename.

---

# 20. Protocollo transazionale candidato

```text
BEGIN

1. validate requested canonical_name:
   - supplied
   - non-empty

2. SELECT exact Object
   FOR NO KEY UPDATE

3. if Object missing:
       fail

4. read current full Object state

5. if requested name == current name:
       no-op
       no UPDATE
       no audit
       COMMIT / return unchanged

6. build canonical before snapshot

7. build candidate:
   same:
       id
       template_id
       template_version
       properties_json

   changed:
       canonical_name

8. UPDATE objects
   SET canonical_name = :new_name
   WHERE id = :object_id

9. build canonical after snapshot

10. INSERT object_changes:
    kind           = RENAME
    object_id      = object id
    canonical_name = new canonical_name
    before_json    = before snapshot
    after_json     = after snapshot

11. COMMIT
```

Qualsiasi failure produce:

```text
ROLLBACK
```

---

# 21. Lock non richiesti

`rename Object` non richiede:

```text
FOR SHARE ObjectTemplateVersion
```

Non richiede:

```text
FOR SHARE DataTypeVersion
```

Non richiede:

```text
ownership graph lock
```

Non richiede:

```text
parent/child attachment lock
```

Non richiede:

```text
ObjectTemplate lineage lock
```

L'unico lock applicativo esplicito richiesto è:

```text
FOR NO KEY UPDATE
sulla exact Object row
```

---

# 22. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
new canonical_name supplied

new canonical_name non-empty

RENAME changes only canonical_name

same-name rename is idempotent no-op

canonical before/after snapshot semantics

RENAME audit semantics
```

## PostgreSQL / relational model

Garantisce:

```text
Object identity
    -> PRIMARY KEY

canonical_name non-empty
    -> CHECK

Object row serialization
    -> row locking

audit structural consistency
    -> object_changes CHECK constraints

atomicity
    -> single PostgreSQL transaction
```

## Concurrency protocol

Garantisce:

```text
current-state read non-stale

rename vs rename serialization

coherent before/after audit

serialization with other live-state mutations
when they adopt the same Object state gate
```

---

# 23. Verdetto DRAFT

> **Rename Object è una mutation locale della exact Object row.**
>
> Prima di leggere il current state deve acquisire:
>
> ```text
> FOR NO KEY UPDATE
> ```
>
> sulla exact `objects(id)` row.
>
> Il lock protegge:
>
> ```text
> current-state decision
> no lost semantic update
> coherent before/after audit
> serialization with other live-state mutations
> ```
>
> `canonical_name` non è unique e non richiede coordinamento globale.
>
> Un rename verso il nome già corrente è un no-op idempotente senza audit event.
>
> `UPDATE objects.canonical_name` e `INSERT object_changes(RENAME)` devono essere committati atomicamente nella stessa transazione.
>
> Non sono necessari lock su ObjectTemplateVersion, DataTypeVersion o ownership graph.
>
> Nessun locking globale viene introdotto.
