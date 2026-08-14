# M1 — PostgreSQL Concurrency Realization Matrix

**Status:** DRAFT — REALIZE-01..REALIZE-15 ratificati; PostgreSQL concurrency realization semanticamente completa. Questo file è l'**indice canonico** della realization M1 e deve restare allineato ai companion e a `persistence-uow-concurrency.md`.

## 1. Scopo e document map

Questo documento realizza tecnicamente la semantic concurrency matrix M1 definita in `concurrency-semantic-matrix.md`.

Catena normativa:

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

La semantic matrix resta authority sul **cosa deve essere vero**. La realization definisce **come PostgreSQL lo garantisce**.

La realization completa è distribuita intenzionalmente in quattro documenti, senza gerarchia implicita fra copie divergenti:

```text
concurrency-postgresql-realization-matrix.md
    -> canonical index, REALIZE registry, cross-cutting rules

persistence-uow-concurrency.md
    -> isolation, UoW, lock strength/order, FK/constraint/gate baseline

concurrency-postgresql-realization-object-ownership.md
    -> REALIZE-08..11 + Object/ownership impact of REALIZE-15

concurrency-postgresql-realization-relationship.md
    -> REALIZE-12..14 + Relationship impact of REALIZE-15
```

`concurrency-postgresql-test-matrix.md` deriva i real-PG test dalla stessa catena ma non modifica la semantics/realization.

### 1.1 Documentation alignment invariant

Per M1 la documentazione `docs/milestones/M1/architecture/` è la baseline per il coding.

Regola forte:

> una decisione/refinement cross-cutting non è considerata consolidata finché non sono aggiornati nello stesso ciclo il canonical index, il baseline tecnico e ogni companion/domain document che contiene la stessa assumption.

Non è ammesso risolvere divergenze chiedendo al coder di “preferire il documento più recente”. Le formulazioni normative duplicate devono essere coerenti.

---

## 2. REALIZE-01 — canonical cell model

Ogni cella non-triviale usa, quando applicabile:

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

Si distinguono sempre:

- **concurrency authority**: state autorevole che decide il predicate;
- **physical authority**: row/key/FK/set persistito che rappresenta/protegge quello state;
- **mechanism**: `FOR NO KEY UPDATE`, `FOR UPDATE`, `FOR SHARE`, PK/UNIQUE, FK `RESTRICT`, advisory gate, coherent snapshot, ecc.

Un lock non è l'authority semantica.

### 2.2 Physical-authority families

1. **row-state authority** — mutable current state su una specifica row;
2. **relational uniqueness authority** — PK/UNIQUE arbitra competing facts;
3. **referential lifetime authority** — FK `RESTRICT` arbitra reference-vs-delete;
4. **predicate-set authority** — committed row set stabilizzato da logical gate;
5. **snapshot authority** — coherent committed observation senza writer serialization.

### 2.3 Outcome classes

```text
SERIALIZATION
ARBITRATION
CONVERGENCE
REFERENTIAL
SNAPSHOT
INDEPENDENT
```

Le classi possono comporsi, per esempio Relationship factual CREATE usa `ARBITRATION + CONVERGENCE`.

Una semantic `I` cell può comunque avere implementation contention; tali casi devono essere documentati e testati quando architetturalmente rilevanti.

---

## 3. Cross-cutting PostgreSQL lock baseline — REALIZE-15

Il consistency sweep ha raffinato la precedente primitive generica `FOR UPDATE`.

Canonical rule:

```text
non-key mutable-state owner
    -> FOR NO KEY UPDATE

row delete / referenced-key-changing owner
    -> FOR UPDATE

lifecycle-sensitive exact dependency
    -> FOR SHARE

pure referential lifetime
    -> FK machinery / key-share semantics, no extra RL-only lock
```

Razionale:

- writer owner sulla stessa row restano mutuamente esclusivi;
- `FOR SHARE` continua a bloccare lifecycle state mutation;
- una pure FK/key-share reference non deve serializzare una non-key metadata/state mutation;
- M1 non usa lock strength più forte del predicate richiesto.

`FOR UPDATE` rimane normativo per delete della referenced row identity, per esempio Object DELETE, Definition DELETE, Relationship DELETE, whole-lineage DELETE ed exact `DELETE_DRAFT` sulla row rimossa.

### 3.1 Canonical resource ordering

Per model resources:

```text
(kind, lineage_uuid, resource_rank, version)
```

con lineage header prima della exact version della stessa lineage.

Quando servono entrambe:

```text
lineage -> exact
```

Ownership:

```text
parent Object -> OWNERSHIP_GRAPH_WRITE_GATE
```

RelationshipDefinition:

```text
Definition header -> RELATIONSHIP_DEFINITION_CONFLICT_GATE
```

Nessuna M1 UoW acquisisce entrambi i global gate.

### 3.2 Logical-gate fresh-snapshot rule

Per ogni transaction-level advisory gate:

```text
statement 1:
    SELECT pg_advisory_xact_lock(...)

statement 2+:
    authoritative protected-set read/re-read
```

Il post-wait predicate viene quindi osservato con un fresh `READ COMMITTED` statement snapshot. Il gate resta detenuto fino a commit/rollback.

---

## 4. Predicate realization registry

| Predicate | Concurrency / physical authority | PostgreSQL realization | Detailed authority |
|---|---|---|---|
| `NU` | qualified-name ownership / `UNIQUE(namespace,name)` | relational arbitration; no name lock | REALIZE-02 |
| `VS` | current lineage version set / lineage header + versions | lineage owner `FOR NO KEY UPDATE`; recompute after wait | REALIZE-02 |
| `DG` | exact DRAFT generation / exact version row | non-delete writer `FOR NO KEY UPDATE`; delete target `FOR UPDATE`; revision recheck | REALIZE-03 |
| `LS` | exact version lifecycle state | exact version non-key owner + status recheck | REALIZE-03 |
| `DV` | lineage default policy + exact target status | lineage `FOR NO KEY UPDATE`; target `FOR SHARE`; deprecate lineage `FOR SHARE` | REALIZE-04 |
| `BA` | newly selected exact dependency | explicit exact `FOR SHARE`; implicit header `FOR SHARE` -> exact `FOR SHARE` | REALIZE-05 |
| `AM` | direct PUBLISHED consumer/dependency set | publisher dependencies `FOR SHARE`; dependency deprecator exact owner + reverse lookup | REALIZE-06 |
| `RL` | current direct reference graph / FK | immediate `NOT DEFERRABLE` FK `RESTRICT`; no generic RL-only target lock | REALIZE-07 |
| `AL` | aggregate root/owned state lifetime | root delete `FOR UPDATE`; existing child owner rendezvous; CASCADE only owned state | object/ownership companion |
| `ML` | lineage description row value | atomic row UPDATE / PostgreSQL writer order | object/ownership companion |
| `OS` | complete current intrinsic Object row | non-delete Object mutation `FOR NO KEY UPDATE`; DELETE `FOR UPDATE` | object/ownership companion |
| `PO` | parent Object schema + outgoing ownership set | parent `FOR NO KEY UPDATE` | object/ownership companion |
| `OF` | current `object_components` fact for child | current-fact re-read + exact idempotent decision | object/ownership companion |
| `SO` | child ownership uniqueness | `PRIMARY KEY(child_object_id)` | object/ownership companion |
| `OC` | committed ownership graph | `OWNERSHIP_GRAPH_WRITE_GATE` + fresh graph read + cycle check | object/ownership companion |
| `RC` | committed certified Definition/Resolution set | `RELATIONSHIP_DEFINITION_CONFLICT_GATE` + fresh global check | Relationship companion |
| `RF` | current exact runtime resolved view | runtime exact-view PK arbitration + fresh-UoW convergence | Relationship companion |
| `RA` | exact `Relationship.id` lifetime | Relationship delete owner `FOR UPDATE`; exact-ID idempotency/ABA | Relationship companion |
| `ES` | one coherent committed metadata observation | one SQL MVCC observation statement, no metadata writer lock | Relationship companion |

Tutti i 19 safety predicate M1 hanno quindi authority, mechanism e real-PG test family identificati.

---

## 5. REALIZE decision registry

### REALIZE-02 — `NU`, `VS`

- `UNIQUE(namespace,name)` è final authority per same-kind model names; precheck non è race authority.
- Stable lineage header possiede current version membership/allocation.
- `CREATE_NEXT` serializza sul lineage owner e ricalcola `max(existing)+1` dopo il lock.
- `DELETE_DRAFT` partecipa sia a `VS` sia a `DG`: lineage owner prima, exact DRAFT delete owner dopo.
- Delete di DRAFT differenti della stessa lineage è intentional over-serialization.

### REALIZE-03 — `DG`, `LS`

- Exact DTV/OTV row possiede generation/lifecycle.
- `REVISE`/`PUBLISH` usano exact non-key owner e verificano `status=DRAFT`, `revision=expected` dopo il lock.
- `DELETE_DRAFT` usa `FOR UPDATE` sulla row eliminata.
- `DEPRECATE` usa exact non-key owner e richiede current `PUBLISHED`.
- Nessun automatic retry trasforma una stale expected generation in nuovo intent.

### REALIZE-04 — `DV`

- Stable lineage header possiede la default policy.
- `PUBLISH` prende sempre lineage owner, anche se default già non-NULL.
- `SET_DEFAULT`: lineage owner -> target exact `FOR SHARE`.
- `CLEAR_DEFAULT`: lineage owner.
- `DEPRECATE`: lineage `FOR SHARE` -> exact lifecycle owner.
- First publish auto-default e explicit set/clear sono serialmente spiegabili.

### REALIZE-05 — `BA`

- New/rebound explicit exact dependency: exact row `FOR SHARE`, recheck PUBLISHED.
- Implicit binding: dependency lineage `FOR SHARE` -> resolve default -> exact `FOR SHARE` -> recheck PUBLISHED.
- Historical unchanged pins non vengono ricertificati durante DRAFT revise.
- `CREATE_NEXT` historical clone non è nuova admission.
- Multi-dependency resources seguono canonical deterministic order.

### REALIZE-06 — `AM`

- Exact dependency row è rendezvous fra active-edge activation e dependency deprecation.
- OTV publish stabilizza soltanto direct lifecycle-sensitive exact dependencies con `FOR SHARE`.
- Dependency deprecator stabilizza exact row e fa reverse lookup dei direct PUBLISHED consumer.
- Reverse consumer rows non vengono fan-out locked; concurrent consumer removal può causare conservative failure.
- Nessun active-model global gate e nessun transitive dependency lock traversal.

### REALIZE-07 — `RL`

- Current cross-aggregate lifetime è finalmente arbitrata dalle FK `ON DELETE RESTRICT` immediate/NOT DEFERRABLE.
- Semantic precheck serve a error quality, non alla race correctness.
- `CASCADE` è solo root -> owned child dello stesso aggregate; external/current refs sono `RESTRICT`.
- Le FK riflettono direct persisted authority refs, non semantic dependency transitive.

### REALIZE-08 — `AL`, `ML`

Dettaglio in `concurrency-postgresql-realization-object-ownership.md`.

- Nessun universal aggregate-share lock.
- Whole-lineage root delete `FOR UPDATE`; owned children CASCADE; external refs RL.
- REVISE exact-child owner rendezvous con cascade delete senza lineage-wide lock.
- Description è atomic LWW metadata senza revision/CAS.

### REALIZE-09 — `OS`

Dettaglio nel companion Object/ownership.

- Object non-delete intrinsic mutation: Object row `FOR NO KEY UPDATE` prima della state-dependent candidate derivation.
- DELETE: Object row `FOR UPDATE`.
- Candidate deve essere derivata/rivalidata dal complete post-lock state.
- Current write + exact lifecycle event candidate sono una UoW.
- DATA_CHANGE semantic no-op produce zero event.

### REALIZE-10 — `PO`, `OF`, `SO`

- Parent Object `FOR NO KEY UPDATE` possiede current exact parent schema + outgoing set.
- ATTACH/DETACH valutano il current child ownership fact dopo parent stabilization.
- `PRIMARY KEY(child_object_id)` resta final single-owner authority, anche se il graph gate può mascherare la raw race.
- Nessun generic child Object lock.
- Ownership non ha stable edge identity né Relationship-style ABA protection.

### REALIZE-11 — `OC`

- Committed `object_components` graph è authority.
- Solo real ATTACH edge-add acquisisce `OWNERSHIP_GRAPH_WRITE_GATE`.
- Gate acquisition e graph read sono statement separati; child ownership viene riletto dopo il gate.
- Cycle check avviene sul fresh committed graph; gate resta fino a commit.
- DETACH non prende il gate.
- Global serialization di unrelated edge-add è intentional over-serialization.

### REALIZE-12 — `RC`

Dettaglio in `concurrency-postgresql-realization-relationship.md`.

- RD.CREATE e RD.RENAME passano dal global conflict gate.
- RD.RENAME acquisisce prima Definition `FOR NO KEY UPDATE`.
- Gate holder legge un fresh committed certified set, poi esegue equivalence + conflict check nella stessa critical section.
- RD.DELETE non prende il gate; può rimuovere blocker, con conservative failure ammessa per candidate che la vede ancora current.
- Nessun fan-out lock sulle altre Definition e nessun runtime Relationship gate.

### REALIZE-13 — `RF`, `RA`

- Runtime exact-view PK è factual arbitration authority.
- Existing requested view -> converge/no-op/no event.
- Real CREATE deriva, deduplica e canonical-sorta la complete closure; header + closure + events sono atomic.
- Exact-view collision abortisce l'intera UoW; convergence avviene in una fresh semantic UoW.
- Relationship DELETE usa exact header `FOR UPDATE`; same-ID repeated delete converge no-op.
- Recreate stessa semantic association usa nuova UUID; late DELETE old ID non colpisce la nuova fact.

### REALIZE-14 — `ES`

- One factual Relationship transition usa un solo SQL metadata-observation statement a `READ COMMITTED` per l'intero event set.
- Lo statement osserva Resolution names + endpoint canonical names nello stesso MVCC snapshot.
- Nessun metadata `FOR SHARE/FOR UPDATE` solely for ES.
- CREATE osserva dopo complete closure insertion riuscita; DELETE prima della closure removal.
- Event projection/dedup appartiene allo stesso observation boundary.
- `occurred_at=transaction_timestamp()` non è metadata-observation time né commit/global order.

### REALIZE-15 — consistency sweep

- Tutti i 19 predicate risultano coperti; nessun normal lock-order cycle identificato.
- Generic mutable owner raffinato a `FOR NO KEY UPDATE`; delete/key-changing owner resta `FOR UPDATE`.
- Questo evita FK-induced serialization di non-key Object/RD mutation e preserva `ES`/semantic `I` hot paths.
- Ownership structural-event parent name proviene dalla locked parent row; child name è committed display metadata osservato dopo parent stabilization senza child lock solely for event metadata.
- Intentional over-serialization condivisa resta documentata; important intentional non-serialization è regression-tested.

---

## 6. Intentional physical contention registry

Semantic `I` non implica physical parallelism.

Intentional M1 over-serialization include almeno:

```text
OBJ.RENAME(parent) × OBJ.ATTACH(parent)
OBJ.DATA_CHANGE(parent) × OBJ.DETACH(parent)
SET_DESCRIPTION × same-lineage header-owner mutations
unrelated real ATTACH × unrelated real ATTACH via global ownership gate
unrelated RD.CREATE/RENAME × unrelated RD.CREATE/RENAME via global conflict gate
same-lineage publish of different DRAFT versions via default-policy owner
DELETE_DRAFT of different DRAFTs same lineage via version-set owner
```

Intentional non-serialization/proportionality include almeno:

```text
REL.CREATE × OBJ.RENAME               -> no FK-only block; ES snapshot when real event
REL.CREATE × OBJ.DATA_CHANGE/SCHEMA_CHANGE -> no generic runtime/model serialization
REL.CREATE × RD.RENAME                -> no FK-only block; ES snapshot
unrelated REL.CREATE × unrelated REL.CREATE -> no global Relationship lock
DEPRECATE(v1) × DEPRECATE(v2) same lineage -> lineage FOR SHARE may coexist
REVISE exact DRAFT × SET_DESCRIPTION same lineage -> no universal lineage owner
```

Queste proprietà sono parte della architecture e devono essere protette da `T-PAR` regression test.

---

## 7. Retry/convergence registry

```text
stale DRAFT generation
    -> semantic failure, no automatic intent rewrite

FK/RESTRICT arbitration loss
    -> domain lifetime failure, no generic automatic retry

exact Relationship-view PK collision
    -> full UoW rollback + fresh semantic CREATE/convergence UoW

same-ID Relationship DELETE waiter
    -> absent => idempotent no-op

advisory gate wait
    -> normal blocking path; fresh predicate read after acquisition

deadlock/transient DB failure
    -> complete-UoW retry policy where explicitly supported;
       never repository-fragment retry with stale candidate
```

---

## 8. Traceability and coding baseline

Required chain:

```text
Invariant / domain contract
-> semantic matrix scoped rule
-> safety predicate
-> this realization authority/mechanism
-> persistence structure / lock / gate / snapshot
-> concurrency-postgresql-test-matrix scenario
-> M1 implementation
```

A future mutation is not concurrency-designed until it is added to the semantic census, compared against all existing operations, assigned realization authority/mechanism, and mapped to real PostgreSQL test coverage.

Before coding begins, architecture review must treat any disagreement among the canonical index, `persistence-uow-concurrency.md`, the two realization companions, domain lifecycle docs and the PG test matrix as an architecture defect to resolve — not as an implementation choice.
