# M1 — PostgreSQL Concurrency Test Matrix

**Status:** DRAFT — PGTEST-01..PGTEST-04 ratificati; canonical scenario contract, census, 19-predicate coverage mapping, deterministic harness contract e reusable execution recipes completi. La concurrency/test architecture M1 è considerata chiusa salvo finding retroattivi o gap emersi durante l'implementation design.

## 1. Scopo

Questo documento deriva i test di concorrenza PostgreSQL dalla catena normativa M1:

```text
semantic matrix cell / safety predicate
-> concurrency authority
-> PostgreSQL realization mechanism
-> real PostgreSQL concurrency test
```

La matrice dei test è sparse e scenario-based. Non viene materializzata una suite 1:1 delle 528 celle pairwise della semantic matrix.

---

## 2. PGTEST-01 — canonical concurrency-test contract

Ogni scenario normativo descrive, quando applicabile:

```text
Test ID
Operations
Concrete scope
Safety predicate(s)

Initial committed state

T1 phases
T2 phases
[optional T3 phases]

Deterministic coordination points

Expected blocking / non-blocking
Allowed committed outcomes
Forbidden outcomes

Final current-state assertions
Lifecycle-event assertions
Retry / convergence assertions

Authority being exercised
PostgreSQL mechanism being exercised

Semantic-matrix refs
Realization refs
```

### 2.1 Semantic assertions vs mechanism assertions

Ogni test distingue due categorie.

**Semantic outcome assertions** sono sempre normative: verificano che lo state committed e gli event set appartengano esclusivamente agli outcome ammessi dal dominio.

**Mechanism assertions** sono normative quando il mechanism è parte esplicita della realization. Esempi:

- row-lock rendezvous richiesto;
- FK/PK/UNIQUE arbitration;
- advisory-gate wait e fresh snapshot successivo;
- intentional non-blocking fra operation che devono restare non genericamente serializzate;
- intentional implementation over-serialization documentata.

Questa distinzione impedisce che un test funzionale continui a passare mentre un refactor introduce lock più forti, global lock nascosti o perde una proprietà di parallelismo M1.

### 2.2 Real PostgreSQL requirement

I concurrency test normativi usano PostgreSQL reale e almeno due connection/transaction indipendenti.

Mock repository, fake transaction, SQLite o simulazioni in-process non dimostrano:

```text
row-lock compatibility
FK arbitration
PK/UNIQUE arbitration
MVCC snapshot visibility
transaction-level advisory lock semantics
rollback/wait interactions
```

Possono esistere test unitari separati, ma non sostituiscono questi contract test.

### 2.3 Deterministic interleaving

Gli interleaving vengono costruiti tramite deterministic barrier/latch/test hook su phase semanticamente rilevanti, per esempio:

```text
owner lock acquired
advisory gate acquired
uncommitted reference inserted
complete closure inserted
metadata snapshot completed
```

`sleep()` non è una correctness coordination primitive. Timeout possono essere usati per osservare/assertare blocking, non come unico meccanismo per produrre l'ordine della race.

### 2.4 Persistence-level vs kernel-level tests

M1 distingue:

```text
Persistence concurrency contract tests
Kernel semantic concurrency tests
```

Persistence-level tests possono osservare direttamente statement ordering, lock wait, advisory gate, FK/PK/UNIQUE behavior, MVCC visibility e rollback.

Kernel-level tests invocano le semantic mutation e verificano domain outcome, current state, idempotenza, convergence e lifecycle event set senza dover conoscere necessariamente ogni SQL primitive.

Entrambi derivano dalla stessa traceability chain.

### 2.5 Canonical scenario families

```text
T-ROW
    row-state serialization / freshness

T-ARB
    PK/UNIQUE arbitration + semantic convergence

T-REF
    FK RESTRICT lifetime arbitration

T-GATE
    advisory predicate-set gates + fresh snapshot

T-SNAP
    coherent MVCC observation without writer serialization

T-ATOMIC
    aggregate/event all-or-nothing rollback

T-PAR
    intentional parallelism / intentional over-serialization
```

Una race può appartenere a più family se verifica predicate/mechanism composti.

### 2.6 Coverage rule

Ogni non-`I` scoped semantic rule deve essere coperta da almeno uno scenario concreto direttamente traceable oppure dichiarare esplicitamente quale scenario/family equivalente esercita la stessa authority/mechanism.

Non è richiesto un test per ogni cella materializzata delle 528 pairwise combination.

In aggiunta, ogni intentional implementation over-serialization e ogni importante intentional non-serialization della realization M1 possiede almeno un regression scenario.

### 2.7 Allowed outcome sets

I test verificano insiemi di outcome ammessi e stati vietati. Non impongono un winner arbitrario quando il semantic contract permette entrambi gli ordini seriali.

Quando il contract richiede invece una specifica arbitration/convergence property — per esempio single-owner PK, exact Relationship fact o same-ID delete idempotency — il test la verifica esplicitamente.

---

## 3. PGTEST-01 decisions

```text
P1.1  sparse scenario-based matrix, not 528 literal tests
P1.2  full predicate -> authority -> mechanism -> test traceability
P1.3  real PostgreSQL with independent connections/transactions
P1.4  deterministic barriers/hooks; no sleep-only coordination
P1.5  semantic assertions separated from mechanism assertions
P1.6  persistence-level and kernel-level concurrency suites
P1.7  canonical families T-ROW/T-ARB/T-REF/T-GATE/T-SNAP/T-ATOMIC/T-PAR
P1.8  every non-I semantic rule maps to a concrete/equivalent scenario
P1.9  important intentional over-serialization and non-serialization are regression-tested
P1.10 tests assert allowed outcome sets and forbidden states rather than arbitrary scheduling
```

---

## 4. PGTEST-02 — canonical scenario census

Il canonical census contiene:

```text
44 correctness scenarios
+ 7 T-PAR regression probes
= 51 canonical scenario IDs
```

Una variante `A/B/C` sotto lo stesso scenario ID è ammessa soltanto quando conserva la stessa concurrency authority, lo stesso PostgreSQL mechanism e la stessa deterministic orchestration, cambiando soltanto il concrete semantic case.

DTV e OTV non vengono duplicati quando il concurrency contract è realmente simmetrico. Una variante per dominio viene mantenuta soltanto se cambia la physical shape o l'authority exercised.

### 4.1 `T-ROW` — 17 scenari

```text
ROW-01  DT/OT CREATE_NEXT × CREATE_NEXT, same lineage
        VS — lineage owner; unique serial version allocation.

ROW-02  DT/OT CREATE_NEXT × DELETE_DRAFT(max)
        VS — version-set/source re-evaluation after waiter wake-up.

ROW-03  DT/OT REVISE × REVISE, same DRAFT generation
        DG — one winner, stale loser.

ROW-04  exact DRAFT terminal races
        A: REVISE × PUBLISH
        B: PUBLISH × DELETE_DRAFT
        DG + LS — exact-version owner and post-wait state recheck.

ROW-05  PUBLISH(vA) × PUBLISH(vB), same lineage, default NULL
        DV — first serial publisher becomes auto-default.

ROW-06  SET_DEFAULT(v) × DEPRECATE(v)
        DV + LS — never current default pointing to DEPRECATED.

ROW-07  explicit new binding × target DEPRECATE
        BA — target exact FOR SHARE vs lifecycle writer.

ROW-08  implicit binding default resolution
        A: binder × SET_DEFAULT
        B: binder × CLEAR_DEFAULT
        BA + DV — coherent default selection + exact admission.

ROW-09  OTV PUBLISH consumer × dependency DEPRECATE
        AM — active-edge activation/deprecation rendezvous.

ROW-10  active blocker removal × dependency DEPRECATE
        A: consumer DEPRECATE
        B: consumer DELETE_LINEAGE
        AM — removal-first success or conservative dependency failure.

ROW-11  OBJ.DATA_CHANGE × OBJ.DATA_CHANGE
        OS — no lost JSONB update; serial candidate derivation.

ROW-12  Object schema/current-state races
        A: DATA_CHANGE × SCHEMA_CHANGE
        B: SCHEMA_CHANGE × SCHEMA_CHANGE
        OS (+ BA on target) — waiter re-derives from committed current state.

ROW-13  ATTACH × SCHEMA_CHANGE(parent)
        PO — edge/schema serial composability.

ROW-14  DETACH × SCHEMA_CHANGE(parent)
        PO — removal may unblock migration.

ROW-15  SET_DESCRIPTION × SET_DESCRIPTION
        ML — atomic complete-value LWW.

ROW-16  REVISE × DELETE_LINEAGE, same aggregate
        AL — exact child owner vs aggregate cascade.

ROW-17  RD.RENAME × RD.DELETE, same Definition
        AL — same aggregate lifetime serialization.
```

### 4.2 `T-ARB` — 7 scenari

```text
ARB-01  model CREATE × CREATE, same qualified name
        NU — UNIQUE arbitration.

ARB-02  ATTACH(P1,C) × ATTACH(P2,C)
        SO — PK(child_object_id) final single-owner authority.
        Include persistence-level raw-PK test because the graph gate may
        otherwise mask the database arbitration.

ARB-03  identical ownership mutation
        A: ATTACH(P,S,C) × ATTACH(P,S,C)
        B: DETACH(P,S,C) × DETACH(P,S,C)
        OF — one real transition/event; other converges no-op.

ARB-04  ATTACH(P,S,C) × DETACH(P,S,C)
        OF — only serially explainable fact/event sequences.

ARB-05  equivalent REL.CREATE
        A: non-symmetric reciprocal selectors
        B: symmetric inverse assignment
        C: inheritance-overlap multi-view case
        RF — exact-view PK arbitration + convergence.

ARB-06  REL.DELETE(X) × REL.DELETE(X)
        RA — one deletion/event set; waiter no-op.

ARB-07  Relationship lifetime/convergence ABA
        A: DELETE X -> recreate Y -> late DELETE X
        B: CREATE loser collision; winner disappears before convergence read
        RF + RA — current-state restart and exact-ID safety.
```

### 4.3 `T-REF` — 6 scenari

```text
REF-01  model reference creation × target lineage delete
        variants include:
          OBJ.CREATE -> exact OTV
          OT.REVISE -> exact DTV
          RD.CREATE -> OT lineage
        RL — exercise exact/composite FK and stable-lineage FK arbitration.

REF-02  ATTACH × OBJ.DELETE
        A: parent deletion
        B: child deletion
        RL — ownership current reference vs Object lifetime.

REF-03  REL.CREATE × OBJ.DELETE(endpoint)
        RL — runtime endpoint FK arbitration.

REF-04  REL.CREATE × RD.DELETE
        RL — factual Relationship/Definition lifetime.

REF-05  reference removal × target delete
        A: DETACH × OBJ.DELETE
        B: REL.DELETE × OBJ.DELETE
        RL — removal-first may unblock; current blocker may fail conservatively.

REF-06  aggregate CASCADE × external RESTRICT
        RL — internal owned-state CASCADE must never bypass external current reference.
```

RL coverage must exercise at least one composite exact FK and one stable-lineage FK.

### 4.4 `T-GATE` — 6 scenari

```text
GATE-01 ownership opposite edge-add
        A->B × B->A
        OC — at most one can complete without a cycle.

GATE-02 ownership nontrivial graph
        A: longer-cycle candidate
        B: cycle check × concurrent DETACH removing blocking path
        OC — safe success or conservative rejection only.

GATE-03 ownership gate visibility
        A: waiter sees previous holder committed edge with fresh post-gate statement snapshot
        B: child ownership changes while waiter awaits gate; mandatory post-gate reread
        OC — fresh-snapshot discipline.

GATE-04 RD certified-set concurrent CREATE
        A: semantically equivalent
        B: non-equivalent but conflicting
        RC — one globally admissible candidate.

GATE-05 RD candidate mutation conflicts
        A: CREATE × RENAME
        B: RENAME(D1) × RENAME(D2)
        RC — global certified-set candidate serialization.

GATE-06 RD gate visibility/removal
        A: waiter fresh snapshot sees previous holder commit
        B: blocker DELETE concurrent with CREATE/RENAME
        RC — DELETE takes no gate; conservative failure permitted.
```

`GATE-03A` e `GATE-06A` devono fallire se gate acquisition e authoritative read vengono accidentalmente accorpati in uno statement con stale pre-wait snapshot.

### 4.5 `T-SNAP` — 4 scenari

```text
SNAP-01 RD.RENAME × real REL.CREATE/DELETE
        ES — entire event set old names OR new names; never half-renamed.

SNAP-02 OBJ.RENAME × real REL.CREATE/DELETE
        ES — endpoint display metadata from one committed observation.

SNAP-03 two independently renamed Relationship endpoints
        ES — only metadata combinations that existed in one statement snapshot;
             include occurred_at-before-later-observation variant.

SNAP-04 ownership structural event metadata
        child rename concurrent with ATTACH/DETACH
        REALIZE-15 clarification — no child lock solely for display metadata;
        event captures one committed child-name observation.
```

`SNAP-04` non introduce un nuovo safety predicate; protegge la lifecycle-display-metadata clarification del sweep.

### 4.6 `T-ATOMIC` — 4 scenari

```text
ATOMIC-01 OTV multi-row candidate mutation failure
          revise/publish cannot expose mixed header/property/component generation.

ATOMIC-02 REL.CREATE collision on a later closure row
          loser header + previously inserted rows + events all rollback.

ATOMIC-03 REL.DELETE forced rollback
          Relationship + complete closure remain current; no deletion event commits.

ATOMIC-04 state-transition/event atomicity variants
          A: intrinsic Object transition
          B: ownership edge transition
          C: RD complete Resolution-name mutation
          no current-state/event or aggregate-child partial commit.
```

Atomic tests coprono le differenti aggregate shapes, non ogni mutation singolarmente.

### 4.7 `T-PAR` — 7 normative realization regression probes

```text
PAR-01 REL.CREATE × OBJ.RENAME
       must not block solely because FK needs referenced Object identity.
       Protects REALIZE-15 FOR NO KEY UPDATE refinement.

PAR-02 REL.CREATE × RD.RENAME
       runtime factual mutation must not serialize solely on non-key Definition rename.

PAR-03 OBJ.RENAME(parent) × ATTACH(parent)
       intentional serialization on shared parent non-key owner.

PAR-04 unrelated real ATTACH × unrelated real ATTACH
       intentional global ownership-gate serialization.

PAR-05 unrelated REL.CREATE × unrelated REL.CREATE
       no global Relationship serialization.

PAR-06 DEPRECATE(v1) × DEPRECATE(v2), same lineage
       lineage FOR SHARE permits concurrency at lineage-lock level.

PAR-07 description/header topology
       A: SET_DESCRIPTION × SET_DEFAULT -> intentional header contention
       B: SET_DESCRIPTION × REVISE -> no artificial lineage-owner contention.
```

`T-PAR` è normative regression coverage della concurrency/performance architecture: verifica sia blocking intenzionale sia non-blocking intenzionale. Un implementation refactor che mantiene gli outcome funzionali ma rompe questi contract non è architecture-compatible.

---

## 5. Safety-predicate coverage map

```text
NU  -> ARB-01
VS  -> ROW-01, ROW-02
DG  -> ROW-03, ROW-04, ATOMIC-01
LS  -> ROW-04, ROW-06
DV  -> ROW-05, ROW-06, ROW-08
BA  -> ROW-07, ROW-08, ROW-12
AM  -> ROW-09, ROW-10
RL  -> REF-01..REF-06
AL  -> ROW-16, ROW-17
ML  -> ROW-15
OS  -> ROW-11, ROW-12, ATOMIC-04A
PO  -> ROW-13, ROW-14
OF  -> ARB-03, ARB-04, ATOMIC-04B
SO  -> ARB-02
OC  -> GATE-01..GATE-03, PAR-04
RC  -> GATE-04..GATE-06, ATOMIC-04C
RF  -> ARB-05, ARB-07, ATOMIC-02
RA  -> ARB-06, ARB-07, ATOMIC-03
ES  -> SNAP-01..SNAP-03, PAR-01, PAR-02
```

Tutti i 19 safety predicate risultano coperti prima dell'implementazione.

`NU` e `ML` hanno coverage più concentrata perché la relativa authority è volutamente semplice (`UNIQUE` e atomic row LWW); non viene duplicato un test senza differenza di mechanism.

---

## 6. PGTEST-02 decisions

```text
P2.1  44 correctness scenarios + 7 PAR probes = 51 canonical IDs.
P2.2  Variants share one ID only with same authority/mechanism/orchestration.
P2.3  DTV/OTV tests are not duplicated where concurrency contract is truly symmetric.
P2.4  RL coverage exercises both exact/composite and stable-lineage FK shapes.
P2.5  SO has raw persistence PK coverage because the graph gate may mask arbitration.
P2.6  Gate fresh-snapshot behavior has explicit mechanism tests.
P2.7  ATOMIC tests cover aggregate shapes rather than every operation.
P2.8  T-PAR is normative regression coverage for intended blocking and non-blocking.
P2.9  All 19 safety predicates are covered before implementation.
P2.10 Scenario IDs are stable source-of-truth identifiers; future scenarios append without renumbering existing IDs.
```

---

## 7. PGTEST-03 — deterministic PostgreSQL concurrency harness contract

### 7.1 Canonical harness roles

Ogni scenario usa connection PostgreSQL realmente indipendenti con i seguenti ruoli concettuali:

```text
CTL
    harness controller; orchestra worker/barrier/release,
    non è una semantic transaction.

OBS
    observer/introspection connection; osserva blocker/wait/lock/current state,
    non partecipa semanticamente alla race.

B
    optional blocker/control transaction usata per costruire
    deterministicamente uno specifico DB wait point.

T1 / T2 / [T3]
    semantic worker transactions.
```

Ogni worker registra `scenario_id`, role e `pg_backend_pid()`. Le sessioni di test usano un `application_name` riconoscibile, per esempio `netauto-pgtest:ROW-09:T1`, esclusivamente come diagnostica/test metadata.

### 7.2 External PostgreSQL blocker first

Tecnica primaria di orchestration:

```text
B acquires the database lock/gate needed by T1
-> T1 starts semantic operation and blocks at that real PostgreSQL boundary
-> OBS proves the blocker relation
-> T2 performs the competing operation
-> B commits/rolls back and releases
-> T1 wakes, re-reads and continues/fails according to the semantic contract
```

Questa tecnica è preferita a qualsiasi pause branch nel production kernel. Il test controlla l'interleaving tramite authority/mechanism reali, non tramite timing casuale.

### 7.3 Positive blocking assertion

La blocker relation canonica viene verificata primariamente tramite:

```text
pg_blocking_pids(worker_pid)
```

con expected blocker PID noto al harness.

`pg_stat_activity` e `pg_locks` sono supporto diagnostico/mechanism inspection, inclusi `state`, `wait_event_type`, `wait_event`, `granted` e `waitstart` dove applicabili. I test non ricostruiscono manualmente come authority il blocker graph tramite self-join fragile di `pg_locks`.

### 7.4 No tuple-lock representation dependency

I test non assumono che una row-lock wait debba apparire come una specifica `locktype='tuple'` row in `pg_locks`. PostgreSQL può rappresentare la wait anche tramite transaction-id machinery.

M1 non richiede l'estensione `pgrowlocks` per la suite normativa. Il contract testa chi blocca chi e quale semantic/physical authority viene esercitata, non una particolare rappresentazione interna del lock manager.

### 7.5 Intentional non-blocking proof

Il non-blocking architetturalmente rilevante non viene provato con una breve attesa temporale.

Regola:

> mentre la potentially conflicting transaction resta intenzionalmente open, il secondo worker deve raggiungere un successivo deterministic progress point che sarebbe impossibile se il meccanismo vietato lo stesse bloccando.

Esempio `PAR-01`: mantenere aperta una `OBJ.RENAME` dopo `FOR NO KEY UPDATE` e dimostrare che `REL.CREATE` raggiunge una phase successiva alla referential-key protection prima del rilascio della rename transaction.

### 7.6 Downstream blockers

Il harness può usare un blocker DB posto **dopo** una phase semanticamente rilevante per fermare la UoW senza introdurre application hook.

Esempio per snapshot/event ordering: una transaction B può detenere un table lock incompatibile con l'event INSERT; la Relationship UoW esegue prima il metadata snapshot e si blocca poi sull'event write. Durante il blocco può committare una metadata rename; al rilascio, l'event deve utilizzare il snapshot già catturato.

Questa tecnica è test-only e non cambia production persistence semantics.

### 7.7 Test-only persistence phase interceptor

Un test-only persistence proxy/interceptor è ammesso **solo come escape hatch** quando un deterministic interleaving non è costruibile ragionevolmente tramite PostgreSQL blocker/gate/constraint behavior.

Boundary:

```text
may:
    observe a named persistence phase
    signal a harness barrier
    wait for harness release
    record ordering

must not:
    change candidate data
    issue additional semantic SQL
    change isolation
    commit/rollback
    swallow/translate DB errors differently
    select a different production path
    sleep to force scheduling
```

Non si introducono `if TESTING` o pause hook nel domain/application kernel.

### 7.8 Test phase vocabulary

Il harness usa phase semantiche/test-level, non line numbers o SQL-string matching come source of truth. Canonical vocabulary iniziale:

```text
UOW_STARTED
OWNER_STABILIZED
DEPENDENCIES_STABILIZED
GATE_WAITING
GATE_ACQUIRED
PROTECTED_STATE_REREAD
CANDIDATE_WRITTEN
CLOSURE_WRITTEN
METADATA_SNAPSHOT_CAPTURED
EVENT_SET_WRITTEN
BEFORE_COMMIT
COMMITTED
ROLLED_BACK
```

Non tutte le UoW attraversano tutte le phase. Il vocabulary è harness-level e non diventa public production API.

### 7.9 Gate fresh-snapshot tests

`GATE-03A` e `GATE-06A` vengono orchestrati senza application pause hook quando possibile:

```text
B owns logical advisory gate
T1 waits on gate
B mutates protected state and COMMITs
T1 acquires gate
T1 executes a subsequent protected-read statement
```

Il semantic outcome deve dimostrare che T1 vede lo state committed dal previous holder. Questo prova simultaneamente gate wait, gate lifetime e fresh post-wait READ COMMITTED snapshot discipline.

### 7.10 Isolation contract

Ogni semantic worker usa esplicitamente:

```text
READ COMMITTED
```

anche se coincide con il server default. La suite non dipende da configuration ambientale dell'isolation level.

OBS deve ottenere observation fresche; non mantiene accidentalmente un transaction-wide stale snapshot quando sta verificando blocker/current committed state.

### 7.11 Timeout contract

Timeout/deadline sono esclusivamente safety net per impedire CI hang.

```text
deterministic barrier/blocker
    -> establishes ordering

timeout
    -> detects broken progress only
```

Il harness può usare scenario-level deadline e worker-local PostgreSQL `lock_timeout` / `statement_timeout` appropriati. I valori concreti appartengono alla test configuration, non al domain contract.

Nessun `sleep()` determina quando avviare la transaction concorrente.

### 7.12 Test database isolation

Una ordinary outer test transaction non è sufficiente al cleanup perché i semantic worker usano connection indipendenti e alcuni outcome devono realmente COMMITtare.

Baseline:

```text
isolated PostgreSQL test database per parallel test worker
+
scenario-owned unique IDs/names
+
explicit cleanup only after worker sessions terminate
```

Scenario che usano gli stessi global logical advisory gate non vengono eseguiti parallelamente nello stesso test database. Il suite parallelism viene ottenuto tramite database isolati, non tramite cross-scenario condivisione del protected authority state.

### 7.13 Failure diagnostics

Ogni failure concurrency deve rendere disponibili almeno:

```text
scenario ID
worker roles / pg_backend_pid / application_name
last harness phase
worker result/exception
pg_blocking_pids snapshot
relevant pg_stat_activity wait/state information
relevant pg_locks rows
final current authority state
final lifecycle-event state
```

La diagnostica non è domain state e non modifica il comportamento della UoW sotto test.

### 7.14 Retry boundary

Il harness non ritenta automaticamente uno scenario fallito per farlo passare.

Sono ammessi soltanto retry/convergence che fanno parte del semantic operation contract sotto test, per esempio `REL.CREATE` exact-view collision -> rollback -> fresh semantic UoW -> convergence/re-evaluation.

Un generic harness rerun è vietato come flakiness treatment della normative suite.

### 7.15 Deterministic contract vs stress suite

Si distinguono:

```text
Deterministic contract concurrency tests
    normative
    required CI
    controlled known interleavings

Stress/randomized concurrency tests
    supplementary
    many workers/randomized interleavings
    discovery-oriented
```

Uno stress test che scopre una nuova race genera lavoro architetturale/testuale:

```text
stress reproducer
-> reduce to deterministic scenario
-> add/update stable PGTEST scenario ID
-> align affected architecture if a new finding emerges
-> fix implementation
```

La stress suite non sostituisce i deterministic contract tests.

---

## 8. PGTEST-03 decisions

```text
P3.1  independent real PostgreSQL connections for semantic workers.
P3.2  canonical roles: CTL, OBS, optional blocker B, T1/T2/[T3].
P3.3  external PostgreSQL blockers are the preferred deterministic coordination mechanism.
P3.4  positive blocking is proved primarily via pg_blocking_pids; pg_stat_activity/pg_locks support diagnostics.
P3.5  no dependency on tuple-lock representation or pgrowlocks.
P3.6  intentional non-blocking is proved through positive progress while the other transaction remains open.
P3.7  downstream blockers may freeze a UoW after a known phase without production hooks.
P3.8  test-only persistence interceptor is last-resort and may pause/observe only, never change semantics/SQL/transaction behavior.
P3.9  logical-gate tests explicitly prove post-wait fresh-snapshot behavior.
P3.10 workers explicitly use READ COMMITTED.
P3.11 timeouts are failure safety nets, never orchestration primitives.
P3.12 parallel runners use isolated PostgreSQL databases; gate scenarios do not accidentally interact cross-test.
P3.13 failure diagnostics include backend identity, phase, blocker/wait/lock information, final state and lifecycle state.
P3.14 harness never retries failed scenarios to hide flakiness; only semantic retries defined by the operation are allowed.
P3.15 deterministic contract tests are normative CI; stress tests are supplementary and discoveries are reduced to deterministic scenarios.
```

---

## 9. PGTEST-04 — reusable deterministic execution recipes

### 9.1 Principle

Scenario ID e execution recipe hanno responsabilità distinte:

```text
scenario ID
    -> cosa deve essere dimostrato
       (scope, predicate, authority, allowed/forbidden outcome, assertions)

execution recipe
    -> come costruire deterministicamente l'interleaving
       senza ridefinire la semantics dello scenario
```

Ogni scenario possiede esattamente una `primary_recipe` e può comporre zero o più `secondary_recipes` quando devono essere esercitati più meccanismi. Una variante che richiede una concurrency authority diversa o una primary recipe diversa non viene nascosta sotto `A/B/C`: riceve un nuovo stable scenario ID.

Canonical recipe set M1:

```text
REC-LOCK
REC-UNIQUE
REC-FK
REC-GATE
REC-CUT
REC-ROLLBACK
REC-PROGRESS
REC-ABA
```

### 9.2 `REC-LOCK` — owner/row-lock waiter

Usata quando la safety deriva dalla serializzazione tramite una row owner authority.

```text
T1
    acquire semantic owner
    -> remain open at deterministic downstream point

T2
    start competing semantic operation
    -> must block on T1 owner

OBS
    pg_blocking_pids(T2) contains T1

release T1
    -> COMMIT or ROLLBACK

T2
    wakes
    -> mandatory re-read/revalidation
    -> success/failure/no-op according to winner state
```

Quando la semantic UoW non espone naturalmente un post-owner barrier, il preferred construction è un downstream PostgreSQL blocker raggiungibile da T1 soltanto dopo l'owner stabilization. La recipe prova owner corretto, lock strength, post-wait re-read e serial outcome.

### 9.3 `REC-UNIQUE` — PK/UNIQUE arbitration

```text
T1
    insert candidate unique fact
    keep transaction uncommitted

T2
    insert competing fact
    -> waits/arbitrates on same PK/UNIQUE authority

OBS
    prove blocker/arbitration relation when blocking is observable

T1 COMMIT

T2
    receives the expected unique/PK arbitration outcome
    -> candidate UoW rollback if the operation contract requires it
```

Domain handling resta scenario-specific:

```text
NU
    -> duplicate-name failure

SO
    -> same fact may converge; different desired ownership conflicts

RF
    -> rollback complete candidate UoW
       -> fresh semantic UoW
       -> converge/re-evaluate current fact
```

M1 non usa row-by-row partial `ON CONFLICT DO NOTHING` come aggregate-convergence recipe.

### 9.4 `REC-FK` — referential lifetime race

Submode canonici:

```text
REFERENCE_FIRST
    T1 creates current FK reference and remains open
    T2 attempts target DELETE
    T1 commits
    T2 cannot commit a state with dangling reference

DELETE_FIRST
    T1 deletes target and remains open
    T2 attempts new reference
    T1 commits
    T2 cannot establish a current FK to the deleted target

REMOVAL_UNBLOCKS_DELETE
    initial current reference exists
    T1 removes reference
    T2 attempts target DELETE
    removal-visible-first may allow success;
    delete seeing current blocker may wait/fail conservatively
```

Semantic precheck e FK final authority restano distinti: la recipe non impone un particolare precheck scheduling, ma vieta sempre dangling current references.

### 9.5 `REC-GATE` — logical predicate-set waiter

Usata per entrambi i logical gate M1.

```text
HOLDER
    acquire advisory xact gate
    optionally mutate protected state

WAITER
    attempt same gate
    -> blocks

OBS
    prove blocker relation

HOLDER
    COMMIT

WAITER
    acquires gate
    -> executes a NEW SQL statement
    -> obtains fresh READ COMMITTED snapshot
    -> rereads protected predicate
```

Critical assertion:

```text
gate acquisition != protected-state observation
```

Per ownership il protected reread include fresh child-ownership state + graph predicate. Per RelationshipDefinition include fresh certified set. La recipe verifica wait, hold-through-commit e post-wait fresh-snapshot discipline; può inoltre dimostrare intentional global over-serialization.

### 9.6 `REC-CUT` — committed observation cut

Definisce da quale lato di un commit boundary avviene una authoritative observation senza generic writer serialization.

Submode:

```text
NEW_BEFORE_OBSERVATION
    T1 changes metadata/state and commits
    T2 authoritative observation must see new committed state

NEW_AFTER_OBSERVATION
    T2 captures authoritative old committed observation
    T2 is blocked at a downstream DB boundary
    T1 changes metadata/state and commits
    release T2
    T2 must continue using the captured old observation

CHANGE_UNCOMMITTED_DURING_OBSERVATION
    T1 changes state but remains uncommitted
    T2 READ COMMITTED observation sees old committed state
```

La recipe serve sia `S-REL-EVENT-SNAPSHOT` sia monotone blocker-removal races dove un uncommitted remover può essere ancora osservato come blocker e causare conservative failure.

### 9.7 `REC-ROLLBACK` — rollback after physical work

Dimostra:

```text
partial SQL execution != partial committed semantic transition
```

Failure/rollback injection preference:

```text
1. natural later PK/FK/constraint arbitration
2. downstream PostgreSQL blocker + controlled statement abort/timeout
3. persistence-level controlled transaction rollback
4. last-resort test-only phase interceptor
```

Pattern:

```text
T1 performs one or more physical writes
-> pause/fail before semantic UoW completion
-> ROLLBACK

OBS
    no uncommitted current state remains visible
    no partial lifecycle event set exists
```

Per DELETE, rollback deve ripristinare il complete previous aggregate e non lasciare deletion events. La recipe verifica transaction boundary, non una SQL ordering che non sia normativa.

### 9.8 `REC-PROGRESS` — intentional non-blocking

Usata per proteggere le intentional non-serialization della realization.

```text
T1
    acquire potentially interacting lock/state
    remain transactionally open

T2
    start operation that MUST NOT be generically serialized

T2
    reaches a deterministic positive progress point
    while T1 is still open

only then
    release T1
```

La prova primaria è forward progress verso una phase che sarebbe irraggiungibile se il prohibited blocking esistesse. Una optional `pg_blocking_pids(T2)` negativa può supportare la diagnosi ma non sostituisce il progress proof.

### 9.9 `REC-ABA` — fresh-UoW restart / exact identity

Due submode canonici.

```text
EXACT_ID_ABA
    X current
    DELETE X -> COMMIT
    CREATE same semantic fact -> Y -> COMMIT
    late DELETE X -> no-op
    assert Y remains current

WINNER_DISAPPEARS_BEFORE_CONVERGENCE
    T1 creates X
    T2 competing CREATE loses PK arbitration and fully rolls back
    DELETE X -> COMMIT before T2 convergence read
    T2 restarts the semantic operation in a fresh UoW
    -> current exact view absent
    -> may create new Y
```

La recipe dimostra che a collisione non corrisponde una permanent winner identity e che retry/convergence riparte dal current committed state, non da candidate/cache stale.

### 9.10 Canonical 51-ID -> recipe mapping

```text
ROW-01   REC-LOCK
ROW-02   REC-LOCK
ROW-03   REC-LOCK
ROW-04   REC-LOCK
ROW-05   REC-LOCK
ROW-06   REC-LOCK
ROW-07   REC-LOCK
ROW-08   REC-LOCK
ROW-09   REC-LOCK
ROW-10   REC-CUT
ROW-11   REC-LOCK
ROW-12   REC-LOCK
ROW-13   REC-LOCK
ROW-14   REC-LOCK
ROW-15   REC-LOCK
ROW-16   REC-LOCK
ROW-17   REC-LOCK

ARB-01   REC-UNIQUE
ARB-02   REC-UNIQUE
ARB-03   REC-LOCK
ARB-04   REC-LOCK
ARB-05   REC-UNIQUE + REC-ABA
ARB-06   REC-LOCK
ARB-07   REC-ABA
          variant B also REC-UNIQUE

REF-01   REC-FK
REF-02   REC-FK
REF-03   REC-FK
REF-04   REC-FK
REF-05   REC-FK
REF-06   REC-FK

GATE-01  REC-GATE
GATE-02  REC-GATE
          removal variant also REC-CUT
GATE-03  REC-GATE
GATE-04  REC-GATE
GATE-05  REC-GATE
GATE-06  REC-GATE
          blocker-delete variant also REC-CUT

SNAP-01  REC-CUT
SNAP-02  REC-CUT
SNAP-03  REC-CUT
SNAP-04  REC-CUT

ATOMIC-01 REC-ROLLBACK
ATOMIC-02 REC-UNIQUE + REC-ROLLBACK
ATOMIC-03 REC-ROLLBACK
ATOMIC-04 REC-ROLLBACK

PAR-01   REC-PROGRESS
PAR-02   REC-PROGRESS
PAR-03   REC-LOCK
PAR-04   REC-GATE
PAR-05   REC-PROGRESS
PAR-06   REC-PROGRESS
PAR-07A  REC-LOCK
PAR-07B  REC-PROGRESS
```

Il mapping è completo: nessuno dei 51 canonical scenario ID richiede una nona orchestration family.

### 9.11 Recipe composition and variant discipline

Le otto recipe sono primitive di orchestration, non una nuova tassonomia di dominio.

Ogni scenario dichiara:

```text
primary_recipe
secondary_recipes[]
```

La primary recipe identifica il meccanismo dominante della race. Secondary recipes servono quando lo stesso scenario deve esercitare una seconda proprietà, per esempio `ARB-05` con `REC-UNIQUE` primaria e `REC-ABA` secondaria.

Una variante che richiede una authority differente o una primary recipe differente ottiene un nuovo scenario ID; non viene aggiunta artificialmente come `A/B/C` per evitare di estendere il census.

### 9.12 Test-hook budget

Prima di introdurre un test-only persistence interceptor deve essere dimostrato che l'interleaving richiesto non è realizzabile ragionevolmente tramite una delle otto recipe usando PostgreSQL blocker, PK/UNIQUE/FK arbitration, transaction boundary o advisory gate.

L'interceptor resta quindi una escape hatch e non una dependency ordinaria del kernel/test design.

---

## 10. PGTEST-04 decisions

```text
P4.1  Eight stable orchestration recipes: REC-LOCK, REC-UNIQUE, REC-FK,
      REC-GATE, REC-CUT, REC-ROLLBACK, REC-PROGRESS, REC-ABA.
P4.2  Recipe defines deterministic orchestration only; scenario semantics remain authoritative.
P4.3  Every scenario has exactly one primary recipe and optional secondary recipes.
P4.4  REC-LOCK proves owner serialization + mandatory post-wait re-read.
P4.5  REC-UNIQUE proves PK/UNIQUE arbitration; collision handling remains domain-specific.
P4.6  REC-FK covers reference-first, delete-first and removal-unblocks-delete.
P4.7  REC-GATE proves wait, hold-through-commit and fresh post-wait protected-state observation.
P4.8  REC-CUT defines committed observation boundaries for metadata and monotone blocker-removal races.
P4.9  REC-ROLLBACK proves no partial semantic commit after physical work; natural DB failure is preferred.
P4.10 REC-PROGRESS proves intentional non-serialization through positive forward progress.
P4.11 REC-ABA separately proves fresh-UoW restart and exact-identity ABA safety.
P4.12 The canonical 51-ID -> recipe mapping is complete.
P4.13 Variants requiring different authority/primary recipe receive a new stable scenario ID.
P4.14 Test-only persistence interceptor requires proof that canonical PostgreSQL recipes are insufficient.
```

---

## 11. Concurrency/test architecture closure

Con PGTEST-01..04 la baseline M1 definisce già:

```text
what semantic races must be tested
which stable scenario IDs cover them
which authority/mechanism each scenario exercises
how workers are orchestrated deterministically
how blocking/non-blocking is proved
how rollback/snapshot/gate/ABA cases are built
which reusable recipe each scenario uses
```

Non viene introdotto un PGTEST-05 soltanto per progettare ulteriormente fixture/helper/test class structure: tali scelte appartengono alla successiva decomposizione implementativa, purché rispettino PGTEST-01..04.

Un nuovo PGTEST design point viene aperto soltanto se implementation planning o un finding retroattivo dimostrano che una delle 51 race non è deterministicamente realizzabile con il contract corrente o richiede una nuova architecture-level test guarantee.
