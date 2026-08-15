# M1 — PostgreSQL Concurrency Realization: aggregate, Object, ownership

**Status:** DRAFT — REALIZE-08..REALIZE-11 ratificati; REALIZE-15 applica il lock-strength refinement `FOR NO KEY UPDATE` agli owner non-key e completa il consistency sweep. Documento companion di `concurrency-postgresql-realization-matrix.md`; le decisioni qui contenute fanno parte della stessa realization matrix e vengono mantenute traceable predicate -> authority -> PostgreSQL mechanism -> real-PG test.

## 1. REALIZE-08 — `S-AGGREGATE-LIFETIME` (`AL`) e `S-METADATA-LWW` (`ML`)

### 1.1 Aggregate lifetime

M1 non introduce un universal aggregate `FOR SHARE` lock.

`DELETE_LINEAGE` acquisisce la stable lineage root `FOR UPDATE` e poi elimina l'aggregate con root -> owned-child `CASCADE`, subject alle external `RESTRICT` già definite.

Le mutation che già usano la lineage header (`CREATE_NEXT`, `DELETE_DRAFT`, `PUBLISH`, `SET_DEFAULT`, `CLEAR_DEFAULT`, `DEPRECATE`) rendezvous naturalmente con la whole-lineage delete sulla root row.

`REVISE` resta invece exact-DRAFT owner, ora realizzato con `FOR NO KEY UPDATE` perché non modifica né elimina la row identity. Il `CASCADE` della lineage delete deve eliminare quella exact version row e quindi non può rimuoverla mentre una revise la possiede. Outcome ammessi: revise-first e successiva whole-lineage delete, oppure delete-first e nessuna successiva mutation della generation rimossa.

`SET_DESCRIPTION` vive sulla lineage header e usa un single-statement atomic `UPDATE`; la row-write arbitration PostgreSQL coordina `SET_DESCRIPTION × DELETE_LINEAGE` senza pre-lock aggiuntivo.

`RD.RENAME × RD.DELETE` serializza sulla stessa RelationshipDefinition header: RENAME usa il non-key owner mode, DELETE il delete/key-changing owner mode.

External references non appartengono ad `AL`: restano `S-REFERENCE-LIFETIME` con FK `RESTRICT` final authority.

### 1.2 Metadata LWW

`description` è mutable non-semantic metadata. `SET_DESCRIPTION(A) × SET_DESCRIPTION(B)` può far riuscire entrambi i writer; il final value è quello dell'ultimo writer nel PostgreSQL row-write serialization order. Non si promette wall-clock/request ordering, non esiste merge, stale failure, metadata revision o CAS.

La collocazione di `description` sulla lineage header produce intentional implementation over-serialization con semantic-`I` operations che usano la stessa row. M1 non separa la metadata in una tabella dedicata solo per aumentare parallelismo model-plane.

Required PG tests: revise/delete-lineage, publish/delete-lineage, create-next/delete-lineage, delete-draft/delete-lineage, set-description/delete-lineage, RD rename/delete, concurrent descriptions complete-value LWW, description vs default over-serialization, description vs revise senza artificial lineage-wide locking.

---

## 2. REALIZE-09 — `S-OBJECT-STATE` (`OS`)

La row `objects(O)` è il concurrency owner del complete current intrinsic Object state:

```text
id
canonical_name
template_id
template_version
properties
```

Per ogni Object esistente:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
```

la mutation acquisisce `objects(O) FOR NO KEY UPDATE` **prima** di qualunque state-dependent candidate derivation. `DELETE` acquisisce invece `objects(O) FOR UPDATE`, perché elimina la referenced row identity.

Dopo il lock la UoW ricarica il complete current state, deriva la candidate, esegue le dependency/schema validation ulteriori richieste, persiste current state e complete lifecycle event nella stessa semantic transaction. Una candidate derivata soltanto da una pre-lock read non può essere committata senza post-lock re-derivation/revalidation.

`DATA_CHANGE × DATA_CHANGE` non perde update anche con `properties` JSONB: il secondo writer ricarica lo state prodotto dal primo e deriva da quello. Il DATA_CHANGE semantic no-op è valutato post-lock; no current mutation implica no lifecycle event.

`DATA_CHANGE × SCHEMA_CHANGE` e `SCHEMA_CHANGE × SCHEMA_CHANGE` sono serialmente componibili: il waiter rivaluta current `template_version` e properties e può riuscire oppure fallire sullo state prodotto dal winner; non riusa una migration candidate stale.

`SCHEMA_CHANGE` compone più authority senza confonderle:

```text
objects(O) FOR NO KEY UPDATE -> S-OBJECT-STATE
target exact OTV FOR SHARE   -> S-BINDING-ADMISSION
outgoing ownership read      -> S-PARENT-OWNERSHIP validation
```

`DELETE` usa `FOR UPDATE` sulla stessa Object row per il final intrinsic snapshot; external ownership/Relationship races restano finalizzate dalle FK `RESTRICT` di `S-REFERENCE-LIFETIME`. Delete-first impedisce qualsiasi resurrection.

Lifecycle `before` deriva dallo state ricaricato post-lock; `after` dalla stessa canonical candidate persistita. Current-state write ed event insert sono atomici nella stessa UoW.

M1 non introduce `Object.state_revision`, generic Object CAS o operation-specific conditional-update concurrency models.

Required PG tests: rename/rename, rename/data-change event composability, data-change/data-change no lost update, equivalent data-change one real transition + no-op, both DATA_CHANGE/SCHEMA_CHANGE orderings, concurrent schema changes source re-evaluation, intrinsic mutation/delete races, rollback waiter behavior, lifecycle before/after identity, intentional `RENAME(parent) × ATTACH(parent)` physical contention, e compatibilità `REL.CREATE × OBJ.RENAME` senza serialization dovuta soltanto alla FK.

---

## 3. REALIZE-10 — ownership locale: `PO`, `OF`, `SO`

### 3.1 `S-PARENT-OWNERSHIP` (`PO`)

`objects(parent)` è il concurrency owner del parent current exact schema + outgoing ownership edge set.

```text
ATTACH(parent,...)
DETACH(parent,...)
SCHEMA_CHANGE(parent)
```

acquisiscono `objects(parent) FOR NO KEY UPDATE` prima delle rispettive state-dependent decisioni. ATTACH valida slot e child compatibility contro il parent schema ricaricato post-lock. SCHEMA_CHANGE, dopo il lock, valida il target schema contro l'outgoing set current.

DETACH non esegue una nuova slot/compatibility admission: la removal authority resta l'exact current ownership fact. Tuttavia, quando un exact edge esiste, il suo `slot_name` deve risolvere una current `SlotSemanticKey` nella exact effective schema del parent stabilizzato, perché il current parent schema è l'autorità semantica del fact e fornisce anche `slot_declaring_template_id` alla projection/event. Un persisted edge non risolvibile non viene reinterpretato tramite historical lookup: è invariant corruption/internal failure.

### 3.2 `S-OWNERSHIP-FACT` (`OF`)

Il current ownership fact di child `C` è:

```text
detached
oppure
(parent=P, slot=S)
```

persistito in `object_components` senza stable edge identity e senza persisted `slot_declaring_template_id`. La semantic identity corrente dello slot viene derivata dal current exact schema del parent.

ATTACH decision table sul current fact:

```text
absent            -> candidate real edge-add
exact requested   -> idempotent success/no-op/no event
different P/S     -> ownership conflict
```

DETACH decision table:

```text
exact requested   -> resolve current SlotSemanticKey -> real delete + one DETACH_FROM event
detached          -> idempotent success/no-op/no event
different P/S     -> ownership mismatch; never remove that other edge
```

Se il current exact edge esiste ma il current parent schema non contiene esattamente lo slot richiesto, la row contraddice l'invariant secondo cui ogni committed edge è valido nel current schema: nessuna "last known declaration" o lifecycle-history fallback è ammessa.

Cross-parent DETACH/ATTACH può produrre conservative ATTACH failure se la concurrent detach non è ancora committed; oppure detach-first e successivo attach. Entrambi sono serialmente validi.

Ownership non possiede Relationship-style ABA protection: detach + later reattach dello stesso `(P,S,C)` produce un nuovo current fact indistinguibile dalla prospettiva di un late exact DETACH; non si introduce `ownership_edge_id`.

### 3.3 `S-SINGLE-OWNER` (`SO`)

La final physical/concurrency authority è:

```text
PRIMARY KEY (child_object_id)
```

su `object_components`.

Una child può avere al massimo un current owner/slot anche nello state initially absent. Un `SELECT ... FOR UPDATE` su `object_components WHERE child_object_id=C` non è sufficiente come absent-state guard e non sostituisce la PK.

M1 non prende generic lock sulla `objects(child)` row per ownership: `child.template_id` è stable per le normal mutation, single-owner è PK-enforced e Object DELETE lifetime è FK-enforced. Questo evita unnecessary contention con child RENAME/DATA_CHANGE/SCHEMA_CHANGE.

Identical ATTACH/DETACH converge sul current fact; una real transition produce esattamente un lifecycle event, un no-op nessun event.

Il graph gate può fisicamente serializzare molte ATTACH, ma **non** è l'authority di `S-SINGLE-OWNER`.

Required PG tests: ATTACH/SCHEMA_CHANGE(parent), DETACH/SCHEMA_CHANGE(parent), identical ATTACH one edge/event, different-parent same-child at most one owner, ATTACH/DETACH exact, cross-parent detach/attach, identical DETACH one removal/event, wrong-owner DETACH safety, child intrinsic operations not lock requirements, direct PK tests, absent-state races, rollback behavior, parent over-serialization, no-op event absence, explicit ABA behavior, e persisted-edge/current-slot inconsistency come internal invariant failure.

---

## 4. REALIZE-11 — `S-OWN-CYCLE` (`OC`)

### 4.1 Authority and gate

`S-OWN-CYCLE` authority è il **current committed `object_components` graph**. Il mechanism M1 è l'exclusive transaction-level advisory gate:

```text
pg_advisory_xact_lock(OWNERSHIP_GRAPH_WRITE_GATE)
```

Il gate non contiene né sostituisce il graph state; serializza soltanto le real edge-add critical sections.

Ogni real ATTACH segue:

```text
parent Object FOR NO KEY UPDATE
-> local slot/compatibility/self checks
-> read current child ownership
-> fast exit on exact no-op or conflict
-> acquire OWNERSHIP_GRAPH_WRITE_GATE
-> fresh READ COMMITTED snapshot
-> re-read child ownership
-> cycle check against committed graph
-> INSERT edge
-> ATTACH_TO event
-> COMMIT
```

Il gate viene acquisito soltanto quando l'operation resta una candidate real edge-add.

### 4.2 Fresh snapshot rule after blocking advisory lock

L'acquisition del logical gate e la protected predicate read devono essere **SQL statement separati**.

A `READ COMMITTED`, un singolo statement che acquisisce il gate dopo una wait potrebbe avere ottenuto lo statement snapshot prima dell'attesa. Quindi il baseline M1 è:

```text
statement 1: SELECT pg_advisory_xact_lock(...)
statement 2+: read/re-read protected predicate using a fresh snapshot
```

Questa regola è generale per ogni M1 logical gate, incluso `RELATIONSHIP_DEFINITION_CONFLICT_GATE`.

Dopo il gate ATTACH rilegge anche current child ownership, perché un altro edge-add può averla modificata mentre la transaction attendeva.

### 4.3 Cycle check and gate lifetime

Con edge orientation `parent -> child`, candidate `P -> C` è valido iff `P` non è raggiungibile da `C` nel current committed graph. M1 usa una recursive traversal del graph authoritative; non introduce closure table, materialized path, nested-set authority o path-row locking.

Il advisory xact lock resta detenuto fino al commit. Rilasciarlo prima renderebbe invisibile al successivo gate holder una edge-add non ancora committed.

`DETACH` non prende il gate: edge removal non può introdurre un ciclo e può soltanto rendere un candidate successivo più permissivo; conservative cycle rejection durante una concurrent uncommitted removal è ammessa.

Ordering M1:

```text
parent Object FOR NO KEY UPDATE
-> OWNERSHIP_GRAPH_WRITE_GATE
```

mai il contrario. Nessuna M1 UoW attualmente acquisisce entrambi i global logical gate.

### 4.4 Intentional over-serialization

Tutte le real ownership edge-add sono globalmente serializzate anche se appartengono a graph region indipendenti. È intentional implementation over-serialization, non semantic requirement. `PK(child_object_id)` rimane separatamente `S-SINGLE-OWNER` authority.

Rejected baseline alternatives: `SERIALIZABLE` special case per ATTACH, table lock su `object_components`, path-row locking, session-level advisory lock.

Required PG tests: opposite concurrent edges `A->B` / `B->A`, longer cycle, unrelated edge-add serialization, second gate holder sees first committed edge, explicit fresh-snapshot-after-wait test, post-gate child re-read, cycle check concurrent DETACH, DETACH no gate, failed/no-op/conflict ATTACH no gate, rollback releases gate and hides rolled-back edge, parent-before-gate ordering, no session-lock leakage, no authoritative protected read before gate, edge+event all-or-nothing.

---

## 5. REALIZE-15 — lock-strength refinement e ownership-event observation

### 5.1 Non-key owner mode

Il consistency sweep ha mostrato che `FOR UPDATE` come primitive universale è più forte del necessario e può interferire con la referential-lifetime machinery. M1 usa quindi:

```text
non-key mutable-state owner
    -> FOR NO KEY UPDATE

row delete / referenced-key-changing owner
    -> FOR UPDATE

lifecycle-sensitive dependency
    -> FOR SHARE
```

Il refinement non cambia concurrency authority, lock order o safety predicate. Gli owner writer della stessa row restano mutuamente esclusivi e `FOR SHARE` continua a stabilizzare lifecycle-sensitive dependency; una pure referential key-share protection può invece coesistere con non-key state mutation.

Applicazioni in questo companion:

```text
Object RENAME/DATA_CHANGE/SCHEMA_CHANGE -> FOR NO KEY UPDATE
Object DELETE                           -> FOR UPDATE
ATTACH/DETACH parent owner              -> FOR NO KEY UPDATE
DT/OT REVISE                            -> exact DRAFT FOR NO KEY UPDATE
RD.RENAME                               -> Definition FOR NO KEY UPDATE
```

### 5.2 Ownership structural-event display metadata

`ATTACH_TO`/`DETACH_FROM` persistono `canonical_name` del child e `destination_canonical_name` del parent come historical display metadata.

Il parent canonical name proviene dallo state della parent row già stabilizzata dal parent-owner lock. Il child canonical name viene letto come committed display metadata dopo la parent stabilization, senza introdurre un child lock soltanto per l'evento.

La structural event `SlotSemanticKey` (`slot_declaring_template_id`, `slot_name`) viene risolta dalla current exact effective schema del parent stabilizzato. `object_components` persiste soltanto `slot_name`: non esiste una seconda current slot-identity authority nella runtime row. Per `DETACH_FROM`, la risoluzione serve a interpretare l'exact fact che si sta rimuovendo, non a ripetere ATTACH admission; se il fact non è interpretabile nel current schema, la mutation incontra persisted invariant corruption.

Ownership produce un singolo structural event, quindi non necessita del multi-event `S-REL-EVENT-SNAPSHOT` machinery. Edge mutation ed event restano nella stessa UoW; una concurrent child rename può produrre old o new committed display name secondo l'observation point, ma non modifica la ownership fact semantics.

### 5.3 Over-serialization retained intentionally

Il refinement non rimuove le contention M1 che derivano da una scelta di owner realmente condivisa, per esempio:

```text
RENAME(parent) × ATTACH(parent)
DATA_CHANGE(parent) × DETACH(parent)
```

Entrambe usano `FOR NO KEY UPDATE` sulla stessa parent row e restano intentional implementation over-serialization. Il refinement elimina invece soltanto contention incidentale dovuta a una lock strength più forte del predicate richiesto.

---

## 6. Gate-wide invariant carried forward

Per ogni transaction-level logical gate M1:

1. il committed protected row set è l'authority;
2. `pg_advisory_xact_lock` è solo stabilization mechanism;
3. acquisition e authoritative protected read avvengono in statement separati;
4. dopo una blocking wait il predicate viene sempre letto/riletto con fresh READ COMMITTED snapshot;
5. il gate resta detenuto fino al commit della mutation del protected set;
6. rollback libera automaticamente il gate e nessuna partial state diventa visible.
