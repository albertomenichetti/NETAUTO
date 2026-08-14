# M1 — Relationship Concurrency & Transaction Contracts

**Status:** DRAFT

## 1. Principio

Relationship M1 deve preservare strong consistency senza introdurre un generic graph-wide lock.

Le garanzie derivano da:

- stable endpoint structural facts;
- persistence referential integrity;
- exact runtime uniqueness;
- model-plane serialization dei RelationshipDefinition conflict predicate;
- per-definition coordination dove runtime lifecycle event dipende dai mutable directional labels.

Il concrete PostgreSQL mechanism viene deciso negli implementation/concurrency steps.

## 2. Structural facts che non cambiano nelle normali operation

Le seguenti facts sono stable:

```text
Object.template_id
ObjectTemplate parent lineage
RelationshipDefinition.source_template_id
RelationshipDefinition.target_template_id
```

Di conseguenza runtime type compatibility non può essere invalidata da:

```text
Object.RENAME
Object.DATA_CHANGE
Object.SCHEMA_CHANGE
OTV publish/deprecate/default changes
```

Questa proprietà evita endpoint locks generalizzati per preservare compatibility.

## 3. Relationship CREATE predicates

Al commit devono valere:

```text
definition exists
source Object exists
target Object exists
endpoint compatibility holds
runtime edge uniqueness holds
```

Per symmetric definition deve essere applicata la canonical endpoint representation prima della uniqueness authority.

## 4. Nessun global Relationship graph lock

Relationship graph:

- può contenere cicli;
- non ha single-owner;
- non ha graph-wide acyclicity predicate.

Quindi CREATE/DELETE runtime non acquisiscono un global graph write gate analogo all'ownership graph.

## 5. Runtime uniqueness authority

Per directed definition:

```text
unique(D, source, target)
```

Per symmetric definition:

```text
unique(D, canonical_endpoint_1, canonical_endpoint_2)
```

deve essere authoritative al commit.

Scenario:

```text
T1 CREATE D/A/B
T2 CREATE D/A/B
```

Risultato:

```text
one current Relationship
both operations may converge successfully
one lifecycle creation event
```

Per symmetric definition lo stesso vale per concurrent:

```text
T1 CREATE D/A/B
T2 CREATE D/B/A
```

## 6. CREATE vs Object.DELETE

Race:

```text
T1 Relationship.CREATE(D,A,B)
T2 Object.DELETE(A)
```

Required serial outcomes:

```text
CREATE wins
    -> Relationship current reference exists
    -> Object.DELETE fails

DELETE wins
    -> A no longer exists
    -> Relationship.CREATE fails
```

È vietata una current Relationship verso Object cancellato.

FK/referential authority deve essere `RESTRICT` semantics, non cascade cleanup.

## 7. DELETE Relationship vs Object.DELETE

Race:

```text
T1 Relationship.DELETE(R)
T2 Object.DELETE(endpoint)
```

Sono valide serializzazioni coerenti:

```text
Relationship DELETE first
    -> reference removed
    -> Object DELETE may proceed if all other preconditions hold

Object DELETE attempt while R still exists
    -> Object DELETE fails
```

Relationship delete non è implicitamente eseguita da Object delete.

## 8. CREATE vs RelationshipDefinition.DELETE

Race:

```text
T1 Relationship.CREATE using D
T2 RelationshipDefinition.DELETE(D)
```

Required outcomes:

```text
CREATE wins
    -> D becomes current-referenced
    -> definition DELETE fails

definition DELETE wins
    -> D no longer exists
    -> CREATE fails
```

È vietata una current Relationship verso definition cancellata.

## 9. Definition model-plane conflict domain

`RelationshipDefinition.CREATE` e `RelationshipDefinition.RENAME` possono modificare il global set rispetto a:

```text
semantic equivalence
directional role conflict
```

Due transaction concorrenti non possono entrambe validare su uno stale snapshot e committare un conflicting set.

Normative requirement:

> model-plane mutation che può alterare il RelationshipDefinition semantic conflict set viene serializzata rispetto alla conflict validation + commit phase.

M1 può usare un model-plane write gate/concurrency domain dedicato.

Il concrete PostgreSQL primitive non è fissato qui.

## 10. Definition RENAME vs runtime mutation

Runtime lifecycle events denormalizzano:

```text
relationship_forward_name
relationship_reverse_name
```

Race:

```text
T1 Relationship.CREATE/DELETE using D
T2 RelationshipDefinition.RENAME(D)
```

Il committed runtime transition e il relativo event devono appartenere a una serial history coerente.

Valido:

```text
runtime transition before rename
    -> event stores old names
```

oppure:

```text
rename before runtime transition
    -> event stores new names
```

Vietato:

```text
runtime validation/semantic snapshot from one definition state
+
event labels from another state
```

Normative requirement:

> runtime Relationship mutation e RelationshipDefinition.RENAME si coordinano sulla specifica definition rispetto al mutable label snapshot.

Non serve un global lock per tutte le runtime Relationship mutation.

## 11. Object.RENAME vs Relationship lifecycle event

`canonical_name` e `destination_canonical_name` nei structural event sono historical display metadata, non endpoint semantic contract.

Relationship mutation non deve essere serializzata genericamente con Object.RENAME soltanto per questi campi.

L'event registra i canonical names osservati nello snapshot coerente della mutation.

Non promette che tali display names siano gli exact current names al physical commit instant in presenza di una independent concurrent rename.

## 12. Relationship DELETE idempotency e ABA

DELETE è exact-ID based:

```text
DELETE(R1)
```

Se:

```text
R1 deleted
same semantic tuple later recreated as R2
late retry DELETE(R1)
```

il retry è un no-op e non può rimuovere `R2`.

Questo è parte del semantic contract, non soltanto API convenience.

## 13. RelationshipDefinition whole-lineage references

RelationshipDefinition endpoint lineage references devono concorrere correttamente con ObjectTemplate whole-lineage delete.

Required serial outcomes:

```text
definition reference wins
    -> template lineage delete fails

template lineage delete wins
    -> definition create fails
```

RelationshipDefinition non costituisce invece lifecycle-sensitive exact-version consumer e non partecipa a OTV deprecation locking.

## 14. Lifecycle atomicity

Per una reale runtime mutation:

```text
current Relationship edge mutation
+
Object lifecycle event append
```

committano o rollbackano insieme.

Sono vietati:

```text
edge without event
event without edge transition
duplicate event for idempotent no-op
```

## 15. Read consistency

Current Relationship reads restituiscono committed runtime edge state.

Navigation reads che combinano edge e definition labels devono osservare uno snapshot transazionalmente coerente della singola operation.

Non è garantita repeatability fra richieste separate.

## 16. High-risk PostgreSQL concurrency tests

M1 deve includere almeno test reali PostgreSQL per:

1. concurrent identical directed CREATE;
2. concurrent inverse CREATE su symmetric definition;
3. Relationship CREATE vs Object DELETE;
4. Relationship DELETE vs Object DELETE;
5. Relationship CREATE vs RelationshipDefinition DELETE;
6. RelationshipDefinition CREATE vs conflicting CREATE;
7. RelationshipDefinition RENAME vs conflicting CREATE/RENAME;
8. RelationshipDefinition RENAME vs Relationship CREATE/DELETE lifecycle label snapshot;
9. ObjectTemplate whole-lineage DELETE vs RelationshipDefinition CREATE;
10. delete/recreate same semantic tuple + late DELETE retry sul vecchio relationship_id.

I test devono verificare outcome serialmente validi, non uno specifico lock scheduling.
