# M1 — Relationship Concurrency & Transaction Contracts

**Status:** DRAFT

## 1. Principio

R2 separa deliberatamente i concurrency cost:

```text
model-plane
    -> paga interpretation + global Definition conflict consistency

data-plane
    -> paga endpoint admission + factual uniqueness
       + complete closure + referential/transactional consistency
```

M1 non introduce un global Relationship graph lock.

Il concrete PostgreSQL mechanism viene definito successivamente.

## 2. Stable structural facts

Restano stable nelle normali operation:

```text
Object.template_id
ObjectTemplate parent lineage

RelationshipDefinition.symmetric

RelationshipResolution.id
RelationshipResolution.from_template_id
RelationshipResolution.to_template_id

Relationship.relationship_definition_id
```

Di conseguenza runtime type validity non è minacciata da:

```text
Object.RENAME
Object.DATA_CHANGE
Object.SCHEMA_CHANGE
OTV publish/deprecate/default changes
```

## 3. Model-plane conflict serialization

`RelationshipDefinition.CREATE` e `RENAME` possono modificare il global certified Resolution set rispetto a:

```text
Definition semantic equivalence
cross-definition Resolution conflict
```

Due transaction concorrenti non possono entrambe validare contro uno stale conflict snapshot e committare un invalid set.

Normative requirement:

> Definition CREATE/RENAME vengono serializzate rispetto alla complete candidate conflict-validation + commit phase.

Il concrete write gate/locking primitive non è fissato qui.

## 4. Definition DELETE

Definition DELETE non introduce nuovi Resolution conflicts.

Deve tuttavia concorrere correttamente con runtime Relationship CREATE e con external referential dependencies.

Current factual Relationship reference vince:

```text
Definition DELETE fails
```

Definition DELETE committa prima:

```text
later runtime CREATE using its Resolution fails
```

## 5. Runtime CREATE predicates

Al commit devono valere:

```text
selected Resolution exists
from/to Object exist
selected endpoint admission holds

complete Definition Resolution set is coherent
complete runtime closure is derivable

every candidate runtime row references that Definition/Resolution/Object set
exact resolved-view uniqueness holds
```

Il runtime non rivalida cross-definition name conflicts.

## 6. Concurrent CREATE dello stesso factual relationship

Esempio non-symmetric:

```text
T1 CREATE via R1: A -> B
T2 CREATE via reciprocal R2: B -> A
```

oppure symmetric inverse/overlap equivalent input.

Required outcome:

```text
exactly one factual Relationship header
exactly one complete runtime closure
exactly one required lifecycle creation event set
```

Le operation concorrenti possono entrambe essere osservabili come semantic success; il loser deve convergere sulla Relationship creata dal winner.

Exact runtime-view uniqueness è final authority per rilevare la collisione.

## 7. Partial closure forbidden

Per ogni real CREATE:

```text
Relationship header
+
complete RuntimeRelationshipResolution closure
+
complete distinct lifecycle semantic-view event set
```

committano oppure rollbackano insieme.

Sono vietati:

- header senza complete child set;
- subset di runtime rows;
- child rows semanticamente mescolate;
- runtime mutation senza complete lifecycle event set;
- lifecycle event set senza factual runtime mutation.

## 8. CREATE vs Object.DELETE

Race:

```text
T1 Relationship.CREATE involving Object A
T2 Object.DELETE(A)
```

Required serial outcomes:

```text
CREATE wins
    -> current runtime references exist
    -> Object DELETE fails

Object DELETE wins
    -> CREATE fails
```

Persistence current references devono avere RESTRICT semantics, non cascade cleanup.

## 9. Relationship DELETE vs Object.DELETE

```text
Relationship DELETE first
    -> complete factual association removed
    -> Object DELETE may proceed if all remaining preconditions hold

Object DELETE while Relationship still current
    -> Object DELETE fails
```

Object DELETE non chiama implicitamente Relationship DELETE.

## 10. CREATE vs RelationshipDefinition.DELETE

```text
CREATE wins
    -> factual Relationship references Definition
    -> Definition DELETE fails

Definition DELETE wins
    -> selected Resolution/Definition no longer exist
    -> CREATE fails
```

## 11. Definition CREATE vs ObjectTemplate whole-lineage DELETE

Resolution endpoint refs sono stable lineage dependencies.

```text
Definition CREATE wins
    -> template lineage delete fails

template lineage delete wins
    -> Definition CREATE fails
```

No coordination è richiesta con exact OTV deprecation.

## 12. RENAME vs runtime mutation

Definition RENAME modifica soltanto Resolution names.

Non invalida:

```text
resolution_id
endpoint compatibility
factual identity
runtime closure membership
```

Runtime CREATE/DELETE non viene genericamente serializzata con RENAME.

Lifecycle event `relationship_name` deve però provenire da un coherent committed model snapshot osservato dalla mutation.

Per una non-symmetric rename atomica non sono ammessi event set con semantic names provenienti da metà old candidate e metà new candidate.

Il concrete mechanism può essere, per esempio, una singola snapshot-consistent read del complete Resolution set; non è fissato qui.

## 13. Object.RENAME vs lifecycle event

Object canonical names nel Relationship lifecycle event sono historical display metadata.

Relationship mutation non viene serializzata genericamente con Object.RENAME soltanto per tali fields.

L'event set salva i canonical names osservati nello snapshot coerente della mutation.

## 14. Relationship DELETE concurrency

Due concurrent:

```text
DELETE(X)
DELETE(X)
```

convergono:

```text
one removes complete aggregate + deletion event set
other is idempotent no-op
```

Nessun duplicate deletion event set.

## 15. DELETE vs CREATE same semantic association

Stato iniziale: Relationship X esiste.

Valide serializzazioni:

```text
CREATE first
    -> converges on X
DELETE then removes X
    -> final absent
```

oppure:

```text
DELETE first
    -> removes X
CREATE then creates new Relationship Y
    -> final present
```

Nessuna resurrection di X.

## 16. Read consistency

Definition read:

```text
header + complete Resolution set
```

devono appartenere allo stesso committed snapshot.

Runtime factual read non deve osservare aggregate parziali.

Raw Object relationship lookup usa:

```text
RuntimeRelationshipResolution.from_object_id
```

e la semantic read projection deduplica eventuali overlapping Resolution access paths.

## 17. High-risk PostgreSQL concurrency tests

M1 deve verificare almeno:

1. concurrent CREATE della stessa non-symmetric factual Relationship tramite Resolution reciproche;
2. concurrent symmetric inverse CREATE;
3. symmetric inheritance-overlap CREATE con candidate closure multipla;
4. CREATE vs Object DELETE;
5. Relationship DELETE vs Object DELETE;
6. CREATE vs Definition DELETE;
7. Definition CREATE vs ObjectTemplate whole-lineage DELETE;
8. conflicting Definition CREATE vs CREATE;
9. Definition RENAME vs conflicting CREATE/RENAME;
10. Definition RENAME vs runtime CREATE/DELETE lifecycle-name snapshot;
11. concurrent DELETE dello stesso relationship_id;
12. DELETE/recreate same semantic association + late DELETE old id;
13. rollback test che impedisca header/closure/event-set partial commit.

I test verificano outcome serialmente validi, non uno specifico scheduling.

