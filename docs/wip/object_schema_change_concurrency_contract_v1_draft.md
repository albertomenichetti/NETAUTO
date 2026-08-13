# Object SCHEMA_CHANGE — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `SCHEMA_CHANGE`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application
- invarianti di schema migration
- garanzie relazionali PostgreSQL
- race concorrenti
- protocollo transazionale
- compatibilità con ownership attachments
- atomicità mutation + audit
```

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
Object Create — Concurrency Contract DRAFT v1
Object Rename — Concurrency Contract DRAFT v1
Object DATA_CHANGE — Concurrency Contract DRAFT v1
```

Nessun locking globale del model-plane o cross-plane viene introdotto.

---

# 2. Obiettivo dell'operazione

`SCHEMA_CHANGE` modifica atomicamente:

```text
objects.template_id
objects.template_version
objects.properties_json
```

e produce:

```text
object_changes
kind = SCHEMA_CHANGE
```

Devono rimanere invariati:

```text
id
canonical_name
```

`SCHEMA_CHANGE` non modifica implicitamente:

```text
object_components
```

Una migration incompatibile con attachment esistenti deve quindi fallire.

La remediation esplicita è:

```text
detach
SCHEMA_CHANGE
eventuale attach
```

---

# 3. Target ObjectTemplateVersion resolution

La target OTV può essere richiesta in due modalità.

## 3.1 Exact target

Input:

```text
target_template_id = T
target_template_version = V
```

La exact target deve:

```text
exist
be PUBLISHED
```

e viene stabilizzata con:

```text
FOR SHARE
```

fino al commit.

## 3.2 Version omessa

Input:

```text
target_template_id = T
target_template_version = omitted
```

Il dominio risolve:

> la version numericamente più alta tra tutte e sole le ObjectTemplateVersion `PUBLISHED` della target lineage.

La selected exact OTV viene stabilizzata:

```text
FOR SHARE
```

fino al commit.

La semantica è:

```text
highest PUBLISHED at resolution/admission
```

non:

```text
highest PUBLISHED at COMMIT
```

Una volta risolta, la target diventa sempre:

```text
exact (template_id, template_version)
```

---

# 4. Same-pin no-op

Se la target exact coincide già con il current pin:

```text
current = T/v3
target  = T/v3
```

non esiste alcun reale `SCHEMA_CHANGE`.

Semantica ratificata:

```text
no-op
no UPDATE
no audit
```

Questo vale anche se la current exact OTV è ormai:

```text
DEPRECATED
```

perché non viene creato alcun nuovo binding.

In exact mode non deve essere richiesto che la same current OTV torni `PUBLISHED`.

---

# 5. Exact Object row come schema gate

`SCHEMA_CHANGE` deve iniziare con:

```sql
SELECT ...
FROM objects
WHERE id = :object_id
FOR UPDATE;
```

prima di qualsiasi decision read.

La exact Object row protegge:

```text
current live state
current template pin
schema migration decision
before/after audit
coordination with concurrent attach
```

---

# 6. Perché `FOR UPDATE`

`RENAME` e `DATA_CHANGE` usano:

```text
FOR NO KEY UPDATE
```

perché modificano live state senza modificare il template pin.

`SCHEMA_CHANGE` modifica invece:

```text
template_id
template_version
```

che determinano:

```text
effective slots
child compatibility
incoming attachment compatibility
```

Per questo viene adottato:

```text
FOR UPDATE
```

come Object schema gate.

Questo crea una distinzione ratificata:

```text
RENAME
DATA_CHANGE
    -> FOR NO KEY UPDATE

SCHEMA_CHANGE
    -> FOR UPDATE
```

---

# 7. Reciprocal contract atteso per `attach`

Il protocollo di `SCHEMA_CHANGE` richiede che una futura `attach` stabilizzi gli endpoint con un lock compatibile con:

```text
RENAME
DATA_CHANGE
```

ma incompatibile con:

```text
SCHEMA_CHANGE
DELETE
```

Il candidato ratificato da verificare formalmente nell'action `attach` è:

```text
FOR KEY SHARE parent Object
FOR KEY SHARE child Object
```

Questo perché:

```text
FOR KEY SHARE
    does not conflict with
FOR NO KEY UPDATE
```

ma:

```text
FOR KEY SHARE
    conflicts with
FOR UPDATE
```

Quindi:

```text
attach
```

può restare concorrente con rename/data changes, ma non con una schema migration che coinvolga uno dei due endpoint.

---

# 8. Perché il solo Object schema gate non basta

Un Object può essere:

```text
parent di uno o più children
```

e/o:

```text
child di un parent
```

Una modifica del template pin può invalidare relazioni già persistite.

Esempio outgoing:

```text
Parent P
slot "interfaces"
    -> Child C
```

Se il target schema di P:

```text
rimuove slot "interfaces"
```

oppure cambia il relativo target in modo incompatibile con C, l'attachment diventerebbe invalido.

Esempio incoming:

```text
Parent P / slot S -> Object X
```

Se X migra verso una template lineage non compatibile con `S.target_template_id`, l'attachment diventerebbe invalido.

---

# 9. Outgoing attachment invariant

Per ogni row:

```text
object_components.parent_object_id = X
```

la migration di X deve verificare contro il target effective schema:

```text
slot_name still exists as an effective slot
```

e:

```text
child.template_id
compatible with
slot.target_template_id
```

Se uno slot occupato non esiste più:

```text
SCHEMA_CHANGE FAIL
```

Se un child esistente non è più compatibile:

```text
SCHEMA_CHANGE FAIL
```

Non viene eseguito alcun detach implicito.

---

# 10. Incoming attachment invariant

Dato che:

```text
PRIMARY KEY(child_object_id)
```

può esistere al massimo una incoming attachment row.

Se esiste:

```text
P / slot S -> X
```

la candidate target template di X deve restare compatibile con:

```text
effective slot S
```

del current schema di P.

Se la compatibilità non è preservata:

```text
SCHEMA_CHANGE FAIL
```

---

# 11. Race fondamentale: parent e child migrano insieme

Scenario:

```text
P -> C
```

T1 migra P.

T2 migra C.

Senza un coordination point comune:

```text
T1:
    validates new P against old C

T2:
    validates new C against old P
```

ma il risultato finale:

```text
new P + new C
```

potrebbe essere incompatibile.

Questo è un write skew.

Il solo:

```text
FOR UPDATE sulla propria Object row
```

non basta perché T1 e T2 possono lockare due Object rows differenti.

---

# 12. `object_components` row come attachment compatibility gate

La row:

```text
object_components(parent_object_id, slot_name, child_object_id)
```

rappresenta esattamente l'invariante condiviso tra:

```text
parent schema
slot
child schema
```

Ogni `SCHEMA_CHANGE` deve quindi acquisire le proprie current incident attachment rows:

```sql
SELECT ...
FROM object_components
WHERE parent_object_id = :object_id
   OR child_object_id = :object_id
ORDER BY child_object_id
FOR NO KEY UPDATE;
```

Il lock viene mantenuto fino al commit.

Queste rows fungono da:

```text
attachment compatibility gates
```

---

# 13. Perché `FOR NO KEY UPDATE` sulle relation rows

La migration non deve modificare le `object_components` rows.

Deve però impedire che due schema mutation concorrenti sullo stesso edge validino contro due stati reciproci ormai stale.

`FOR NO KEY UPDATE` è sufficiente come lock esclusivo rispetto a un'altra acquisition equivalente e rispetto al delete della relation row.

Non viene introdotto un graph-wide lock.

---

# 14. Parent/child concurrent schema changes

Con:

```text
P -> C
```

T1:

```text
FOR UPDATE P
FOR NO KEY UPDATE edge P-C
```

T2:

```text
FOR UPDATE C
FOR NO KEY UPDATE edge P-C
```

solo una transaction può acquisire l'edge compatibility gate per prima.

L'altra attende.

La transaction che acquisisce successivamente l'edge deve leggere lo stato del related Object soltanto dopo l'acquisizione del gate.

Questo rende la seconda validation consapevole dell'eventuale schema change già committato dall'altra transaction.

---

# 15. Nessun lock aggiuntivo sui related Object

Dopo aver acquisito l'incident edge gate, lo schema corrente del related Object viene letto normalmente.

Non viene acquisito:

```text
FOR SHARE related Object
```

né un altro row lock sul related endpoint.

Motivazione:

```text
- l'edge row è il coordination point condiviso
- lock aggiuntivi sugli endpoint potrebbero creare deadlock inutili
```

Il protocollo deve rispettare:

> nessun UPDATE dell'Object in schema migration prima di aver acquisito tutti gli attachment compatibility gates rilevanti.

---

# 16. Canonical ordering delle incident edge rows

Se un Object ha più incident attachments, tutte le relevant rows devono essere acquisite in ordine canonico.

Baseline:

```text
ORDER BY child_object_id
```

o altro ordinamento totale equivalente stabilito dall'implementazione.

L'obiettivo è ridurre il rischio di deadlock tra migration concorrenti che condividono più edge.

La scelta tecnica finale dell'ordering key può essere affinata, ma deve rimanere deterministica e canonica.

---

# 17. Concurrent attach e phantom edges

Una nuova attachment row non esiste ancora e quindi non può essere protetta dal lock sulle current incident rows.

Per impedire che un attach inserisca un nuovo incident edge durante una schema migration, `SCHEMA_CHANGE` usa:

```text
FOR UPDATE own Object
```

Il reciprocal contract richiesto a `attach` è:

```text
FOR KEY SHARE parent Object
FOR KEY SHARE child Object
```

prima della compatibility validation e dell'INSERT.

Quindi:

```text
SCHEMA_CHANGE wins
    -> attach waits
    -> after commit validates new schema
```

oppure:

```text
attach wins
    -> attach commits
    -> SCHEMA_CHANGE scans and sees new edge
```

Questo elimina il phantom semanticamente rilevante senza graph-wide locking.

---

# 18. Concurrent detach

Per una existing edge row:

```text
SCHEMA_CHANGE
    -> FOR NO KEY UPDATE edge
```

confligge con il `DELETE` della row eseguito da `detach`.

Se detach vince:

```text
edge disappears
-> migration no longer needs to validate it
```

Se schema change vince:

```text
detach waits
-> migration validates against the still-existing edge
```

Entrambi gli ordini sono coerenti.

---

# 19. Stabilità dell'insieme incident edges

Il combination contract è:

```text
own Object FOR UPDATE
+
current incident edges FOR NO KEY UPDATE
```

con il futuro reciprocal protocol di `attach`.

Questo garantisce che durante la decisione di migration:

```text
- non entrino nuovi incident edges
- gli edge esistenti non cambino/disappaiano senza serializzazione
```

senza introdurre un lock sul grafo completo.

---

# 20. Target OTV lifecycle

La target exact OTV rappresenta un nuovo binding.

Deve quindi:

```text
exist
be PUBLISHED
```

e viene acquisita:

```text
FOR SHARE
```

fino al commit.

Questo protegge:

```text
PUBLISHED admission-time consistency
```

rispetto a:

```text
PUBLISHED -> DEPRECATED
```

Se la target viene deprecata dopo il commit, l'Object già migrato resta valido.

---

# 21. Current/source OTV lifecycle

La current OTV è un binding già esistente.

Può essere:

```text
PUBLISHED
DEPRECATED
```

e non richiede una nuova lifecycle admission.

La composite FK da `objects` garantisce che la current exact OTV esista fino alla conclusione della migration.

Non serve:

```text
FOR SHARE current OTV
```

per il lifecycle predicate.

---

# 22. Target dependencies già incorporate

La target `PUBLISHED` OTV è uno schema certificato.

Le exact dependency già incorporate:

```text
ancestor OTV
DataTypeVersion
```

possono essere ormai:

```text
DEPRECATED
```

senza rendere invalida la target OTV.

Non sono richiesti:

```text
FOR SHARE ancestor OTV
FOR SHARE DTV
require dependency status == PUBLISHED
```

Il nuovo direct lifecycle binding è soltanto:

```text
Object -> target exact OTV
```

---

# 23. Abstract target template

La target template lineage deve essere instantiable.

Quindi:

```text
ObjectTemplate.abstract == FALSE
```

Se la target è abstract:

```text
SCHEMA_CHANGE FAIL
```

---

# 24. Migration candidate

La migration deve costruire una complete candidate:

```text
current locked Object
+
current effective schema
+
target effective schema
=
migrated candidate properties
```

Il dettaglio completo del mapping algorithm può essere raffinato separatamente.

Il concurrency contract richiede però che:

```text
- la source sia il current locked Object state
- il target schema sia la selected exact OTV
- la candidate venga costruita nella stessa transaction
- la candidate finale venga validata integralmente
```

---

# 25. `migration_default`

Regola già ratificata:

```text
migration_default
!= create-time default
```

Durante `SCHEMA_CHANGE`, se una target required property non ha un usable carried-forward value:

```text
use migration_default
```

secondo le migration semantics ratificate.

Ogni migration default effettivamente usato contribuisce alla complete candidate finale, che deve comunque essere validata contro la target exact DTV.

---

# 26. Complete target validation

Indipendentemente da come viene costruita, la migrated candidate finale deve soddisfare integralmente il target effective schema:

```text
no unknown properties

every required property present

every present value valid
against target exact DataTypeVersion
```

Non serve un ulteriore lifecycle lock sulle DTV perché le exact DTV incorporate sono strutturalmente immutabili.

---

# 27. Outgoing attachment validation

Per ogni locked row:

```text
X / slot S -> C
```

la migration deve:

```text
1. verify effective slot S exists
   in target schema of X

2. read C current template pin
   after edge gate acquisition

3. verify:
   C.template_id
   compatible with
   S.target_template_id
```

Se una di queste condizioni fallisce:

```text
SCHEMA_CHANGE FAIL
```

---

# 28. Incoming attachment validation

Se esiste:

```text
P / slot S -> X
```

la migration deve:

```text
1. read P current template pin
   after edge gate acquisition

2. resolve effective slot S of P

3. verify:
   candidate X.template_id
   compatible with
   S.target_template_id
```

Se fallisce:

```text
SCHEMA_CHANGE FAIL
```

---

# 29. Exact semantics di compatibility

La regola:

```text
child.template_id
compatible with
slot.target_template_id
```

è già un invariante ratificato del modello Object.

La definizione tecnica esatta di `compatible` non viene fissata in questo documento.

Deve essere ratificata nell'action primaria:

```text
attach Object
```

e poi riutilizzata identicamente da:

```text
SCHEMA_CHANGE
```

Il concurrency protocol descritto qui non dipende dalla specifica definizione di compatibility.

---

# 30. Nessuna mutation implicita del graph

`SCHEMA_CHANGE` non deve:

```text
detach
reattach
move
delete attachment rows
```

automaticamente.

Se il target schema rende invalido un existing attachment:

```text
FAIL
```

La modifica del graph deve essere effettuata tramite action esplicite separate.

---

# 31. SCHEMA_CHANGE vs RENAME

Lock:

```text
SCHEMA_CHANGE
    -> FOR UPDATE Object

RENAME
    -> FOR NO KEY UPDATE Object
```

Le due operation vengono serializzate sulla same Object row.

Quindi gli audit snapshot descrivono stati realmente consecutivi.

---

# 32. SCHEMA_CHANGE vs DATA_CHANGE

Lock:

```text
SCHEMA_CHANGE
    -> FOR UPDATE Object

DATA_CHANGE
    -> FOR NO KEY UPDATE Object
```

Le due operation vengono serializzate.

Se DATA_CHANGE vince:

```text
migration uses the updated properties as source
```

Se SCHEMA_CHANGE vince:

```text
DATA_CHANGE reads the new template pin
and validates against the new schema
```

Questo evita stale schema validation.

---

# 33. Canonical before snapshot

Dopo aver stabilizzato il live Object state viene costruito:

```json
{
  "canonical_name": "...",
  "template_id": "old-template",
  "template_version": 2,
  "properties": {
    "...": "old"
  }
}
```

Questo rappresenta la source reale della migration.

---

# 34. Canonical after snapshot

L'after snapshot contiene:

```text
same canonical_name
target template_id
target template_version
migrated properties
```

Esempio:

```json
{
  "canonical_name": "...",
  "template_id": "new-template",
  "template_version": 3,
  "properties": {
    "...": "migrated"
  }
}
```

---

# 35. Domain invariant di `SCHEMA_CHANGE`

Un evento:

```text
kind = SCHEMA_CHANGE
```

significa:

```text
before.canonical_name == after.canonical_name

(before.template_id, before.template_version)
    !=
(after.template_id, after.template_version)
```

Le properties:

```text
may change
or
may remain semantically equal
```

Un cambio di exact schema pin è sufficiente a giustificare l'event kind.

---

# 36. `object_changes.canonical_name`

Per:

```text
SCHEMA_CHANGE
```

la colonna:

```text
object_changes.canonical_name
```

contiene il canonical name corrente.

Dato che SCHEMA_CHANGE non rinomina:

```text
before.canonical_name
=
after.canonical_name
=
object_changes.canonical_name
```

---

# 37. Mutation + audit atomicity

La migration live e il relativo audit sono una singola unità semantica.

Devono essere committati atomicamente:

```text
UPDATE objects:
    template_id
    template_version
    properties_json

+

INSERT object_changes SCHEMA_CHANGE
```

Se:

```text
target validation fails
attachment validation fails
audit insert fails
```

l'intera operation deve:

```text
ROLLBACK
```

senza modificare live Object o ownership graph.

---

# 38. Protocollo transazionale candidato

```text
BEGIN

1. SELECT exact Object
   FOR UPDATE

2. if Object missing:
       FAIL

3. read current complete Object state

4. resolve requested target

   exact target:
       if exact target == current exact pin:
           no-op
           no UPDATE
           no audit
           COMMIT / return unchanged

       otherwise:
           SELECT exact target OTV FOR SHARE
           require exists
           require PUBLISHED

   version omitted:
       SELECT highest PUBLISHED target OTV
       ORDER BY version DESC
       LIMIT 1
       FOR SHARE

       require at least one PUBLISHED

       if selected exact target == current pin:
           no-op
           no UPDATE
           no audit
           COMMIT / return unchanged

5. require target template:
   abstract == FALSE

6. acquire all current incident
   object_components rows
   FOR NO KEY UPDATE
   in canonical order

7. resolve current effective schema

8. resolve target effective schema

9. build complete migrated properties candidate

10. validate complete target candidate

11. validate every outgoing attachment:
    - target effective slot exists
    - child current template compatible

12. validate incoming attachment if any:
    - current parent effective slot exists
    - candidate target template compatible

13. build canonical before snapshot

14. UPDATE objects:
    template_id      = target template_id
    template_version = target version
    properties_json  = migrated candidate

15. build canonical after snapshot

16. INSERT object_changes:
    kind           = SCHEMA_CHANGE
    object_id      = Object id
    canonical_name = unchanged current name
    before_json    = before snapshot
    after_json     = after snapshot

17. COMMIT
```

Qualsiasi failure produce:

```text
ROLLBACK
```

---

# 39. Lock picture

## Own Object row

```text
FOR UPDATE
```

Protegge:

```text
current state
current schema pin
schema mutation
coordination with attach
serialization with rename/data change
```

## Target exact OTV

```text
FOR SHARE
```

Protegge:

```text
PUBLISHED admission
```

## Incident object_components rows

```text
FOR NO KEY UPDATE
```

Proteggono:

```text
parent/child schema compatibility
schema_change vs schema_change
schema_change vs detach
```

## Related Object rows

```text
ordinary read after edge gate
```

Nessun additional row lock richiesto.

---

# 40. Lock non richiesti

`SCHEMA_CHANGE` non richiede:

```text
global ownership graph lock
```

Non richiede:

```text
model-plane global guard
```

Non richiede:

```text
FOR SHARE ancestor OTV
```

Non richiede:

```text
FOR SHARE target DTV
```

Non richiede:

```text
FOR SHARE related Object endpoints
```

Il coordinamento rimane locale alle rows direttamente rilevanti per la migration.

---

# 41. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
target exact vs implicit-latest semantics

same-pin no-op

target must be instantiable

migration candidate construction

migration_default semantics

complete candidate validation

outgoing attachment compatibility

incoming attachment compatibility

no implicit graph mutation

canonical before/after snapshots

SCHEMA_CHANGE audit semantics
```

## PostgreSQL / relational model

Garantisce:

```text
Object identity
    -> PRIMARY KEY

current exact OTV existence
    -> composite FK

target exact OTV existence after UPDATE
    -> composite FK

referenced OTV cannot be deleted while Object exists
    -> ON DELETE RESTRICT

Object row serialization
    -> FOR UPDATE

incident edge serialization
    -> row locks

audit structural consistency
    -> object_changes CHECK constraints

atomicity
    -> single PostgreSQL transaction
```

## Concurrency protocol

Garantisce:

```text
SCHEMA_CHANGE vs RENAME serialization

SCHEMA_CHANGE vs DATA_CHANGE serialization

SCHEMA_CHANGE vs SCHEMA_CHANGE on same Object serialization

parent/child concurrent schema changes coordinated via shared edge gate

new attach cannot enter while endpoint schema changes
once attach adopts reciprocal FOR KEY SHARE protocol

detach races serialize on existing edge rows

candidate validated against stable target admission

coherent before/after audit
```

---

# 42. Verdetto DRAFT

> **SCHEMA_CHANGE è una mutation del live Object state che modifica anche il template pin e quindi richiede `FOR UPDATE` sulla exact Object row.**
>
> La target exact ObjectTemplateVersion rappresenta una nuova admission e deve essere `PUBLISHED`, stabilizzata `FOR SHARE` fino al commit. La versione può essere exact oppure risolta come highest `PUBLISHED` della target lineage al momento dell'admission.
>
> Se la target exact coincide già con il current pin, l'operation è un no-op senza audit, anche se la current OTV è ormai `DEPRECATED`.
>
> Gli existing attachment costituiscono invarianti concorrenti condivisi. Tutte le current incident `object_components` rows vengono quindi acquisite `FOR NO KEY UPDATE` e fungono da attachment compatibility gates.
>
> Questo elimina il write skew tra schema migration concorrenti di parent e child senza introdurre un graph-wide lock.
>
> La migration deve preservare ogni existing attachment. Se un target schema rimuove uno slot occupato, rende incompatibile un child esistente, oppure rende l'Object incompatibile con il proprio parent slot, `SCHEMA_CHANGE` fallisce.
>
> Nessun detach/reattach viene eseguito implicitamente.
>
> Il reciprocal contract richiesto al futuro `attach` è stabilizzare parent e child con `FOR KEY SHARE`, così da restare concorrente con `RENAME`/`DATA_CHANGE` ma essere serializzato con `SCHEMA_CHANGE`.
>
> Current/source OTV e dependency storiche possono essere `DEPRECATED`; non richiedono nuova lifecycle admission.
>
> `UPDATE objects(template_id, template_version, properties_json)` e `INSERT object_changes(SCHEMA_CHANGE)` devono essere committati atomicamente nella stessa transazione.
>
> Nessun locking globale viene introdotto.
