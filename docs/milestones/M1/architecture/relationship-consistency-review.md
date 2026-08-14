# M1 — Relationship Consistency Review

**Status:** DRAFT

## 1. Scopo

Questo documento registra il consistency pass finale del dominio Relationship rispetto ai design M1 già consolidati di Object e ObjectTemplate e rispetto alla baseline implementativa pre-M1.

Non introduce nuove capability.

Serve come riferimento per gli implementation steps e per identificare chiaramente quali parti della baseline corrente devono essere sostituite.

## 2. Coerenze cross-domain confermate

### 2.1 Object SCHEMA_CHANGE non revalida Relationship

Runtime endpoint compatibility dipende da:

```text
Object.template_id
stable lineage ancestry
```

Normale Object `SCHEMA_CHANGE` mantiene `template_id`.

Quindi Relationship esistenti non richiedono revalidation durante schema migration.

### 2.2 Object DELETE richiede zero incident Relationship

Object DELETE non esegue relationship cleanup implicito.

Current incident Relationship sono external references e devono essere eliminate esplicitamente prima.

### 2.3 RelationshipDefinition -> ObjectTemplate è lineage-level

Una definition:

- blocca whole-lineage hard delete degli endpoint ObjectTemplate;
- non blocca exact OTV deprecation;
- non richiede current/default PUBLISHED version;
- non appartiene all'active-model-graph exact dependency set.

### 2.4 Ownership e Relationship restano grafi distinti

Ownership:

```text
single-owner
acyclic
forest
component-slot semantics
```

Relationship:

```text
generic association
cycles allowed
self-loop allowed
no implicit ownership/lifecycle composition
```

Nessun invariant deve essere riutilizzato accidentalmente fra i due graph domain.

## 3. Correzioni emerse durante consistency pass

### 3.1 Directionality class immutable

Poiché M1 deriva symmetry da:

```text
source lineage == target lineage
AND
forward_name == reverse_name
```

RelationshipDefinition `RENAME` non può cambiare tale classificazione.

Altrimenti edge già persistite verrebbero reinterpretate fra ordered e unordered semantics.

Normative rule:

```text
is_symmetric(before) == is_symmetric(after)
```

### 3.2 Common lifecycle event role generalization

Nel common changelog `object_id` non può più significare sempre genericamente "subject".

Per Relationship event:

```text
object_id = canonical source endpoint
destination_object_id = canonical target endpoint
```

Il significato preciso è quindi event-kind-specific.

### 3.3 Exact-ID Relationship DELETE

Runtime DELETE deve essere exact `relationship_id` based per evitare ABA:

```text
R1 delete
same tuple recreate -> R2
late delete R1
```

non può rimuovere R2.

### 3.4 Canonical name denormalization is display metadata

Directional labels della definition richiedono semantic snapshot coherence con runtime mutation.

Object canonical names invece sono mutable display metadata e non giustificano generic serialization con Object.RENAME.

### 3.5 Directed self-loop read projection

Un directed self-loop può ricoprire simultaneamente source e target role.

Una read projection `SELF` non deve perdere forward/reverse semantic role information.

## 4. Decisione esplicita su overlapping role della stessa definition

Non viene introdotto un generic self-conflict invariant sulla singola definition quando:

- forward/reverse name coincidono;
- endpoint lineage spaces si sovrappongono parzialmente.

Esempio potenzialmente valido:

```text
Device --connects_to--> Router
Device <--connects_to-- Router
```

con `Router IS-A Device`.

La runtime Relationship mantiene comunque canonical source/target.

L'eventuale ambiguità di navigation viene rappresentata tramite:

```text
relationship_definition_id
direction
```

e non risolta vietando il modello.

Solo l'equivalenza completa dei due directional role:

```text
same endpoint lineage
same name
```

produce symmetric semantics M1.

## 5. Baseline pre-M1 da sostituire

La baseline corrente non è normativa e contiene diversi comportamenti incompatibili col design frozen.

### 5.1 Exact OTV based relationship compatibility

Da rimuovere:

```text
Relationship compatibility
-> Object.template_version
-> exact OTV inheritance resolver
```

Target:

```text
Relationship compatibility
-> Object.template_id
-> stable lineage ancestry
```

### 5.2 Requirement di endpoint con PUBLISHED version

Da rimuovere dalla RelationshipDefinition CREATE.

Target: deve bastare l'esistenza della ObjectTemplate lineage.

### 5.3 Relationship conflict revalidation durante OTV publish

Da rimuovere.

Nel nuovo modello definition conflict dipende da stable lineage ancestry, quindi OTV lifecycle/pubblicazione non modifica gli endpoint spaces.

### 5.4 Runtime duplicate create come error

Da sostituire con idempotent convergence sulla Relationship current esistente.

### 5.5 Runtime delete missing come error

Da sostituire con idempotent no-op su exact relationship_id assente.

### 5.6 Symmetric reverse uniqueness

La baseline uniqueness exact `(definition, source, target)` va estesa con canonical endpoint representation per symmetric definition.

### 5.7 Lifecycle integration

La baseline changelog deve essere estesa a:

```text
RELATIONSHIP_CREATED
RELATIONSHIP_DELETED
```

con typed historical fields e atomicity col runtime edge mutation.

## 6. Persistence facts utili già coerenti

Le FK runtime Relationship verso:

```text
RelationshipDefinition
source Object
target Object
```

devono mantenere `RESTRICT` semantics.

La current exact tuple uniqueness è una buona authority per directed edge dopo il consolidamento delle idempotency semantics.

## 7. Freeze outcome

Con le decisioni consolidate nei documenti Relationship:

> il dominio Relationship è semanticamente frozen per M1.

Restano da definire nei successivi architecture/implementation contracts i meccanismi concreti di:

- PostgreSQL constraint/locking;
- Unit of Work;
- API DTO/failure mapping;
- persistence layout;
- integration/concurrency tests.

Tali decisioni non devono modificare le semantics frozen qui registrate.
