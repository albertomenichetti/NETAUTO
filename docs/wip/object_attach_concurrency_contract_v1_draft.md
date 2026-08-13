# Object ATTACH — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `attach Object`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application
- invarianti di ownership
- effective slot validation
- child/template compatibility
- garanzie relazionali PostgreSQL
- race concorrenti
- prevenzione dei cicli
- protocollo transazionale
```

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
Object SCHEMA_CHANGE — Concurrency Contract DRAFT v1
```

Nessun ownership graph global lock viene introdotto.

---

# 2. Obiettivo dell'operazione

`attach Object` crea una sola ownership relation:

```text
object_components
-----------------
parent_object_id = P
slot_name        = S
child_object_id  = C
```

Semantica:

```text
P / slot S -> C
```

L'operation non modifica:

```text
objects
object_changes
```

e non modifica implicitamente altre attachment rows.

---

# 3. Nessuna action `move`

`move` non esiste come action autonoma.

La semantica ratificata è:

```text
move
=
detach
+
attach
```

Di conseguenza `attach` non deve mai:

```text
spostare implicitamente un child
cambiare implicitamente owner
cambiare implicitamente slot
```

Se il child è già attached altrove:

```text
ATTACH FAIL
```

---

# 4. Shape relazionale

Baseline:

```text
object_components
-----------------
parent_object_id
slot_name
child_object_id
```

Constraint autorevoli già ratificati:

```text
PRIMARY KEY(child_object_id)

FOREIGN KEY(parent_object_id)
    -> objects.id
    ON DELETE RESTRICT

FOREIGN KEY(child_object_id)
    -> objects.id
    ON DELETE RESTRICT

CHECK(parent_object_id <> child_object_id)

CHECK(slot_name <> '')
```

Indice principale:

```text
INDEX(parent_object_id, slot_name)
```

Non esiste:

```text
UNIQUE(parent_object_id, slot_name)
```

perché ogni slot ha cardinalità:

```text
0..N
```

---

# 5. Invarianti già protetti direttamente dal DB

Il modello relazionale garantisce:

## Endpoint existence

```text
parent exists
child exists
```

tramite FK.

## Single ownership

```text
a child può essere attached
a un solo owner/slot
```

tramite:

```text
PRIMARY KEY(child_object_id)
```

## No self-attachment

```text
A -> A
```

è impedito da:

```text
CHECK(parent_object_id <> child_object_id)
```

## Non-empty slot

```text
slot_name <> ''
```

è protetto da CHECK.

---

# 6. Invarianti che richiedono Domain/Application + concurrency protocol

Restano da garantire:

```text
1. requested slot_name appartiene
   agli effective component slots del parent

2. child template è compatibile con
   slot.target_template_id

3. ownership graph rimane aciclico
```

Questi invarianti non sono completamente esprimibili tramite normali PK/FK/CHECK.

---

# 7. Stabilizzazione degli endpoint

`attach` prende decisioni basate su:

```text
parent.template_id
parent.template_version

child.template_id
child.template_version
```

Questi pin devono rimanere stabili durante validation + INSERT.

L'action deve quindi acquisire parent e child:

```sql
SELECT ...
FROM objects
WHERE id IN (:parent_id, :child_id)
ORDER BY id
FOR KEY SHARE;
```

L'acquisition deve avvenire in ordine canonico di Object id.

---

# 8. Perché `FOR KEY SHARE`

Il reciprocal contract con le altre Object action è:

```text
RENAME
DATA_CHANGE
    -> FOR NO KEY UPDATE

SCHEMA_CHANGE
    -> FOR UPDATE

ATTACH
    -> FOR KEY SHARE endpoint Objects
```

`FOR KEY SHARE`:

```text
non confligge con FOR NO KEY UPDATE
```

quindi `attach` può restare concorrente con:

```text
RENAME
DATA_CHANGE
```

ma:

```text
confligge con FOR UPDATE
```

quindi viene serializzato con:

```text
SCHEMA_CHANGE
```

e con una futura delete che stabilizzi l'endpoint in modo incompatibile.

Questo è il lock strength minimo utile per proteggere il template pin degli endpoint senza bloccare inutilmente mutation che non incidono sulla compatibility.

---

# 9. Parent effective slot validation

Dopo aver acquisito gli endpoint locks viene letto il current exact template pin del parent:

```text
(parent.template_id, parent.template_version)
```

Da questo viene risolto il:

```text
effective component schema
```

La requested:

```text
slot_name = S
```

deve appartenere agli effective slots del parent.

La parola **effective** è vincolante.

Uno slot può essere:

```text
definito localmente
```

oppure:

```text
ereditato tramite ObjectTemplate inheritance
```

Non è sufficiente verificare le sole rows locali di:

```text
object_template_components
```

della exact parent OTV.

Se lo slot non esiste:

```text
ATTACH FAIL
```

---

# 10. Lifecycle della parent ObjectTemplateVersion

`attach` non crea un nuovo binding:

```text
Object -> ObjectTemplateVersion
```

Il parent è già un Object esistente.

La current exact OTV del parent può essere:

```text
PUBLISHED
DEPRECATED
```

e il parent deve continuare a poter utilizzare i propri effective slots storici.

Non serve quindi:

```text
FOR SHARE parent OTV
```

né:

```text
require parent OTV == PUBLISHED
```

La stessa regola vale per ancestor OTV e DataTypeVersion incorporate nello schema.

---

# 11. Child/template compatibility — semantica ratificata

Uno slot effettivo dichiara:

```text
target_template_id = T
```

`T` rappresenta una accepted ObjectTemplate lineage.

Il child `C` è compatibile con `T` se:

```text
C.template_id == T
```

oppure se la current template lineage di C deriva transitivamente da `T`.

Quindi il predicate è:

```text
compatible(C, T)
=
same lineage
OR
transitive descendant lineage
```

---

# 12. Esempio di compatibility polimorfica

Esempio di inheritance:

```text
NetworkDevice
    ^
    |
Router
```

Uno slot:

```text
target_template_id = NetworkDevice
```

può accettare:

```text
NetworkDevice
Router
```

Un slot:

```text
target_template_id = Router
```

non può accettare un generico:

```text
NetworkDevice
```

che non derivi da Router.

Questa semantica viene riutilizzata identicamente da:

```text
SCHEMA_CHANGE
```

per validare existing attachments durante una migration.

---

# 13. Nessun lifecycle lock sulle template dependency

Parent e child sono stabilizzati:

```text
FOR KEY SHARE
```

e quindi i loro exact template pin non possono essere modificati da `SCHEMA_CHANGE` durante l'attach.

Le exact OTV coinvolte sono strutturalmente immutabili una volta PUBLISHED/DEPRECATED.

Non servono:

```text
FOR SHARE OTV
FOR SHARE DTV
```

per la effective slot resolution o per la child inheritance resolution.

`attach` non crea una nuova lifecycle admission verso queste dependency.

---

# 14. Child già attached

Prima dell'INSERT viene verificato il current attachment del child.

## Same exact edge

Se esiste già:

```text
P / S -> C
```

la richiesta è:

```text
idempotent no-op
```

con:

```text
nessun INSERT
nessuna mutation
```

## Different edge

Se esiste:

```text
P1 / S1 -> C
```

e viene richiesto:

```text
P2 / S2 -> C
```

con edge differente:

```text
ATTACH FAIL: AlreadyAttached
```

Non viene effettuato alcun move implicito.

Per cambiare owner o slot:

```text
detach
attach
```

---

# 15. PK come authority finale del single-owner invariant

Sotto race:

```text
T1: P1 / S1 -> C
T2: P2 / S2 -> C
```

entrambe le transaction possono inizialmente osservare C detached.

La:

```text
PRIMARY KEY(child_object_id)
```

rimane l'autorità finale.

Una sola relation row può essere persistita.

L'altra transaction può ricevere:

```text
unique violation
```

oppure, in una transaction SERIALIZABLE, una:

```text
serialization failure
```

e deve poi rieseguire l'intera action.

---

# 16. Ownership graph aciclico

Il grafo di ownership deve rimanere aciclico.

Sono vietati:

```text
A -> B
B -> A
```

e cicli più lunghi:

```text
A -> B
B -> C
C -> A
```

Dato il:

```text
single-owner invariant
```

ogni Object ha al massimo un parent.

Il graph assume quindi la forma di una foresta.

---

# 17. Cycle predicate locale

Per una richiesta:

```text
P -> C
```

creeremmo un ciclo se:

```text
C è già un ancestor di P
```

prima dell'INSERT.

È quindi sufficiente percorrere la parent chain di P verso l'alto.

Non serve attraversare l'intero subtree del child.

Predicate:

```text
C must NOT be an ancestor of P
```

---

# 18. Recursive ancestor check

Forma concettuale:

```sql
WITH RECURSIVE ancestors(id) AS (
    SELECT :parent_id

    UNION ALL

    SELECT oc.parent_object_id
    FROM object_components oc
    JOIN ancestors a
      ON oc.child_object_id = a.id
)
SELECT 1
FROM ancestors
WHERE id = :child_id;
```

Se viene trovato:

```text
child_id
```

nella parent chain del requested parent:

```text
ATTACH FAIL: OwnershipCycle
```

---

# 19. Perché READ COMMITTED non è sufficiente

Scenario iniziale:

```text
A detached
B detached
```

T1:

```text
attach A -> B
```

T2:

```text
attach B -> A
```

Entrambe possono osservare:

```text
no cycle
```

perché nessun edge esiste ancora.

Poi:

```text
T1 inserts child=B
T2 inserts child=A
```

Le PK sono differenti.

Entrambe potrebbero committare sotto un normale protocollo non serializzabile.

Risultato invalido:

```text
A -> B -> A
```

La stessa race esiste con cicli concorrenti più lunghi.

---

# 20. Nessun graph-wide lock

Non viene introdotto:

```text
global ownership lock
table-wide ownership lock
model-plane guard
cross-plane guard
```

Il fatto che l'invariante sia globalmente esprimibile come aciclicità non implica che ogni attach debba serializzare l'intero graph.

---

# 21. Transaction isolation ratificata

`attach Object` deve essere eseguita in una transaction:

```text
SERIALIZABLE
```

Il protocollo completo:

```text
endpoint stabilization
effective slot validation
child compatibility validation
current ownership read
ancestor predicate read
edge INSERT
```

deve appartenere alla stessa SERIALIZABLE transaction.

---

# 22. Perché PostgreSQL SERIALIZABLE è adatto

Due attach concorrenti che, insieme, creerebbero un ciclo:

```text
leggono predicate che dipendono dal graph corrente
+
scrivono edge che rendono falso il predicate letto dall'altra
```

non sono serializzabili in un ordine che permetta ad entrambe di riuscire.

PostgreSQL Serializable Snapshot Isolation rileva le read/write dependencies rilevanti.

Almeno una transaction deve abortire con:

```text
SQLSTATE 40001
```

quando l'esecuzione concorrente non può essere serializzata.

---

# 23. Whole-action retry

Una:

```text
SQLSTATE 40001
```

non rappresenta una business failure.

Significa:

```text
l'execution concorrente deve essere rieseguita
contro un nuovo stato consistente
```

Il retry deve ripartire dall'inizio della transaction.

Deve rieseguire:

```text
endpoint locks
Object reads
current attachment check
effective slot resolution
compatibility validation
ancestor traversal
INSERT
```

Non deve essere ritentato soltanto l'INSERT.

---

# 24. Business failures dopo retry

Dopo un retry la request può diventare una normale business failure, ad esempio:

```text
AlreadyAttached
OwnershipCycle
InvalidSlot
IncompatibleChild
ObjectNotFound
```

Questi errori sono distinti dalla transient:

```text
serialization failure
```

---

# 25. Concurrent SCHEMA_CHANGE

Il reciprocal contract è ora ratificato.

`attach`:

```text
FOR KEY SHARE parent
FOR KEY SHARE child
```

`SCHEMA_CHANGE`:

```text
FOR UPDATE Object
```

Se attach vince:

```text
endpoint schemas stable
validate
INSERT edge
COMMIT

SCHEMA_CHANGE resumes
and sees the new incident edge
```

Se SCHEMA_CHANGE vince:

```text
attach waits

after migration commit:
attach reads new endpoint template pin
and validates against new schema
```

Questo impedisce compatibility decisions basate su schema pin stale.

---

# 26. Concurrent RENAME

`RENAME` usa:

```text
FOR NO KEY UPDATE
```

che è compatibile con:

```text
FOR KEY SHARE
```

quindi `attach` e `RENAME` possono procedere contemporaneamente.

Questo è corretto perché:

```text
canonical_name
```

non partecipa alla attachment compatibility.

---

# 27. Concurrent DATA_CHANGE

`DATA_CHANGE` usa:

```text
FOR NO KEY UPDATE
```

che è compatibile con:

```text
FOR KEY SHARE
```

quindi può procedere contemporaneamente ad attach.

Questo è corretto perché, nel modello corrente:

```text
runtime property values
```

non partecipano al predicate di attachment compatibility.

La compatibility dipende dal template lineage/schema pin, che rimane stabilizzato.

---

# 28. Concurrent DETACH

Un detach può rimuovere un edge presente nella parent chain letta dalla cycle detection.

In SERIALIZABLE isolation l'esito è interpretato secondo un ordine seriale valido.

Se attach osserva ancora l'edge e conclude:

```text
OwnershipCycle
```

la failure è corretta rispetto all'ordine:

```text
attach attempt
then detach
```

Se detach precede semanticamente l'attach:

```text
attach
```

può vedere la nuova chain e riuscire.

Non è richiesto che attach attenda sempre un detach concorrente che potrebbe renderlo valido.

---

# 29. Concurrent DELETE

Il contratto definitivo di `delete Object` sarà ratificato separatamente.

La requirement reciproca è che delete stabilizzi la Object row in modo incompatibile con:

```text
FOR KEY SHARE
```

sugli endpoint.

Le FK restano comunque final authority:

```text
attach commits first
    -> relation references endpoint Objects
    -> delete must respect RESTRICT / deletion protocol

delete commits first
    -> endpoint disappears
    -> attach cannot persist dangling FK
```

---

# 30. Nessun `object_changes` audit event

Il canonical Object snapshot ratificato contiene:

```text
canonical_name
template pin
properties
```

e non contiene ownership attachments.

Di conseguenza `attach` non deve essere registrato impropriamente come:

```text
DATA_CHANGE
SCHEMA_CHANGE
```

Non esiste attualmente:

```text
ATTACH
```

tra i kind di `object_changes`.

Quindi:

```text
attach
    -> no object_changes event
```

Un eventuale audit storico del graph ownership richiederebbe un modello specifico separato.

---

# 31. Protocollo transazionale candidato

```text
BEGIN TRANSACTION
ISOLATION LEVEL SERIALIZABLE

1. validate:
   - parent_id != child_id
   - slot_name non-empty

2. acquire parent + child Object rows
   FOR KEY SHARE
   in canonical Object-id order

3. require:
   parent exists
   child exists

4. read current exact template pins
   of parent and child

5. inspect current child attachment

   if exact same P/S/C edge exists:
       no-op
       COMMIT / return unchanged

   if child attached elsewhere:
       FAIL AlreadyAttached

6. resolve parent effective component schema

7. require requested effective slot S exists

8. resolve child current ObjectTemplate ancestry

9. require:
   child compatible with slot.target_template_id

10. traverse parent chain upward from P

11. if C is encountered:
       FAIL OwnershipCycle

12. INSERT object_components:
    parent_object_id = P
    slot_name        = S
    child_object_id  = C

13. COMMIT
```

Su:

```text
SQLSTATE 40001
```

ritentare l'intera transaction.

---

# 32. Canonical lock ordering

Parent e child Object rows devono essere acquisiti in ordine deterministico, ad esempio:

```text
ORDER BY Object.id
```

Questo evita di codificare l'ordine semantico parent/child nell'ordine dei lock e riduce i deadlock tra attach concorrenti.

Non viene introdotto alcun graph-wide lock ordering.

---

# 33. Specialized Unit of Work

`attach Object` è un caso naturale per una UoW specializzata perché richiede:

```text
SERIALIZABLE transaction isolation
whole-action retry semantics
```

Esempio concettuale:

```text
ObjectAttachUnitOfWork
    isolation = SERIALIZABLE
```

La UoW non deve contenere business logic.

Deve codificare esclusivamente:

```text
transaction boundary
isolation level
retry semantics
```

La business logic rimane nel service/domain workflow.

---

# 34. Lock non richiesti

`attach Object` non richiede:

```text
global ownership graph lock
```

Non richiede:

```text
FOR UPDATE parent/child
```

Non richiede:

```text
FOR SHARE ObjectTemplateVersion
```

Non richiede:

```text
FOR SHARE DataTypeVersion
```

Non richiede:

```text
model-plane global guard
cross-plane global guard
```

Il coordinamento rimane limitato agli endpoint e al predicate ownership letto nella SERIALIZABLE transaction.

---

# 35. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
slot_name semantic validity

effective slot resolution

child/template compatibility

same-edge idempotent no-op

different existing attachment -> AlreadyAttached

cycle predicate:
    child must not be ancestor of parent

no implicit move
```

## PostgreSQL / relational model

Garantisce:

```text
parent existence
    -> FK

child existence
    -> FK

single ownership
    -> PRIMARY KEY(child_object_id)

self-attachment forbidden
    -> CHECK

non-empty slot_name
    -> CHECK

referential integrity
    -> FK RESTRICT
```

## Concurrency protocol

Garantisce:

```text
stable endpoint template pins
    -> FOR KEY SHARE

attach vs SCHEMA_CHANGE serialization
    -> FOR KEY SHARE vs FOR UPDATE

attach vs RENAME/DATA_CHANGE concurrency
    -> compatible lock modes

general concurrent cycle prevention
    -> SERIALIZABLE transaction

non-serializable execution recovery
    -> whole-action retry on SQLSTATE 40001
```

---

# 36. Verdetto DRAFT

> **ATTACH crea una singola `object_components` row e non modifica implicitamente altri attachment.**
>
> Parent e child vengono stabilizzati `FOR KEY SHARE` in ordine canonico. Questo mantiene stabili i loro schema pin, resta concorrente con `RENAME`/`DATA_CHANGE` ed è incompatibile con `SCHEMA_CHANGE`.
>
> La requested `slot_name` deve essere un effective component slot della current exact OTV del parent.
>
> La compatibilità è polimorfica: il child è compatibile con `slot.target_template_id = T` se appartiene alla stessa ObjectTemplate lineage `T` oppure a una lineage che deriva transitivamente da `T`.
>
> Un exact same-edge reattach è un no-op idempotente. Un child già attached a un edge diverso produce `AlreadyAttached`; non esiste move implicito.
>
> La `PRIMARY KEY(child_object_id)` rimane l'autorità finale del single-owner invariant.
>
> Per prevenire general ownership cycles sotto concorrenza, la action viene eseguita in una PostgreSQL transaction `SERIALIZABLE`. La cycle detection percorre la parent chain del requested parent e richiede che il requested child non ne sia già un ancestor.
>
> Su `SQLSTATE 40001` viene ritentata l'intera action, non soltanto l'INSERT.
>
> Non viene introdotto alcun ownership graph global lock.
>
> `attach` non produce attualmente un `object_changes` event.
