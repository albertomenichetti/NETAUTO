# M1 — ObjectTemplate Architecture

**Status:** DRAFT

## 1. Scopo

Questo documento è l'indice normativo dell'architettura `ObjectTemplate` per M1.

Documenti collegati:

- `objecttemplate-lifecycle.md` — stable identity, naming, inheritance, versioning, lifecycle, default, publish/deprecate/delete e read consistency;
- `objecttemplate-properties.md` — property typing, `SCALAR`/`LIST`, `required`, `migration_default`, identity ed evolution;
- `objecttemplate-components.md` — ownership slots, compatibility polimorfica, evolution e naming;
- `objecttemplate-effective-schema.md` — effective schema, create/revise, publication certification e active model graph.

I meccanismi PostgreSQL concreti — FK, constraint, lock mode, CAS, trigger, isolation level, reverse lookup e lock ordering — saranno definiti nei documenti tecnici/concurrency. Qui e nei documenti collegati sono normative le semantics e le invarianti.

## 2. Responsabilità

Una `ObjectTemplate` lineage rappresenta l'identità stabile di un **tipo di entità**.

Una `ObjectTemplateVersion` rappresenta una exact snapshot versionata dello schema di quel tipo.

```text
DataType
    -> valore atomico

ObjectTemplateProperty
    -> uno o più valori tipizzati

ObjectTemplateComponent
    -> ownership/composizione di Object con identity propria

Relationship
    -> associazione generica distinta dalla composition ownership
```

Un component non è un embedded value e una property multi-valore non è un component.

## 3. Principi M1

- semantic ownership e physical storage sono concetti distinti;
- parent lineage stabile, exact parent version evolutiva;
- exact pinning ovunque il riferimento è version-sensitive;
- nessun floating reference persistito;
- DRAFT sempre well-formed, ma non necessariamente publishable;
- PUBLISHED e DEPRECATED sono snapshot immutabili;
- effective schema derivato, non authoritative-materialized;
- strong consistency sugli invarianti semantici;
- il costo della lifecycle consistency viene pagato sul model-plane, non sul runtime hot path;
- capability che reinterpretano o possono invalidare state esistente diventano workflow espliciti e controllati, non generic CRUD mutation.

## 4. Invarianti aggregate

- **OT-INV-001 — Stable lineage identity:** `id`, `namespace`, `name`, `abstract` e parent lineage non cambiano tramite normali mutation.
- **OT-INV-002 — Qualified uniqueness:** `(namespace, name)` è univoco tra `ObjectTemplate`.
- **OT-INV-003 — Stable parent lineage:** tutte le versioni mantengono la stessa parent lineage.
- **OT-INV-004 — Exact parent pin:** ogni non-root OTV materializza una exact parent version.
- **OT-INV-005 — Acyclic inheritance:** l'inheritance graph è aciclico.
- **OT-INV-006 — Positive unique version:** `version >= 1`, univoca tra le versioni esistenti della lineage.
- **OT-INV-007 — Lifecycle monotonicity:** solo `DRAFT -> PUBLISHED -> DEPRECATED`.
- **OT-INV-008 — Stable snapshot immutability:** PUBLISHED/DEPRECATED sono strutturalmente immutabili.
- **OT-INV-009 — Draft freshness:** revise/publish/delete DRAFT rispettano `expected_revision`.
- **OT-INV-010 — DRAFT well-formedness:** ogni DRAFT persistito è semanticamente well-formed.
- **OT-INV-011 — Exact property typing:** ogni property materializza un exact DTV pin.
- **OT-INV-012 — Property cardinality:** `SCALAR`/`LIST` rispettano la cardinalità derivata da `required`.
- **OT-INV-013 — migration_default coherence:** optional -> assente; required -> presente e valido secondo value mode/exact DTV.
- **OT-INV-014 — Property identity uniqueness:** nessun property override/shadow nell'effective schema.
- **OT-INV-015 — Property historical identity:** dopo first publication, `name` e `datatype_id` sono stabili.
- **OT-INV-016 — Monotonic value-mode evolution:** normale M1 solo `SCALAR -> LIST`.
- **OT-INV-017 — Component ownership slot:** component = named `0..N` ownership slot.
- **OT-INV-018 — Polymorphic component compatibility:** child della target lineage o di una descendant lineage.
- **OT-INV-019 — Component target widening:** normale evolution solo verso ancestor della target corrente.
- **OT-INV-020 — Shared member namespace:** property e slot names sono disgiunti nell'effective schema.
- **OT-INV-021 — Derived effective schema:** source of truth = exact parent chain + local declarations.
- **OT-INV-022 — Default validity:** default `NULL` oppure exact PUBLISHED OTV della stessa lineage.
- **OT-INV-023 — No floating bindings:** ogni persisted version-sensitive binding è exact.
- **OT-INV-024 — Active model graph:** ogni PUBLISHED OTV ha direct lifecycle-sensitive dependencies PUBLISHED.
- **OT-INV-025 — Deprecation safety:** una exact dependency non può diventare DEPRECATED con active direct PUBLISHED consumer.
- **OT-INV-026 — No implicit data-plane remediation:** model mutation non esegue automaticamente Object migration/detach.
- **OT-INV-027 — Draft-only individual deletion:** single-version delete solo DRAFT.
- **OT-INV-028 — Referential lineage delete safety:** whole-lineage delete solo senza external references.
- **OT-INV-029 — Strong concurrent consistency:** nessun supported interleaving può committare uno stato che viola le invarianti.

## 5. Candidate future / RFE

- controlled type reclassification A -> B; mai generic parent update;
- controlled property rename con data preservation;
- cross-DataType-lineage controlled property migration;
- `LIST -> SCALAR` controlled data migration;
- SET / unique-items semantics;
- arbitrary property `min_count` / `max_count`;
- nested / heterogeneous collections;
- required/min/max component-slot cardinality;
- controlled component-slot narrowing;
- component target migration verso lineage non correlate;
- richer presentation/layout metadata;
- create-next provenance/audit;
- persistent/compiled effective-schema cache solo se giustificata da misure.

## 6. Decisioni tecniche ancora da finalizzare

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
