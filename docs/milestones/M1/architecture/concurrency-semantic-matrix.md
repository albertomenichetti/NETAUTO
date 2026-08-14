# M1 — Semantic Concurrency Matrix

**Status:** DRAFT — semantic operation census, safety predicate vocabulary e canonical sparse matrix ratificati; nessun PostgreSQL mechanism è normativo in questo documento.

## 1. Scopo

Questo documento definisce la matrice semantica di concorrenza M1 **prima** della scelta dei meccanismi PostgreSQL.

Per ogni coppia di mutation risponde nell'ordine a:

```text
1. quando le due operation interagiscono davvero?      -> scope
2. quale invalid committed state/interleaving minaccia? -> risk
3. quale proprietà deve restare vera?                  -> safety predicate
4. quali outcome seriali/convergenti sono validi?      -> allowed outcomes
```

Non appartengono a questo documento:

- `FOR UPDATE` / `FOR SHARE`;
- advisory lock;
- PK/FK/UNIQUE specifici;
- isolation level;
- retry SQL/error mapping.

Tali aspetti appartengono alla successiva PostgreSQL realization matrix.

Principio:

> la semantic matrix dice **che cosa deve restare vero**; la realization matrix dirà **come PostgreSQL lo garantisce**.

---

## 2. Canonical operation census

M1 possiede 32 mutation primitive rilevanti ai fini della concurrency review.

### DataType — 10

```text
DT.C      CREATE
DT.CN     CREATE_NEXT
DT.R      REVISE
DT.P      PUBLISH
DT.SD     SET_DEFAULT
DT.CD     CLEAR_DEFAULT
DT.D      DEPRECATE
DT.DD     DELETE_DRAFT
DT.DL     DELETE_LINEAGE
DT.DESC   SET_DESCRIPTION
```

### ObjectTemplate — 10

```text
OT.C      CREATE
OT.CN     CREATE_NEXT
OT.R      REVISE
OT.P      PUBLISH
OT.SD     SET_DEFAULT
OT.CD     CLEAR_DEFAULT
OT.D      DEPRECATE
OT.DD     DELETE_DRAFT
OT.DL     DELETE_LINEAGE
OT.DESC   SET_DESCRIPTION
```

### Object / Ownership — 7

```text
OBJ.C     CREATE
OBJ.RN    RENAME
OBJ.DC    DATA_CHANGE
OBJ.SC    SCHEMA_CHANGE
OBJ.A     ATTACH
OBJ.DET   DETACH
OBJ.DEL   DELETE
```

### RelationshipDefinition — 3

```text
RD.C      CREATE
RD.RN     RENAME
RD.DEL    DELETE
```

### Relationship — 2

```text
REL.C     CREATE
REL.DEL   DELETE
```

Totale:

```text
32 operations
32 * 33 / 2 = 528 upper-triangular cells including diagonal
```

Ogni futura mutation deve essere aggiunta a questo census e confrontata semanticamente con **tutte** le mutation esistenti prima che il relativo concurrency design possa essere considerato completo.

Read-only primitive non fanno parte della mutation matrix; i loro snapshot/read-consistency contract restano nei documenti di dominio e persistence.

---

## 3. Regola di rappresentazione canonicale

La matrice normativa è **sparse**:

1. ogni cella parte da `I — INDEPENDENT`;
2. le scoped rule definite in questo documento sostituiscono `I` quando lo scope concreto matcha;
3. più safety predicate possono applicarsi contemporaneamente;
4. una materializzazione grafica 32×32 è un read model derivato, non la source of truth.

Questo evita duplicazione di 528 descrizioni e rende esplicito che il significato dipende anche dalle concrete entity/reference coinvolte, non soltanto dal nome delle operation.

---

## 4. `I — INDEPENDENT`

Definizione normativa:

> `I` significa che la sovrapposizione delle due mutation non introduce alcun safety predicate M1 condiviso nello scope considerato.

`I` **non** significa:

- assenza garantita di row-lock contention;
- assenza di FK/constraint interaction conservativa;
- parallelismo fisico garantito;
- assenza di implementation over-serialization.

Esempio intenzionale:

```text
OBJ.RENAME(P)
×
OBJ.ATTACH(P,S,C)

semantic = I
```

La realization M1 può comunque farle attendere incidentalmente sulla stessa Object row. Questa differenza deve essere resa visibile nella realization matrix.

---

## 5. Safety predicate catalog

### S-NAME-UNIQUE (`NU`)

Scope: due mutation possono introdurre/riutilizzare lo stesso stable model `(namespace,name)` nello stesso entity kind.

Safety:

```text
at most one current stable model entity
may own the qualified name
```

---

### S-VERSION-SET (`VS`)

Scope: mutation concorrenti modificano o usano il current version set della stessa lineage per allocation/source eligibility.

Safety:

```text
version allocation and source eligibility
must be evaluated against one serially coherent
current version set
```

`max(existing)+1` e la regola source-not-current-max devono appartenere allo stesso coherent state.

---

### S-DRAFT-GENERATION (`DG`)

Scope: mutation basate sulla stessa exact DRAFT generation / `expected_revision`.

Safety:

```text
operations based on the same candidate generation
cannot independently commit incompatible outcomes
```

Copre `REVISE`, `PUBLISH`, `DELETE_DRAFT` della stessa exact DRAFT generation.

---

### S-LIFECYCLE-STATE (`LS`)

Scope: due mutation agiscono sulla lifecycle state della stessa exact version.

Safety:

```text
committed transitions must be explainable by a valid order of:
DRAFT -> PUBLISHED -> DEPRECATED
```

Nessuna transition può partire da uno status che non la ammette o applicarsi due volte come real transition.

---

### S-DEFAULT-VALIDITY (`DV`)

Scope: mutation che leggono/modificano default policy o lifecycle della exact version target/current-default.

Safety:

```text
default_version IS NULL
OR
default_version identifies a PUBLISHED exact version
of the same lineage
```

Inoltre first-publish auto-default e explicit set/clear devono essere spiegabili da un unico ordine seriale della default policy.

---

### S-BINDING-ADMISSION (`BA`)

Scope: una mutation crea/ribinda un nuovo lifecycle-sensitive exact dependency o risolve un implicit default in un persisted exact pin.

Safety:

```text
the selected exact dependency remains PUBLISHED
through admission/commit
```

Per implicit resolution, selection e resulting exact pin devono provenire da un coherent default/lifecycle state.

`CREATE_NEXT` clone di historical exact pin non è una nuova admission.

---

### S-ACTIVE-MODEL (`AM`)

Scope: mutation concorrenti possono attivare/disattivare un direct lifecycle-sensitive exact consumer edge o deprecare la dependency.

Safety:

```text
no committed active edge:
PUBLISHED consumer -> non-PUBLISHED exact dependency
```

Gli outcome devono essere spiegabili da un ordine seriale delle lifecycle transition coinvolte.

---

### S-REFERENCE-LIFETIME (`RL`)

Scope: una mutation crea/mantiene/rimuove una current cross-aggregate/domain reference mentre un'altra elimina il target.

Safety:

```text
reference wins
    -> target delete cannot commit

target delete wins
    -> new reference cannot commit

reference removal first
    -> target delete may become admissible
```

Nessun semantic cascade implicito.

---

### S-AGGREGATE-LIFETIME (`AL`)

Scope: una mutation agisce su un aggregate/owned child mentre una concurrent operation elimina l'intero stesso aggregate.

Safety:

```text
mutation wins
    -> may complete before aggregate deletion

delete wins
    -> later mutation cannot commit against/resurrect absent aggregate
```

Nessun partial resurrection o orphan child state.

---

### S-METADATA-LWW (`ML`)

Scope: concurrent write dello stesso metadata field per cui M1 dichiara last-write-wins (`description`).

Safety:

```text
each write is atomic
final value is exactly one committed candidate value
```

Nessun merge implicito, optimistic freshness o conflict failure è richiesto dal dominio.

---

### S-OBJECT-STATE (`OS`)

Scope: intrinsic mutation sullo stesso Object che dipendono/producono il complete current Object snapshot.

Safety:

```text
committed state and lifecycle snapshots
must be explainable by a serial ordering
of the semantic Object transitions
```

Previene lost update e lifecycle snapshot impossibili.

---

### S-PARENT-OWNERSHIP (`PO`)

Scope: `ATTACH`/`DETACH` concorre con `SCHEMA_CHANGE` del **parent** Object.

Safety:

```text
every committed outgoing ownership edge
must be valid against the parent's committed current exact schema
```

Se ATTACH vince, schema change osserva/preserva-o-fallisce l'edge; se schema change vince, ATTACH valida contro il nuovo schema. DETACH può rimuovere un blocker e rendere la migration ammissibile.

---

### S-OWNERSHIP-FACT (`OF`)

Scope: ATTACH/DETACH concorrenti riguardano lo stesso child/current ownership fact.

Safety:

```text
child current ownership evolves as a serial sequence between:
detached
or
attached exactly to (parent, slot)
```

Conseguenze:

- identical ATTACH converge senza duplicate event;
- identical DETACH converge senza duplicate event;
- DETACH non rimuove un edge diverso da quello richiesto;
- ATTACH non effettua implicit move;
- ATTACH vs DETACH final state deve essere serialmente spiegabile.

---

### S-SINGLE-OWNER (`SO`)

Scope: concurrent ATTACH con stesso child e desired `(parent,slot)` differenti.

Safety:

```text
child has at most one current owner/slot
```

Al massimo una desired ownership differente può essere creata.

---

### S-OWN-CYCLE (`OC`)

Scope: concurrent ownership edge-add il cui combined graph potrebbe introdurre un ciclo anche se ogni candidate edge è localmente valida sullo snapshot iniziale.

Safety:

```text
committed ownership graph remains acyclic
```

---

### S-RD-CERTIFIED-SET (`RC`)

Scope: RelationshipDefinition CREATE/RENAME e removal di blockers possono modificare il global certified Definition interpretation set.

Safety:

```text
committed Definition set remains:
- semantically non-duplicated
- cross-definition conflict-free
```

Ogni CREATE/RENAME è una atomic complete-Definition candidate transition. Definition DELETE può rimuovere blocker e rendere una successiva candidate ammissibile, ma non introduce nuovi conflict.

---

### S-REL-FACT (`RF`)

Scope: concurrent `REL.CREATE` rappresentano lo stesso factual relationship, anche tramite reciprocal Resolution, symmetric inverse assignment o inheritance-overlap equivalent access path.

Safety:

```text
exactly one current factual Relationship exists
for the semantic fact
```

Equivalent CREATE possono convergere sullo stesso `relationship_id`; esiste un solo complete runtime closure e un solo creation lifecycle event set.

---

### S-REL-LIFETIME (`RA`)

Scope: CREATE/DELETE/retry intorno alla stessa factual semantic association e specifica Relationship identity.

Safety:

```text
DELETE(X) affects only factual identity X
```

Se X viene eliminata e la stessa semantic association viene ricreata come Y, un late `DELETE(X)` è no-op e non può eliminare Y. Concurrent same-ID DELETE produce una sola real deletion/event set.

---

### S-REL-EVENT-SNAPSHOT (`ES`)

Scope: una real Relationship factual transition concorre con metadata mutabile denormalizzato nel complete lifecycle event set.

Safety:

```text
complete Relationship lifecycle event set
is derived from coherent committed metadata snapshots
observed by the Relationship mutation
```

Per `RelationshipDefinition.RENAME`:

- semantic names del complete event set sono tutti old-state o tutti new-state secondo un coherent committed Definition snapshot;
- nessun mix di metà old candidate e metà new candidate.

Per `Object.RENAME`:

- canonical names sono historical display metadata;
- non richiedono generic serialization;
- occorrenze dello stesso Object nel medesimo event set devono derivare da una coherent observation della mutation.

`ES` richiede snapshot coherence, **non** generic serialization fra metadata mutation e Relationship hot path.

---

## 6. Canonical sparse matrix rules

Qualunque cella non intercettata da una rule seguente resta `I`.

### 6.1 DataType × DataType

```text
DT.C × DT.C
  NU if same (namespace,name)

DT.C × DT.DL
  NU if CREATE reuses qualified name of lineage being deleted

DT.CN × DT.CN
  VS if same lineage

DT.CN × DT.DD
  VS if same lineage and draft removal changes relevant current version set

{DT.R, DT.P, DT.DD} × {DT.R, DT.P, DT.DD}
  DG if same exact DRAFT generation

DT.P × DT.P
  DG if same exact DRAFT generation
  DV if different DRAFTs same lineage and first-publish/default policy is relevant

DT.P × {DT.SD, DT.CD}
{DT.SD, DT.CD} × {DT.SD, DT.CD}
  DV if same lineage

{DT.SD, DT.CD} × DT.D
  DV when D targets current/selected default version

DT.P × DT.D
  LS if same exact version
  plus DV when first-publish/default state is material

DT.D × DT.D
  LS if same exact PUBLISHED version

same-lineage internal mutation × DT.DL
  AL when one operation acts on the aggregate that DL removes

DT.DESC × DT.DESC
  ML if same lineage
```

All other DT×DT scopes are `I` unless another explicit same-lineage predicate above applies.

### 6.2 ObjectTemplate × ObjectTemplate — same-lineage core

DataType-like lineage/version rules apply symmetrically:

```text
NU / VS / DG / LS / DV / AL / ML
```

using ObjectTemplate/ObjectTemplateVersion identities.

### 6.3 ObjectTemplate × ObjectTemplate — cross-lineage model dependencies

```text
OT.C or OT.R
×
OT.P / OT.SD / OT.CD / OT.D of parent candidate
  BA when C/R creates or rebinds a new exact parent OTV

OT.P(consumer)
×
OT.D(dependency)
  AM when consumer exact parent edge targets dependency

OT.D(consumer)
×
OT.D(dependency)
  AM when deprecating consumer removes an active blocker of dependency

OT.DL(consumer lineage)
×
OT.D(dependency)
  AM when lineage deletion removes active PUBLISHED exact-parent consumers

OT.C or OT.R
×
OT.DL(target lineage)
  RL when candidate adds/removes parent/component reference to target

OT.DD(consumer draft)
×
OT.DL(target lineage)
  RL when draft removal removes a current blocker

OT.DL(consumer lineage)
×
OT.DL(target lineage)
  RL when consumer lineage contains external references to target
```

`OT.CN` clone of an existing exact pin is not a new `BA` admission.

### 6.4 DataType × ObjectTemplate

```text
OT.C or OT.R
×
DT.P / DT.SD / DT.CD / DT.D
  BA when candidate property creates/rebinds exact DTV

OT.C or OT.R
×
DT.DL
  RL when candidate adds/removes property reference to target DT lineage

OT.P
×
DT.D
  AM when PUBLISH would activate property edge to DTV being deprecated

OT.D
×
DT.D
  AM when OTV consumer deprecation removes active blocker of DTV deprecation

OT.DD
×
DT.DL
  RL when DRAFT removal removes current DTV-lineage blocker

OT.DL
×
DT.D
  AM when OT lineage deletion removes active OTV consumers

OT.DL
×
DT.DL
  RL when OT lineage contains property references to DT target
```

All other DT×OT scopes are `I`.

### 6.5 ObjectTemplate × Object / Ownership

```text
OBJ.C
×
OT.P / OT.SD / OT.CD / OT.D
  BA when the OT mutation affects explicit/default target OTV admission

OBJ.C
×
OT.DL
  RL when CREATE introduces Object -> exact OTV reference to deleted lineage

OBJ.SC
×
OT.P / OT.D
  BA when OT mutation concerns exact target OTV of schema change

OBJ.DEL
×
OT.DL
  RL when Object deletion removes a current reference to target OT lineage
```

Important intentional `I`:

```text
OBJ.SC × OT.DL = I
```

because `Object.template_id` is unchanged and the lineage reference existed before and after schema change.

`OBJ.RN`, `OBJ.DC`, `OBJ.A`, `OBJ.DET` consume already-bound historical schema and do not create new OTV lifecycle admission.

### 6.6 Object / Ownership internal

```text
{OBJ.RN, OBJ.DC, OBJ.SC, OBJ.DEL}
×
{OBJ.RN, OBJ.DC, OBJ.SC, OBJ.DEL}
  OS when same Object and both are real intrinsic/current-state transitions

OBJ.SC(P)
×
OBJ.A(P,S,C)
  PO when schema-changed Object is ATTACH parent

OBJ.SC(P)
×
OBJ.DET(P,S,C)
  PO when schema-changed Object is DETACH parent

OBJ.A(P,S,C)
×
OBJ.A(P,S,C)
  OF for identical desired ownership

OBJ.A(P1,S1,C)
×
OBJ.A(P2,S2,C)
  SO when desired ownership differs

OBJ.A edge1
×
OBJ.A edge2
  OC when combined committed graph would form a cycle

OBJ.A
×
OBJ.DET
  OF when same child/current ownership fact is involved

OBJ.DET
×
OBJ.DET
  OF when same child/current ownership fact is involved

OBJ.A
×
OBJ.DEL
  RL when real ATTACH creates current reference to Object being deleted

OBJ.DET
×
OBJ.DEL
  RL when DETACH removes current ownership reference blocking delete
```

Intentional `I` examples:

```text
OBJ.RN(P) × OBJ.A(P,S,C) = I
OBJ.DC(P) × OBJ.A(P,S,C) = I
OBJ.SC(C) × OBJ.A(P,S,C) = I
```

The realization may still over-serialize some of these.

### 6.7 RelationshipDefinition internal

```text
RD.C × RD.C
  RC when candidates are equivalent or cross-conflicting

RD.C × RD.RN
  RC when create candidate and renamed candidate may conflict/equivalate

RD.RN × RD.RN
  RC for same Definition complete candidate transition
  or different Definitions whose renamed candidates may conflict

RD.C or RD.RN
×
RD.DEL(other)
  RC when deleted Definition is a blocker of the candidate certified set

RD.RN × RD.DEL
  AL when same Definition

RD.DEL × RD.DEL
  AL when same Definition
```

Definition DELETE only removes conflict-set members; it does not itself introduce a conflict.

### 6.8 ObjectTemplate × RelationshipDefinition

```text
RD.C × OT.DL
  RL when Definition candidate introduces Resolution endpoint reference to target lineage

RD.DEL × OT.DL
  RL when Definition deletion removes Resolution endpoint reference to target lineage
```

`RD.RN × OT.DL = I` because Resolution endpoint refs do not change.

All exact OTV lifecycle/default mutations are `I` with RD operations: RelationshipResolution depends on stable lineage, not exact OTV lifecycle.

### 6.9 RelationshipDefinition × Relationship runtime

```text
RD.RN × REL.C
  ES when same Definition and CREATE is a real factual transition

RD.RN × REL.DEL
  ES when same Definition and DELETE is a real factual transition

RD.DEL × REL.C
  RL when real CREATE uses Definition being deleted

RD.DEL × REL.DEL
  RL when Relationship DELETE removes current blocker of Definition delete
```

Idempotent `REL.C` convergence with no factual transition produces no lifecycle event set and therefore does not activate `ES`.

### 6.10 Relationship runtime internal

```text
REL.C × REL.C
  RF when both requests represent the same absent factual relationship

REL.C × REL.DEL
  RA when DELETE targets the current factual identity of the same semantic fact

REL.DEL × REL.DEL
  RA when same relationship_id
```

Different factual Relationship mutation are normally `I`; generic Relationship graph has no ownership-style acyclicity/global graph predicate.

### 6.11 Object × Relationship runtime

```text
OBJ.RN(O) × REL.C
  ES when O participates in the real factual transition

OBJ.RN(O) × REL.DEL
  ES when O participates in the real factual transition

OBJ.DEL(O) × REL.C
  RL when real CREATE introduces current reference to O

OBJ.DEL(O) × REL.DEL
  RL when Relationship removal removes a current blocker of O delete
```

Intentional `I`:

```text
OBJ.DC × REL.C/REL.DEL
OBJ.SC × REL.C/REL.DEL
OBJ.A  × REL.C/REL.DEL
OBJ.DET× REL.C/REL.DEL
```

Relationship endpoint admission uses stable `Object.template_id`, not properties, exact `template_version` or ownership state.

### 6.12 Completely independent cross-domain blocks

All cells in these cross-domain blocks are `I`:

```text
DataType × Object
DataType × RelationshipDefinition
DataType × Relationship
ObjectTemplate × Relationship runtime
Object × RelationshipDefinition
```

These declarations are normative: the independence has been evaluated and is not an omission.

Examples of the architectural reason:

- Object runtime consumes DTV only through already-certified exact OTV model state;
- RelationshipDefinition M1 has no typed property schema;
- Relationship runtime endpoint admission uses stable ObjectTemplate lineage assignments;
- RelationshipResolution already owns ObjectTemplate endpoint-lineage references;
- Object/ownership runtime state does not participate in RelationshipDefinition conflict certification.

---

## 7. Multi-predicate cells

A concrete pair may activate more than one predicate when multiple scopes are simultaneously true.

The matrix therefore associates a **set** of predicates with the concrete race; it does not select an arbitrary “primary” predicate.

Example class:

```text
same-lineage lifecycle mutation
+
cross-lineage active dependency relation
```

may require both a local lifecycle/default predicate and `AM` depending on the actual entities involved.

---

## 8. Predicate vs mechanism

A safety predicate does not imply a specific technical mechanism.

Examples:

```text
ES
  -> requires coherent snapshot
  -> does NOT imply generic exclusive serialization

RL
  -> requires valid lifetime ordering
  -> mechanism may later be FK RESTRICT plus UoW ordering

RF
  -> requires factual convergence
  -> realization may use exact-view uniqueness rather than pre-existing row lock
```

The realization document must preserve this distinction.

---

## 9. Realization matrix contract

After PostgreSQL detail design, a second matrix must map every non-trivial semantic cell to:

```text
operation A
operation B
scope qualifier
semantic predicate(s)
concurrency owner / authority
DB constraint / CAS / row lock / advisory gate
isolation assumption
retry/convergence behavior
required real PostgreSQL race test
```

Required traceability:

```text
Invariant
    -> semantic matrix cell
    -> safety predicate
    -> PostgreSQL authority/mechanism
    -> real concurrency test
```

Strong completion rule:

> if a non-trivial semantic cell cannot be mapped to a concrete, testable PostgreSQL authority/mechanism, the concurrency design is not closed.

Likewise, any realization serialization applied to a semantic `I` cell must be documented as intentional implementation over-serialization rather than reinterpreted as a domain invariant.

---

## 10. Evolution rule

Any future mutation primitive must, before implementation:

1. be added to the canonical operation census;
2. be compared with every existing mutation;
3. reuse an existing safety predicate or introduce a justified new one;
4. update the realization matrix;
5. derive/update real PostgreSQL concurrency tests.

No future feature may bypass this step by adding an isolated lock or constraint without first defining the semantic race it protects.
