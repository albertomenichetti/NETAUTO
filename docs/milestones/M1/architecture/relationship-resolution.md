# M1 — RelationshipResolution

**Status:** DRAFT

## 1. Responsabilità

`RelationshipResolution` è il model-plane resolved semantic perspective di una `RelationshipDefinition`.

Risponde alla domanda:

> dato un Object appartenente al `from_template` compatibility space, con quale semantic name può vedere/usare questa Relationship e quale `to_template` space deve soddisfare l'altro Object?

Concettualmente:

```text
RelationshipResolution
----------------------
id
relationship_definition_id
from_template_id
to_template_id
name
```

Non esistono `forward` o `reverse` role nel domain.

## 2. Resolution identity

`RelationshipResolution.id`:

- è kernel-generated UUIDv4;
- è stabile;
- non dipende da `name`;
- identifica una specifica endpoint perspective del Definition aggregate.

Serve come stable selector applicativo per runtime `Relationship.CREATE` e per non-symmetric Definition RENAME.

## 3. Capability applicability

Una Resolution `R` è applicabile come from-perspective a un ObjectTemplate lineage `T` iff:

```text
T == R.from_template_id
OR
T descendant-of R.from_template_id
```

L'expected related endpoint space è:

```text
R.to_template_id
```

anch'esso lineage-polymorphic.

L'applicabilità non dipende da exact OTV disponibili o dal loro lifecycle.

## 4. Model-plane capability read

Per un Object/ObjectTemplate lineage T, la primitive read naturale è:

```text
all RelationshipResolution
whose from_template space admits T
```

Il risultato espone già:

```text
resolution_id
relationship_definition_id
name
from_template_id
to_template_id
```

Non richiede inversione o ricostruzione di directional semantics.

## 5. Endpoint-space overlap

Con single stable ObjectTemplate inheritance, due lineage spaces `A`, `B` si sovrappongono quando:

```text
A == B
OR
A descendant-of B
OR
B descendant-of A
```

Questo overlap è una proprietà stable del lineage graph M1.

## 6. Cross-definition conflict

Due Resolution appartenenti a **Definition distinte** confliggono quando:

```text
same name
AND
from-template spaces overlap
AND
to-template spaces overlap
```

Definition che produrrebbero un tale conflict non possono coesistere.

Le Resolution della stessa Definition non sono valutate come conflicting fra loro: il loro overlap può essere intenzionale e viene gestito dalla runtime resolution closure.

## 7. Semantic equivalence e conflict

Semantic equivalence della Definition e Resolution conflict sono concetti distinti.

Equivalent Definition:

```text
same symmetric
+
same complete semantic Resolution set
```

Conflicting Definition:

```text
non necessariamente equivalenti,
ma almeno una coppia di Resolution cross-definition
viola la conflict rule
```

Per enforcement, la conflict validation può naturalmente intercettare anche duplicate Definition; la semantic equivalence resta un concetto di dominio esplicito.

## 8. Model-plane one-shot certification

Definition CREATE/RENAME devono:

1. costruire il complete candidate Resolution set;
2. validarne la shape;
3. validare semantic equivalence;
4. validare cross-definition Resolution conflicts;
5. preservare tali predicate fino al commit.

Una volta committato il model-plane, runtime Relationship mutation non ripete questa analisi.

## 9. RelationshipResolution non è public mutable aggregate

Non esistono primitive M1:

```text
CREATE RelationshipResolution
DELETE RelationshipResolution
rebind Resolution endpoint
add/remove Resolution
```

Il child state viene creato/mutato/cancellato esclusivamente dentro `RelationshipDefinition` operations.

## 10. Rename e conflict

Una Definition RENAME modifica Resolution names.

Prima del commit deve rieseguire semantic-equivalence/conflict validation sul complete candidate set.

Poiché endpoint/symmetry non cambiano, la rename non invalida factual runtime Relationship già esistenti.

## 11. ObjectTemplate whole-lineage delete

Una persisted Resolution è una external lineage reference.

Race:

```text
Definition CREATE wins
    -> referenced ObjectTemplate whole-lineage delete fails

ObjectTemplate whole-lineage delete wins
    -> Definition CREATE fails
```

Exact OTV deprecation/pubblicazione/default changes non richiedono RelationshipResolution revalidation.

