# Linee guida di progetto

## Scopo

Questo documento definisce le regole generali di lavoro adottate per l'evoluzione di NETAUTO.

Il progetto viene sviluppato per milestone successive e l'implementazione di una milestone può iniziare soltanto dopo che il relativo perimetro e il relativo design sono stati definiti e congelati.

## Ruoli e modalità di lavoro

La fase di design e la fase di implementazione sono attività distinte.

Durante la fase di design vengono definiti:

- domain model;
- invarianti;
- contratti applicativi e di persistenza;
- Unit of Work e transaction boundary;
- concurrency contract;
- API contract;
- acceptance criteria;
- decomposizione implementativa.

Durante questa fase non viene sviluppato codice applicativo.

L'implementazione viene eseguita da Codex esclusivamente dopo il freeze del design della milestone.

Per ogni step:

1. viene prodotto un prompt implementativo coerente con il design congelato;
2. Codex realizza lo sviluppo e pubblica il relativo delta sul repository GitHub;
3. il delta viene revisionato rispetto ai contratti, alle invarianti e alla documentazione della milestone;
4. lo step viene considerato completato soltanto se repository, comportamento e documentazione risultano ancora coerenti.

Il codice non costituisce una fonte autonoma di decisioni architetturali: eventuali ambiguità devono essere risolte nel design.

## Repository e autorità documentale

Durante la core review il branch di riferimento è `core_review`.

La directory `docs.old/` costituisce memoria storica del progetto ed è da considerarsi read-only. Il suo contenuto non è normativo per il design corrente.

La documentazione corrente viene sviluppata sotto `docs/`.

I documenti temporanei non ancora assegnati a una milestone possono risiedere in `docs/wip/`.

Una volta definita una milestone, i documenti normativi relativi al suo perimetro risiedono sotto:

`docs/milestones/<milestone>/`

## Struttura delle milestone

Ogni milestone viene identificata con un nome progressivo (`M1`, `M2`, `M3`, ...) e utilizza la seguente struttura:

```text
docs/milestones/M1/
├── wip/
├── contract.md
├── steps.md
├── status.md
└── architecture/
```

### `wip/`

Contiene appunti, analisi, alternative, note e documenti temporanei.

Il suo contenuto non è normativo finché non viene consolidato nei documenti ufficiali della milestone.

### `contract.md`

Definisce cosa la milestone deve ottenere ad alto livello.

Deve contenere almeno:

- obiettivi;
- perimetro;
- non-obiettivi espliciti;
- concetti e capability interessati;
- risultati attesi;
- acceptance criteria verificabili.

`contract.md` definisce **cosa** la milestone deve ottenere, non i dettagli implementativi necessari per ottenerlo.

Lo sviluppo non può iniziare finché `contract.md` non è stato finalizzato e congelato.

### `architecture/`

Contiene i documenti tecnici e architetturali della milestone, separati per dominio o ambito quando opportuno.

Qui vengono definiti in dettaglio, tra gli altri:

- semantica del domain model;
- lifecycle;
- invarianti;
- contratti applicativi;
- Unit of Work;
- transaction boundary;
- persistence model;
- vincoli relazionali;
- concurrency contract;
- API contract;
- failure semantics;
- eventuali decisioni tecniche necessarie a garantire il contratto della milestone.

I documenti in `architecture/` definiscono **come deve funzionare semanticamente e tecnicamente** quanto stabilito in `contract.md`.

Lo sviluppo non può iniziare finché la documentazione architetturale necessaria alla milestone non è stata finalizzata e congelata.

### `steps.md`

Contiene la decomposizione della milestone in step implementativi.

Ogni step deve rappresentare, per quanto possibile, uno stato coerente e verificabile del repository e può essere considerato un'unità naturale di commit o revisione.

Ogni step deve indicare chiaramente:

- obiettivo;
- contratti e invarianti interessati;
- componenti coinvolti;
- verifiche richieste;
- condizioni necessarie per considerare lo step completato.

La decomposizione deve privilegiare step verticali rispetto a modifiche parziali per layer.

Quando un'invariante coinvolge domain model, persistence, API e test, lo step dovrebbe idealmente portare l'intera invariante a uno stato implementato e verificabile.

Lo sviluppo non può iniziare finché `steps.md` non è stato finalizzato e congelato.

### `status.md`

Contiene lo stato operativo corrente della milestone.

Deve permettere di determinare rapidamente:

- stato generale della milestone;
- step completati;
- step corrente;
- eventuali blocchi o problemi noti.

Non deve duplicare il contenuto di `contract.md`, `steps.md` o della documentazione architetturale.

## Ordine di definizione di una milestone

Ogni milestone segue il seguente ordine vincolante:

1. definizione e finalizzazione di `contract.md`;
2. definizione e finalizzazione dei documenti in `architecture/`;
3. definizione e finalizzazione di `steps.md`;
4. definizione iniziale di `status.md`;
5. avvio della fase di sviluppo.

Ogni fase dipende semanticamente dalla precedente.

Gli step implementativi devono derivare dal design architetturale e il design architetturale deve derivare dal contratto della milestone.

## Allineamento documentale durante il design

La documentazione architetturale non viene riallineata soltanto a fine fase: l'allineamento è parte della ratifica di ogni decisione.

Regola forte:

> quando un nuovo design point produce un finding retroattivo che modifica, raffina o chiude un'assunzione già presente in altri documenti normativi, la sequenza di design viene interrotta e il finding viene propagato immediatamente a tutti i documenti impattati prima di procedere con il design point successivo.

Non è ammesso rimandare consapevolmente la propagation a un futuro consistency sweep quando sono già noti i documenti affetti.

Una decisione cross-cutting è considerata consolidata soltanto quando risultano coerenti, per quanto applicabile:

```text
owning domain contract
cross-cutting architecture/realization index
persistence / Unit of Work baseline
concurrency companion
API/failure contract
acceptance/test matrix
milestone architecture index
```

### Pre-flight architetturale del design point successivo

Prima di iniziare un design point `N+1`, quando il nuovo punto dipende da semantiche, representation contract, invarianti o meccanismi già consolidati, deve essere eseguita una **re-validation pre-flight** della baseline documentale impattata.

La re-validation non deve basarsi sulla sola memoria della conversazione o su riassunti informali. Devono essere riletti i documenti normativi rilevanti nel repository, in misura proporzionata al tema.

Il set minimo tipico comprende, per quanto applicabile:

```text
owning domain document
cross-domain document directly involved
persistence/concurrency/API contract touched by the new point
milestone architecture index / closed-open status
```

Non è necessario rileggere meccanicamente l'intera milestone prima di ogni singolo punto quando le dipendenze sono circoscritte; è invece obbligatorio rileggere tutte le authority documentali da cui il nuovo design sta assumendo un contratto.

La sequenza operativa è:

```text
identify assumptions/dependencies of N+1
-> re-read authoritative milestone documents
-> verify that assumptions are still current and mutually coherent
-> if drift/conflict/stale-open marker is found: stop N+1
-> align/propagate documentation
-> only then resume N+1
```

Il pre-flight deve distinguere esplicitamente fra livelli diversi quando rilevante, per esempio:

```text
domain accepted input semantics
!=
canonical persistence representation
!=
public API wire representation
```

Una decisione del nuovo point non può restringere o ampliare implicitamente un contratto già congelato senza una esplicita architecture change e relativa propagation.

Un consistency sweep periodico resta comunque obbligatorio come verifica difensiva: serve a trovare drift non noto, stale-open marker, TODO già chiusi e contraddizioni sfuggite alla propagation immediata.

Una contraddizione tra documenti normativi è un **architecture defect**, non una libertà implementativa. Non deve essere risolta scegliendo il documento più recente o quello letto per ultimo: la documentazione va riallineata prima di codificare il comportamento interessato.

Quando una decisione chiude una precedente sezione “da finalizzare”, tale sezione deve essere aggiornata nello stesso ciclo oppure trasformata in un cross-link alla decisione ora autorevole.

## Freeze del perimetro

Lo sviluppo effettivo di una milestone non parte finché il suo perimetro non è congelato.

Dopo il freeze, il perimetro non deve essere ampliato durante l'implementazione.

Sono ammesse modifiche soltanto quando, durante lo sviluppo, emergono casi non previsti che devono necessariamente essere gestiti per garantire la correttezza semantica o funzionale di quanto già incluso nella milestone.

Nuove capability, miglioramenti opportunistici o funzionalità non necessarie alla correttezza del perimetro congelato devono essere rinviati a milestone successive.

Il freeze viene gestito pragmaticamente tramite Git e accordo esplicito sullo stato dei documenti, senza introdurre in questa fase workflow formali aggiuntivi di governance.

## Acceptance criteria

Ogni milestone deve definire acceptance criteria espliciti e verificabili all'interno di `contract.md`.

Gli acceptance criteria devono descrivere proprietà osservabili del sistema e non formulazioni generiche.

Esempio non sufficiente:

> La gestione delle Relationship deve essere robusta.

Esempio appropriato:

> Nessuna operazione concorrente supportata può produrre una Relationship incompatibile con gli endpoint secondo le invarianti ratificate.

Gli acceptance criteria rappresentano la condizione di successo della milestone e costituiscono il riferimento finale rispetto al quale verificare il risultato dell'implementazione.

## Invarianti e traceability

Le invarianti rappresentano le proprietà semantiche che il sistema deve preservare in ogni stato valido.

Le invarianti rilevanti devono essere esplicitate nella documentazione architetturale e, quando utile, identificate tramite un codice stabile per dominio, ad esempio:

```text
DT-INV-001
OT-INV-001
OBJ-INV-001
REL-INV-001
```

La numerazione non ha finalità burocratica: serve a rendere tracciabile la relazione tra design e implementazione.

La traceability desiderata è:

```text
Acceptance criterion
        ↓
Invariant
        ↓
Architecture decision / contract
        ↓
Implementation step
        ↓
Implementation mechanism
        ↓
Test / verification
```

`steps.md` deve quindi permettere di risalire dalle attività implementative alle invarianti e ai contratti che esse realizzano.

## Definizione dei contratti tecnici

Per ogni operazione significativa il design deve partire dalla semantica e non dal meccanismo tecnico.

La sequenza di ragionamento preferita è:

```text
Invariant
   ↓
Threat / race / invalid state
   ↓
Required guarantee
   ↓
Chosen mechanism
```

Meccanismi come constraint SQL, foreign key, unique constraint, CAS, row lock, advisory lock o livelli di isolamento transazionale sono strumenti utilizzati per garantire un'invariante; non definiscono essi stessi la semantica del dominio.

Quando possibile:

- il domain model deve definire quali stati abbiano significato;
- il persistence layer deve impedire gli stati strutturalmente impossibili che può ragionevolmente esprimere;
- le Unit of Work devono garantire che le trasformazioni di stato rilevanti siano atomiche;
- i concurrency contract devono garantire che le invarianti rimangano vere anche in presenza di operazioni concorrenti.

## Coerenza a fine step

La fine di ogni step implementativo deve lasciare il repository in uno stato coerente.

Devono rimanere allineati, per quanto interessati dallo step:

- domain model;
- application contract;
- persistence contract;
- schema e constraint del database;
- concurrency semantics;
- API contract;
- test;
- documentazione architetturale.

Uno step non deve essere considerato completato se introduce una divergenza semantica tra questi livelli.

Quando tecnicamente possibile, gli step devono quindi essere progettati come evoluzioni verticali e complete di un insieme limitato di invarianti o contratti.

## Principio generale

NETAUTO privilegia la correttezza semantica e la coerenza architetturale rispetto alla velocità di implementazione locale.

Le decisioni devono essere prese e documentate prima di essere trasformate in codice.

La documentazione deve permettere, per ogni comportamento importante, di rispondere in modo non ambiguo alle seguenti domande:

- quale proprietà del sistema stiamo cercando di garantire?
- dove è definita?
- quale operazione può minacciarla?
- quale meccanismo la preserva?
- quale step la implementa?
- quale verifica dimostra che il contratto è rispettato?
