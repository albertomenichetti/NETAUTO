# M1 — PostgreSQL Unit of Work & Concurrency Realization Baseline

**Status:** DRAFT — decisioni PERSIST-16..PERSIST-20 ratificate; REALIZE-15 raffina PERSIST-19 distinguendo non-key mutation owner (`FOR NO KEY UPDATE`) da delete/key-changing owner (`FOR UPDATE`). La complete realization matrix è consolidata nei documenti companion `concurrency-postgresql-realization-*.md`.

## 1. Scopo

Questo documento definisce il baseline tecnico PostgreSQL già ratificato per:

- enforcement boundary DB vs Unit of Work;
- semantic transaction boundary;
- isolation level;
- row-lock ownership, strength e ordering;
- lifecycle-sensitive dependency admission;
- ownership graph gate;
- RelationshipDefinition global conflict gate;
- retry/convergence expectations ad alto livello.

La sequenza normativa resta:

```text
invariant / semantic predicate
    -> required guarantee
    -> persistence authority
    -> PostgreSQL mechanism
    -> real PostgreSQL concurrency test
```

Il documento non sostituisce `concurrency-semantic-matrix.md`: la semantic matrix è technology-agnostic e viene prima della realization.

---

## 2. Enforcement matrix — PERSIST-16

M1 baseline usa esclusivamente declarative PostgreSQL constraints:

```text
PRIMARY KEY
UNIQUE
FOREIGN KEY
CHECK
NOT NULL
ON DELETE action
```

per gli invarianti che il relational model può esprimere in modo diretto e comprensibile.

### 2.1 No constraint triggers baseline

M1 **non usa constraint trigger** come baseline per semantic invariants cross-row/cross-aggregate.

Ragione:

> il relational model deve dichiarare chiaramente cosa può proteggere; ciò che richiede lifecycle logic, candidate reconstruction, graph traversal o multi-aggregate interpretation appartiene alla model -> persistence Unit of Work.

Non viene implementato un “domain service in SQL”.

Un constraint trigger è future escape hatch solo se viene dimostrato che UoW + standard constraints producono una soluzione peggiore. Richiede esplicita riapertura architetturale.

### 2.2 DB-enforced vs UoW-enforced

Ogni invariant persistence/concurrency deve essere classificato esplicitamente come:

```text
DB-enforced
oppure
UoW-enforced
```

Se UoW-enforced, la documentazione deve spiegare perché non è ragionevole o trasparente esprimerlo declarativamente nel DB.

Esempi DB-enforced:

- PK/identity uniqueness;
- exact composite FK existence;
- `Object` -> exact OTV existence;
- ownership single-owner via child PK;
- Relationship exact runtime-view uniqueness;
- same-Definition runtime row consistency tramite composite FK;
- cross-aggregate lifetime via `RESTRICT`;
- local scalar row-shape CHECK.

Esempi UoW/concurrency-enforced:

- lifecycle transition admission;
- current default must be PUBLISHED;
- active model graph;
- OTV effective-schema validity;
- exact canonical Object property validity;
- OTV parent denormalization equality con stable lineage parent;
- ownership slot compatibility;
- ownership acyclicity;
- RelationshipDefinition aggregate shape;
- global Definition equivalence/conflict-free set;
- runtime Relationship complete closure;
- Relationship factual endpoint-pair coherence;
- complete lifecycle event-set atomicity.

Published/Deprecated immutability e lifecycle monotonicity sono UoW contracts, non trigger contracts.

---

## 3. Semantic Unit of Work boundary — PERSIST-17

Regola M1:

> **una semantic kernel mutation = una PostgreSQL write Unit of Work**.

La stessa UoW comprende:

1. tutte le state-dependent read necessarie per admission;
2. eventuale dependency/default resolution;
3. candidate derivation e canonical validation;
4. stabilization/locking dei predicate rilevanti;
5. current-state writes;
6. complete required lifecycle event set;
7. commit/rollback atomico.

Repository/DAO non possiede `commit`; il transaction boundary appartiene alla Unit of Work/application boundary.

Una semantic mutation può attraversare più tabelle e aggregate quando il suo contract lo richiede.

### 3.1 Fuori dalla UoW

Parsing o validation puramente sintattica che non dipende da mutable persisted state può avvenire prima dell'apertura della transaction.

Qualunque correctness predicate dipendente da current state deve invece essere letto e stabilizzato dentro la UoW.

### 3.2 Non-goal

M1 non mantiene transaction aperte:

- tra richieste HTTP diverse;
- durante workflow lunghi;
- come generic orchestration boundary.

Più primitive M1 non condividono automaticamente la stessa UoW. Una futura higher-level semantic command deve dichiarare esplicitamente il proprio transaction contract se richiede all-or-nothing composition.

### 3.3 Failure/retry scope

Una failure della semantic mutation rollbacka l'intera UoW.

Quando una race richiede retry/convergence, il retry riguarda normalmente la **semantic UoW completa**, non un frammento repository interno che potrebbe usare state stale.

Whole-lineage delete verification + cleanup è una sola transaction.

Lifecycle DB-generated identity/timestamp appartengono alla stessa transaction della mutation.

---

## 4. Isolation strategy — PERSIST-18

Default mutation isolation M1:

```text
READ COMMITTED
```

Strong consistency non viene ottenuta usando globalmente `SERIALIZABLE`, ma combinando:

- row locks espliciti con strength coerente al predicate;
- exact uniqueness/PK authority;
- foreign-key lifetime authority;
- optimistic draft generation checks;
- logical advisory gates per i pochi predicate globali;
- re-read dei predicate dopo stabilization.

### 4.1 Regola READ COMMITTED

Ogni mutation UoW deve possedere un punto di stabilization appropriato.

Dopo aver acquisito il lock/gate, il predicate rilevante viene letto o ri-letto. Non si committa in base a candidate state derivato esclusivamente da una pre-lock read.

### 4.2 Read-only

Ordinary single-statement reads usano READ COMMITTED.

Composite multi-statement read che richiede uno snapshot coerente può usare:

```text
REPEATABLE READ READ ONLY
```

quando non è ragionevole esprimere la read in un'unica coherent SQL statement.

`REPEATABLE READ` non è il default delle mutation.

### 4.3 SERIALIZABLE

Non fa parte del baseline M1.

Un futuro uso per specifiche UoW richiede decisione esplicita e retry contract esplicito.

---

## 5. Lock semantics comuni — PERSIST-19

### 5.1 Mutation owner strength

Quando una persisted row è il concurrency owner di una mutable state transition che **non elimina la row e non modifica una referenced key**, il baseline primitive è:

```text
SELECT ... FOR NO KEY UPDATE
```

Quando la mutation elimina la row o modifica una referenced key/identity, il baseline primitive è:

```text
SELECT ... FOR UPDATE
```

Razionale del refinement REALIZE-15:

- owner writer sulla stessa row restano mutuamente esclusivi;
- `FOR SHARE` lifecycle admission continua a confliggere con non-key state writers;
- una pure referential key-share protection può coesistere con una non-key mutation owner;
- non si usa una lock strength più forte del safety predicate richiesto.

Questa distinzione cambia il PostgreSQL mechanism strength, non la concurrency authority semantica.

### 5.2 Lifecycle-sensitive dependency admission

Quando una mutation crea/certifica un nuovo exact binding verso una dependency che deve restare PUBLISHED fino al commit:

```text
SELECT ... FOR SHARE
```

sulla exact dependency row.

`FOR KEY SHARE` non è sufficiente perché deve bloccare un concurrent non-key status UPDATE/deprecation.

### 5.3 Re-read rule

Dopo eventuale lock wait:

> il caller deve ri-leggere e ri-validare il predicate; non può fidarsi di una cached pre-lock observation.

### 5.4 Deterministic multi-row order

Quando una UoW deve acquisire lock su un equivalente set di più exact rows, l'ordine deve essere deterministico.

Per model dependencies la realization usa una canonical resource key concettuale:

```text
(kind, lineage_uuid, resource_rank, version)
```

con lineage header prima della exact version quando entrambe appartengono alla stessa resource lineage.

Non viene introdotto un artificiale global lock hierarchy cross-domain oltre ai casi esplicitamente richiesti.

Deadlock detection resta fallback di sicurezza/retry, non meccanismo di serializzazione normale.

---

## 6. DataType/ObjectTemplate locking baseline

### 6.1 Create-next / version allocation

Concurrency owner:

```text
stable lineage header FOR NO KEY UPDATE
```

per stabilizzare:

- current version set;
- `max(existing)+1` allocation;
- source eligibility rispetto al coherent current set.

### 6.2 Draft mutation

Exact DTV/OTV DRAFT row è mutation owner.

Per `REVISE` e `PUBLISH`:

```text
exact DRAFT FOR NO KEY UPDATE
```

Per `DELETE_DRAFT`, dopo la lineage owner lock richiesta da `S-VERSION-SET`:

```text
lineage header FOR NO KEY UPDATE
    -> exact DRAFT FOR UPDATE
```

perché la target row viene eliminata.

Dopo l'owner lock si verifica:

```text
status == DRAFT
revision == expected_revision
```

Il loser non riapplica automaticamente il proprio intent su una nuova generation.

### 6.3 Set default

Ordering baseline:

```text
lineage header FOR NO KEY UPDATE
    -> target exact version FOR SHARE
    -> recheck target PUBLISHED
```

### 6.4 Clear default

```text
lineage header FOR NO KEY UPDATE
```

### 6.5 Implicit default binding

```text
lineage header FOR SHARE
    -> resolve default_version
    -> target exact version FOR SHARE
    -> recheck PUBLISHED
```

Il resulting persisted binding è sempre exact.

### 6.6 Explicit new binding

```text
target exact version FOR SHARE
```

con PUBLISHED recheck prima del commit.

### 6.7 Publish OTV consumer

PUBLISH acquisisce sempre:

```text
consumer lineage header FOR NO KEY UPDATE
    -> exact DRAFT OTV FOR NO KEY UPDATE
```

per default policy + draft lifecycle/generation.

Dopo candidate/freshness validation, ogni **direct lifecycle-sensitive exact dependency** viene stabilizzata con `FOR SHARE` in deterministic resource order e ri-validata PUBLISHED.

Non si locka transitivamente l'intera dependency closure: il direct published graph invariant è sufficiente.

### 6.8 Deprecate exact version

Baseline ordering:

```text
lineage header FOR SHARE
    -> exact version FOR NO KEY UPDATE
    -> recheck lifecycle/default blockers
    -> reverse direct active-consumer validation
```

Il mechanism specifico di reverse lookup usa le authority rows/indices del persistence model; non viene materializzato un reverse-dependency aggregate.

### 6.9 Whole-lineage delete

```text
lineage header FOR UPDATE
```

La UoW esegue semantic precondition checks e cleanup owned state.

Le cross-aggregate FK `RESTRICT` restano la final race authority contro una reference che vincesse concorrentemente.

---

## 7. Object locking baseline

L'Object row è concurrency owner del complete current intrinsic state.

Per:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
```

baseline:

```text
Object row FOR NO KEY UPDATE
```

Per:

```text
DELETE
```

baseline:

```text
Object row FOR UPDATE
```

Questo preserva la serial composability del complete intrinsic state/lifecycle snapshots senza trasformare non-key Object mutation in un blocco referentiale più forte del necessario.

Dopo il lock la UoW ricarica il complete current Object state e deriva/rivalida la candidate da quello state.

### SCHEMA_CHANGE target

Dopo Object owner lock:

```text
target exact OTV FOR SHARE
```

per la new-binding admission.

La migration viene derivata/rivalidata rispetto alla current Object state osservata dopo il lock.

---

## 8. Ownership locking baseline

### 8.1 Parent concurrency owner

M1 usa la parent Object row come concurrency owner per:

```text
ATTACH(parent)
DETACH(parent)
SCHEMA_CHANGE(parent)
```

quindi:

```text
parent Object FOR NO KEY UPDATE
```

serializza il current exact parent schema e il parent outgoing ownership edge set.

Questa scelta può over-serializzare semanticamente independent mutation sulla stessa Object row, per esempio `RENAME(parent)` vs `ATTACH(parent)`. L'over-serialization è accettata in M1 per semplicità e deve risultare visibile confrontando semantic e realization matrix.

### 8.2 ATTACH

Sequenza concettuale:

```text
parent FOR NO KEY UPDATE
-> validate current slot / child stable compatibility
-> inspect current child ownership
-> fast exit on exact no-op or ownership conflict
-> ownership graph edge-add gate
-> fresh post-gate child-ownership read
-> cycle check on protected committed graph
-> insert edge + event
-> commit
```

Il child non viene genericamente row-lockato per ATTACH:

- `Object.template_id` è stable;
- child PK sull'ownership table è final single-owner authority;
- Object FK gestisce DELETE race.

### 8.3 DETACH

DETACH usa il parent owner domain ma **non** acquisisce il graph-wide cycle gate, perché rimuovere un edge non può introdurre un ciclo.

### 8.4 Ownership structural-event display metadata

Per `ATTACH_TO`/`DETACH_FROM`, il parent display name proviene dalla parent row già stabilizzata; il child canonical name è historical display metadata letto come committed observation dopo parent stabilization, senza child lock introdotto soltanto per l'evento.

---

## 9. RelationshipDefinition locking baseline

### 9.1 CREATE

CREATE modifica il global certified Definition set e usa il global conflict gate definito in PERSIST-20.

La complete candidate shape/equivalence/conflict predicate viene letto/ri-letto dopo gate acquisition prima del commit.

### 9.2 RENAME

Baseline:

```text
specific Definition header FOR NO KEY UPDATE
    -> global RelationshipDefinition conflict gate
    -> fresh read of complete Definition/global candidate conflicts
    -> atomic complete Resolution-name update
```

RENAME modifica non-key semantic metadata e non usa `FOR UPDATE` soltanto perché la Definition è referenced da factual Relationship.

### 9.3 DELETE

```text
Definition header FOR UPDATE
```

DELETE non acquisisce il global conflict gate perché può soltanto rimuovere Definition/Resolution dal certified conflict set, non introdurre un nuovo conflict.

Current factual Relationship FK `RESTRICT` è final lifetime race authority.

---

## 10. Runtime Relationship locking/convergence baseline

### 10.1 CREATE

Non esiste una pre-existing factual header row affidabile da usare come universal lock owner per equivalent concurrent create.

Quindi M1 non introduce un global Relationship graph lock.

Pipeline concettuale:

```text
load selected Resolution + endpoint Objects
validate stable endpoint admission
lookup exact runtime view
if present -> converge/no-op
else derive complete candidate closure
exact-deduplicate + canonical-sort closure rows
attempt aggregate insert
```

Final collision authority:

```text
PRIMARY KEY (
  resolution_id,
  from_object_id,
  to_object_id
)
```

su `runtime_relationship_resolutions`.

Concurrent equivalent CREATE:

- un candidate UoW vince;
- l'altro può ricevere unique/PK collision;
- la failed candidate transaction viene rollbackata integralmente;
- la semantic operation riparte in una fresh UoW e rivaluta il current exact view;
- se il winner è ancora current converge sulla winner Relationship; se è già stato eliminato può creare una nuova factual identity.

Nessun duplicate factual header o duplicate lifecycle creation event set è ammesso.

### 10.2 DELETE

Concurrency owner:

```text
Relationship header FOR UPDATE
```

perché la row viene eliminata.

Dopo il lock si ricaricano:

- complete runtime closure;
- required semantic-view deletion event set.

Una real DELETE elimina child closure + header + complete event set atomicamente.

Concurrent secondo DELETE trova l'aggregate assente e converge come idempotent no-op.

### 10.3 CREATE vs DELETE / ABA

La semantic correctness resta exact-identity based:

- late `DELETE(X)` può eliminare solo X;
- recreating same semantic association crea Y;
- late DELETE X non può eliminare Y.

---

## 11. Relationship lifecycle metadata snapshot

RelationshipDefinition `RENAME` non deve genericamente serializzare runtime Relationship mutation: rename non cambia structural Resolution identity, endpoint spaces o factual closure.

Analogamente, Object canonical names negli Relationship event sono historical display metadata: runtime Relationship mutation non deve genericamente serializzare con `Object.RENAME` soltanto per tali fields.

La concrete `S-REL-EVENT-SNAPSHOT` realization è:

> una singola real Relationship factual transition ottiene l'intero semantic lifecycle event projection da **un solo SQL metadata-observation statement** a `READ COMMITTED`.

Lo statement osserva nello stesso MVCC snapshot tutti i required Resolution names e source/destination Object canonical names. Non prende `FOR SHARE`/`FOR UPDATE` soltanto per metadata storica.

Per CREATE la observation avviene dopo la complete runtime closure insertion riuscita; per DELETE prima della closure removal. La semantic-view dedup può avvenire nella stessa query. Metadata mutation dopo tale observation ma prima del factual commit non invalida il captured event set.

`occurred_at = transaction_timestamp()` resta transaction-start time e non timestamp del metadata observation, commit time o global ordering authority.

---

## 12. Logical gates — PERSIST-20

M1 usa PostgreSQL **exclusive transaction-level advisory locks**:

```text
pg_advisory_xact_lock(...)
```

Non vengono usati session-level advisory lock e non esiste manual release: il lock segue la transaction lifetime.

Esistono due risorse logiche distinte:

```text
OWNERSHIP_GRAPH_WRITE_GATE
RELATIONSHIP_DEFINITION_CONFLICT_GATE
```

La key strategy è centralizzata e nominata, concettualmente come namespace NETAUTO + resource key. Non si usano runtime string hash sparsi nel codice.

### 12.1 Fresh-snapshot rule comune

Per ogni blocking logical gate:

```text
statement 1:
    SELECT pg_advisory_xact_lock(...)

statement 2+:
    read/re-read protected predicate
```

Acquisition e authoritative protected read sono statement separati. A `READ COMMITTED`, il post-wait predicate deve essere osservato con un fresh statement snapshot che includa lo state committed dal precedente gate holder.

Il gate è stabilization mechanism; il committed protected row set resta l'authority.

### 12.2 OWNERSHIP_GRAPH_WRITE_GATE

Acquisito soltanto da operation `ATTACH` che aggiungono realmente un ownership edge.

Protected critical phase:

```text
acquire gate
-> fresh re-read child ownership
-> fresh graph read / cycle validation
-> edge add + event
-> commit
```

`DETACH` non acquisisce il gate.

Normal read non acquisisce il gate.

### 12.3 RELATIONSHIP_DEFINITION_CONFLICT_GATE

Acquisito da:

```text
RelationshipDefinition.CREATE
RelationshipDefinition.RENAME
```

Protected phase:

```text
acquire gate
-> fresh re-read global certified set
-> validate equivalence/conflicts
-> commit candidate mutation
```

`RelationshipDefinition.DELETE` non acquisisce il gate.

### 12.4 Discipline

Advisory-lock correctness è application contract:

> ogni kernel mutation capace di cambiare il protected predicate deve passare dalla central persistence capability che acquisisce il gate.

Le gate operation devono essere centralizzate e non duplicate come magic SQL.

M1 non possiede una semantic UoW che necessiti entrambi i global gate. Se una futura operation li richiede, deve prima definire un explicit gate ordering contract.

Blocking acquisition è il semantic path baseline, non try-lock polling.

I gate sono osservabili operationally tramite `pg_locks`.

---

## 13. Concurrency realization matrix — stato normativo

La PostgreSQL realization matrix è distribuita nei documenti:

```text
concurrency-postgresql-realization-matrix.md
concurrency-postgresql-realization-object-ownership.md
concurrency-postgresql-realization-relationship.md
```

REALIZE-01..REALIZE-15 hanno identificato per tutti i 19 safety predicate M1:

```text
semantic scope
required outcome
concurrency authority
physical authority
PostgreSQL mechanism
revalidation point
retry/convergence behavior
required real-PG test family
```

Regola forte:

> se una non-trivial semantic matrix cell non può essere ricondotta a una concrete authority/mechanism e a un real PostgreSQL concurrency test, il concurrency design non è chiuso.

La realization matrix rende inoltre esplicita l'**over-serialization tecnica** quando una semantic `I` cell può comunque attendere per una scelta implementativa M1.

Esempi intenzionali ancora presenti:

```text
OBJ.RENAME(P) × OBJ.ATTACH(P,S,C)
    -> same parent Object non-key owner

unrelated real ownership ATTACH × ATTACH
    -> global ownership graph gate

unrelated RD.CREATE/RENAME
    -> global Definition conflict gate
```

REALIZE-15 elimina invece over-serialization puramente accidentale dovuta all'uso indiscriminato di `FOR UPDATE` per mutation non-key.

---

## 14. Traceability e test derivation

Traceability normativa:

```text
Invariant
    -> semantic matrix cell
    -> safety predicate
    -> persistence authority
    -> concrete PostgreSQL mechanism
    -> real PostgreSQL concurrency test
```

Ogni non-trivial semantic cell deve generare almeno un test race rappresentativo o essere coperta esplicitamente da una test family equivalente.

Ogni futura mutation M1/M2 deve essere aggiunta alla semantic operation census e comparata con tutte le mutation esistenti **prima** di dichiararne completo il concurrency design.

Il passo successivo alla complete realization è derivare e congelare la **PostgreSQL concurrency test matrix**, senza introdurre nuove semantic decision salvo che un test design riveli un gap reale.
