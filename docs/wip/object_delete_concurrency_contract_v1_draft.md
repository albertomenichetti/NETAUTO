# Object DELETE — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `delete Object`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application
- subtree deletion semantics
- garanzie relazionali PostgreSQL
- race concorrenti
- recursive subtree stabilization
- protocollo transazionale
- audit DELETED
- atomicità dell'intera subtree deletion
```

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
Object ATTACH — Concurrency Contract DRAFT v1
Object DETACH — Concurrency Contract DRAFT v1
Object RENAME — Concurrency Contract DRAFT v1
Object DATA_CHANGE — Concurrency Contract DRAFT v1
Object SCHEMA_CHANGE — Concurrency Contract DRAFT v1
```

Nessun ownership graph global lock viene introdotto.

---

# 2. Obiettivo dell'operazione

Dato:

```text
delete Object X
```

l'operation elimina atomicamente:

```text
X
+
tutti i descendants attualmente owned da X
```

seguendo le current:

```text
object_components
```

rows.

La delete non elimina l'owner del root.

Esempio:

```text
A
├── B
│   ├── D
│   └── E
└── C
```

`delete A` elimina:

```text
D
E
B
C
A
```

`delete B` elimina:

```text
D
E
B
```

ma non elimina:

```text
A
```

---

# 3. Owned component delete semantics

Se il requested root è a sua volta owned:

```text
A -> B
```

e viene richiesto:

```text
delete B
```

l'operation:

```text
- rimuove l'incoming edge A -> B
- elimina B
- elimina tutti i descendants di B
- preserva A
```

Questa semantica è distinta da una delete del parent owner.

---

# 4. Current subtree semantics

Il subtree da eliminare è quello che appartiene al root secondo il graph ownership rilevante per l'ordine seriale dell'operation.

Esempio:

```text
A -> B
```

Se prima viene completato:

```text
detach A/B
```

e poi:

```text
delete A
```

B deve sopravvivere.

Se invece la delete stabilizza il branch:

```text
A -> B
```

prima del detach concorrente, B fa parte del subtree eliminato.

La semantics richiesta è quindi serializzabile:

```text
detach before delete
    -> detached branch survives

delete before detach
    -> branch is deleted
```

---

# 5. Cosa viene scritto

Per un subtree di N Objects, l'operation modifica:

```text
object_components
    -> delete internal subtree edges
    -> delete possible incoming edge of root

objects
    -> delete N Object rows

object_changes
    -> insert N DELETED events
```

Ogni Object eliminato produce il proprio audit storico.

---

# 6. Nessun cascade ownership implicito

Le FK:

```text
object_components.parent_object_id -> objects.id RESTRICT
object_components.child_object_id  -> objects.id RESTRICT
```

non implementano automaticamente la subtree deletion.

La subtree semantics appartiene alla workflow applicativa.

L'application service deve quindi:

```text
discover subtree
stabilize subtree
remove ownership edges
delete Object rows
write DELETED audit events
```

nella stessa transaction.

---

# 7. Perché un semplice recursive SELECT non basta

Scenario:

```text
A
└── B
```

T1:

```text
delete A
```

T2:

```text
attach A -> C
```

Se T1 esegue soltanto un recursive read e vede:

```text
A,B
```

T2 potrebbe inserire:

```text
A -> C
```

prima della mutation finale.

La subtree membership letta da T1 non sarebbe più sufficientemente stabile.

Lo stesso problema esiste rispetto a:

```text
detach
concurrent subtree delete
```

La delete deve quindi proteggere un recursive multi-row predicate:

```text
current descendants of requested root
```

---

# 8. Transaction isolation ratificata

`delete Object` deve essere eseguita in una PostgreSQL transaction:

```text
SERIALIZABLE
```

La transaction contiene:

```text
recursive subtree discovery
corruption/cycle validation
Object row locking
ownership edge locking
snapshot collection
edge deletion
Object deletion
DELETED audit insertion
```

Un'esecuzione che non può essere serializzata deve abortire con:

```text
SQLSTATE 40001
```

e l'intera action deve essere ritentata.

---

# 9. Specialized Unit of Work

`delete Object` è un caso naturale per una UoW specializzata.

Forma concettuale:

```text
ObjectDeleteUnitOfWork
    isolation = SERIALIZABLE
    retry whole action on SQLSTATE 40001
```

La UoW non contiene business logic.

Deve codificare esclusivamente:

```text
transaction boundary
isolation level
retry contract
```

La business logic di subtree discovery, ordering, snapshot e delete resta nel service/domain workflow.

---

# 10. Whole-action retry

Su:

```text
SQLSTATE 40001
```

non deve essere ritentato soltanto:

```text
DELETE
```

o soltanto:

```text
COMMIT
```

Il retry deve ripartire da:

```text
BEGIN
```

e rieseguire:

```text
root lookup
subtree discovery
cycle detection
Object locking
edge locking
snapshot collection
edge deletion
Object deletion
audit insertion
```

perché il graph potrebbe essere cambiato.

---

# 11. Discovery completa prima delle mutation

Regola ratificata:

> l'intero subtree deve essere scoperto prima della prima mutation persistente.

Prima di:

```text
DELETE edge
DELETE Object
INSERT DELETED audit
```

devono già essere completati:

```text
recursive subtree discovery
graph corruption detection
delete ordering derivation
Object row stabilization
edge stabilization
final snapshot collection
```

I lock non sono considerati mutation di dominio.

---

# 12. Corrupt ownership cycle

Anche se `ATTACH` deve impedire la creazione di nuovi cicli, la delete deve rimanere difensiva rispetto a dati corrotti.

Se durante la discovery viene rilevato:

```text
A -> B -> C -> A
```

la delete deve:

```text
FAIL
ROLLBACK
```

prima di qualsiasi mutation persistente.

Non deve esistere una partial subtree delete in presenza di corruption.

---

# 13. Candidate subtree

La recursive discovery produce almeno:

```text
root Object id
all descendant Object ids
ownership relationships traversed
post-order delete ordering
```

Il candidate set può essere rappresentato concettualmente come:

```text
S = {O1, O2, ..., On}
```

---

# 14. Canonical Object row locking

Dopo la discovery, tutte le candidate subtree Object rows devono essere acquisite:

```sql
SELECT ...
FROM objects
WHERE id IN (...)
ORDER BY id
FOR UPDATE;
```

L'ordine deve essere canonico e deterministico.

Baseline:

```text
ORDER BY objects.id
```

La lock order non segue quindi l'ordine topologico parent/child.

---

# 15. Perché canonical Object-id order

`ATTACH` acquisisce parent/child Object rows in canonical Object-id order:

```text
FOR KEY SHARE
ORDER BY id
```

Se delete acquisisse rows:

```text
parent first
then child
```

si potrebbero creare lock-order inversi tra attach e delete.

La delete deve quindi:

```text
discover first
lock all candidate Object rows in canonical id order
```

evitando di codificare l'ownership traversal order nell'ordine dei lock.

---

# 16. Perché `FOR UPDATE` sulle subtree Object rows

La delete deve congelare il full live state di ogni Object che verrà eliminato.

Questo include:

```text
canonical_name
template_id
template_version
properties_json
```

Il lock deve serializzare la delete con:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
ATTACH involving stabilized endpoint
```

`FOR UPDATE` è quindi il lock appropriato.

---

# 17. Reciprocal lock matrix

Le action già ratificate usano:

```text
RENAME
DATA_CHANGE
    -> FOR NO KEY UPDATE

SCHEMA_CHANGE
    -> FOR UPDATE

ATTACH
    -> FOR KEY SHARE endpoints

DELETE
    -> FOR UPDATE subtree Objects
```

Quindi delete viene serializzata correttamente con tutte le live-state/schema-affecting mutations rilevanti.

---

# 18. ATTACH vs DELETE

Se delete ha già stabilizzato un subtree Object:

```text
FOR UPDATE
```

un attach che richiede:

```text
FOR KEY SHARE
```

sullo stesso endpoint deve attendere.

Dopo il commit della delete:

```text
endpoint missing
-> ATTACH FAIL
```

Se attach committa prima della stabilizzazione della delete, il nuovo edge deve appartenere al graph che la delete deve considerare secondo l'ordine seriale.

`SERIALIZABLE` protegge la finestra fra recursive discovery e stabilizzazione.

---

# 19. Phantom child attach durante discovery

Scenario iniziale:

```text
A -> B
```

Delete legge:

```text
subtree = {A,B}
```

ma un concurrent attach inserisce:

```text
A -> C
```

Se l'ordine seriale è:

```text
attach
then delete
```

la delete deve includere C.

Se la current execution aveva già letto un predicate incompatibile con tale ordine, PostgreSQL può abortire:

```text
SQLSTATE 40001
```

Al retry:

```text
subtree = {A,B,C}
```

Questo evita una partial or stale subtree decision senza graph-wide lock.

---

# 20. Ownership edge stabilization

Dopo aver stabilizzato le candidate Object rows, la delete deve acquisire le relevant ownership rows.

Servono:

```text
all internal subtree edges
+
possible incoming edge of root
```

Le rows vengono acquisite:

```text
FOR NO KEY UPDATE
```

in canonical deterministic order.

Baseline possibile:

```text
ORDER BY child_object_id
```

---

# 21. Internal subtree edges

Sono internal edges tutte le rows:

```text
parent_object_id in subtree
AND
child_object_id in subtree
```

In un ownership forest valido, ogni outgoing edge di un subtree Object verso un child implica che il child appartenga al subtree.

Dopo stabilizzazione non deve esistere un outgoing edge da un subtree parent verso un Object escluso dal stabilized subtree.

Se emerge tale incongruenza:

```text
retry / fail
```

ma non partial delete.

---

# 22. Incoming edge del root

Il requested root può avere al massimo una incoming ownership edge:

```text
outside owner -> root
```

grazie a:

```text
PRIMARY KEY(child_object_id)
```

Questa edge deve essere inclusa nella stabilization e successivamente rimossa.

L'outside owner:

```text
survives
```

e non viene incluso nella subtree delete.

---

# 23. Nessun altro external incoming edge

Per ogni descendant diverso dal root, la sua unique incoming edge deve provenire da un parent interno al subtree.

Quindi, in una foresta valida:

```text
external incoming edges into subtree
=
0 or 1
```

e l'unica possibile external incoming edge è quella del root.

---

# 24. DETACH vs DELETE

Caso:

```text
A -> B
```

## Detach prima

```text
detach A/B
COMMIT
```

poi:

```text
delete A
```

non include B.

B sopravvive.

## Delete prima

Delete stabilizza:

```text
A
B
edge A/B
```

Il detach deve attendere o diventare stale rispetto alla delete.

Dopo il commit della delete, una exact:

```text
detach A/B
```

è un no-op.

---

# 25. `DETACH` non deve diventare SERIALIZABLE

`DETACH` rimuove edge e quindi è monotonicamente safe rispetto ad:

```text
acyclicity
subtree growth
```

Non può creare nuovi descendants.

La delete SERIALIZABLE + exact edge locking è sufficiente per coordinare il lato subtree predicate.

Non è necessario promuovere `DETACH` allo stesso isolation level.

---

# 26. DELETE vs DELETE stesso root

Due concurrent:

```text
delete X
```

competono sulle same subtree Object rows.

Una transaction può completare per prima.

L'altra, dopo retry/rilettura, può trovare:

```text
root missing
```

Semantica Domain ratificata:

```text
root missing
-> ObjectNotFound
```

Non viene prodotto un secondo `DELETED` event.

Una eventuale idempotenza HTTP è responsabilità dell'API layer, non del domain model.

---

# 27. DELETE ancestor vs DELETE descendant

Scenario:

```text
A
└── B
    └── C
```

T1:

```text
delete A
```

T2:

```text
delete B
```

Le candidate subtree si sovrappongono.

Il canonical Object-id locking evita ordini arbitrari di lock sulle rows condivise.

La SERIALIZABLE transaction garantisce che l'esito complessivo corrisponda a un ordine seriale valido.

Possibili risultati:

```text
delete B first
-> B,C removed
-> delete A retry sees only A
-> A removed
```

oppure:

```text
delete A first
-> A,B,C removed
-> delete B retry -> ObjectNotFound
```

Non deve esistere una partial overlapping delete incoerente.

---

# 28. DELETE vs RENAME

Delete usa:

```text
FOR UPDATE
```

Rename usa:

```text
FOR NO KEY UPDATE
```

sulla same Object row.

Le operation vengono serializzate.

Se rename vince:

```text
DELETED.before_json
```

deve contenere il renamed final state.

Se delete vince:

```text
Object disappears
-> rename cannot proceed
```

---

# 29. DELETE vs DATA_CHANGE

Delete usa:

```text
FOR UPDATE
```

DATA_CHANGE usa:

```text
FOR NO KEY UPDATE
```

Le operation vengono serializzate.

Se DATA_CHANGE vince:

```text
DELETED.before_json
```

contiene le final updated properties.

Se delete vince:

```text
DATA_CHANGE cannot proceed
```

---

# 30. DELETE vs SCHEMA_CHANGE

Entrambe usano:

```text
FOR UPDATE
```

sulla affected Object row.

Quindi sono serializzate.

Se schema change vince:

```text
DELETED.before_json
```

contiene il migrated final schema/data state.

Se delete vince:

```text
SCHEMA_CHANGE cannot proceed
```

---

# 31. Nessuna schema lifecycle validation

Delete non crea:

```text
new ObjectTemplateVersion binding
new DataTypeVersion binding
```

Non deve quindi:

```text
require OTV PUBLISHED
require DTV PUBLISHED
resolve target schema
validate current properties against schema
```

Può eliminare Object pinnati a:

```text
PUBLISHED OTV
DEPRECATED OTV
```

senza nuova lifecycle admission.

---

# 32. Final canonical snapshots

Dopo aver stabilizzato tutte le subtree Object rows, la delete costruisce per ogni Object il canonical final snapshot:

```json
{
  "canonical_name": "...",
  "template_id": "...",
  "template_version": 3,
  "properties": {
    "...": "..."
  }
}
```

Questo snapshot viene usato come:

```text
DELETED.before_json
```

---

# 33. Audit `DELETED`

Per ogni Object eliminato viene inserito:

```text
kind           = DELETED
object_id      = deleted Object id
canonical_name = last canonical name
before_json    = final canonical snapshot
after_json     = NULL
```

L'audit deve sopravvivere alla cancellazione della live row.

Questo è possibile perché:

```text
object_changes.object_id
```

non ha FK verso:

```text
objects.id
```

---

# 34. Un DELETED event per ogni Object

Per un subtree:

```text
A
├── B
└── C
```

la delete produce:

```text
DELETED(A)
DELETED(B)
DELETED(C)
```

Non soltanto:

```text
DELETED(A)
```

Ogni Object mantiene la propria audit history indipendente.

---

# 35. Descendants-before-parent order

L'ordine di eliminazione ratificato è:

```text
post-order
descendants-before-parent
```

Esempio:

```text
A
└── B
    └── C
```

ordine:

```text
C
B
A
```

Questo ordering è una semantica applicativa.

L'ordine dei row locks rimane invece canonical Object-id order.

Lock ordering e delete ordering non devono essere confusi.

---

# 36. Edge deletion

Dopo:

```text
complete discovery
Object locking
edge locking
snapshot collection
```

vengono rimosse:

```text
all internal subtree edges
possible incoming root edge
```

nella stessa transaction.

Solo dopo la rimozione delle ownership references vengono cancellate le Object rows secondo post-order.

---

# 37. External FK authority

La subtree delete non deve aggirare eventuali external references verso:

```text
objects.id
```

definite da altri domini.

Se esistono FK:

```text
SomeTable -> objects.id
ON DELETE RESTRICT
```

queste rimangono final consistency authority.

Pre-check applicativi possono migliorare la UX, ma sotto race la FK DB decide.

Non viene introdotto alcun implicit cascade verso aggregate esterni.

---

# 38. Mutation + audit atomicity

Per l'intero subtree:

```text
ownership edge deletion
+
Object row deletion
+
DELETED audit insertion
```

sono una singola unità semantica.

Non deve essere possibile committare:

```text
half subtree deleted
```

né:

```text
Object deleted without DELETED audit
```

né:

```text
DELETED audit while live Object survives
```

Qualsiasi failure produce:

```text
ROLLBACK
```

dell'intera subtree deletion.

---

# 39. Protocollo transazionale candidato

```text
BEGIN TRANSACTION
ISOLATION LEVEL SERIALIZABLE

1. resolve requested root Object

2. if root missing:
       FAIL ObjectNotFound

3. recursively discover complete current ownership subtree

4. detect ownership cycle / graph corruption

   if detected:
       FAIL before any mutation

5. derive:
   - subtree Object ids
   - post-order delete order
   - internal ownership edges
   - possible incoming root edge

6. acquire ALL subtree Object rows
   FOR UPDATE
   in canonical Object-id order

7. acquire relevant ownership edge rows
   FOR NO KEY UPDATE
   in canonical deterministic order

8. verify stabilized graph still matches
   the candidate subtree assumptions

   if serialization conflict:
       transaction abort / retry

9. collect final canonical snapshot
   of every subtree Object

10. DELETE:
    - all internal ownership edges
    - incoming root edge if present

11. for each Object
    in descendants-before-parent order:

        DELETE objects row

        INSERT object_changes:
            kind           = DELETED
            object_id      = Object id
            canonical_name = final canonical name
            before_json    = final canonical snapshot
            after_json     = NULL

12. COMMIT
```

Su:

```text
SQLSTATE 40001
```

ritentare l'intera action.

---

# 40. Lock picture

## Subtree Object rows

```text
FOR UPDATE
```

Proteggono:

```text
live state
canonical final snapshots
template pin
coordination with rename
coordination with data change
coordination with schema change
coordination with new attach
```

## Relevant ownership edge rows

```text
FOR NO KEY UPDATE
```

Proteggono:

```text
exact subtree membership edges
incoming root ownership
coordination with detach
coordination with schema-change edge gates
```

## Transaction isolation

```text
SERIALIZABLE
```

Protegge:

```text
recursive subtree membership predicate
against concurrent graph changes / phantoms
```

---

# 41. Lock non richiesti

Delete non richiede:

```text
global ownership graph lock
model-plane global guard
cross-plane global guard

FOR SHARE ObjectTemplateVersion
FOR SHARE DataTypeVersion

effective schema validation
child compatibility validation
```

Il coordinamento rimane locale al root subtree e alle rows direttamente coinvolte.

---

# 42. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
subtree semantics

owned-component direct delete semantics

full discovery before mutation

cycle/corruption detection

post-order delete ordering

one DELETED event per Object

canonical final snapshots

ObjectNotFound semantics for missing root
```

## PostgreSQL / relational model

Garantisce:

```text
Object identity
    -> PRIMARY KEY

ownership references
    -> object_components FKs

edge mutation serialization
    -> row locking

live Object state serialization
    -> FOR UPDATE

external references final authority
    -> FK RESTRICT

audit structural consistency
    -> object_changes CHECK constraints

atomicity
    -> single PostgreSQL transaction
```

## Concurrency protocol

Garantisce:

```text
recursive subtree predicate protection
    -> SERIALIZABLE

new attach vs delete coordination
    -> ATTACH FOR KEY SHARE
       vs DELETE FOR UPDATE

detach vs delete coordination
    -> relevant edge row locking

delete vs rename/data/schema serialization
    -> FOR UPDATE Object rows

overlapping subtree delete consistency
    -> canonical lock ordering + SERIALIZABLE

whole-action retry on SQLSTATE 40001
```

---

# 43. Verdetto DRAFT

> **DELETE elimina il current ownership subtree rooted nell'Object richiesto e non elimina il suo owner.**
>
> Un branch detached prima dell'ordine seriale della delete sopravvive; un branch appartenente al subtree stabilizzato viene eliminato integralmente.
>
> La action viene eseguita in una PostgreSQL transaction `SERIALIZABLE` perché la subtree membership è un recursive multi-row predicate suscettibile a concurrent graph changes.
>
> L'intero subtree viene scoperto prima della prima mutation. Eventuale graph corruption/cycle produce failure prima di qualsiasi delete.
>
> Tutte le subtree Object rows vengono acquisite `FOR UPDATE` in canonical Object-id order, separando lock ordering dal post-order di cancellazione.
>
> Le internal ownership edges e l'eventuale incoming edge del root vengono stabilizzate `FOR NO KEY UPDATE` prima della mutation.
>
> Le ownership edges vengono rimosse esplicitamente; poi gli Object vengono eliminati descendants-before-parent.
>
> Ogni Object eliminato produce il proprio `DELETED` event con final canonical snapshot.
>
> Edge deletion, Object deletion e audit insertion appartengono alla stessa transaction e sono atomici per l'intero subtree.
>
> Su `SQLSTATE 40001` viene ritentata l'intera subtree delete.
>
> External FK `RESTRICT` rimangono final consistency authority.
>
> Nessun ownership graph global lock viene introdotto.
