# M1 — PostgreSQL Concurrency Realization Matrix

**Status:** DRAFT — REALIZE-01..REALIZE-07 ratificati; il documento viene esteso predicate-by-predicate.

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

Per singolo entity kind:

```text
datatypes         UNIQUE(namespace, name)
object_templates  UNIQUE(namespace, name)
```

La UNIQUE è sia structural authority sia concurrency arbiter.

### 3.1 CREATE × CREATE stesso qualified name

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

### 3.2 CREATE × DELETE_LINEAGE con riuso del nome

La stessa UNIQUE arbitra il riuso del qualified name. Se la delete committa per prima, la nuova lineage può acquisire il nome con una nuova UUID identity; se la vecchia row resta current, la CREATE non può committare. Non si usa advisory/name lock.

### 3.3 Required PostgreSQL tests

Almeno:

1. concurrent CREATE same name -> esattamente un current owner;
2. CREATE same name vs successful lineage delete -> outcome serialmente valido;
3. CREATE same name vs failed/rolled-back lineage delete -> CREATE non bypassa la UNIQUE.

---

## 4. REALIZE-02 — `S-VERSION-SET` (`VS`)

La **stable lineage header row** è il concurrency owner del current version membership/allocation set.

> Ogni supported M1 mutation che aggiunge o rimuove una current version della lineage acquisisce la lineage header `FOR UPDATE` prima di modificare il set.

In M1:

```text
CREATE_NEXT
DELETE_DRAFT
```

### 4.1 CREATE_NEXT

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

La source PUBLISHED/DEPRECATED non richiede exact-row lock soltanto per `CREATE_NEXT`: è strutturalmente immutable, non è individualmente deletable e `PUBLISHED -> DEPRECATED` non cambia la source eligibility. Whole-lineage delete è esclusa dal lineage-header lock.

### 4.2 DELETE_DRAFT

`DELETE_DRAFT` partecipa a due concurrency domain:

```text
lineage header -> S-VERSION-SET
exact DRAFT    -> S-DRAFT-GENERATION
```

Ordering:

```text
lineage header FOR UPDATE
-> exact DRAFT row FOR UPDATE
-> recheck status == DRAFT
-> recheck revision == expected_revision
-> DELETE
```

### 4.3 Lock ordering

Quando una mutation necessita sia della stable lineage row sia di una exact version row:

```text
lineage row -> exact version row
```

mai il contrario.

### 4.4 CREATE_NEXT × CREATE_NEXT

Outcome `SERIALIZATION` sulla lineage header. Dopo il wait si ricalcolano max e source eligibility. Entrambe possono riuscire in sequenza, per esempio creando `v3` e poi `v4`, se la source resta ammissibile.

### 4.5 CREATE_NEXT × DELETE_DRAFT

Entrambe acquisiscono la stessa lineage header `FOR UPDATE`. Se CREATE_NEXT vince, può allocare rispetto al pre-delete set; se DELETE_DRAFT vince, CREATE_NEXT rivaluta max/source eligibility sul nuovo set e può diventare non ammissibile.

### 4.6 Intentional over-serialization

Due `DELETE_DRAFT` di exact DRAFT differenti della stessa lineage vengono serializzate sulla lineage header per mantenere una sola authority semplice del current version membership.

### 4.7 Required PostgreSQL tests

1. CREATE_NEXT × CREATE_NEXT stessa lineage;
2. CREATE_NEXT(source older) × DELETE_DRAFT(max), entrambi gli ordini;
3. DELETE_DRAFT(vA) × DELETE_DRAFT(vB) stessa lineage;
4. verifica lock order `lineage -> exact`.

---

## 5. REALIZE-03 — `S-DRAFT-GENERATION` (`DG`) e `S-LIFECYCLE-STATE` (`LS`)

La exact DTV/OTV row è il concurrency owner di:

```text
exact DRAFT generation
exact lifecycle state
```

Per DTV l'identity è `(datatype_id, version)`; per OTV `(template_id, version)`.

Le exact rows vengono stabilizzate con `FOR UPDATE` prima di mutation che cambiano `revision`, `status` o l'esistenza della DRAFT. Il DB `CHECK` limita il vocabolario dello status; monotonicità e transition admission restano UoW-enforced.

### 5.1 Common DRAFT mutation pipeline

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

### 5.2 Same-generation races

- `REVISE × REVISE`: il primo porta `N -> N+1`; il secondo fallisce freshness.
- `REVISE × PUBLISH`: revise-first rende stale il publish; publish-first rende la revise non più DRAFT.
- `REVISE × DELETE_DRAFT`: revise-first cambia generation; delete-first rimuove il target.
- `PUBLISH × DELETE_DRAFT`: publish-first rende la row non deletable; delete-first rimuove la generation.
- `PUBLISH × PUBLISH`: una sola real transition `DRAFT -> PUBLISHED`.

Il loser non riapplica automaticamente il proprio intent sul nuovo state.

### 5.3 DEPRECATE

`DEPRECATE` stabilizza la exact version con `FOR UPDATE` e, dopo ogni wait, richiede current `status == PUBLISHED` prima di `PUBLISHED -> DEPRECATED`.

- `PUBLISH × DEPRECATE`: la exact-row authority impedisce transition incompatibili; eventuali blocker `DV`/`AM` si compongono.
- `DEPRECATE × DEPRECATE`: una sola real transition; la seconda osserva DEPRECATED.

La public error/idempotency mapping resta nel failure/API contract.

### 5.4 Rejected alternative: CAS-only

Non si adotta come modello generale un solo conditional `UPDATE ... WHERE status='DRAFT' AND revision=:expected`. OTV è aggregate multi-row e DTV/OTV mantengono un modello simmetrico basato su exact-root `FOR UPDATE` + recheck.

### 5.5 Required PostgreSQL tests

1. REVISE × REVISE same generation;
2. REVISE × PUBLISH;
3. REVISE × DELETE_DRAFT;
4. PUBLISH × DELETE_DRAFT;
5. PUBLISH × PUBLISH same DRAFT;
6. DEPRECATE × DEPRECATE same version;
7. PUBLISH × DEPRECATE same exact version;
8. OTV revise non produce mixed child-declaration candidate.

---

## 6. REALIZE-04 — `S-DEFAULT-VALIDITY` (`DV`)

La stable lineage header è il concurrency owner dell'intera default policy. La physical authority è composta da:

```text
lineage header      -> current default_version
exact version row   -> lifecycle status della target
```

### 6.1 Lock set

```text
PUBLISH
    lineage FOR UPDATE
    -> exact DRAFT FOR UPDATE

SET_DEFAULT
    lineage FOR UPDATE
    -> target exact version FOR SHARE

CLEAR_DEFAULT
    lineage FOR UPDATE

DEPRECATE
    lineage FOR SHARE
    -> exact version FOR UPDATE
```

`PUBLISH` prende **sempre** la lineage `FOR UPDATE`, anche quando il default sembra già non-NULL. Questo evita lock upgrade/path condizionali e rende first-publish auto-default serialmente semplice. È intentional M1 over-serialization fra publish di DRAFT diverse della stessa lineage.

`DEPRECATE` usa lineage `FOR SHARE`: non modifica il default ma deve impedirne una concurrent mutation mentre verifica che la target non sia current default. Più deprecation di exact version differenti possono quindi coesistere al lineage-lock level.

### 6.2 Revalidation

Ogni decisione relativa al default viene presa solo dopo il lineage lock:

```text
acquire lineage lock
-> read/re-read default_version
-> acquire exact target lock if required
-> re-read target status
-> decide
```

### 6.3 Race principali

- `PUBLISH(v2) × PUBLISH(v3)` con default NULL: entrambi possono pubblicare, ma il first serial publisher diventa default; il secondo non sostituisce automaticamente.
- `PUBLISH × SET_DEFAULT`: serializzazione sulla lineage; explicit set può sostituire l'auto-default secondo l'ordine seriale.
- `PUBLISH × CLEAR_DEFAULT`: final state dipende dall'ordine seriale (`default=v` oppure `NULL`).
- `SET_DEFAULT(v) × DEPRECATE(v)`: mai `default=v` con `v=DEPRECATED`.
- `CLEAR_DEFAULT × DEPRECATE(current default)`: clear-first può rendere la deprecate ammissibile; deprecate-first può fallire conservativamente.
- `SET_DEFAULT(v2) × SET_DEFAULT(v3)`: last serial writer determina il default.

### 6.4 Required PostgreSQL tests

1. PUBLISH(v2) × PUBLISH(v3), default NULL;
2. stessa race con default già valorizzato;
3. PUBLISH × SET_DEFAULT;
4. PUBLISH × CLEAR_DEFAULT;
5. SET_DEFAULT(v) × DEPRECATE(v);
6. CLEAR_DEFAULT × DEPRECATE(current default);
7. SET_DEFAULT(v2) × SET_DEFAULT(v3);
8. PUBLISH × DEPRECATE same exact (`DV + LS`);
9. due DEPRECATE di version differenti verificano parallelismo al lineage-lock level;
10. lock order `lineage -> exact`.

---

## 7. REALIZE-05 — `S-BINDING-ADMISSION` (`BA`)

Ogni exact dependency lifecycle-sensitive nuova o ribindata deve essere PUBLISHED dopo stabilization e restarlo fino al commit della mutation consumer.

M1 copre:

```text
OTV -> exact parent OTV
ObjectTemplateProperty -> exact DTV
Object -> exact OTV
```

Non copre lineage-level component target o RelationshipResolution endpoint.

### 7.1 Explicit binding

```text
exact dependency row FOR SHARE
-> re-read status
-> require PUBLISHED
-> materialize/use exact pin
-> hold through consumer commit
```

Non serve la dependency lineage header soltanto per BA.

### 7.2 Implicit default binding

```text
dependency lineage header FOR SHARE
-> read/re-read default_version
-> require non-NULL
-> target exact version FOR SHARE
-> re-read target status
-> require PUBLISHED
-> materialize exact version
-> hold locks through commit
```

La header stabilizza la selection; la exact row stabilizza l'admissibility.

### 7.3 Candidate semantics

Per `OT.CREATE/REVISE`, BA si applica solo ai binding **nuovi o ribindati**. Historical pin invariati non vengono ricertificati; possono diventare DEPRECATED e lasciare la DRAFT well-formed ma non publishable.

`CREATE_NEXT` clone non esegue BA lock/certification e può clonare historical DEPRECATED dependencies.

### 7.4 Deterministic dependency-resource order

Per più dependency resources:

```text
(kind, lineage_uuid, resource_rank, version)
```

con:

```text
resource_rank 0 = lineage header
resource_rank 1 = exact version
```

quindi header prima di exact per la stessa lineage. Le dependency lineages sono processate in canonical order; per implicit resolution la target exact version viene risolta dopo il lock della header.

### 7.5 Separate consumer/dependency authorities

Esempi:

```text
OBJ.SCHEMA_CHANGE
    objects(O) FOR UPDATE           -> current Object state
    target OTV FOR SHARE            -> BA

OT.REVISE
    exact DRAFT OTV FOR UPDATE      -> DG
    new dependency FOR SHARE        -> BA
```

BA non sostituisce il consumer owner.

### 7.6 Required PostgreSQL tests

1. explicit binding × target deprecate;
2. implicit binding × SET_DEFAULT;
3. implicit binding × CLEAR_DEFAULT;
4. implicit binding × first PUBLISH auto-default;
5. implicit binding × deprecate target;
6. OT.REVISE multi-dependency canonical order;
7. unchanged dependency × deprecate -> revise può riuscire e DRAFT diventare nonpublishable;
8. CREATE_NEXT clone DEPRECATED dependency;
9. OBJ.SCHEMA_CHANGE × target OTV.DEPRECATE;
10. OBJ.CREATE explicit/implicit target × deprecate;
11. rollback non lascia partial binding.

---

## 8. REALIZE-06 — `S-ACTIVE-MODEL` (`AM`)

La exact dependency row è il rendezvous point tra chi **attiva** un nuovo PUBLISHED consumer edge e chi prova a deprecare la dependency.

### 8.1 Activation side — OTV PUBLISH

Dopo i propri owner lock, `OT.PUBLISH`:

```text
-> derive complete set of direct lifecycle-sensitive exact dependencies
-> lock every direct dependency FOR SHARE in deterministic order
-> re-read every dependency status
-> require all PUBLISHED
-> publish consumer
-> hold dependency locks through commit
```

Direct dependencies M1:

```text
exact parent OTV
exact DTV of every effective property
```

Component target lineage non partecipa. Nessun lock transitivo della closure.

### 8.2 Dependency side — DEPRECATE

```text
dependency lineage FOR SHARE
-> dependency exact version FOR UPDATE
-> re-read status/default blockers
-> reverse lookup direct PUBLISHED consumers
-> fail if any current blocker
-> otherwise status = DEPRECATED
```

La exact dependency `FOR UPDATE` impedisce che un nuovo publisher completi dopo un reverse lookup che ha visto zero blocker: ogni publisher corretto necessita `FOR SHARE` sulla stessa dependency.

### 8.3 Reverse lookup without reverse consumer locks

Le reverse consumer rows **non vengono lockate**. Consumer removal (`OT.DEPRECATE`, `OT.DELETE_LINEAGE`) è monotona rispetto alla deprecation della dependency: se non è ancora committed, il deprecator può vedere ancora il blocker e fallire conservativamente. Non serve un reverse-lock fan-out.

Questo evita di lockare migliaia di consumer solo per attendere rimozioni che possono unicamente rendere il predicate più permissivo.

### 8.4 Physical lookup paths

DTV reverse lookup usa `object_template_properties(datatype_id, datatype_version)` + owning OTV status.

Parent OTV reverse lookup usa `object_template_versions(parent_template_id, parent_version)` + child OTV status.

Non esiste reverse-dependency authority table.

### 8.5 No global active-model gate

M1 non introduce `ACTIVE_MODEL_GRAPH_WRITE_GATE`. Gli unici global advisory gate restano quelli già ratificati per ownership acyclicity e RelationshipDefinition conflict set.

### 8.6 Required PostgreSQL tests

1. OT.PUBLISH(property->DTV) × DTV.DEPRECATE;
2. child OT.PUBLISH × parent OTV.DEPRECATE;
3. publisher-first -> deprecator vede nuovo PUBLISHED consumer;
4. deprecator-first -> publisher vede DEPRECATED;
5. consumer DEPRECATE × dependency DEPRECATE, consumer commit first;
6. stessa race con dependency reverse lookup prima del consumer commit -> conservative failure ammesso;
7. child deprecate × parent deprecate;
8. consumer lineage DELETE × dependency DEPRECATE;
9. publish multi-dependency + una concurrent deprecation -> all-or-nothing;
10. verifica no transitive dependency locks;
11. reverse lookup senza reverse `FOR UPDATE`;
12. publisher iniziato dopo reverse lookup ma prima del deprecate commit resta bloccato e poi fallisce;
13. rollback deprecator sblocca publisher correttamente;
14. rollback publisher non crea active blocker.

---

## 9. REALIZE-07 — `S-REFERENCE-LIFETIME` (`RL`)

La FK current-state `ON DELETE RESTRICT` è la final concurrency authority per ogni cross-aggregate/current-domain lifetime dependency rappresentabile relazionalmente.

### 9.1 General pattern

```text
reference creation/update
    -> current FK nella stessa atomic write UoW

target DELETE
    -> physical delete della referenced row

FK RESTRICT
    -> final arbitration
```

Outcome:

```text
reference wins -> target DELETE cannot commit
target DELETE wins -> new reference cannot commit
```

Classification:

```text
Required outcome     REFERENTIAL
Concurrency authority current cross-aggregate reference graph
Physical authority   FOREIGN KEY ... ON DELETE RESTRICT
RL-only app lock      none
```

Semantic precheck sono ammessi per error quality ma non sono race-authoritative.

### 9.2 Immediate current-state FKs

Le FK current-state cross-aggregate M1 sono **NOT DEFERRABLE**. M1 non richiede UoW che debbano committare passando temporaneamente da dangling current references.

### 9.3 No generic target lock solely for RL

RL non introduce generic `SELECT target FOR SHARE`. Una operation può già lockare lo stesso target per altri predicate (`BA`, `PO`, ecc.), ma la lifetime authority resta la FK.

### 9.4 Removal races

Reference removal non richiede special target coordination. Se removal committa prima, la target delete può diventare ammissibile; se il target delete vede ancora il blocker può fallire conservativamente. Nessun implicit cleanup viene introdotto.

### 9.5 CASCADE internal / RESTRICT external

`CASCADE` resta limitato root -> owned child state dello stesso aggregate; external/current references sono `RESTRICT`. Il CASCADE pulisce owned state **dopo** che la root delete è ammessa e non bypassa external blockers.

### 9.6 Direct persisted references only

Le FK riflettono le direct authority references realmente persistite, non dependency transitive. Per esempio Object->OTV->DTV non produce Object->DTV FK; Relationship->Object non produce Relationship->ObjectTemplate-lineage FK.

### 9.7 Failure/retry

Una expected FK arbitration loss deve essere traducibile in una domain failure significativa, distinguibile da corruption/internal DB errors. Genuine reference-vs-delete loss non viene automaticamente ritentata.

### 9.8 Required PostgreSQL tests

1. OBJ.CREATE × OT.DELETE_LINEAGE;
2. OBJ.DELETE × OT.DELETE_LINEAGE;
3. ATTACH × OBJ.DELETE(parent);
4. ATTACH × OBJ.DELETE(child);
5. DETACH × OBJ.DELETE;
6. REL.CREATE × OBJ.DELETE, entrambi endpoint;
7. REL.DELETE × OBJ.DELETE;
8. REL.CREATE × RD.DELETE;
9. REL.DELETE × RD.DELETE;
10. RD.CREATE × OT.DELETE_LINEAGE;
11. RD.DELETE × OT.DELETE_LINEAGE;
12. OT.REVISE new DTV ref × DT.DELETE_LINEAGE;
13. OT.DELETE_DRAFT × DT.DELETE_LINEAGE;
14. OT.DELETE_LINEAGE consumer × DT.DELETE_LINEAGE;
15. exact parent reference × parent lineage delete;
16. reference INSERT durante target DELETE;
17. target DELETE durante uncommitted reference INSERT;
18. reference removal concorrente con target DELETE;
19. owned CASCADE non bypassa external RESTRICT;
20. verifica che nessuna current FK M1 richieda deferred behavior.

---

## 10. Traceability rule

Ogni successivo REALIZE point deve aggiornare questa catena:

```text
semantic predicate / scoped matrix cell
-> authority
-> PostgreSQL mechanism
-> loser/retry behavior
-> required real-PG concurrency test
```

Nessuna futura mutation è concurrency-designed finché non viene confrontata con il census completo della semantic matrix e non viene aggiunta anche a questo livello di realization.
