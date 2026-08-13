# Relationship CREATE — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `Relationship.CREATE`.**

Questo documento descrive:

```text
- semantica Domain/Application della create runtime
- righe lette e scritte
- polymorphic compatibility
- interaction con Object lifecycle
- interaction con RelationshipDefinition lifecycle
- duplicate semantics
- race concorrenti
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
RelationshipDefinition DELETE — Concurrency Contract DRAFT v1
Object DELETE — Concurrency Contract DRAFT v1
Object SCHEMA_CHANGE — Concurrency Contract DRAFT v1
```

---

# 2. Obiettivo dell'action

`Relationship.CREATE` crea una singola row:

```text
relationships
-------------
id
relationship_definition_id
source_object_id
target_object_id
```

Non modifica:

```text
RelationshipDefinition
source Object
target Object
ObjectTemplate
ObjectTemplateVersion
ownership graph
```

---

# 3. Input

Input concettuale:

```text
relationship_id = R
relationship_definition_id = D
source_object_id = S
target_object_id = T
```

La Relationship identity è:

```text
relationships.id
```

La tuple:

```text
(D, S, T)
```

non è identity e non è unique.

---

# 4. Invarianti Domain

Devono valere:

```text
R unique

D exists
S exists
T exists

S != T

S.template_id
    compatible with D.source_template_id

T.template_id
    compatible with D.target_template_id
```

Le Relationship duplicate sono esplicitamente ammesse.

---

# 5. Self-relationship runtime vietata

La create deve rifiutare:

```text
source_object_id == target_object_id
```

Questa regola può essere validata direttamente sull'input.

Il database mantiene comunque la final authority tramite:

```text
CHECK(source_object_id <> target_object_id)
```

---

# 6. Duplicate Relationship ammesse

Non deve essere eseguita alcuna query:

```text
SELECT relationships
WHERE relationship_definition_id = D
  AND source_object_id = S
  AND target_object_id = T
```

per verificare l'assenza di duplicati.

Sono valide contemporaneamente:

```text
R1:
D / S -> T

R2:
D / S -> T
```

purché:

```text
R1.id != R2.id
```

---

# 7. Exact rows lette

La validation richiede concettualmente i seguenti facts autorevoli:

```text
RelationshipDefinition D:
    source_template_id
    target_template_id

Object S:
    template_id

Object T:
    template_id
```

e due compatibility predicates tramite ancestry.

Non servono:

```text
Object.template_version
Object.properties_json
Object.canonical_name
RelationshipDefinition.forward_name
RelationshipDefinition.reverse_name
other Relationships
object_components
effective Object schema
```

---

# 8. Exact rows scritte

Una sola row:

```text
relationships(R)
```

Forma concettuale:

```sql
INSERT INTO relationships (
    id,
    relationship_definition_id,
    source_object_id,
    target_object_id
)
VALUES (...);
```

---

# 9. Structural facts immutabili

La action si basa su tre proprietà ratificate:

```text
Object.template_id
    immutable for Object lifetime

RelationshipDefinition.source_template_id
RelationshipDefinition.target_template_id
    immutable for definition lifetime

ObjectTemplate parent lineage
    identity-stable
```

Questi facts determinano la Relationship compatibility.

---

# 10. Conseguenza concurrency

Fra validation e INSERT, i structural facts che determinano la compatibility non possono essere modificati da normali mutation concorrenti.

Possono soltanto:

```text
continue to exist
or
the referenced identity can be deleted
```

La scomparsa delle referenced identities viene intercettata dalle FK dell'INSERT.

Per questo non serve stabilizzare i facts tramite explicit row lock.

---

# 11. Polymorphic compatibility

La compatibility è definita come:

```text
compatible(actual_template, declared_template)
```

se:

```text
actual_template == declared_template
OR
actual_template transitively derives from declared_template
```

La regola viene applicata indipendentemente ai due endpoint.

---

# 12. Source compatibility

Deve valere:

```text
compatible(
    S.template_id,
    D.source_template_id
)
```

Esempio:

```text
Device
  ^
  |
Router
```

con definition:

```text
Device -> Network
```

un Object `Router` è valido come SOURCE.

---

# 13. Target compatibility

Deve valere:

```text
compatible(
    T.template_id,
    D.target_template_id
)
```

La stessa subtype admission semantics vale simmetricamente sul TARGET.

---

# 14. Compatibility su entrambi i lati

Esempio:

```text
Device
  ^
  |
Router

Network
  ^
  |
VlanNetwork
```

Definition:

```text
Device -> Network
```

Candidate Relationship:

```text
RouterObject -> VlanNetworkObject
```

è valida.

---

# 15. Ancestry identity-level

La compatibility usa:

```text
object_template_ancestry
```

a livello:

```text
ObjectTemplate identity / lineage
```

Non usa:

```text
ObjectTemplateVersion
parent_version
```

La Relationship eligibility è indipendente dalla concrete structural version dell'Object.

---

# 16. Query shape candidata

Una possibile shape è una singola query che legge:

```text
definition
source Object
target Object
source ancestry predicate
target ancestry predicate
```

nello stesso statement.

Forma concettuale:

```sql
SELECT ...
FROM relationship_definitions d
JOIN objects s
  ON s.id = :source_object_id
JOIN objects t
  ON t.id = :target_object_id
JOIN object_template_ancestry sa
  ON sa.template_id = s.template_id
 AND sa.ancestor_template_id = d.source_template_id
JOIN object_template_ancestry ta
  ON ta.template_id = t.template_id
 AND ta.ancestor_template_id = d.target_template_id
WHERE d.id = :relationship_definition_id;
```

Questa shape fornisce:

```text
one MVCC statement snapshot
```

ma non è richiesta come concurrency mechanism.

---

# 17. Separate reads sono concurrency-safe

È ammesso anche un protocollo con più read:

```text
read definition
read source Object
read target Object
verify source ancestry
verify target ancestry
insert Relationship
```

sotto:

```text
READ COMMITTED
```

perché:

```text
definition endpoint templates cannot change
Object.template_id cannot change
template lineage cannot change for the same identity
```

L'unica invalidazione possibile è la delete di una referenced identity, che viene intercettata dalle FK.

---

# 18. Error semantics

L'application può distinguere:

```text
RelationshipDefinitionNotFound
SourceObjectNotFound
TargetObjectNotFound
SourceTemplateIncompatible
TargetTemplateIncompatible
SelfRelationship
```

La query shape concreta può essere scelta per preservare error reporting preciso.

Questo non modifica il concurrency contract.

---

# 19. PK authority

La:

```text
PRIMARY KEY(relationships.id)
```

è final authority sull'identity.

Se due create tentano lo stesso:

```text
relationship_id
```

una può riuscire e l'altra fallisce per PK violation.

Nessun lock preventivo è richiesto.

---

# 20. FK authority sulla RelationshipDefinition

La FK:

```text
relationships.relationship_definition_id
    -> relationship_definitions.id
    ON DELETE RESTRICT
```

è final authority per l'esistenza della definition al momento dell'INSERT.

Un eventuale pre-check:

```text
definition exists
```

non sostituisce la FK.

---

# 21. FK authority sugli Object endpoint

Le FK:

```text
relationships.source_object_id
    -> objects.id
    ON DELETE RESTRICT

relationships.target_object_id
    -> objects.id
    ON DELETE RESTRICT
```

sono final authority per l'esistenza degli endpoint al momento dell'INSERT.

---

# 22. CREATE Relationship vs RelationshipDefinition.RENAME

`RelationshipDefinition.RENAME` modifica soltanto:

```text
forward_name
reverse_name
```

La create usa per compatibility:

```text
source_template_id
target_template_id
```

che sono immutabili.

Quindi:

```text
Relationship.CREATE
RelationshipDefinition.RENAME
```

possono procedere concorrentemente.

Non serve serializzarle.

---

# 23. Effetto di Definition.RENAME su Relationship create

Una Relationship creata mentre la definition viene rinominata mantiene:

```text
relationship_definition_id = D
```

Dopo il commit della rename, le VIEW/query vedranno la Relationship con:

```text
new forward_name
new reverse_name
```

Non esiste alcuna migration runtime.

---

# 24. CREATE Relationship vs RelationshipDefinition.DELETE

Race fondamentale.

## Relationship CREATE vince

Se l'INSERT Relationship stabilisce prima:

```text
relationship_definition_id = D
```

la successiva:

```text
DELETE RelationshipDefinition D
```

deve fallire per:

```text
FK RESTRICT
```

## Definition DELETE vince

Se:

```text
DELETE D
COMMIT
```

avviene prima dell'INSERT Relationship, l'INSERT fallisce perché la FK target non esiste più.

---

# 25. Nessun explicit lock sulla definition

Non serve acquisire:

```text
FOR KEY SHARE
FOR SHARE
FOR NO KEY UPDATE
FOR UPDATE
```

sulla RelationshipDefinition.

La compatibility structural state è immutabile e la FK dell'INSERT gestisce la race con delete.

---

# 26. CREATE Relationship vs Object.RENAME

`Object.RENAME` modifica:

```text
canonical_name
```

La Relationship compatibility non dipende dal nome.

Quindi le action sono indipendenti e possono procedere concorrentemente.

---

# 27. CREATE Relationship vs Object.DATA_CHANGE

`Object.DATA_CHANGE` modifica:

```text
properties_json
```

La Relationship compatibility non dipende dalle properties.

Quindi le action sono indipendenti.

---

# 28. CREATE Relationship vs Object.SCHEMA_CHANGE

Nel modello ratificato:

```text
Object.template_id
    immutable

Object.SCHEMA_CHANGE modifies:
    template_version
    properties_json
```

Quindi uno schema change non può modificare Relationship eligibility.

`Relationship.CREATE` e `Object.SCHEMA_CHANGE` possono procedere concorrentemente.

---

# 29. Nessun explicit lock sugli Object endpoint

Non serve acquisire:

```text
source Object FOR KEY SHARE
target Object FOR KEY SHARE
```

o altri explicit row lock.

La Relationship compatibility dipende da:

```text
Object.template_id
```

che è immutabile.

La FK dell'INSERT gestisce la race con Object delete.

---

# 30. CREATE Relationship vs Object.DELETE — source

Scenario:

```text
CREATE R:
S -> T
```

con concurrent:

```text
DELETE S
```

Due ordini seriali sono validi.

## Relationship INSERT vince

L'INSERT stabilisce:

```text
relationships.source_object_id = S
```

La successiva Object delete deve fallire per:

```text
FK RESTRICT
```

## Object DELETE vince

S scompare prima dell'INSERT.

L'INSERT Relationship fallisce perché:

```text
source_object_id = S
```

non soddisfa più la FK.

---

# 31. CREATE Relationship vs Object.DELETE — target

La stessa semantica vale simmetricamente per:

```text
target_object_id = T
```

Se la Relationship stabilisce prima il riferimento:

```text
DELETE T
    -> FAIL
```

Se T viene eliminato prima:

```text
Relationship INSERT
    -> FAIL FK
```

---

# 32. Implicazione per Object subtree DELETE

Se un subtree contiene un Object che partecipa a una Relationship:

```text
Object subtree DELETE
    -> MUST FAIL
```

La Relationship non appartiene alla ownership lifecycle.

Una concurrent Relationship create può quindi influenzare l'esito della subtree delete secondo un ordine seriale valido.

---

# 33. Concurrent Relationship CREATE verso subtree Object

Scenario:

```text
subtree:
A
└── B
```

concurrent:

```text
CREATE Relationship
X -> B
```

## Relationship wins first

Il riferimento verso B viene stabilito.

La subtree delete incontra la FK `RESTRICT` e deve fallire atomicamente.

## Subtree delete wins first

B scompare.

La Relationship create fallisce FK.

Non serve un reciprocal explicit Object lock.

---

# 34. Atomicità della Object subtree delete

Se una Relationship reference impedisce la delete di uno qualunque degli Object del subtree:

```text
whole subtree delete transaction
    -> ROLLBACK
```

Non deve rimanere un subtree parzialmente eliminato.

Questa atomicità appartiene al contratto Object DELETE.

---

# 35. Nessun duplicate check

Poiché duplicati runtime sono ammessi, non deve essere eseguito:

```text
check if D/S/T already exists
```

prima dell'INSERT.

Questo elimina:

```text
duplicate predicate race
pair-level locking
uniqueness coordination
```

---

# 36. Concurrent Relationship.CREATE con stessi endpoint

Esempio:

```text
T1:
R1 / D / S -> T

T2:
R2 / D / S -> T
```

con:

```text
R1 != R2
```

Entrambe devono poter riuscire.

Non esiste business contention sulla endpoint tuple.

---

# 37. Nessuna maximum cardinality race

La cardinalità è:

```text
0..N
```

su entrambi i lati.

Non esiste un invariant:

```text
at most one
```

da proteggere.

Non servono:

```text
COUNT
slot lock
endpoint cardinality lock
SERIALIZABLE
```

---

# 38. Nessun graph invariant

Relationship non è ownership.

Non esistono invarianti:

```text
acyclicity
single parent
forest
```

Sono ammesse, se type-compatible, configurazioni:

```text
A -> B
B -> A
```

e cicli più lunghi.

L'unica prohibition locale è:

```text
A -> A
```

nella stessa Relationship runtime.

---

# 39. Nessun SERIALIZABLE

Non esiste un recursive/multi-row graph predicate da proteggere.

Quindi non serve:

```text
SERIALIZABLE
```

né whole-action retry su:

```text
SQLSTATE 40001
```

---

# 40. Isolation level

È sufficiente:

```text
READ COMMITTED
```

La action combina:

```text
validation of immutable structural facts
+
single INSERT
+
PK/FK/CHECK final authorities
```

---

# 41. Explicit lock picture

Baseline ratificata:

```text
RelationshipDefinition:
    no explicit row lock

Source Object:
    no explicit row lock

Target Object:
    no explicit row lock
```

Non viene ratificato:

```text
FOR KEY SHARE
FOR SHARE
FOR NO KEY UPDATE
FOR UPDATE
```

come parte del protocollo minimo.

---

# 42. Perché non usare `FOR KEY SHARE`

Una strategia più conservativa potrebbe lockare:

```text
definition
source Object
target Object
```

per impedire delete durante la validation.

Non viene ratificata perché:

```text
structural compatibility facts are immutable

and

FK + RESTRICT already establish correct delete/create ordering
```

Aggiungere lock anticipati allargherebbe la contention window senza proteggere un mutable business fact.

---

# 43. Nessun lock ordering contract

Poiché non esistono explicit application row lock:

```text
no canonical lock ordering
```

è richiesto.

Non serve ordinare:

```text
S
T
D
```

per il protocollo minimo.

---

# 44. Nessuna specialized Unit of Work

Una normale transaction è sufficiente:

```text
BEGIN
READ COMMITTED

validate Relationship
INSERT relationships

COMMIT
```

Non esiste requisito di:

```text
special isolation
serialization retry
custom lock ordering
graph coordination
```

---

# 45. Audit

Non è stato ratificato un audit model specifico per:

```text
Relationship
RelationshipDefinition
```

Quindi:

```text
Relationship.CREATE
    -> no audit side effect
```

Non deve essere usato:

```text
object_changes
```

per rappresentare la Relationship create.

---

# 46. Protocollo transazionale candidato

```text
BEGIN
READ COMMITTED

1. validate input:
       source_object_id != target_object_id

2. read RelationshipDefinition D:
       source_template_id
       target_template_id

   if missing:
       FAIL RelationshipDefinitionNotFound

3. read source Object S:
       template_id

   if missing:
       FAIL SourceObjectNotFound

4. read target Object T:
       template_id

   if missing:
       FAIL TargetObjectNotFound

5. verify source compatibility:

       compatible(
           S.template_id,
           D.source_template_id
       )

   using object_template_ancestry

   if false:
       FAIL SourceTemplateIncompatible

6. verify target compatibility:

       compatible(
           T.template_id,
           D.target_template_id
       )

   using object_template_ancestry

   if false:
       FAIL TargetTemplateIncompatible

7. INSERT relationships:
       id
       relationship_definition_id
       source_object_id
       target_object_id

8. DB final authorities:
       PK(id)
       FK(definition)
       FK(source Object)
       FK(target Object)
       CHECK(source != target)

9. COMMIT
```

---

# 47. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
source != target semantic validation

definition/source/target lookup semantics

polymorphic compatibility

precise incompatible-endpoint errors

no duplicate rejection

no cardinality restriction
```

## PostgreSQL / relational model

Garantisce:

```text
Relationship identity
    -> PRIMARY KEY

definition existence
    -> FK

source Object existence
    -> FK

target Object existence
    -> FK

Object/Definition delete protection
    -> ON DELETE RESTRICT

self-instance prohibition
    -> CHECK(source_object_id <> target_object_id)
```

## Concurrency protocol

Garantisce intenzionalmente:

```text
validation of immutable structural facts
+
constraint-driven final admission
```

senza explicit row lock.

---

# 48. Reciprocal contracts completati

## With RelationshipDefinition.RENAME

```text
may proceed concurrently
```

perché rename modifica soltanto i nomi.

## With RelationshipDefinition.DELETE

```text
FK establishes winner
```

- Relationship reference first -> definition delete fails
- definition delete first -> Relationship create fails

## With Object.RENAME / DATA_CHANGE / SCHEMA_CHANGE

```text
may proceed concurrently
```

perché non modificano `Object.template_id`.

## With Object.DELETE

```text
FK establishes winner
```

- Relationship reference first -> Object delete fails
- Object delete first -> Relationship create fails

---

# 49. Verdetto DRAFT

> **`Relationship.CREATE` crea una singola runtime Relationship fra due Object distinti usando una RelationshipDefinition esistente.**
>
> La compatibility è polimorfica su entrambi i lati e dipende esclusivamente da `Object.template_id`, dagli endpoint immutabili della definition e dalla lineage ancestry identity-level.
>
> Questi structural facts sono immutabili durante la vita delle rispettive identities; pertanto la validation non richiede explicit row locks.
>
> Concurrent `Object.RENAME`, `Object.DATA_CHANGE` e `Object.SCHEMA_CHANGE` non influenzano Relationship eligibility.
>
> `RelationshipDefinition.RENAME` può procedere concorrentemente perché modifica soltanto i nomi.
>
> Le race con `RelationshipDefinition.DELETE` e `Object.DELETE` sono risolte dalle FK: se la Relationship stabilisce prima il riferimento, la delete viene impedita da `RESTRICT`; se la referenced identity viene eliminata prima, l'INSERT Relationship fallisce FK.
>
> Le Relationship duplicate sono ammesse e quindi non viene eseguito alcun duplicate check né acquisito un endpoint-pair lock.
>
> Non esistono graph acyclicity o maximum-cardinality predicates.
>
> `READ COMMITTED` è sufficiente; nessun `SERIALIZABLE`, nessun explicit row lock, nessun lock ordering e nessuna specialized Unit of Work sono necessari.
>
> PK/FK/CHECK rimangono le authority finali sull'INSERT.
>
> Nessun audit side effect viene prodotto finché non viene ratificato un audit model specifico per Relationship/RelationshipDefinition.
