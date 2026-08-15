# M1 — ObjectTemplate Effective Schema & Certification

**Status:** DRAFT

## 1. Source of truth

L'autorità persistita di una ObjectTemplateVersion è costituita da:

```text
exact parent pin
+
local property declarations
+
local component declarations
```

Le declarations inherited non vengono materializzate nella child.

## 2. Effective schema resolution

L'effective schema è derivato deterministicamente percorrendo la exact parent chain root -> leaf.

Per ogni livello vengono aggiunte le sole local declarations di quella exact OTV.

Gli exact parent pins rendono la resolution riproducibile:

```text
Router@3 -> NetworkDevice@5
```

non viene modificato dalla futura creazione di `NetworkDevice@6`.

Effective ordering:

- ancestor/root property blocks prima, poi child blocks;
- ogni local property block ordinato per `position`;
- stessa regola per component slots;
- property e component ordering sono domini distinti.

Tutte le naming/override/collision invariants vengono valutate sull'effective schema completo.

M1 non introduce authoritative persistent effective-schema materialization.

Eventuali cache interne o precomputed execution structures sono implementation optimization e non source of truth né validation authority. Non costituiscono un JSON Schema compiler/projection o un secondo schema language pubblico.

## 3. DRAFT effective schema

Per una DRAFT:

```text
effective candidate
    =
immutable exact inherited snapshots
+
current local DRAFT snapshot
```

Una modifica di `parent_version`, local properties o local components cambia la candidate generation e incrementa la DRAFT `revision`.

La DRAFT persistita deve essere sempre well-formed.

Può però essere non publishable, per esempio se un exact dependency storico è ormai DEPRECATED.

## 4. Create ObjectTemplate

La create crea atomicamente:

```text
stable lineage identity
+
v1 DRAFT revision=1
+
exact parent pin, se presente
+
local properties
+
local component slots
```

Non è un normale risultato valido avere una lineage creata senza v1.

Root: parent assente.

Child: exact parent version explicit oppure implicit via `parent.default_version`; selected parent deve essere PUBLISHED fino al commit.

`abstract` viene stabilito alla create ed è immutabile.

La v1 può includere local declarations iniziali purché la candidate risultante sia well-formed.

La create non esegue auto-publish.

Qualsiasi failure causa rollback dell'intero aggregate.

## 5. Revise ObjectTemplateVersion

`revise` è una mutation atomica dell'intera candidate DRAFT.

```text
current DRAFT revision=N
+
requested changes
    ->
build complete candidate
    ->
resolve complete effective candidate schema
    ->
validate
    ->
persist atomically
    ->
revision=N+1
```

Precondizioni:

```text
status == DRAFT
revision == expected_revision
```

Non sono revisionabili:

```text
template_id
version
parent_template_id
stable lineage identity
abstract
```

Sono revisionabili solo dati version-specific nel rispetto delle evolution rules.

Una validation failure produce rollback completo e lascia revision invariata.

La candidate può essere well-formed ma non ancora publishable.

## 6. Publish certification

`publish(ObjectTemplateVersion)` è una certification atomica dell'intero effective schema.

Richiede:

```text
status == DRAFT
revision == expected_revision
```

La certification verifica almeno:

- final exact parent pin valido;
- inheritance aciclica;
- effective member names univoci;
- nessun property/property, slot/slot o property/slot collision;
- nessun inherited override/shadowing;
- property historical/evolution rules;
- `SCALAR`/`LIST`, `required` e `migration_default`;
- exact DataTypeVersion dependencies ammissibili;
- component target/evolution rules;
- naming rules.

Al successo:

```text
DRAFT revision=N
    ->
PUBLISHED revision=N
```

Publish non incrementa revision.

## 7. Publication vs runtime dataset

La publication certifica il **model-plane schema**, non la migrabilità immediata dell'intero runtime dataset.

Non deve:

- scansionare tutti gli Object;
- verificare che ogni Object sia migrabile;
- verificare gli attachment runtime correnti;
- eseguire detach;
- eseguire data migration.

Una OTV può essere pubblicata anche se alcuni Object esistenti richiederanno remediation prima del repinning.

## 8. Active model graph invariant

Principio M1:

> la strong lifecycle consistency viene pagata quando cambia il model-plane, non a ogni consumo del data-plane.

Invariante:

```text
If an ObjectTemplateVersion is PUBLISHED,
all of its direct lifecycle-sensitive exact-version
model dependencies MUST also be PUBLISHED.
```

In M1 lifecycle-sensitive exact dependencies includono almeno:

- exact parent ObjectTemplateVersion;
- exact DataTypeVersion pins delle properties.

Lineage-level references, come component `target_template_id`, non sono lifecycle-sensitive exact dependencies.

È sufficiente proteggere le direct dependencies.

Se ogni PUBLISHED node dipende soltanto da PUBLISHED direct dependencies, l'intera active closure è consistente transitivamente.

## 9. Deprecation consequence

Una exact dependency non può diventare DEPRECATED mentre un direct PUBLISHED model-plane consumer la usa.

Quindi:

```text
publish consumer
vs
deprecate dependency
```

devono essere fortemente consistenti.

Gli unici esiti ammessi sono:

```text
publish wins
    -> dependency deprecate fails due active consumer
```

oppure:

```text
deprecate wins
    -> consumer publish fails certification
```

Non può esistere un committed edge:

```text
PUBLISHED consumer
    ->
DEPRECATED exact dependency
```

## 10. Object create consequence

Un nuovo `Object` crea un direct binding verso una exact ObjectTemplateVersion PUBLISHED.

Grazie all'active-model-graph invariant, `Object create` non deve ricertificare a ogni richiesta lo status lifecycle dell'intera parent/DTV dependency closure.

Deve poter trattare la target OTV PUBLISHED come schema attivo già certificato.

Questo concentra il costo di lifecycle consistency sulle relativamente rare model-plane mutation invece che sul data-plane hot path.

## 11. Read consistency

Ordinary GET/list/effective-schema read restituiscono uno snapshot transazionalmente coerente della singola operation.

Non è garantita repeatability tra richieste separate.

Una effective-schema resolution deve osservare una exact parent chain e local declarations internamente coerenti.

Per DRAFT, local structure e `revision` devono rappresentare la stessa candidate generation.

Read usate per admission/mutation devono preservare fino al commit i predicate rilevanti:

```text
implicit default resolution
parent exact admission
DTV exact admission
set_default
publish
deprecate
delete
```
