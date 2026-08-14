# M1 — PostgreSQL Concurrency Test Matrix

**Status:** DRAFT — PGTEST-01 ratificato; scenario census e coverage mapping vengono aggiunti nei successivi PGTEST point.

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

**Mechanism assertions** sono normative soltanto quando il mechanism è parte esplicita della realization. Esempi:

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

## 4. Successivi point

PGTEST-02 definisce il concrete scenario census e gli ID canonicali per tutte le family, con coverage mapping dei 19 safety predicate prima di qualsiasi implementazione di test.
