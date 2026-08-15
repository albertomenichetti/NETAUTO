# M1 — Object Ownership

**Status:** DRAFT — ownership semantics frozen; PostgreSQL realization aligned to REALIZE-10/11/15.

## 1. Responsabilità

Component ownership è structural runtime state distinto dall'intrinsic Object snapshot e dalle generic Relationships.

Un ownership edge è concettualmente:

```text
parent_object_id
slot_name
child_object_id
```

Semanticamente lo slot è identificato da:

```text
SlotSemanticKey
=
(declaring_template_id, name)
```

La runtime row persiste `slot_name`; la declaring lineage viene ricavata dalla **current exact effective closure del parent** quando serve semantic resolution.

Il current ownership fact non è un historical pin alla declaration esistente al momento dell'ATTACH. La sua semantica corrente è sempre interpretata contro la current exact OTV del parent. Di conseguenza `slot_declaring_template_id` non viene duplicato nella runtime row: il current parent schema resta l'unica authority semantica della `SlotSemanticKey`.

## 2. Ownership invariants

M1:

- uno stesso `(parent, slot)` contiene `0..N` child;
- un child appartiene ad al massimo un `(owner, slot)`;
- self-attachment è vietato;
- l'ownership graph committed è aciclico;
- ogni edge usa uno slot effettivo della current exact OTV del parent;
- ogni current edge risolve esattamente una `SlotSemanticKey` nella current exact effective closure del parent;
- ogni child è lineage-compatible con lo slot target;
- single-owner + acyclicity rendono l'ownership graph una foresta.

Un persisted edge che non sia più semanticamente risolvibile contro la current exact schema del parent contraddice le invarianti M1. Non è uno stato legacy supportato o una normale condizione di remediation tramite DETACH: è persisted invariant corruption e deve emergere come internal failure.

## 3. ATTACH admission

Command concettuale:

```text
ATTACH(
    parent_object_id = P,
    slot_name = S,
    child_object_id = C
)
```

Per creare un nuovo edge devono valere:

```text
P exists
C exists
P != C

S exists in effective component schema
of P current exact OTV

C.template_id compatible with S.target_template_id

C detached

adding P -> C does not create a cycle
```

Effective slot resolution usa esclusivamente la exact current OTV closure del parent.

Nessun default/latest resolution.

## 4. Existing DEPRECATED parent schema

Un Object già pinnato a una DEPRECATED OTV può continuare a ricevere data-plane ownership mutations interpretate secondo quella immutable historical exact closure.

ATTACH non crea un nuovo Object->OTV binding.

La deprecazione della current parent OTV non rende retroattivamente immutable l'Object.

## 5. Child compatibility

Compatibility:

```text
child.template_id == slot.target_template_id
OR
child.template_id is descendant of slot.target_template_id
```

Non dipende da:

```text
child.template_version
child.properties
child relationships
```

Poiché `Object.template_id` è stable e ObjectTemplate ancestry è stable, un normale SCHEMA_CHANGE del child non può rendere type-incompatible un incoming ownership edge.

## 6. Exact ATTACH idempotency

Tre casi.

### Child detached

```text
ATTACH(P,S,C)
    -> may create edge
```

### Child già attached esattamente a P/S

```text
ATTACH(P,S,C)
    -> successful idempotent no-op
```

Nessun nuovo lifecycle event.

### Child attached a differente P'/S'

```text
ATTACH(P,S,C)
    -> FAIL ownership conflict
```

Nessun implicit move.

Due concurrent identical ATTACH possono entrambi convergere con successo sul medesimo edge.

Due concurrent different ATTACH sullo stesso child possono avere al massimo un vincitore.

## 7. DETACH semantics

Command:

```text
DETACH(P,S,C)
```

Rimuove esclusivamente l'exact ownership edge indicato.

Casi:

```text
exact P/S -> C exists
    -> remove

C already detached
    -> successful idempotent no-op

C attached to different P'/S'
    -> FAIL ownership mismatch
```

DETACH non rimuove mai un edge differente da quello richiesto.

DETACH **non esegue una nuova slot admission**: non rivalida la compatibilità del child, non richiede che lo slot sia oggi ammissibile per una nuova ATTACH e non tratta la removal come una nuova binding operation.

Tuttavia un exact current edge esistente deve essere semanticamente interpretabile contro la current exact effective schema del parent, perché quella closure è l'autorità della `SlotSemanticKey` usata anche dalla projection e dal lifecycle event `DETACH_FROM`. Sotto il parent owner lock, DETACH risolve quindi il current `slot_name` nella current exact closure esclusivamente per interpretare il fact già esistente e ottenere `slot_declaring_template_id`.

Se la runtime row esiste ma il relativo `slot_name` non risolve esattamente uno slot corrente del parent, il dataset viola l'ownership invariant: la operation non inventa una historical declaration, non cerca una "last known" slot version e non usa il lifecycle changelog come authority. Il caso è persisted invariant corruption e fallisce come internal failure.

DETACH:

- non esegue child compatibility validation;
- non esegue cycle traversal;
- non può introdurre single-owner violation;
- non può introdurre cicli.

Nessun implicit move. Un nuovo owner richiede successivo ATTACH.

## 8. No atomic move primitive M1

M1 non introduce:

```text
MOVE child from P1/S1 to P2/S2
```

come kernel primitive.

Una higher-level workflow può comporre:

```text
DETACH
ATTACH
```

con le rispettive atomic semantics.

## 9. Parent-schema concurrency domain

`ATTACH`, `DETACH` e `SCHEMA_CHANGE(parent)` devono essere fortemente consistenti rispetto a:

```text
parent current exact schema
+
parent outgoing ownership edges
```

Nessun interleaving può committare un edge che non sia più valido nella current exact OTV del parent.

PostgreSQL realization M1:

```text
objects(parent) FOR NO KEY UPDATE
```

è il shared concurrency owner per `ATTACH`, `DETACH` e `SCHEMA_CHANGE(parent)`. Dopo ogni eventuale wait la mutation rilegge il parent current state prima delle decisioni dipendenti dallo schema/outgoing set.

Questo può intentionally over-serializzare semantic-`I` mutation come `RENAME(parent) × ATTACH(parent)`; il trade-off è normativo e regression-tested.

## 10. Single-owner concurrency domain

Single-owner è un invariant locale al child.

Concurrent:

```text
ATTACH P1/S1 -> C
ATTACH P2/S2 -> C
```

con desired edge diverse:

```text
at most one may create ownership
```

Final PostgreSQL authority:

```text
object_components PRIMARY KEY(child_object_id)
```

Il child Object non viene genericamente row-lockato. Un `SELECT object_components ... FOR UPDATE` non può sostituire la PK nello state detached perché non esiste una row-gap lock authority M1.

## 11. Acyclicity concurrency domain

Acyclicity è un graph-wide predicate.

Scenario minimo:

```text
T1: ATTACH A -> B
T2: ATTACH B -> A
```

Entrambe potrebbero risultare localmente valide sullo stesso initial snapshot; non possono entrambe committare.

Normative PostgreSQL strategy:

> ogni `ATTACH` che resta una **real edge-add candidate** dopo parent/local/current-fact validation acquisisce `pg_advisory_xact_lock(OWNERSHIP_GRAPH_WRITE_GATE)` e mantiene il gate fino al commit/rollback.

Ordering:

```text
parent Object FOR NO KEY UPDATE
-> local/current-fact validation
-> OWNERSHIP_GRAPH_WRITE_GATE
-> fresh post-gate child-ownership read
-> fresh graph/cycle check
-> edge insert + lifecycle event
-> commit
```

Gate acquisition e protected graph read sono SQL statement separati: a `READ COMMITTED` il predicate dopo una blocking wait deve usare un fresh statement snapshot che includa lo state committed dal previous gate holder.

Il gate è stabilization mechanism; il committed `object_components` graph è l'authority.

DETACH non acquisisce il global cycle gate perché edge removal non può introdurre un ciclo. Un ATTACH che fallisce conservativamente perché un concurrent DETACH non è ancora visible è un valido ordine seriale.

## 12. Lifecycle events

Una reale edge creation produce:

```text
ATTACH_TO
```

Una reale edge removal produce:

```text
DETACH_FROM
```

Event direction:

```text
object_id
    = child / subject

destination_object_id
    = parent / owner
```

L'event registra inoltre:

```text
canonical_name
    = historical child display metadata observed by the mutation

destination_canonical_name
    = parent canonical_name from the already stabilized parent row

slot_declaring_template_id
slot_name
```

Per `ATTACH_TO` e `DETACH_FROM`, `slot_declaring_template_id + slot_name` è la current `SlotSemanticKey` risolta dalla exact effective schema del parent stabilizzato. L'event preserva historical metadata della transition; la runtime edge row non materializza una seconda semantic authority della slot identity.

REALIZE-15 observation rule:

- parent display name deriva dalla parent row già posseduta con `FOR NO KEY UPDATE`;
- child canonical name viene letto come committed display metadata dopo parent stabilization;
- non si introduce un child lock soltanto per lifecycle display metadata;
- una concurrent child RENAME può quindi far osservare old oppure new committed name secondo l'observation point;
- questo non modifica ownership identity/validity semantics.

Idempotent no-op non produce duplicate lifecycle events.

Ownership mutation e structural lifecycle event sono atomici.

## 13. Delete interaction

Object DELETE non esegue DETACH implicitamente.

Per essere cancellato un Object deve avere:

```text
no incoming ownership
no outgoing ownership
```

Le parent/child Object FK in `object_components` sono current `RESTRICT` references. Se l'ownership edge vince la race, Object DELETE non può committare; se Object DELETE vince, una nuova ATTACH non può stabilire la reference.

Nessun `CASCADE` ownership cleanup è ammesso.
