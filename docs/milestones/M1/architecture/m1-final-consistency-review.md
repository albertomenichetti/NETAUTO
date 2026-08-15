# M1 — Final Architecture Consistency Review

**Status:** FROZEN — final consistency review complete; global M1 architecture freeze ratified on 2026-08-14 and revalidated on 2026-08-15 after the ownership current-edge clarification and the S07 RelationshipResolution physical-key correction below.

## 1. Purpose

This document records the final consistency review and freeze decision for the normative M1 architecture baseline under:

```text
docs/milestones/M1/architecture/
```

The review does not add capability. It verifies that already-ratified semantics and technical contracts agree across domain, persistence, concurrency, PostgreSQL test and public API documents.

Historical `docs.old/` material is explicitly non-normative and was not used to override the M1 baseline.

## 2. Review baseline

The review covered the consolidated M1 chain:

```text
DataType
ObjectTemplate
Object / ownership / lifecycle
Relationship R2

-> persistence PERSIST-01..20
-> concurrency predicates / REALIZE-01..15
-> real PostgreSQL PGTEST-01..04
-> public API API-01..03.11B
```

The review also checked the architecture-index and owner-document status/open-work markers against the current ratified baseline.

## 3. Findings corrected during the review

The following were documentation alignment defects, not new feature additions.

### 3.1 JSON Schema compiler/projection

Final decision:

```text
JSON Schema is not a NETAUTO validation language,
compile target or public schema projection.

No JSON Schema compiler/API/persisted representation is part of M1.
The capability is not retained as an RFE.
```

NETAUTO domain/application validation remains the sole semantic authority.

An internal effective-schema cache or precomputed execution structure may exist only as an implementation/performance optimization if justified by measurements. It is not a JSON Schema capability and not a second validation authority.

Stale or ambiguous compiler markers were removed/clarified in the owning DataType/ObjectTemplate/Object/Relationship/API/index documents.

### 3.2 Object consistency review

The review document still described the real-PostgreSQL test closure only through PGTEST-01..02.

It was aligned to the current closed baseline:

```text
REALIZE-01..15
PGTEST-01..04
API-03.11
```

No Object-specific architecture item remains open.

### 3.3 Relationship consistency review

The review document still listed REST/error work and PGTEST-03 as open.

It was aligned to the current closed baseline:

```text
REALIZE-12..15
PGTEST-01..04
API-03.11
```

No Relationship-specific architecture item remains open.

### 3.4 API companion status

`api-read-contract.md` still described success/failure mapping as the next API point.

It was aligned to API-03.11, which is already ratified and normative in `api-error-contract.md`.

### 3.5 Effective-schema optimization wording

The phrase `compiled representation` was narrowed to:

```text
internal cache or precomputed execution structure
```

and explicitly separated from JSON Schema/public schema language/validation authority.

### 3.6 Ownership current-edge slot authority — 2026-08-15 pre-flight clarification

The M1-S05 implementation pre-flight exposed a documentation contradiction between:

```text
current ownership invariant
    -> every committed edge is valid in the parent's current exact schema

PERSIST-06
    -> object_components persists parent/child/slot_name only

lifecycle/API projection
    -> structural events/projections require SlotSemanticKey
       including slot_declaring_template_id

stale DETACH wording
    -> suggested that an exact edge could be normally removed
       even when its slot no longer existed in the current parent schema
```

The stale wording would require inventing a historical slot-identity authority that does not exist in PERSIST-06.

The clarified and re-frozen rule is:

```text
current ownership fact
    = (parent_object_id, slot_name, child_object_id)

current semantic interpretation
    = resolve slot_name in the parent's current exact effective schema

SlotSemanticKey
    = (declaring_template_id, slot_name)
      derived from that current exact schema
```

`slot_declaring_template_id` is intentionally **not** duplicated in `object_components`. The runtime edge is a current fact, not a historical pin to the declaration that existed when ATTACH happened.

Consequences:

- ATTACH performs current slot/compatibility admission;
- DETACH removes the exact current edge and does not repeat ATTACH-style compatibility admission;
- nevertheless an existing current edge must remain semantically resolvable in the current exact schema of the parent;
- SCHEMA_CHANGE must fail before repinning if any outgoing edge would lose its `SlotSemanticKey` or child compatibility in the target schema;
- an `object_components` row that cannot be resolved in the current parent schema is persisted invariant corruption and maps to internal failure; no old-version, "last known slot" or lifecycle-history fallback becomes current-state authority;
- ATTACH_TO / DETACH_FROM materialize the resolved current `SlotSemanticKey` into historical lifecycle metadata at transition time.

The clarification was propagated in the same cycle to `object-ownership.md`, `object-schema-change.md`, `persistence-model.md`, `concurrency-postgresql-realization-object-ownership.md`, `object-lifecycle-changelog.md` and API-03.6 in `api-wire-contract.md`.

This correction does not add a table/column, does not change the 13-table persistence authority, does not add a concurrency predicate/gate and does not require a new PGTEST scenario ID. It closes an authority ambiguity while preserving the already-ratified ownership invariants and PERSIST-06 shape.

### 3.7 RelationshipResolution mutable-name physical key — 2026-08-15 S07 correction

The deterministic S07 `PAR-02 REL.CREATE × RD.RENAME` regression exposed a physical-schema contradiction between:

```text
RelationshipResolution.name
    -> mutable non-key Definition metadata

REALIZE-15 / PAR-02
    -> RD.RENAME uses non-key ownership semantics
    -> runtime Relationship FK insertion must not serialize solely on rename

former PERSIST-07 defensive UNIQUE
    -> UNIQUE(relationship_definition_id, from_template_id, to_template_id, name)
```

On PostgreSQL, changing a column that participates in a UNIQUE/index key eligible to back a foreign key can make the UPDATE key-changing. The former defensive UNIQUE therefore caused Resolution-name RENAME to take a stronger row lock that conflicts with the key-share protection acquired by the runtime composite FK insertion path.

That physical behavior contradicted the already-ratified semantic/mechanism contract; PAR-02 was not relaxed.

The re-frozen physical rule is:

```text
RelationshipResolution.name
    = mutable non-key metadata

therefore:
    no baseline FK-referenziable UNIQUE/index key may include name
```

The former defensive exact-child UNIQUE is removed from PERSIST-07. Complete Definition shape and duplicate semantic-child rejection remain atomic domain/UoW invariants. The following physical authorities are unchanged:

```text
PRIMARY KEY relationship_resolutions(id)
UNIQUE relationship_resolutions(id, relationship_definition_id)
FK endpoint lineage references
FK owned-child Definition relationship
runtime composite same-Definition FK
```

Consequences:

- `RD.RENAME` remains a non-key mutation and retains `FOR NO KEY UPDATE` owner semantics;
- `REL.CREATE` may acquire its required FK key-share protection without artificial serialization on Resolution-name metadata;
- REALIZE-14 old/new coherent metadata snapshot semantics remain unchanged;
- semantic equivalence/conflict and complete Definition-shape validation remain unchanged;
- no new table, column, concurrency predicate, gate, runtime identity or API behavior is introduced;
- the physical correction requires metadata/Alembic alignment that drops only the obsolete defensive constraint; existing committed migration history is advanced rather than silently rewritten.

The correction is propagated to PERSIST-07/PERSIST-15 and REALIZE-15. The canonical PAR-02 scenario remains unchanged and is the regression authority proving the correction.

## 4. Domain consistency outcome

### DataType

Confirmed aligned:

- fixed M1 PrimitiveType catalog;
- exact canonical value semantics;
- exact DTV pinning and lifecycle/default rules;
- strict public primitive lexical forms;
- no JSON Schema validation/compiler dependency.

### ObjectTemplate

Confirmed aligned:

- stable lineage + exact version snapshot model;
- exact parent/DTV pins;
- complete-candidate DRAFT revise semantics;
- derived effective schema as sole model interpretation authority;
- PropertySemanticKey / SlotSemanticKey continuity;
- no authoritative materialized effective schema;
- no JSON Schema compiler/projection.

### Object / ownership / lifecycle

Confirmed aligned:

- stable Object identity/type lineage + exact OTV pin;
- canonical JSONB runtime state;
- operation-specific mutation semantics;
- forward same-lineage SCHEMA_CHANGE with no implicit remediation;
- single-owner acyclic ownership forest;
- current ownership edges interpreted only against the parent's current exact effective schema;
- SlotSemanticKey derived from current schema, not duplicated as a runtime edge authority;
- exact attach/detach idempotency semantics;
- typed append-only lifecycle semantic-view projection;
- API read/list/error/success semantics match the domain operations.

### Relationship R2

Confirmed aligned:

- Definition/Resolution/factual Relationship/runtime Resolution separation;
- no source/target or forward/reverse semantic authority;
- Resolution name is mutable non-key metadata and is not represented by an FK-referenziable physical UNIQUE;
- complete model/runtime resolved closure;
- exact factual-view uniqueness and convergence;
- exact-ID ABA-safe delete;
- semantic-view lifecycle/read projection;
- API command/read/list/error/success contract matches R2 semantics.

## 5. Persistence and concurrency consistency outcome

Confirmed aligned:

```text
13 authoritative PostgreSQL tables
PERSIST-01..20
32 mutation census
19 semantic safety predicates
REALIZE-01..15
READ COMMITTED mutation baseline
owner lock-strength refinement
FK RESTRICT lifetime authority
ownership current-edge authority = parent current exact schema
ownership graph gate
RelationshipDefinition conflict gate
Relationship exact-view arbitration + fresh-UoW convergence
RelationshipResolution mutable name excluded from FK-referenziable physical keys
one-statement Relationship lifecycle metadata observation
```

No stale persistence/concurrency design item remains after the ownership clarification and S07 Resolution-name physical-key correction.

## 6. Real PostgreSQL test consistency outcome

Confirmed aligned:

```text
PGTEST-01 canonical test contract
PGTEST-02 51-scenario census / predicate coverage
PGTEST-03 deterministic real-PG harness contract
PGTEST-04 reusable execution recipes
```

A PGTEST-05 is not planned for fixture/helper/file-layout decomposition. A new PGTEST architecture point is opened only by a genuine architecture-level testing gap.

The ownership current-edge clarification requires targeted S05 invariant regression coverage but no new canonical concurrency scenario ID: existing ROW-13/14, ownership arbitration/gate scenarios and S05 domain/persistence tests remain the appropriate authorities.

The S07 physical-key correction likewise adds no scenario ID. Existing `PAR-02` remains the canonical regression proving that `REL.CREATE × RD.RENAME` is not artificially serialized by mutable Resolution-name storage.

## 7. Public API consistency outcome

Confirmed aligned:

```text
API-01 application/transport boundary
API-02 canonical 32-mutation route inventory
API-03.1..08 command/wire/primitive contracts
API-03.9 canonical read projections
API-03.10 keyset list/pagination/filter contract
API-03.11 finite failure codes + success HTTP policy
```

API-03.6 now explicitly distinguishes DETACH removal semantics from ATTACH admission while retaining current-schema interpretability as a persisted invariant.

No public HTTP/JSON design point remains open.

## 8. Historical baseline separation

`docs.old/` contains historical ADRs and previous architecture/code assumptions, including former JSON Schema/compiler work.

They remain read-only historical material and do not regain authority through implementation convenience or name similarity.

Any implementation conflict is resolved against the normative M1 architecture, not against `docs.old/` or pre-M1 experimental code.

## 9. Freeze decision — FREEZE-01

No blocking contradiction or unowned M1 architecture decision remains after the corrections above.

The M1 milestone contract has also completed its final review and is `FINAL / FROZEN`.

Therefore the architecture baseline state remains ratified as:

```text
M1 ARCHITECTURE FROZEN
```

Consequences:

- no M1 semantic, persistence, concurrency, PostgreSQL-test or public-API decision is left to implementation choice;
- implementation planning may decompose the frozen baseline but may not reinterpret or silently replace it;
- internal optimizations are allowed only when they preserve every relevant frozen contract;
- `docs.old/` remains historical/read-only and has no authority over the frozen baseline;
- any later contradiction or genuine architecture gap requires explicit architecture reopening and same-cycle propagation to every affected normative document.

The 2026-08-15 ownership authority clarification completed its reopen/propagate/re-freeze cycle without changing milestone scope or physical schema. The later S07 PAR-02 correction completed a second same-day reopen/propagate/re-freeze cycle: it preserves Relationship semantics and concurrency contracts while removing one obsolete defensive physical UNIQUE and authorizing the minimal forward schema migration needed to align existing databases.
