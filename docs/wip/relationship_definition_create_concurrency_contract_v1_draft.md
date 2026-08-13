# RelationshipDefinition CREATE — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `RelationshipDefinition.CREATE`.**

Questo documento descrive:

```text
- semantica Domain/Application della create
- righe lette e scritte
- invarianti relazionali
- race concorrenti
- interaction con ObjectTemplate lifecycle
- lock richiesti / non richiesti
- isolation level
- Unit of Work
- audit scope
```

Baseline di riferimento:

```text
Relationship — Modello Relazionale + Domain/Business Model RATIFICATO v1
ObjectTemplate — Modello Relazionale ratificato
ObjectTemplate DELETE — Concurrency Contract ratificato
```

---

# 2. Obiettivo dell'action

`RelationshipDefinition.CREATE` crea una singola:

```text
relationship_definitions
```

row.

Shape logica:

```text
id
source_template_id
target_template_id
forward_name
reverse_name
```

Non crea:

```text
Relationship runtime
Object
ObjectTemplate
ObjectTemplateVersion
audit row
```

---

# 3. Stato autorevole creato

La sola mutation persistente è:

```sql
INSERT INTO relationship_definitions (
    id,
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
VALUES (...);
```

Non vengono scritte altre tabelle.

---

# 4. Source e target sono ObjectTemplate identity-level

Gli endpoint dichiarati dalla definition sono:

```text
source_template_id
target_template_id
```

con FK verso:

```text
object_templates.id
```

La definition è quindi definita a livello di:

```text
ObjectTemplate identity / lineage type
```

e non a livello di:

```text
ObjectTemplateVersion
```

---

# 5. Abstract ObjectTemplate ammessi

È esplicitamente ammesso usare come endpoint dichiarato un ObjectTemplate:

```text
abstract = TRUE
```

Esempio:

```text
Device (abstract)
    ^
    |
Router
```

Definition valida:

```text
Device
    -- connected_to -->
Network
```

La definition dichiara un accepted type e non richiede che il tipo dichiarato sia direttamente istanziabile.

Non deve essere introdotto alcun vincolo:

```text
source abstract == FALSE
target abstract == FALSE
```

---

# 6. Nessun lifecycle gate su ObjectTemplateVersion

La create richiede soltanto che esistano:

```text
source ObjectTemplate identity
target ObjectTemplate identity
```

Non richiede:

```text
at least one PUBLISHED OTV
latest OTV PUBLISHED
specific OTV PUBLISHED
specific OTV lifecycle state
```

La definition non referenzia alcuna:

```text
ObjectTemplateVersion
```

e non deve essere artificialmente legata al lifecycle di una versione.

---

# 7. Template con sole versioni DRAFT

È ammesso creare una RelationshipDefinition anche se uno o entrambi gli ObjectTemplate endpoint hanno, in quel momento:

```text
only DRAFT versions
```

La definition rimane identity-level.

La concreta utilizzabilità runtime emergerà quando esisteranno Object compatibili.

---

# 8. Exact rows read

Il protocollo minimo non richiede decision-read applicative autorevoli.

Non è necessario leggere:

```text
ObjectTemplateVersion
Object
Relationship
object_template_ancestry
relationship_definition_endpoints
```

prima dell'INSERT.

Un eventuale lookup applicativo di:

```text
source ObjectTemplate
target ObjectTemplate
```

può essere usato per error mapping o UX, ma non è concurrency authority.

---

# 9. Exact rows written

Una sola row:

```text
relationship_definitions(id)
```

Nessun'altra mutation persistente è richiesta.

---

# 10. Invarianti dell'INSERT

La row deve soddisfare:

```text
id unique

source_template_id exists
target_template_id exists

forward_name <> ''
reverse_name <> ''

(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
unique
```

Sono invece esplicitamente validi:

```text
source_template_id == target_template_id
```

e:

```text
forward_name == reverse_name
```

---

# 11. PK authority

L'identity della definition è:

```text
relationship_definitions.id
```

La:

```text
PRIMARY KEY(id)
```

è final authority contro collisioni concorrenti o accidentali.

Nessun explicit lock è richiesto per prevenire PK collision.

---

# 12. FK authority sugli endpoint template

Le FK:

```text
source_template_id
    -> object_templates.id
    ON DELETE RESTRICT

target_template_id
    -> object_templates.id
    ON DELETE RESTRICT
```

sono final authority per l'esistenza degli endpoint dichiarati.

Un eventuale pre-check applicativo non sostituisce la FK.

---

# 13. CHECK authority sui nomi

I nomi devono essere:

```text
NOT NULL
non-empty
```

con:

```text
CHECK(forward_name <> '')
CHECK(reverse_name <> '')
```

Non viene introdotta alcuna ulteriore semantica implicita di:

```text
TRIM
case-folding
Unicode normalization
case-insensitive comparison
```

---

# 14. UNIQUE authority sulla definition tuple

La tuple business-unique è:

```text
(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

La:

```text
UNIQUE(...)
```

è final authority.

Non deve essere usato un protocollo:

```text
SELECT if not exists
then INSERT
```

come meccanismo di concorrenza.

---

# 15. Concurrent create della stessa definition

Scenario:

```text
T1:
CREATE
A -> B
forward = connected_to
reverse = connected_from

T2:
CREATE
A -> B
forward = connected_to
reverse = connected_from
```

Entrambe tentano di creare la stessa business tuple.

Semantica:

```text
one INSERT succeeds
one INSERT fails on UNIQUE
```

Non servono:

```text
explicit row locks
application mutex
SERIALIZABLE
```

---

# 16. Concurrent create di definitions diverse

Scenario:

```text
T1:
A -> B
connected_to / connected_from

T2:
A -> B
depends_on / dependency_of
```

Le tuple sono diverse.

Entrambe devono poter procedere concorrentemente.

Non esiste un coordination gate comune per:

```text
same source template
same target template
```

se la business tuple completa è diversa.

---

# 17. Nessuna ancestry validation

`RelationshipDefinition.CREATE` non deve verificare inheritance compatibility.

La definition stessa dichiara:

```text
source accepted base type
target accepted base type
```

Quindi non deve interrogare:

```text
object_template_ancestry
```

per decidere se source e target siano correlati fra loro.

Non esiste alcun requisito di inheritance relationship fra:

```text
source_template_id
target_template_id
```

---

# 18. Polymorphism entra in gioco solo a runtime

La ancestry viene usata successivamente quando una candidate:

```text
Relationship
```

deve verificare:

```text
source Object.template_id
    compatible with definition.source_template_id

target Object.template_id
    compatible with definition.target_template_id
```

Non è parte della create della definition.

---

# 19. CREATE Definition vs DELETE ObjectTemplate

Race principale:

```text
T1:
CREATE RelationshipDefinition referencing ObjectTemplate A

T2:
DELETE ObjectTemplate A
```

Sono validi due ordini seriali.

## Definition vince

```text
definition INSERT establishes FK reference
ObjectTemplate DELETE
    -> FAIL because RESTRICT
```

## ObjectTemplate delete vince

```text
ObjectTemplate disappears
definition INSERT
    -> FAIL because FK target missing
```

Non serve introdurre un explicit:

```text
ObjectTemplate FOR SHARE
```

nel service.

La FK realizza il reciprocal consistency contract necessario.

---

# 20. Reciprocal dependency di ObjectTemplate DELETE

La baseline ObjectTemplate DELETE deve includere esplicitamente come dependency:

```text
relationship_definitions.source_template_id
relationship_definitions.target_template_id
```

Un ObjectTemplate referenziato da almeno una RelationshipDefinition non può essere cancellato.

La FK `RESTRICT` è final authority.

---

# 21. Nessun explicit row lock

L'action non richiede:

```text
FOR KEY SHARE
FOR SHARE
FOR NO KEY UPDATE
FOR UPDATE
```

Non esiste una decisione read-then-write non coperta da constraint che debba essere stabilizzata.

Il protocollo è:

```text
INSERT
subject to PK/FK/CHECK/UNIQUE
```

---

# 22. Nessun lock ordering contract

Poiché non vengono acquisiti explicit row locks:

```text
no canonical lock ordering required
```

Non esiste una sequenza di endpoint lock da coordinare.

---

# 23. Isolation level

È sufficiente:

```text
READ COMMITTED
```

Non servono:

```text
REPEATABLE READ
SERIALIZABLE
```

L'action non contiene:

```text
MAX + 1 allocation
recursive predicate
multi-row decision predicate
check-then-act not protected by a DB constraint
```

---

# 24. Nessuna specialized Unit of Work

Non serve una UoW specializzata.

Una normale transaction è sufficiente:

```text
BEGIN
INSERT relationship_definitions
COMMIT
```

Non esiste un requisito specifico di:

```text
special isolation
retry on 40001
custom lock protocol
```

---

# 25. Error semantics

L'application può distinguere concettualmente:

```text
source template missing
target template missing
empty forward_name
empty reverse_name
duplicate definition tuple
id collision
```

Eventuali pre-check possono servire per produrre errori applicativi più leggibili.

Non devono però essere trattati come final consistency authority.

---

# 26. Pre-check non autorevoli

Esempio:

```text
SELECT ObjectTemplate A
-> exists
```

non garantisce che A esista ancora quando viene eseguito l'INSERT.

Una concurrent ObjectTemplate delete può intervenire.

Quindi:

```text
FOREIGN KEY
```

rimane sempre final authority.

Lo stesso principio vale per la duplicate tuple:

```text
SELECT no duplicate
```

non sostituisce:

```text
UNIQUE
```

---

# 27. Audit

Non è stato ratificato alcun audit model specifico per:

```text
RelationshipDefinition
Relationship
```

Quindi:

```text
RelationshipDefinition.CREATE
    -> no audit side effect
```

Non deve essere riutilizzato:

```text
object_changes
```

perché appartiene alla history del live Object state.

Un eventuale metadata audit richiede un modello separato e una ratifica esplicita.

---

# 28. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
request semantics

source/target template identifiers

forward/reverse names

abstract templates allowed

no OTV lifecycle requirement

no ancestry validation
```

## PostgreSQL / relational model

Garantisce:

```text
definition identity
    -> PRIMARY KEY

endpoint existence
    -> FOREIGN KEY

template delete protection
    -> ON DELETE RESTRICT

non-empty names
    -> CHECK

business tuple uniqueness
    -> UNIQUE
```

## Concurrency protocol

Garantisce intenzionalmente soltanto:

```text
normal INSERT transaction
constraint-driven conflict resolution
```

senza explicit locking.

---

# 29. Lock picture

```text
explicit application row locks:
    NONE
```

```text
isolation:
    READ COMMITTED
```

```text
retry contract:
    NONE beyond normal transaction/error handling
```

```text
specialized UoW:
    NONE
```

---

# 30. Verdetto DRAFT

> **`RelationshipDefinition.CREATE` crea una singola definition identity-level attraverso un normale INSERT.**
>
> Source e target devono essere ObjectTemplate identity esistenti; non viene richiesto alcun particolare stato di una ObjectTemplateVersion.
>
> Gli abstract ObjectTemplate sono ammessi come endpoint dichiarati.
>
> Non viene effettuata ancestry validation: source e target rappresentano i tipi base dichiarati; inheritance e polymorphism vengono applicati quando si crea una Relationship runtime.
>
> PK, FK, CHECK e UNIQUE sono le authority finali per identity, esistenza template, non-empty names e duplicate definition.
>
> `source_template_id == target_template_id` e `forward_name == reverse_name` sono validi.
>
> La race con `ObjectTemplate.DELETE` è risolta dalle FK `RESTRICT`: se la definition viene creata prima, la template delete fallisce; se la template viene cancellata prima, l'INSERT definition fallisce.
>
> Nessun explicit row lock, nessun lock ordering, nessun `SERIALIZABLE` e nessuna specialized UoW sono necessari.
>
> Nessun audit side effect viene introdotto finché non viene ratificato un audit model specifico per Relationship/RelationshipDefinition.
