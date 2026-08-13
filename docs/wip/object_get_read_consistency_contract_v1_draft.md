# Object GET/READ — Consistency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente della query `get/read Object`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application della read
- garanzie PostgreSQL MVCC
- interaction con mutation concorrenti
- isolation level
- assenza intenzionale di explicit locking
```

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
Object RENAME — Concurrency Contract DRAFT v1
Object DATA_CHANGE — Concurrency Contract DRAFT v1
Object SCHEMA_CHANGE — Concurrency Contract DRAFT v1
Object DELETE — Concurrency Contract DRAFT v1
```

Questa query riguarda esclusivamente la lettura della exact live `objects` row.

Non include:

```text
object_components
object_changes
effective schema
ownership subtree
```

che richiedono query contract separati.

---

# 2. Obiettivo della query

Input:

```text
object_id = X
```

Output:

```text
id
canonical_name
template_id
template_version
properties
```

oppure:

```text
ObjectNotFound
```

La query non modifica alcuno stato e non produce audit event.

---

# 3. Live Object state

Il live Object state autorevole è contenuto nella singola row:

```text
objects
-------
id
canonical_name
template_id
template_version
properties_json
```

La query legge esclusivamente questa row.

---

# 4. SQL naturale

Forma concettuale:

```sql
SELECT
    id,
    canonical_name,
    template_id,
    template_version,
    properties_json
FROM objects
WHERE id = :object_id;
```

Non viene aggiunta alcuna locking clause.

---

# 5. Nessun explicit row lock

`get/read Object` non deve usare:

```text
FOR SHARE
FOR KEY SHARE
FOR NO KEY UPDATE
FOR UPDATE
```

La query è osservativa.

Non deve diventare un coordination point che rallenta o serializza inutilmente:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
DELETE
```

---

# 6. PostgreSQL MVCC guarantee

Le mutation del live Object state sono transazionali.

Di conseguenza una read concorrente osserva:

```text
uno stato committed precedente
```

oppure:

```text
uno stato committed successivo
```

della row.

Non deve osservare una row parzialmente aggiornata.

---

# 7. READ vs RENAME

Scenario:

```text
before:
    canonical_name = A

RENAME:
    A -> B
```

Una concurrent read può vedere:

```text
A
```

oppure:

```text
B
```

in funzione del proprio statement snapshot.

Entrambi sono risultati corretti.

La read non deve attendere il rename per ottenere necessariamente il valore più recente possibile.

---

# 8. READ vs DATA_CHANGE

Scenario:

```text
properties:
    P0 -> P1
```

La read può osservare:

```text
P0
```

oppure:

```text
P1
```

come complete committed value.

Non deve osservare una partial JSON mutation.

---

# 9. READ vs SCHEMA_CHANGE

`SCHEMA_CHANGE` modifica atomicamente:

```text
template_id
template_version
properties_json
```

Esempio:

```text
before:
    template = v2
    properties = P2

after:
    template = v3
    properties = P3
```

Una read deve osservare:

```text
v2 / P2
```

oppure:

```text
v3 / P3
```

Non deve osservare combinazioni incoerenti come:

```text
v3 / P2
v2 / P3
```

La garanzia deriva dalla singola row + transazione PostgreSQL.

---

# 10. READ vs DELETE

Una delete non ancora committata non rende automaticamente invisibile la row alle read concorrenti.

Una read può ancora osservare l'Object secondo il proprio MVCC snapshot.

Dopo il commit della delete, una nuova query restituisce:

```text
ObjectNotFound
```

Non viene richiesto che la read:

```text
blocchi
attenda
fallisca preventivamente
```

solo perché una delete concorrente è in corso.

---

# 11. READ vs CREATE

Prima del commit di `create Object`:

```text
ObjectNotFound
```

Dopo il commit:

```text
complete Object
```

La create persiste atomicamente:

```text
Object row
+
CREATED audit
```

ma `get/read Object` legge soltanto la live Object row.

---

# 12. Nessuna lifecycle validation

La query non crea alcun nuovo binding.

Non deve quindi richiedere:

```text
current exact OTV == PUBLISHED
```

Un Object pinnato a una OTV ormai:

```text
DEPRECATED
```

rimane perfettamente leggibile.

Non servono:

```text
FOR SHARE OTV
status checks
DTV status checks
```

---

# 13. Nessuna effective schema resolution

La normale `get/read Object` non deve:

```text
resolve ObjectTemplate inheritance
resolve effective properties
resolve component slots
```

La query restituisce lo stato live persistito.

Effective-schema inspection è una query distinta.

---

# 14. Nessuna property revalidation

La read non deve comportarsi come integrity verification.

Non deve:

```text
read Object
-> resolve schema
-> revalidate every property
```

ogni volta.

La query deve restituire la row persistita anche nel caso in cui un futuro integrity verifier possa rilevare inconsistenze.

Questo mantiene separati:

```text
normal read
integrity verification
```

---

# 15. Isolation level

Per questa query è sufficiente:

```text
READ COMMITTED
```

e in particolare il normale statement snapshot della singola SELECT.

Non servono:

```text
REPEATABLE READ
SERIALIZABLE
```

perché non vengono effettuate decision reads correlate su più statement.

---

# 16. Nessuna specialized Unit of Work

Non è necessaria una UoW specializzata.

Non esiste un requisito specifico di:

```text
special isolation
retry
multi-row predicate stabilization
```

Una normale query/repository transaction è sufficiente.

---

# 17. Read non equivale a reservation

Una `get/read Object` non stabilizza lo stato per una write futura.

Esempio non ammesso come assumption:

```text
GET Object
...
later
UPDATE assuming Object is still unchanged
```

La GET non mantiene lock dopo la query.

Ogni write action deve:

```text
enter its own transaction
acquire its own concurrency gate
re-read current state
make decision against that current state
```

---

# 18. Relationship con i write gates

Le action mutate già ratificate usano:

```text
RENAME
DATA_CHANGE
    -> FOR NO KEY UPDATE

SCHEMA_CHANGE
DELETE
    -> FOR UPDATE

ATTACH
    -> FOR KEY SHARE endpoints
```

`get/read Object` usa:

```text
plain SELECT
```

e non partecipa a questa lock matrix.

---

# 19. Canonical live DTO

Una possibile shape applicativa è:

```json
{
  "id": "...",
  "canonical_name": "router-rm-01",
  "template_id": "...",
  "template_version": 3,
  "properties": {
    "...": "..."
  }
}
```

La presenza di:

```text
id
```

nel live DTO è naturale.

Nel canonical audit snapshot, invece, `id` può restare esterno al JSON perché è già disponibile come:

```text
object_changes.object_id
```

---

# 20. Scope limitato della garanzia

Le conclusioni di questo documento valgono perché la query legge una singola:

```text
objects row
```

Non devono essere generalizzate automaticamente a query multi-row come:

```text
Object + components
Object + owner
Object subtree
Object + audit history
list Objects
```

Sotto `READ COMMITTED`, più SELECT distinti possono osservare statement snapshot differenti.

Queste query richiedono contratti separati.

---

# 21. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
lookup by exact Object id

ObjectNotFound if live row not visible

live DTO construction

no implicit validation or schema expansion
```

## PostgreSQL / relational model

Garantisce:

```text
single-row committed visibility
    -> MVCC

atomic visibility of row updates
    -> transaction semantics

Object identity
    -> PRIMARY KEY
```

## Concurrency protocol

Garantisce intenzionalmente soltanto:

```text
read a committed live Object state
without blocking writers
```

Non garantisce:

```text
latest-at-return-time semantics
reservation of state
repeatable multi-statement snapshot
```

---

# 22. Verdetto DRAFT

> **GET/READ Object è una read non bloccante della exact live Object row.**
>
> La query usa un normale `SELECT` sotto `READ COMMITTED`, senza explicit row locks.
>
> PostgreSQL MVCC garantisce che la reader osservi uno stato committed completo della row, precedente o successivo a una mutation, mai una combinazione parziale del live Object state.
>
> La query non richiede lifecycle validation della current ObjectTemplateVersion, non rivalida `properties_json` e non risolve l'effective schema.
>
> Un Object pinnato a una OTV `DEPRECATED` rimane leggibile.
>
> Una read concorrente con delete può ancora osservare la row finché il proprio snapshot la rende visibile; le read successive al commit della delete restituiscono `ObjectNotFound`.
>
> La GET non rappresenta una reservation sullo stato e non può essere usata come precondizione implicita di una write successiva.
>
> Nessuna specialized UoW e nessun locking esplicito sono necessari.
