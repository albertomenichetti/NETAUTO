# M1 — PostgreSQL Concurrency Realization Matrix

**Status:** DRAFT — REALIZE-01..REALIZE-03 ratificati; il documento viene esteso predicate-by-predicate.

## 1. Scopo

Questo documento realizza tecnicamente la semantic concurrency matrix M1 definita in `concurrency-semantic-matrix.md`.

La sequenza normativa è:

```text
semantic race / scope
-> safety predicate
-> required outcome class
-> concurrency authority
-> physical authority
-> PostgreSQL stabilization/arbitration mechanism
-> revalidation point
-> loser/retry behavior
-> real PostgreSQL concurrency test
```

La semantic matrix resta authority sul **cosa deve essere vero**. Questo documento definisce **come PostgreSQL lo garantisce**.

---

## 2. REALIZE-01 — canonical cell format

Ogni cella non-triviale usa, quando applicabile, i campi:

```text
Operation A × Operation B

Scope
Semantic predicate
Required outcome
Concurrency authority
Physical authority
Stabilization / arbitration mechanism
Revalidation point
Loser behavior
Retry behavior
Intentional over-serialization
Required PostgreSQL concurrency test
```

### 2.1 Authority != mechanism

La documentazione distingue sempre:

- **concurrency authority**: lo state autorevole che decide se il predicate è soddisfatto;
- **physical authority**: row/key/FK/set concreto che rappresenta o protegge quello state;
- **mechanism**: il modo in cui PostgreSQL stabilizza/arbitra la race (`FOR UPDATE`, `FOR SHARE`, UNIQUE/PK, FK `RESTRICT`, advisory gate, coherent snapshot, ...).

Un lock non è di per sé l'authority semantica.

### 2.2 Physical-authority families M1

1. **row-state authority** — una row rappresenta mutable state seriale;
2. **relational uniqueness authority** — PK/UNIQUE arbitra competing facts;
3. **referential lifetime authority** — FK `RESTRICT` arbitra reference-vs-delete;
4. **predicate-set authority** — un committed row set viene stabilizzato da logical gate;
5. **snapshot authority** — non serve writer serialization, ma una coherent committed observation.

### 2.3 Required outcome classes

```text
SERIALIZATION
ARBITRATION
CONVERGENCE
REFERENTIAL
SNAPSHOT
INDEPENDENT
```

Le classi possono comporsi. Esempio: equivalent `Relationship.CREATE` usa `ARBITRATION + CONVERGENCE`.

### 2.4 `I` semantic cells nella realization matrix

Una cella semanticamente `I` può comunque avere contention fisica.

La realization matrix deve rendere visibili i casi di **intentional implementation over-serialization**, per esempio:

```text
OBJ.RENAME(P) × OBJ.ATTACH(P,S,C)
semantic: I
physical: may serialize on objects(P) FOR UPDATE
```

Questo consente futuri miglioramenti di parallelismo senza riaprire la semantica del dominio.

---

## 3. REALIZE-02 — `S-NAME-UNIQUE` (`NU`)

### 3.1 Physical authority

Per singolo entity kind:

```text
datatypes        UNIQUE(namespace, name)
object_templates UNIQUE(namespace, name)
```

La UNIQUE è sia structural authority sia concurrency arbiter.

### 3.2 CREATE × CREATE stesso qualified name

```text
Predicate
    S-NAME-UNIQUE

Required outcome
    ARBITRATION

Concurrency authority
    current ownership of (namespace,name) within entity kind

Physical authority
    UNIQUE(namespace,name)

Stabilization
    none before INSERT

Revalidation
    none required for correctness

Loser
    unique-constraint violation -> semantic duplicate-name failure

Retry
    none automatically
```

Un eventuale precheck `SELECT` è solo fast-fail/error-quality optimization e non è race authority.

### 3.3 CREATE × DELETE_LINEAGE con riuso del nome

La stessa UNIQUE arbitra il riuso del qualified name. Se la delete committa per prima, la nuova lineage può acquisire il nome con una nuova UUID identity; se la vecchia row resta current, la CREATE non può committare.

Non si usa advisory/name lock.

### 3.4 Required PostgreSQL tests

Almeno:

1. concurrent CREATE same name -> esattamente un current owner;
2. CREATE same name vs successful lineage delete -> success outcome serialmente valido;
3. CREATE same name vs failed/rolled-back lineage delete -> CREATE non bypassa la UNIQUE.

---

## 4. REALIZE-02 — `S-VERSION-SET` (`VS`)

### 4.1 Concurrency owner

La **stable lineage header row** è il concurrency owner del current version membership/allocation set.

Regola:

> ogni supported M1 mutation che aggiunge o rimuove una current version della lineage acquisisce la lineage header `FOR UPDATE` prima di modificare il set.

In M1:

```text
CREATE_NEXT
DELETE_DRAFT
```

### 4.2 CREATE_NEXT

```text
lineage header FOR UPDATE
-> read coherent current version set
-> compute current max
-> validate source exists
-> validate source status in {PUBLISHED, DEPRECATED}
-> validate source.version != current max
-> allocate current max + 1
-> INSERT new DRAFT revision=1
```

La source PUBLISHED/DEPRECATED non richiede un exact-row lock soltanto per `CREATE_NEXT`: è strutturalmente immutable, non è individualmente deletable, e `PUBLISHED -> DEPRECATED` non cambia la sua source eligibility.

Whole-lineage delete è esclusa dal lineage-header lock.

### 4.3 DELETE_DRAFT

`DELETE_DRAFT` partecipa a due concurrency domain:

```text
lineage header
    -> S-VERSION-SET

exact DRAFT row
    -> S-DRAFT-GENERATION
```

Ordering:

```text
lineage header FOR UPDATE
-> exact DRAFT row FOR UPDATE
-> recheck status == DRAFT
-> recheck revision == expected_revision
-> DELETE
```

### 4.4 Lock ordering

Quando una mutation necessita sia della stable lineage row sia di una exact version row:

```text
lineage row
-> exact version row
```

mai il contrario.

Questa è la baseline order condivisa anche con le operation future della realization matrix che necessitano entrambe.

### 4.5 CREATE_NEXT × CREATE_NEXT

```text
Predicate
    S-VERSION-SET

Required outcome
    SERIALIZATION

Authority
    current version set

Physical authority
    lineage header + authoritative version rows

Stabilization
    lineage header FOR UPDATE

Revalidation
    after lock, recompute max and source eligibility

Loser
    ordinary waiter; after wake-up derives from winner's committed set
```

Entrambe possono riuscire, per esempio `v3` e poi `v4`, se source eligibility resta valida.

### 4.6 CREATE_NEXT × DELETE_DRAFT

Entrambe acquisiscono la stessa lineage header `FOR UPDATE`.

Se `CREATE_NEXT` vince, può allocare rispetto al pre-delete set e il successivo delete rimuove il DRAFT. Se `DELETE_DRAFT` vince, `CREATE_NEXT` rivaluta `max(existing)` e source eligibility sul nuovo set e può anche diventare non ammissibile.

### 4.7 Intentional over-serialization

Due `DELETE_DRAFT` di exact DRAFT differenti della stessa lineage sono normalmente semanticamente indipendenti rispetto al version-set predicate, ma M1 le serializza sulla lineage header per mantenere una sola semplice authority del current version membership.

Il costo è accettato perché è model-plane contention, non runtime hot-path.

### 4.8 Required PostgreSQL tests

Almeno:

1. `CREATE_NEXT × CREATE_NEXT` stessa lineage -> unique consecutive allocation, nessuna collisione/lost set;
2. `CREATE_NEXT(source older) × DELETE_DRAFT(max)` -> entrambi i possibili ordini seriali;
3. `DELETE_DRAFT(vA) × DELETE_DRAFT(vB)` stessa lineage -> correctness nonostante intentional over-serialization;
4. verifica lock-order `lineage -> exact` nei path che richiedono entrambe.

---

## 5. REALIZE-03 — `S-DRAFT-GENERATION` (`DG`) e `S-LIFECYCLE-STATE` (`LS`)

### 5.1 Exact-version concurrency owner

La exact DTV/OTV row è il concurrency owner di:

```text
exact DRAFT generation
exact lifecycle state
```

Per DTV l'identity è `(datatype_id, version)`; per OTV `(template_id, version)`.

Le exact rows vengono stabilizzate con `FOR UPDATE` prima di mutation che cambiano `revision`, `status` o l'esistenza della DRAFT.

Il DB `CHECK` limita il vocabolario dello status; monotonicità e transition admission restano UoW-enforced.

### 5.2 Common DRAFT mutation pipeline

Per `REVISE`, `PUBLISH`, `DELETE_DRAFT`:

```text
acquire any required higher-level lineage lock first
-> exact DRAFT row FOR UPDATE
-> re-read status
-> re-read revision
-> require status == DRAFT
-> require revision == expected_revision
-> execute semantic transition
```

`expected_revision` è generation token semantico e non sostituisce il row lock.

Per OTV, la exact OTV row possiede concorrentemente l'intera DRAFT candidate: parent pin + local property declarations + local component declarations. Le child declaration rows non hanno autonomous mutation locking/lifecycle.

### 5.3 `REVISE × REVISE`

Same exact DRAFT generation:

```text
Required outcome
    SERIALIZATION

Physical authority
    exact version row

Mechanism
    FOR UPDATE

After wait
    re-read status + revision
```

Se entrambe partono da `expected_revision=N`, la prima revise porta `N -> N+1`; la seconda osserva una generation diversa e fallisce freshness. Non esiste automatic retry con il nuovo revision, perché cambierebbe l'intent del caller.

### 5.4 `REVISE × PUBLISH`

Se REVISE committa prima, PUBLISH basata sulla vecchia revision fallisce freshness. Se PUBLISH committa prima, la successiva REVISE osserva status non più DRAFT e fallisce admission.

Il loser non riapplica automaticamente il proprio intent sul nuovo state.

### 5.5 `REVISE × DELETE_DRAFT`

Se REVISE vince, cambia generation e DELETE_DRAFT con old `expected_revision` fallisce. Se DELETE_DRAFT vince, la exact target generation non esiste più e REVISE non può committare.

### 5.6 `PUBLISH × DELETE_DRAFT`

Se PUBLISH vince, la row diventa PUBLISHED e non è più individualmente deletable. Se DELETE_DRAFT vince, PUBLISH non trova più la target generation.

### 5.7 `PUBLISH × PUBLISH` sulla stessa exact DRAFT

Una sola transaction può effettuare la reale transition `DRAFT -> PUBLISHED`. La seconda, dopo il wait, osserva PUBLISHED e non produce una seconda publication transition né un secondo effetto di first-publish/default policy.

La public failure/idempotency surface della seconda operation viene definita nel failure/API contract; la persistence guarantee è che la real transition avvenga al massimo una volta.

### 5.8 `DEPRECATE` e lifecycle state

`DEPRECATE` stabilizza la exact version con `FOR UPDATE` e, dopo ogni eventuale wait, richiede current `status == PUBLISHED` prima della transition `PUBLISHED -> DEPRECATED`.

Gli ulteriori predicate di default e active-model graph possono aggiungere blocker; vengono realizzati nei successivi REALIZE point.

### 5.9 `PUBLISH × DEPRECATE`

La exact-row lifecycle authority impedisce transition incompatibili. Se DEPRECATE osserva ancora DRAFT non è ammissibile. Se PUBLISH committa prima, DEPRECATE può successivamente essere rivalutata sul nuovo PUBLISHED state e riuscire solo se tutti gli altri blocker (`DV`, `AM`) sono assenti.

### 5.10 `DEPRECATE × DEPRECATE`

Una sola transaction può effettuare la reale transition `PUBLISHED -> DEPRECATED`; la seconda osserva DEPRECATED dopo il wait e non applica una seconda real transition.

La public error/idempotency mapping è differita alle failure semantics.

### 5.11 Lock ordering

Quando la stessa mutation richiede anche stable-lineage state, vale sempre:

```text
lineage row
-> exact version row
```

`REVISE` normalmente non necessita della lineage row e può acquisire direttamente la exact DRAFT row.

`PUBLISH` viene completata in REALIZE-04 perché first-publish/default policy può richiedere stable-lineage coordination.

### 5.12 Rejected alternative: CAS-only DRAFT mutations

Un conditional `UPDATE ... WHERE status='DRAFT' AND revision=:expected` potrebbe essere sufficiente per alcune DTV mutation, ma non viene adottato come modello generale M1.

Ragioni:

- OTV è un aggregate multi-row;
- la exact OTV row deve possedere la complete DRAFT candidate;
- DTV e OTV mantengono un modello di concurrency simmetrico;
- explicit `FOR UPDATE` + recheck rende chiara la stabilization authority.

### 5.13 Required PostgreSQL tests

Almeno:

1. `REVISE × REVISE` stessa generation -> un solo winner, loser stale;
2. `REVISE × PUBLISH` -> entrambi gli ordini serialmente validi;
3. `REVISE × DELETE_DRAFT` -> nessuna mutation su generation rimossa/stale;
4. `PUBLISH × DELETE_DRAFT` -> mai publish+delete della stessa generation;
5. `PUBLISH × PUBLISH` stessa DRAFT -> una sola real transition;
6. `DEPRECATE × DEPRECATE` stessa PUBLISHED version -> una sola real transition;
7. `PUBLISH × DEPRECATE` stessa exact version -> nessun lifecycle state non spiegabile dalla state machine;
8. OTV revise concorrente non può produrre mixed child-declaration candidate.

---

## 6. Traceability rule

Ogni successivo REALIZE point deve aggiornare questa catena:

```text
semantic predicate / scoped matrix cell
-> authority
-> PostgreSQL mechanism
-> loser/retry behavior
-> required real-PG concurrency test
```

Nessuna futura mutation è concurrency-designed finché non viene confrontata con il census completo della semantic matrix e non viene aggiunta anche a questo livello di realization.
