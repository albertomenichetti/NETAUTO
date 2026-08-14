# M1 checkpoint — 2026-08-14

> **NON NORMATIVO / WIP**  
> Questo file è un checkpoint operativo per ricordare rapidamente **come siamo arrivati allo stato attuale** e **cosa manca prima della chiusura architetturale di M1**.  
> In caso di divergenza, fanno fede `docs/milestones/M1/contract.md` e i documenti normativi sotto `docs/milestones/M1/architecture/`.

## 1. Contesto di lavoro

Branch di riferimento della core review:

```text
core_review
```

Processo ratificato:

```text
contract
-> architecture
-> steps
-> status
-> implementation
```

Durante la fase corrente non si sviluppa codice applicativo. Il codice e i vecchi documenti sono input per la review, non authority semantica. `docs.old/` è memoria storica/read-only.

M1 ha come obiettivo il consolidamento del kernel PostgreSQL-only attorno a:

```text
DataType
ObjectTemplate
Object
Relationship
```

con strong consistency, Unit of Work corrette, persistence coerente, API/failure semantics allineate e verification su PostgreSQL reale.

---

# 2. Come siamo arrivati qui

## 2.1 Principio generale emerso durante la review

La linea architetturale che si è consolidata è:

> definire prima la semantica e le invarianti; scegliere dopo il meccanismo PostgreSQL minimo necessario a preservarle.

Nei punti in cui model-plane e data-plane interagiscono, il pattern preferito è:

> pagare il costo di interpretazione/certificazione quando cambia il modello; rendere il consumo runtime il più meccanico possibile.

Questo principio è visibile sia nell'`Active Model Graph` sia nel redesign finale delle Relationship.

---

# 3. DataType — stato attuale

Il dominio DataType è stato revisionato e considerato semanticamente chiuso per M1.

Decisioni principali:

- `DataType` = stable atomic scalar identity;
- `DataTypeVersion` = exact immutable value-schema snapshot dopo publish;
- lifecycle `DRAFT -> PUBLISHED -> DEPRECATED`;
- multiple DRAFT ammesse;
- DRAFT `revision` con optimistic concurrency;
- exact version pinning, nessun floating/latest binding persistito;
- `default_version` esplicita, valida solo verso PUBLISHED exact version;
- PrimitiveType built-in immutable e code-defined;
- canonicalizzazione e constraint validation deterministiche;
- enum canonicalizzato prima della duplicate detection;
- `SCALAR/LIST`, required/cardinality e migration semantics **non** appartengono al DataType ma al consumer/property layer;
- deprecation bloccata dai direct PUBLISHED lifecycle-sensitive consumer;
- whole-lineage delete solo senza external references.

PrimitiveType M1:

```text
core.string
core.integer
core.number
core.boolean
core.date
core.datetime
core.ip
core.ip_prefix
core.byte_size
```

Nota importante: `number` è exact finite decimal; datetime è absolute/offset-aware e canonicalizzato UTC; IP/prefix e byte-size hanno canonicalizzazione intrinseca definita.

---

# 4. ObjectTemplate — stato attuale

Il dominio ObjectTemplate è stato revisionato e considerato semanticamente chiuso per M1.

## 4.1 Stable lineage e versioning

`ObjectTemplate` rappresenta la stable type identity.

`ObjectTemplateVersion` rappresenta una exact schema snapshot.

Stable nella lineage:

```text
id
namespace
name
abstract
parent lineage
```

Version-specific:

```text
exact parent version
local properties
local component slots
```

Parent lineage è scelta alla create e non cambia tramite normali operation.

## 4.2 Active Model Graph

Principio centrale:

> una PUBLISHED model snapshot appartiene a un grafo attivo in cui tutte le direct lifecycle-sensitive exact dependencies sono anch'esse PUBLISHED.

Conseguenze:

- publish consumer vs deprecate dependency devono serializzare;
- DTV deprecation è bloccata dai direct PUBLISHED OTV consumer;
- exact parent OTV deprecation è bloccata dai direct PUBLISHED child OTV;
- lineage-level refs non entrano in questo invariant;
- runtime Object esistenti non bloccano la deprecation di exact OTV/DTV.

## 4.3 Properties

Property semantic key storico:

```text
(declaring_template_id, name)
```

Decisioni principali:

- exact DTV pin;
- `SCALAR | LIST`;
- `required` determina cardinalità;
- `migration_default` solo per required e solo per colmare assenza;
- `migration_default` non sostituisce mai un source value esistente;
- LIST ordinata, homogeneous, duplicati ammessi;
- niente property override/shadow;
- historical name e `datatype_id` stabili dopo first publication;
- normale value-mode evolution solo `SCALAR -> LIST`;
- remove/re-add same declaring lineage conserva historical semantic identity.

## 4.4 Component slots

Component = ownership slot `0..N`, non embedded value e non generic Relationship.

Slot semantic key storico:

```text
(declaring_template_id, name)
```

Target è ObjectTemplate lineage-level.

Normal evolution del target: widening verso ancestor.

Property e slot condividono lo stesso effective member namespace.

## 4.5 Effective schema

Source of truth:

```text
exact parent pin
+
local property declarations
+
local component declarations
```

Effective schema derivato dinamicamente root -> leaf.

Nessuna materializzazione autorevole degli inherited member.

---

# 5. Object — stato attuale

Il dominio Object è stato revisionato e considerato semanticamente chiuso per M1.

## 5.1 Identity e schema binding

```text
Object.id
    -> authoritative runtime identity

Object.template_id
    -> stable type assignment

Object.template_version
    -> exact current schema pin
```

`template_id` non cambia nelle normali operation M1.

Future cross-lineage reclassification sarà un workflow controllato, non generic update.

## 5.2 CREATE

Object CREATE:

- target lineage non abstract;
- exact target OTV esplicita oppure `default_version` risolta e materializzata;
- selected OTV deve restare PUBLISHED fino al commit;
- runtime properties canonicalizzate e validate contro exact effective closure;
- unknown properties reject;
- JSON null non valido;
- optional LIST absent e `[]` convergono a key assente;
- `migration_default` non usato in CREATE;
- Object nasce detached;
- current state + lifecycle `CREATED` atomicamente.

## 5.3 Nessun generic Object revision

M1 **non** introduce `Object.state_revision`.

Strong consistency viene ottenuta tramite action-specific concurrency contract.

## 5.4 Mutation primitives

Operation separate:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
ATTACH
DETACH
DELETE
```

Nessun generic full-object update.

### DATA_CHANGE

Per-property `SET`/`REMOVE`, complete candidate validation, LIST whole replacement, no partial mutation.

### SCHEMA_CHANGE

- forward-only intra-lineage;
- same `template_id`;
- exact target PUBLISHED OTV;
- source/target closure separate;
- property carry via `PropertySemanticKey`;
- existing incompatible value => migration fails;
- migration_default fills absence only;
- no remediation/transformation M1;
- outgoing ownership attachments devono restare valide;
- incoming ownership e Relationships non richiedono revalidation perché dipendono dal stable `template_id`.

## 5.5 Ownership graph

Ownership è distinto dalle generic Relationship.

Invarianti:

- child ha al massimo un owner/slot;
- self-attach vietato;
- graph aciclico;
- forest semantics;
- ATTACH idempotente sull'exact existing edge;
- DETACH idempotente se child already detached;
- no implicit move;
- global ownership-graph write gate per la phase cycle-check + edge-add di ATTACH;
- parent-local concurrency domain per ATTACH/DETACH vs parent SCHEMA_CHANGE.

## 5.6 DELETE

Object DELETE:

- exact Object only;
- no subtree delete;
- no implicit detach;
- no relationship cleanup;
- richiede zero incoming/outgoing ownership e zero external current references;
- delete + `DELETED` lifecycle atomici;
- FK/reference semantics devono essere RESTRICT, non CASCADE.

---

# 6. Unified lifecycle changelog — stato attuale

Il changelog M1 è operativo, non compliance/audit subsystem.

Event kinds correnti:

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
ATTACH_TO
DETACH_FROM
RELATIONSHIP_CREATED
RELATIONSHIP_DELETED
DELETED
```

Principi:

- append-only nelle normali kernel workflow;
- public surface read-only;
- event IDs UUIDv4 kernel-generated;
- `occurred_at` kernel-owned;
- ordering `(occurred_at, event_id)`;
- nessuna strict global commit-order guarantee;
- historical identifiers nel changelog non sono live FK;
- current mutation + complete required lifecycle **event set** devono commit/rollback insieme.

Per Object/ownership mutation l'event set ha cardinalità 1.

Per Relationship può avere cardinalità > 1 secondo le distinct object-relative semantic views.

---

# 7. Relationship R2 — come ci siamo arrivati

Relationship è stato il dominio più iterativo della review.

Il primo modello consolidato era basato su:

```text
RelationshipDefinition
    source_template_id
    target_template_id
    forward_name
    reverse_name

Relationship
    source_object_id
    target_object_id
```

Durante la review sono emersi diversi problemi:

- `forward/reverse` dipendevano dal punto di vista del caller e non erano vere semantics di dominio;
- la symmetry derivata da endpoint/name produceva regole fragili;
- una singola factual Relationship doveva essere navigabile uniformemente dai due endpoint;
- future Relationship properties rischiavano di riaprire pesantemente il graph model;
- source/target canonical ordering tendeva a riapparire come artificio tecnico nel runtime e nel changelog.

La soluzione finale è il **resolved graph model R2**.

---

# 8. Relationship R2 — stato frozen

## 8.1 Model-plane aggregate

```text
RelationshipDefinition
----------------------
id
symmetric
```

```text
RelationshipResolution
----------------------
id
relationship_definition_id
from_template_id
to_template_id
name
```

Le Resolution sono authoritative child state della Definition aggregate.

Non sono CRUD resource indipendenti.

Stable:

```text
Definition.id
Definition.symmetric
Resolution.id
Resolution.from_template_id
Resolution.to_template_id
```

Mutable:

```text
Resolution.name
```

## 8.2 Definition shape

Non-symmetric:

```text
exactly 2 reciprocal Resolution
names distinct
```

Esempio:

```text
VM         -> Hypervisor / is_hosted_by
Hypervisor -> VM         / hosts
```

Symmetric same-template:

```text
1 Resolution
T -> T / name
```

Symmetric different-template:

```text
2 reciprocal Resolution
same semantic name
```

Endpoint template-space overlap via inheritance è ammesso.

## 8.3 Definition CREATE API semantics

Non-symmetric input = due unordered endpoint perspectives:

```text
[
    { template_id, name },
    { template_id, name }
]
```

Symmetric input:

```text
endpoint_template_a
endpoint_template_b
name
```

Il caller non crea direttamente Resolution e non esprime forward/reverse.

Il domain genera complete Resolution set + IDs e valida one-shot semantic equivalence/conflict prima del commit.

## 8.4 Model-plane conflict rule

Due Resolution di Definition **distinte** confliggono se:

```text
same name
AND
from-template spaces overlap
AND
to-template spaces overlap
```

Definition semantic equivalence = stessa:

```text
symmetric
+
complete unordered semantic Resolution set
```

Il costo di conflict interpretation viene pagato su Definition CREATE/RENAME, non nel runtime hot path.

## 8.5 Runtime factual aggregate

```text
Relationship
------------
id
relationship_definition_id
```

La header è la factual association identity.

Questo è anche il futuro seam naturale per:

```text
relationship_definition_version
properties
```

## 8.6 Runtime resolved child state

```text
RuntimeRelationshipResolution
-----------------------------
relationship_id
resolution_id
from_object_id
to_object_id
```

Le runtime rows sono authoritative child state, non aggregate indipendenti.

Runtime CREATE è resolution-based:

```text
CREATE(
    resolution_id,
    from_object_id,
    to_object_id
)
```

Endpoint compatibility usa solo stable `Object.template_id` + lineage ancestry.

## 8.7 Complete runtime closure

Ogni factual Relationship materializza tutte le object-relative resolved access paths necessarie per permettere lookup uniforme via:

```text
WHERE from_object_id = O
```

Non-symmetric:

- selected endpoint assignment non è intercambiabile;
- materializza le reciprocal perspectives della stessa factual association.

Symmetric:

- factual endpoint pair è unordered;
- materializza tutte le distinct `(resolution, from_object, to_object)` view applicabili alle due assignment;
- same-template distinct objects => due rows con stessa Resolution;
- self-loop => deduplica;
- inheritance overlap può produrre fino a quattro runtime rows.

Ogni Relationship aggregate deve avere una sola factual endpoint pair e un runtime child set che sia **esattamente** la deterministic complete closure prevista.

## 8.8 Runtime uniqueness/idempotency

Exact resolved-view uniqueness:

```text
(resolution_id, from_object_id, to_object_id)
```

appartiene ad al massimo una current factual Relationship.

CREATE che trova già la exact view converge sulla stessa factual Relationship e non genera nuova mutation/event set.

DELETE è exact `relationship_id` based e idempotente sull'assenza; questo preserva ABA safety.

## 8.9 Runtime read model

Raw resolved storage lookup:

```text
RuntimeRelationshipResolution
WHERE from_object_id = O
```

A causa di inheritance overlap, più rows possono descrivere la stessa object-relative semantic association.

Quindi:

```text
RuntimeRelationshipResolution
    -> resolved storage/index model

ObjectRelationshipView
    -> semantic read projection
```

La semantic read projection deduplica per factual relationship/object perspective/name.

## 8.10 Relationship lifecycle

Una factual Relationship transition non produce un event per runtime row.

Produce:

> un event per ogni distinct object-relative semantic view.

Event shape Relationship:

```text
object_id
canonical_name

destination_object_id
destination_canonical_name

relationship_id
relationship_definition_id
relationship_name
```

Non persistiamo nel changelog:

```text
source/target
forward/reverse
direction
relationship_resolution_id
```

Esempi:

- ordinary two-endpoint association: normalmente 2 events;
- symmetric self-loop: 1 event;
- non-symmetric self-loop con due names: 2 events;
- 4 runtime rows per inheritance overlap possono collassare a 2 lifecycle semantic-view events.

---

# 9. Naming condiviso

Persisted model entities usano:

```text
<kind>.<namespace>.<name>
```

Namespace:

```text
segment("." segment)*
segment = [a-z][a-z0-9_]*
```

`core` e `core.*` reserved.

Local semantic names (properties, slots, RelationshipResolution names) usano:

```text
[a-z][a-z0-9_]*
```

max 64, no normalization automatica.

---

# 10. Cosa manca prima della chiusura architetturale di M1

I quattro domain model core sono ora semanticamente consolidati. Prima di poter considerare `architecture/` completa e passare a `steps.md`, resta da chiudere il **cross-cutting technical architecture**.

Ordine di lavoro suggerito:

## 10.1 Persistence model PostgreSQL complessivo

Da derivare dagli invarianti frozen, non dallo schema corrente.

Da definire almeno:

- tabelle/aggregate layout per DataType/Version;
- ObjectTemplate/Version/local property/component layout;
- Object current state;
- ownership edges;
- RelationshipDefinition + RelationshipResolution;
- Relationship factual header + RuntimeRelationshipResolution;
- unified lifecycle event persistence;
- JSON/typed representation delle canonical properties;
- PK/FK/UNIQUE/CHECK/index;
- RESTRICT/CASCADE policy;
- whole-lineage delete physical strategy;
- historical changelog identifiers senza live FK;
- runtime/test database configuration boundary.

Particolare attenzione:

- vecchio `ObjectComponentRow` usa CASCADE e deve diventare coerente con RESTRICT semantics;
- schema Relationship pre-R2 deve essere sostituito integralmente;
- la DB authority per exact resolved-view uniqueness va progettata esplicitamente;
- complete aggregate/closure invariants non devono essere lasciati accidentalmente alla sola application code se PostgreSQL può rafforzarne parti in modo ragionevole.

## 10.2 Unit of Work e transaction boundary

Definire per ogni mutation significativa:

```text
read/admission set
candidate construction
persistence mutation set
lifecycle event/event-set append
commit/rollback boundary
```

Da esplicitare soprattutto:

- publish/deprecate model-plane;
- Object CREATE/DATA_CHANGE/SCHEMA_CHANGE;
- ownership ATTACH/DETACH;
- RelationshipDefinition CREATE/RENAME/DELETE;
- Relationship CREATE/DELETE con complete runtime closure + lifecycle event set.

## 10.3 Concurrency architecture e lock ordering

Le invarianti sono già note; manca il meccanismo PostgreSQL concreto.

Da chiudere:

- model-plane write serialization per DT/OT/RelationshipDefinition dove necessaria;
- active-model-graph publish/deprecate coordination;
- DRAFT revision/CAS implementation;
- Object DATA_CHANGE vs SCHEMA_CHANGE;
- parent ownership SCHEMA_CHANGE vs ATTACH/DETACH;
- single-owner authority;
- global ownership cycle write gate;
- Relationship exact resolved-view uniqueness/concurrent convergence;
- CREATE/DELETE races con Object/Definition/lineage delete;
- global lock acquisition ordering per evitare deadlock;
- isolation level e retry strategy.

## 10.4 API/application contract finale

Da consolidare dopo persistence/UoW/concurrency perché l'API deve riflettere il domain frozen, non la baseline pre-M1.

Da definire:

- command/read DTO;
- explicit vs implicit version resolution;
- RelationshipDefinition create symmetric/non-symmetric shape;
- Relationship CREATE resolution-based;
- Object DATA_CHANGE `SET/REMOVE` shape;
- lifecycle reads;
- semantic read projection Relationship;
- delete/idempotency responses;
- pagination/list/read contracts.

## 10.5 Failure semantics / error taxonomy

Mappare in modo coerente:

```text
NotFound
Conflict
StaleRevision
NotPublishable
InUse / DeleteBlocked
EndpointIncompatible
SchemaMigrationBlocked
OwnershipConflict/Mismatch/Cycle
SemanticDefinitionConflict
Persistence/concurrency retryable failures
```

Il mapping application/API non deve esporre accidentalmente errori SQL come domain contract.

## 10.6 Verification strategy

Per ogni invariant critica definire unit/integration/concurrency verification.

PostgreSQL reale obbligatorio per ciò che dipende da:

- FK/constraints;
- transaction isolation;
- locks;
- concurrent uniqueness;
- publish/deprecate races;
- ownership cycle/single-owner;
- Relationship closure concurrency;
- rollback atomicity.

## 10.7 Architecture final consistency pass

Quando persistence/UoW/concurrency/API/failures saranno scritti:

- rileggere tutti i domain docs;
- verificare che nessun meccanismo tecnico abbia reinterpretato la semantics;
- controllare cross-domain delete/lifecycle/race;
- verificare traceability da `contract.md` agli invariant codes.

Solo dopo questo pass `architecture/` può essere considerata frozen.

## 10.8 `steps.md`

Dopo architecture freeze:

- decomporre M1 in step verticali;
- ogni step deve lasciare repo coerente;
- traceability `AC -> INV -> architecture -> step -> mechanism -> test`;
- privilegiare slice end-to-end rispetto a layer-only refactor.

## 10.9 `status.md`

Dopo `steps.md`:

- inizializzare stato operativo;
- indicare step corrente;
- poi iniziare implementazione via Codex.

---

# 11. Future/RFE importanti da non trascinare dentro M1

Da ricordare ma **non riaprire durante la chiusura M1** salvo necessità di correctness:

- auth/authz e tenancy;
- Observation/discovery/reconciliation/automation/workflow/plugin system;
- Object cross-lineage reclassification;
- schema downgrade/rollback;
- Object state_revision/ETag generico;
- migration remediation/transformation;
- richer component cardinality;
- RelationshipDefinitionVersion + typed Relationship properties;
- Relationship property migration;
- multi-edge factual Relationship con state distinti;
- historical `as-of` reconstruction;
- richer composite/expanded reads;
- CDC/replication ordering token.

Relationship properties sono una RFE importante ma il modello R2 è stato costruito appositamente per inserirle senza reinterpretare il resolved graph:

```text
RelationshipDefinition
    -> stable topology/navigation

future RelationshipDefinitionVersion
    -> exact typed property schema

Relationship
    -> future exact RDV pin + properties

RuntimeRelationshipResolution
    -> invariato resolved access-path state
```

---

# 12. Stato sintetico

```text
M1 contract
    -> frozen baseline

DataType domain architecture
    -> semanticamente chiusa

ObjectTemplate domain architecture
    -> semanticamente chiusa

Object domain architecture
    -> semanticamente chiusa

Relationship R2 domain architecture
    -> semanticamente chiusa

Cross-cutting persistence/UoW/concurrency/API/failure architecture
    -> DA FARE

Final architecture consistency pass
    -> DA FARE

steps.md
    -> DA FARE

status.md
    -> DA FARE

implementation
    -> NON INIZIATA
```

Prossimo punto di ripartenza consigliato:

> **derivare il persistence model PostgreSQL M1 complessivo dagli invarianti frozen dei quattro domini.**
