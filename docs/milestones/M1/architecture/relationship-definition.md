# M1 — RelationshipDefinition

**Status:** DRAFT

## 1. Responsabilità e shape

Concettualmente:

```text
RelationshipDefinition
----------------------
id
source_template_id
target_template_id
forward_name
reverse_name
```

`RelationshipDefinition` è il model-plane semantic contract di un relationship type.

Non contiene runtime state e non è ownership.

## 2. Stable identity

L'identity autorevole è:

```text
RelationshipDefinition.id
```

`id`:

- è opaco;
- è immutabile;
- viene generato esclusivamente dal kernel;
- M1 usa UUIDv4;
- non può essere specificato dal caller.

La quadrupla endpoint/names non è identity. È subject a semantic uniqueness invariants.

`RelationshipDefinition.id` è deliberatamente modellata come stable identity destinata a sopravvivere a future definition-versioning.

## 3. Endpoint contract

```text
source_template_id
target_template_id
```

referenziano sempre stable ObjectTemplate lineage.

Non referenziano:

```text
ObjectTemplateVersion
default_version
latest/highest published version
```

Gli endpoint sono immutabili per tutta la lifetime della definition.

Cambiare source/target significa cambiare relationship type e richiede una nuova definition.

Sono ammesse:

- lineage abstract;
- lineage senza current default;
- lineage senza alcuna PUBLISHED exact version;
- `source_template_id == target_template_id`.

La sola precondizione model-plane è l'esistenza della lineage.

## 4. RelationshipDefinition dependency verso ObjectTemplate

La reference:

```text
RelationshipDefinition -> ObjectTemplate lineage
```

è una lineage-level dependency.

Conseguenze:

- blocca whole-lineage hard delete della ObjectTemplate;
- non blocca OTV deprecation;
- non partecipa all'active-model-graph invariant;
- non richiede una PUBLISHED/default exact OTV.

## 5. Directional names

```text
forward_name
reverse_name
```

sono semantic directional labels.

Naming grammar M1:

```text
[a-z][a-z0-9_]*
```

Massimo 64 caratteri. Nessuna normalization automatica.

Forward role:

```text
source_template_id --forward_name--> target_template_id
```

Reverse role:

```text
target_template_id --reverse_name--> source_template_id
```

I names non sono identity e possono cambiare tramite specifica `RENAME`.

## 6. Symmetry derivata

M1 considera symmetric una definition iff:

```text
source_template_id == target_template_id
AND
forward_name == reverse_name
```

Questa è equivalenza completa dei due directional role.

La sola overlap/ancestor compatibility fra source e target spaces non implica symmetry.

Per evitare reinterpretazione retroattiva delle Relationship esistenti:

> la directionality class è immutabile.

Quindi una `RENAME` deve preservare:

```text
is_symmetric(before) == is_symmetric(after)
```

Non viene persistito o esposto un boolean `symmetric`.

## 7. Semantic equivalence

Due definition sono semanticamente equivalenti se coincidono direttamente:

```text
left.source == right.source
left.target == right.target
left.forward == right.forward
left.reverse == right.reverse
```

oppure se coincidono in orientamento inverso:

```text
left.source == right.target
left.target == right.source
left.forward == right.reverse
left.reverse == right.forward
```

Definition semanticamente equivalenti non possono coesistere.

L'identity autorevole rimane comunque `id`.

## 8. Directional conflict fra definition distinte

La semantic equivalence non esaurisce i conflitti possibili.

Ogni definition espone due directional role:

```text
(from_space, name, to_space)
```

Due role appartenenti a **definition distinte** sono in conflitto quando:

```text
same directional name
AND
from spaces overlap
AND
to spaces overlap
```

Con single stable ObjectTemplate inheritance, due lineage spaces si sovrappongono quando:

```text
A == B
OR
A descendant-of B
OR
B descendant-of A
```

L'overlap dipende esclusivamente dalla stable lineage ancestry.

Non dipende dall'esistenza o dal lifecycle di exact OTV.

La conflict analysis considera tutte le orientation rilevanti fra definition distinte.

Non viene introdotto un ulteriore divieto solo perché i due role della **stessa** definition hanno name uguale e endpoint spaces parzialmente sovrapposti. In tal caso la runtime Relationship conserva source/target canonici e le navigation view espongono la direction.

## 9. Modelling guideline

Una definition dovrebbe essere dichiarata:

> sulla lineage più generale per cui la relazione è semanticamente corretta per tutti i discendenti.

Scendere nell'albero solo quando la relationship semantics è realmente più specifica.

Una definition più specifica non va aggiunta soltanto per restringere artificialmente lo spazio di compatibility di una semantics già espressa da una definition più generale.

## 10. CREATE

Command concettuale:

```text
CREATE RelationshipDefinition(
    source_template_id,
    target_template_id,
    forward_name,
    reverse_name
)
```

Semantica:

1. source lineage esiste;
2. target lineage esiste;
3. names validi;
4. candidate rispetta semantic definition uniqueness;
5. candidate rispetta directional conflict rules rispetto alle definition esistenti;
6. kernel genera `id`;
7. definition viene persistita atomicamente e diventa immediatamente utilizzabile.

M1 non introduce:

```text
DRAFT
PUBLISHED
DEPRECATED
version
default_version
revision
```

per RelationshipDefinition.

## 11. RENAME

`RENAME` sostituisce atomicamente l'intera coppia:

```text
(forward_name, reverse_name)
```

anche se soltanto uno dei due valori cambia.

Non modifica:

```text
id
source_template_id
target_template_id
```

Prima del commit la candidate deve preservare:

- naming validity;
- REL semantic uniqueness;
- directional conflict rules;
- directionality class.

Non esiste partial field patch come semantic primitive.

M1 non introduce RelationshipDefinition revision token.

## 12. DELETE

RelationshipDefinition delete è ammessa soltanto se:

```text
zero current runtime Relationship references
```

La presenza di lifecycle event storici non blocca la delete.

La delete non:

- elimina Relationship implicitamente;
- modifica Object;
- modifica ObjectTemplate;
- elimina changelog event.

## 13. Definition read consistency

Ordinary reads restituiscono committed definition state.

Mutation/admission che dipendono da:

```text
definition existence
directional labels
definition conflict set
```

devono preservare i relativi predicate fino al commit secondo il concurrency contract.

## 14. Future definition versioning seam

Quando verranno introdotte typed Relationship properties, la stable definition potrà diventare il lineage-like anchor:

```text
RelationshipDefinition
    id
    endpoints
    directional semantic identity

RelationshipDefinitionVersion
    version
    lifecycle
    typed property schema
```

Gli endpoint restano structural contract della stable definition.
