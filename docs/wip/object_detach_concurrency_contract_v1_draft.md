# Object DETACH — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `detach Object`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application
- exact-edge detach semantics
- garanzie relazionali PostgreSQL
- race concorrenti
- protocollo transazionale
- interaction con attach/schema change/delete
```

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
Object ATTACH — Concurrency Contract DRAFT v1
Object SCHEMA_CHANGE — Concurrency Contract DRAFT v1
```

Nessun ownership graph global lock viene introdotto.

---

# 2. Obiettivo dell'operazione

`detach Object` rimuove una exact ownership relation:

```text
object_components
-----------------
parent_object_id = P
slot_name        = S
child_object_id  = C
```

Semantica:

```text
detach exact edge P / S -> C
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

Di conseguenza `detach`:

```text
- non cerca un nuovo owner
- non cerca un nuovo slot
- non effettua attach implicito
```

---

# 4. Exact-edge semantics

La richiesta di detach deve identificare l'intera relazione attesa:

```text
parent_object_id
slot_name
child_object_id
```

Non viene introdotta una operation generica:

```text
detach(child_id)
```

che significhi:

```text
detach child da qualunque owner abbia adesso
```

Motivazione:

una stale request non deve poter rimuovere un attachment più recente verso un altro owner/slot.

---

# 5. Esempio stale detach

Stato iniziale:

```text
P1 / S1 -> C
```

Poi:

```text
detach P1/S1/C
attach P2/S2/C
```

Una vecchia richiesta:

```text
detach P1/S1/C
```

deve essere un no-op.

Non deve poter eliminare:

```text
P2/S2 -> C
```

Questo è garantito condizionando il DELETE sull'intera exact edge.

---

# 6. SQL naturale dell'operazione

La mutation deve essere espressa direttamente come conditional delete:

```sql
DELETE FROM object_components
WHERE parent_object_id = :parent_id
  AND slot_name = :slot_name
  AND child_object_id = :child_id
RETURNING parent_object_id, slot_name, child_object_id;
```

Non è necessario:

```text
SELECT
then DELETE
```

per prendere la decisione.

Il `DELETE` stesso è il coordination point.

---

# 7. Idempotenza

Semantica ratificata:

## Exact edge exists

```text
P / S -> C exists
```

risultato:

```text
DELETE row
changed = true
```

## Exact edge absent

```text
P / S -> C absent
```

risultato:

```text
no-op
changed = false
```

L'operation è quindi idempotente.

---

# 8. Child attached altrove

Se la exact requested edge è assente ma il child è attached altrove:

```text
P2 / S2 -> C
```

una richiesta:

```text
detach P1 / S1 -> C
```

produce:

```text
no-op
```

e non tocca la current relation.

Questo preserva la semantica:

> detach assicura che la exact requested edge non esista.

Non significa:

> detach child da qualunque owner corrente.

---

# 9. Perché non serve cycle detection

`detach` produce:

```text
Graph_after
=
Graph_before - edge
```

Rimuovere un edge da un graph aciclico:

```text
non può creare un ciclo
```

e non può violare il single-owner invariant.

Non servono quindi:

```text
recursive CTE
ancestor traversal
cycle predicate
SERIALIZABLE
ownership graph lock
```

La cycle prevention rimane responsabilità dell'action che aggiunge edge:

```text
attach
```

---

# 10. Nessuna effective slot validation

Rimuovere una relation non può introdurre:

```text
invalid slot
incompatible child
```

`detach` non deve quindi:

```text
resolve parent effective schema
verify slot existence
resolve child ancestry
verify target_template_id compatibility
```

Questo è importante anche come remediation:

una relation eventualmente incompatibile deve poter essere rimossa senza ulteriori precondizioni di schema.

---

# 11. Nessun lock sugli endpoint Object

`detach` non prende decisioni basate su:

```text
parent.template_id/version
child.template_id/version
canonical_name
properties_json
```

Non servono quindi:

```text
FOR KEY SHARE parent
FOR KEY SHARE child
FOR NO KEY UPDATE parent/child
FOR UPDATE parent/child
```

Se l'edge esiste, le FK già garantiscono che gli endpoint esistano.

Se l'edge non esiste, la detach è un no-op.

---

# 12. Row locking implicito del DELETE

Il `DELETE` acquisisce il lock necessario sulla target relation row.

Questo è sufficiente per coordinarsi con:

```text
concurrent DETACH
SCHEMA_CHANGE incident-edge locks
DELETE workflows che mutano la same edge
```

Non serve un esplicito:

```text
SELECT edge FOR UPDATE
```

prima del DELETE.

---

# 13. DETACH vs DETACH

Scenario:

```text
P / S -> C
```

T1 e T2 eseguono contemporaneamente:

```text
detach P/S/C
```

Una transaction elimina la row.

L'altra, dopo la necessaria serializzazione sulla same row, osserva la row assente.

Risultato:

```text
one:
    changed = true

other:
    changed = false
```

Entrambe le execution rispettano l'idempotenza.

---

# 14. DETACH vs SCHEMA_CHANGE

`SCHEMA_CHANGE` acquisisce current incident `object_components` rows:

```text
FOR NO KEY UPDATE
```

`detach` esegue:

```text
DELETE same edge row
```

Le mutation vengono quindi serializzate sulla exact edge.

## Detach prima

```text
DELETE edge
COMMIT
```

Poi `SCHEMA_CHANGE` non vede più la relation e non deve validarla.

## Schema change prima

```text
lock edge
validate attachment
migrate
COMMIT
```

Poi detach procede e rimuove la relation.

Entrambi gli ordini sono semanticamente corretti.

---

# 15. DETACH vs ATTACH della stessa exact edge

Stato:

```text
P / S -> C
```

T1:

```text
detach P/S/C
```

T2:

```text
attach P/S/C
```

Possibili ordini seriali validi:

## Attach semanticamente prima

Attach osserva exact same edge e produce:

```text
idempotent no-op
```

Poi detach elimina la relation.

Final state:

```text
detached
```

## Detach semanticamente prima

Detach elimina la relation.

Poi attach può reinserirla se tutti i propri invarianti sono soddisfatti.

Final state:

```text
attached
```

Non viene imposto un vincitore universale.

---

# 16. DETACH old edge vs ATTACH new edge

Caso tipico della semantica di move:

```text
current:
P1/S1 -> C
```

T1:

```text
detach P1/S1/C
```

T2:

```text
attach P2/S2/C
```

Se attach verifica prima del commit della detach:

```text
child still attached
-> AlreadyAttached
```

oppure può incorrere in una serialization failure secondo il proprio protocollo SERIALIZABLE.

Se detach committa prima:

```text
C detached
```

e l'attach può riuscire.

Questo è coerente con la decisione:

```text
move is not atomic
```

e con la workflow esplicita:

```text
detach
COMMIT
attach
```

---

# 17. DETACH vs ATTACH cycle detection

Un detach concorrente può rimuovere una row presente nella parent chain letta da `attach`.

Questa race non può creare inconsistenza perché `detach` può soltanto:

```text
remove paths
break possible cycles
```

non crearne di nuovi.

`attach` rimane l'action che deve usare:

```text
SERIALIZABLE
```

per proteggere la cycle-creating side dell'invariante.

`detach` non necessita dello stesso isolation level.

---

# 18. DETACH vs RENAME

`detach` non legge né modifica:

```text
canonical_name
```

e non richiede il live Object state gate.

Può quindi procedere indipendentemente da:

```text
RENAME
```

quando PostgreSQL non rileva altri conflitti relazionali.

---

# 19. DETACH vs DATA_CHANGE

`detach` non legge né modifica:

```text
properties_json
```

e non dipende dai runtime property values.

Può quindi procedere indipendentemente da:

```text
DATA_CHANGE
```

---

# 20. DETACH vs DELETE

Il protocollo completo di `delete Object` viene ratificato separatamente.

Per la same exact relation row, i normali row locks delle mutation:

```text
DELETE edge
```

serializzano `detach` con eventuali delete workflows che rimuovano la stessa edge.

Non viene introdotto alcun reciprocal endpoint lock in questo documento.

---

# 21. Nessun `object_changes` audit event

Il canonical Object snapshot ratificato contiene:

```text
canonical_name
template pin
properties
```

e non contiene ownership attachments.

Di conseguenza `detach` non deve essere registrato impropriamente come:

```text
DATA_CHANGE
SCHEMA_CHANGE
```

Non esiste attualmente un kind:

```text
DETACH
```

in `object_changes`.

Quindi:

```text
detach
    -> no object_changes event
```

Un eventuale audit storico dell'ownership graph richiederebbe un modello separato.

---

# 22. Isolation level

`detach` non richiede:

```text
SERIALIZABLE
```

La normale transaction isolation usata dal repository/UoW è sufficiente.

Baseline:

```text
READ COMMITTED
```

La consistenza dell'operation è concentrata nel singolo:

```text
DELETE exact edge
```

---

# 23. Nessuna specialized Unit of Work

A differenza di `attach`, `detach` non richiede:

```text
special isolation level
whole-action retry su SQLSTATE 40001
multi-step predicate stabilization
```

Il normale Object UoW transazionale è sufficiente.

Non viene introdotta una:

```text
ObjectDetachUnitOfWork
```

specializzata.

---

# 24. Protocollo transazionale candidato

```text
BEGIN

1. validate request shape:
   - parent_id != child_id
   - slot_name non-empty

2. DELETE FROM object_components
   WHERE:
       parent_object_id = P
       slot_name        = S
       child_object_id  = C
   RETURNING ...

3. if one row returned:
       changed = true

   if no row returned:
       changed = false
       idempotent no-op

4. COMMIT
```

Qualsiasi DB failure reale produce:

```text
ROLLBACK
```

---

# 25. Lock non richiesti

`detach Object` non richiede:

```text
FOR KEY SHARE parent Object
FOR KEY SHARE child Object

FOR NO KEY UPDATE Object

FOR UPDATE Object

FOR SHARE ObjectTemplateVersion

FOR SHARE DataTypeVersion

ownership graph lock

SERIALIZABLE transaction
```

Il solo coordination point necessario è la exact relation row interessata dal conditional DELETE.

---

# 26. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
exact-edge detach semantics

request identifies:
    parent_id
    slot_name
    child_id

idempotent no-op if exact edge absent

no implicit move

no schema/compatibility/cycle validation required
```

## PostgreSQL / relational model

Garantisce:

```text
relation identity state
    -> object_components row

endpoint referential integrity
    -> FKs

single ownership baseline
    -> PRIMARY KEY(child_object_id)

conditional mutation
    -> DELETE WHERE exact edge

same-row concurrency
    -> row locking of DELETE
```

## Concurrency protocol

Garantisce:

```text
DETACH vs DETACH serialization on same edge

DETACH vs SCHEMA_CHANGE serialization on same edge

stale detach cannot remove a different current edge

no graph-wide coordination
```

---

# 27. Verdetto DRAFT

> **DETACH è una exact-edge idempotent conditional delete.**
>
> La request identifica:
>
> ```text
> parent_object_id
> slot_name
> child_object_id
> ```
>
> e PostgreSQL esegue direttamente:
>
> ```sql
> DELETE ... WHERE exact P/S/C edge
> ```
>
> senza una precedente decision read.
>
> Se l'exact edge è già assente, l'operation è un no-op.
>
> Una stale detach non può eliminare un attachment più recente dello stesso child verso un altro owner/slot.
>
> Non sono necessari endpoint locks, effective schema resolution, child compatibility validation, cycle detection o SERIALIZABLE isolation.
>
> Il row lock acquisito naturalmente dal DELETE è sufficiente per coordinarsi con mutation concorrenti della stessa edge.
>
> `detach` non produce `object_changes`.
>
> Nessuna specialized UoW è necessaria.
>
> Nessun locking globale viene introdotto.
