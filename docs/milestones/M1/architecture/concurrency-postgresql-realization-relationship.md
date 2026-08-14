# M1 — PostgreSQL Concurrency Realization: Relationship model/runtime

**Status:** DRAFT — REALIZE-12..REALIZE-15 ratificati; Relationship predicate realization completa e consistency sweep applicato.

Companion di `concurrency-postgresql-realization-matrix.md`. La catena normativa resta:

```text
semantic predicate
-> concurrency authority
-> physical authority
-> PostgreSQL mechanism
-> loser/retry behavior
-> real PostgreSQL concurrency test
```

---

## 1. REALIZE-12 — `S-RD-CERTIFIED-SET` (`RC`)

La authority è il current committed certified `RelationshipDefinition` set, composto da Definition headers + complete authoritative Resolution sets. La stable ObjectTemplate lineage ancestry partecipa alla semantica di endpoint-space overlap.

Il mechanism è l'exclusive transaction-level advisory lock:

```text
RELATIONSHIP_DEFINITION_CONFLICT_GATE
```

acquisito da `RD.CREATE` e `RD.RENAME`, non da `RD.DELETE`.

### 1.1 Fresh-snapshot rule dopo il gate

Gate acquisition e authoritative certified-set read sono sempre SQL statement separati:

```text
statement 1:
    SELECT pg_advisory_xact_lock(...)

statement 2+:
    read/re-read protected certified set
```

A `READ COMMITTED` questo garantisce che un waiter osservi con un nuovo snapshot lo state committed dal precedente gate holder. Il gate stabilizza i writer; non è esso stesso l'authority del certified set.

### 1.2 `RD.CREATE`

```text
local complete-candidate validation
-> acquire conflict gate
-> fresh certified-set read
-> semantic-equivalence check
-> global cross-Definition Resolution conflict check
-> insert Definition + complete Resolution set
-> commit while holding gate
```

Equivalence e conflict appartengono alla stessa protected critical section. Una sola Resolution conflicting fa fallire l'intera candidate Definition.

### 1.3 `RD.RENAME`

```text
Definition header FOR NO KEY UPDATE
-> load/re-read own complete aggregate
-> acquire conflict gate
-> fresh certified-set read
-> derive final renamed complete candidate
-> equivalence/conflict check excluding self
-> atomically update the complete relevant Resolution-name set
-> commit while holding gate
```

Same-Definition rename/delete lifetime resta serializzata dalla Definition header: RENAME usa il non-key owner mode, DELETE il delete owner mode; il global gate non è la lifetime authority.

### 1.4 `RD.DELETE`

`RD.DELETE` non acquisisce il conflict gate perché può soltanto rimuovere un blocker dal certified set. Se CREATE/RENAME vede ancora il blocker prima che la delete committi, una conservative semantic failure è valida; se la delete è già committed quando il gate holder fa il fresh read, la candidate può diventare ammissibile.

### 1.5 No fan-out locks / no runtime gate

Il protected global check non prende `FOR UPDATE` su tutte le altre Definition rows: il gate serializza le sole supported predicate-changing mutation `CREATE/RENAME`.

Runtime `Relationship.CREATE/DELETE` non acquisisce il conflict gate: consumano un Definition contract già certified. Endpoint ObjectTemplate lineage lifetime resta `S-REFERENCE-LIFETIME` con FK `RESTRICT`, non `RC`.

M1 non introduce ancestry-closure authority né partitioned/name-keyed conflict gates.

### 1.6 Gate lifetime

`RELATIONSHIP_DEFINITION_CONFLICT_GATE` è `pg_advisory_xact_lock` e resta detenuto fino a commit/rollback. Rilasciarlo prima del commit permetterebbe a un altro candidate di validare contro uno state precedente non ancora visibile.

### 1.7 Required PostgreSQL tests

Almeno:

1. equivalent concurrent `RD.CREATE × RD.CREATE` -> un solo certified Definition;
2. non-equivalent but conflicting concurrent CREATE -> un solo winner;
3. unrelated CREATE -> correctness con intentional global over-serialization;
4. `RD.CREATE × RD.RENAME` che diventano conflicting;
5. `RD.RENAME(D1) × RD.RENAME(D2)` verso conflicting state;
6. same-Definition rename × rename -> Definition-header serialization prima del gate;
7. non-symmetric/symmetric complete rename atomicity;
8. waiter vede lo state committed dal previous gate holder;
9. explicit fresh-snapshot-after-advisory-wait test;
10. global check senza fan-out `FOR UPDATE` sulle Definition;
11. blocker `RD.DELETE × CREATE/RENAME`, entrambi gli scheduling ammessi;
12. endpoint OT lineage DELETE vs RD.CREATE -> FK lifetime arbitration;
13. rollback CREATE/RENAME non lascia partial certified candidate;
14. gate held through commit;
15. runtime Relationship mutation non prende il conflict gate;
16. endpoint overlap test per equality/ancestor/descendant.

---

## 2. REALIZE-13 — `S-REL-FACT` (`RF`) e `S-REL-LIFETIME` (`RA`)

### 2.1 Exact-view factual authority

La final factual arbitration authority è:

```text
runtime_relationship_resolutions
PRIMARY KEY (resolution_id, from_object_id, to_object_id)
```

Una exact resolved view appartiene ad al massimo una current factual Relationship. Non esiste global Relationship lock, endpoint-pair lock, fact hash o canonical endpoint-pair authority.

`REL.CREATE` usa `ARBITRATION + CONVERGENCE`: se la selected exact view è già current, converge sul relativo `relationship_id` senza mutation/event. Se non esiste, deriva la complete deterministic closure, la exact-deduplica, ordina le candidate rows per `(resolution_id, from_object_id, to_object_id)`, crea una nuova Relationship UUID e tenta atomically header + complete closure + complete lifecycle creation event set.

### 2.2 Collision and convergence

Una collisione sulla exact-view PK abortisce l'intera semantic UoW. M1 non usa row-per-row `ON CONFLICT DO NOTHING`, partial merge o reparenting verso il winner.

Dopo la collisione:

```text
rollback complete candidate UoW
-> fresh semantic UoW
-> read current requested exact view
```

Se il winner è ancora current, il loser converge su quel `relationship_id` senza secondo event set. Se il winner è stato nel frattempo eliminato, la fresh semantic CREATE può rivalutare lo state e creare una nuova Relationship identity.

Il loser-generated UUID non è mai committed identity e viene scartato con il rollback.

### 2.3 Complete closure authority boundary

La exact-view PK arbitra `RF`, ma non certifica la complete runtime closure. Complete closure, factual endpoint coherence e complete lifecycle event set restano UoW invariants: header + tutte le runtime rows + tutti gli eventi required committano o rollbackano insieme. Nessun autonomous CRUD path esiste sulle runtime child rows.

### 2.4 `REL.DELETE` e exact factual lifetime

`relationships.id` è il concurrency owner di `S-REL-LIFETIME` per DELETE:

```text
SELECT relationship X FOR UPDATE

absent
    -> idempotent no-op, no event

present
    -> load complete current closure
    -> derive complete deletion semantic-view event set
    -> delete Relationship header
       (CASCADE owned runtime closure)
    -> insert deletion event set
    -> commit
```

Concurrent `DELETE(X) × DELETE(X)` produce una sola real deletion + un solo deletion event set; il waiter osserva X absent e converge come no-op.

### 2.5 ABA safety

Recreate della stessa semantic association genera sempre una nuova Relationship UUID. Una late `DELETE(X)` opera esclusivamente sull'exact old id X e non può cancellare la nuova Relationship Y, anche se Y rappresenta la stessa semantic association.

`CREATE` contro X current può convergere su X e poi una DELETE rimuoverlo; DELETE-first può invece rendere una successiva CREATE responsabile della nuova Y. Entrambi sono validi serial outcomes. Nessuna resurrection di X.

### 2.6 Retry boundary

Exact-view unique collision è un expected semantic-convergence signal e richiede complete semantic-UoW restart. Generic deadlock/transient DB retry resta una failure class separata. Non si ritenta un repository fragment con candidate state stale.

### 2.7 Separation da RL/ES

`REL.CREATE × Object.DELETE` e `REL.CREATE × RD.DELETE` restano `S-REFERENCE-LIFETIME` con FK `RESTRICT` final authority. `RD.RENAME × REL.CREATE/DELETE` non appartiene a RF/RA: riguarda solo `S-REL-EVENT-SNAPSHOT` e viene realizzato separatamente.

### 2.8 Required PostgreSQL tests

Almeno:

1. concurrent equivalent non-symmetric CREATE via reciprocal Resolutions -> one header/closure/event set, both calls may converge;
2. symmetric inverse CREATE;
3. symmetric inheritance-overlap closure multi-view;
4. canonical closure-row insertion order;
5. collision sulla prima e su una successiva closure row -> full loser rollback;
6. no partial `ON CONFLICT` aggregate behavior;
7. loser UUID non rimane current;
8. loser fresh-UoW convergence sul winner;
9. winner deleted before convergence read -> fresh CREATE may create Y;
10. concurrent `DELETE(X) × DELETE(X)` -> one event set;
11. delete absent -> no-op/no event;
12. CREATE-converge-then-DELETE -> valid final absent;
13. DELETE-then-recreate -> new Y;
14. late DELETE X after recreate Y leaves Y intact;
15. rollback CREATE/DELETE preserves complete aggregate semantics;
16. Object/Definition delete races use RL/FK;
17. unrelated Relationship CREATEs have no global serialization.

---

## 3. REALIZE-14 — `S-REL-EVENT-SNAPSHOT` (`ES`)

`S-REL-EVENT-SNAPSHOT` usa outcome `SNAPSHOT`, non writer serialization. La authority è una coherent committed metadata observation dei current `relationship_resolutions.name` e `objects.canonical_name` necessari all'intero lifecycle event set.

### 3.1 One-statement observation boundary

Una singola Relationship factual transition usa **un solo SQL metadata-observation statement** a `READ COMMITTED` per ottenere, nello stesso MVCC snapshot:

```text
all required runtime semantic views
all Resolution relationship names
all source/destination Object canonical names
```

Non sono ammesse più SELECT metadata separate che possano osservare snapshot differenti. Il result dello statement viene catturato dalla UoW e usato integralmente per costruire il complete event set; non si fanno metadata reread per singolo evento.

Nessun `FOR SHARE`/`FOR UPDATE` viene acquisito soltanto per event metadata: `RD.RENAME` e `OBJ.RENAME` non vengono genericamente serializzati con runtime Relationship mutation.

### 3.2 CREATE ordering

Per una real `REL.CREATE`:

```text
validate + derive complete closure
-> insert Relationship header
-> insert complete runtime closure
-> exact-view arbitration succeeds
-> ONE metadata/semantic-view SELECT over the complete candidate closure
-> build complete creation event set
-> insert events
-> commit
```

Le runtime rows inserite dalla stessa transaction sono visibili al proprio SELECT. Se factual arbitration fallisce, la UoW rollbacka prima della metadata observation.

### 3.3 DELETE ordering

Per `REL.DELETE(X)` current:

```text
Relationship X FOR UPDATE
-> ONE metadata/semantic-view SELECT over the complete current closure
-> capture complete deletion event set
-> delete Relationship header / CASCADE closure
-> insert captured deletion events
-> commit
```

La semantic projection deve essere catturata prima della closure removal.

### 3.4 Semantic-view dedup

Il lifecycle contract resta one event per distinct:

```text
(object_id, destination_object_id, relationship_name)
```

non per runtime row. Il one-statement snapshot può quindi produrre direttamente la domain semantic projection/dedup (`SELECT DISTINCT` o equivalente), preservando complete event-set semantics anche quando più runtime rows rappresentano la stessa semantic view.

### 3.5 Concurrent metadata mutation

Per `RD.RENAME × REL.CREATE/DELETE`, l'event set può osservare integralmente il committed old name set oppure integralmente il committed new name set. Un non-symmetric atomic rename non può produrre half-old/half-new names nello stesso event snapshot.

Per `OBJ.RENAME`, ogni endpoint canonical name proviene dallo stesso DB statement snapshot. Se due endpoint vengono rinominati da transaction indipendenti, qualunque combinazione che sia realmente esistita nello stesso committed DB snapshot è valida; ciò che è vietato è mescolare osservazioni provenienti da statement snapshot differenti.

Una metadata mutation che committa dopo lo snapshot ma prima del Relationship commit non invalida il captured event set.

### 3.6 No REPEATABLE READ special case

Runtime Relationship mutation resta a `READ COMMITTED`. Non si introduce `REPEATABLE READ` soltanto per eventi: un singolo coherent SQL statement fornisce già l'observation boundary richiesto con minore complessità e senza snapshot transaction-wide più vecchi.

### 3.7 `occurred_at` semantics

`object_lifecycle_events.occurred_at = transaction_timestamp()` rappresenta l'inizio della transaction, non il metadata-observation instant, commit time o un ordine causale/globale. È quindi valido che il metadata SELECT osservi una rename committed dopo il transaction start pur producendo un evento con `occurred_at` precedente a quella rename in wall-clock time.

### 3.8 Atomic completeness

Se lo statement non consente di costruire il complete expected semantic-view event set, l'intera factual UoW rollbacka. Non sono ammessi partial event set. Dopo la projection, le event views vengono ordinate deterministicamente (per esempio `(object_id, destination_object_id, relationship_name)`) prima dell'insert per rendere implementazione/test/debug deterministici senza introdurre semantic identity o global ordering.

### 3.9 Required PostgreSQL tests

Almeno:

1. RD.RENAME commits before metadata SELECT -> complete new names;
2. RD.RENAME commits after metadata SELECT -> complete old names;
3. non-symmetric rename never yields half-old/half-new event names;
4. OBJ.RENAME before/after snapshot -> valid old/new canonical names;
5. two independent endpoint renames -> only combinations that existed in one committed statement snapshot;
6. REL.CREATE/DELETE do not lock metadata rows solely for ES;
7. CREATE metadata SELECT occurs only after complete closure insert success;
8. DELETE metadata SELECT occurs before closure removal;
9. semantic-view dedup belongs to the one statement projection;
10. incomplete projection -> full UoW rollback;
11. metadata mutation after snapshot but before factual commit does not invalidate event set;
12. transaction-start `occurred_at` may precede metadata mutation observed by later snapshot.

---

## 4. REALIZE-15 — Relationship impact of the lock-strength consistency sweep

The sweep keeps all Relationship semantic predicates and authorities unchanged but refines non-key mutable owner locks from `FOR UPDATE` to `FOR NO KEY UPDATE`.

### 4.1 RelationshipDefinition rename

`RD.RENAME` changes Resolution names and no referenced Definition key. Its owner primitive is therefore:

```text
Definition header FOR NO KEY UPDATE
-> RELATIONSHIP_DEFINITION_CONFLICT_GATE
```

`RD.DELETE` remains `Definition header FOR UPDATE` because it deletes the referenced identity.

This distinction preserves same-Definition writer serialization while avoiding a lock strength that would unnecessarily conflict with pure referential key-share protection from concurrent runtime Relationship creation.

### 4.2 Runtime Relationship vs Object metadata/state mutation

Object `RENAME`, `DATA_CHANGE` and `SCHEMA_CHANGE` similarly use their Object row as `FOR NO KEY UPDATE` owner; Object DELETE remains `FOR UPDATE`.

Therefore a runtime Relationship CREATE that establishes current Object FKs is not intentionally serialized with non-key Object mutations merely because of referential integrity. The semantic relationship remains the one already defined:

```text
REL.CREATE × OBJ.RENAME -> ES snapshot only when a real event set is produced
REL.CREATE × OBJ.DATA_CHANGE/SCHEMA_CHANGE -> semantic I
REL.CREATE × OBJ.DELETE -> RL/FK arbitration
```

### 4.3 Lifecycle dependency strength remains `FOR SHARE`

The refinement does **not** weaken lifecycle-sensitive dependency admission/certification locks. Whenever RelationshipDefinition or ObjectTemplate semantics require `FOR SHARE`, that stronger shared lock remains intentional and continues to conflict with non-key lifecycle state writers.

### 4.4 Required sweep tests

Add explicit real-PG tests that prove:

1. `REL.CREATE × RD.RENAME` does not block solely because of Definition FK key protection;
2. `REL.CREATE × OBJ.RENAME` does not block solely because of Object FK key protection;
3. `REL.CREATE × OBJ.DATA_CHANGE` and `REL.CREATE × OBJ.SCHEMA_CHANGE` remain free of artificial FK-vs-owner serialization where no other predicate applies;
4. `REL.CREATE × RD.DELETE` and `REL.CREATE × OBJ.DELETE` still arbitrate correctly through FK `RESTRICT`/delete semantics;
5. same-Definition rename writers remain serialized;
6. same-Object non-key intrinsic writers remain serialized.

The refinement changes mechanism strength only; it does not alter RF, RA, ES or RL semantics.
