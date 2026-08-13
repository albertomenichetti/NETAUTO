# Relationship DELETE — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `Relationship.DELETE`.**

Questo documento descrive:

```text
- semantica Domain/Application della delete runtime
- exact identity semantics
- righe lette e scritte
- interaction con Object lifecycle
- interaction con RelationshipDefinition lifecycle
- duplicate Relationship semantics
- race concorrenti
- isolation level
- lock strategy
- Unit of Work
- audit scope
- runtime immutability rule
```

Baseline di riferimento:

```text
Relationship — Modello Relazionale + Domain/Business Model RATIFICATO v1
Relationship CREATE — Concurrency Contract DRAFT v1
RelationshipDefinition DELETE — Concurrency Contract DRAFT v1
Object DELETE — Concurrency Contract DRAFT v1
```

---

# 2. Obiettivo dell'action

Input:

```text
relationship_id = R
```

L'action elimina esclusivamente:

```text
relationships(R)
```

Non modifica e non elimina:

```text
RelationshipDefinition
source Object
target Object
ObjectTemplate
ObjectTemplateVersion
ownership edges
other Relationship rows
```

---

# 3. Exact identity semantics

La Relationship runtime è identificata esclusivamente da:

```text
relationships.id
```

La delete deve quindi essere sempre eseguita per exact Relationship identity.

Non deve essere interpretata come delete per tuple:

```text
relationship_definition_id
source_object_id
target_object_id
```

perché tale tuple non è unique e Relationship duplicate sono ammesse.

---

# 4. Single-statement delete

La forma ratificata è:

```sql
DELETE FROM relationships
WHERE id = :relationship_id
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

# 5. Exact rows read

Non esiste una decision-read applicativa obbligatoria prima della mutation.

Non devono essere lette preventivamente:

```text
Relationship
RelationshipDefinition
source Object
target Object
ObjectTemplate
ObjectTemplateVersion
object_template_ancestry
```

per decidere se la delete sia ammessa.

---

# 6. Exact rows written

Una sola row può essere eliminata:

```text
relationships(R)
```

Nessun'altra tabella viene mutata.

---

# 7. Relationship assente

Se:

```sql
DELETE ... RETURNING
```

non restituisce alcuna row:

```text
RelationshipNotFound
```

Semantica Domain ratificata:

```text
delete missing Relationship
    -> NotFound
```

La delete non è idempotent-success su identity assente.

---

# 8. Nessuna endpoint validation

La delete non deve verificare:

```text
source Object exists
target Object exists
source compatibility
target compatibility
RelationshipDefinition exists
```

Eliminare una Relationship non introduce alcun nuovo binding.

Non richiede quindi admission validation.

---

# 9. Nessuna ancestry validation

Non deve essere interrogata:

```text
object_template_ancestry
```

La polymorphic compatibility è una regola di `Relationship.CREATE`, non di delete.

La delete rimuove semplicemente una Relationship già persistita.

---

# 10. Nessun lock sugli Object endpoint

Non serve acquisire explicit row lock su:

```text
source Object
target Object
```

La Relationship delete rimuove riferimenti verso gli Object e non modifica alcun loro stato.

Può quindi procedere concorrentemente con:

```text
Object.RENAME
Object.DATA_CHANGE
Object.SCHEMA_CHANGE
```

senza coordinamento aggiuntivo.

---

# 11. Nessun lock sulla RelationshipDefinition

Non serve acquisire explicit lock su:

```text
relationship_definitions
```

La Relationship delete non modifica la definition.

Può procedere concorrentemente con:

```text
RelationshipDefinition.RENAME
```

senza serializzazione semantica.

---

# 12. DELETE Relationship vs Object.DELETE

Le FK:

```text
relationships.source_object_id
    -> objects.id
    ON DELETE RESTRICT

relationships.target_object_id
    -> objects.id
    ON DELETE RESTRICT
```

impediscono la cancellazione degli Object endpoint finché la Relationship esiste.

La Relationship delete rimuove una di queste dependency rows.

---

# 13. Relationship delete prima di Object delete

Se:

```text
DELETE Relationship R
COMMIT
```

avviene prima, quella specifica reference verso source/target viene rimossa.

Una successiva:

```text
Object.DELETE
```

può procedere soltanto se non esistono altre Relationship o altre dependency `RESTRICT`.

La Relationship delete non garantisce da sola che l'Object sia diventato deletable.

---

# 14. Object delete mentre Relationship esiste

Finché R esiste:

```text
Object endpoint DELETE
    -> MUST FAIL
```

per FK `RESTRICT`.

La Relationship non viene cancellata automaticamente.

Questo preserva la regola Domain:

```text
Relationship is non-owning
```

e non appartiene alla lifecycle dell'Object.

---

# 15. Duplicate Relationship e Object delete

Dato:

```text
R1:
D / A -> B

R2:
D / A -> B
```

se viene eliminata soltanto:

```text
R1
```

rimane:

```text
R2
```

Quindi:

```text
DELETE A
DELETE B
```

rimangono bloccate dalla Relationship residua.

Ogni Relationship è una reference autonoma.

---

# 16. DELETE Relationship vs Object subtree DELETE

Scenario:

```text
subtree:
A
└── B

Relationship:
R: X -> B
```

Se prima viene completato:

```text
DELETE R
```

la specifica dependency verso B scompare.

La successiva subtree delete può procedere se nessun Object del subtree ha altre Relationship incidenti.

---

# 17. Relationship ancora presente durante subtree delete

Se R esiste quando la subtree delete tenta di eliminare B:

```text
FK RESTRICT
    -> subtree delete fails
```

Poiché `Object.DELETE` è atomica per l'intero subtree:

```text
whole subtree transaction
    -> ROLLBACK
```

Non deve esistere una partial subtree deletion.

---

# 18. DELETE Relationship vs RelationshipDefinition.DELETE

La FK:

```text
relationships.relationship_definition_id
    -> relationship_definitions.id
    ON DELETE RESTRICT
```

impedisce la delete della definition finché R esiste.

La Relationship delete rimuove quella dependency.

---

# 19. Relationship delete prima di Definition delete

Se:

```text
DELETE R
COMMIT
```

rimuove l'ultima Relationship che referenzia D, una successiva:

```text
RelationshipDefinition.DELETE D
```

può procedere.

Se restano altre Relationship che referenziano D:

```text
Definition.DELETE
    -> still fails
```

---

# 20. Nessun cascade verso la RelationshipDefinition

`Relationship.DELETE` non modifica:

```text
relationship_definitions
```

e non elimina automaticamente una definition diventata unused.

La cleanup workflow è sempre esplicita.

---

# 21. Cleanup esplicito

La lifecycle corretta è:

```text
DELETE Relationship(s)
COMMIT

then optionally:
    DELETE Object
```

oppure:

```text
DELETE Relationship(s)
COMMIT

then optionally:
    DELETE RelationshipDefinition
```

Non esiste un hidden aggregate cascade.

---

# 22. DELETE vs RelationshipDefinition.RENAME

Le due action sono indipendenti.

`RelationshipDefinition.RENAME` modifica:

```text
forward_name
reverse_name
```

`Relationship.DELETE` elimina:

```text
relationships(R)
```

La Relationship delete usa esclusivamente:

```text
relationships.id
```

e non dipende dai nomi della definition.

---

# 23. DELETE vs Object.RENAME

`Object.RENAME` modifica:

```text
canonical_name
```

La Relationship delete non usa il canonical name.

Le due action possono procedere concorrentemente.

---

# 24. DELETE vs Object.DATA_CHANGE

`Object.DATA_CHANGE` modifica:

```text
properties_json
```

La Relationship delete non usa le properties.

Le due action possono procedere concorrentemente.

---

# 25. DELETE vs Object.SCHEMA_CHANGE

`Object.SCHEMA_CHANGE` modifica:

```text
template_version
properties_json
```

e non modifica:

```text
Object.template_id
```

La Relationship delete non richiede comunque compatibility revalidation.

Le due action possono procedere concorrentemente.

---

# 26. DELETE vs DELETE stessa Relationship

Scenario:

```text
T1:
DELETE R

T2:
DELETE R
```

Una transaction elimina la row.

L'altra, dopo la serializzazione interna della DML, ottiene:

```text
0 rows RETURNING
```

e produce:

```text
RelationshipNotFound
```

Semantica:

```text
one success
one NotFound
```

---

# 27. DELETE vs DELETE Relationship duplicate

Dato:

```text
R1:
D / A -> B

R2:
D / A -> B
```

T1:

```text
DELETE R1
```

T2:

```text
DELETE R2
```

sono delete su identities diverse.

Devono poter procedere indipendentemente.

Non esiste:

```text
endpoint-pair lock
definition/source/target tuple gate
```

---

# 28. DELETE vs CREATE Relationship duplicate

Dato:

```text
R1:
D / A -> B
```

T1:

```text
DELETE R1
```

T2:

```text
CREATE R2:
D / A -> B
```

con:

```text
R1.id != R2.id
```

le action sono semanticamente indipendenti.

Risultato valido:

```text
R1 absent
R2 present
```

Non esiste una semantica implicita:

```text
delete relation between A and B
```

La delete è per Relationship identity.

---

# 29. Nessuna delete by tuple implicita

Non deve essere introdotta una action ambigua:

```text
DELETE Relationship
WHERE definition = D
  AND source = A
  AND target = B
```

perché con Relationship duplicate non sarebbe chiaro se significhi:

```text
delete one arbitrary match
```

oppure:

```text
delete all matches
```

Eventuali bulk delete devono essere ratificate come action distinte.

---

# 30. DELETE vs CREATE stesso Relationship ID

Se una concurrent create tenta:

```text
id = R
```

mentre la precedente Relationship R viene cancellata, la:

```text
PRIMARY KEY(id)
```

e il normale ordering transazionale determinano l'esito.

Non serve application locking.

---

# 31. ID reuse non ratificato

Dopo una committed delete, il database potrebbe tecnicamente accettare in futuro una nuova Relationship con lo stesso:

```text
id
```

se l'ID generation lo producesse.

Non viene ratificata in questo documento una regola:

```text
Relationship IDs can never be reused historically
```

perché non esiste un audit/tombstone model Relationship che la renda oggi enforceable.

Se questa proprietà sarà desiderata, richiederà una decisione separata.

---

# 32. Nessuna inbound dependency su `relationships.id`

Nel modello corrente non è stata ratificata alcuna tabella con FK verso:

```text
relationships.id
```

Quindi Relationship è attualmente una leaf reference entity.

La delete:

```text
removes outward FK references
```

ma non è bloccata da altre dependency inbound.

Non esiste oggi un domain error:

```text
RelationshipInUse
```

---

# 33. Future inbound references

Se in futuro un altro aggregate referenzierà:

```text
relationships.id
```

il contratto `Relationship.DELETE` dovrà essere riesaminato.

Non deve essere assunto che la leaf semantics sia eterna.

---

# 34. Nessun explicit row lock

Non deve essere usato:

```text
SELECT R
FOR UPDATE
```

prima della delete.

Il singolo:

```sql
DELETE ... RETURNING
```

è già il coordination point necessario.

Non fanno parte del protocollo applicativo:

```text
FOR KEY SHARE
FOR SHARE
FOR NO KEY UPDATE
FOR UPDATE
```

---

# 35. Nessun lock ordering contract

Non vengono acquisiti explicit multi-row lock.

Quindi:

```text
no application canonical lock ordering
```

è richiesto.

---

# 36. Isolation level

È sufficiente:

```text
READ COMMITTED
```

La action è:

```text
single exact-row DELETE
```

senza:

```text
recursive predicate
cardinality check
compatibility decision
read-modify-write
MAX + 1
```

Non serve:

```text
REPEATABLE READ
SERIALIZABLE
```

---

# 37. Nessuna specialized Unit of Work

Una normale transaction è sufficiente:

```text
BEGIN
READ COMMITTED

DELETE FROM relationships
WHERE id = :relationship_id
RETURNING id

if no row:
    RelationshipNotFound

COMMIT
```

Non esiste requisito di:

```text
special isolation
serialization retry
custom lock ordering
```

---

# 38. Audit

Non è stato ratificato un audit model specifico per:

```text
Relationship
RelationshipDefinition
```

Quindi:

```text
Relationship.DELETE
    -> no audit side effect
```

Non deve essere usato:

```text
object_changes
```

per auditare la Relationship delete.

---

# 39. Runtime mutability rule

Con questa action viene chiuso il punto ancora aperto sulla mutabilità della Relationship runtime.

Dopo la create sono immutabili:

```text
relationship_definition_id
source_object_id
target_object_id
```

Non esiste una normale action:

```text
Relationship.UPDATE
Relationship.MOVE
Relationship.RETARGET
```

---

# 40. Cambiare definition o endpoint

Per cambiare:

```text
relationship_definition_id
source_object_id
target_object_id
```

la workflow è:

```text
DELETE old Relationship
CREATE new Relationship
```

Sono due action distinte.

Non vengono interpretate automaticamente come una singola mutation atomica.

---

# 41. Nessuna replace atomica implicita

Se in futuro servirà una operation:

```text
replace Relationship atomically
```

dovrà essere ratificata come nuova domain action.

Non deve essere implementata implicitamente nascondendo:

```text
DELETE + CREATE
```

dietro una generica `UPDATE`.

---

# 42. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
exact Relationship identity input

RelationshipNotFound semantics

no tuple-based delete ambiguity

runtime structural immutability
```

## PostgreSQL / relational model

Garantisce:

```text
Relationship identity
    -> PRIMARY KEY

Object delete protection while Relationship exists
    -> source/target FK RESTRICT

Definition delete protection while Relationship exists
    -> definition FK RESTRICT
```

## Concurrency protocol

Garantisce intenzionalmente:

```text
single-statement exact-row mutation
```

senza explicit pre-lock o validation.

---

# 43. Lock picture

```text
explicit application row locks:
    NONE
```

```text
endpoint reads:
    NONE
```

```text
definition reads:
    NONE
```

```text
ancestry reads:
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

# 44. Protocollo transazionale candidato

```text
BEGIN
READ COMMITTED

1. DELETE FROM relationships
   WHERE id = :relationship_id
   RETURNING id

2. if zero rows:
       FAIL RelationshipNotFound

3. COMMIT
```

Non esiste:

```text
select-before-delete
endpoint lookup
definition lookup
compatibility validation
ancestry traversal
explicit row locking
```

---

# 45. Verdetto DRAFT

> **`Relationship.DELETE` elimina esclusivamente una exact Relationship identificata tramite `relationships.id`.**
>
> La action usa un singolo `DELETE ... RETURNING`; non esegue select-before-delete, endpoint lookup, definition lookup, ancestry validation o compatibility revalidation.
>
> Relationship assente produce `RelationshipNotFound`.
>
> La delete non elimina Object, RelationshipDefinition, ownership edges o altre Relationship duplicate.
>
> Rimuovendo la Relationship vengono semplicemente rilasciate le FK `RESTRICT` che potevano impedire `Object.DELETE` o `RelationshipDefinition.DELETE`; tali delete possono procedere successivamente soltanto se non esistono altre references.
>
> Concurrent mutation di Object e rename della definition non richiedono coordinamento.
>
> Due delete della stessa Relationship producono un solo successo e un successivo `NotFound`; delete di Relationship duplicate distinte sono indipendenti.
>
> L'action è sempre by Relationship identity e mai implicitamente by `(definition, source, target)`.
>
> Nessun explicit row lock, nessun lock ordering, nessun `SERIALIZABLE` e nessuna specialized Unit of Work sono necessari; `READ COMMITTED` è sufficiente.
>
> Nessun audit side effect viene prodotto.
>
> `relationship_definition_id`, `source_object_id` e `target_object_id` sono immutabili dopo la create. Modificarli richiede explicit `DELETE + CREATE`; non esiste una generica `Relationship.UPDATE` implicita.
