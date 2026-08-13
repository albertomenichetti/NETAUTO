# Object LIST ATTACHED COMPONENTS — Consistency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente della query `list attached components of Object`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application della query
- shape relazionale della read
- garanzie PostgreSQL MVCC
- interaction con mutation concorrenti
- isolation level
- assenza intenzionale di explicit locking
```

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
Object GET/READ — Consistency Contract DRAFT v1
Object ATTACH — Concurrency Contract DRAFT v1
Object DETACH — Concurrency Contract DRAFT v1
Object SCHEMA_CHANGE — Concurrency Contract DRAFT v1
Object DELETE — Concurrency Contract DRAFT v1
```

Questa query riguarda esclusivamente:

```text
current runtime attachments
immediatamente sotto un parent Object
```

Non include:

```text
effective empty slots
ObjectTemplate schema inspection
ownership subtree recursive expansion
audit history
```

---

# 2. Obiettivo della query

Input:

```text
parent_object_id = P
```

Output:

```text
slot_name
child Object live state
```

per tutte le current rows:

```text
object_components.parent_object_id = P
```

Esempio:

```text
Router R1

network_interfaces:
    if1
    if2

supervisors:
    sup1
```

La query restituisce:

```text
network_interfaces -> if1
network_interfaces -> if2
supervisors        -> sup1
```

---

# 3. Attachment presenti vs effective slots

La query risponde:

> quali Object sono attualmente attached al parent e in quale slot?

Non risponde:

> quali slot ammette l'effective ObjectTemplate schema del parent?

Quindi:

```text
effective slot vuoto
```

non compare nel risultato.

Una query sugli effective slots è una query distinta.

---

# 4. Nessuna effective schema resolution

`list attached components` non deve:

```text
resolve ObjectTemplate inheritance
resolve effective component definitions
show empty slots
validate target_template_id compatibility
```

La query restituisce esclusivamente il runtime ownership state persistito.

---

# 5. Requisito principale: single SQL statement

Parent existence, attachment rows e child live states devono essere letti nello stesso SQL statement.

Non deve essere usato un pattern:

```text
SELECT parent

then

SELECT object_components

then

SELECT child Objects
```

sotto una normale READ COMMITTED transaction.

Motivazione:

statement distinti possono osservare snapshot MVCC distinti e produrre una vista artificialmente incoerente.

---

# 6. Esempio di incoerenza multi-statement

Scenario:

```text
P / S -> C
```

Query naive:

```text
SELECT edges
    -> vede P/S -> C
```

Poi una concurrent:

```text
detach/delete
```

committa.

Una successiva:

```text
SELECT child C
```

potrebbe non vedere più C.

Il problema non appartiene al modello relazionale: sarebbe introdotto dalla query shape.

La soluzione ratificata è:

```text
ONE SQL statement
ONE MVCC statement snapshot
```

---

# 7. Shape SQL candidata

Forma concettuale:

```sql
SELECT
    p.id AS parent_id,

    oc.slot_name,

    c.id AS child_id,
    c.canonical_name,
    c.template_id,
    c.template_version,
    c.properties_json

FROM objects AS p

LEFT JOIN object_components AS oc
    ON oc.parent_object_id = p.id

LEFT JOIN objects AS c
    ON c.id = oc.child_object_id

WHERE p.id = :parent_id

ORDER BY
    oc.slot_name,
    oc.child_object_id;
```

La sintassi concreta può essere adattata dal repository.

L'invariante importante è:

```text
parent
edge
child
```

letti nello stesso statement snapshot.

---

# 8. Perché partire dalla parent row

Una query basata soltanto su:

```sql
SELECT ...
FROM object_components
WHERE parent_object_id = :parent_id;
```

non permetterebbe di distinguere:

```text
parent exists, zero attachments
```

da:

```text
parent does not exist
```

Entrambi produrrebbero zero rows.

La query deve invece partire da:

```text
objects AS parent
```

e usare:

```text
LEFT JOIN
```

verso attachments e children.

---

# 9. Parent missing vs empty collection

Semantica ratificata:

## Parent missing

```text
no parent row visible
-> ObjectNotFound
```

## Parent exists, zero attachments

```text
parent row visible
no object_components rows
-> []
```

Questa distinzione deve essere ottenibile dallo stesso SQL statement.

---

# 10. Nessun explicit row lock

La query non deve usare:

```text
FOR SHARE
FOR KEY SHARE
FOR NO KEY UPDATE
FOR UPDATE
```

È una query osservativa.

Non deve diventare una reservation del graph o un coordination point per le mutation.

---

# 11. Isolation level

Per questa query è sufficiente:

```text
READ COMMITTED
```

perché:

```text
parent
attachments
children
```

vengono letti in un singolo statement.

Non servono:

```text
REPEATABLE READ
SERIALIZABLE
```

---

# 12. READ vs ATTACH

Scenario:

```text
attach P/S -> C
```

Una concurrent list query può osservare:

```text
edge absent
```

se il proprio statement snapshot precede il commit dell'attach,

oppure:

```text
edge present
+
child C
```

se il proprio statement snapshot segue il commit.

Entrambi i risultati sono corretti.

La query non deve attendere una attach in corso per ottenere necessariamente lo stato più recente.

---

# 13. READ vs DETACH

Scenario:

```text
P/S -> C
```

Una concurrent detach può far sì che la list query osservi:

```text
edge present
```

oppure:

```text
edge absent
```

in base al statement snapshot.

Entrambi gli esiti sono corretti.

---

# 14. READ vs child RENAME

Scenario:

```text
P/S -> C
```

e C viene rinominato:

```text
old -> new
```

La query può restituire:

```text
P/S -> C(old)
```

oppure:

```text
P/S -> C(new)
```

ma edge e child live state appartengono allo stesso statement snapshot.

Non vengono combinati risultati provenienti da momenti differenti.

---

# 15. READ vs child DATA_CHANGE

Scenario:

```text
P/S -> C
```

con:

```text
C.properties:
P0 -> P1
```

La query può vedere:

```text
P/S -> C(P0)
```

oppure:

```text
P/S -> C(P1)
```

come committed child state coerente.

---

# 16. READ vs SCHEMA_CHANGE

La query può concorrere con schema migration sia del parent sia del child.

`SCHEMA_CHANGE` modifica atomicamente:

```text
template pin
properties
```

e preserva gli existing attachments oppure fallisce.

La list query può quindi osservare un committed state precedente o successivo alla migration.

Non deve però rivalidare la compatibility degli attachment.

---

# 17. READ vs child DELETE

La subtree delete rimuove atomicamente nella stessa transaction:

```text
ownership edges
child Object row
DELETED audit
```

La query può osservare lo stato pre-delete:

```text
edge P -> C
+
C live state
```

oppure lo stato post-delete:

```text
no edge
no C
```

Il single-statement contract evita di costruire artificialmente:

```text
edge present
child missing
```

tramite snapshot differenti.

---

# 18. READ vs parent DELETE

Se il parent è ancora visibile allo statement snapshot:

```text
parent
+
attachments visible in same snapshot
```

possono essere restituiti.

Dopo il commit della delete, una nuova query produce:

```text
ObjectNotFound
```

---

# 19. Nessuna lifecycle validation

Parent e child possono essere pinnati a ObjectTemplateVersion ormai:

```text
DEPRECATED
```

e rimanere live Objects validamente leggibili.

La query non crea nuovi lifecycle binding.

Non servono:

```text
FOR SHARE OTV
require OTV PUBLISHED
DTV lifecycle checks
```

---

# 20. Nessuna integrity revalidation

La query non deve:

```text
resolve every effective slot
verify every child compatibility
verify ownership acyclicity
revalidate child properties
```

Queste responsabilità appartengono a:

```text
write admission protocols
integrity verification
```

La normale read deve poter osservare lo stato persistito.

---

# 21. Ordering

Il runtime model non contiene un:

```text
child_position
```

all'interno di uno slot.

Quindi non esiste un domain/business ordering dei children.

Per output deterministico può essere usato:

```text
ORDER BY slot_name, child_object_id
```

Questo ordering è:

```text
presentation/debug/test determinism
```

e non una semantica di dominio.

---

# 22. `object_template_components.position` non ordina i runtime children

La colonna:

```text
object_template_components.position
```

ordina le component-slot definitions nello schema.

Non deve essere interpretata come ordering dei child Object runtime all'interno della collection.

Le due semantiche sono distinte.

---

# 23. Nessuna specialized Unit of Work

Non è richiesta una UoW specializzata.

La query richiede:

```text
one SELECT
READ COMMITTED
no explicit locks
no retry contract
```

Una normale repository/query path è sufficiente.

---

# 24. La read non stabilizza il graph

Il risultato della query non rappresenta una reservation.

Non è corretto assumere:

```text
list components
...
later
same children are still attached
```

Se una write successiva dipende dalla current membership deve applicare il proprio concurrency contract.

Esempi:

```text
ATTACH
DETACH
SCHEMA_CHANGE
DELETE
```

devono sempre rileggere/stabilizzare le rows richieste dalla propria action.

---

# 25. Scope della garanzia

Questo contratto riguarda:

```text
one parent
+
its immediate current attachment rows
+
current live state of attached children
```

Non deve essere generalizzato automaticamente a:

```text
recursive subtree read
Object + owner + children + grandchildren
Object + audit history
effective slots + runtime attachments
```

Queste query possono richiedere contratti differenti.

---

# 26. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
lookup by exact parent Object id

ObjectNotFound if parent missing

empty collection if parent exists with zero attachments

return only currently persisted attachments

no implicit effective-slot expansion

deterministic presentation ordering if desired
```

## PostgreSQL / relational model

Garantisce:

```text
parent identity
    -> objects PRIMARY KEY

edge referential integrity
    -> object_components FKs

single-owner relation baseline
    -> PRIMARY KEY(child_object_id)

consistent statement snapshot
    -> MVCC
```

## Query-shape contract

Garantisce:

```text
parent existence
attachment membership
child live state
```

provengano dallo stesso statement snapshot tramite:

```text
single joined SELECT
```

---

# 27. Verdetto DRAFT

> **LIST ATTACHED COMPONENTS è una query read-only del current ownership graph immediatamente sotto un parent Object.**
>
> Parent existence, attachment rows e child live states devono essere letti in un unico SQL statement, così tutte le informazioni appartengono allo stesso PostgreSQL MVCC statement snapshot.
>
> La query usa `READ COMMITTED` e non richiede explicit row locks.
>
> Parent inesistente produce `ObjectNotFound`; parent esistente senza attachment produce una collection vuota.
>
> Vengono restituiti soltanto gli attachment realmente persistiti. Gli effective slots vuoti non vengono materializzati e richiedono una query distinta sullo schema.
>
> La query non rivalida lifecycle, effective slot compatibility, child compatibility, properties o graph acyclicity.
>
> Attach, detach, schema change e delete concorrenti possono far osservare il committed state precedente oppure successivo, senza blocking.
>
> `ORDER BY slot_name, child_object_id` può essere usato per determinismo di presentazione, ma non rappresenta un business ordering dei child runtime.
>
> Nessuna specialized UoW è necessaria.
