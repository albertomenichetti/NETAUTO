# M1 — PostgreSQL Unit of Work & Concurrency Realization Baseline

**Status:** DRAFT — decisioni PERSIST-16..PERSIST-20 ratificate; complete realization matrix ancora da consolidare dopo la semantic matrix.

## 1. Scopo

Questo documento definisce il baseline tecnico PostgreSQL già ratificato per:

- enforcement boundary DB vs Unit of Work;
- semantic transaction boundary;
- isolation level;
- row-lock ownership e ordering;
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

- row locks espliciti;
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

### 5.1 Mutation owner

Quando una persisted row è il concurrency owner della mutable state transition:

```text
SELECT ... FOR UPDATE
```

è il baseline primitive.

### 5.2 Lifecycle-sensitive dependency admission

Quando una mutation crea/certifica un nuovo exact binding verso una dependency che deve restare PUBLISHED fino al commit:

```text
SELECT ... FOR SHARE
```

sulla exact dependency row.

`FOR KEY SHARE` non è sufficiente perché deve bloccare un concurrent status UPDATE/deprecation.

### 5.3 Re-read rule

Dopo eventuale lock wait:

> il caller deve ri-leggere e ri-validare il predicate; non può fidarsi di una cached pre-lock observation.

### 5.4 Deterministic multi-row order

Quando una UoW deve acquisire lock su un equivalente set di più exact rows, l'ordine deve essere deterministico.

Per model dependencies il baseline ordering key concettuale è:

```text
(kind, lineage_uuid, version)
```

Non viene introdotto un artificiale global lock hierarchy cross-domain oltre ai casi esplicitamente richiesti.

Deadlock detection resta fallback di sicurezza/retry, non meccanismo di serializzazione normale.

---

## 6. DataType/ObjectTemplate locking baseline

### 6.1 Create-next / version allocation

Concurrency owner:

```text
stable lineage header FOR UPDATE
```

per stabilizzare:

- current version set;
- `max(existing)+1` allocation;
- source eligibility rispetto al coherent current set.

### 6.2 Draft mutation

Exact DTV/OTV DRAFT row è mutation owner:

```text
FOR UPDATE
```

poi si verifica:

```text
status == DRAFT
revision == expected_revision
```

per `REVISE`, `PUBLISH`, `DELETE_DRAFT`.

### 6.3 Set default

Ordering baseline:

```text
lineage header FOR UPDATE
    -> target exact version FOR SHARE
    -> recheck target PUBLISHED
```

### 6.4 Clear default

```text
lineage header FOR UPDATE
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

DRAFT OTV row è mutation owner `FOR UPDATE`.

Dopo candidate/freshness validation, ogni **direct lifecycle-sensitive exact dependency** viene stabilizzata con `FOR SHARE` in deterministic order e ri-validata PUBLISHED.

Non si locka transitivamente l'intera dependency closure: il direct published graph invariant è sufficiente.

### 6.8 Deprecate exact version

Baseline ordering:

```text
lineage header FOR SHARE
    -> exact version FOR UPDATE
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

L'Object row è concurrency owner per le intrinsic/current-state mutation:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
DELETE
```

Baseline:

```text
Object row FOR UPDATE
```

Questo garantisce la serial composability del complete intrinsic state/lifecycle snapshots.

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
parent Object FOR UPDATE
```

serializza il current exact parent schema e il parent outgoing ownership edge set.

Questa scelta può over-serializzare semanticamente independent mutation sulla stessa Object row, per esempio `RENAME(parent)` vs `ATTACH(parent)`. L'over-serialization è accettata in M1 per semplicità e deve risultare visibile confrontando semantic e realization matrix.

### 8.2 ATTACH

Sequenza concettuale:

```text
parent FOR UPDATE
-> validate current slot / child stable compatibility
-> ownership graph edge-add gate
-> cycle check on protected committed graph
-> insert edge
```

Il child non viene genericamente row-lockato per ATTACH:

- `Object.template_id` è stable;
- child PK sull'ownership table è final single-owner authority;
- Object FK gestisce DELETE race.

### 8.3 DETACH

DETACH usa il parent owner domain ma **non** acquisisce il graph-wide cycle gate, perché rimuovere un edge non può introdurre un ciclo.

---

## 9. RelationshipDefinition locking baseline

### 9.1 CREATE

CREATE modifica il global certified Definition set e usa il global conflict gate definito in PERSIST-20.

La complete candidate shape/equivalence/conflict predicate viene letto/ri-letto dopo gate acquisition prima del commit.

### 9.2 RENAME

Baseline:

```text
specific Definition header FOR UPDATE
    -> global RelationshipDefinition conflict gate
    -> re-read complete Definition/global candidate conflicts
    -> atomic complete Resolution-name update
```

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
- la failed candidate transaction viene rollbackata;
- la semantic operation viene ri-eseguita/ri-letta e converge sulla winner Relationship.

Nessun duplicate factual header o duplicate lifecycle creation event set è ammesso.

### 10.2 DELETE

Concurrency owner:

```text
Relationship header FOR UPDATE
```

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

La Relationship mutation deve però costruire `relationship_name` del complete lifecycle event set da un **coherent committed Definition snapshot**.

Analogamente, Object canonical names negli Relationship event sono historical display metadata: runtime Relationship mutation non deve genericamente serializzare con `Object.RENAME` soltanto per tali fields.

La complete event derivation deve osservare coherent committed metadata state secondo il predicate `S-REL-EVENT-SNAPSHOT` definito nella semantic matrix.

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

### 12.1 OWNERSHIP_GRAPH_WRITE_GATE

Acquisito soltanto da operation `ATTACH` che aggiungono un ownership edge.

Protected critical phase:

```text
acquire gate
-> re-read graph predicate as needed
-> cycle validation
-> edge add
```

`DETACH` non acquisisce il gate.

Normal read non acquisisce il gate.

### 12.2 RELATIONSHIP_DEFINITION_CONFLICT_GATE

Acquisito da:

```text
RelationshipDefinition.CREATE
RelationshipDefinition.RENAME
```

Protected phase:

```text
acquire gate
-> re-read global certified set
-> validate equivalence/conflicts
-> commit candidate mutation
```

`RelationshipDefinition.DELETE` non acquisisce il gate.

### 12.3 Discipline

Advisory-lock correctness è application contract:

> ogni kernel mutation capace di cambiare il protected predicate deve passare dalla central persistence capability che acquisisce il gate.

Le gate operation devono essere centralizzate e non duplicate come magic SQL.

M1 non possiede una semantic UoW che necessiti entrambi i global gate. Se una futura operation li richiede, deve prima definire un explicit gate ordering contract.

Blocking acquisition è il semantic path baseline, non try-lock polling.

I gate sono osservabili operationally tramite `pg_locks`.

---

## 13. Concurrency realization matrix — struttura normativa

La complete PostgreSQL realization matrix viene prodotta **dopo** il freeze della semantic matrix.

Per ogni non-trivial pairwise cell deve contenere almeno:

```text
semantic operation A
semantic operation B
scope qualifier
semantic safety predicate(s)
semantic independence vs required ordering
concurrency owner / authority
DB constraint / CAS / row lock / advisory gate
isolation assumption
retry/convergence behavior
required PostgreSQL concurrency test
```

Regola forte:

> se una non-trivial semantic matrix cell non può essere ricondotta a una concrete authority/mechanism e a un real PostgreSQL concurrency test, il concurrency design non è chiuso.

La realization matrix deve inoltre rendere esplicita l'**over-serialization tecnica** quando una semantic `I` cell può comunque attendere per una scelta implementativa M1.

Esempio già noto:

```text
OBJ.RENAME(P) × OBJ.ATTACH(P,S,C)
semantic: I
realization: può serializzare sulla stessa parent/Object row
```

---

## 14. Traceability e test derivation

Traceability desiderata:

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
