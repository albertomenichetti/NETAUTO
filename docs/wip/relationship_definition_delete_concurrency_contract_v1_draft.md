# RelationshipDefinition DELETE — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `RelationshipDefinition.DELETE`.**

Questo documento descrive:

```text
- semantica Domain/Application della delete
- righe lette e scritte
- usage constraint
- race concorrenti
- interaction con Relationship.CREATE
- interaction con RENAME
- interaction con ObjectTemplate lifecycle
- isolation level
- lock strategy
- Unit of Work
- audit scope
```

Baseline di riferimento:

```text
Relationship — Modello Relazionale + Domain/Business Model RATIFICATO v1
RelationshipDefinition CREATE — Concurrency Contract DRAFT v1
RelationshipDefinition RENAME — Concurrency Contract DRAFT v1
```

---

# 2. Obiettivo dell'action

Input:

```text
relationship_definition_id = D
```

L'action elimina esattamente una:

```text
relationship_definitions(D)
```

row.

La delete è ammessa soltanto se la definition non è referenziata da alcuna Relationship runtime.

Non viene cancellata automaticamente alcuna:

```text
Relationship
Object
ObjectTemplate
```

---

# 3. Usage invariant

Una RelationshipDefinition è deletable se e solo se:

```text
definition exists
AND
no relationships row references definition.id
```

La dependency è espressa fisicamente da:

```text
relationships.relationship_definition_id
    -> relationship_definitions.id
    ON DELETE RESTRICT
```

Questa FK è la final consistency authority.

---

# 4. Nessun pre-check `unused`

Non deve essere usato come concurrency mechanism un pattern:

```text
SELECT COUNT(*)
FROM relationships
WHERE relationship_definition_id = :id

if count == 0:
    DELETE definition
```

Questo introdurrebbe un race fra:

```text
usage check
```

e:

```text
DELETE
```

La FK `RESTRICT` esprime già la business rule in modo autorevole.

---

# 5. Single-statement delete

La forma candidata è:

```sql
DELETE FROM relationship_definitions
WHERE id = :id
RETURNING id;
```

Il `DELETE` stesso è:

```text
lookup
mutation
coordination point
```

Non serve un select-before-delete.

---

# 6. Exact rows read

Non esiste una decision-read applicativa obbligatoria prima della mutation.

Non devono essere lette preventivamente:

```text
RelationshipDefinition
Relationships
ObjectTemplate
Object
object_template_ancestry
```

per stabilire se la delete sia ammessa.

La DML + FK determinano l'esito.

---

# 7. Exact rows written

Una sola row può essere eliminata:

```text
relationship_definitions(D)
```

Non vengono mutate:

```text
relationships
objects
object_templates
```

---

# 8. Definition inesistente

Con:

```sql
DELETE ... RETURNING
```

se non viene restituita alcuna row:

```text
RelationshipDefinitionNotFound
```

Semantica Domain ratificata:

```text
delete missing definition
    -> NotFound
```

La delete non è idempotent-success su identity assente.

---

# 9. Definition in uso

Se esiste almeno una:

```text
relationships.relationship_definition_id = D
```

la delete deve fallire.

Non importa se esistono:

```text
1
10
1000
```

Relationship.

La business condition è semplicemente:

```text
at least one reference
    -> delete prohibited
```

La FK `RESTRICT` è final authority.

---

# 10. Error mapping `in use`

Una violation della FK:

```text
relationships.relationship_definition_id
    -> relationship_definitions.id
```

durante la delete può essere mappata semanticamente a:

```text
RelationshipDefinitionInUse
```

o equivalente domain error.

Il nome concreto dell'errore applicativo non modifica il concurrency contract.

---

# 11. DELETE vs CREATE Relationship

Race fondamentale:

```text
T1:
DELETE RelationshipDefinition D

T2:
CREATE Relationship R referencing D
```

Sono ammessi due ordini seriali.

---

# 12. CREATE Relationship vince

Se la Relationship stabilisce per prima:

```text
relationship_definition_id = D
```

la definition diventa referenced.

La successiva:

```text
DELETE D
```

deve fallire per:

```text
FK RESTRICT
```

Semantica:

```text
Relationship exists
Definition survives
```

---

# 13. DELETE Definition vince

Se la definition viene cancellata per prima:

```text
DELETE D
COMMIT
```

la successiva Relationship create che tenta:

```text
relationship_definition_id = D
```

deve fallire perché la FK target non esiste più.

Semantica:

```text
Definition absent
Relationship CREATE fails
```

---

# 14. Nessun application-level usage lock

Per la race:

```text
Definition.DELETE
vs
Relationship.CREATE
```

non deve essere introdotto un:

```text
definition usage mutex
relationship scan lock
global RelationshipDefinition gate
```

La referential integrity PostgreSQL esprime già il reciprocal consistency contract necessario.

Il futuro `Relationship.CREATE` deve rispettare questa baseline senza introdurre coordinamento più forte del necessario.

---

# 15. DELETE vs RENAME stessa definition

`RelationshipDefinition.RENAME` usa:

```text
relationship_definitions(id)
FOR NO KEY UPDATE
```

La delete della stessa row entra in conflitto con la mutation/lock sulla definition.

Quindi le due action si serializzano.

---

# 16. RENAME prima

Se rename stabilizza la definition per prima:

```text
FOR NO KEY UPDATE
```

la delete deve attendere.

Dopo il commit della rename:

```text
DELETE
```

può:

```text
succeed if definition unused
```

oppure:

```text
fail if definition referenced
```

I nuovi nomi non cambiano l'usage invariant.

---

# 17. DELETE prima

Se delete elimina la definition per prima:

```text
definition disappears
```

una rename successiva, dopo la propria rilettura, produce:

```text
RelationshipDefinitionNotFound
```

Non esiste lost update o rename di una row già cancellata.

---

# 18. DELETE vs DELETE stessa definition

Due concurrent:

```text
DELETE D
```

competono sulla stessa row.

Una transaction elimina la row.

L'altra, dopo la serializzazione, ottiene:

```text
0 rows returned
```

e quindi:

```text
RelationshipDefinitionNotFound
```

Non viene prodotta una seconda successful delete.

---

# 19. DELETE vs CREATE RelationshipDefinition stesso id

Se una create concorrente tenta di usare lo stesso:

```text
id = D
```

la PK/MVCC determinano l'ordine valido.

Non serve coordinamento specifico.

La:

```text
PRIMARY KEY(id)
```

rimane final authority sull'identity.

---

# 20. DELETE vs CREATE RelationshipDefinition stessa business tuple

La delete può rimuovere una definition con tuple:

```text
(source_template_id,
 target_template_id,
 forward_name,
 reverse_name)
```

mentre una concurrent create tenta di riutilizzare la stessa tuple.

Non serve un application-level tuple lock.

La:

```text
UNIQUE(...)
```

e il normale ordine transazionale determinano se la create debba attendere/fallire o possa riuscire dopo la delete.

---

# 21. DELETE vs ObjectTemplate.DELETE

Una RelationshipDefinition esistente mantiene FK verso:

```text
source_template_id
target_template_id
```

Quindi finché D esiste:

```text
ObjectTemplate referenced by D
    -> ObjectTemplate DELETE must fail
```

per FK `RESTRICT`.

---

# 22. Definition delete prima di ObjectTemplate delete

Se:

```text
DELETE D
COMMIT
```

rimuove il riferimento e non esistono altre dependency, una successiva:

```text
ObjectTemplate DELETE
```

può procedere.

Non serve un coordinamento esplicito fra le due action.

---

# 23. ObjectTemplate delete mentre D esiste

Se una ObjectTemplate delete compete mentre D la referenzia:

```text
ObjectTemplate DELETE
    -> blocked/fails by FK RESTRICT
```

La RelationshipDefinition non deve acquisire lock aggiuntivi sul template durante la propria delete.

---

# 24. Nessun explicit row lock applicativo

Non deve essere usato:

```text
SELECT D
FOR UPDATE
```

prima del:

```text
DELETE D
```

Il `DELETE` stesso è già la mutation e acquisisce il necessario row-level coordination nel database.

Quindi il protocollo applicativo non richiede:

```text
FOR SHARE
FOR KEY SHARE
FOR NO KEY UPDATE
FOR UPDATE
```

espliciti.

---

# 25. Nessuna Relationship scan

Non devono essere eseguite query del tipo:

```text
SELECT relationships
WHERE relationship_definition_id = D
FOR ...
```

come prerequisito della delete.

Motivazione:

```text
FK RESTRICT
```

gestisce:

```text
current usage
+
new concurrent usage
```

in modo più autorevole di un pre-scan applicativo.

---

# 26. Nessun ancestry / Object read

La delete non modifica:

```text
source_template_id
target_template_id
```

perché elimina l'intera definition.

Non deve quindi leggere:

```text
object_template_ancestry
objects
```

né rivalidare compatibility.

---

# 27. Isolation level

È sufficiente:

```text
READ COMMITTED
```

L'action è:

```text
single exact DELETE
+
FK RESTRICT
```

Non contiene:

```text
recursive predicate
MAX + 1
check-then-act
multi-row write skew
```

che richiedano isolation più forte.

---

# 28. Lock ordering

Non vengono acquisiti explicit multi-row lock.

Quindi:

```text
no application canonical lock ordering
```

è necessario.

---

# 29. Nessuna specialized Unit of Work

Una normale transaction è sufficiente:

```text
BEGIN

DELETE FROM relationship_definitions
WHERE id = :id
RETURNING id

if no row:
    RelationshipDefinitionNotFound

COMMIT
```

Una FK violation viene mappata a:

```text
RelationshipDefinitionInUse
```

o equivalente.

Non esiste un requisito di:

```text
special isolation
serialization retry
custom lock ordering
```

---

# 30. Audit

Non è stato ratificato un audit model specifico per:

```text
RelationshipDefinition
Relationship
```

Quindi:

```text
RelationshipDefinition.DELETE
    -> no audit side effect
```

Non deve essere usato:

```text
object_changes
```

per auditare la definition delete.

---

# 31. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
exact definition identity input

NotFound semantics

mapping of FK violation to DefinitionInUse
```

## PostgreSQL / relational model

Garantisce:

```text
definition identity
    -> PRIMARY KEY

definition usage protection
    -> relationships FK RESTRICT

template dependency
    -> source/target template FK RESTRICT

business tuple consistency
    -> UNIQUE
```

## Concurrency protocol

Garantisce intenzionalmente:

```text
single-statement mutation
constraint-driven race resolution
```

senza pre-check e senza explicit application row locks.

---

# 32. Lock picture

```text
explicit application row locks:
    NONE
```

```text
relationship scans:
    NONE
```

```text
isolation:
    READ COMMITTED
```

```text
specialized UoW:
    NONE
```

```text
retry contract:
    NONE beyond normal transaction/error handling
```

---

# 33. Protocollo transazionale candidato

```text
BEGIN
READ COMMITTED

1. DELETE FROM relationship_definitions
   WHERE id = :id
   RETURNING id

2. if zero rows:
       FAIL RelationshipDefinitionNotFound

3. if FK RESTRICT violation from relationships:
       FAIL RelationshipDefinitionInUse

4. COMMIT
```

Non esiste:

```text
pre-read
usage count
relationship locking
template locking
ancestry validation
```

---

# 34. Verdetto DRAFT

> **`RelationshipDefinition.DELETE` è una single-statement exact-row delete.**
>
> Non viene eseguito alcun pre-check applicativo per stabilire se la definition sia unused.
>
> La FK `relationships.relationship_definition_id -> relationship_definitions.id ON DELETE RESTRICT` è la final authority: una definition referenziata non può essere cancellata.
>
> `DELETE ... RETURNING` distingue direttamente successful delete da `RelationshipDefinitionNotFound`.
>
> La race con `Relationship.CREATE` è risolta referenzialmente: se la Relationship stabilisce prima il riferimento, la definition delete fallisce; se la definition viene eliminata prima, la Relationship create fallisce FK.
>
> Rename e delete della stessa definition si serializzano sulla exact definition row.
>
> Non vengono scandite o lockate le Relationship runtime.
>
> La delete non richiede Object, ObjectTemplateVersion o ancestry validation.
>
> Nessun explicit row lock, nessun `SERIALIZABLE`, nessuna specialized Unit of Work e nessun audit side effect sono necessari.
>
> `READ COMMITTED` è sufficiente.
