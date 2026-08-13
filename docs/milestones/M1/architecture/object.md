# M1 — Object Architecture

**Status:** DRAFT

## 1. Scopo

Questo documento è l'indice normativo dell'architettura `Object` per M1.

Documenti collegati:

- `object-runtime-state.md` — identity, create, canonical runtime properties, rename, data change, delete e current-state reads;
- `object-schema-change.md` — forward intra-lineage schema migration, definitive closures, property carry-forward e attachment validation;
- `object-ownership.md` — component ownership, attach/detach, single-owner, acyclicity e concurrency domains;
- `object-lifecycle-changelog.md` — lifecycle event stream unico, event shape, ordering, historical references e read-only surface.

I meccanismi PostgreSQL concreti — row/advisory locks, FK, CHECK, isolation level, retry, lock ordering e query shape — saranno definiti nei concurrency/persistence contract. Qui sono normative le semantics e le invarianti osservabili.

## 2. Responsabilità

Un `Object` rappresenta un'entità runtime con:

```text
id
canonical_name
template_id
template_version
properties
```

Distinzione fondamentale:

```text
Object.id
    -> authoritative entity identity

Object.template_id
    -> stable type assignment / ObjectTemplate lineage

Object.template_version
    -> exact schema snapshot corrente

Object.properties
    -> canonical mutable semantic state

Object.canonical_name
    -> mutable human/search metadata
```

Ownership/component state e Relationship state sono domini relazionali distinti dall'intrinsic Object snapshot.

## 3. Principi M1

- `Object.id` è opaco, immutabile e generato esclusivamente dal kernel;
- `template_id` non cambia tramite normali operation M1;
- ogni Object persiste un exact ObjectTemplateVersion pin;
- nessun floating/default/latest reference è persistito;
- la definitive schema closure deriva esclusivamente da exact persisted pins;
- runtime values sono sempre canonicalizzati;
- nessun generic Object update ambiguo;
- `RENAME`, `DATA_CHANGE`, `SCHEMA_CHANGE`, `ATTACH`, `DETACH`, `DELETE` sono operation semanticamente distinte;
- M1 non introduce `Object.state_revision`;
- strong consistency viene ottenuta dai concurrency contract delle singole operation;
- nessuna mutation nasconde remediation, move, detach, subtree delete o data transformation implicita;
- ogni reale lifecycle transition e il relativo changelog event sono atomici.

## 4. Invarianti aggregate

- **OBJ-INV-001 — Kernel identity:** `Object.id` è generato dal kernel e immutabile.
- **OBJ-INV-002 — Stable type assignment:** `template_id` non cambia nelle normali operation M1.
- **OBJ-INV-003 — Exact schema pin:** ogni Object materializza `(template_id, template_version)`.
- **OBJ-INV-004 — Concrete create target:** una create diretta usa una lineage non abstract.
- **OBJ-INV-005 — Create admission:** il target exact OTV deve rimanere PUBLISHED fino al commit.
- **OBJ-INV-006 — Definitive exact closure:** schema resolution usa solo exact parent/DTV pins, mai current defaults.
- **OBJ-INV-007 — Canonical runtime state:** le properties persistite sono canonical semantic values.
- **OBJ-INV-008 — No null values:** JSON `null` non è un runtime property value M1.
- **OBJ-INV-009 — Canonical zero cardinality:** optional LIST absent e `[]` convergono a key assente.
- **OBJ-INV-010 — Complete state validity:** ogni Object committed soddisfa required/cardinality/value constraints della current exact closure.
- **OBJ-INV-011 — No unknown properties:** runtime state non contiene property non presenti nell'effective schema.
- **OBJ-INV-012 — No create migration defaults:** `migration_default` non viene usato da Object CREATE.
- **OBJ-INV-013 — No generic Object revision:** M1 non introduce una generation/revision globale del live Object.
- **OBJ-INV-014 — Semantic mutation separation:** rename/data/schema/ownership/delete non sono fusi in generic update.
- **OBJ-INV-015 — Forward schema change:** normale `SCHEMA_CHANGE` mantiene `template_id` e usa `target_version > source_version`.
- **OBJ-INV-016 — Property semantic continuity:** migration carry usa `(declaring_template_id, name)`, non il solo effective name.
- **OBJ-INV-017 — Preserve existing information:** un source value presente ma target-incompatible causa schema-change failure.
- **OBJ-INV-018 — Migration default fills absence only:** non sostituisce mai automaticamente un source value esistente.
- **OBJ-INV-019 — No migration remediation M1:** nessun target override/transformation dentro `SCHEMA_CHANGE`.
- **OBJ-INV-020 — Slot semantic continuity:** attachment preservation usa `(declaring_template_id, name)`.
- **OBJ-INV-021 — No implicit detach:** schema change/delete non rimuovono ownership edges automaticamente.
- **OBJ-INV-022 — Single-owner child:** ogni child appartiene ad al massimo un `(owner, slot)`.
- **OBJ-INV-023 — Ownership acyclic:** l'ownership graph committed è aciclico.
- **OBJ-INV-024 — Effective-slot validity:** ogni outgoing edge usa uno slot effettivo della current exact OTV del parent e un child type-compatible.
- **OBJ-INV-025 — Delete isolation:** Object DELETE richiede zero incoming/outgoing ownership edge e zero external references rilevanti.
- **OBJ-INV-026 — No subtree delete:** DELETE rimuove solo l'Object richiesto.
- **OBJ-INV-027 — Unified lifecycle changelog:** intrinsic e structural events appartengono allo stesso event stream.
- **OBJ-INV-028 — Lifecycle atomicity:** una mutation reale e il suo lifecycle event committano o rollbackano insieme.
- **OBJ-INV-029 — Append-only lifecycle:** il kernel non modifica/cancella event già prodotti.
- **OBJ-INV-030 — Read-only lifecycle surface:** il changelog espone pubblicamente solo read/query operations.
- **OBJ-INV-031 — Strong concurrent consistency:** nessun supported interleaving può committare uno stato che viola le invarianti sopra.

## 5. High-risk concurrency invariants

Richiedono design PostgreSQL e integration/concurrency test dedicati:

1. `SCHEMA_CHANGE(parent)` vs `ATTACH/DETACH` sugli outgoing edges dello stesso parent;
2. concurrent `ATTACH` sullo stesso child rispetto al single-owner invariant;
3. concurrent edge-add rispetto all'ownership acyclicity;
4. `DATA_CHANGE` vs `SCHEMA_CHANGE` sullo stesso Object;
5. `DELETE` vs nuove ownership/Relationship references.

M1 privilegia correctness e semplicità rispetto al massimo parallelismo. Per il cycle predicate è ratificata la strategia di un global ownership-graph write gate per gli edge-add (`ATTACH`), lasciando il meccanismo PostgreSQL concreto ai concurrency contract.

## 6. Candidate future / RFE

- controlled cross-lineage Object reclassification A -> B;
- controlled schema migration con target-value remediation/transformation esplicita;
- Object schema downgrade/rollback;
- generic optimistic `state_revision` / ETag se use case reali lo richiederanno;
- richer DATA_CHANGE preconditions/CAS per property;
- item-level LIST mutation;
- explicit atomic move workflow sopra DETACH + ATTACH;
- orchestration API per detach/delete related state e poi DELETE Object;
- structural migration workflows più ricchi;
- expanded/composite Object reads;
- Object historical reconstruction `as-of` event/time;
- lifecycle/change feed capabilities più forti se serviranno CDC/replication semantics.

Le expanded/composite reads e historical reconstruction sono candidate ad alta priorità per M2.

## 7. Decisioni tecniche ancora da finalizzare

- PostgreSQL representation finale di canonical properties;
- exact max length e DB type di `canonical_name`;
- clock authority di `occurred_at`;
- DTO/REST shape di DATA_CHANGE `SET`/`REMOVE`;
- exact FK/CHECK/index layout;
- parent-local serialization mechanism per ownership/schema change;
- child single-owner enforcement;
- concrete global graph write gate mechanism;
- transaction isolation e retry strategy;
- lifecycle event persistence shape definitiva;
- error taxonomy;
- expanded read API shape futura.
