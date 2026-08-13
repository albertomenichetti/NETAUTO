# Relationship — Modello Relazionale + Domain/Business Model RATIFICATO v1

## 1. Stato del documento

**RATIFICATO come baseline corrente del modello `Relationship`.**

Questo documento consolida le decisioni concordate per:

```text
- RelationshipDefinition
- Relationship runtime
- directional semantics source/target
- cardinalità
- duplicati
- self-relationship
- inheritance e polymorphism
- lifecycle di RelationshipDefinition
- interaction con Object lifecycle
- VIEW PostgreSQL orientate per endpoint
- indici necessari per le query bidirezionali
```

Il documento definisce il modello relazionale e le regole Domain/Business.

**Non definisce ancora i concurrency contract delle singole action Relationship.**

Saranno analizzate separatamente le action, a partire da questa baseline.

---

# 2. Concetti fondamentali

Il dominio distingue due entità:

```text
RelationshipDefinition
Relationship
```

`RelationshipDefinition` definisce:

```text
- quali ObjectTemplate possono partecipare dal lato SOURCE
- quali ObjectTemplate possono partecipare dal lato TARGET
- il nome leggibile dal SOURCE verso il TARGET
- il nome leggibile dal TARGET verso il SOURCE
```

`Relationship` rappresenta invece una singola istanza runtime fra due Object.

La Relationship è:

```text
- binaria
- direzionale
- non-owning
- many-to-many
- identificata da una propria identity
```

`source` e `target` non sono colonne intercambiabili prive di semantica.

Sono due ruoli distinti del dominio.

---

# 3. RelationshipDefinition — modello relazionale autorevole

Schema logico ratificato:

```text
relationship_definitions
------------------------
id                  PK
source_template_id  NOT NULL
target_template_id  NOT NULL
forward_name        NOT NULL
reverse_name        NOT NULL
```

Vincoli:

```text
PK(id)

FK(source_template_id)
    -> object_templates.id
    ON DELETE RESTRICT

FK(target_template_id)
    -> object_templates.id
    ON DELETE RESTRICT

CHECK(forward_name <> '')
CHECK(reverse_name <> '')

UNIQUE(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

I concrete SQL data types degli identificativi restano quelli adottati dal modello fisico del progetto.

Questo documento ratifica la struttura logica e i vincoli, non cambia autonomamente il tipo degli ID.

---

# 4. Identity di RelationshipDefinition

La sola identity della definition è:

```text
relationship_definitions.id
```

La tuple:

```text
(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

è business-unique ma non sostituisce l'identity.

Quindi:

```text
id
```

rimane la PK e il riferimento stabile usato da:

```text
relationships.relationship_definition_id
```

---

# 5. Semantica direzionale dei nomi

Per una definition:

```text
source_template = A
target_template = B

forward_name = "contains"
reverse_name = "contained_by"
```

la semantica è:

```text
SOURCE A
    -- contains -->
TARGET B
```

e, osservando la stessa Relationship dal TARGET:

```text
TARGET B
    -- contained_by -->
SOURCE A
```

Quindi:

```text
forward_name
```

è il nome della relazione dal punto di vista SOURCE.

```text
reverse_name
```

è il nome della stessa relazione dal punto di vista TARGET.

---

# 6. `forward_name` e `reverse_name`

Entrambi devono essere:

```text
NOT NULL
non-empty
```

Vincoli minimi ratificati:

```text
CHECK(forward_name <> '')
CHECK(reverse_name <> '')
```

È esplicitamente ammesso:

```text
forward_name == reverse_name
```

Esempio valido:

```text
Device
    connected_to / connected_to
Device
```

Non viene introdotto alcun:

```text
CHECK(forward_name <> reverse_name)
```

---

# 7. Semantica di "non-empty"

La regola ratificata è letteralmente:

```text
value <> ''
```

Non è stata ratificata alcuna ulteriore normalizzazione del tipo:

```text
TRIM
case-folding
Unicode normalization
case-insensitive uniqueness
```

Quindi il modello baseline non deve introdurre implicitamente queste semantiche.

L'eventuale politica di normalizzazione dei nomi richiede una decisione separata.

---

# 8. Unicità della RelationshipDefinition

È business-unique la tuple esatta:

```text
(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

Quindi non possono esistere due definitions identiche sotto tutti e quattro questi campi.

Sono invece distinte, per esempio:

```text
A -> B / forward=x / reverse=y
A -> B / forward=x / reverse=z
```

oppure:

```text
A -> B / forward=x / reverse=y
B -> A / forward=x / reverse=y
```

perché source e target mantengono semantica direzionale.

L'unicità usa la normale equality/collation delle colonne persistite.

Non è stata ratificata una uniqueness case-insensitive.

---

# 9. Self-definition a livello ObjectTemplate

È esplicitamente ammesso:

```text
source_template_id == target_template_id
```

Quindi una definition:

```text
A -> A
```

è valida.

Non deve esistere:

```text
CHECK(source_template_id <> target_template_id)
```

Esempi:

```text
Person
    parent_of / child_of
Person
```

oppure:

```text
Device
    connected_to / connected_to
Device
```

sono entrambi rappresentabili.

---

# 10. Cardinalità di RelationshipDefinition

La cardinalità runtime è sempre:

```text
SOURCE side: 0..N
TARGET side: 0..N
```

Non esistono cardinalità:

```text
0..1
1..1
1..N come minimo obbligatorio
```

nel modello Relationship corrente.

Una definition non impone che un Object abbia almeno una Relationship.

Non impone neppure un massimo di Relationship su uno dei lati.

---

# 11. Nessuna uniqueness di cardinalità

Non devono essere introdotti vincoli come:

```text
UNIQUE(relationship_definition_id, source_object_id)
UNIQUE(relationship_definition_id, target_object_id)
```

perché limiterebbero implicitamente la cardinalità a `0..1`.

La cardinalità ratificata è sempre `0..N`.

---

# 12. Lifecycle di RelationshipDefinition

I campi:

```text
source_template_id
target_template_id
```

sono **immutabili nel dominio** dopo la creazione della definition.

Gli unici campi modificabili sono:

```text
forward_name
reverse_name
```

Quindi una modifica della definition può esclusivamente rinominare uno o entrambi i nomi direzionali.

Il cambio di source/target template non è una rename e non è una mutation ammessa della stessa definition.

---

# 13. Rename di RelationshipDefinition in uso

Una RelationshipDefinition può essere rinominata anche se esistono Relationship runtime che la referenziano.

Le Relationship runtime memorizzano:

```text
relationship_definition_id
```

e non snapshot locali di:

```text
forward_name
reverse_name
```

Di conseguenza, dopo una rename della definition, le Relationship esistenti vengono osservate con i nuovi nomi.

La rename non cambia:

```text
Relationship.id
source_object_id
target_object_id
relationship_definition_id
```

---

# 14. Rename e UNIQUE constraint

Qualunque rename di:

```text
forward_name
reverse_name
```

deve continuare a rispettare:

```text
UNIQUE(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

La UNIQUE del database rimane final authority sotto race concorrenti.

Il concurrency contract specifico della rename sarà analizzato separatamente.

---

# 15. Delete di RelationshipDefinition

Una RelationshipDefinition può essere cancellata **soltanto se non è in uso**.

Il vincolo autorevole è:

```text
relationships.relationship_definition_id
    -> relationship_definitions.id
    ON DELETE RESTRICT
```

Quindi:

```text
definition referenced by >= 1 Relationship
    -> delete definition MUST FAIL
```

La definition deve prima diventare unused tramite esplicita cancellazione delle Relationship che la referenziano.

Non esiste cascade:

```text
delete definition
    -> delete relationships
```

---

# 16. Relationship — modello relazionale autorevole

Schema logico ratificato:

```text
relationships
-------------
id                          PK
relationship_definition_id  NOT NULL
source_object_id             NOT NULL
target_object_id             NOT NULL
```

Vincoli:

```text
PK(id)

FK(relationship_definition_id)
    -> relationship_definitions.id
    ON DELETE RESTRICT

FK(source_object_id)
    -> objects.id
    ON DELETE RESTRICT

FK(target_object_id)
    -> objects.id
    ON DELETE RESTRICT

CHECK(source_object_id <> target_object_id)
```

Non esistono altre UNIQUE business sulle endpoint tuple.

---

# 17. Identity della Relationship runtime

La sola identity della Relationship è:

```text
relationships.id
```

La tuple:

```text
(
    relationship_definition_id,
    source_object_id,
    target_object_id
)
```

**non è identity** e **non è unique**.

Ogni row rappresenta una Relationship distinta anche quando source, target e definition coincidono con una Relationship già esistente.

---

# 18. Duplicate Relationship esplicitamente ammesse

Sono valide contemporaneamente:

```text
R1:
    definition = D
    source = A
    target = B

R2:
    definition = D
    source = A
    target = B
```

purché:

```text
R1.id <> R2.id
```

Queste sono due Relationship diverse.

Non deve esistere:

```text
UNIQUE(
    relationship_definition_id,
    source_object_id,
    target_object_id
)
```

La possibilità di Relationship duplicate è intenzionalmente preservata anche se non esiste oggi un use case forte.

---

# 19. Orientamento inverso non equivale a duplicato

Le rows:

```text
D / A -> B
D / B -> A
```

sono semanticamente differenti.

La seconda è valida soltanto se:

```text
B.template_id
    è compatible con D.source_template_id

AND

A.template_id
    è compatible con D.target_template_id
```

Source e target non vengono automaticamente normalizzati o ordinati.

---

# 20. Self-relationship a livello Object runtime

È **vietato**:

```text
source_object_id == target_object_id
```

Il vincolo deve essere fisico:

```text
CHECK(source_object_id <> target_object_id)
```

Quindi è possibile definire:

```text
ObjectTemplate A -> ObjectTemplate A
```

ma una singola Relationship runtime deve comunque collegare **due Object distinti**.

Esempio:

```text
A1 -> A2
```

è valido.

```text
A1 -> A1
```

non è valido.

---

# 21. Distinzione fondamentale: self-definition vs self-instance

Sono due concetti diversi:

```text
RelationshipDefinition:
    A -> A
    ALLOWED

Relationship:
    Object X -> Object X
    FORBIDDEN
```

Il modello non deve confondere queste due regole.

---

# 22. Relationship non è ownership

`Relationship` è una associazione fra Object autonomi.

Non rappresenta:

```text
composition
ownership
lifecycle containment
```

Queste semantiche appartengono a:

```text
object_components
```

La distinzione è strutturale e comportamentale.

---

# 23. Ownership vs Relationship

`object_components` significa:

```text
parent owns child
```

e partecipa alla subtree lifecycle.

`relationships` significa:

```text
Object A is related to Object B
```

senza ownership.

Conseguenza:

```text
Object subtree delete
```

può rimuovere ownership edges come parte della workflow,

ma **non può rimuovere automaticamente Relationship**.

---

# 24. Object delete bloccata da Relationship incidenti

Se un Object che deve essere eliminato compare come:

```text
relationships.source_object_id
```

oppure:

```text
relationships.target_object_id
```

la Object delete deve fallire.

Per una subtree delete, questa regola vale per **ogni Object del subtree**.

Quindi:

```text
if any subtree Object participates in any Relationship
    -> whole Object subtree delete MUST FAIL
```

---

# 25. Anche Relationship interne al subtree bloccano la delete

La regola precedente vale anche quando entrambi gli endpoint appartengono allo stesso subtree.

Esempio:

```text
subtree:
    A
    └── B

Relationship:
    A -> B
```

`delete A` non deve interpretare quella Relationship come parte dell'ownership lifecycle.

La Relationship deve essere esplicitamente eliminata prima.

Finché esiste:

```text
delete subtree A
    -> FAIL
```

---

# 26. FK RESTRICT come final authority per Object delete

Le FK:

```text
relationships.source_object_id
    -> objects.id
    ON DELETE RESTRICT

relationships.target_object_id
    -> objects.id
    ON DELETE RESTRICT
```

sono la final consistency authority sotto race.

Il contratto `Object DELETE` deve quindi essere interpretato esplicitamente come:

```text
ownership edges
    -> removable as part of subtree delete

Relationship edges
    -> external RESTRICT dependency
    -> block subtree delete
```

Il reciprocal concurrency protocol con `CREATE Relationship` sarà ratificato nell'analisi delle action.

---

# 27. ObjectTemplate delete bloccata da RelationshipDefinition

Le FK:

```text
relationship_definitions.source_template_id
    -> object_templates.id
    ON DELETE RESTRICT

relationship_definitions.target_template_id
    -> object_templates.id
    ON DELETE RESTRICT
```

implicano:

```text
ObjectTemplate referenced by any RelationshipDefinition
    -> ObjectTemplate delete MUST FAIL
```

Una definition deve essere rimossa esplicitamente prima di poter eliminare il template che referenzia.

---

# 28. Object binding e Relationship compatibility

Nel modello Object ratificato:

```text
Object.template_id
```

è stabile per l'intera vita dell'Object.

`SCHEMA_CHANGE` può cambiare:

```text
template_version
properties_json
```

ma non può spostare l'Object verso un diverso:

```text
template_id
```

Questa proprietà è fondamentale per Relationship.

---

# 29. Conseguenza: SCHEMA_CHANGE non invalida Relationship

La compatibility di Relationship è definita rispetto a:

```text
Object.template_id
```

e alla ancestry della template lineage.

Non dipende da:

```text
Object.template_version
```

Quindi:

```text
Router v1 -> Router v2
```

non modifica il tipo `Router` dell'Object.

Una Relationship compatibile prima dello schema change rimane compatibile dopo.

Pertanto:

```text
Object SCHEMA_CHANGE
```

non deve stabilizzare o rivalidare le Relationship incidenti soltanto per il cambio di template version.

---

# 30. Correzione della semantica Object SCHEMA_CHANGE

La baseline Relationship assume esplicitamente:

```text
Object.template_id
    immutable

Object.template_version
    mutable via SCHEMA_CHANGE
```

Quindi ogni precedente descrizione di `SCHEMA_CHANGE` che trattasse:

```text
template_id
```

come modificabile deve essere corretta nella review Object.

`SCHEMA_CHANGE` modifica:

```text
template_version
properties_json
```

e non cambia la ObjectTemplate identity.

---

# 31. Inheritance e polymorphism

RelationshipDefinition usa semantica polimorfica.

Una endpoint declaration:

```text
source_template_id = T
```

accetta come source Object:

```text
Object.template_id == T
```

oppure:

```text
Object.template_id
    derives transitively from T
```

La stessa regola vale simmetricamente sul target.

---

# 32. Compatibility predicate ratificato

Per una definition `D` e una candidate Relationship:

```text
source Object = S
target Object = T
```

la Relationship è type-compatible se e solo se:

```text
compatible(
    S.template_id,
    D.source_template_id
)

AND

compatible(
    T.template_id,
    D.target_template_id
)
```

dove:

```text
compatible(actual_template, declared_template)
```

significa:

```text
actual_template == declared_template
OR
actual_template transitively derives from declared_template
```

---

# 33. Polymorphism è direzionale

La compatibility:

```text
Router compatible with Device
```

non implica:

```text
Device compatible with Router
```

se:

```text
Router derives from Device
```

La regola segue il normale subtype admission:

```text
declared base type
    accepts concrete subtype
```

non il contrario.

---

# 34. Polymorphism vale su entrambi i lati

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
Device
    -- connected_to -->
Network
```

è compatibile con:

```text
Router
    -- connected_to -->
VlanNetwork
```

perché:

```text
Router derives from Device

AND

VlanNetwork derives from Network
```

---

# 35. Parent lineage usata per la compatibility

Il modello ObjectTemplate ratificato stabilisce:

```text
parent_template_id
```

come lineage-stable.

`parent_version` può evolvere fra versioni DRAFT/PUBLISHED ma non cambia la parent template identity della lineage.

Per la Relationship compatibility conta:

```text
template identity ancestry
```

non:

```text
specific ObjectTemplateVersion parent pin
```

---

# 36. `parent_version` non partecipa alla Relationship compatibility

RelationshipDefinition referenzia:

```text
object_templates.id
```

e non:

```text
object_template_versions(template_id, version)
```

Quindi:

```text
parent_version
```

non deve essere usato per decidere se un Object è compatible con una definition.

La compatibility è type-level e lineage-level.

---

# 37. Single inheritance baseline

Il modello ObjectTemplate corrente ha:

```text
one parent_template_id per template lineage
```

e quindi rappresenta una forest di inheritance a livello template identity.

Le VIEW descritte in questo documento assumono questa baseline.

Un eventuale futuro multiple inheritance richiederebbe una nuova ratifica del modello.

---

# 38. Projection relazionale della ancestry

Per evitare che l'application debba implementare ripetutamente:

```text
exact template
OR descendant of template
```

viene ratificata una projection relazionale della ancestry.

Forma concettuale:

```text
object_template_ancestry
------------------------
template_id
ancestor_template_id
depth
```

Semantica:

```text
template_id
    = actual/subtype template

ancestor_template_id
    = compatible declared/base template

depth
    = inheritance distance
```

---

# 39. Reflexive ancestry

La ancestry deve essere reflexive.

Per ogni template:

```text
T
```

deve esistere:

```text
T -> T
depth = 0
```

Esempio:

```text
Router -> Router
depth 0
```

Questo permette di usare un unico predicate relazionale per:

```text
exact match
+
inherited match
```

---

# 40. Transitive ancestry

Esempio:

```text
ManagedObject
     ^
     |
NetworkDevice
     ^
     |
Router
```

la closure deve contenere:

```text
Router        -> Router          depth 0
Router        -> NetworkDevice   depth 1
Router        -> ManagedObject   depth 2

NetworkDevice -> NetworkDevice   depth 0
NetworkDevice -> ManagedObject   depth 1

ManagedObject -> ManagedObject   depth 0
```

---

# 41. Derivazione della lineage edge

Poiché `parent_template_id` è persistito sulle:

```text
object_template_versions
```

ma è lineage-stable, la relazione identity-level può essere derivata concettualmente come:

```text
object_template_lineage_edges
-----------------------------
template_id
parent_template_id
```

con una sola edge logica per template lineage non-root.

Una possibile projection è:

```text
SELECT DISTINCT
    template_id,
    parent_template_id
FROM object_template_versions
WHERE parent_template_id IS NOT NULL
```

La validità di questa projection dipende dall'invariante già ratificato:

```text
parent_template_id immutable and lineage-stable
```

---

# 42. VIEW `object_template_ancestry`

`object_template_ancestry` può essere implementata come recursive PostgreSQL VIEW/CTE derivata da:

```text
object_templates
object_template_lineage_edges
```

Non è una nuova source of truth.

La source of truth rimane il modello ObjectTemplate.

La closure è una projection derivata.

---

# 43. Perché VIEW e non duplicazione fisica della ancestry

Baseline ratificata:

```text
derive ancestry relationally
```

e non:

```text
persist duplicate closure rows as authoritative state
```

Non viene introdotta oggi una closure table materializzata autorevole.

Se in futuro profiling reale dimostrasse un hotspot, una materialized/closure optimization potrà essere valutata separatamente.

---

# 44. VIEW orientata per RelationshipDefinition endpoint

Per rendere semplice la domanda:

> quali RelationshipDefinition supporta questo ObjectTemplate e da quale lato?

viene ratificata una projection:

```text
relationship_definition_endpoints
```

La VIEW è polimorfica.

Non rappresenta soltanto exact source/target equality.

---

# 45. Shape logica di `relationship_definition_endpoints`

Colonne concettuali:

```text
relationship_definition_id

supported_template_id
role

declared_template_id
related_declared_template_id

relationship_name

inheritance_depth
```

dove:

```text
supported_template_id
```

è una template identity che può occupare quel ruolo grazie a exact match o inheritance.

---

# 46. SOURCE branch della definition endpoint VIEW

Per il lato SOURCE:

```text
role
    = SOURCE

declared_template_id
    = relationship_definitions.source_template_id

related_declared_template_id
    = relationship_definitions.target_template_id

relationship_name
    = relationship_definitions.forward_name
```

`supported_template_id` include ogni template `X` tale che:

```text
X == source_template_id
OR
X derives from source_template_id
```

`inheritance_depth` deriva dalla ancestry:

```text
0
    -> exact source template

> 0
    -> inherited/polymorphic source support
```

---

# 47. TARGET branch della definition endpoint VIEW

Per il lato TARGET:

```text
role
    = TARGET

declared_template_id
    = relationship_definitions.target_template_id

related_declared_template_id
    = relationship_definitions.source_template_id

relationship_name
    = relationship_definitions.reverse_name
```

`supported_template_id` include ogni template `X` tale che:

```text
X == target_template_id
OR
X derives from target_template_id
```

---

# 48. `UNION ALL` obbligatorio per definition endpoints

I due branch SOURCE e TARGET devono essere combinati con:

```text
UNION ALL
```

non:

```text
UNION
```

perché i due ruoli sono semanticamente distinti.

Questo vale anche quando:

```text
source_template_id == target_template_id
```

e anche quando:

```text
forward_name == reverse_name
```

---

# 49. Self-definition nella polymorphic VIEW

Per:

```text
source_template_id = A
target_template_id = A
forward_name = "connected_to"
reverse_name = "connected_to"
```

la VIEW deve comunque produrre due righe logiche per `A`:

```text
A / SOURCE / connected_to
A / TARGET / connected_to
```

Sono due role projections della stessa definition.

Non devono essere deduplicate.

---

# 50. Esempio polymorphic definition endpoint

Inheritance:

```text
Device
  ^
  |
Router
```

Definition:

```text
D1

source_template_id = Device
target_template_id = Network
forward_name = connected_to
reverse_name = connected_from
```

la VIEW deve rendere osservabile almeno:

```text
D1 | Device | SOURCE | Device | Network | connected_to | depth 0
D1 | Router | SOURCE | Device | Network | connected_to | depth 1
```

Quindi:

```text
lookup supported_template_id = Router
```

restituisce D1 senza richiedere all'application di implementare manualmente l'ancestry traversal.

---

# 51. Nessun cross-product preventivo source × target

La baseline non richiede di materializzare nella VIEW tutte le combinazioni:

```text
concrete source subtype
x
concrete target subtype
```

Esempio da evitare come projection base:

```text
Device       -> Network
Router       -> Network
Device       -> VlanNetwork
Router       -> VlanNetwork
...
```

per ogni definition.

Questo cross-product può crescere inutilmente.

La VIEW endpoint-oriented deve risolvere il polymorphism del ruolo interrogato.

La compatibility del concrete related endpoint viene verificata con la stessa ancestry predicate quando necessario.

---

# 52. Significato di `related_declared_template_id`

In:

```text
relationship_definition_endpoints
```

il campo:

```text
related_declared_template_id
```

rappresenta il tipo dichiarato dell'altro endpoint della definition.

Non rappresenta tutte le possibili concrete subtype identities del lato opposto.

Questo è intenzionale.

---

# 53. VIEW runtime `relationship_endpoints`

Per rendere semplice la domanda:

> quali Relationship coinvolgono questo Object, indipendentemente dal fatto che sia source o target?

viene ratificata una projection runtime:

```text
relationship_endpoints
```

La VIEW orienta ogni Relationship rispetto a ciascuno dei suoi due endpoint.

---

# 54. Shape logica di `relationship_endpoints`

Colonne concettuali:

```text
relationship_id
relationship_definition_id

object_id
related_object_id

role
relationship_name

declared_template_id
related_declared_template_id
```

La VIEW può inoltre esporre, senza cambiarne la semantica:

```text
actual object template ids
compatibility depth
```

se utili a query/debugging.

Queste colonne aggiuntive non devono però nascondere Relationship persistite in caso di dati corrotti.

---

# 55. SOURCE branch della runtime VIEW

Per il lato SOURCE:

```text
relationship_id
    = relationships.id

object_id
    = relationships.source_object_id

related_object_id
    = relationships.target_object_id

role
    = SOURCE

relationship_name
    = relationship_definitions.forward_name

declared_template_id
    = relationship_definitions.source_template_id

related_declared_template_id
    = relationship_definitions.target_template_id
```

---

# 56. TARGET branch della runtime VIEW

Per il lato TARGET:

```text
relationship_id
    = relationships.id

object_id
    = relationships.target_object_id

related_object_id
    = relationships.source_object_id

role
    = TARGET

relationship_name
    = relationship_definitions.reverse_name

declared_template_id
    = relationship_definitions.target_template_id

related_declared_template_id
    = relationship_definitions.source_template_id
```

---

# 57. `UNION ALL` obbligatorio nella runtime VIEW

Anche:

```text
relationship_endpoints
```

deve usare:

```text
UNION ALL
```

Non deve usare:

```text
UNION
DISTINCT
```

come semantica base.

Ogni Relationship produce due endpoint-role projections.

---

# 58. Duplicati runtime preservati dalla VIEW

Dato:

```text
R1: D / A -> B
R2: D / A -> B
```

la VIEW deve preservare entrambe le identities.

Dal punto di vista A:

```text
R1 / SOURCE / B
R2 / SOURCE / B
```

devono essere entrambe visibili.

Una UI può eventualmente aggregarle, ma la VIEW base non deve farlo.

---

# 59. Query naturale delle Relationship incidenti

Con la VIEW runtime, la query concettuale diventa:

```sql
SELECT *
FROM relationship_endpoints
WHERE object_id = :object_id;
```

senza richiedere al caller:

```text
source_object_id = :id
OR
target_object_id = :id
```

e senza richiedere branch applicativi per:

```text
forward_name
vs
reverse_name
```

---

# 60. Query naturale delle definitions supportate

Con la polymorphic definition VIEW:

```sql
SELECT *
FROM relationship_definition_endpoints
WHERE supported_template_id = :template_id;
```

restituisce:

```text
definitions supportate
+
ruolo SOURCE/TARGET
+
relationship_name corretto
+
declared related type
+
inheritance depth
```

includendo inheritance e polymorphism.

---

# 61. VIEW come access model, non source of truth

Le VIEW:

```text
object_template_ancestry
relationship_definition_endpoints
relationship_endpoints
```

sono projection/query model.

Non duplicano authoritative business state.

Le tabelle autorevoli rimangono:

```text
relationship_definitions
relationships
```

insieme al modello Object/ObjectTemplate già ratificato.

---

# 62. Perché non denormalizzare fisicamente Relationship

Non viene introdotta una tabella autorevole del tipo:

```text
relationship_endpoint_rows
```

con due righe persistite per Relationship.

Non vengono duplicate fisicamente:

```text
A -> B
B -> A
```

come due relationship facts.

Motivazione:

la duplicazione introdurrebbe nuovi invarianti di sincronizzazione:

```text
both endpoint rows must exist
both must reference same relationship
both must be created atomically
both must be deleted atomically
roles must never swap
names must remain consistent
```

Questi invarianti non servono perché la stessa proiezione può essere derivata deterministicamente tramite VIEW.

---

# 63. Perché il modello source/target è preferito

Per una relazione binaria e direzionale:

```text
source_object_id
target_object_id
```

esprimono direttamente il dominio.

Una generalized endpoint table avrebbe maggiore valore soltanto in un futuro modello con:

```text
n-ary relationships
dynamic endpoint roles
more than two endpoints
```

Questi requisiti non fanno parte del modello corrente.

---

# 64. Indici ratificati per Relationship runtime

Devono esistere indici separati su:

```text
relationships(source_object_id)
relationships(target_object_id)
```

Motivazione:

la principale query bidirezionale cerca un Object su entrambi i ruoli.

La VIEW runtime deve poter essere pianificata come due branch indicizzati.

---

# 65. Indici ratificati per RelationshipDefinition

Devono esistere indici separati su:

```text
relationship_definitions(source_template_id)
relationship_definitions(target_template_id)
```

Motivazione:

supportano:

```text
template-reference lookup
definition endpoint lookup
template delete dependency checks
```

e le query orientate ai due ruoli.

---

# 66. FK e indici referencing

La presenza di una FK PostgreSQL non deve essere considerata equivalente alla presenza automatica di un indice sulla colonna referencing.

Gli indici endpoint sopra sono quindi parte esplicita della baseline e non un'assunzione implicita.

---

# 67. Indici e duplicati

Gli indici:

```text
relationships(source_object_id)
relationships(target_object_id)
```

non sono UNIQUE.

Analogamente:

```text
relationship_definitions(source_template_id)
relationship_definitions(target_template_id)
```

non sono UNIQUE.

Non devono introdurre cardinalità o business uniqueness non ratificate.

---

# 68. Relationship compatibility non è espressa da una FK semplice

Le FK garantiscono:

```text
definition exists
source Object exists
target Object exists
```

ma non possono esprimere direttamente:

```text
source Object.template_id
    derives from definition.source_template_id

AND

target Object.template_id
    derives from definition.target_template_id
```

Questa è una domain admission invariant.

Il relativo concurrency contract verrà ratificato nella action `CREATE Relationship`.

---

# 69. Persisted Relationship invariant

Ogni Relationship valida deve soddisfare:

```text
source_object_id <> target_object_id

source Object exists
target Object exists
definition exists

source Object.template_id
    compatible with definition.source_template_id

target Object.template_id
    compatible with definition.target_template_id
```

I primi aspetti di identity/existence sono supportati direttamente da PK/FK/CHECK.

La compatibility polimorfica richiede il protocollo applicativo/action-specifico.

---

# 70. Nessuna dependency dalla ObjectTemplateVersion

Una Relationship runtime non persiste:

```text
source_template_version
target_template_version
```

e RelationshipDefinition non referenzia versioni.

Questo è intenzionale.

Relationship è definita a livello di:

```text
ObjectTemplate identity / lineage type
```

non di structural version.

---

# 71. Implicazione per OTV lifecycle

Publish/deprecate di una ObjectTemplateVersion non modifica direttamente una RelationshipDefinition e non invalida Relationship esistenti.

La type identity coinvolta rimane:

```text
object_templates.id
```

La Relationship compatibility non dipende dallo status della specifica OTV corrente dell'Object.

---

# 72. Nessun cascade implicito ratificato

Sono intenzionalmente assenti cascade:

```text
delete RelationshipDefinition
    -> delete Relationships

delete Object
    -> delete Relationships

delete ObjectTemplate
    -> delete RelationshipDefinitions
```

Queste dependency usano:

```text
ON DELETE RESTRICT
```

e richiedono cleanup esplicito nell'ordine corretto.

---

# 73. Relationship delete non influenza gli endpoint

La cancellazione di una Relationship runtime elimina soltanto:

```text
relationships row
```

Non elimina:

```text
source Object
target Object
RelationshipDefinition
ownership edges
```

Il concurrency contract specifico della delete verrà analizzato separatamente.

---

# 74. Nomi e Relationship identity

`forward_name` e `reverse_name` appartengono alla definition, non alla Relationship identity.

Una rename della definition non crea una nuova Relationship e non modifica:

```text
relationships.id
```

Il significato nominale osservato tramite le VIEW cambia in funzione della current definition.

---

# 75. Assenza di runtime ordering

Non è definito alcun business ordering fra Relationship incidenti a un Object.

L'eventuale:

```text
ORDER BY
```

usato da API/query deve essere considerato ordering di presentazione.

Non deve essere dedotto un ordine semantico da:

```text
relationship id
definition id
source/target position
```

senza una decisione separata.

---

# 76. Assenza di minimum cardinality

La presenza di una RelationshipDefinition non obbliga nessun Object a creare Relationship.

Per ogni Object e definition compatibile:

```text
number of Relationships may be 0
```

Questo vale sia dal lato SOURCE sia dal lato TARGET.

---

# 77. Assenza di maximum cardinality

Per ogni Object e definition compatibile:

```text
number of Relationships may be N
```

senza limite business espresso dal modello corrente.

Questo include Relationship duplicate con gli stessi endpoint e la stessa definition.

---

# 78. Caso self-template con due Object distinti

Definition:

```text
A -> A
```

Objects:

```text
A1
A2
A3
```

sono validi, se desiderati:

```text
A1 -> A2
A1 -> A3
A2 -> A1
```

e anche duplicate:

```text
R1: A1 -> A2
R2: A1 -> A2
```

Non è valido:

```text
A1 -> A1
```

---

# 79. Caso subtype su self-template definition

Inheritance:

```text
A
^
|
B
```

Definition:

```text
A -> A
```

può ammettere, per esempio:

```text
B1 -> A1
A1 -> B1
B1 -> B2
```

purché gli Object source/target siano distinti.

Questo deriva dal polymorphism applicato indipendentemente ai due endpoint.

---

# 80. Role support multiplo della stessa definition

Uno stesso ObjectTemplate può supportare la stessa definition:

```text
come SOURCE
come TARGET
```

contemporaneamente.

Questo accade naturalmente quando la template è compatible con entrambi gli endpoint dichiarati.

La VIEW deve preservare entrambi i role records.

Non deve collassarli.

---

# 81. Role semantico indipendente dal nome

Anche se:

```text
forward_name == reverse_name
```

SOURCE e TARGET rimangono ruoli distinti.

Il nome uguale non rende la Relationship non-direzionale a livello strutturale.

La direzione continua a essere persistita tramite:

```text
source_object_id
target_object_id
```

---

# 82. Non viene ratificata una Relationship "undirected"

Il modello corrente è sempre strutturalmente direzionale.

Una UI/domain semantics può scegliere nomi uguali per rappresentare una relazione percepita come simmetrica, ma il persistence model continua ad avere:

```text
SOURCE
TARGET
```

distinti.

Non viene introdotta una canonical endpoint sort per rendere la relation undirected.

---

# 83. Non viene ratificata una automatic reverse Relationship

Creare:

```text
A -> B
```

non crea automaticamente una seconda row:

```text
B -> A
```

La reverse view è una proiezione della **stessa** Relationship.

Non è una seconda Relationship runtime.

---

# 84. `reverse_name` non rappresenta una seconda Relationship

`reverse_name` è il nome con cui la stessa Relationship viene osservata dal TARGET.

Non implica:

```text
second relationships row
```

Questo chiarisce la differenza fra:

```text
reverse projection
```

e:

```text
reverse Relationship instance
```

---

# 85. Scope delle VIEW

Le VIEW ratificate hanno lo scopo di eliminare la scomodità applicativa delle query:

```text
source OR target
forward vs reverse
exact type OR inherited type
```

senza modificare il modello autorevole.

Non sono nuove domain entities.

---

# 86. RelationshipDefinition endpoint support di un Object

Per un Object concreto `O`, le definitions supportate si ottengono a partire da:

```text
O.template_id
```

e dalla polymorphic:

```text
relationship_definition_endpoints
```

Non si usa:

```text
O.template_version
```

per determinare la eligibility Relationship.

---

# 87. Relationship runtime incidenti a un Object

Per un Object concreto `O`, le Relationship incidenti si ottengono tramite:

```text
relationship_endpoints.object_id = O.id
```

La VIEW restituisce il corretto:

```text
relationship_name
role
related_object_id
```

senza branch source/target nel caller.

---

# 88. Separazione source of truth / access model

## Source of truth

```text
relationship_definitions
relationships

object_templates
object_template_versions
objects
```

secondo i rispettivi modelli ratificati.

## Derived access model

```text
object_template_lineage_edges
object_template_ancestry
relationship_definition_endpoints
relationship_endpoints
```

Le derived VIEW non introducono authoritative duplicated state.

---

# 89. Decisioni esplicitamente NON prese in questo documento

Per evitare ambiguità, i seguenti aspetti non sono implicitamente ratificati:

```text
- concurrency protocol delle action
- exact lock mode
- transaction isolation level
- retry semantics
- audit model per Relationship / RelationshipDefinition
- API/read model pubblico
- case-insensitive name semantics
- whitespace normalization dei nomi
- materialized ancestry closure
- multiple inheritance
- cardinalità diverse da 0..N
```

Richiedono documenti/action analysis separati.

---

# 90. Punto ancora aperto: mutabilità della Relationship runtime

Non è stata ancora ratificata una action:

```text
UPDATE Relationship
```

che possa cambiare:

```text
relationship_definition_id
source_object_id
target_object_id
```

Questo documento **non assume** automaticamente che tali campi siano mutabili nel dominio.

La decisione verrà presa durante l'inventario/action analysis di Relationship.

Fino a quella ratifica:

```text
non introdurre update semantics implicite
```

e non assumere che un cambio endpoint equivalga necessariamente a una update ammessa.

---

# 91. Punto non ratificato: abstract template come definition endpoint

Non è stata ancora presa una decisione esplicita sul fatto che una RelationshipDefinition possa o meno dichiarare:

```text
abstract ObjectTemplate
```

come source/target template.

Il modello relazionale non introduce un vincolo fisico su `abstract`.

Questa eventuale restriction, se desiderata, deve essere ratificata separatamente.

Non deve essere inventata dall'implementazione.

---

# 92. Verdetto finale — modello relazionale

Il persistence model autorevole ratificato è:

```text
relationship_definitions
------------------------
id                  PK
source_template_id  NOT NULL FK -> object_templates.id RESTRICT
target_template_id  NOT NULL FK -> object_templates.id RESTRICT
forward_name        NOT NULL
reverse_name        NOT NULL

CHECK(forward_name <> '')
CHECK(reverse_name <> '')

UNIQUE(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

e:

```text
relationships
-------------
id                          PK
relationship_definition_id  NOT NULL FK -> relationship_definitions.id RESTRICT
source_object_id             NOT NULL FK -> objects.id RESTRICT
target_object_id             NOT NULL FK -> objects.id RESTRICT

CHECK(source_object_id <> target_object_id)
```

Con indici:

```text
relationship_definitions(source_template_id)
relationship_definitions(target_template_id)

relationships(source_object_id)
relationships(target_object_id)
```

---

# 93. Verdetto finale — domain/business

> **RelationshipDefinition è una definition binaria e direzionale a livello ObjectTemplate identity.**
>
> Source e target template sono immutabili; solo `forward_name` e `reverse_name` sono modificabili.
>
> Entrambi i nomi devono essere non-empty, possono essere uguali, e la tuple `(source_template_id, target_template_id, forward_name, reverse_name)` è unique.
>
> `source_template_id == target_template_id` è ammesso.
>
> La cardinalità è sempre `0..N` su entrambi i lati.
>
> **Relationship runtime è una associazione non-owning fra due Object distinti.**
>
> `source_object_id == target_object_id` è vietato.
>
> La Relationship identity è esclusivamente `relationships.id`.
>
> Relationship duplicate con stessa definition/source/target sono esplicitamente ammesse.
>
> Inheritance e polymorphism valgono simmetricamente su source e target: una definition dichiarata su un base ObjectTemplate accetta Object appartenenti a subtype lineage.
>
> La compatibility dipende da `Object.template_id` e dalla template ancestry, non dalla `template_version`.
>
> `Object.template_id` è stabile lungo la vita dell'Object; uno `SCHEMA_CHANGE` che cambia soltanto version binding/properties non invalida Relationship esistenti.
>
> Relationship non appartiene alla ownership subtree lifecycle.
>
> Qualunque Relationship incidente a un Object del subtree blocca la Object delete tramite FK `RESTRICT`, anche se entrambi gli endpoint della Relationship sono interni allo stesso subtree.
>
> Una RelationshipDefinition può essere cancellata soltanto quando non è referenziata da Relationship runtime.
>
> Un ObjectTemplate referenziato da una RelationshipDefinition non può essere cancellato finché la definition esiste.
>
> La bidirezionalità di lettura e il polymorphism vengono risolti tramite VIEW PostgreSQL derivate (`object_template_ancestry`, `relationship_definition_endpoints`, `relationship_endpoints`), non tramite denormalizzazione fisica dello stato autorevole.
>
> `UNION ALL` preserva sempre i ruoli SOURCE/TARGET e le Relationship duplicate.
>
> Nessuna projection derivata sostituisce le tabelle autorevoli o introduce nuovo stato da sincronizzare.
