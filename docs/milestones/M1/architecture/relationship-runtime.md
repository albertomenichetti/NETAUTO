# M1 — Runtime Relationship

**Status:** DRAFT

## 1. Factual aggregate root

Una factual runtime association possiede una stable identity:

```text
Relationship
------------
id
relationship_definition_id
```

`Relationship.id`:

- è opaque UUIDv4;
- è generato esclusivamente dal kernel;
- non è caller-supplied;
- è immutable;
- identifica il factual relationship, non una singola resolved view.

`relationship_definition_id` è stable per la lifetime della Relationship.

## 2. Runtime resolved child state

Concettualmente:

```text
RuntimeRelationshipResolution
-----------------------------
relationship_id
resolution_id
from_object_id
to_object_id
```

Le runtime rows sono authoritative child state della factual Relationship aggregate.

Non sono aggregate indipendenti e non possiedono public CRUD/lifecycle autonomo.

La physical row key è persistence detail da finalizzare.

## 3. Relationship resolution-based CREATE

Kernel/application primitive concettuale:

```text
CREATE Relationship(
    resolution_id,
    from_object_id,
    to_object_id
)
```

`relationship_definition_id` da solo non è sufficiente come CREATE selector.

La selected Resolution esprime il semantic perspective da cui il caller sta descrivendo il fatto.

## 4. Endpoint admission

Per selected Resolution `R`:

```text
from_object.template_id
    == R.from_template_id
    OR descendant-of R.from_template_id

to_object.template_id
    == R.to_template_id
    OR descendant-of R.to_template_id
```

Admission dipende esclusivamente da stable lineage type assignment.

Non dipende da:

```text
Object.template_version
Object properties
Object canonical_name
OTV lifecycle/default
```

Normale Object `SCHEMA_CHANGE` non richiede Relationship revalidation.

## 5. Factual endpoint assignment

### Non-symmetric

La selected Resolution determina quale Object occupa quale endpoint perspective.

L'assegnazione non è intercambiabile.

Esempio:

```text
R1: Person -> Person / manages
R2: Person -> Person / managed_by
```

CREATE:

```text
R1 / Alice -> Bob
```

rappresenta un factual relationship diverso da:

```text
R1 / Bob -> Alice
```

### Symmetric

La factual pair è unordered semanticamente:

```text
{A,B}
```

Qualunque Resolution/assignment semanticamente applicabile alla stessa pair deve convergere sulla stessa factual Relationship.

## 6. Deterministic complete runtime closure

Ogni factual Relationship deve materializzare tutte le object-relative resolved access paths richieste dal proprio Definition aggregate.

### 6.1 Non-symmetric

Dato selected Resolution `R1` e input `A -> B`, con reciprocal Resolution `R2`:

```text
R1 / A -> B
R2 / B -> A
```

sono il complete runtime set.

Se `A == B`, restano due runtime rows quando `R1 != R2`.

Non vengono aggiunte assignment inverse ulteriori anche se, per inheritance overlap, sarebbero type-compatible: rappresenterebbero l'opposto factual relationship.

### 6.2 Symmetric

Per una factual unordered pair `{A,B}` il runtime closure è:

> il set di tutte le tuple distinte `(resolution_id, from_object_id, to_object_id)` ottenibili usando ogni model Resolution della Definition e entrambe le assignment `(A,B)` / `(B,A)` che soddisfano i rispettivi lineage compatibility predicate.

Questo produce:

- same-template, A != B: due runtime rows con la stessa Resolution id;
- same-template self-loop: una runtime row;
- different-template disjoint spaces: normalmente due rows reciproche;
- different-template overlapping spaces: fino a quattro runtime rows.

Il numero è bounded in M1 perché una Definition possiede al massimo due model Resolution.

## 7. Factual endpoint-pair coherence

Per ogni `Relationship.id` esiste una sola factual endpoint pair.

Tutte le runtime rows devono:

- usare esclusivamente gli Object di quella pair;
- referenziare Resolution della stessa `relationship_definition_id`;
- costituire esattamente la deterministic complete closure prevista.

Sono vietati aggregate parziali o mescolati.

## 8. Exact resolved-view uniqueness

Semantic invariant:

```text
(resolution_id, from_object_id, to_object_id)
```

può appartenere ad al massimo una current factual Relationship.

Questa è l'autorità semantica per factual duplicate detection M1.

## 9. CREATE idempotency

Pipeline concettuale:

```text
load selected Resolution
load from/to Object
validate selected endpoint admission

lookup exact runtime view
(resolution_id, from_object_id, to_object_id)

if exists:
    return its factual Relationship
    no mutation
    no lifecycle event set

if absent:
    load already-certified complete Definition Resolution set
    derive deterministic complete runtime closure
    validate complete candidate closure
    ensure no exact view belongs to another factual Relationship
    create Relationship header
    create complete runtime closure
    create required lifecycle semantic-view event set
    commit atomically
```

CREATE effettuate tramite Resolution reciproche o, per symmetric Definition, tramite assignment inverse, convergono sulla stessa factual Relationship quando rappresentano lo stesso fatto.

## 10. Runtime semantic read projection

Raw runtime lookup naturale:

```text
RuntimeRelationshipResolution
WHERE from_object_id = O
```

restituisce tutti gli access path concreti verso factual Relationship visibili da O.

A causa di inheritance overlap, più runtime rows possono rappresentare la stessa object-relative semantic association.

Quindi distinguiamo:

```text
RuntimeRelationshipResolution
    -> resolved storage/index model

ObjectRelationshipView
    -> semantic read projection
```

La semantic projection collassa rows equivalenti per la stessa factual Relationship/object perspective.

Concettualmente la distinct semantic view è identificata da:

```text
relationship_id
from_object_id
to_object_id
current relationship name
```

Il read non richiede ricerca su `to_object_id` per scoprire tutte le association di O.

## 11. DELETE primitive

Kernel primitive:

```text
DELETE Relationship(relationship_id)
```

Casi:

```text
Relationship exists
    -> remove complete runtime child set
    -> remove header
    -> append required RELATIONSHIP_DELETED semantic-view event set

Relationship absent
    -> successful idempotent no-op
```

Nessuna runtime child row è eliminabile singolarmente.

## 12. ABA safety

Scenario:

```text
Relationship X deleted
same semantic association later recreated as Y
late DELETE(X)
```

La late delete è no-op e non può rimuovere Y.

Per questo M1 non usa delete-by-semantic-tuple come kernel primitive.

## 13. Self-loop

Self-loop sono ammessi quando endpoint admission lo consente.

### Symmetric self-loop

Normalmente una sola runtime row e una sola distinct lifecycle semantic view.

### Non-symmetric self-loop

Due Resolution semanticamente diverse possono produrre:

```text
A manages A
A managed_by A
```

come due runtime rows e due distinct semantic views della stessa factual Relationship.

## 14. Generic graph semantics

Relationship non è component ownership.

Non applica:

```text
single owner
acyclicity
forest semantics
subtree lifecycle
implicit detach
```

Relationship graph può contenere cicli e self-loop.

## 15. Delete interactions

Current factual Relationship blocca:

```text
Object.DELETE
RelationshipDefinition.DELETE
```

Nessun cleanup implicito.

Object DELETE è semanticamente bloccata se esiste una current runtime semantic association dell'Object. Grazie alla complete object-relative materialization, ogni endpoint non-self compare in almeno una runtime row come `from_object_id`.

Entrambe le runtime Object columns restano comunque veri current references.

