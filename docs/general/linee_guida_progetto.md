# Linee guida di progetto

## Scopo e tipi di ciclo

Questo documento definisce le regole generali di lavoro adottate per l'evoluzione di NETAUTO.

Lo sviluppo della code-base avviene esclusivamente all'interno di due tipi di ciclo:

- **milestone**, identificata da `M`, per l'evoluzione funzionale e architetturale pianificata del software;
- **fix**, identificato da `F`, per la correzione di difetti della baseline già consegnata senza introdurre nuove capability o modifiche intenzionali del public API contract.

Fuori da uno di questi cicli non è possibile modificare la code-base.

Le milestone seguono la naming convention `M1`, `M2`, ... `Mn`.

I fix seguono la naming convention `F1-1`, `F1-2`, `F2-1`, ... `Fn-m`: `Fx-y` identifica il fix `y` eseguito temporalmente dopo `Mx` e prima di `Mx+1`.

Ogni ciclo opera su un branch dedicato. Per i fix, il nome del branch corrisponde al nome del ciclo. Il merge su `master` è sempre un'attività umana e non viene mai eseguito dall'agente.

## Regole comuni ai cicli

### Authority documentale

Il codice non costituisce **MAI** una fonte autonoma di decisioni architetturali.

Le decisioni normative correnti devono essere ricavate dai documenti autorevoli del ciclo e, per lo stato già consegnato, da `docs/architecture/`.

Codice, Git history, chat, riassunti, report dell'implementatore e risultati diagnostici possono essere evidence, strumenti di navigazione o fonti utili all'analisi, ma **non sostituiscono l'autorità documentale corrente**.

Non è ammesso risolvere una contraddizione scegliendo implicitamente il documento più recente, quello letto per ultimo, il comportamento corrente del codice o la soluzione tecnicamente più conveniente.

Directory o file storici rimossi dal working tree non devono essere ripristinati come baseline implicita. La memoria storica rimane disponibile nella Git history e nei record dei cicli precedenti.

### AS-IS corrente, TO-BE e record storico

Devono essere distinti tre ruoli documentali:

```text
docs/architecture/
    = AS-IS architetturale autorevole del sistema già consolidato e consegnato

docs/milestones/<Mx>/
    = TO-BE normativo della milestone Mx durante il ciclo
      + record storico permanente del ciclo dopo la consegna

docs/fixes/<Fx-y>/
    = perimetro e correction design normativi del fix durante il ciclo
      + record storico permanente del ciclo dopo la consegna
```

Ogni nuovo ciclo parte dall'AS-IS corrente in `docs/architecture/`.

Tutti gli assunti iniziali, le condizioni ereditate e i comportamenti dichiarati invariati devono essere verificabili e coerenti con `docs/architecture/`.

Se un ciclo assume come punto di partenza una proprietà, una semantica, una struttura o un comportamento che non è verificabile in `docs/architecture/`, oppure risulta in contraddizione con essa, il lavoro sul punto interessato entra in **STOP**. Prima di procedere deve essere chiarito se:

- `docs/architecture/` è incompleta o non allineata allo stato corrente realmente consolidato;
- l'assunto iniziale del ciclo è errato;
- il ciclo sta in realtà introducendo una modifica architetturale che deve essere dichiarata e progettata esplicitamente.

La discrepanza deve essere risolta documentalmente prima di continuare il design o trasformare l'assunto in codice.

Una milestone può divergere intenzionalmente dall'AS-IS nei punti che intende evolvere: la divergenza non è un conflitto quando è esplicitamente identificata come modifica TO-BE, deriva da `contract.md` ed è consolidata nella documentazione architetturale della milestone. Una differenza non dichiarata o non tracciabile è drift documentale.

Un fix, invece, corregge il comportamento già dovuto: non può usare il ciclo correttivo come canale implicito per introdurre una nuova capability, una breaking change o una nuova semantica di prodotto.

### Naming delle slice

Ogni step implementativo prende il nome di **slice**.

L'identificativo locale è zero-padded:

```text
S01
S02
...
Snn
```

L'identificativo completo include sempre il ciclo:

```text
M1-S01
M2-S03
F1-1-S01
F2-1-S04
```

Nei documenti interni allo stesso ciclo è ammessa la forma locale `Snn` quando il contesto è inequivocabile. Nei prompt, nei commit, nei report, nei riferimenti cross-document e nelle comunicazioni operative deve essere preferita la forma completa `Mx-Snn` o `Fx-y-Snn`.

### Execution aid e `wip/`

Le directory `wip/` contengono appunti, analisi, alternative, note, prompt implementativi e review-fix temporanei.

Il loro contenuto non è normativo finché non viene consolidato nei documenti ufficiali del ciclo.

La regola operativa è:

```text
wip/
    = execution aid e materiale temporaneo ancora attivi

Git history
    = memoria degli aid già eseguiti o superseded
```

Quando un prompt è stato eseguito e viene sostituito da un review-fix, oppure quando la relativa slice è stata definitivamente accettata, il prompt operativo concluso viene rimosso da `wip/`. Non deve essere mantenuto nel working tree soltanto come memoria storica.

### Implementer, reviewer e lifecycle della slice

Implementazione e review hanno responsabilità distinte:

```text
implementer / Codex
    = produce un candidate implementativo e il relativo report di esecuzione

reviewer
    = verifica il delta realmente pubblicato nel repository e decide se accettarlo
```

Il report dell'implementatore è un ausilio alla review, non una prova autonoma di completamento. Dichiarazioni come test eseguiti, working tree pulito, commit pubblicato o comportamento implementato devono essere verificate, per quanto necessario, contro il repository e l'evidence effettivamente disponibile.

La sequenza ordinaria di una slice è:

```text
pre-flight implementativo
    -> prompt della slice
    -> implementation candidate
    -> push del delta sul branch del ciclo
    -> report dell'implementatore
    -> review del delta reale rispetto alle authority congelate
    -> eventuale review-fix nella stessa slice
    -> nuova review
    -> reviewer approval
    -> slice COMPLETED
```

Sono reviewer-owned almeno le transizioni:

```text
slice -> COMPLETED
cycle -> DELIVERED
review outcome -> ACCEPTED / REVIEW CHANGES REQUIRED
```

Quando la review individua un implementation defect o una verification gap appartenente alla slice corrente, la slice non viene chiusa e non si crea artificiosamente una nuova slice per correggerla. Il lavoro rimane parte della stessa slice e lo stato operativo deve rendere visibile il finding, per esempio:

```text
IN PROGRESS — REVIEW CHANGES REQUIRED
```

### Re-validation delle authority

Ogni re-validation deve essere:

- **dependency-driven**: si rileggono tutte le authority da cui il punto assume semantica, rappresentazione o garanzie;
- **repository-based**: memoria, chat e report non sostituiscono i documenti normativi correnti;
- **proporzionata allo scope**: non è necessario rileggere meccanicamente l'intero ciclo quando le dipendenze sono circoscritte;
- **bloccante in presenza di drift o contradiction**: se una dipendenza non è verificabile o coerente, il lavoro interessato entra in STOP fino alla risoluzione.

Il pattern generale è:

```text
identify scope and dependencies
    -> re-read authoritative documents
    -> verify assumptions are current and mutually coherent
    -> if drift / contradiction / stale-open marker exists: STOP
    -> resolve and propagate the finding
    -> restore a coherent frozen state when required
    -> only then resume
```

Questo pattern viene applicato in tre momenti distinti:

- **design pre-flight**, prima di un design point che dipende da decisioni già consolidate;
- **implementation pre-flight**, prima di predisporre o eseguire il prompt di ogni slice;
- **reopen**, quando un finding mette in discussione una decisione già congelata.

Particolare attenzione è richiesta quando esistono rappresentazioni differenti. Non devono essere confuse implicitamente, per esempio:

```text
domain accepted-input semantics
!=
canonical in-memory/domain state
!=
canonical persistence representation
!=
public API wire representation
```

### Finding: implementation defect vs architecture defect

Ogni finding emerso durante design, implementation, test o review deve essere classificato almeno distinguendo:

```text
implementation defect
    = le authority applicabili definiscono già in modo corretto e univoco
      il comportamento atteso; è il codice a non rispettarlo

architecture defect / missing decision
    = le authority sono contraddittorie, incomplete, non allineate,
      errate oppure non permettono di determinare un comportamento univoco
```

Nel caso di **implementation defect**, il design rimane valido. Si corregge l'implementazione nel rispetto delle authority esistenti e, quando il difetto è riproducibile o riguarda un contratto rilevante, si aggiunge o rafforza una regression verification adeguata. Non si riapre l'architettura soltanto perché il codice contiene un bug.

Nel caso di **architecture defect / missing decision**, il comportamento interessato entra immediatamente in **STOP**. Non è ammesso scegliere in codice una delle interpretazioni possibili, indebolire una verifica per ottenere un risultato verde, usare il comportamento corrente dell'implementazione come nuova authority o proseguire sulla base della soluzione tecnicamente più conveniente.

La sequenza obbligatoria è:

```text
finding
    -> classificazione come architecture defect / missing decision
    -> STOP del comportamento interessato
    -> identificazione dello scope di riapertura
    -> re-read delle authority pertinenti
    -> decisione / correzione architetturale esplicita
    -> propagation nello stesso ciclo a tutti i documenti normativi impattati
    -> verifica di coerenza della baseline riallineata
    -> re-freeze esplicito del design interessato
    -> solo dopo ripresa dell'implementazione
```

La riapertura deve essere proporzionata al finding: non è necessario riaprire l'intero ciclo quando il problema è circoscritto, ma devono essere riesaminate tutte le authority da cui la decisione dipende e tutti i documenti che ne rappresentano le conseguenze. Una correzione cross-cutting richiede una propagation cross-cutting.

### Invariante di completion di una slice

Ogni slice deve lasciare il repository in uno stato coerente e verificabile.

Devono rimanere allineati, per quanto interessati dalla slice:

- domain model;
- application contract;
- persistence contract;
- schema e constraint del database;
- concurrency semantics;
- API contract;
- failure semantics;
- test e verification;
- documentazione architetturale e normativa del ciclo.

Una slice non può essere considerata `COMPLETED` se introduce una divergenza semantica tra questi livelli.

Quando tecnicamente possibile, le slice devono essere progettate come evoluzioni verticali e complete di un insieme limitato di invarianti, contratti o defect.

## Principi di design semantico

### Invarianti e traceability

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
Acceptance criterion / defect correction requirement
        ↓
Invariant / required property
        ↓
Architecture decision / contract
        ↓
Implementation slice
        ↓
Implementation mechanism
        ↓
Test / verification
```

`steps.md` deve quindi permettere di risalire dalle attività implementative alle invarianti, ai contratti o ai defect che esse realizzano.

### Definizione dei contratti tecnici

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

### Confine fra architettura e decomposizione implementativa

Il design architetturale deve chiudere tutte le decisioni necessarie a determinare in modo univoco:

- semantica del dominio e stati validi;
- invarianti e failure semantics;
- boundary applicativi e pubblici;
- garanzie di persistenza, atomicità e concorrenza quando rilevanti;
- rappresentazioni o meccanismi tecnici quando fanno parte della correttezza richiesta;
- verification contract necessario a dimostrare le garanzie.

Non deve invece trasformarsi in micro-governance dell'implementazione. Dettagli locali come struttura dei moduli, helper, fixture, naming interno, disposizione dei test o decomposition tecnica restano libertà implementative quando non modificano una semantica, una garanzia, un boundary o una verification authority congelata.

```text
semantic / correctness choice
    -> deve essere chiusa nel design prima del coding

local implementation decomposition
    -> può essere scelta durante implementation
       se preserva integralmente le authority frozen
```

Un dubbio su un dettaglio implementativo non giustifica di per sé la riapertura dell'architettura; una scelta che cambierebbe il significato o la garanzia del sistema invece sì.

### Principio generale

NETAUTO privilegia la correttezza semantica e la coerenza architetturale rispetto alla velocità di implementazione locale.

Le decisioni devono essere prese e documentate prima di essere trasformate in codice.

La documentazione deve permettere, per ogni comportamento importante, di rispondere in modo non ambiguo alle seguenti domande:

- quale proprietà del sistema stiamo cercando di garantire?
- dove è definita?
- quale operazione può minacciarla?
- quale meccanismo la preserva?
- quale slice la implementa?
- quale verifica dimostra che il contratto è rispettato?

## Funzionamento di un ciclo di milestone (M)

### Separazione fra design e implementazione

La fase di design e la fase di implementazione sono attività distinte e temporalmente separate.

Durante la fase di design vengono definiti, per quanto applicabili:

- domain model;
- invarianti;
- contratti applicativi e di persistenza;
- Unit of Work e transaction boundary;
- concurrency contract;
- API contract;
- acceptance criteria;
- decomposizione implementativa.

Durante questa fase non viene sviluppato codice applicativo.

L'implementazione viene eseguita da Codex esclusivamente dopo il completamento dei design gate della milestone.

### Struttura documentale della milestone

Tutta la documentazione relativa alla milestone `Mx` viene sviluppata sotto `docs/milestones/<Mx>/`:

```text
docs/milestones/<Mx>/
├── wip/
├── contract.md
├── architecture/
│   ├── README.md
│   └── ...
├── steps.md
├── status.md
└── acceptance.md        # quando previsto o utile
```

#### `contract.md`

Definisce **cosa** la milestone deve ottenere ad alto livello e non i dettagli implementativi necessari per ottenerlo.

Deve contenere almeno:

- obiettivi;
- perimetro;
- non-obiettivi espliciti;
- concetti e capability interessati;
- risultati attesi;
- acceptance criteria verificabili.

Gli acceptance criteria devono descrivere proprietà osservabili del sistema e non formulazioni generiche.

Esempio non sufficiente:

> La gestione delle Relationship deve essere robusta.

Esempio appropriato:

> Nessuna operazione concorrente supportata può produrre una Relationship incompatibile con gli endpoint secondo le invarianti ratificate.

Gli acceptance criteria rappresentano la condizione di successo della milestone e costituiscono il riferimento finale rispetto al quale verificare il risultato dell'implementazione.

#### `architecture/`

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

##### `architecture/README.md` e architecture-set lifecycle

Ogni milestone deve avere obbligatoriamente `docs/milestones/<Mx>/architecture/README.md`.

Il README non è un semplice indice e non deve diventare una seconda copia delle decisioni contenute nei documenti owning. È il documento di controllo e di ingresso dell'**architecture set** della milestone.

Il contenuto minimo deve includere:

- **purpose e authority boundary** — `contract.md` possiede il perimetro, `architecture/README.md` possiede composizione e stato del set, i singoli documenti indicizzati possiedono le decisioni di dettaglio;
- **architecture-set status** — uno stato inequivocabile come `DESIGN IN PROGRESS`, `FROZEN` oppure `PARTIALLY REOPENED`;
- **normative document map** — documenti che compongono il set e area/domain/cross-cutting concern posseduto da ciascuno;
- **coverage / ownership map** — aree necessarie al contract, relativo owning document e presenza di eventuali gap;
- **open design points** — punti ancora aperti durante il design; al freeze deve risultare esplicitamente che non rimangono open point necessari all'implementazione;
- **freeze / reopen state** — stato corrente del set e, in caso di riapertura, scope interessato fino al successivo re-freeze.

La regola preferita è:

```text
architecture/README.md
    = map + ownership + status + closure del set

owning architecture documents
    = contenuto semantico e tecnico autorevole
```

Il README è l'authority per lo **stato complessivo** del set; il contenuto di una decisione appartiene invece al relativo owning document.

La milestone può entrare in implementazione soltanto quando l'architettura è stata congelata **come insieme**. La dichiarazione:

```text
ARCHITECTURE SET = FROZEN
```

significa che:

- il normative document map è completo per il perimetro della milestone;
- ogni area necessaria al contract ha un owning document identificato;
- non rimangono open design point che lascino libertà semantica all'implementazione;
- le decisioni cross-cutting sono state propagate nei documenti impattati;
- il corpus è stato sottoposto a consistency sweep sufficiente a verificarne la mutua coerenza;
- le verification authority necessarie a dimostrare le garanzie congelate sono definite o almeno contrattualmente determinate in modo sufficiente per la successiva decomposition.

Prima del freeze gli header/status dei documenti individuali devono essere sottoposti a consistency sweep e resi coerenti con lo stato del set. Eventuali eccezioni intenzionali devono essere dichiarate esplicitamente nel README. Un documento locale non può creare implicitamente una libertà di design in contrasto con il set-level freeze; la prevalenza del set è una protezione contro il drift, non un sostituto della pulizia documentale.

Se un punto viene riaperto dopo il freeze, il README deve rendere visibile lo scope riaperto e lo stato del set finché la decisione non è stata revalidata, propagata e nuovamente congelata.

#### `steps.md`

Contiene la decomposizione della milestone in slice implementative.

Ogni slice deve rappresentare, per quanto possibile, uno stato coerente e verificabile del repository e può essere considerata un'unità naturale di commit o revisione.

Ogni slice deve indicare chiaramente:

- obiettivo;
- contratti e invarianti interessati;
- componenti coinvolti;
- verifiche richieste;
- condizioni necessarie per considerarla completata.

La decomposizione deve privilegiare slice verticali rispetto a modifiche parziali per layer. Quando un'invariante coinvolge domain model, persistence, API e test, la slice dovrebbe idealmente portare l'intera invariante a uno stato implementato e verificabile.

#### `status.md`

Contiene lo stato operativo corrente della milestone.

Deve permettere di determinare rapidamente:

- stato generale della milestone;
- slice completate;
- slice corrente;
- eventuali blocchi o problemi noti.

Non deve duplicare il contenuto di `contract.md`, `steps.md` o della documentazione architetturale.

### Design gate e ordine vincolante

Ogni milestone segue il seguente ordine:

1. definizione, finalizzazione e freeze di `contract.md`;
2. definizione, consistency review e freeze dell'architecture set, dichiarato da `architecture/README.md`;
3. definizione, finalizzazione e freeze di `steps.md`;
4. definizione iniziale di `status.md`;
5. avvio della fase di sviluppo.

Ogni fase dipende semanticamente dalla precedente.

Gli step implementativi devono derivare dal design architetturale e il design architetturale deve derivare dal contratto della milestone.

### Allineamento documentale durante il design

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
architecture/README.md
```

Quando una decisione chiude una precedente sezione “da finalizzare”, tale sezione deve essere aggiornata nello stesso ciclo oppure trasformata in un cross-link alla decisione ora autorevole.

Un consistency sweep periodico resta obbligatorio come verifica difensiva per trovare drift non noto, stale-open marker, TODO già chiusi e contraddizioni sfuggite alla propagation immediata.

### Pre-flight architetturale del design point successivo

Prima di iniziare un design point `N+1`, quando il nuovo punto dipende da semantiche, representation contract, invarianti o meccanismi già consolidati, deve essere applicata la disciplina generale di re-validation.

Il set minimo tipico comprende, per quanto applicabile:

```text
owning domain document
cross-domain document directly involved
persistence / concurrency / API contract toccato dal nuovo punto
architecture/README.md e relativo closed/open status
```

Una decisione del nuovo point non può restringere o ampliare implicitamente un contratto già congelato senza una esplicita architecture change e relativa propagation.

### Freeze del perimetro

Lo sviluppo effettivo di una milestone non parte finché il suo perimetro non è congelato.

Dopo il freeze, il perimetro non deve essere ampliato durante l'implementazione.

Sono ammesse modifiche soltanto quando, durante lo sviluppo, emergono casi non previsti che devono necessariamente essere gestiti per garantire la correttezza semantica o funzionale di quanto già incluso nella milestone.

Nuove capability, miglioramenti opportunistici o funzionalità non necessarie alla correttezza del perimetro congelato devono essere rinviati a milestone successive.

Il freeze viene gestito pragmaticamente tramite Git e accordo esplicito sullo stato dei documenti, senza introdurre workflow formali aggiuntivi di governance.

### Pre-flight implementativo della milestone

Prima di predisporre o eseguire il prompt di ogni `Mx-Snn` deve essere applicata la disciplina generale di re-validation verificando, per quanto applicabile:

```text
contract.md ancora FINAL / FROZEN
architecture set ancora FROZEN
architecture/README.md corrente e coerente con il set
owning domain / cross-domain authority della slice
persistence / Unit of Work / concurrency / API authority coinvolte
invarianti e verification richieste dalla slice
assenza di contradiction, architecture gap o reopen pendenti
```

Se una verifica fallisce, la slice entra in STOP **prima** dell'esecuzione del prompt e il problema deve essere risolto tramite il processo di reopen applicabile.

### Final acceptance gate della milestone

Il completamento di tutte le slice è una condizione necessaria, ma **non sufficiente**, per dichiarare conclusa una milestone:

```text
slice completion
    !=
milestone acceptance
```

Una milestone può entrare nel final acceptance gate soltanto quando tutte le slice previste da `steps.md` risultano `COMPLETED` dopo review.

Il gate finale deve verificare, in misura proporzionata al perimetro e al rischio della milestone, almeno:

- chiusura esplicita di tutti gli acceptance criteria definiti in `contract.md`;
- regressione integrata del repository, non soltanto test isolati per slice;
- coerenza finale tra domain model, application contract, persistence, schema/constraint, concurrency semantics, API, failure semantics e verifiche, per quanto applicabili;
- migration/schema closure quando la milestone modifica la persistenza;
- traceability sufficiente dal contract e dalle invarianti fino alle verifiche che ne dimostrano il rispetto;
- static analysis, reproducibility/build e altri quality gate ratificati dal progetto quando applicabili;
- assenza di architecture/documentation drift noto o di finding aperti incompatibili con la consegna;
- eventuali deliverable operativi richiesti espressamente dalla milestone.

La forma concreta dell'evidence non è prescritta uniformemente. La verification closure deve essere **integrata, verificabile e durevole**, con un livello di rigore adeguato alla complessità e ai rischi del contract.

Quando utile, l'evidence finale può essere raccolta in `acceptance.md`; la presenza del file non è obbligatoria salvo che sia prevista dal contract o dagli step. Deve però essere sempre possibile determinare in modo non ambiguo quale verifica dimostra ciascun criterio di accettazione rilevante e gli esiti dichiarati devono essere supportati dal repository e dai risultati effettivamente revisionati.

Il final acceptance gate è reviewer-owned: l'implementatore può preparare l'acceptance candidate ed eseguire le verifiche richieste, ma non può dichiarare autonomamente la milestone `DELIVERED`.

## Funzionamento di un ciclo di fix (F)

### Scopo del fix

Un ciclo di fix corregge difetti della baseline già consegnata. Non introduce nuove capability, non amplia intenzionalmente il comportamento del prodotto e non modifica intenzionalmente il public API contract.

Se l'analisi dimostra che la correzione richiede una nuova capability, una breaking change o una nuova semantica di prodotto, il lavoro non appartiene più a un ciclo di fix e deve essere pianificato in una milestone.

Ogni fix parte dall'AS-IS autorevole corrente in `docs/architecture/` e viene eseguito su un branch dedicato il cui nome corrisponde al ciclo `Fx-y`.

### Struttura documentale del fix

```text
docs/fixes/<Fx-y>/
├── wip/
├── defects.md
├── architecture/          # opzionale: solo quando serve correction design architetturale
│   ├── README.md          # obbligatorio se architecture/ è utilizzata
│   └── ...
├── steps.md
└── status.md
```

`architecture/` viene utilizzata quando almeno un defect richiede una correzione o una chiarificazione architetturale; può essere omessa quando tutti i defect sono puramente implementativi e l'AS-IS esistente è già univoco e corretto.

Quando `architecture/` è presente, `architecture/README.md` è obbligatorio e svolge lo stesso ruolo di architecture-set control/index definito per le milestone, adattato al **correction-design set** del fix: dichiara composizione, ownership, open point, stato di freeze/reopen e confine con l'AS-IS corrente.

### `defects.md`

`defects.md` definisce il perimetro correttivo del ciclo e svolge, per un fix, il ruolo di ingresso che `contract.md` svolge per una milestone.

Ogni defect deve avere un identificativo stabile e univoco nel ciclo, per esempio:

```text
F1-1-DEF-001
F1-1-DEF-002
F2-1-DEF-001
```

Per ogni defect devono essere documentati almeno:

- **Observed defect** — comportamento osservato e motivo per cui costituisce un difetto;
- **Reproduction evidence** — prova concreta, ripetibile e verificabile del problema sulla baseline difettosa;
- **Violated authority** — regola, invariante, contract, API guarantee, persistence guarantee o altra authority già consegnata che il comportamento viola;
- **Analysis** — classificazione e causa del problema per quanto necessarie a progettare la correzione;
- **Correction design** — comportamento corretto atteso e, quando necessario, decisioni architetturali o tecniche che lo garantiscono;
- **Regression evidence** — verifica permanente o durevole che deve dimostrare che il defect non è più presente dopo il fix.

La descrizione può evolvere durante l'analisi. Inizialmente un defect può contenere soltanto identità, descrizione e prova di riproducibilità; prima del freeze devono però risultare chiari authority violata, classificazione e correction design.

### Reproduction-first

Nessun defect può essere considerato pronto per l'implementazione finché il problema non è stato riprodotto in modo sufficientemente deterministico e verificabile.

La reproduction evidence deve fallire o dimostrare il comportamento errato sulla baseline difettosa. Quando tecnicamente appropriato, la stessa evidence deve essere trasformata nella regression verification permanente che passerà dopo la correzione.

La reproduction evidence non deve essere necessariamente fin dall'inizio il test definitivo: defect complessi possono richiedere harness, diagnostica o una procedura controllata. Deve però essere abbastanza concreta da distinguere un difetto reale da un'ipotesi o da un comportamento soltanto sospetto.

### Analisi e correction design

La classificazione del defect segue la tassonomia comune `implementation defect` vs `architecture defect / missing decision`.

Per un **implementation defect**, il fix non deve reinventare il design: la correzione deve riportare il codice all'AS-IS già autorevole e aggiungere o rafforzare la regression evidence necessaria.

Per un **architecture defect / missing decision**, il comportamento interessato entra in STOP fino a quando la correzione architetturale non è stata progettata nel ciclo di fix. Le authority AS-IS coinvolte devono essere rilette e il correction-design set deve essere congelato prima di implementare.

### Freeze del ciclo di fix

`defects.md` deve raggiungere uno stato esplicitamente frozen prima dell'implementazione. Il freeze chiude il perimetro del ciclo: il fix corregge tutti e soli i defect presenti nel documento congelato, salvo dipendenze strettamente necessarie a correggerli correttamente.

La sequenza è:

```text
raccolta defect
    -> reproduction di ogni defect
    -> identificazione delle authority violate
    -> analysis e classificazione
    -> correction design
    -> propagation documentale necessaria
    -> freeze di defects.md
    -> se architecture/ è presente: architecture/README.md dichiara il correction-design set FROZEN
```

Un nuovo defect scoperto dopo il freeze non viene aggiunto automaticamente al ciclo corrente. Normalmente viene registrato per un ciclo successivo, ad esempio `F1-2` dopo `F1-1`.

Se un nuovo finding è inseparabile dalla correzione corretta di un defect già frozen, il perimetro interessato deve essere riaperto esplicitamente, il finding deve essere documentato e propagato, e `defects.md` deve essere nuovamente congelato prima di riprendere l'implementazione. Il freeze non deve essere aggirato facendo crescere implicitamente il bug train.

### `steps.md` e `status.md`

Dopo il freeze dei defect viene definito e congelato `steps.md`, decomponendo il ciclo in slice verticali e verificabili.

Ogni slice deve indicare chiaramente:

- quali defect frozen corregge o fa avanzare;
- quali authority e componenti sono coinvolti;
- quale correction design realizza;
- quali regression verification devono passare;
- quali verifiche integrate sono richieste;
- quali condizioni consentono al reviewer di marcarla `COMPLETED`.

`status.md` mantiene lo stato operativo corrente con la stessa separazione fra authority normativa e avanzamento utilizzata nelle milestone.

### Pre-flight implementativo del fix

Prima di ogni `Fx-y-Snn` deve essere applicata la disciplina generale di re-validation verificando almeno:

```text
defects.md frozen
correction-design set frozen, quando architecture/ è presente
authority AS-IS violate o interessate
regression evidence richieste dalla slice
assenza di reopen pendenti sui defect coinvolti
```

Se una verifica fallisce, la slice entra in STOP prima dell'esecuzione del prompt.

### Final regression gate del fix

Il completamento delle singole slice non è sufficiente a chiudere un ciclo di fix. Quando tutte le slice sono `COMPLETED`, deve essere eseguito un final regression gate integrato.

Il gate finale deve verificare almeno:

- tutti i defect frozen risultano corretti e verificati;
- tutte le reproduction evidence originarie sono ora soddisfatte come regression evidence o sono state sostituite da verifiche permanenti equivalenti e più forti;
- la suite di regressione integrata applicabile rimane verde;
- non sono state introdotte nuove capability o modifiche intenzionali del public contract;
- eventuali correzioni di persistence, schema, concurrency, API o failure semantics sono coerenti con il correction design frozen;
- non rimangono architecture/documentation drift o finding aperti incompatibili con la consegna;
- static analysis, build/reproducibility e quality gate ratificati applicabili risultano soddisfatti.

L'evidence finale deve essere verificabile e durevole in misura proporzionata al rischio del ciclo. L'implementatore può preparare il candidate e i risultati, ma l'approvazione del final regression gate è reviewer-owned.

## Chiusura formale dei cicli

Il completamento delle slice non equivale alla consegna del ciclo. La chiusura formale può iniziare soltanto dopo l'approvazione reviewer-owned del relativo gate finale:

```text
milestone
    -> final acceptance gate APPROVED

fix
    -> final regression gate APPROVED
```

### Consolidamento dell'AS-IS

`docs/architecture/` deve descrivere esclusivamente l'**AS-IS architetturale autorevole del sistema consegnato**.

Per una milestone, a chiusura di `Mx` devono essere derivate dalle decisioni approvate del ciclo soltanto le informazioni necessarie a descrivere correttamente il sistema risultante, integrandole e armonizzandole con la baseline AS-IS precedente.

Per un fix, eventuali correction design architetturali vengono consolidati e armonizzati in `docs/architecture/`; se il fix è puramente implementativo, deve comunque essere verificato che l'AS-IS documentale rimanga corretto e coerente con il software consegnato.

Il consolidamento non è un copy/paste della documentazione del ciclo. Deve produrre una documentazione corrente coerente e autosufficiente, dalla quale sia possibile comprendere l'architettura del sistema senza ricostruire la sequenza storica dei cicli.

Nel nuovo AS-IS devono essere rimossi o riformulati i riferimenti che hanno senso soltanto nel contesto temporale del ciclo, per esempio:

```text
target della milestone
durante Mx
da implementare
candidate
stato futuro
```

quando tali formulazioni non descrivono più il sistema consegnato.

### Preservazione del record storico

La chiusura non comporta lo spostamento, la fusione o la cancellazione dei documenti del ciclo per trasferirli in `docs/architecture/`.

Per una milestone rimangono nel record del ciclo, tra gli altri:

```text
contract.md
architecture/
steps.md
status.md
acceptance.md, quando presente
```

Per un fix rimangono nel record del ciclo, tra gli altri:

```text
defects.md
architecture/, quando presente
steps.md
status.md
```

Il materiale `wip/` segue la disciplina degli execution aid e non diventa automaticamente architettura corrente.

I documenti dei cicli e la Git history preservano **perché**, **quando** e **attraverso quale ciclo** una decisione o una correzione è stata introdotta; `docs/architecture/` preserva invece la fotografia autorevole dello stato corrente.

### Stato `DELIVERED` e merge

Dopo il consolidamento dell'AS-IS e la verifica della coerenza finale:

1. il reviewer aggiorna `status.md` del ciclo a `DELIVERED`;
2. il branch del ciclo può essere mergiato su `master`;
3. il merge viene eseguito dall'essere umano e **MAI** dall'agente.

Un ciclo terminato deve quindi lasciare software, verification, documentazione del ciclo e `docs/architecture/` mutuamente coerenti, senza perdita della memoria storica e senza trasformare un fix in un canale implicito di evoluzione funzionale.