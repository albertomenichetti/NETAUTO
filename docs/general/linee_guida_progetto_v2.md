# Linee guida di progetto

## Scopo

Questo documento definisce le regole generali di lavoro adottate per l'evoluzione di NETAUTO.

Lo sviluppo viene fatto su cicli di milestone, identificati da M, e cicli di fix, identificati da F; fuori da una di queste due fasi non è possibile mettere mano alla code-base.
I cicli di milestone hanno naming convention M1, M2,...Mn ed è all'interno di tali cicli che il software evolve.
I cicli di fix hanno naming convention F1-1, F1-2, F2-1,....Fn-m; in generale Fx-y è il ciclo di fix y e temporalmente è stato eseguito tra Mx ed Mx+1; durante i cicli di fix si risolvono eventuali problemi ma non si introducono funzionalità e non si cambia l'api contract.

I cicli di fix vengono effettuati su branch dedicati il cui nome corrisponde al nome del ciclo.

## Funzionamento di un ciclo di milestone (M)

La fase di design e la fase di implementazione sono attività distinte ed avvengono in fasi temporalmente separate.

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

Per ogni step implementativo, che prende il nome di slice, viene utilizzato un identificativo locale zero-padded `S01`, `S02`, ... `Snn`. L'identificativo completo include sempre il ciclo di appartenenza, per esempio `M1-S01`, `M2-S03`.

Nei documenti interni alla stessa milestone è ammesso usare la forma locale `Snn` quando il contesto è inequivocabile; nei prompt, nei commit, nei report, nei riferimenti cross-document e nelle comunicazioni operative deve essere preferita la forma completa `Mx-Snn`.

Per ogni slice:

1. viene prodotto un prompt implementativo coerente con il design congelato;
2. Codex realizza lo sviluppo e pubblica il relativo delta sul repository GitHub;
3. il delta viene revisionato rispetto ai contratti, alle invarianti e alla documentazione della milestone;
4. lo step viene considerato completato soltanto se repository, comportamento e documentazione risultano ancora coerenti.

### Ownership della review e stato delle slice

Implementazione e review hanno responsabilità distinte:

```text
implementer / Codex
    = produce un candidate implementativo e il relativo report di esecuzione

reviewer
    = verifica il delta realmente pubblicato nel repository e decide se accettarlo
```

Il report dell'implementatore è un ausilio alla review, non una prova autonoma di completamento. Dichiarazioni come test eseguiti, working tree pulito, commit pubblicato o comportamento implementato devono essere verificate, per quanto necessario, contro il repository e l'evidence effettivamente disponibile.

La sequenza ordinaria di una slice è quindi:

```text
Codex completa il candidate
    -> push del delta sul branch del ciclo
    -> report di esecuzione
    -> review del delta reale rispetto alle authority congelate
    -> eventuali review-fix
    -> nuova review
    -> solo il reviewer può marcare la slice COMPLETED
```

Lo stesso principio vale per la chiusura della milestone: l'implementatore può produrre un acceptance candidate e la relativa evidence, ma non può dichiarare autonomamente la milestone `DELIVERED`. Gli stati di accettazione finale sono reviewer-owned.

Sono quindi reviewer-owned almeno le transizioni:

```text
slice -> COMPLETED
milestone -> DELIVERED
review outcome -> ACCEPTED / REVIEW CHANGES REQUIRED
```

Quando la review individua un implementation defect o una verification gap appartenente alla slice corrente, la slice **non** viene chiusa e non si crea artificiosamente una nuova slice per correggerla. Il lavoro rimane parte della stessa slice e lo stato operativo deve rendere visibile il finding, per esempio:

```text
IN PROGRESS — REVIEW CHANGES REQUIRED
```

Il reviewer può predisporre un prompt di review-fix mirato esclusivamente ai finding emersi. Codex applica il fix, pubblica un nuovo delta e il risultato torna in review. La slice diventa `COMPLETED` soltanto dopo l'accettazione del candidate complessivo.

### Disciplina degli execution aid in `wip/`

`docs/milestones/<Mx>/wip/` deve rendere evidente quale lavoro operativo è ancora attivo. I prompt implementativi e di review-fix sono execution aid non normativi e non devono accumularsi fino a rendere ambiguo quale sia l'istruzione corrente.

La regola operativa è:

```text
docs/milestones/<Mx>/wip/
    = execution aid ancora attivi

Git history
    = memoria dei prompt e degli aid già eseguiti o superseded
```

Quando un prompt è stato eseguito e viene sostituito da un review-fix, oppure quando la slice è stata definitivamente accettata, il prompt operativo ormai concluso viene rimosso da `wip/`. La sua storia rimane recuperabile da Git e non deve essere conservata nel working tree soltanto come memoria.

Il codice non costituisce **MAI** una fonte autonoma di decisioni architetturali: eventuali ambiguità devono essere risolte nel design.

### Struttura documentale

Tutta la documentazione relativa alla specifica milesone Mx viene sviluppata sotto `docs/milestones/<Mx>/`.

Durante il ciclo di milestone devono essere mantenuti distinti due livelli documentali con ruoli diversi:

```text
docs/architecture/
    = AS-IS architetturale autorevole del sistema già consolidato e consegnato

docs/milestones/<Mx>/
    = TO-BE normativo della milestone Mx, limitatamente al perimetro e alle modifiche
      che la milestone intende introdurre
```

`docs/architecture/` rappresenta quindi la baseline architetturale corrente da cui ogni nuova milestone parte. Tutti gli assunti iniziali della milestone, le condizioni ereditate dal sistema corrente e i comportamenti che la milestone dichiara di non modificare devono essere verificabili e coerenti con quanto documentato in `docs/architecture/`.

Questa verifica è un gate obbligatorio del design. Se `docs/milestones/<Mx>/` assume come punto di partenza una proprietà, una semantica, una struttura o un comportamento che non è verificabile in `docs/architecture/`, oppure che risulta in contraddizione con essa, il design del punto interessato deve fermarsi. Prima di procedere deve essere chiarito esplicitamente se:

- `docs/architecture/` è incompleta o non allineata allo stato corrente realmente consolidato;
- l'assunto iniziale della milestone è errato;
- la milestone sta in realtà introducendo una modifica architetturale che deve essere dichiarata e progettata come parte del proprio TO-BE.

La discrepanza deve essere risolta documentalmente prima di continuare il design o trasformare quell'assunto in codice. Non è ammesso scegliere implicitamente la versione più conveniente, affidarsi alla memoria, al codice esistente o alla Git history come sostituti dell'autorità documentale corrente.

Una milestone può e normalmente deve divergere da `docs/architecture/` nei punti che intende evolvere: tale divergenza non è un conflitto quando è **esplicitamente identificata come modifica TO-BE**, deriva dal `contract.md` della milestone ed è consolidata nella relativa documentazione architetturale. Una differenza non dichiarata o non tracciabile è invece drift documentale e deve essere trattata come un problema da risolvere.

In sintesi:

```text
assunto ereditato / comportamento invariato
    -> deve essere verificabile in docs/architecture/

modifica introdotta da Mx
    -> deve essere esplicita in docs/milestones/<Mx>/
       e tracciabile dal contract al design

punto di partenza non verificabile o contraddittorio
    -> STOP del design interessato
    -> analisi della discrepanza
    -> riallineamento / correzione / esplicitazione della modifica
    -> solo dopo si riprende
```

Al termine della milestone, il nuovo stato architetturale risultante dalle modifiche approvate viene consolidato e armonizzato in `docs/architecture/`, che diventa così la nuova baseline AS-IS per i cicli successivi.

Il materiale storico eventualmente necessario è sempre recuperabile dalla Git history e dalle fasi di milestone o fix precedenti, non costituisce autorità per il design o l'implementazione corrente; eventuali conflitti in tal senso devono essere risolti in modo esplicito. Directory o file storici rimossi dal working tree non devono essere ripristinati come baseline implicita.

I documenti normativi relativi alla specifica milestone sono così organizzati:

```text
docs/milestones/<Mx>/
├── wip/
├── contract.md
├── steps.md
├── status.md
└── architecture/
```

#### `wip/`

Contiene appunti, analisi, alternative, note e documenti temporanei.

Il suo contenuto non è normativo finché non viene consolidato nei documenti ufficiali della milestone.

#### `contract.md`

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

Lo sviluppo non può iniziare finché la documentazione architetturale necessaria alla milestone non è stata finalizzata e congelata.

#### `steps.md`

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

#### `status.md`

Contiene lo stato operativo corrente della milestone.

Deve permettere di determinare rapidamente:

- stato generale della milestone;
- step completati;
- step corrente;
- eventuali blocchi o problemi noti.

Non deve duplicare il contenuto di `contract.md`, `steps.md` o della documentazione architetturale.

### Ordine di definizione di una milestone

Ogni milestone segue il seguente ordine vincolante:

1. definizione e finalizzazione di `contract.md`;
2. definizione e finalizzazione dei documenti in `architecture/`;
3. definizione e finalizzazione di `steps.md`;
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

### Freeze del perimetro

Lo sviluppo effettivo di una milestone non parte finché il suo perimetro non è congelato.

Dopo il freeze, il perimetro non deve essere ampliato durante l'implementazione.

Sono ammesse modifiche soltanto quando, durante lo sviluppo, emergono casi non previsti che devono necessariamente essere gestiti per garantire la correttezza semantica o funzionale di quanto già incluso nella milestone.

Nuove capability, miglioramenti opportunistici o funzionalità non necessarie alla correttezza del perimetro congelato devono essere rinviati a milestone successive.

Il freeze viene gestito pragmaticamente tramite Git e accordo esplicito sullo stato dei documenti, senza introdurre in questa fase workflow formali aggiuntivi di governance.

### Finding durante implementazione e review

Il freeze del design vincola anche le fasi di implementazione e review. Un problema emerso durante lo sviluppo, nei test o nella revisione non autorizza mai l'implementatore a reinterpretare implicitamente il design, modificare una semantica congelata o indebolire una verifica per ottenere un risultato funzionante.

Ogni finding deve essere prima classificato distinguendo almeno tra:

```text
implementation defect
    = il codice non realizza correttamente una semantica già definita in modo
      univoco dalle authority congelate

architecture defect / missing decision
    = le authority congelate sono contraddittorie, incomplete, non allineate
      oppure non permettono di determinare un comportamento univoco
```

Nel caso di **implementation defect**, il design rimane valido. Si corregge l'implementazione nel rispetto delle authority esistenti e, quando il difetto è riproducibile o riguarda un contratto rilevante, si aggiunge o rafforza una regression verification adeguata. Non si riapre l'architettura soltanto perché il codice contiene un bug.

Nel caso di **architecture defect / missing decision**, il comportamento interessato entra immediatamente in stato di **STOP**. Non è ammesso scegliere in codice una delle interpretazioni possibili, assumere che il test sia troppo restrittivo, usare il comportamento corrente dell'implementazione come nuova authority o proseguire sulla base della soluzione tecnicamente più conveniente.

La sequenza obbligatoria è:

```text
finding durante implementation / test / review
    -> classificazione come architecture defect o missing decision
    -> STOP del comportamento interessato
    -> identificazione dello scope di riapertura
    -> re-read delle authority documentali pertinenti
    -> decisione / correzione architetturale esplicita
    -> propagation nello stesso ciclo a tutti i documenti normativi impattati
    -> verifica di coerenza della baseline riallineata
    -> re-freeze esplicito del design interessato
    -> solo dopo ripresa dell'implementazione
```

La riapertura deve essere proporzionata al finding: non è necessario riaprire l'intera milestone quando il problema è circoscritto, ma devono essere riesaminate tutte le authority da cui la decisione dipende e tutti i documenti che ne rappresentano le conseguenze. Una correzione cross-cutting richiede quindi una propagation cross-cutting.

Il codice, i risultati dei test, i report dell'implementatore e la Git history possono fornire evidence utile a diagnosticare il problema, ma **non sostituiscono mai la decisione documentale** quando il finding riguarda una semantica o un meccanismo congelato.

In sintesi:

```text
semantica frozen chiara + codice errato
    -> implementation defect
    -> fix del codice + regression verification

semantica frozen contraddittoria / incompleta / non deterministica
    -> architecture defect / missing decision
    -> STOP
    -> reopen -> revalidate -> decide -> propagate -> re-freeze
    -> resume
```

### Acceptance criteria

Ogni milestone deve definire acceptance criteria espliciti e verificabili all'interno di `contract.md`.

Gli acceptance criteria devono descrivere proprietà osservabili del sistema e non formulazioni generiche.

Esempio non sufficiente:

> La gestione delle Relationship deve essere robusta.

Esempio appropriato:

> Nessuna operazione concorrente supportata può produrre una Relationship incompatibile con gli endpoint secondo le invarianti ratificate.

Gli acceptance criteria rappresentano la condizione di successo della milestone e costituiscono il riferimento finale rispetto al quale verificare il risultato dell'implementazione.

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

### Coerenza a fine step

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

### Principio generale

NETAUTO privilegia la correttezza semantica e la coerenza architetturale rispetto alla velocità di implementazione locale.

Le decisioni devono essere prese e documentate prima di essere trasformate in codice.

La documentazione deve permettere, per ogni comportamento importante, di rispondere in modo non ambiguo alle seguenti domande:

- quale proprietà del sistema stiamo cercando di garantire?
- dove è definita?
- quale operazione può minacciarla?
- quale meccanismo la preserva?
- quale step la implementa?
- quale verifica dimostra che il contratto è rispettato?

### Final acceptance gate della milestone

Il completamento di tutte le slice è una condizione necessaria, ma **non sufficiente**, per dichiarare conclusa una milestone.

Vale la distinzione:

```text
slice completion
    !=
milestone acceptance
```

Una milestone può entrare nel final acceptance gate soltanto quando tutte le slice previste da `steps.md` risultano `COMPLETED` dopo review. Prima della chiusura formale deve quindi essere eseguita una verification closure integrata dell'intero risultato rispetto al `contract.md` e alle authority congelate della milestone.

La sequenza vincolante è:

```text
tutte le slice COMPLETED
    -> final acceptance gate
    -> verifica integrata contro contract.md e architecture frozen
    -> tutti gli acceptance criteria applicabili PASS
    -> reviewer approval
    -> consolidamento del nuovo AS-IS in docs/architecture/
    -> status milestone = DELIVERED
    -> merge umano del branch del ciclo
```

Il final acceptance gate deve verificare, in misura proporzionata al perimetro e al rischio della milestone, almeno:

- chiusura esplicita di tutti gli acceptance criteria definiti in `contract.md`;
- regressione integrata del repository, non soltanto test isolati per slice;
- coerenza finale tra domain model, application contract, persistence, schema/constraint, concurrency semantics, API, failure semantics e verifiche, per quanto applicabili;
- migration/schema closure quando la milestone modifica la persistenza;
- traceability sufficiente dal contract e dalle invarianti fino alle verifiche che ne dimostrano il rispetto;
- static analysis, reproducibility/build e altri quality gate ratificati dal progetto quando applicabili;
- assenza di architecture/documentation drift noto o di finding aperti incompatibili con la consegna;
- eventuali deliverable operativi richiesti espressamente dalla milestone.

La forma concreta dell'evidence non è prescritta in modo uniforme per tutte le milestone. Il principio obbligatorio è che la verification closure sia **integrata, verificabile e durevole**, con un livello di rigore adeguato alla complessità e ai rischi del relativo contract. Una milestone semplice può richiedere un acceptance step contenuto; una milestone con forti requisiti di persistenza, concorrenza, compatibilità o API può richiedere registri di traceability, matrici o evidence più estese.

Quando utile, l'evidence finale può essere raccolta in un documento come `acceptance.md`; la presenza di tale file non è di per sé obbligatoria salvo che sia prevista dal contract o dagli step. Ciò che è obbligatorio è che il reviewer possa determinare in modo non ambiguo **quale verifica dimostra ciascun criterio di accettazione rilevante** e che gli esiti dichiarati siano supportati dal repository e dai risultati effettivamente revisionati.

Il final acceptance gate è reviewer-owned: l'implementatore può preparare l'acceptance candidate ed eseguire le verifiche richieste, ma la milestone non può essere marcata `DELIVERED` prima dell'approvazione finale del reviewer.

### Chiusura formale della milestone

La chiusura formale della milestone deve distinguere nettamente tra **record storico del ciclo** e **documentazione architetturale corrente del sistema**.

`docs/milestones/<Mx>/` rimane il record completo e permanente della milestone Mx: documenta cosa si voleva ottenere, come è stato progettato il cambiamento, come è stato decomposto e verificato e quale stato operativo ha raggiunto il ciclo. La chiusura della milestone non comporta quindi lo spostamento, la fusione o la cancellazione dei suoi documenti per trasferirli in `docs/architecture/`.

In particolare, restano sotto `docs/milestones/<Mx>/` come record del ciclo:

```text
contract.md
steps.md
status.md
acceptance.md, quando presente
architecture/
```

L'eventuale materiale `wip/` segue la specifica disciplina prevista per il materiale temporaneo del ciclo, ma non diventa automaticamente architettura corrente.

`docs/architecture/` ha una responsabilità diversa: deve descrivere esclusivamente l'**AS-IS architetturale autorevole risultante dopo la milestone**. A chiusura di Mx si devono quindi derivare dalle decisioni approvate della milestone soltanto le informazioni necessarie a descrivere correttamente il sistema ormai consegnato, integrandole e armonizzandole con la baseline AS-IS precedente.

Il consolidamento non è un copy/paste dei documenti della milestone. Deve produrre una documentazione corrente coerente e autosufficiente, dalla quale sia possibile comprendere l'architettura del sistema senza dover ricostruire la sequenza storica M1, M2, ... Mn.

Nel nuovo AS-IS devono essere rimossi o riformulati i riferimenti che hanno senso soltanto nel contesto temporale della milestone, per esempio formulazioni come:

```text
target della milestone
durante Mx
da implementare
candidate
stato futuro
```

quando tali formulazioni non descrivono più il sistema consegnato.

Devono invece essere preservati nei documenti di milestone tutti gli elementi necessari a ricostruire **perché** e **attraverso quale ciclo** una determinata decisione è stata introdotta. La Git history e i documenti di milestone costituiscono quindi la memoria storica dell'evoluzione; `docs/architecture/` costituisce la fotografia autorevole dello stato corrente.

La relazione finale è:

```text
docs/milestones/<Mx>/
    = memoria normativa e storica del ciclo Mx

docs/architecture/
    = AS-IS architetturale corrente dopo Mx
```

La chiusura formale della milestone prevede quindi 3 azioni distinte che devono essere **SEMPRE** svolte:

1. consolidare in `docs/architecture/` il nuovo AS-IS risultante dalla milestone, armonizzando le decisioni architetturali approvate con la baseline precedente senza copiare indiscriminatamente la documentazione del ciclo;
2. aggiornare `docs/milestones/<Mx>/status.md` in modo che riporti chiaramente che lo stato della milestone è `DELIVERED`;
3. eseguire il merge del branch di milestone su master; questa attività non viene **MAI** fatta dall'agente ma è a carico dell'essere umano.


## Funzionamento di un ciclo di fix (F)

Un ciclo di fix corregge difetti della baseline già consegnata. Non introduce nuove capability, non amplia intenzionalmente il comportamento del prodotto e non modifica intenzionalmente il public API contract. Se l'analisi dimostra che la correzione richiede una nuova capability, una breaking change o una nuova semantica di prodotto, il lavoro non appartiene più a un ciclo di fix e deve essere pianificato in una milestone.

Ogni ciclo `Fx-y` parte dall'AS-IS autorevole corrente in `docs/architecture/`. La documentazione del fix deve poter identificare con precisione quale comportamento consegnato è difettoso, quale authority viene violata e quale comportamento avrebbe già dovuto essere garantito.

### Struttura documentale del fix

La documentazione di un ciclo di fix risiede sotto:

```text
docs/fixes/<Fx-y>/
├── wip/
├── defects.md
├── steps.md
├── status.md
└── architecture/
```

`architecture/` è utilizzata quando almeno un defect richiede una correzione o una chiarificazione architetturale; può rimanere minimale quando tutti i defect sono puramente implementativi e l'AS-IS esistente è già univoco e corretto.

`wip/` segue la stessa disciplina degli execution aid delle milestone: contiene soltanto materiale operativo ancora attivo; prompt conclusi o superseded rimangono recuperabili dalla Git history e vengono rimossi dal working tree.

### `defects.md`

`defects.md` è il documento che definisce il perimetro correttivo del ciclo e svolge, per un fix, il ruolo di ingresso che `contract.md` svolge per una milestone.

Ogni defect deve avere un identificativo stabile e univoco nel ciclo, per esempio:

```text
F1-1-DEF-001
F1-1-DEF-002
F2-1-DEF-001
```

Per ogni defect devono essere documentati almeno:

- **Observed defect** — il comportamento osservato e perché costituisce un difetto;
- **Reproduction evidence** — una prova concreta, ripetibile e verificabile che dimostri il problema sulla baseline difettosa;
- **Violated authority** — la regola, invariante, contract, API guarantee, persistence guarantee o altra authority già consegnata che il comportamento viola;
- **Analysis** — la classificazione e la causa del problema per quanto necessarie a progettare la correzione;
- **Correction design** — il comportamento corretto atteso e, quando necessario, le decisioni architetturali o tecniche che lo garantiscono;
- **Regression evidence** — la verifica permanente o durevole che deve dimostrare che il defect non è più presente dopo il fix.

La descrizione può evolvere durante la fase di analisi: inizialmente un defect può contenere soltanto identità, descrizione e prova di riproducibilità; prima del freeze devono però risultare chiari authority violata, classificazione e correction design.

### Reproduction-first

Nessun defect può essere considerato pronto per l'implementazione finché il problema non è stato riprodotto in modo sufficientemente deterministico e verificabile.

La prova di riproducibilità deve fallire o dimostrare il comportamento errato sulla baseline difettosa. Quando tecnicamente appropriato, la stessa evidence deve essere trasformata nella regression verification permanente che passerà dopo la correzione.

La reproduction evidence non deve essere necessariamente fin dall'inizio il test definitivo: defect complessi possono richiedere harness, diagnostica o una procedura controllata. Deve però essere abbastanza concreta da distinguere un difetto reale da un'ipotesi o da un comportamento soltanto sospetto.

### Classificazione del defect

L'analisi deve distinguere almeno:

```text
implementation defect
    = docs/architecture e le altre authority consegnate definiscono già
      correttamente e univocamente il comportamento atteso;
      è l'implementazione a non rispettarlo

architecture defect / missing decision
    = la baseline documentale consegnata è contraddittoria, incompleta,
      errata o non permette di determinare un comportamento corretto univoco
```

Per un **implementation defect** il fix non deve reinventare il design: la correzione deve riportare il codice all'AS-IS già autorevole e aggiungere o rafforzare la regression evidence necessaria.

Per un **architecture defect / missing decision** il comportamento interessato entra in STOP fino a quando la correzione architetturale non è stata progettata nel ciclo di fix. Le authority AS-IS coinvolte devono essere rilette, la decisione deve essere esplicita, le conseguenze devono essere propagate nei documenti del fix e il correction design deve essere congelato prima di implementare.

Il codice e la Git history possono aiutare la diagnosi, ma non diventano authority sostitutive.

### Freeze del ciclo di fix

`defects.md` deve raggiungere uno stato esplicitamente frozen prima dell'implementazione. Il freeze chiude il perimetro del ciclo: il ciclo corregge tutti e soli i defect presenti nel documento congelato, salvo dipendenze strettamente necessarie a correggerli correttamente.

La sequenza prima del freeze è:

```text
raccolta defect
    -> reproduction di ogni defect
    -> identificazione delle authority violate
    -> analysis e classificazione
    -> correction design
    -> propagation documentale necessaria
    -> freeze di defects.md e dell'eventuale architecture/ del fix
```

Un nuovo defect scoperto dopo il freeze non viene aggiunto automaticamente al ciclo corrente. Normalmente viene registrato per un ciclo successivo, ad esempio `F1-2` dopo `F1-1`.

Se un nuovo finding è inseparabile dalla correzione corretta di un defect già frozen, il perimetro interessato deve essere riaperto esplicitamente, il finding deve essere documentato e propagato, e `defects.md` deve essere nuovamente congelato prima di riprendere l'implementazione. Il freeze non deve essere aggirato facendo crescere implicitamente il bug train.

### `steps.md`, `status.md` e slice del fix

Dopo il freeze dei defect viene definito e congelato `steps.md`, decomponendo il ciclo in slice verticali e verificabili. `status.md` mantiene lo stato operativo corrente con la stessa separazione fra authority normativa e avanzamento utilizzata nelle milestone.

Le slice del fix usano gli stessi identificativi locali zero-padded:

```text
S01
S02
...
Snn
```

La forma completa include il ciclo di fix:

```text
F1-1-S01
F1-1-S02
F2-1-S01
```

Nei prompt, commit, report e riferimenti cross-document deve essere preferita la forma completa `Fx-y-Snn`.

Ogni slice deve indicare chiaramente:

- quali defect frozen corregge o fa avanzare;
- quali authority e componenti sono coinvolti;
- quale correction design realizza;
- quali regression verification devono passare;
- quali verifiche integrate sono richieste;
- quali condizioni consentono al reviewer di marcarla `COMPLETED`.

### Implementazione e review del fix

Dopo il freeze, il ciclo di fix segue la stessa disciplina di implementazione e review delle milestone:

```text
prompt della slice
    -> implementation candidate
    -> push del delta
    -> report dell'implementatore
    -> review del delta reale
    -> eventuale review-fix nella stessa slice
    -> reviewer approval
    -> slice COMPLETED
```

Il report dell'implementatore non costituisce completion evidence autonoma e gli stati `COMPLETED`, `ACCEPTED` e `DELIVERED` restano reviewer-owned.

Ogni slice deve lasciare il repository in stato coerente e deve dimostrare, tramite le regression evidence previste, che i defect interessati non sono stati soltanto mascherati ma corretti secondo le authority applicabili.

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

L'evidence finale deve essere verificabile e durevole in misura proporzionata al rischio del ciclo. Come per le milestone, l'implementatore può preparare il candidate e i risultati, ma l'approvazione del final regression gate è reviewer-owned.

### Chiusura del ciclo di fix

Dopo l'approvazione del final regression gate:

1. le eventuali correzioni architetturali introdotte dal fix vengono consolidate e armonizzate in `docs/architecture/`, che torna a rappresentare l'AS-IS autorevole corretto;
2. `docs/fixes/<Fx-y>/` rimane come record storico del ciclo, con `defects.md`, `steps.md`, `status.md` e l'eventuale `architecture/`;
3. `status.md` viene aggiornato a `DELIVERED` dal reviewer;
4. il merge del branch del ciclo viene eseguito dall'essere umano e **MAI** dall'agente.

Un ciclo di fix terminato deve quindi lasciare sia il software sia `docs/architecture/` coerenti con il comportamento corretto già dovuto, senza trasformare il fix in un canale implicito di evoluzione funzionale.