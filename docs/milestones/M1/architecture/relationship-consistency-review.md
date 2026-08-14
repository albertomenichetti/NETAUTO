# M1 — Relationship R2 Consistency Review

**Status:** REVIEW COMPLETE — R2 semantics frozen; persistence/concurrency technical closure integrated through REALIZE-12..15.

## 1. Scopo

Questo documento registra il consistency pass finale del redesign Relationship R2 e il successivo technical closure outcome.

R2 sostituisce integralmente la precedente architecture Relationship basata su:

```text
source_template
target_template
forward_name
reverse_name
canonical source/target runtime edge
```

Il vecchio modello non è più normativo.

## 2. Motivazione del redesign

Il precedente modello accoppiava eccessivamente:

- stable relationship type;
- symmetry inference;
- navigation direction;
- runtime endpoint ordering;
- lifecycle projection;
- future Relationship properties.

R2 separa:

```text
RelationshipDefinition
RelationshipResolution
Relationship
RuntimeRelationshipResolution
```

e materializza esplicitamente il resolved graph sia model-plane sia data-plane.

## 3. Cross-domain consistency — ObjectTemplate

`RelationshipResolution.from_template_id/to_template_id` sono stable lineage references.

Conseguenze confermate:

- bloccano ObjectTemplate whole-lineage hard delete;
- non referenziano exact OTV;
- non bloccano OTV deprecation;
- non richiedono default/PUBLISHED exact version;
- non entrano nell'active-model-graph exact dependency invariant.

Parent lineage M1 è stable, quindi Resolution endpoint-space overlap non cambia a causa di una normale OTV mutation.

## 4. Cross-domain consistency — Object

Runtime endpoint admission dipende esclusivamente da:

```text
Object.template_id
stable ObjectTemplate ancestry
```

Normale Object `SCHEMA_CHANGE` modifica soltanto `template_version`.

Quindi:

```text
Object.RENAME
Object.DATA_CHANGE
Object.SCHEMA_CHANGE
```

non invalidano Relationship correnti e non richiedono runtime Relationship revalidation.

Object DELETE continua a richiedere rimozione esplicita di ogni current Relationship association.

## 5. Ownership boundary

Ownership e Relationship restano semanticamente distinti.

Ownership:

```text
single-owner
acyclic
forest
component-slot contract
```

Relationship:

```text
generic association
cycles allowed
self-loop allowed
resolved multi-view materialization
```

Nessun ownership invariant viene riutilizzato sul Relationship graph.

## 6. Model-plane resolved contract

Definition aggregate:

```text
RelationshipDefinition
    id
    symmetric

RelationshipResolution*
    id
    definition_id
    from_template_id
    to_template_id
    name
```

Shape:

```text
non-symmetric
    -> 2 reciprocal Resolution
    -> distinct names

symmetric same-template
    -> 1 Resolution

symmetric different-template
    -> 2 reciprocal Resolution
    -> same name
```

Resolution id è stable e name-independent.

## 7. Runtime resolved contract

Factual aggregate:

```text
Relationship
    id
    relationship_definition_id

RuntimeRelationshipResolution*
    relationship_id
    resolution_id
    from_object_id
    to_object_id
```

Runtime closure:

```text
non-symmetric
    -> selected endpoint assignment preserved
    -> reciprocal object-relative views

symmetric
    -> all distinct applicable resolution/object assignment views
       for the unordered factual endpoint pair
```

Inheritance overlap può produrre più runtime access rows per la stessa object-relative semantic association.

## 8. Semantic read vs storage resolved rows

`RuntimeRelationshipResolution` è resolved storage/index state.

`ObjectRelationshipView` è semantic read projection.

Raw lookup:

```text
WHERE from_object_id = O
```

è sufficiente a trovare tutti gli access path di O.

La semantic projection deduplica overlapping rows che descrivono la stessa:

```text
relationship_id
from_object
to_object
relationship_name
```

## 9. Lifecycle correction

La precedente architecture usava canonical source/target event orientation e forward/reverse names.

R2 sostituisce tale modello.

Una factual Relationship transition produce:

> un event per ogni distinct object-relative semantic view.

Event cardinality non coincide necessariamente con runtime row cardinality.

Esempi:

```text
ordinary two-endpoint relationship
    -> normalmente 2 events

symmetric same-template self-loop
    -> 1 event

non-symmetric self-loop with two distinct names
    -> 2 events

inheritance-overlap symmetric runtime closure with 4 rows
    -> può produrre solo 2 semantic-view events
```

## 10. Lifecycle event-set atomicity

Per Relationship:

```text
factual header mutation
+
complete runtime closure mutation
+
complete required lifecycle event set
```

sono una singola atomic transition.

Questo generalizza il precedente Object changelog invariant da single-event a event-set atomicity.

Per intrinsic Object e ownership mutation l'event set mantiene cardinalità 1.

## 11. Future Relationship properties seam

R2 isola la futura schema evolution:

```text
RelationshipDefinition
    -> stable topology/navigation

future RelationshipDefinitionVersion
    -> typed property schema

Relationship
    -> future exact RDV pin + factual properties

RuntimeRelationshipResolution
    -> unchanged access-path state
```

Una property migration può fallire o mantenere una factual Relationship sulla vecchia RDV senza reinterpretare l'associazione graph o le runtime resolution views.

## 12. Baseline/current code delta

L'implementazione pre-M1 dovrà essere sostituita dove assume:

- `source_template_id/target_template_id` sulla Definition;
- `forward_name/reverse_name`;
- exact OTV based compatibility;
- source/target runtime Relationship row;
- one-row-per-factual-edge persistence;
- directed/symmetric inference/canonical endpoint ordering;
- one lifecycle Relationship event con source/target projection;
- duplicate CREATE come errore;
- missing runtime DELETE come errore;
- Relationship conflict checks durante OTV publication.

R2 non richiede backward compatibility con tale baseline sperimentale.

## 13. Freeze and technical closure outcome

Il dominio Relationship è semanticamente frozen per M1.

Le seguenti voci, precedentemente tecniche e aperte, sono ora chiuse e normative:

```text
PostgreSQL physical schema
    -> PERSIST-01..15

DB constraint/FK/UNIQUE layout
    -> persistence-model.md

model-plane conflict serialization
    -> REALIZE-12 / RELATIONSHIP_DEFINITION_CONFLICT_GATE

runtime factual uniqueness + convergence retry
    -> REALIZE-13 / exact-view PK + fresh semantic UoW

exact transaction isolation / lock strength
    -> READ COMMITTED + PERSIST-19 / REALIZE-15

lifecycle metadata observation
    -> REALIZE-14 / one SQL statement snapshot

persistence/index optimization baseline
    -> PERSIST-15, no ancestry closure/reverse authority table

real PostgreSQL race coverage
    -> PGTEST-01..02
```

Restano prima del final M1 architecture freeze aspetti di transport/application e test-harness realization, non scelte aperte di Relationship persistence/concurrency:

- REST/DTO and public error/status shape;
- PGTEST-03 deterministic harness contract and later implementation details.
