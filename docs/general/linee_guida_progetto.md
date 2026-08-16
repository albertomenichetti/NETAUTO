# Linee guida di progetto

**Status:** CURRENT — autorità generale per la governance di milestone, fix e documentazione di progetto.

## Scopo e tipi di ciclo

Questo documento definisce le regole generali adottate per l'evoluzione di NETAUTO.

Le modifiche al software — codice applicativo, schema, migration, dipendenze o comportamento runtime — avvengono esclusivamente all'interno di uno dei seguenti cicli:

- **milestone**, identificata da `M`, per evoluzione funzionale o architetturale pianificata;
- **fix**, identificato da `F`, per correggere difetti della baseline consegnata senza introdurre nuove capability o modifiche intenzionali del public contract.

Le milestone usano `M1`, `M2`, ... `Mn`.

I fix usano `F1-1`, `F1-2`, `F2-1`, ... `Fn-m`: `Fx-y` indica il fix `y` eseguito dopo `Mx` e prima di `Mx+1`.

Ogni ciclo opera su un branch dedicato. Il branch di una milestone deve essere dichiarato nel README root e nello `status.md` del ciclo; per i fix il branch coincide normalmente con l'identificativo `Fx-y`. Il merge su `master` è un'attività umana e non viene mai eseguito dal coding agent.

### Manutenzione documentale fuori da un ciclo software

In assenza di un ciclo M/F non è possibile modificare il software.

È ammessa soltanto manutenzione documentale esplicitamente autorizzata da un essere umano e con scope delimitato. Può riguardare:

- README e navigazione del repository;
- `AGENTS.md` e governance generale;
- riferimenti rotti, wording temporale o drift editoriale;
- chiarimenti lossless dell'AS-IS già consegnato.

Questa manutenzione non può cambiare il significato del sistema, il public contract, le garanzie di persistenza/concorrenza o la technology baseline. Se una correzione modifica il comportamento dovuto, il lavoro deve essere ricondotto a una milestone o a un fix.

## Ruoli documentali

### Authority documentale

Il codice non costituisce **mai** una fonte autonoma di decisioni architetturali.

Le decisioni normative correnti derivano:

- da `docs/architecture/` per lo stato già consegnato;
- dai documenti frozen del ciclo attivo per il delta TO-BE o correttivo;
- da `docs/general/technology_baseline.md` per le tecnologie project-wide ratificate.

Codice, test, Git history, chat, report e diagnostica sono evidence o strumenti di navigazione, non authority sostitutive.

Non è ammesso risolvere una contraddizione scegliendo implicitamente il documento più recente, quello letto per ultimo, il comportamento corrente del codice o la soluzione tecnicamente più conveniente.

### AS-IS, TO-BE e record storico

```text
docs/architecture/
    = AS-IS architetturale autorevole del sistema consegnato

docs/milestones/<Mx>/
    = TO-BE normativo della milestone mentre è attiva
      + record storico permanente dopo la consegna

docs/fixes/<Fx-y>/
    = perimetro e correction design del fix mentre è attivo
      + record storico permanente dopo la consegna
```

Ogni nuovo ciclo parte dall'AS-IS in `docs/architecture/`.

Tutti gli assunti iniziali e i comportamenti dichiarati invariati devono essere verificabili e coerenti con quell'AS-IS. Se un assunto non è verificabile o lo contraddice, il punto interessato entra in **STOP** finché non viene chiarito se:

- l'AS-IS è incompleta o non allineata;
- l'assunto del ciclo è errato;
- il ciclo sta introducendo una modifica che deve essere esplicitamente progettata.

Una milestone può divergere dall'AS-IS solo tramite una modifica TO-BE esplicita, derivata dal `contract.md` e congelata nell'architecture set. Una differenza non dichiarata è drift.

Un fix corregge comportamento già dovuto e non può diventare un canale implicito per nuova capability, breaking change o nuova semantica di prodotto.

### README root

Il README root è la proiezione operativa minimale del repository, non una semantic authority.

Deve permettere di identificare senza ambiguità:

```text
active cycle, oppure nessun ciclo attivo
tipo del ciclo
repository documentale del ciclo
branch del ciclo
cicli già DELIVERED / MERGED
```

Quando il README indica `M2`, il lettore deve proseguire in `docs/milestones/M2/`; quando indica `F1-1`, deve proseguire in `docs/fixes/F1-1/`.

Il README non duplica fase dettagliata, slice corrente, blocker o task: tali informazioni appartengono a `status.md`, `steps.md` e agli eventuali execution aid del ciclo.

Il README viene aggiornato quando un ciclo viene aperto, cambia branch canonico, viene consegnato o viene mergiato. Se README, branch e `status.md` non concordano, il lavoro entra in STOP fino al riallineamento del repository.

## Regole comuni ai cicli

### Naming delle slice

Ogni step implementativo è una **slice**.

Identificativo locale:

```text
S01
S02
...
Snn
```

Identificativo completo:

```text
M2-S01
F1-1-S03
```

`S00` è ammesso soltanto quando `steps.md` lo riserva esplicitamente a bootstrap/foundation del ciclo; le normali slice successive partono da `S01`.

Nei documenti interni allo stesso ciclo è ammessa la forma locale `Snn` quando il contesto è inequivocabile. Nei prompt, commit, report e riferimenti cross-document si preferisce sempre la forma completa.

### Execution aid e `wip/`

Le directory `wip/` contengono prompt, review-fix, appunti e materiale temporaneo.

```text
wip/
    = execution aid attivi e non normativi

Git history
    = memoria degli aid eseguiti o superseded
```

Quando un prompt viene sostituito o la relativa slice viene accettata, l'aid concluso viene rimosso dal working tree. Non viene conservato in `wip/` soltanto come memoria storica.

### Implementer e reviewer

```text
implementer / coding agent
    = produce un candidate e il report di esecuzione

reviewer
    = verifica il delta reale e decide se accettarlo
```

Il report dell'implementer è un ausilio, non completion evidence autonoma.

Sono reviewer-owned almeno:

```text
slice -> COMPLETED
cycle -> DELIVERED
review outcome -> ACCEPTED / REVIEW CHANGES REQUIRED
```

Un review-fix resta nella stessa slice. La slice non viene chiusa e non se ne crea una nuova soltanto per correggere finding della review corrente.

### Re-validation delle authority

Ogni re-validation deve essere:

- **dependency-driven**;
- **repository-based**;
- proporzionata allo scope;
- bloccante in presenza di drift, contradiction o reopen pendente.

Pattern generale:

```text
identify scope and dependencies
    -> re-read authoritative documents
    -> verify current and mutual coherence
    -> STOP on drift / contradiction / stale-open marker
    -> resolve and propagate
    -> restore frozen state when required
    -> resume
```

Si applica:

- prima di un design point dipendente da decisioni già consolidate;
- prima di ogni slice implementativa;
- dopo un finding che mette in discussione un design frozen.

Rappresentazioni differenti non devono essere confuse:

```text
domain accepted input
!= canonical domain state
!= canonical persistence representation
!= public API wire representation
```

### Finding: implementation defect vs architecture defect

```text
implementation defect
    = le authority definiscono già il comportamento in modo univoco;
      il codice non lo rispetta

architecture defect / missing decision
    = le authority sono contraddittorie, incomplete, errate
      o non determinano un comportamento univoco
```

Per un implementation defect si preserva il design, si corregge il codice e si aggiunge o rafforza la regression evidence appropriata.

Per un architecture defect / missing decision:

```text
finding
    -> STOP del comportamento interessato
    -> scope di reopen
    -> re-read delle authority
    -> decisione esplicita
    -> propagation cross-document
    -> consistency check
    -> re-freeze
    -> resume
```

Non è ammesso scegliere una semantica in codice, indebolire un test, adattare i documenti frozen all'implementazione comoda o usare il codice corrente come nuova authority.

### Invariante di completion della slice

Ogni slice deve lasciare il repository coerente e verificabile fra tutti i livelli interessati:

- domain model;
- application contract;
- persistence e schema;
- concurrency;
- API e failure semantics;
- test/verification;
- documentazione del ciclo.

Quando tecnicamente possibile, le slice devono essere verticali e completare un insieme limitato di invarianti, contratti o defect.

## Principi di design semantico

### Invarianti e traceability

Le invarianti descrivono le proprietà che devono restare vere in ogni stato valido. Quando utile vengono identificate con codici stabili, ad esempio `DT-INV-001`, `OT-INV-001`, `OBJ-INV-001`, `REL-INV-001`.

Traceability desiderata:

```text
acceptance criterion / defect requirement
    -> invariant / required property
    -> architecture decision
    -> implementation slice
    -> implementation mechanism
    -> verification
```

`steps.md` deve permettere di risalire dalle attività alle authority che realizzano.

### Contratti tecnici

Il design parte dalla semantica, non dal meccanismo:

```text
Invariant
    -> Threat / race / invalid state
    -> Required guarantee
    -> Chosen mechanism
```

Constraint, FK, UNIQUE, CAS, row lock, advisory gate e isolation level sono strumenti per garantire un'invariante; non definiscono da soli la semantica.

### Architettura vs decomposizione implementativa

Il design deve chiudere tutte le scelte necessarie a determinare semantica, invarianti, failure semantics, boundary, garanzie di persistenza/concorrenza e verification contract.

Non deve prescrivere micro-dettagli locali che non alterano tali contratti. Struttura dei moduli, helper, fixture e naming interno restano libertà dell'implementer quando le authority li lasciano aperti.

```text
semantic / correctness choice
    -> design prima del coding

local implementation decomposition
    -> scelta implementativa, se preserva il design frozen
```

## Ciclo di milestone

### Separazione design / implementation

Durante il design vengono definiti, quando applicabili:

- domain model e invarianti;
- application e persistence contract;
- UoW e transaction boundary;
- concurrency contract;
- API/failure contract;
- acceptance criteria;
- verification contract;
- decomposizione implementativa.

Durante questa fase non viene sviluppato codice applicativo. L'implementation inizia solo dopo il completamento dei design gate.

### Struttura documentale

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

Definisce obiettivi, scope, non-obiettivi, capability coinvolte, risultati attesi e acceptance criteria osservabili. Non contiene decomposizione implementativa.

#### `architecture/`

Definisce il TO-BE semantico e tecnico necessario a soddisfare il contract.

Ogni milestone deve avere `architecture/README.md`, che controlla l'architecture set senza duplicare i documenti owning. Deve includere:

- purpose e authority boundary;
- set status (`DESIGN IN PROGRESS`, `FROZEN`, `PARTIALLY REOPENED` o equivalente univoco);
- normative document map;
- coverage/ownership map;
- open design points;
- freeze/reopen scope.

La milestone entra in implementation solo con:

```text
ARCHITECTURE SET = FROZEN
```

Questo significa che il set è completo rispetto al contract, ogni area ha un owner, non restano decisioni semantiche aperte, le conseguenze cross-cutting sono propagate e il corpus ha superato un consistency sweep.

#### `steps.md`

Contiene slice, obiettivo, authority/invarianti, componenti coinvolti, verifiche richieste e completion condition.

Deve indicare esplicitamente come viene rappresentato il final acceptance gate:

- come final slice dedicata; oppure
- come gate esterno successivo alle slice implementative.

Il modello scelto non deve essere ambiguo. Se il gate è una final slice, il suo pre-flight richiede tutte le slice implementative precedenti `COMPLETED`; la final slice diventa `COMPLETED` soltanto dopo l'approvazione del gate.

#### `status.md`

Possiede lo stato operativo dettagliato: fase corrente, slice corrente, slice completate, blocker e finding aperti. Possiede anche il vocabolario concreto degli stati usato dal ciclo; README e agent non devono inventare sinonimi.

#### `acceptance.md`

Quando presente, conserva evidence durevole del final gate. Non sostituisce contract o architecture.

### Ordine vincolante

```text
contract FINAL / FROZEN
    -> architecture set FROZEN
    -> steps FINAL / FROZEN
    -> status initialized
    -> implementation
```

Ogni fase deriva semanticamente dalla precedente.

### Propagation durante il design

Quando un design point produce un finding retroattivo, il lavoro viene interrotto e la decisione viene propagata immediatamente a tutti i documenti impattati. Non si rinvia consapevolmente la propagation al consistency sweep finale.

Un consistency sweep periodico resta obbligatorio per individuare drift non noto, stale-open marker e TODO già chiusi.

### Freeze del perimetro

Dopo il freeze il perimetro non viene ampliato durante l'implementation. Sono ammesse soltanto correzioni necessarie alla correttezza di quanto già incluso. Nuove capability o miglioramenti opportunistici vengono rinviati.

### Pre-flight implementativo

Prima di ogni `Mx-Snn` si verificano almeno:

```text
contract ancora FINAL / FROZEN
architecture set ancora FROZEN
steps ancora frozen
status che autorizza la slice
owning authority e invarianti della slice
verification richiesta
assenza di contradiction o reopen pendenti
```

### Final acceptance gate

Il completamento delle slice implementative è necessario ma non sufficiente alla consegna.

Il gate finale verifica, in modo proporzionato al rischio:

- tutti gli acceptance criteria;
- regressione integrata;
- coerenza domain/application/persistence/schema/concurrency/API/failure/verification;
- migration/schema closure quando applicabile;
- traceability;
- build, static analysis e reproducibility gate ratificati;
- assenza di drift o finding aperti incompatibili;
- deliverable operativi previsti dal contract.

L'evidence deve essere verificabile e durevole. Il final acceptance gate è reviewer-owned: l'implementer prepara il candidate ma non dichiara autonomamente `DELIVERED`.

## Ciclo di fix

### Scopo e struttura

Un fix corregge difetti della baseline consegnata e non introduce nuove capability, nuova semantica di prodotto o modifica intenzionale del public contract.

```text
docs/fixes/<Fx-y>/
├── wip/
├── defects.md
├── architecture/          # opzionale
│   ├── README.md          # obbligatorio se architecture/ esiste
│   └── ...
├── steps.md
└── status.md
```

`architecture/` è presente soltanto quando serve correction design architetturale.

### `defects.md`

È il perimetro correttivo del fix. Ogni defect ha ID stabile, ad esempio `F1-1-DEF-001`, e contiene almeno:

- observed defect;
- reproduction evidence;
- violated authority;
- analysis/classification;
- correction design;
- regression evidence.

### Reproduction-first

Nessun defect è pronto per implementation finché non è riprodotto in modo sufficientemente deterministico e verificabile. Quando appropriato, la reproduction evidence diventa regression permanente.

### Freeze

Prima dell'implementation:

```text
reproduce every defect
    -> identify violated authority
    -> classify and design correction
    -> propagate documentation
    -> defects.md FROZEN
    -> correction architecture set FROZEN, when present
    -> steps.md FROZEN
```

Un defect scoperto dopo il freeze va normalmente in un fix successivo. Se è inseparabile dalla correzione di un defect frozen, il perimetro viene riaperto esplicitamente e nuovamente congelato.

### `steps.md` e `status.md`

Ogni slice indica defect coperti, authority, correction design, regression evidence, verification integrate e completion condition.

Come per le milestone, `steps.md` dichiara se il final regression gate è una final slice o un gate esterno. Se è una final slice, richiede tutte le slice correttive precedenti `COMPLETED`.

`status.md` possiede fase, slice, blocker e vocabolario operativo concreto.

### Pre-flight implementativo

Prima di ogni `Fx-y-Snn`:

```text
defects.md FROZEN
correction architecture FROZEN, quando presente
steps.md FROZEN
status che autorizza la slice
violated/current AS-IS authority identificate
regression evidence definite
nessun reopen pendente
```

### Final regression gate

Verifica almeno:

- tutti i defect frozen corretti;
- reproduction evidence trasformate o sostituite da regression equivalenti/più forti;
- regressione integrata verde;
- nessuna nuova capability o modifica intenzionale del public contract;
- coerenza con correction design;
- assenza di drift/finding aperti;
- quality gate applicabili.

L'approvazione è reviewer-owned.

## Chiusura formale dei cicli

La chiusura inizia soltanto dopo il final gate approvato.

### Consolidamento AS-IS

`docs/architecture/` descrive esclusivamente il sistema consegnato.

A fine milestone o fix vengono consolidate soltanto le decisioni necessarie a descrivere il nuovo AS-IS. Il consolidamento non è copy/paste: rimuove wording temporale (`target`, `candidate`, `durante Mx`, `da implementare`) e produce un corpus corrente autosufficiente.

Un fix puramente implementativo deve comunque verificare che l'AS-IS documentale resti corretto.

### Preservazione del record storico

I documenti del ciclo restano nella relativa directory e preservano perché, quando e attraverso quale ciclo una decisione è stata introdotta. Non vengono spostati o fusi in `docs/architecture/`.

### `DELIVERED` e merge

Dopo consolidamento e consistency check:

1. il reviewer marca il ciclo `DELIVERED` in `status.md`;
2. il README viene aggiornato per riflettere consegna e merge pendente;
3. l'essere umano esegue il merge su `master`;
4. il README viene aggiornato a `MERGED` e, se non esiste un nuovo ciclo, a `NO ACTIVE CYCLE`.

Il ciclo chiuso deve lasciare software, verification, documentazione storica e AS-IS mutuamente coerenti.
