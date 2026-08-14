# M1 — PostgreSQL Concurrency Test Matrix

**Status:** DRAFT — PGTEST-01 e PGTEST-02 ratificati; canonical scenario contract, census e 19-predicate coverage mapping completi. Il deterministic harness contract viene definito nel successivo PGTEST point.

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

## 7. Next point

PGTEST-03 definisce il deterministic concurrency harness contract:

- two/three independent transaction orchestration;
- barrier/test-hook placement;
- safe observation of blocked state without sleep-only coordination;
- allowed use of `pg_locks` / `pg_stat_activity` in persistence-level tests;
- timeout and teardown rules that prevent hanging CI or leaked transactions.
