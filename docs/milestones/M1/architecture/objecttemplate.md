# M1 — ObjectTemplate Architecture

**Status:** DRAFT

## 1. Scopo

Questo documento è l'indice normativo dell'architettura `ObjectTemplate` M1. I dettagli sono separati per area per mantenere leggibile il contratto e facilitare traceability verso concurrency contract e implementation steps.

Documenti normativi collegati:

- `objecttemplate-lifecycle.md` — stable identity, naming, inheritance, versioning, pinning, lifecycle, default, publish/deprecate/delete e read consistency;
- `objecttemplate-properties.md` — property typing, SCALAR/LIST, required, migration_default, identity ed evolution;
- `objecttemplate-components.md` — ownership slots, polymorphic compatibility, evolution e naming;
- `objecttemplate-effective-schema.md` — effective schema resolution, create/revise e active model graph invariant.

I meccanismi PostgreSQL concreti (FK, constraint, lock, CAS, trigger, isolation e lock ordering) saranno definiti nei documenti tecnici/concurrency. Qui e nei documenti collegati sono normative le semantics e le invarianti.

## 2. Responsabilità

Una `ObjectTemplate` lineage rappresenta l'identità stabile di un **tipo di entità**. Una `ObjectTemplateVersion` rappresenta una exact snapshot versionata del relativo schema.

```text
DataType                  -> valore atomico
ObjectTemplateProperty    -> uno o più valori tipizzati
ObjectTemplateComponent   -> ownership/composizione di Object con identity propria
Relationship              -> associazione generica distinta dalla composition
```

Un component non è un embedded value e una property multi-valore non è un component.

## 3. Invarianti aggregate M1

- stable lineage identity: `id`, `namespace`, `name`, `abstract` e parent lineage non cambiano tramite normali mutation;
- `(namespace, name)` è univoco tra ObjectTemplate;
- ogni non-root OTV materializza un exact parent-version pin;
- inheritance aciclica;
- lifecycle monotono `DRAFT -> PUBLISHED -> DEPRECATED`;
- PUBLISHED/DEPRECATED sono structural snapshot immutabili;
- DRAFT mutation protette da `expected_revision`;
- ogni DRAFT persistito è semanticamente well-formed;
- effective schema derivato da exact parent chain + local declarations, senza authoritative materialization;
- property e component slot condividono un unico effective member namespace;
- ogni PUBLISHED OTV possiede soltanto direct lifecycle-sensitive exact dependencies PUBLISHED;
- una exact dependency non può diventare DEPRECATED mentre esiste un direct active/PUBLISHED consumer;
- model mutation non esegue implicit Object migration o detach;
- single-version delete solo DRAFT; whole-lineage delete solo senza external references;
- ogni supported concurrent interleaving deve preservare tutte le invarianti.

## 4. Cost/benefit principle

M1 privilegia strong semantics con costo permanente controllato. Le capability che reinterpretano o possono invalidare state esistente devono essere workflow espliciti e controllati, non generic CRUD mutation.

In particolare sono deliberate future RFE:

- controlled type reclassification A -> B;
- controlled property rename/data migration;
- `LIST -> SCALAR` migration;
- cross-DataType-lineage property migration;
- component-slot narrowing;
- arbitrary property/component cardinality;
- SET/nested/heterogeneous collections;
- richer layout metadata;
- create-next provenance/audit;
- persistent effective-schema cache solo se giustificata da misure.

## 5. Decisioni tecniche ancora da finalizzare

Prima del freeze M1 restano da definire:

- schema PostgreSQL finale e collocazione fisica di `parent_template_id`;
- FK/check/constraint-trigger definitivi;
- DB/API representation di `value_mode` e LIST cardinality zero;
- DTO shape di local/effective schema reads;
- concurrency mechanism per create/create-next/revise/publish/deprecate/delete;
- reverse-dependency query/index per active-model-graph deprecation;
- global lock ordering OTV/DTV;
- transaction isolation dei singoli UoW;
- REST endpoints/error taxonomy;
- compiled schema/caching policy.
