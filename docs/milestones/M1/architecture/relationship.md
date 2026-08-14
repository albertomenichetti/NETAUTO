# M1 — Relationship Architecture

**Status:** DRAFT

## 1. Scopo

Questo documento è l'indice normativo dell'architettura `Relationship` per M1.

Documenti collegati:

- `relationship-definition.md` — stable identity, endpoint contract, directional semantics, conflict rules, create/rename/delete;
- `relationship-runtime.md` — runtime edge identity, compatibility, directed/symmetric semantics, create/delete, navigation e lifecycle;
- `relationship-concurrency.md` — transaction boundary, consistency domains, referential races e high-risk concurrency cases;
- `relationship-consistency-review.md` — consistency pass finale cross-domain e principali delta rispetto alla baseline pre-M1;
- `object-lifecycle-changelog.md` — event stream unificato, incluso `RELATIONSHIP_CREATED` / `RELATIONSHIP_DELETED`.

I meccanismi PostgreSQL concreti — constraint, FK, lock mode, advisory/row locks, isolation level, retry e query shape — saranno definiti nei concurrency/persistence contract. Qui sono normative le semantics e le invarianti osservabili.

## 2. Responsabilità

`RelationshipDefinition` rappresenta una stable semantic identity per un tipo di associazione fra due ObjectTemplate lineage.

`Relationship` rappresenta un factual runtime edge che materializza una specifica definition fra due Object.

```text
RelationshipDefinition
    -> model-plane semantic contract

Relationship
    -> data-plane factual edge
```

Una Relationship non è ownership/composition e non eredita le invarianti di component ownership.

## 3. Principi M1

- `RelationshipDefinition.id` è stable semantic identity;
- gli endpoint della definition sono ObjectTemplate lineage references, non exact OTV;
- source/target endpoint contract sono immutabili;
- i directional names sono semantic labels mutabili tramite specifica `RENAME`;
- RelationshipDefinition M1 non è versionata;
- runtime compatibility dipende esclusivamente da stable ObjectTemplate lineage ancestry;
- normale Object `SCHEMA_CHANGE` non richiede Relationship revalidation;
- Relationship è un generic graph edge distinto dall'ownership graph;
- self-loop sono ammessi;
- runtime duplicate exact edge non sono ammessi;
- CREATE e DELETE runtime sono idempotenti secondo i contratti definiti;
- ogni reale runtime edge transition produce un lifecycle event atomico;
- strong consistency viene ottenuta con concurrency domains specifici, non tramite un global Relationship graph lock.

## 4. Invarianti aggregate

- **REL-INV-001 — Definition stable identity:** `RelationshipDefinition.id` è l'identity autorevole e stabile del relationship type.
- **REL-INV-002 — Stable endpoint contract:** `source_template_id` e `target_template_id` sono immutabili.
- **REL-INV-003 — Lineage-level dependency:** gli endpoint referenziano ObjectTemplate lineage, mai exact ObjectTemplateVersion.
- **REL-INV-004 — Endpoint existence:** ogni endpoint lineage referenziata da una definition esiste.
- **REL-INV-005 — Directional label validity:** `forward_name` e `reverse_name` rispettano la naming grammar M1.
- **REL-INV-006 — Semantic definition uniqueness:** due RelationshipDefinition semanticamente equivalenti, anche in orientamento inverso, non possono coesistere.
- **REL-INV-007 — Navigation unambiguity across definitions:** directional role con stesso name e sovrapposizione sia from-space sia to-space non possono appartenere a definition distinte concorrenti.
- **REL-INV-008 — Stable directionality class:** una `RENAME` non può trasformare una definition da symmetric a directed o viceversa.
- **REL-INV-009 — Runtime kernel identity:** `Relationship.id` è l'identity autorevole della runtime edge ed è generato dal kernel.
- **REL-INV-010 — Exact edge uniqueness:** per definition directed esiste al massimo una Relationship per exact `(definition, source, target)`.
- **REL-INV-011 — Symmetric edge uniqueness:** per definition symmetric `(D,A,B)` e `(D,B,A)` rappresentano lo stesso factual edge.
- **REL-INV-012 — Lineage-polymorphic compatibility:** source e target Object sono compatibili tramite stable lineage equality/descendancy.
- **REL-INV-013 — No exact-OTV dependency:** runtime Relationship validity non dipende da `template_version`, properties o OTV lifecycle degli endpoint.
- **REL-INV-014 — Self-loop allowed:** `source_object_id == target_object_id` è valido se l'Object soddisfa entrambi gli endpoint contract.
- **REL-INV-015 — No ownership semantics:** Relationship non applica single-owner, acyclicity, subtree o implicit lifecycle composition.
- **REL-INV-016 — Runtime referential integrity:** ogni current Relationship referenzia una current definition e due current Object.
- **REL-INV-017 — No implicit cleanup:** Object/definition delete non eliminano Relationship implicitamente.
- **REL-INV-018 — Definition delete safety:** RelationshipDefinition delete richiede zero current runtime Relationship referenti.
- **REL-INV-019 — Object delete safety:** Object delete richiede zero current incident Relationship.
- **REL-INV-020 — Runtime lifecycle atomicity:** edge create/delete e relativo lifecycle event committano o rollbackano insieme.
- **REL-INV-021 — Historical references:** identifier Relationship/definition/Object salvati nel changelog sono historical identifiers, non live dependencies.
- **REL-INV-022 — Definition snapshot coherence:** Relationship runtime mutation e lifecycle event osservano lo stesso semantic snapshot dei directional labels della definition.
- **REL-INV-023 — Strong concurrent consistency:** nessun supported interleaving può committare uno stato che viola le invarianti sopra.

## 5. Symmetric definition M1

M1 non espone un flag `symmetric`.

La symmetry è derivata dall'equivalenza completa dei due directional role:

```text
source_template_id == target_template_id
AND
forward_name == reverse_name
```

In questo specifico caso la definition è symmetric e gli endpoint runtime sono unordered semanticamente.

M1 non supporta l'intento distinto di una Relationship directed con contemporaneamente:

```text
same source/target lineage
AND
same forward/reverse name
```

Se in futuro emergerà un use case concreto, una explicit directionality discriminator potrà essere introdotta tramite decisione architetturale dedicata.

La sola sovrapposizione parziale degli endpoint spaces non implica symmetry.

## 6. Relationship properties — future seam

M1 non introduce runtime Relationship properties né `RelationshipDefinitionVersion`.

Questa omissione è deliberatamente future-compatible:

```text
RelationshipDefinition
    -> stable semantic identity

future RelationshipDefinitionVersion
    -> exact property schema snapshot

future Relationship
    -> exact definition-version pin
    -> typed canonical properties
```

La futura introduzione di typed Relationship properties potrà promuovere deterministicamente ogni definition M1 a una `v1` con schema vuoto e aggiungere l'exact version pin alle Relationship esistenti.

Gli endpoint lineage-level restano parte della stable definition identity e non diventano version-specific.

Questa capability è RFE ad alta priorità.

## 7. Modelling guideline

Per una RelationshipDefinition:

> scegliere la lineage più alta nell'albero per cui la semantica è corretta per tutti i discendenti, e scendere solo quando la semantica richiede una specializzazione.

Sintesi:

```text
highest semantically correct,
lowest necessary
```

Non creare specialization duplicate soltanto per restringere artificialmente gli endpoint spaces.

I directional names sono semantic labels, non chiavi sufficienti da sole a identificare un role. Le navigation/read view mantengono esplicita la direction quando necessario.

## 8. Candidate future / RFE

- versioned `RelationshipDefinitionVersion`;
- typed Relationship properties;
- exact RDV pin sulla runtime Relationship;
- Relationship schema migration;
- explicit directionality discriminator solo se emerge un caso reale non rappresentabile dalla regola symmetric M1;
- parallel/multi-edge instances fra la stessa `(definition, endpoints)` quando giustificate da relationship properties;
- richer relationship query/read projections;
- historical reconstruction/composite graph views.

## 9. Decisioni tecniche ancora da finalizzare

- exact PostgreSQL representation della semantic definition conflict authority;
- concrete model-plane serialization mechanism per definition CREATE/RENAME;
- canonical endpoint ordering tecnica per symmetric Relationship;
- exact FK/index/check layout;
- transaction isolation e retry strategy;
- lifecycle event persistence shape finale;
- REST/DTO shape e failure taxonomy;
- query/index strategy per directional/effective relationship navigation.
