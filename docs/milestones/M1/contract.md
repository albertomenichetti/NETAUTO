# M1 — Kernel Consistency Baseline

**Status:** FINAL / FROZEN — milestone contract ratified. Scope, goals, non-goals and acceptance criteria are definitive for M1; any change requires explicit contract reopening and architecture impact analysis.

## 1. Missione

La milestone M1 ha l'obiettivo di consolidare il kernel fondamentale di NETAUTO attorno a un unico backend PostgreSQL e a un modello semanticamente stabile per i concetti di:

- `DataType`;
- `ObjectTemplate`;
- `Object`;
- `Relationship`.

Al termine della milestone, tali concetti devono formare un kernel minimale ma coerente, nel quale domain model, application contract, persistence model, Unit of Work, concurrency semantics, API e test rappresentino e preservino le stesse invarianti.

La priorità di M1 è la **correctness**: il dataset non deve poter raggiungere stati semanticamente o strutturalmente invalidi attraverso le operazioni supportate, incluse le operazioni concorrenti rilevanti.

M1 rappresenta inoltre il momento nel quale le decisioni esistenti sul kernel possono ancora essere messe in discussione liberamente. Il codice e la documentazione preesistenti costituiscono input per la review, non vincoli di backward compatibility.

---

## 2. Obiettivi

### G1 — PostgreSQL-only persistence

Completare la transizione a PostgreSQL e renderlo l'unico backend di persistenza supportato dal kernel.

SQLite e l'implementazione persistence in-memory non fanno parte dell'architettura target di M1 e devono essere rimossi come backend alternativi supportati.

Il domain model deve rimanere indipendente dalla tecnologia di persistenza, ma l'architettura applicativa e di persistence non deve mantenere astrazioni il cui unico scopo sia preservare una database portability non richiesta.

### G2 — Consolidamento di `DataType`

Revisionare e stabilizzare semantica, lifecycle, operazioni e invarianti di `DataType`, inclusi i rapporti con gli altri concetti del kernel.

Durante la review devono essere valutate anche eventuali capability o migliorie utili per l'evoluzione futura del type system. Ogni proposta deve essere deliberatamente classificata come:

- inclusa in M1 perché necessaria alla correttezza o alla coerenza del kernel;
- rinviata a una milestone futura;
- esclusa perché non coerente con gli obiettivi del progetto o non giustificata dalla complessità introdotta.

### G3 — Consolidamento di `ObjectTemplate`

Revisionare e stabilizzare semantica, lifecycle, versioning, inheritance, proprietà, riferimenti e operazioni di `ObjectTemplate`.

Il modello deve definire in modo non ambiguo quali stati e transizioni siano validi e quali dipendenze debbano essere preservate durante l'evoluzione dei template.

### G4 — Consolidamento di `Object`

Revisionare e stabilizzare identità, schema association, proprietà, lifecycle, operazioni e invarianti di `Object`.

Le operazioni che modificano un Object devono preservare sia la validità locale dell'Object sia la validità delle strutture e dei riferimenti che dipendono da esso.

### G5 — Consolidamento di `Relationship`

Revisionare e stabilizzare il modello delle Relationship, comprese le relative definizioni, la semantica degli endpoint, la compatibility, il lifecycle e le deletion semantics.

Il modello deve impedire la creazione o la permanenza di Relationship incompatibili con lo stato valido degli Object e degli ObjectTemplate coinvolti.

### G6 — Consolidamento delle invarianti cross-domain

Analizzare esplicitamente le interazioni tra `DataType`, `ObjectTemplate`, `Object` e `Relationship`.

La correttezza di M1 non viene valutata soltanto sui singoli aggregate o CRUD: nessuna operazione su un concetto del kernel deve poter rendere semanticamente invalido un altro concetto dipendente.

### G7 — Correttezza delle Unit of Work

Definire transaction boundary e Unit of Work coerenti con le operazioni del dominio.

Ogni operazione definita come atomica deve produrre interamente il proprio stato finale oppure non lasciare alcun effetto persistente osservabile.

Devono essere definite e verificate anche rollback semantics, failure semantics e mapping degli errori di persistenza rilevanti verso i contratti applicativi.

### G8 — Strong consistency e correttezza concorrente

Le invarianti ratificate devono rimanere vere anche in presenza delle operazioni concorrenti supportate.

Per ogni race significativa devono essere identificati il rischio, la garanzia richiesta e il meccanismo minimo necessario a preservarla.

La consistenza forte del dataset è un requisito primario del kernel e ha precedenza rispetto a ottimizzazioni premature di throughput o alla generalità del persistence layer.

### G9 — Baseline API coerente con il kernel

Revisionare e consolidare le API relative ai quattro concetti core in modo che input, output, operazioni e failure semantics rappresentino correttamente il domain model ratificato.

Durante M1 le API sperimentali esistenti possono essere modificate o rimosse quando necessario alla correttezza del modello.

Al termine di M1 deve esistere una baseline API stabile e funzionale per il perimetro del kernel consolidato.

### G10 — Verification coverage e traceability

Ogni invariante critica deve essere verificabile e tracciabile dal design fino ai test appropriati.

La strategia di verifica deve includere, secondo necessità:

- domain/unit test;
- integration test su PostgreSQL reale;
- test delle Unit of Work e del rollback;
- test dei constraint del persistence layer;
- concurrency test con transazioni realmente concorrenti.

I test di persistenza e concorrenza non devono dipendere da backend alternativi o simulazioni che non offrano le stesse garanzie di PostgreSQL.

---

## 3. Perimetro

M1 comprende la revisione e il consolidamento end-to-end di:

- domain model dei quattro concetti core;
- operazioni CRUD e operazioni domain-specific necessarie ai relativi lifecycle;
- invarianti locali e cross-domain;
- versioning e identity semantics dove applicabili;
- referential integrity;
- deletion semantics;
- Unit of Work e transaction boundary;
- persistence model PostgreSQL;
- constraint e garanzie demandabili al database;
- concurrency semantics;
- failure semantics;
- API relative al kernel;
- test e verifiche necessarie a dimostrare le garanzie ratificate;
- configurazione centralizzata delle connessioni PostgreSQL per runtime e test automatici.

Il perimetro include la possibilità di modificare o rimuovere strutture, API, migration, repository abstraction e decisioni pregresse quando ciò sia necessario a ottenere un kernel più corretto e coerente.

---

## 4. Non-obiettivi

Sono esplicitamente fuori dal perimetro di M1, salvo che un elemento minimo diventi strettamente necessario per garantire la correttezza del kernel definito in questa milestone:

- autenticazione e autorizzazione;
- multi-tenancy;
- `Observation`;
- discovery e onboarding da sorgenti esterne;
- reconciliation e desired/observed state;
- automation ed execution engine;
- scheduling e workflow;
- plugin system e plugin SDK;
- web UI;
- telemetry e time-series data;
- high availability e distributed deployment;
- supporto a persistence backend alternativi a PostgreSQL;
- database portability come requisito architetturale;
- backward compatibility con persistence model, migration o API sperimentali precedenti a M1;
- migrazione o conservazione di dati legacy non ancora soggetti a requisiti di produzione.

M1 non deve introdurre capability future soltanto perché risultano convenienti durante l'implementazione. Le evoluzioni non necessarie alla correttezza del perimetro devono essere rinviate a milestone successive.

---

## 5. Principi vincolanti

### P1 — Correctness first

La correttezza semantica e la consistenza del dataset hanno priorità rispetto a performance premature, compatibilità legacy sperimentale o generalità infrastrutturale.

### P2 — Domain semantics as authority

Il domain model definisce quali stati e transizioni abbiano significato.

Il persistence layer deve rafforzare tali garanzie impedendo, quando ragionevolmente esprimibile, stati strutturalmente impossibili.

### P3 — PostgreSQL as persistence authority

PostgreSQL è l'unico backend persistente supportato da M1 e può essere utilizzato deliberatamente per le garanzie che offre.

Una futura sostituzione di PostgreSQL richiederebbe una nuova decisione architetturale esplicita; la sostituibilità del database non è un requisito del kernel M1.

### P4 — No accidental abstractions

Le astrazioni devono esistere per rappresentare boundary o contratti reali del sistema, non esclusivamente per mantenere compatibilità con backend che il progetto non intende supportare.

### P5 — Atomic state transitions

Le operazioni di dominio che costituiscono una singola trasformazione logica devono essere persistite atomicamente.

Uno stato parzialmente applicato non è un risultato valido.

### P6 — Concurrency is part of correctness

Un'invariante non è considerata garantita se può essere violata da un interleaving concorrente legalmente eseguibile.

I concurrency contract fanno parte della specifica del kernel e non costituiscono un'ottimizzazione o un requisito secondario.

### P7 — Cross-domain correctness

La validità locale di una singola entità non è sufficiente.

Le operazioni devono preservare le invarianti dell'intero sottoinsieme di dataset interessato e le dipendenze tra i quattro concetti core.

### P8 — Design may challenge existing decisions

Durante la fase di design M1, qualsiasi decisione presente nel codice o nei documenti di lavoro precedenti può essere riesaminata.

Nessuna scelta viene mantenuta soltanto perché già implementata. Dopo il freeze del contract e dell'architettura, una modifica a una decisione ratificata richiede invece una riapertura esplicita del design e la relativa propagation documentale.

### P9 — Stable semantics before stable implementation

La stabilità perseguita da M1 riguarda prima di tutto il significato dei concetti, delle operazioni e degli errori.

I meccanismi implementativi devono derivare dalle invarianti ratificate e sono definiti dalla documentazione `architecture/` congelata. L'implementazione può decomporre tali decisioni, ma non reinterpretarle o sostituirle silenziosamente.

### P10 — Real PostgreSQL verification

Le garanzie attribuite a PostgreSQL, alle transazioni o alla concorrenza devono essere verificate contro PostgreSQL reale.

L'assenza del precedente backend in-memory non impedisce l'uso locale di fake o mock nei test unitari quando non rappresentano un persistence backend alternativo e non vengono utilizzati per dimostrare garanzie proprie del database.

---

## 6. Configurazione PostgreSQL

NETAUTO deve utilizzare configurazione esterna e centralizzata per determinare la connessione al database PostgreSQL.

Devono essere supportate almeno due configurazioni logicamente distinte:

- database runtime utilizzato dall'applicazione;
- database dedicato alle test-suite automatiche.

La test-suite deve poter utilizzare il proprio database senza dipendere dalla configurazione runtime e senza richiedere che il progetto gestisca direttamente provisioning o lifecycle dell'istanza PostgreSQL.

I nomi delle variabili, il punto concreto di composition e le modalità tecniche di inizializzazione appartengono alla documentazione `architecture/` e non sono fissati dal presente contract.

---

## 7. Acceptance criteria

### AC-01 — PostgreSQL authority

PostgreSQL è l'unico persistence backend supportato dal kernel M1.

Non rimangono implementazioni runtime SQLite o in-memory mantenute come backend alternativi equivalenti.

### AC-02 — Valid domain states

Tutti gli stati persistibili e tutte le transizioni supportate relative a `DataType`, `ObjectTemplate`, `Object` e `Relationship` rispettano le invarianti ratificate nella documentazione architetturale di M1.

### AC-03 — Cross-domain consistency

Nessuna operazione supportata su un concetto del kernel può committare uno stato che renda semanticamente invalido un altro concetto o riferimento dipendente.

### AC-04 — Transactional atomicity

Ogni operazione definita come atomica produce interamente lo stato finale previsto oppure non produce alcun effetto persistente parziale.

I failure path rilevanti preservano tale proprietà.

### AC-05 — Concurrent correctness

Gli interleaving concorrenti identificati come rilevanti e supportati non possono violare le invarianti ratificate del kernel.

Le relative garanzie sono verificate tramite test appropriati su PostgreSQL reale.

### AC-06 — Persistence enforcement

Le invarianti strutturali che possono essere ragionevolmente ed efficacemente rappresentate mediante primitive PostgreSQL sono protette anche dal persistence layer e non dipendono esclusivamente da validazioni applicative.

### AC-07 — API semantics

Le operazioni API incluse nel perimetro M1 hanno input, output e failure semantics esplicitamente definite e coerenti con il domain model ratificato.

Non esistono endpoint supportati che permettano di aggirare le invarianti del kernel.

### AC-08 — Verification and invariant traceability

Ogni invariante critica ratificata è tracciabile verso almeno una verifica adeguata e, quando la garanzia dipende da PostgreSQL o dalla concorrenza, verso uno o più integration/concurrency test eseguiti contro PostgreSQL reale.

### AC-09 — Runtime/test database separation

La configurazione del database runtime e quella del database utilizzato dalle test-suite automatiche sono separate, centralizzate e iniettabili dall'esterno.

Il provisioning e la gestione delle istanze PostgreSQL restano fuori dal perimetro applicativo di M1.

### AC-10 — No alternative-backend burden

Il design consolidato non mantiene implementazioni o astrazioni la cui unica responsabilità sia supportare backend di persistenza alternativi non previsti.

La separazione tra dominio e persistenza rimane invece preservata come boundary architetturale.

---

## 8. Stato definitivo del contract

Il presente `contract.md` è **FINAL / FROZEN**.

Le condizioni di freeze risultano soddisfatte:

- missione, obiettivi e non-obiettivi descrivono senza ambiguità il perimetro di M1;
- gli acceptance criteria sono sufficienti a determinare se M1 abbia raggiunto il proprio obiettivo;
- non rimangono decisioni di scope aperte;
- la documentazione normativa in `architecture/` è stata finalizzata, sottoposta a consistency review e congelata come baseline di implementazione.

Il contract definisce **cosa** M1 deve ottenere; `architecture/` definisce **come deve funzionare semanticamente e tecnicamente** il kernel per soddisfarlo.

Una modifica futura a missione, scope, non-obiettivi o acceptance criteria richiede una riapertura esplicita del milestone contract e una verifica/propagation dell'impatto sull'architettura congelata. La successiva decomposizione in `steps.md` deve derivare da contract e architecture senza estendere implicitamente il perimetro.
