# RelationshipDefinition RENAME — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `RelationshipDefinition.RENAME`.**

Questo documento descrive:

```text
- semantica Domain/Application della rename
- righe lette e scritte
- concurrency gate
- invarianti
- no-op semantics
- interaction con Relationship runtime
- race concorrenti
- isolation level
- lock ordering
- Unit of Work
- audit scope
```

Baseline di riferimento:

```text
Relationship — Modello Relazionale + Domain/Business Model RATIFICATO v1
RelationshipDefinition CREATE — Concurrency Contract DRAFT v1
```

---

# 2. Obiettivo dell'action

`RelationshipDefinition.RENAME` modifica esclusivamente i nomi direzionali della definition:

```text
forward_name
reverse_name
```

Uno solo o entrambi possono cambiare.

Non modifica:

```text
id
source_template_id
target_template_id
```

---

# 3. Campi immutabili e mutabili

Baseline ratificata:

```text
immutable:
    id
    source_template_id
    target_template_id

mutable:
    forward_name
    reverse_name
```

Il cambio di source/target template non è una rename e non è una mutation ammessa della stessa RelationshipDefinition.

---

# 4. Exact row letta

L'action deve acquisire la exact definition row prima di qualsiasi decision read:

```sql
SELECT
    id,
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
FROM relationship_definitions
WHERE id = :id
FOR NO KEY UPDATE;
```

Se la row non esiste:

```text
RelationshipDefinitionNotFound
```

---

# 5. Concurrency gate

La exact:

```text
relationship_definitions(id)
```

row è il concurrency gate dell'action.

Il gate deve essere acquisito:

```text
before
    current-name comparison
    candidate validation
    no-op decision
    UPDATE
```

Non deve essere usato un pattern:

```text
read current state
then later lock/update
```

perché produrrebbe decisioni basate su uno stato potenzialmente stale.

---

# 6. Perché `FOR NO KEY UPDATE`

La rename modifica soltanto:

```text
forward_name
reverse_name
```

e non modifica:

```text
relationship_definitions.id
```

che è la key referenziata da:

```text
relationships.relationship_definition_id
```

Quindi non è necessario il lock più forte:

```text
FOR UPDATE
```

`FOR NO KEY UPDATE` è sufficiente come gate della mutable non-key state della definition.

---

# 7. Candidate state

Dopo il lock:

```text
current:
    forward_name = F0
    reverse_name = R0
```

l'application costruisce:

```text
candidate:
    forward_name = F1
    reverse_name = R1
```

La candidate deve rispettare:

```text
F1 <> ''
R1 <> ''
```

e la business uniqueness:

```text
(
    source_template_id,
    target_template_id,
    F1,
    R1
)
```

---

# 8. No-op semantics

Se:

```text
F1 == F0
AND
R1 == R0
```

la rename è un idempotent no-op.

Semantica:

```text
no UPDATE
no audit
COMMIT
```

Non deve essere generata una write inutile.

---

# 9. Exact row scritta

Se la candidate differisce dal current state, viene aggiornata una sola row:

```text
relationship_definitions(id)
```

Forma concettuale:

```sql
UPDATE relationship_definitions
SET
    forward_name = :forward_name,
    reverse_name = :reverse_name
WHERE id = :id;
```

Gli endpoint template non devono comparire nel `SET`.

---

# 10. CHECK authority sui nomi

La candidate deve continuare a rispettare:

```text
CHECK(forward_name <> '')
CHECK(reverse_name <> '')
```

Non viene introdotta alcuna semantica implicita di:

```text
TRIM
case-folding
Unicode normalization
case-insensitive comparison
```

---

# 11. UNIQUE authority

La candidate deve rispettare:

```text
UNIQUE(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

La UNIQUE è final authority sotto race.

Un eventuale:

```text
SELECT duplicate
```

può essere usato per UX/error mapping ma non è concurrency authority.

---

# 12. Concurrent rename della stessa definition

Scenario:

```text
D current:
foo / bar
```

T1:

```text
rename D -> x / y
```

T2:

```text
rename D -> m / n
```

Entrambe acquisiscono:

```text
D FOR NO KEY UPDATE
```

Una transaction procede per prima.

L'altra attende e prende la propria decisione sul current state successivo.

Non deve esistere lost update.

Il risultato corrisponde a un ordine seriale:

```text
T1 then T2
```

oppure:

```text
T2 then T1
```

---

# 13. Definitions differenti non condividono un gate

Due rename su definitions differenti:

```text
D1
D2
```

non devono essere serializzate soltanto perché condividono:

```text
source_template_id
target_template_id
```

Ogni definition usa la propria row come gate.

Eventuali collisioni sulla business tuple sono delegate alla UNIQUE.

---

# 14. Concurrent rename verso la stessa business tuple

Esempio:

```text
D1:
A -> B / foo / bar

D2:
A -> B / x / y

D3:
A -> B / m / n
```

T1:

```text
rename D2 -> q / r
```

T2:

```text
rename D3 -> q / r
```

D2 e D3 hanno row lock indipendenti.

Non deve essere introdotto un lock comune su:

```text
source ObjectTemplate
target ObjectTemplate
template pair
```

La:

```text
UNIQUE(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

risolve il conflitto.

Una rename può riuscire; l'altra può fallire per unique violation.

---

# 15. RENAME vs CREATE RelationshipDefinition

Scenario:

```text
T1:
rename existing D -> tuple X

T2:
create new definition with tuple X
```

Non serve coordinamento esplicito fra le due action.

La UNIQUE rimane final authority.

Non deve essere introdotto un global/template-pair lock per prevenire questa race.

---

# 16. Relationship runtime già esistenti

La rename è ammessa anche quando la definition è referenziata da:

```text
relationships
```

Le Relationship runtime persistono:

```text
relationship_definition_id
```

e non snapshot locali di:

```text
forward_name
reverse_name
```

Quindi una rename non richiede:

```text
SELECT relationships
lock relationships
update relationships
```

---

# 17. Effetto sui nomi osservati dalle Relationship esistenti

Dopo il commit della rename:

```text
relationship_definition_id
```

rimane invariato.

Le VIEW/query che joinano la current definition vedranno:

```text
new forward_name
new reverse_name
```

anche per Relationship runtime create prima della rename.

Non esiste data migration delle Relationship.

---

# 18. Nessuna compatibility revalidation

La rename non modifica:

```text
source_template_id
target_template_id
```

Quindi non modifica:

```text
source compatibility predicate
target compatibility predicate
```

Non devono essere interrogati o rivalidati:

```text
Object
object_template_ancestry
Relationship runtime
```

---

# 19. Nessun ObjectTemplate lock

La rename non crea né modifica i riferimenti:

```text
source_template_id
target_template_id
```

Non servono explicit lock su:

```text
object_templates
```

Le FK esistenti restano invariate.

---

# 20. Nessun ancestry lock/read

La rename è nominale.

Non modifica il type system della definition.

Quindi:

```text
object_template_ancestry
relationship_definition_endpoints
```

non devono essere usate come decision source della rename.

---

# 21. RENAME vs CREATE Relationship runtime

`Relationship.CREATE` usa la definition per la structural compatibility:

```text
source_template_id
target_template_id
```

Questi campi sono immutabili.

`RelationshipDefinition.RENAME` modifica soltanto:

```text
forward_name
reverse_name
```

Quindi le due action non devono essere semanticamente serializzate.

Una Relationship può essere creata mentre la definition viene rinominata.

Dopo il commit della rename, la Relationship sarà osservata con i nuovi nomi.

---

# 22. Reciprocal requirement per Relationship.CREATE

Il futuro concurrency contract di:

```text
Relationship.CREATE
```

deve rispettare:

```text
CREATE Relationship
    may proceed concurrently with Definition.RENAME

CREATE Relationship
    must coordinate safely with Definition.DELETE
```

Non deve essere introdotto nel create runtime un lock inutilmente incompatibile con:

```text
Definition.RENAME
    -> FOR NO KEY UPDATE
```

Il lock concreto verrà ratificato nell'action `Relationship.CREATE`.

---

# 23. RENAME vs DELETE RelationshipDefinition

Rename e delete della stessa definition devono serializzarsi sulla exact definition row.

Se rename acquisisce per prima:

```text
FOR NO KEY UPDATE
```

la delete deve attendere il proprio conflicting gate.

Dopo la rename, la delete potrà:

```text
succeed if unused
```

oppure:

```text
fail because Relationship FK RESTRICT
```

Se la delete vince prima:

```text
definition disappears
```

e la rename successiva produce:

```text
RelationshipDefinitionNotFound
```

---

# 24. RENAME vs ObjectTemplate lifecycle

La rename non modifica i template endpoint e non crea nuovi template reference.

Quindi non richiede coordinamento specifico con:

```text
ObjectTemplate publish
ObjectTemplate deprecate
ObjectTemplate create-next
```

La eventuale delete dei referenced ObjectTemplate è già bloccata dalle FK della definition stessa.

---

# 25. Isolation level

È sufficiente:

```text
READ COMMITTED
```

Il protocollo usa:

```text
one exact row gate
+
UNIQUE final authority
```

Non esistono recursive o multi-row predicates da proteggere.

Non serve:

```text
REPEATABLE READ
SERIALIZABLE
```

---

# 26. Lock ordering

L'action acquisisce una sola explicit row lock:

```text
relationship_definitions(id)
FOR NO KEY UPDATE
```

Quindi non serve un canonical multi-row lock ordering contract.

---

# 27. Nessuna specialized Unit of Work

Una normale transaction è sufficiente:

```text
BEGIN

SELECT exact definition
FOR NO KEY UPDATE

derive candidate
validate candidate

if no-op:
    COMMIT
else:
    UPDATE names
    COMMIT
```

Non esiste un requisito specifico di:

```text
special isolation
serialization retry
multi-row locking
```

---

# 28. Audit

Non è stato ratificato un audit model specifico per:

```text
RelationshipDefinition
Relationship
```

Quindi:

```text
RelationshipDefinition.RENAME
    -> no audit side effect
```

Non deve essere riutilizzato:

```text
object_changes
```

per la history della definition.

---

# 29. Protocollo transazionale candidato

```text
BEGIN
READ COMMITTED

1. SELECT exact RelationshipDefinition
   WHERE id = :id
   FOR NO KEY UPDATE

2. if missing:
       FAIL RelationshipDefinitionNotFound

3. derive candidate:
       forward_name
       reverse_name

4. validate:
       forward_name <> ''
       reverse_name <> ''

5. if candidate == current names:
       no-op
       COMMIT

6. UPDATE exact definition row
       SET forward_name = ...
           reverse_name = ...

7. UNIQUE constraint remains final authority

8. COMMIT
```

---

# 30. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
only forward/reverse names are mutable

candidate construction

non-empty semantic validation

no-op detection

RelationshipDefinitionNotFound semantics
```

## PostgreSQL / relational model

Garantisce:

```text
exact definition identity
    -> PRIMARY KEY

non-empty names
    -> CHECK

business tuple uniqueness
    -> UNIQUE

Relationship reference stability
    -> FK relationship_definition_id
```

## Concurrency protocol

Garantisce:

```text
same-definition rename serialization
    -> FOR NO KEY UPDATE

different-definition independence
    -> no shared gate

cross-definition tuple collision
    -> UNIQUE final authority
```

---

# 31. Lock picture

```text
relationship_definitions(id)
    -> FOR NO KEY UPDATE
```

Non vengono lockate:

```text
relationships
objects
object_templates
object_template_versions
object_template_ancestry
```

Isolation:

```text
READ COMMITTED
```

Specialized UoW:

```text
NONE
```

Retry contract:

```text
NONE beyond normal transaction/error handling
```

---

# 32. Verdetto DRAFT

> **`RelationshipDefinition.RENAME` modifica esclusivamente `forward_name` e/o `reverse_name`; source e target template restano immutabili.**
>
> La exact definition row viene acquisita `FOR NO KEY UPDATE` prima di qualsiasi decision read e costituisce il concurrency gate dell'action.
>
> Concurrent rename della stessa definition viene serializzata senza lost update.
>
> Definitions differenti non vengono serializzate fra loro; eventuali collisioni sulla business tuple sono risolte dalla `UNIQUE(source_template_id, target_template_id, forward_name, reverse_name)`.
>
> Se i candidate names coincidono con il current state, la rename è un idempotent no-op e non produce UPDATE.
>
> Le Relationship runtime già esistenti non vengono lette, bloccate o aggiornate: mantengono lo stesso `relationship_definition_id` e osservano i nuovi nomi dopo il commit.
>
> La rename non modifica compatibility e non richiede Object, ObjectTemplate, ObjectTemplateVersion o ancestry lock.
>
> `Relationship.CREATE` dovrà poter procedere concorrentemente con la rename e coordinarsi separatamente con Definition.DELETE.
>
> `RelationshipDefinition.RENAME` e `RelationshipDefinition.DELETE` della stessa definition si serializzano sulla definition row.
>
> `READ COMMITTED` è sufficiente; non serve una specialized Unit of Work.
>
> Nessun audit side effect viene prodotto finché non viene ratificato un audit model specifico.
