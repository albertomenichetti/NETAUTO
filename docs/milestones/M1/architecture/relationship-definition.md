# M1 — RelationshipDefinition Aggregate

**Status:** DRAFT

## 1. Responsabilità

`RelationshipDefinition` è la stable semantic identity e structural classification di un relationship type.

Concettualmente:

```text
RelationshipDefinition
----------------------
id
symmetric
```

La Definition completa include sempre il proprio complete `RelationshipResolution` set.

## 2. Stable identity

```text
RelationshipDefinition.id
```

è l'identity autorevole.

Regole:

- opaque UUIDv4;
- generato esclusivamente dal kernel;
- immutabile;
- non specificabile dal caller.

`id` non è derivato da template o names.

## 3. Symmetry

```text
symmetric: bool
```

è structural contract esplicito e immutabile.

Semantica:

```text
symmetric = false
    -> i due endpoint perspectives non sono intercambiabili

symmetric = true
    -> la factual associazione fra i due endpoint è intercambiabile
```

`symmetric` non determina da solo il numero fisico di Resolution rows.

## 4. RelationshipResolution child state

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

Le Resolution sono authoritative child state della Definition aggregate.

Non sono:

- aggregate indipendenti;
- public CRUD resource autonome;
- cache ricostruibile opzionale.

## 5. Stable e mutable state

Immutabili:

```text
RelationshipDefinition.id
RelationshipDefinition.symmetric

RelationshipResolution.id
RelationshipResolution.relationship_definition_id
RelationshipResolution.from_template_id
RelationshipResolution.to_template_id
```

Mutabile tramite specifica Definition RENAME:

```text
RelationshipResolution.name
```

Cambiare symmetry, endpoint lineage, Resolution cardinality o membership significa cambiare relationship type e richiede una nuova Definition.

## 6. Naming

`RelationshipResolution.name`:

```text
[a-z][a-z0-9_]*
```

massimo 64 caratteri, senza normalization automatica.

Il name non è identity.

Una rename mantiene lo stesso `RelationshipResolution.id`.

## 7. Non-symmetric aggregate shape

Per:

```text
symmetric = false
```

esistono esattamente due Resolution `R1`, `R2`.

Devono essere reciproche:

```text
R1.from_template_id == R2.to_template_id
R1.to_template_id   == R2.from_template_id
```

e avere semantic names distinti:

```text
R1.name != R2.name
```

La regola vale sia con endpoint template diversi sia uguali.

Esempi validi:

```text
VM         -> Hypervisor / is_hosted_by
Hypervisor -> VM         / hosts
```

```text
Person -> Person / manages
Person -> Person / managed_by
```

## 8. Symmetric aggregate shape

Per:

```text
symmetric = true
```

esiste un solo semantic name per l'intera Definition.

### Same-template

Se i due endpoint template coincidono:

```text
T == T
```

esiste una sola Resolution:

```text
T -> T / name
```

### Different-template

Se i template sono diversi:

```text
A != B
```

esistono due Resolution reciproche:

```text
A -> B / name
B -> A / name
```

con:

```text
R1.name == R2.name
```

È ammesso che i due template-space si sovrappongano per inheritance.

## 9. Endpoint lineage dependency

`from_template_id` e `to_template_id` referenziano stable ObjectTemplate lineage.

Sono ammesse:

- lineage abstract;
- lineage senza default;
- lineage senza alcuna current PUBLISHED OTV.

Una Resolution:

- blocca whole-lineage hard delete dell'ObjectTemplate referenziata;
- non blocca exact OTV deprecation;
- non partecipa all'active-model-graph exact dependency invariant;
- non richiede exact version resolution.

## 10. CREATE contract

M1 espone due semantic command shape, anche se il transport/API potrà usare un unico discriminator `symmetric`.

### 10.1 Non-symmetric CREATE

Input concettuale:

```text
symmetric = false

endpoint_perspectives = [
    {
        template_id,
        name
    },
    {
        template_id,
        name
    }
]
```

L'ordine delle due perspective non ha significato.

Il domain:

1. valida entrambe le lineage;
2. valida i due names distinti;
3. genera Definition id;
4. genera due Resolution id;
5. costruisce le due Resolution reciproche;
6. valida aggregate shape;
7. valida semantic uniqueness/conflicts;
8. persiste header + complete Resolution set atomicamente.

### 10.2 Symmetric CREATE

Input concettuale:

```text
symmetric = true
endpoint_template_a
endpoint_template_b
name
```

La coppia dei template non ha ordine semantico.

Il domain genera:

- una Resolution se i template coincidono;
- due Resolution reciproche con lo stesso name se sono diversi.

## 11. RENAME contract

RENAME modifica soltanto Resolution names.

### 11.1 Non-symmetric

Il caller identifica stabilmente entrambe le Resolution tramite `resolution_id`:

```text
RENAME D:
[
    { resolution_id = R1, name = new_name_1 },
    { resolution_id = R2, name = new_name_2 }
]
```

Il domain verifica:

- R1/R2 appartengono a D;
- il complete Resolution set è coperto;
- i nuovi names sono validi e distinti;
- semantic equivalence/conflict invariants restano validi.

La rename è atomica.

### 11.2 Symmetric

Il caller fornisce un solo nuovo semantic name:

```text
RENAME D:
name = new_name
```

Il domain aggiorna una o entrambe le Resolution child al medesimo valore nella stessa UoW.

## 12. Semantic equivalence

La semantic signature di una Definition è:

```text
(
    symmetric,
    unordered complete semantic Resolution set
)
```

dove ogni Resolution semantic tuple è:

```text
(from_template_id, to_template_id, name)
```

Gli UUID di Definition/Resolution non partecipano alla semantic equivalence.

Due Definition con stessa signature non possono coesistere, indipendentemente dall'ordine con cui gli endpoint/perspective sono stati forniti alla CREATE.

## 13. DELETE

RelationshipDefinition DELETE è ammessa soltanto se:

```text
zero current factual Relationship
where relationship_definition_id = D
```

Una delete ammessa rimuove atomicamente:

```text
Definition header
+
complete RelationshipResolution child set
```

Nessun runtime Relationship viene eliminato implicitamente.

Historical lifecycle event non bloccano la delete.

## 14. Nessun lifecycle/versioning M1

M1 non introduce sulla Definition:

```text
DRAFT
PUBLISHED
DEPRECATED
version
default_version
revision
```

La Definition viene creata già utilizzabile.

## 15. Future versioning seam

Future `RelationshipDefinitionVersion` versionerà soltanto lo schema delle future factual Relationship properties.

Restano Definition-level e immutabili attraverso le version:

```text
symmetric
RelationshipResolution identity/membership
Resolution endpoint lineage
```

Resolution names restano stable-definition metadata mutabili tramite Definition RENAME, salvo futura diversa decisione esplicita.

